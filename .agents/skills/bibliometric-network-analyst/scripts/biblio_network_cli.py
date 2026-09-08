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
    return [ref.strip() for ref in str(raw_refs).split(";") if ref.strip()]


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


def export_network_graph(
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    output_path: str,
    fmt: str = "gexf"
):
    """Exports graph to GEXF, Pajek (.net), or VOSviewer JSON."""
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
        vos_items = []
        for idx, n in enumerate(nodes, start=1):
            vos_items.append({
                "id": idx,
                "label": n.get("label", n["id"]),
                "cluster": n.get("community", 1),
                "weight": n.get("frequency", 1.0)
            })
        id_map = {n["id"]: idx for idx, n in enumerate(nodes, start=1)}
        vos_links = []
        for e in edges:
            if e["source"] in id_map and e["target"] in id_map:
                vos_links.append({
                    "node1_id": id_map[e["source"]],
                    "node2_id": id_map[e["target"]],
                    "strength": e.get("weight", 1.0)
                })
        vos_data = {"network": {"items": vos_items, "links": vos_links}}
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(vos_data, f, indent=2)


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
    p_bld.add_argument("--input", required=True, help="Path to corpus (.parquet, .csv, .json)")
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
    p_bld.set_defaults(func=cmd_build)

    # Subcommand: sequential-networks (alias period-networks)
    for sub_name in ["sequential-networks", "period-networks"]:
        p_seq = subparsers.add_parser(sub_name, help="Generate sequential longitudinal networks & SOM manifest")
        p_seq.add_argument("--input", required=True, help="Path to corpus (.parquet, .csv, .json)")
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
