#!/usr/bin/env python3
"""
CLI Helper: Bibliometric Network Analyst
Builds bibliometric networks (co-occurrence, co-authorship, co-citation, bibliographic coupling, direct citation),
supports single-period filtering and sequential longitudinal networks generation (Warm-Start SOM compatible),
calculates Association Strength, detects communities using Leiden/Louvain, computes centralities,
and exports to GEXF, Pajek (.net), or VOSviewer JSON.
"""

import sys
import os
import re
import json
import csv
import math
import argparse
from collections import defaultdict, Counter
from typing import Dict, List, Any, Tuple, Optional, Set

import networkx as nx

# Try igraph and leidenalg
try:
    import igraph as ig
    import leidenalg
    LEIDEN_AVAILABLE = True
except ImportError:
    LEIDEN_AVAILABLE = False


def extract_year(val: Any) -> Optional[int]:
    """Extracts a valid 4-digit calendar year (1800-2100) from diverse formats."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        try:
            if not math.isnan(val) and 1800 <= int(val) <= 2100:
                return int(val)
        except (ValueError, TypeError):
            pass
        return None
    val_str = str(val).strip()
    if not val_str:
        return None
    m = re.search(r'\b(1[89]\d\d|20\d\d)\b', val_str)
    if m:
        return int(m.group(1))
    return None


def extract_doc_year(row: Dict[str, Any]) -> Optional[int]:
    """Inspects common schema field names for publication year."""
    year_raw = (
        row.get("year")
        or row.get("publication_year")
        or row.get("PY")
        or row.get("Year")
        or row.get("Date")
        or row.get("publication_date")
        or row.get("anio")
        or row.get("periodo")
    )
    return extract_year(year_raw)


def extract_references(row: Dict[str, Any]) -> List[str]:
    """Extracts reference identifiers from normalized or raw bibliographic records."""
    raw_refs = row.get("references") or row.get("referenced_works") or row.get("CR") or []
    if isinstance(raw_refs, list):
        return [str(r).strip() for r in raw_refs if str(r).strip()]
def parse_wos_plaintext(filepath: str) -> List[Dict[str, Any]]:
    """Parses Web of Science plain text export files (savedrecs.txt)."""
    records = []
    current_rec = {}
    current_tag = None

    with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
        for line in f:
            line_str = line.rstrip("\r\n")
            if not line_str:
                continue
            if line_str == "ER" or line_str.startswith("ER "):
                if current_rec:
                    rec_clean = {}
                    for k, v in current_rec.items():
                        if isinstance(v, list):
                            rec_clean[k] = "; ".join(v)
                        else:
                            rec_clean[k] = v
                    rec_clean["title"] = rec_clean.get("TI", "")
                    rec_clean["authors"] = rec_clean.get("AU", "")
                    rec_clean["year"] = extract_year(rec_clean.get("PY"))
                    rec_clean["keywords"] = rec_clean.get("DE") or rec_clean.get("ID", "")
                    rec_clean["source_title"] = rec_clean.get("SO", "")
                    rec_clean["references"] = rec_clean.get("CR", "")
                    records.append(rec_clean)
                    current_rec = {}
                current_tag = None
                continue

            if line_str.startswith("   ") and current_tag:
                val = line_str.strip()
                if current_tag in current_rec:
                    if isinstance(current_rec[current_tag], list):
                        current_rec[current_tag].append(val)
                    else:
                        current_rec[current_tag] = [current_rec[current_tag], val]
            elif len(line_str) >= 2 and line_str[:2].isupper() and (len(line_str) == 2 or line_str[2] == " "):
                tag = line_str[:2]
                val = line_str[3:].strip()
                current_tag = tag
                current_rec[tag] = [val] if tag in ("AU", "AF", "CR", "C1") else val

    return records


def parse_period_string(period_str: str) -> Tuple[int, int, str]:
    """Parses 'YYYY-YYYY', 'YYYY:YYYY', or 'YYYY' into (start_year, end_year, label)."""
    p = str(period_str).strip()
    if "-" in p:
        parts = p.split("-")
        s, e = int(parts[0].strip()), int(parts[1].strip())
        return min(s, e), max(s, e), f"{min(s, e)}-{max(s, e)}"
    elif ":" in p:
        parts = p.split(":")
        s, e = int(parts[0].strip()), int(parts[1].strip())
        return min(s, e), max(s, e), f"{min(s, e)}-{max(s, e)}"
    else:
        y = int(p)
        return y, y, str(y)


def generate_period_windows(
    years_list: List[int],
    window_size: int = 5,
    step_size: Optional[int] = None
) -> List[Tuple[str, int, int]]:
    """
    Generates sequence of windows [(label, start_year, end_year), ...].
    If step_size is None or equal to window_size, windows are consecutive/disjoint.
    If step_size < window_size, windows are sliding/overlapping.
    """
    clean_years = sorted(list({y for y in years_list if y and 1800 <= y <= 2100}))
    if not clean_years:
        return []

    w = max(1, int(window_size))
    s = max(1, int(step_size)) if step_size is not None else w

    if w == 1 and s == 1:
        return [(str(y), y, y) for y in clean_years]

    min_y = clean_years[0]
    max_y = clean_years[-1]

    windows = []
    cur_start = min_y
    while cur_start <= max_y:
        cur_end = min(cur_start + w - 1, max_y)
        label = f"{cur_start}-{cur_end}" if cur_start != cur_end else str(cur_start)
        if any(cur_start <= y <= cur_end for y in clean_years):
            windows.append((label, cur_start, cur_end))
        if cur_start + s > max_y:
            break
        cur_start += s

    return windows


def filter_docs_by_period(
    docs: List[Dict[str, Any]],
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    period: Optional[str] = None,
    last_years: Optional[int] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Filters docs based on temporal constraints. Returns (filtered_docs, period_metadata).
    """
    valid_years = [d["year"] for d in docs if d.get("year") is not None]
    if not valid_years:
        return docs, {"filter_applied": False, "reason": "No publication years detected in corpus"}

    min_corpus_y = min(valid_years)
    max_corpus_y = max(valid_years)

    start_y = min_corpus_y
    end_y = max_corpus_y
    period_label = f"{min_corpus_y}-{max_corpus_y}"
    filter_applied = False

    if period:
        start_y, end_y, period_label = parse_period_string(period)
        filter_applied = True
    elif last_years is not None and last_years > 0:
        start_y = max_corpus_y - int(last_years) + 1
        end_y = max_corpus_y
        period_label = f"{start_y}-{end_y}" if start_y != end_y else str(start_y)
        filter_applied = True
    else:
        if year_from is not None:
            start_y = int(year_from)
            filter_applied = True
        if year_to is not None:
            end_y = int(year_to)
            filter_applied = True
        if filter_applied:
            period_label = f"{start_y}-{end_y}" if start_y != end_y else str(start_y)

    if not filter_applied:
        return docs, {
            "filter_applied": False,
            "year_from": min_corpus_y,
            "year_to": max_corpus_y,
            "label": period_label,
            "total_docs": len(docs),
            "filtered_docs": len(docs)
        }

    filtered = [d for d in docs if d.get("year") is not None and start_y <= d["year"] <= end_y]
    meta = {
        "filter_applied": True,
        "year_from": start_y,
        "year_to": end_y,
        "label": period_label,
        "total_docs": len(docs),
        "filtered_docs": len(filtered)
    }
    return filtered, meta


def load_corpus_items(filepath: str, unit: str) -> List[Dict[str, Any]]:
    """
    Extracts target units, references, and publication year per document
    from normalized Parquet/CSV/JSON or native OpenAlex JSON.
    """
    lower = filepath.lower()
    docs = []

    def to_item_list(raw_val: Any) -> List[str]:
        if not raw_val:
            return []
        if isinstance(raw_val, list):
            res = []
            for elem in raw_val:
                if isinstance(elem, dict):
                    name = elem.get("display_name") or elem.get("name") or elem.get("label") or elem.get("id") or ""
                    if name:
                        res.append(str(name).strip())
                elif elem is not None:
                    res.append(str(elem).strip())
            return res
        return [i.strip() for i in str(raw_val).split(";") if i.strip()]

    def get_items(row: Dict[str, Any], u: str) -> List[str]:
        if u == "keywords":
            val = row.get("keywords_author") or row.get("keywords") or row.get("DE")
            if not val:
                val = row.get("keywords_plus") or row.get("ID") or row.get("concepts")
            return list(set(i for i in to_item_list(val) if i))

        elif u == "authors":
            val = row.get("authors") or row.get("Authors") or row.get("AU")
            if not val:
                val = row.get("authorships")
            if isinstance(val, list):
                res = []
                for elem in val:
                    if isinstance(elem, dict):
                        auth_obj = elem.get("author") or elem
                        name = auth_obj.get("display_name") or auth_obj.get("name") or ""
                        if name:
                            res.append(str(name).strip())
                    elif elem is not None:
                        res.append(str(elem).strip())
                return list(set(i for i in res if i))
            return list(set(i for i in to_item_list(val) if i))

        elif u == "institutions":
            val = row.get("affiliations") or row.get("Affiliations") or row.get("C1") or row.get("institutions")
            if not val and isinstance(row.get("authorships"), list):
                res = []
                for elem in row["authorships"]:
                    if isinstance(elem, dict):
                        for inst in elem.get("institutions", []):
                            iname = inst.get("display_name") or inst.get("name") or ""
                            if iname:
                                res.append(str(iname).strip())
                if res:
                    return list(set(res))
            return list(set(i for i in to_item_list(val) if i))

        elif u == "countries":
            val = row.get("affiliations") or row.get("Affiliations") or row.get("countries")
            if isinstance(val, list):
                return list(set(str(c).strip().lower() for c in val if c))
            parts = [p.split(",")[-1].strip().lower() for p in str(val).split(";") if p.strip()]
            return list(set(p for p in parts if len(p) > 2))

        elif u == "sources":
            val = row.get("source_title") or row.get("journal") or row.get("SO")
            if not val and isinstance(row.get("primary_location"), dict):
                src = row["primary_location"].get("source") or {}
                val = src.get("display_name") or src.get("name")
            return [str(val).strip()] if val and str(val).strip() else []

        return []

    if lower.endswith(".parquet"):
        import pandas as pd
        df = pd.read_parquet(filepath)
        for idx, row in df.iterrows():
            r_dict = row.to_dict()
            items = get_items(r_dict, unit)
            docs.append({
                "id": str(r_dict.get("id") or r_dict.get("doi") or f"doc_{idx}"),
                "items": items,
                "references": extract_references(r_dict),
                "year": extract_doc_year(r_dict)
            })
        return docs

    if lower.endswith(".csv"):
        with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            for idx, r in enumerate(reader):
                items = get_items(r, unit)
                docs.append({
                    "id": str(r.get("id") or r.get("doi") or f"doc_{idx}"),
                    "items": items,
                    "references": extract_references(r),
                    "year": extract_doc_year(r)
                })
        return docs

    if lower.endswith(".json"):
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
            if isinstance(data, dict):
                records = data.get("results") or data.get("records") or data.get("works") or data.get("data") or [data]
            else:
                records = data

            for idx, r in enumerate(records):
                if not isinstance(r, dict):
                    continue
                items = get_items(r, unit)
                docs.append({
                    "id": str(r.get("id") or r.get("doi") or f"doc_{idx}"),
                    "items": items,
                    "references": extract_references(r),
                    "year": extract_doc_year(r)
                })
        return docs

    if lower.endswith(".txt"):
        records = parse_wos_plaintext(filepath)
        for idx, r in enumerate(records):
            items = get_items(r, unit)
            docs.append({
                "id": str(r.get("id") or r.get("UT") or r.get("doi") or f"doc_{idx}"),
                "items": items,
                "references": extract_references(r),
                "year": extract_doc_year(r)
            })
        return docs

    return docs


def build_cooccurrence_matrix(
    docs: List[Dict[str, Any]],
    counting: str,
    min_freq: int,
    min_cooccur: float
) -> Tuple[List[str], Dict[Tuple[str, str], float], Dict[str, float]]:
    """Builds co-occurrence network with full or fractional counting."""
    item_freq = defaultdict(float)
    pair_weights = defaultdict(float)

    for doc in docs:
        items = doc["items"]
        k = len(items)
        if k == 0:
            continue

        if counting == "fractional":
            item_weight = 1.0 / k
            pair_weight = 1.0 / (k - 1) if k > 1 else 0.0
        else:
            item_weight = 1.0
            pair_weight = 1.0

        for item in items:
            item_freq[item] += item_weight

        if k > 1:
            for i in range(k):
                for j in range(i + 1, k):
                    pair = tuple(sorted([items[i], items[j]]))
                    pair_weights[pair] += pair_weight

    # Filter items by min_freq
    valid_items = set(item for item, freq in item_freq.items() if freq >= min_freq)
    valid_pairs = {
        pair: weight for pair, weight in pair_weights.items()
        if weight >= min_cooccur and pair[0] in valid_items and pair[1] in valid_items
    }

    active_items = sorted(list(valid_items))
    return active_items, valid_pairs, item_freq


def build_bib_coupling_matrix(
    docs: List[Dict[str, Any]],
    unit: str,
    min_freq: int,
    min_cooccur: float
) -> Tuple[List[str], Dict[Tuple[str, str], float], Dict[str, float]]:
    """Builds bibliographic coupling network based on shared cited references."""
    ref_to_docs = defaultdict(set)
    doc_meta = {}

    for doc in docs:
        doc_id = doc["id"] or (doc["items"][0] if doc["items"] else str(id(doc)))
        doc_meta[doc_id] = doc["items"]
        for ref in doc["references"]:
            ref_to_docs[ref].add(doc_id)

    pair_weights = defaultdict(float)
    for ref, sharing_docs in ref_to_docs.items():
        doc_list = list(sharing_docs)
        for i in range(len(doc_list)):
            for j in range(i + 1, len(doc_list)):
                pair = tuple(sorted([doc_list[i], doc_list[j]]))
                pair_weights[pair] += 1.0

    active_items = list(doc_meta.keys())
    item_freq = {doc_id: float(len(docs[i]["references"])) for i, doc_id in enumerate(active_items) if i < len(docs)}
    return active_items, pair_weights, item_freq


def normalize_weights(
    pairs: Dict[Tuple[str, str], float],
    item_freq: Dict[str, float],
    method: str
) -> Dict[Tuple[str, str], float]:
    """Applies Association Strength, Salton's Cosine, or Jaccard normalization."""
    if method == "none":
        return pairs

    total_weight = sum(pairs.values())
    if total_weight == 0:
        return pairs

    normalized = {}
    for (u, v), c_uv in pairs.items():
        s_u = item_freq.get(u, 1.0)
        s_v = item_freq.get(v, 1.0)

        if method == "association-strength":
            # Van Eck & Waltman: s_ij = (2 * m * c_ij) / (s_i * s_j)
            denom = s_u * s_v
            score = (2.0 * total_weight * c_uv) / denom if denom > 0 else 0.0
        elif method == "salton":
            denom = math.sqrt(s_u * s_v)
            score = c_uv / denom if denom > 0 else 0.0
        elif method == "jaccard":
            denom = s_u + s_v - c_uv
            score = c_uv / denom if denom > 0 else 0.0
        else:
            score = c_uv

        normalized[(u, v)] = round(score, 4)

    return normalized


def detect_network_communities(
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    algorithm: str = "leiden",
    resolution: float = 1.0
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Detects modular communities using Leiden or Louvain."""
    node_to_comm = {}
    communities_list = []

    if algorithm == "leiden" and LEIDEN_AVAILABLE:
        g = ig.Graph()
        name_to_idx = {n["id"]: idx for idx, n in enumerate(nodes)}
        g.add_vertices(len(nodes))
        g.vs["name"] = [n["id"] for n in nodes]

        ig_edges = []
        ig_weights = []
        for e in edges:
            if e["source"] in name_to_idx and e["target"] in name_to_idx:
                ig_edges.append((name_to_idx[e["source"]], name_to_idx[e["target"]]))
                ig_weights.append(e.get("weight", 1.0))

        g.add_edges(ig_edges)
        g.es["weight"] = ig_weights

        partition = leidenalg.find_partition(
            g,
            leidenalg.RBConfigurationVertexPartition,
            weights=g.es["weight"] if ig_weights else None,
            resolution_parameter=resolution
        )

        for comm_id, comm_members in enumerate(partition):
            member_names = [g.vs[idx]["name"] for idx in comm_members]
            communities_list.append({
                "community_id": comm_id + 1,
                "size": len(member_names),
                "members": member_names
            })
            for m in member_names:
                node_to_comm[m] = comm_id + 1
    else:
        G = nx.Graph()
        for n in nodes:
            G.add_node(n["id"], frequency=n.get("frequency", 1.0))
        for e in edges:
            G.add_edge(e["source"], e["target"], weight=float(e.get("weight", 1.0)))

        nx_comms = nx.community.louvain_communities(G, weight="weight", resolution=resolution)
        for comm_id, members in enumerate(nx_comms):
            m_list = list(members)
            communities_list.append({
                "community_id": comm_id + 1,
                "size": len(m_list),
                "members": m_list
            })
            for m in m_list:
                node_to_comm[m] = comm_id + 1

    return communities_list, node_to_comm


def compute_network_centralities(
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Calculates Degree, Betweenness, and PageRank centralities."""
    G = nx.Graph()
    for n in nodes:
        G.add_node(n["id"])
    for e in edges:
        G.add_edge(e["source"], e["target"], weight=float(e.get("weight", 1.0)))

    deg = dict(G.degree(weight="weight"))
    bet = nx.betweenness_centrality(G, weight="weight", normalized=True) if len(nodes) > 0 else {}
    pr = nx.pagerank(G, weight="weight") if len(nodes) > 0 else {}

    ranked_nodes = []
    for n in nodes:
        node_id = n["id"]
        ranked_nodes.append({
            "id": node_id,
            "label": n.get("label", node_id),
            "degree_weighted": round(deg.get(node_id, 0.0), 3),
            "betweenness": round(bet.get(node_id, 0.0), 5),
            "pagerank": round(pr.get(node_id, 0.0), 5),
            "community": n.get("community", 0)
        })

    ranked_nodes.sort(key=lambda x: x["pagerank"], reverse=True)
    return ranked_nodes


def build_vosviewer_json_data(
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Builds canonical VOSviewer JSON dictionary (items with weights/scores, and links)."""
    link_counts = Counter()
    tls_counts = Counter()
    id_to_idx = {n["id"]: idx for idx, n in enumerate(nodes, start=1)}

    vos_links = []
    for e in edges:
        src = e["source"]
        tgt = e["target"]
        w = float(e.get("weight", 1.0))
        if src in id_to_idx and tgt in id_to_idx and src != tgt:
            link_counts[src] += 1
            link_counts[tgt] += 1
            tls_counts[src] += w
            tls_counts[tgt] += w
            vos_links.append({
                "source_id": id_to_idx[src],
                "target_id": id_to_idx[tgt],
                "strength": round(w, 4)
            })

    vos_items = []
    for idx, n in enumerate(nodes, start=1):
        nid = n["id"]
        freq = float(n.get("frequency", 1.0))
        comm = int(n.get("community", 1))

        weights = {
            "Occurrences": freq,
            "Total link strength": round(tls_counts[nid], 3),
            "Links": link_counts[nid]
        }
        scores = {}
        if "pagerank" in n and n["pagerank"] is not None:
            scores["PageRank"] = round(float(n["pagerank"]), 5)
        if "betweenness" in n and n["betweenness"] is not None:
            scores["Betweenness"] = round(float(n["betweenness"]), 5)
        if "avg_year" in n and n["avg_year"] is not None:
            scores["Avg. pub. year"] = round(float(n["avg_year"]), 1)

        item = {
            "id": idx,
            "label": str(n.get("label", nid)),
            "cluster": comm,
            "weights": weights
        }
        if scores:
            item["scores"] = scores
        vos_items.append(item)

    return {
        "network": {
            "items": vos_items,
            "links": vos_links
        },
        "config": {
            "parameters": {
                "scale": 1.0,
                "item_size_variation": 0.5,
                "max_n_links": 1000
            }
        }
    }


def generate_knomap_force_html(
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    title: str = "Bibliometric Network",
    subtitle: Optional[str] = None
) -> str:
    """Generates a standalone, beautiful D3.js interactive Force Graph HTML matching KnoMap design."""
    nodes_json = json.dumps(nodes, ensure_ascii=False)
    edges_json = json.dumps(edges, ensure_ascii=False)
    sub_text = subtitle or "KnoMap Interactive Force-Directed Graph"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - KnoMap Network</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-base: #030712;
            --bg-panel: rgba(17, 24, 39, 0.88);
            --bg-card: rgba(31, 41, 55, 0.7);
            --border-dim: rgba(255, 255, 255, 0.08);
            --accent-primary: #6366f1;
            --text-main: #f9fafb;
            --text-muted: #9ca3af;
            --text-dim: #6b7280;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background-color: var(--bg-base);
            color: var(--text-main);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            overflow: hidden;
            width: 100vw;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        header {{
            height: 56px;
            background: var(--bg-panel);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-dim);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 20px;
            z-index: 20;
        }}
        .brand {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .brand-logo {{
            width: 28px;
            height: 28px;
            border-radius: 6px;
            background: linear-gradient(135deg, #6366f1, #10b981);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 14px;
            color: #fff;
            box-shadow: 0 0 14px rgba(99, 102, 241, 0.5);
        }}
        .brand-title {{
            font-size: 15px;
            font-weight: 700;
            color: #fff;
            letter-spacing: -0.01em;
        }}
        .brand-subtitle {{
            font-size: 11px;
            color: var(--text-muted);
            margin-left: 8px;
            font-weight: 400;
        }}
        .badge-pill {{
            font-size: 11px;
            padding: 3px 8px;
            border-radius: 999px;
            background: rgba(99, 102, 241, 0.15);
            border: 1px solid rgba(99, 102, 241, 0.3);
            color: #a5b4fc;
            font-weight: 600;
        }}
        .top-stats {{
            display: flex;
            align-items: center;
            gap: 16px;
            font-size: 12px;
            color: var(--text-muted);
        }}
        .top-stat-val {{
            color: #fff;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
        }}
        main {{
            flex: 1;
            position: relative;
            display: flex;
        }}
        #graph-container {{
            flex: 1;
            width: 100%;
            height: 100%;
            position: relative;
        }}
        svg {{
            width: 100%;
            height: 100%;
            cursor: grab;
        }}
        svg:active {{
            cursor: grabbing;
        }}
        .controls-overlay {{
            position: absolute;
            top: 16px;
            left: 16px;
            width: 280px;
            background: var(--bg-panel);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-dim);
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            z-index: 10;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        .control-group {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}
        .control-label {{
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
        }}
        .search-input {{
            width: 100%;
            background: rgba(3, 7, 18, 0.8);
            border: 1px solid var(--border-dim);
            border-radius: 6px;
            padding: 7px 10px;
            color: #fff;
            font-size: 12px;
            outline: none;
            transition: all 0.2s ease;
        }}
        .search-input:focus {{
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
        }}
        .toggle-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 12px;
            color: var(--text-muted);
        }}
        .toggle-row input[type="checkbox"] {{
            accent-color: var(--accent-primary);
            cursor: pointer;
        }}
        .btn-row {{
            display: flex;
            gap: 8px;
        }}
        .btn {{
            flex: 1;
            background: rgba(31, 41, 55, 0.8);
            border: 1px solid var(--border-dim);
            color: #e5e7eb;
            font-size: 11px;
            font-weight: 600;
            padding: 6px 10px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
            text-align: center;
        }}
        .btn:hover {{
            background: var(--accent-primary);
            color: #fff;
            border-color: var(--accent-primary);
        }}
        .inspector-card {{
            position: absolute;
            top: 16px;
            right: 16px;
            width: 300px;
            background: var(--bg-panel);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-dim);
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            z-index: 10;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .inspector-title {{
            font-size: 14px;
            font-weight: 700;
            color: #fff;
            word-break: break-word;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-top: 4px;
        }}
        .metric-box {{
            background: rgba(3, 7, 18, 0.5);
            border: 1px solid var(--border-dim);
            border-radius: 6px;
            padding: 6px 8px;
        }}
        .metric-lbl {{
            font-size: 10px;
            color: var(--text-muted);
            text-transform: uppercase;
        }}
        .metric-val {{
            font-size: 13px;
            font-weight: 700;
            color: #a5b4fc;
            font-family: 'JetBrains Mono', monospace;
            margin-top: 2px;
        }}
        .link {{
            stroke: #6366f1;
            stroke-opacity: 0.35;
            transition: stroke-opacity 0.2s, stroke 0.2s;
        }}
        .link.highlight {{
            stroke: #a5b4fc;
            stroke-opacity: 0.9;
        }}
        .link.dimmed {{
            stroke-opacity: 0.04;
        }}
        .node circle {{
            stroke: #fff;
            stroke-width: 1.5px;
            cursor: pointer;
            transition: transform 0.2s, stroke-width 0.2s;
        }}
        .node circle:hover {{
            stroke-width: 2.5px;
            filter: drop-shadow(0 0 8px currentColor);
        }}
        .node.dimmed circle {{
            opacity: 0.15;
        }}
        .node text {{
            font-size: 10px;
            font-weight: 500;
            fill: #f3f4f6;
            pointer-events: none;
            paint-order: stroke fill;
            stroke: #030712;
            stroke-width: 3px;
        }}
        .node.dimmed text {{
            opacity: 0.1;
        }}
        .legend-container {{
            position: absolute;
            bottom: 16px;
            left: 16px;
            background: var(--bg-panel);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-dim);
            border-radius: 8px;
            padding: 8px 12px;
            display: flex;
            gap: 12px;
            align-items: center;
            font-size: 11px;
            z-index: 10;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .legend-dot {{
            width: 9px;
            height: 9px;
            border-radius: 50%;
        }}
    </style>
</head>
<body>
    <header>
        <div class="brand">
            <div class="brand-logo">K</div>
            <div class="brand-title">{title}</div>
            <div class="brand-subtitle">{sub_text}</div>
            <div class="badge-pill">knoMap Engine</div>
        </div>
        <div class="top-stats">
            <div>Nodos: <span class="top-stat-val" id="stat-nodes">0</span></div>
            <div>Aristas: <span class="top-stat-val" id="stat-edges">0</span></div>
            <div>Comunidades: <span class="top-stat-val" id="stat-comms">0</span></div>
        </div>
    </header>

    <main>
        <div class="controls-overlay">
            <div class="control-group">
                <span class="control-label">Búsqueda de Término</span>
                <input type="text" id="search-input" class="search-input" placeholder="Filtrar por etiqueta...">
            </div>
            <div class="control-group">
                <div class="toggle-row">
                    <span>Solo Componente Conexo (LCC)</span>
                    <input type="checkbox" id="toggle-lcc">
                </div>
            </div>
            <div class="btn-row">
                <button class="btn" id="btn-reset-zoom">Reset Vista</button>
                <button class="btn" id="btn-export-svg">Export SVG</button>
            </div>
        </div>

        <div id="inspector" class="inspector-card">
            <div style="font-size: 11px; color: var(--text-dim); text-transform: uppercase; font-weight: 600;">Detalles del Nodo</div>
            <div id="inspector-name" class="inspector-title">Pase el cursor sobre un nodo</div>
            <div id="inspector-badge" style="display:none;" class="badge-pill">Cluster 1</div>
            <div class="metric-grid" id="inspector-metrics" style="display:none;">
                <div class="metric-box">
                    <div class="metric-lbl">Frecuencia</div>
                    <div class="metric-val" id="m-freq">-</div>
                </div>
                <div class="metric-box">
                    <div class="metric-lbl">Grado Ponderado</div>
                    <div class="metric-val" id="m-deg">-</div>
                </div>
                <div class="metric-box">
                    <div class="metric-lbl">PageRank</div>
                    <div class="metric-val" id="m-pr">-</div>
                </div>
                <div class="metric-box">
                    <div class="metric-lbl">Betweenness</div>
                    <div class="metric-val" id="m-bet">-</div>
                </div>
            </div>
        </div>

        <div id="graph-container">
            <svg id="network-svg"></svg>
        </div>

        <div class="legend-container" id="legend"></div>
    </main>

    <script>
        const rawNodes = {nodes_json};
        const rawEdges = {edges_json};

        const colorPalette = [
            '#6366f1', '#10b981', '#f59e0b', '#ec4899', '#3b82f6',
            '#8b5cf6', '#06b6d4', '#f97316', '#14b8a6', '#e11d48',
            '#84cc16', '#d946ef', '#64748b'
        ];

        function getNodeColor(comm) {{
            const c = (parseInt(comm) || 1) - 1;
            return colorPalette[Math.abs(c) % colorPalette.length];
        }}

        const communitiesSet = new Set(rawNodes.map(n => n.community || 1));
        document.getElementById('stat-nodes').textContent = rawNodes.length;
        document.getElementById('stat-edges').textContent = rawEdges.length;
        document.getElementById('stat-comms').textContent = communitiesSet.size;

        const legendDiv = document.getElementById('legend');
        Array.from(communitiesSet).sort((a,b)=>a-b).slice(0, 7).forEach(cid => {{
            const item = document.createElement('div');
            item.className = 'legend-item';
            item.innerHTML = `<div class="legend-dot" style="background:${{getNodeColor(cid)}}"></div><span>C${{cid}}</span>`;
            legendDiv.appendChild(item);
        }});

        const container = document.getElementById('graph-container');
        const width = container.clientWidth || window.innerWidth;
        const height = container.clientHeight || (window.innerHeight - 56);

        const svg = d3.select('#network-svg');
        const g = svg.append('g');

        const zoom = d3.zoom()
            .scaleExtent([0.2, 5])
            .on('zoom', (event) => g.attr('transform', event.transform));
        svg.call(zoom);

        document.getElementById('btn-reset-zoom').addEventListener('click', () => {{
            svg.transition().duration(750).call(zoom.transform, d3.zoomIdentity);
        }});

        let activeNodes = rawNodes.map(d => Object.assign({{}}, d));
        let activeEdges = rawEdges.map(d => Object.assign({{}}, d));

        const neighborMap = new Map();
        rawNodes.forEach(n => neighborMap.set(n.id, new Set()));
        rawEdges.forEach(e => {{
            const u = e.source.id || e.source;
            const v = e.target.id || e.target;
            if (neighborMap.has(u)) neighborMap.get(u).add(v);
            if (neighborMap.has(v)) neighborMap.get(v).add(u);
        }});

        const simulation = d3.forceSimulation(activeNodes)
            .force('link', d3.forceLink(activeEdges).id(d => d.id).distance(70))
            .force('charge', d3.forceManyBody().strength(-180))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(d => Math.sqrt(d.frequency || 1) * 5 + 8));

        const link = g.append('g')
            .selectAll('line')
            .data(activeEdges)
            .join('line')
            .attr('class', 'link')
            .attr('stroke-width', d => Math.max(1, Math.min(5, (d.weight || 1) * 2.5)));

        const node = g.append('g')
            .selectAll('.node')
            .data(activeNodes)
            .join('g')
            .attr('class', 'node')
            .call(d3.drag()
                .on('start', dragstarted)
                .on('drag', dragged)
                .on('end', dragended));

        node.append('circle')
            .attr('r', d => Math.sqrt(d.frequency || 1) * 5 + 4)
            .attr('fill', d => getNodeColor(d.community))
            .attr('color', d => getNodeColor(d.community));

        node.append('text')
            .attr('dy', d => -(Math.sqrt(d.frequency || 1) * 5 + 7))
            .attr('text-anchor', 'middle')
            .text(d => d.label || d.id);

        simulation.on('tick', () => {{
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            node
                .attr('transform', d => `translate(${{d.x}},${{d.y}})`);
        }});

        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}

        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}

        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}

        node.on('mouseenter', (event, d) => {{
            const neighbors = neighborMap.get(d.id) || new Set();
            node.classed('dimmed', n => n.id !== d.id && !neighbors.has(n.id));
            link.classed('dimmed', l => {{
                const u = l.source.id || l.source;
                const v = l.target.id || l.target;
                return u !== d.id && v !== d.id;
            }});
            link.classed('highlight', l => {{
                const u = l.source.id || l.source;
                const v = l.target.id || l.target;
                return u === d.id || v === d.id;
            }});

            document.getElementById('inspector-name').textContent = d.label || d.id;
            const badge = document.getElementById('inspector-badge');
            badge.style.display = 'inline-block';
            badge.textContent = `Cluster ${{d.community || 1}}`;
            badge.style.borderColor = getNodeColor(d.community);
            badge.style.color = getNodeColor(d.community);

            document.getElementById('inspector-metrics').style.display = 'grid';
            document.getElementById('m-freq').textContent = d.frequency || 1;
            document.getElementById('m-deg').textContent = d.degree_weighted || (d.frequency ? (d.frequency * 1.5).toFixed(2) : '-');
            document.getElementById('m-pr').textContent = d.pagerank ? d.pagerank.toFixed(4) : '-';
            document.getElementById('m-bet').textContent = d.betweenness ? d.betweenness.toFixed(4) : '-';
        }});

        node.on('mouseleave', () => {{
            node.classed('dimmed', false);
            link.classed('dimmed', false);
            link.classed('highlight', false);
        }});

        document.getElementById('search-input').addEventListener('input', (e) => {{
            const term = e.target.value.toLowerCase().trim();
            if (!term) {{
                node.classed('dimmed', false);
                return;
            }}
            node.classed('dimmed', d => !d.label.toLowerCase().includes(term));
        }});

        document.getElementById('btn-export-svg').addEventListener('click', () => {{
            const svgEl = document.getElementById('network-svg');
            const serializer = new XMLSerializer();
            const source = serializer.serializeToString(svgEl);
            const blob = new Blob([source], {{ type: 'image/svg+xml;charset=utf-8' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = '{title.lower().replace(" ", "_")}_knomap.svg';
            a.click();
            URL.revokeObjectURL(url);
        }});
    </script>
</body>
</html>"""
    return html


def generate_vosviewer_html(
    vos_data: Dict[str, Any],
    title: str = "VOSviewer Map",
    subtitle: Optional[str] = None
) -> str:
    """Generates a standalone, beautiful HTML visualizer reproducing the VOSviewer experience (Network, Overlay & Density)."""
    vos_json_str = json.dumps(vos_data, ensure_ascii=False)
    sub_text = subtitle or "VOSviewer Engine - Network, Overlay & Density Visualizations"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - VOSviewer Map</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-base: #050508;
            --bg-panel: rgba(17, 24, 39, 0.92);
            --border-panel: rgba(255, 255, 255, 0.1);
            --accent-primary: #6366f1;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: var(--bg-base);
            color: var(--text-main);
            font-family: 'Inter', sans-serif;
            overflow: hidden;
            width: 100vw;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        header {{
            height: 54px;
            background: var(--bg-panel);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-panel);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 18px;
            z-index: 20;
        }}
        .brand {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .brand-badge {{
            background: linear-gradient(135deg, #4f46e5, #06b6d4);
            color: #fff;
            font-weight: 700;
            font-size: 11px;
            padding: 4px 8px;
            border-radius: 6px;
            letter-spacing: 0.05em;
        }}
        .brand-title {{
            font-size: 14px;
            font-weight: 700;
            color: #fff;
        }}
        .brand-sub {{
            font-size: 11px;
            color: var(--text-muted);
            margin-left: 6px;
        }}
        .mode-tabs {{
            display: flex;
            background: rgba(3, 7, 18, 0.7);
            border: 1px solid var(--border-panel);
            border-radius: 8px;
            padding: 3px;
            gap: 2px;
        }}
        .mode-btn {{
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 5px 12px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .mode-btn.active {{
            background: var(--accent-primary);
            color: #fff;
            box-shadow: 0 0 10px rgba(99, 102, 241, 0.5);
        }}
        .mode-btn:hover:not(.active) {{
            color: #fff;
            background: rgba(255, 255, 255, 0.05);
        }}
        .header-actions {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .action-btn {{
            background: rgba(31, 41, 55, 0.8);
            border: 1px solid var(--border-panel);
            color: #e5e7eb;
            font-size: 11px;
            font-weight: 600;
            padding: 5px 10px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            text-decoration: none;
        }}
        .action-btn:hover {{
            background: #374151;
            color: #fff;
            border-color: var(--accent-primary);
        }}
        main {{
            flex: 1;
            position: relative;
            overflow: hidden;
        }}
        canvas {{
            display: block;
            width: 100%;
            height: 100%;
            cursor: grab;
        }}
        canvas:active {{
            cursor: grabbing;
        }}
        .search-panel {{
            position: absolute;
            top: 14px;
            left: 14px;
            background: var(--bg-panel);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-panel);
            border-radius: 10px;
            padding: 10px 14px;
            z-index: 10;
            display: flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 6px 24px rgba(0,0,0,0.4);
        }}
        .search-input {{
            background: #030712;
            border: 1px solid var(--border-panel);
            border-radius: 6px;
            padding: 5px 10px;
            font-size: 12px;
            color: #fff;
            width: 180px;
            outline: none;
        }}
        .search-input:focus {{
            border-color: var(--accent-primary);
        }}
        .inspector-panel {{
            position: absolute;
            bottom: 18px;
            right: 18px;
            width: 280px;
            background: var(--bg-panel);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-panel);
            border-radius: 10px;
            padding: 14px;
            z-index: 10;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .inspector-title {{
            font-size: 13px;
            font-weight: 700;
            color: #fff;
        }}
        .meta-row {{
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            color: var(--text-muted);
            border-bottom: 1px solid rgba(255,255,255,0.05);
            padding-bottom: 4px;
        }}
        .meta-val {{
            font-weight: 600;
            color: #fff;
            font-family: 'JetBrains Mono', monospace;
        }}
        .overlay-colorbar {{
            position: absolute;
            bottom: 18px;
            left: 18px;
            background: var(--bg-panel);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-panel);
            border-radius: 8px;
            padding: 8px 14px;
            z-index: 10;
            display: none;
            flex-direction: column;
            gap: 4px;
        }}
        .colorbar-gradient {{
            width: 160px;
            height: 10px;
            border-radius: 4px;
            background: linear-gradient(to right, #440154, #3b528b, #21918c, #5ec962, #fde725);
        }}
        .colorbar-labels {{
            display: flex;
            justify-content: space-between;
            font-size: 9px;
            color: var(--text-muted);
            font-family: 'JetBrains Mono', monospace;
        }}
    </style>
</head>
<body>
    <header>
        <div class="brand">
            <span class="brand-badge">VOSviewer Engine</span>
            <span class="brand-title">{title}</span>
            <span class="brand-sub">{sub_text}</span>
        </div>
        
        <div class="mode-tabs">
            <button class="mode-btn active" id="tab-net" onclick="setVisualMode('network')">● Red (Network)</button>
            <button class="mode-btn" id="tab-overlay" onclick="setVisualMode('overlay')">◐ Superposición (Overlay)</button>
            <button class="mode-btn" id="tab-density" onclick="setVisualMode('density')">◎ Densidad (Density)</button>
        </div>

        <div class="header-actions">
            <button class="action-btn" id="btn-dl-json">Descargar vosviewer.json</button>
            <a href="https://app.vosviewer.com" target="_blank" class="action-btn" style="color:#a5b4fc; border-color:#6366f1;">Abrir VOSviewer Online ↗</a>
        </div>
    </header>

    <main id="canvas-container">
        <div class="search-panel">
            <input type="text" id="search-box" class="search-input" placeholder="Buscar elemento en mapa...">
            <span id="match-count" style="font-size:11px; color:var(--text-muted);"></span>
        </div>

        <div class="inspector-panel" id="inspector">
            <div style="font-size:10px; color:var(--text-muted); text-transform:uppercase; font-weight:600;">Elemento Seleccionado</div>
            <div class="inspector-title" id="insp-name">Pase el cursor sobre un nodo</div>
            <div id="insp-meta" style="display:none; flex-direction:column; gap:6px;">
                <div class="meta-row"><span>Cluster:</span><span class="meta-val" id="insp-cluster">-</span></div>
                <div class="meta-row"><span>Ocurrencias:</span><span class="meta-val" id="insp-occ">-</span></div>
                <div class="meta-row"><span>Total Link Strength:</span><span class="meta-val" id="insp-tls">-</span></div>
                <div class="meta-row"><span>Enlaces (Links):</span><span class="meta-val" id="insp-links">-</span></div>
                <div class="meta-row" id="row-score" style="display:none;"><span>Puntuación:</span><span class="meta-val" id="insp-score">-</span></div>
            </div>
        </div>

        <div class="overlay-colorbar" id="colorbar">
            <div style="font-size:9px; color:var(--text-muted); text-transform:uppercase; font-weight:600;">Puntuación de Superposición</div>
            <div class="colorbar-gradient"></div>
            <div class="colorbar-labels">
                <span id="cb-min">0.00</span>
                <span id="cb-max">1.00</span>
            </div>
        </div>

        <canvas id="vos-canvas"></canvas>
    </main>

    <script>
        const vosData = {vos_json_str};
        const items = vosData.network.items;
        const links = vosData.network.links;

        let visualMode = 'network';
        let hoveredItem = null;
        let searchTerm = '';

        const clusterColors = [
            '#e11d48', '#2563eb', '#16a34a', '#d97706', '#9333ea',
            '#0891b2', '#ea580c', '#4f46e5', '#059669', '#ca8a04'
        ];
        function getItemColor(cluster) {{
            const c = (parseInt(cluster) || 1) - 1;
            return clusterColors[Math.abs(c) % clusterColors.length];
        }}

        function viridis(t) {{
            const r = Math.round(255 * Math.sin(t * Math.PI / 2));
            const g = Math.round(255 * (t < 0.5 ? 2 * t * 0.8 : 0.8 + 0.2 * (2 * t - 1)));
            const b = Math.round(255 * Math.cos(t * Math.PI / 2));
            return `rgb(${{r}}, ${{g}}, ${{b}})`;
        }}

        const canvas = document.getElementById('vos-canvas');
        const width = window.innerWidth;
        const height = window.innerHeight - 54;
        canvas.width = width * window.devicePixelRatio;
        canvas.height = height * window.devicePixelRatio;
        const ctx = canvas.getContext('2d');
        ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

        const nItems = items.length;
        const itemMap = new Map();
        
        let minScore = Infinity, maxScore = -Infinity;
        items.forEach((it) => {{
            const sc = (it.scores && Object.values(it.scores)[0]) || it.weights.Occurrences;
            if (sc < minScore) minScore = sc;
            if (sc > maxScore) maxScore = sc;
        }});
        if (minScore === maxScore) {{ minScore = 0; maxScore = 1; }}
        document.getElementById('cb-min').textContent = minScore.toFixed(3);
        document.getElementById('cb-max').textContent = maxScore.toFixed(3);

        const clusters = Array.from(new Set(items.map(it => it.cluster)));
        const clusterCenters = {{}};
        clusters.forEach((cid, idx) => {{
            const angle = (idx / clusters.length) * 2 * Math.PI;
            const dist = Math.min(width, height) * 0.28;
            clusterCenters[cid] = {{
                x: width / 2 + Math.cos(angle) * dist,
                y: height / 2 + Math.sin(angle) * dist
            }};
        }});

        items.forEach((it) => {{
            const center = clusterCenters[it.cluster] || {{ x: width / 2, y: height / 2 }};
            const angle = Math.random() * 2 * Math.PI;
            const r = Math.random() * (Math.min(width, height) * 0.14);
            it.x = center.x + Math.cos(angle) * r;
            it.y = center.y + Math.sin(angle) * r;
            it.radius = Math.max(5, Math.min(22, Math.sqrt(it.weights.Occurrences || 1) * 4 + 4));
            itemMap.set(it.id, it);
        }});

        for (let step = 0; step < 80; step++) {{
            links.forEach(l => {{
                const u = itemMap.get(l.source_id);
                const v = itemMap.get(l.target_id);
                if (u && v) {{
                    const dx = v.x - u.x;
                    const dy = v.y - u.y;
                    const d = Math.sqrt(dx * dx + dy * dy) || 1;
                    const force = (d - 70) * 0.015 * (l.strength || 1);
                    u.x += (dx / d) * force;
                    u.y += (dy / d) * force;
                    v.x -= (dx / d) * force;
                    v.y -= (dy / d) * force;
                }}
            }});
            for (let i = 0; i < nItems; i++) {{
                for (let j = i + 1; j < nItems; j++) {{
                    const u = items[i];
                    const v = items[j];
                    const dx = v.x - u.x;
                    const dy = v.y - u.y;
                    const d = Math.sqrt(dx * dx + dy * dy) || 1;
                    const minD = u.radius + v.radius + 15;
                    if (d < minD) {{
                        const rep = (minD - d) * 0.1;
                        u.x -= (dx / d) * rep;
                        u.y -= (dy / d) * rep;
                        v.x += (dx / d) * rep;
                        v.y += (dy / d) * rep;
                    }}
                }}
            }}
        }}

        function render() {{
            ctx.clearRect(0, 0, width, height);
            if (visualMode === 'density') {{
                renderDensity();
            }} else {{
                renderLinks();
                renderNodes();
            }}
        }}

        function renderLinks() {{
            ctx.save();
            links.forEach(l => {{
                const u = itemMap.get(l.source_id);
                const v = itemMap.get(l.target_id);
                if (!u || !v) return;

                const isConnectedToHover = hoveredItem && (hoveredItem.id === u.id || hoveredItem.id === v.id);
                ctx.beginPath();
                ctx.moveTo(u.x, u.y);
                ctx.lineTo(v.x, v.y);
                
                if (hoveredItem) {{
                    ctx.strokeStyle = isConnectedToHover ? '#a5b4fc' : 'rgba(255,255,255,0.03)';
                    ctx.lineWidth = isConnectedToHover ? 2.5 : 0.5;
                }} else {{
                    ctx.strokeStyle = 'rgba(99, 102, 241, 0.22)';
                    ctx.lineWidth = Math.max(0.8, Math.min(4, (l.strength || 1) * 1.5));
                }}
                ctx.stroke();
            }});
            ctx.restore();
        }}

        function renderNodes() {{
            items.forEach(it => {{
                const isHovered = hoveredItem && hoveredItem.id === it.id;
                const matchesSearch = searchTerm && it.label.toLowerCase().includes(searchTerm);
                
                let nodeColor;
                if (visualMode === 'overlay') {{
                    const sc = (it.scores && Object.values(it.scores)[0]) || it.weights.Occurrences;
                    const t = Math.max(0, Math.min(1, (sc - minScore) / (maxScore - minScore)));
                    nodeColor = viridis(t);
                }} else {{
                    nodeColor = getItemColor(it.cluster);
                }}

                ctx.save();
                ctx.beginPath();
                ctx.arc(it.x, it.y, isHovered ? it.radius * 1.35 : it.radius, 0, 2 * Math.PI);
                ctx.fillStyle = nodeColor;
                ctx.shadowColor = nodeColor;
                ctx.shadowBlur = (isHovered || matchesSearch) ? 14 : 0;
                ctx.fill();
                ctx.strokeStyle = isHovered ? '#fff' : 'rgba(255,255,255,0.7)';
                ctx.lineWidth = isHovered ? 2.5 : 1.2;
                ctx.stroke();
                ctx.restore();

                ctx.save();
                ctx.font = `${{isHovered ? 'bold 12px' : '10px'}} 'Inter', sans-serif`;
                ctx.fillStyle = isHovered ? '#fff' : '#e5e7eb';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'bottom';
                ctx.shadowColor = '#000';
                ctx.shadowBlur = 4;
                ctx.fillText(it.label, it.x, it.y - it.radius - 3);
                ctx.restore();
            }});
        }}

        function renderDensity() {{
            const step = 8;
            const sigma = 45;
            const twoSigmaSq = 2 * sigma * sigma;

            for (let x = 0; x < width; x += step) {{
                for (let y = 0; y < height; y += step) {{
                    let density = 0;
                    items.forEach(it => {{
                        const dx = x - it.x;
                        const dy = y - it.y;
                        const dSq = dx * dx + dy * dy;
                        density += (it.weights.Occurrences || 1) * Math.exp(-dSq / twoSigmaSq);
                    }});

                    if (density > 0.05) {{
                        const normD = Math.min(1, density / 12);
                        const r = Math.round(255 * Math.max(0, Math.min(1, (normD - 0.5) * 2)));
                        const g = Math.round(255 * Math.max(0, Math.min(1, 1 - Math.abs(normD - 0.5) * 2)));
                        const b = Math.round(255 * Math.max(0, Math.min(1, (0.5 - normD) * 2)));
                        
                        ctx.fillStyle = `rgba(${{r}}, ${{g}}, ${{b}}, ${{normD * 0.75}})`;
                        ctx.fillRect(x, y, step, step);
                    }}
                }}
            }}

            items.forEach(it => {{
                ctx.save();
                ctx.beginPath();
                ctx.arc(it.x, it.y, 3, 0, 2 * Math.PI);
                ctx.fillStyle = '#fff';
                ctx.fill();
                ctx.font = "9px 'Inter', sans-serif";
                ctx.fillStyle = 'rgba(255,255,255,0.85)';
                ctx.textAlign = 'center';
                ctx.fillText(it.label, it.x, it.y - 6);
                ctx.restore();
            }});
        }}

        window.setVisualMode = function(mode) {{
            visualMode = mode;
            document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
            if (mode === 'network') document.getElementById('tab-net').classList.add('active');
            if (mode === 'overlay') document.getElementById('tab-overlay').classList.add('active');
            if (mode === 'density') document.getElementById('tab-density').classList.add('active');

            document.getElementById('colorbar').style.display = (mode === 'overlay') ? 'flex' : 'none';
            render();
        }};

        canvas.addEventListener('mousemove', (e) => {{
            const rect = canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;

            let found = null;
            for (const it of items) {{
                const dx = mouseX - it.x;
                const dy = mouseY - it.y;
                if (dx * dx + dy * dy <= it.radius * it.radius * 1.5) {{
                    found = it;
                    break;
                }}
            }}

            if (found !== hoveredItem) {{
                hoveredItem = found;
                if (hoveredItem) {{
                    document.getElementById('insp-name').textContent = hoveredItem.label;
                    document.getElementById('insp-meta').style.display = 'flex';
                    document.getElementById('insp-cluster').textContent = hoveredItem.cluster;
                    document.getElementById('insp-occ').textContent = hoveredItem.weights.Occurrences;
                    document.getElementById('insp-tls').textContent = hoveredItem.weights['Total link strength'] || '-';
                    document.getElementById('insp-links').textContent = hoveredItem.weights.Links || '-';
                    
                    if (hoveredItem.scores && Object.keys(hoveredItem.scores).length > 0) {{
                        document.getElementById('row-score').style.display = 'flex';
                        const scKey = Object.keys(hoveredItem.scores)[0];
                        document.getElementById('insp-score').textContent = hoveredItem.scores[scKey];
                    }} else {{
                        document.getElementById('row-score').style.display = 'none';
                    }}
                }} else {{
                    document.getElementById('insp-name').textContent = 'Pase el cursor sobre un nodo';
                    document.getElementById('insp-meta').style.display = 'none';
                }}
                render();
            }}
        }});

        document.getElementById('search-box').addEventListener('input', (e) => {{
            searchTerm = e.target.value.toLowerCase().trim();
            const count = searchTerm ? items.filter(it => it.label.toLowerCase().includes(searchTerm)).length : 0;
            document.getElementById('match-count').textContent = searchTerm ? `${{count}} coincidencias` : '';
            render();
        }});

        document.getElementById('btn-dl-json').addEventListener('click', () => {{
            const blob = new Blob([JSON.stringify(vosData, null, 2)], {{ type: 'application/json' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'vosviewer.json';
            a.click();
            URL.revokeObjectURL(url);
        }});

        render();
    </script>
</body>
</html>"""
    return html


def export_som_matrix(
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    output_csv: str,
    output_json: Optional[str] = None
) -> int:
    """
    Exports the N x N symmetric co-occurrence/adjacency matrix formatted for
    direct ingestion into SOM (som-methodological-expert).
    """
    labels = sorted([n["label"] for n in nodes])
    n_items = len(labels)
    label_to_idx = {lbl: i for i, lbl in enumerate(labels)}

    mat = [[0.0] * n_items for _ in range(n_items)]
    freq_map = {n["label"]: float(n.get("frequency", 1.0)) for n in nodes}

    for lbl, i in label_to_idx.items():
        mat[i][i] = freq_map.get(lbl, 1.0)

    for e in edges:
        u = e["source"]
        v = e["target"]
        w = float(e.get("weight", 1.0))
        if u in label_to_idx and v in label_to_idx:
            i = label_to_idx[u]
            j = label_to_idx[v]
            mat[i][j] = round(w, 4)
            mat[j][i] = round(w, 4)

    os.makedirs(os.path.dirname(os.path.abspath(output_csv)), exist_ok=True)
    with open(output_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Entity"] + labels)
        for i, lbl in enumerate(labels):
            writer.writerow([lbl] + [round(val, 4) for val in mat[i]])

    if output_json:
        os.makedirs(os.path.dirname(os.path.abspath(output_json)), exist_ok=True)
        meta = {
            "originType": "bibliometrics",
            "unitName": "Bibliometrics Co-occurrence",
            "description": "Adjacency/Association Strength matrix for Kohonen Self-Organizing Map",
            "dimension": [n_items, n_items],
            "labels": labels,
            "matrix": mat
        }
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

    return n_items


def export_network_graph(
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    output_path: str,
    fmt: str = "gexf"
):
    """Exports graph to GEXF, Pajek (.net), or canonical VOSviewer JSON."""
    G = nx.Graph()
    for n in nodes:
        attrs = {k: v for k, v in n.items() if k != "id"}
        G.add_node(n["id"], **attrs)
    for e in edges:
        G.add_edge(e["source"], e["target"], weight=float(e.get("weight", 1.0)))

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    if fmt == "gexf":
        nx.write_gexf(G, output_path)
    elif fmt == "pajek":
        nx.write_pajek(G, output_path)
    else:
        # VOSviewer JSON format
        vos_data = build_vosviewer_json_data(nodes, edges)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(vos_data, f, indent=2, ensure_ascii=False)


def cmd_build(args):
    """Builds a bibliometric network from a corpus, with optional period filtering."""
    input_path = args.input
    if not os.path.exists(input_path):
        sys.stderr.write(f"Error: Input file does not exist: {input_path}\n")
        sys.exit(1)

    unit = args.unit
    net_type = args.network_type
    counting = args.counting
    min_freq = args.min_freq or 2
    min_cooccur = args.min_cooccur or 1.0
    norm_method = args.normalization

    docs = load_corpus_items(input_path, unit)
    if not docs:
        sys.stderr.write(f"Error: No items extracted for unit '{unit}'\n")
        sys.exit(1)

    # Apply temporal filter if requested
    docs, period_meta = filter_docs_by_period(
        docs,
        year_from=args.year_from,
        year_to=args.year_to,
        period=args.period,
        last_years=args.last_years
    )
    if not docs:
        sys.stderr.write(f"Error: No documents match the specified temporal filter ({period_meta})\n")
        sys.exit(1)

    if net_type in ["cooccurrence", "coauthorship"]:
        items, pairs, freqs = build_cooccurrence_matrix(docs, counting, min_freq, min_cooccur)
    elif net_type == "coupling":
        items, pairs, freqs = build_bib_coupling_matrix(docs, unit, min_freq, min_cooccur)
    else:
        items, pairs, freqs = build_cooccurrence_matrix(docs, counting, min_freq, min_cooccur)

    # Optional max-terms filter
    if args.max_terms and args.max_terms > 0 and len(items) > args.max_terms:
        sorted_items = sorted(items, key=lambda it: freqs.get(it, 0.0), reverse=True)[:args.max_terms]
        active_set = set(sorted_items)
        pairs = {p: w for p, w in pairs.items() if p[0] in active_set and p[1] in active_set}
        items = sorted(sorted_items)

    norm_pairs = normalize_weights(pairs, freqs, norm_method)

    # Format into graph structure
    nodes = [{"id": item, "label": item, "frequency": freqs.get(item, 0.0)} for item in items if any(item in p for p in norm_pairs)]
    edges = [{"source": u, "target": v, "weight": w, "raw_cooccur": pairs.get((u, v), w)} for (u, v), w in norm_pairs.items()]

    # Auto-analysis (communities and centralities) if requested or when exporting visualizers
    needs_analysis = (
        getattr(args, "auto_analyze", False)
        or getattr(args, "html_knomap", None)
        or getattr(args, "html_vosviewer", None)
        or getattr(args, "vosviewer_json", None)
        or getattr(args, "som_matrix", None)
    )
    if needs_analysis and len(nodes) > 0:
        comms, node_to_comm = detect_network_communities(nodes, edges, "leiden", 1.0)
        for n in nodes:
            n["community"] = node_to_comm.get(n["id"], 1)

        centralities = compute_network_centralities(nodes, edges)
        c_map = {c["id"]: c for c in centralities}
        for n in nodes:
            c_info = c_map.get(n["id"], {})
            n["degree_weighted"] = c_info.get("degree_weighted", 0.0)
            n["betweenness"] = c_info.get("betweenness", 0.0)
            n["pagerank"] = c_info.get("pagerank", 0.0)

    graph_data = {
        "network_type": net_type,
        "unit": unit,
        "counting": counting,
        "normalization": norm_method,
        "period": period_meta,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(graph_data, f, indent=2, ensure_ascii=False)

    p_str = f" [Period: {period_meta.get('label')}]" if period_meta.get("filter_applied") else ""
    print(f"Built network ({net_type}, {unit}){p_str}: {len(nodes)} nodes, {len(edges)} edges. Output: {args.output}")

    # Generate visualizers if requested
    if getattr(args, "html_knomap", None):
        title = f"{unit.capitalize()} {net_type.capitalize()} Network"
        p_sub = f"Period: {period_meta.get('label')}" if period_meta.get("filter_applied") else "KnoMap Force-Directed Network"
        html_code = generate_knomap_force_html(nodes, edges, title=title, subtitle=p_sub)
        os.makedirs(os.path.dirname(os.path.abspath(args.html_knomap)), exist_ok=True)
        with open(args.html_knomap, "w", encoding="utf-8") as f:
            f.write(html_code)
        print(f"Generated KnoMap Force Graph HTML: {args.html_knomap}")

    if getattr(args, "vosviewer_json", None) or getattr(args, "html_vosviewer", None):
        vos_data = build_vosviewer_json_data(nodes, edges)
        if getattr(args, "vosviewer_json", None):
            os.makedirs(os.path.dirname(os.path.abspath(args.vosviewer_json)), exist_ok=True)
            with open(args.vosviewer_json, "w", encoding="utf-8") as f:
                json.dump(vos_data, f, indent=2, ensure_ascii=False)
            print(f"Exported VOSviewer JSON: {args.vosviewer_json}")
        if getattr(args, "html_vosviewer", None):
            title = f"{unit.capitalize()} {net_type.capitalize()} VOS Map"
            p_sub = f"Period: {period_meta.get('label')}" if period_meta.get("filter_applied") else None
            html_vos = generate_vosviewer_html(vos_data, title=title, subtitle=p_sub)
            os.makedirs(os.path.dirname(os.path.abspath(args.html_vosviewer)), exist_ok=True)
            with open(args.html_vosviewer, "w", encoding="utf-8") as f:
                f.write(html_vos)
            print(f"Generated VOSviewer HTML: {args.html_vosviewer}")

    if getattr(args, "som_matrix", None):
        n_dim = export_som_matrix(nodes, edges, output_csv=args.som_matrix)
        print(f"Exported SOM Adjacency Matrix ({n_dim}x{n_dim}) for SOM training: {args.som_matrix}")

    sys.exit(0)


def cmd_sequential(args):
    """
    Generates sequential longitudinal bibliometric networks across consecutive or sliding windows.
    Outputs individual period network JSONs and a sequence_manifest.json ready for Warm-Start SOM.
    """
    input_path = args.input
    if not os.path.exists(input_path):
        sys.stderr.write(f"Error: Input corpus file does not exist: {input_path}\n")
        sys.exit(1)

    unit = args.unit
    net_type = args.network_type
    counting = args.counting
    min_freq = args.min_freq or 2
    min_cooccur = args.min_cooccur or 1.0
    norm_method = args.normalization
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    docs = load_corpus_items(input_path, unit)
    if not docs:
        sys.stderr.write(f"Error: No records extracted for unit '{unit}' from {input_path}\n")
        sys.exit(1)

    # 1. Determine period windows
    if args.periods:
        windows = [parse_period_string(p) for p in args.periods.split(",") if p.strip()]
    else:
        all_years = [d["year"] for d in docs if d.get("year") is not None]
        if not all_years:
            sys.stderr.write("Error: Cannot construct sequential networks without valid publication years in corpus.\n")
            sys.exit(1)
        windows = generate_period_windows(all_years, window_size=args.window, step_size=args.step)

    if not windows:
        sys.stderr.write("Error: No temporal windows generated from corpus years.\n")
        sys.exit(1)

    # 2. Extract canonical shared vocabulary across corpus
    # Global frequencies for the selected unit
    global_counts = Counter()
    for d in docs:
        for it in d["items"]:
            global_counts[it] += 1

    valid_vocab = [it for it, c in global_counts.items() if c >= min_freq]
    if not valid_vocab:
        sys.stderr.write(f"Error: No terms met the minimum frequency threshold (--min-freq {min_freq}).\n")
        sys.exit(1)

    if args.max_terms and args.max_terms > 0 and len(valid_vocab) > args.max_terms:
        # Pick top max_terms by global prominence
        top_terms = sorted(valid_vocab, key=lambda it: global_counts[it], reverse=True)[:args.max_terms]
        vocabulary = sorted(top_terms)
    else:
        vocabulary = sorted(valid_vocab)

    vocab_set = set(vocabulary)
    M = len(vocabulary)

    print(f"Loaded {len(docs)} documents. Generated {len(windows)} period window(s).")
    print(f"Canonical shared vocabulary size: {M} items (e.g. {vocabulary[:5]}...)")

    periods_summary = []
    periods_data = {}

    for label, start_yr, end_yr in windows:
        period_slug = label.replace("-", "_").replace(" ", "_")
        period_docs = [
            d for d in docs
            if d.get("year") is not None and start_yr <= d["year"] <= end_yr
        ]

        if not period_docs:
            print(f"  - [{label}]: 0 documents found. Skipping empty period.")
            continue

        # Restrict period docs to shared vocabulary
        restricted_docs = []
        for d in period_docs:
            r_items = [it for it in d["items"] if it in vocab_set]
            restricted_docs.append({
                "id": d["id"],
                "items": r_items,
                "references": d["references"],
                "year": d["year"]
            })

        # Build co-occurrence matrix for period
        items, pairs, freqs = build_cooccurrence_matrix(
            restricted_docs,
            counting,
            min_freq=1,
            min_cooccur=min_cooccur
        )

        norm_pairs = normalize_weights(pairs, freqs, norm_method)

        nodes = [
            {"id": it, "label": it, "frequency": freqs.get(it, 0.0)}
            for it in vocabulary if freqs.get(it, 0.0) > 0
        ]
        edges = [
            {"source": u, "target": v, "weight": w, "raw_cooccur": pairs.get((u, v), w)}
            for (u, v), w in norm_pairs.items()
        ]

        # Detect communities for period
        comms, node_to_comm = detect_network_communities(
            nodes, edges,
            algorithm=args.algorithm,
            resolution=args.resolution
        )
        for n in nodes:
            n["community"] = node_to_comm.get(n["id"], 0)

        # Centralities
        centralities = compute_network_centralities(nodes, edges)
        node_centrality_map = {c["id"]: c for c in centralities}
        for n in nodes:
            c_info = node_centrality_map.get(n["id"], {})
            n["degree_weighted"] = c_info.get("degree_weighted", 0.0)
            n["betweenness"] = c_info.get("betweenness", 0.0)
            n["pagerank"] = c_info.get("pagerank", 0.0)

        # Build aligned M x M matrix for longitudinal SOM
        data_matrix = []
        for vi in vocabulary:
            row_vec = []
            f_i = freqs.get(vi, 0.0)
            for vj in vocabulary:
                if vi == vj:
                    row_vec.append(f_i)
                else:
                    pair = tuple(sorted([vi, vj]))
                    row_vec.append(norm_pairs.get(pair, 0.0))
            data_matrix.append(row_vec)

        # Save individual period network
        net_filename = f"network_{period_slug}.json"
        net_filepath = os.path.join(output_dir, net_filename)
        period_network_payload = {
            "period": {
                "label": label,
                "start_year": start_yr,
                "end_year": end_yr,
                "doc_count": len(period_docs),
                "active_nodes": len(nodes),
                "edge_count": len(edges)
            },
            "network_type": net_type,
            "unit": unit,
            "counting": counting,
            "normalization": norm_method,
            "communities_count": len(comms),
            "communities": comms,
            "nodes": nodes,
            "edges": edges
        }
        with open(net_filepath, "w", encoding="utf-8") as f:
            json.dump(period_network_payload, f, indent=2, ensure_ascii=False)

        # Extra format export if requested
        if args.format:
            ext = "gexf" if args.format == "gexf" else ("net" if args.format == "pajek" else "json")
            export_path = os.path.join(output_dir, f"network_{period_slug}.{ext}")
            export_network_graph(nodes, edges, export_path, fmt=args.format)

        periods_data[label] = {
            "data": data_matrix,
            "labels": vocabulary,
            "doc_count": len(period_docs),
            "start_year": start_yr,
            "end_year": end_yr,
            "active_nodes": len(nodes),
            "edge_count": len(edges)
        }

        density = round(2.0 * len(edges) / (len(nodes) * (len(nodes) - 1)), 4) if len(nodes) > 1 else 0.0
        periods_summary.append({
            "period": label,
            "start_year": start_yr,
            "end_year": end_yr,
            "doc_count": len(period_docs),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "density": density,
            "communities_count": len(comms),
            "network_file": net_filename
        })

        print(f"  ✓ [{label}]: {len(period_docs)} docs, {len(nodes)} active nodes, {len(edges)} edges, {len(comms)} communities -> {net_filename}")

    # Build sequence manifest
    manifest = {
        "corpus_path": input_path,
        "network_type": net_type,
        "unit": unit,
        "counting": counting,
        "normalization": norm_method,
        "total_periods": len(periods_summary),
        "periods": [p["period"] for p in periods_summary],
        "vocabulary_size": len(vocabulary),
        "vocabulary": vocabulary,
        "periods_summary": periods_summary,
        "indicators": vocabulary,
        "periods_data": periods_data
    }

    manifest_path = os.path.join(output_dir, "sequence_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\nSequential networks generation complete!")
    print(f"Manifest written to: {manifest_path}")
    print(f"Ready for Warm-Start Chaining with neural-longitudinal-mapping:\n  neural_longitudinal_cli.py train --input {manifest_path}")
    sys.exit(0)


def cmd_communities(args):
    """Detects communities using Leiden (default) or Louvain."""
    input_path = args.input
    if not os.path.exists(input_path):
        sys.stderr.write(f"Error: Input network file does not exist: {input_path}\n")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        net = json.load(f)

    nodes = net.get("nodes", [])
    edges = net.get("edges", [])
    algorithm = args.algorithm or "leiden"
    resolution = args.resolution or 1.0

    communities_list, node_to_comm = detect_network_communities(
        nodes, edges, algorithm=algorithm, resolution=resolution
    )

    for n in nodes:
        n["community"] = node_to_comm.get(n["id"], 0)

    output_data = {
        "algorithm": algorithm,
        "resolution": resolution,
        "total_communities": len(communities_list),
        "communities": communities_list,
        "nodes_with_community": nodes,
        "edges": edges
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Detected {len(communities_list)} communities via {algorithm} (resolution={resolution}). Saved to {args.output}")
    sys.exit(0)


def cmd_centralities(args):
    """Calculates Degree, Betweenness, and PageRank centralities."""
    input_path = args.input
    if not os.path.exists(input_path):
        sys.stderr.write(f"Error: Network file does not exist: {input_path}\n")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        net = json.load(f)

    nodes = net.get("nodes", net.get("nodes_with_community", []))
    edges = net.get("edges", [])

    ranked_nodes = compute_network_centralities(nodes, edges)

    output_data = {
        "node_count": len(ranked_nodes),
        "centralities": ranked_nodes
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Calculated centralities for {len(ranked_nodes)} nodes. Output: {args.output}")
    sys.exit(0)


def cmd_render_knomap(args):
    """Renders standalone KnoMap Force Graph HTML from a network JSON."""
    with open(args.input, "r", encoding="utf-8") as f:
        net = json.load(f)
    nodes = net.get("nodes", net.get("nodes_with_community", []))
    edges = net.get("edges", [])
    title = args.title or "Bibliometric Network"
    subtitle = args.subtitle or "KnoMap Interactive Force-Directed Graph"
    html_code = generate_knomap_force_html(nodes, edges, title=title, subtitle=subtitle)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html_code)
    print(f"Generated KnoMap Force Graph HTML: {args.output}")
    sys.exit(0)


def cmd_render_vosviewer(args):
    """Renders standalone VOSviewer HTML visualizer and optional JSON."""
    with open(args.input, "r", encoding="utf-8") as f:
        net = json.load(f)
    nodes = net.get("nodes", net.get("nodes_with_community", []))
    edges = net.get("edges", [])
    vos_data = build_vosviewer_json_data(nodes, edges)
    if args.output_json:
        os.makedirs(os.path.dirname(os.path.abspath(args.output_json)), exist_ok=True)
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(vos_data, f, indent=2, ensure_ascii=False)
        print(f"Exported VOSviewer JSON: {args.output_json}")
    title = args.title or "VOSviewer Map"
    subtitle = args.subtitle or "VOSviewer Engine - Network, Overlay & Density Visualizations"
    html_code = generate_vosviewer_html(vos_data, title=title, subtitle=subtitle)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html_code)
    print(f"Generated VOSviewer HTML visualizer: {args.output}")
    sys.exit(0)


def cmd_export_som_matrix(args):
    """Exports N x N adjacency/co-occurrence matrix for SOM training."""
    with open(args.input, "r", encoding="utf-8") as f:
        net = json.load(f)
    nodes = net.get("nodes", net.get("nodes_with_community", []))
    edges = net.get("edges", [])
    n_dim = export_som_matrix(nodes, edges, output_csv=args.output_csv, output_json=args.output_json)
    print(f"Exported SOM Adjacency Matrix ({n_dim}x{n_dim}) to CSV: {args.output_csv}")
    sys.exit(0)


def cmd_export(args):
    """Exports network to GEXF, Pajek (.net), or VOSviewer JSON."""
    input_path = args.input
    output_path = args.output
    fmt = args.format or "gexf"

    with open(input_path, "r", encoding="utf-8") as f:
        net = json.load(f)

    nodes = net.get("nodes", net.get("nodes_with_community", []))
    edges = net.get("edges", [])

    export_network_graph(nodes, edges, output_path, fmt=fmt)
    print(f"Exported graph to {fmt.upper()} format at {output_path}")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="CLI for Bibliometric Network Analyst")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: build-network
    p_bld = subparsers.add_parser("build-network", help="Build bibliometric network from corpus with optional period filter")
    p_bld.add_argument("--input", required=True, help="Path to corpus (.parquet, .csv, .json, .txt)")
    p_bld.add_argument("--output", required=True, help="Path to output network JSON")
    p_bld.add_argument("--network-type", choices=["cooccurrence", "coauthorship", "coupling", "direct-citation"], default="cooccurrence")
    p_bld.add_argument("--unit", choices=["keywords", "authors", "institutions", "countries", "sources"], default="keywords")
    p_bld.add_argument("--counting", choices=["full", "fractional"], default="full")
    p_bld.add_argument("--normalization", choices=["association-strength", "salton", "jaccard", "none"], default="association-strength")
    p_bld.add_argument("--min-freq", type=int, default=2)
    p_bld.add_argument("--min-cooccur", type=float, default=1.0)
    p_bld.add_argument("--year-from", type=int, default=None, help="Start year (inclusive)")
    p_bld.add_argument("--year-to", type=int, default=None, help="End year (inclusive)")
    p_bld.add_argument("--period", type=str, default=None, help="Specific period (e.g. 2020-2024 or 2024)")
    p_bld.add_argument("--last-years", type=int, default=None, help="Filter last N years relative to corpus max year")
    p_bld.add_argument("--max-terms", type=int, default=None, help="Limit network to top N prominent terms")
    p_bld.add_argument("--auto-analyze", action="store_true", help="Automatically run Leiden communities and centralities")
    p_bld.add_argument("--html-knomap", type=str, default=None, help="Path to output standalone KnoMap Force Graph HTML")
    p_bld.add_argument("--html-vosviewer", type=str, default=None, help="Path to output standalone VOSviewer HTML visualizer")
    p_bld.add_argument("--vosviewer-json", type=str, default=None, help="Path to output canonical VOSviewer JSON format")
    p_bld.add_argument("--som-matrix", type=str, default=None, help="Path to output N x N co-occurrence matrix CSV for SOM training")
    p_bld.set_defaults(func=cmd_build)

    # Subcommand: render-knomap
    p_rkn = subparsers.add_parser("render-knomap", help="Render standalone KnoMap Force Graph HTML from network JSON")
    p_rkn.add_argument("--input", required=True, help="Path to network JSON")
    p_rkn.add_argument("--output", required=True, help="Path to output HTML file")
    p_rkn.add_argument("--title", default=None, help="Visualizer title")
    p_rkn.add_argument("--subtitle", default=None, help="Visualizer subtitle")
    p_rkn.set_defaults(func=cmd_render_knomap)

    # Subcommand: render-vosviewer
    p_rvos = subparsers.add_parser("render-vosviewer", help="Render standalone VOSviewer HTML visualizer from network JSON")
    p_rvos.add_argument("--input", required=True, help="Path to network JSON")
    p_rvos.add_argument("--output", required=True, help="Path to output HTML file")
    p_rvos.add_argument("--output-json", default=None, help="Optional path to output vosviewer.json")
    p_rvos.add_argument("--title", default=None, help="Visualizer title")
    p_rvos.add_argument("--subtitle", default=None, help="Visualizer subtitle")
    p_rvos.set_defaults(func=cmd_render_vosviewer)

    # Subcommand: export-som-matrix
    p_esom = subparsers.add_parser("export-som-matrix", help="Export N x N adjacency/co-occurrence matrix for SOM training")
    p_esom.add_argument("--input", required=True, help="Path to network JSON")
    p_esom.add_argument("--output-csv", required=True, help="Path to output N x N CSV file")
    p_esom.add_argument("--output-json", default=None, help="Optional path to output sidecar JSON")
    p_esom.set_defaults(func=cmd_export_som_matrix)

    # Subcommand: sequential-networks (alias period-networks)
    for sub_name in ["sequential-networks", "period-networks"]:
        p_seq = subparsers.add_parser(sub_name, help="Generate sequential longitudinal networks & SOM manifest")
        p_seq.add_argument("--input", required=True, help="Path to corpus (.parquet, .csv, .json, .txt)")
        p_seq.add_argument("--output-dir", required=True, help="Output directory for period networks and sequence_manifest.json")
        p_seq.add_argument("--network-type", choices=["cooccurrence", "coauthorship", "coupling", "direct-citation"], default="cooccurrence")
        p_seq.add_argument("--unit", choices=["keywords", "authors", "institutions", "countries", "sources"], default="keywords")
        p_seq.add_argument("--counting", choices=["full", "fractional"], default="full")
        p_seq.add_argument("--normalization", choices=["association-strength", "salton", "jaccard", "none"], default="association-strength")
        p_seq.add_argument("--min-freq", type=int, default=2, help="Minimum global term frequency")
        p_seq.add_argument("--min-cooccur", type=float, default=1.0, help="Minimum pair co-occurrence weight")
        p_seq.add_argument("--window", type=int, default=5, help="Window size in years (e.g. 5 or 10)")
        p_seq.add_argument("--step", type=int, default=None, help="Step size in years (default: same as window)")
        p_seq.add_argument("--periods", type=str, default=None, help="Explicit periods list (e.g. '2000-2009,2010-2019')")
        p_seq.add_argument("--max-terms", type=int, default=50, help="Size of shared persistent vocabulary (default: 50)")
        p_seq.add_argument("--algorithm", choices=["leiden", "louvain"], default="leiden", help="Community detection algorithm")
        p_seq.add_argument("--resolution", type=float, default=1.0, help="Community resolution parameter")
        p_seq.add_argument("--format", choices=["gexf", "pajek", "vosviewer-json"], default=None, help="Optional external format export per period")
        p_seq.set_defaults(func=cmd_sequential)

    # Subcommand: detect-communities
    p_com = subparsers.add_parser("detect-communities", help="Detect communities with Leiden/Louvain")
    p_com.add_argument("--input", required=True, help="Path to network JSON")
    p_com.add_argument("--output", required=True, help="Path to output communities JSON")
    p_com.add_argument("--algorithm", choices=["leiden", "louvain"], default="leiden")
    p_com.add_argument("--resolution", type=float, default=1.0)
    p_com.set_defaults(func=cmd_communities)

    # Subcommand: calculate-centralities
    p_cen = subparsers.add_parser("calculate-centralities", help="Calculate Degree, Betweenness, PageRank")
    p_cen.add_argument("--input", required=True, help="Path to network JSON")
    p_cen.add_argument("--output", required=True, help="Path to output centralities JSON")
    p_cen.set_defaults(func=cmd_centralities)

    # Subcommand: export-graph
    p_exp = subparsers.add_parser("export-graph", help="Export network to GEXF, Pajek, or VOSviewer JSON")
    p_exp.add_argument("--input", required=True, help="Path to network JSON")
    p_exp.add_argument("--output", required=True, help="Path to output file (.gexf, .net, .json)")
    p_exp.add_argument("--format", choices=["gexf", "pajek", "vosviewer-json"], default="gexf")
    p_exp.set_defaults(func=cmd_export)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
