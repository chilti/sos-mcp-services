#!/usr/bin/env python3
"""
citation_snowball.py

Herramienta de Snowballing de Citas (Backward & Forward) sobre grafos de citación
académica (Wohlin, 2014) para revisiones sistemáticas de literatura PRISMA 2020.
Combina consultas locales de alta velocidad en ClickHouse (rag.works_academic_all, CERO JOINs)
con la API pública de OpenAlex para cobertura internacional completa.
"""

import argparse
import csv
import json
import math
import os
import re
import sys
import time
from collections import Counter, defaultdict
from typing import Dict, List, Any, Optional, Set, Tuple

import requests

try:
    import clickhouse_connect
    HAS_CLICKHOUSE = True
except ImportError:
    HAS_CLICKHOUSE = False


OPENALEX_API_BASE = "https://api.openalex.org/works"
USER_AGENT = "DeepLiteratureResearcher/1.0 (mailto:soporte@knomap.org)"


def get_ch_client():
    if not HAS_CLICKHOUSE:
        return None
    try:
        host = os.getenv("CLICKHOUSE_HOST", "10.90.0.87")
        port = int(os.getenv("CLICKHOUSE_PORT", "8124"))
        user = os.getenv("CLICKHOUSE_USER", "rag_user")
        pwd = os.getenv("CLICKHOUSE_PASSWORD", "$B3tt3r-R4g-3veR-d0N3++").replace("$$", "$")
        db = os.getenv("CLICKHOUSE_DATABASE", "rag")
        return clickhouse_connect.get_client(
            host=host, port=port, username=user, password=pwd, database=db,
            connect_timeout=3, send_receive_timeout=15
        )
    except Exception as e:
        print(f"[Aviso] No se pudo conectar a ClickHouse local ({e}). Usando API OpenAlex.", file=sys.stderr)
        return None


def clean_work_id(raw_id: str) -> str:
    """Normaliza un ID de OpenAlex a formato W..."""
    if not raw_id:
        return ""
    match = re.search(r"W\d+", raw_id)
    return match.group(0) if match else raw_id.strip()


def resolve_seed(identifier: str, ch_client=None) -> Optional[Dict[str, Any]]:
    """Resuelve un DOI o Work ID a un objeto Work estandarizado."""
    identifier = identifier.strip()
    is_doi = "10." in identifier
    is_openalex = identifier.startswith("W") or "openalex.org/W" in identifier

    # Intento 1: ClickHouse local
    if ch_client:
        try:
            if is_doi:
                doi_clean = re.search(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", identifier)
                if doi_clean:
                    sql = f"SELECT id, doi, title, publication_year, cited_by_count, raw_data FROM rag.works_academic_all WHERE positionCaseInsensitiveUTF8(doi, '{doi_clean.group(0)}') > 0 LIMIT 1"
                    rows = ch_client.query(sql).result_rows
                    if rows:
                        r = rows[0]
                        raw = json.loads(r[5]) if r[5] else {}
                        return {
                            "id": clean_work_id(r[0]),
                            "doi": r[1],
                            "title": r[2],
                            "year": r[3],
                            "cited_by_count": r[4],
                            "referenced_works": [clean_work_id(x) for x in raw.get("referenced_works", [])]
                        }
            elif is_openalex:
                w_id = clean_work_id(identifier)
                sql = f"SELECT id, doi, title, publication_year, cited_by_count, raw_data FROM rag.works_academic_all WHERE id = 'https://openalex.org/{w_id}' OR id = '{w_id}' LIMIT 1"
                rows = ch_client.query(sql).result_rows
                if rows:
                    r = rows[0]
                    raw = json.loads(r[5]) if r[5] else {}
                    return {
                        "id": clean_work_id(r[0]),
                        "doi": r[1],
                        "title": r[2],
                        "year": r[3],
                        "cited_by_count": r[4],
                        "referenced_works": [clean_work_id(x) for x in raw.get("referenced_works", [])]
                    }
        except Exception as e:
            print(f"[Debug] Fallo consulta local para {identifier}: {e}", file=sys.stderr)

    # Intento 2: OpenAlex API
    headers = {"User-Agent": USER_AGENT}
    try:
        if is_doi:
            doi_match = re.search(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", identifier)
            url = f"{OPENALEX_API_BASE}/https://doi.org/{doi_match.group(0)}" if doi_match else f"{OPENALEX_API_BASE}/{identifier}"
        elif is_openalex:
            url = f"{OPENALEX_API_BASE}/{clean_work_id(identifier)}"
        else:
            url = f"{OPENALEX_API_BASE}/{identifier}"

        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "id": clean_work_id(data.get("id", "")),
                "doi": data.get("doi", ""),
                "title": data.get("title", data.get("display_name", "")),
                "year": data.get("publication_year"),
                "cited_by_count": data.get("cited_by_count", 0),
                "referenced_works": [clean_work_id(x) for x in data.get("referenced_works", [])]
            }
        else:
            print(f"[Aviso] API OpenAlex respondió {resp.status_code} para {identifier}", file=sys.stderr)
    except Exception as e:
        print(f"[Error] Falló resolución remota para {identifier}: {e}", file=sys.stderr)

    return None


def fetch_works_metadata(work_ids: List[str], ch_client=None) -> Dict[str, Dict[str, Any]]:
    """Recupera metadatos de una lista de Work IDs (usando ClickHouse IN() o OpenAlex API por lotes)."""
    results = {}
    pending_ids = set(work_ids)

    # 1. Resolver en ClickHouse con cláusula IN (CERO JOINS)
    if ch_client and pending_ids:
        try:
            full_ids = [f"'https://openalex.org/{wid}'" for wid in pending_ids]
            chunk_size = 500
            for i in range(0, len(full_ids), chunk_size):
                chunk = full_ids[i:i + chunk_size]
                sql = f"""
                SELECT id, doi, title, publication_year, type, author_names, cited_by_count, fwci
                FROM rag.works_academic_all
                WHERE id IN ({','.join(chunk)})
                """
                rows = ch_client.query(sql).result_rows
                for r in rows:
                    wid = clean_work_id(r[0])
                    results[wid] = {
                        "id": wid,
                        "doi": r[1] or "",
                        "title": r[2] or "",
                        "year": r[3] or None,
                        "type": r[4] or "",
                        "authors": r[5][:3] if r[5] else [],
                        "cited_by_count": r[6] or 0,
                        "fwci": round(r[7], 2) if r[7] else None,
                        "source": "clickhouse_local"
                    }
                    pending_ids.discard(wid)
        except Exception as e:
            print(f"[Debug] Fallo lote local ClickHouse: {e}", file=sys.stderr)

    # 2. Resolver los faltantes vía OpenAlex API (lotes de hasta 50 por filtro openalex_id)
    if pending_ids:
        pending_list = list(pending_ids)
        chunk_size = 50
        headers = {"User-Agent": USER_AGENT}
        for i in range(0, len(pending_list), chunk_size):
            chunk = pending_list[i:i + chunk_size]
            pipe_ids = "|".join([f"https://openalex.org/{wid}" for wid in chunk])
            try:
                params = {
                    "filter": f"openalex_id:{pipe_ids}",
                    "per-page": len(chunk)
                }
                resp = requests.get(OPENALEX_API_BASE, params=params, headers=headers, timeout=12)
                if resp.status_code == 200:
                    data = resp.json().get("results", [])
                    for item in data:
                        wid = clean_work_id(item.get("id", ""))
                        auth_names = [a.get("author", {}).get("display_name", "") for a in item.get("authorships", [])[:3]]
                        results[wid] = {
                            "id": wid,
                            "doi": item.get("doi", "") or "",
                            "title": item.get("title", item.get("display_name", "")) or "",
                            "year": item.get("publication_year"),
                            "type": item.get("type", ""),
                            "authors": auth_names,
                            "cited_by_count": item.get("cited_by_count", 0),
                            "fwci": round(item.get("fwci", 0), 2) if item.get("fwci") else None,
                            "source": "openalex_api"
                        }
                time.sleep(0.1)
            except Exception as e:
                print(f"[Error] Falló lote OpenAlex API: {e}", file=sys.stderr)

    return results


def fetch_forward_citations(work_id: str, limit: int = 25) -> List[Dict[str, Any]]:
    """Recupera los artículos citantes más influyentes de un trabajo vía OpenAlex API."""
    headers = {"User-Agent": USER_AGENT}
    params = {
        "filter": f"cites:https://openalex.org/{work_id}",
        "sort": "cited_by_count:desc",
        "per-page": limit
    }
    citing_works = []
    try:
        resp = requests.get(OPENALEX_API_BASE, params=params, headers=headers, timeout=12)
        if resp.status_code == 200:
            for item in resp.json().get("results", []):
                wid = clean_work_id(item.get("id", ""))
                auth_names = [a.get("author", {}).get("display_name", "") for a in item.get("authorships", [])[:3]]
                citing_works.append({
                    "id": wid,
                    "doi": item.get("doi", "") or "",
                    "title": item.get("title", item.get("display_name", "")) or "",
                    "year": item.get("publication_year"),
                    "type": item.get("type", ""),
                    "authors": auth_names,
                    "cited_by_count": item.get("cited_by_count", 0),
                    "fwci": round(item.get("fwci", 0), 2) if item.get("fwci") else None,
                    "source": "openalex_api_citing"
                })
    except Exception as e:
        print(f"[Error] Falló recuperación de citas hacia adelante para {work_id}: {e}", file=sys.stderr)

    return citing_works


def run_snowballing(seeds_raw: List[str], mode: str, top_candidates: int, min_cocitations: int, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    ch_client = get_ch_client()

    print("\n" + "=" * 60)
    print("  DEEP LITERATURE RESEARCHER: PROTOCOLO DE SNOWBALLING (WOHLIN, 2014)")
    print("=" * 60)

    # 1. Resolver conjunto semilla
    print(f"\n[Fase 1] Resolviendo {len(seeds_raw)} artículos semilla...")
    resolved_seeds = []
    seed_ids = set()
    for s in seeds_raw:
        seed_obj = resolve_seed(s, ch_client)
        if seed_obj:
            resolved_seeds.append(seed_obj)
            seed_ids.add(seed_obj["id"])
            print(f"  ✓ [{seed_obj['id']}] ({seed_obj.get('year', 'N/D')}) {seed_obj.get('title', '')[:70]}...")
        else:
            print(f"  ✗ No se pudo resolver la semilla: {s}", file=sys.stderr)

    if not resolved_seeds:
        print("Error: No se pudo resolver ningún artículo semilla.", file=sys.stderr)
        sys.exit(1)

    # 2. Backward Snowballing (Referencias citadas)
    backward_counter = Counter()
    backward_links = defaultdict(list)
    if mode in ("backward", "both"):
        print("\n[Fase 2] Ejecutando Backward Snowballing (rastreo de raíces teóricas)...")
        for s in resolved_seeds:
            refs = s.get("referenced_works", [])
            print(f"  - Semilla {s['id']}: {len(refs)} referencias citadas.")
            for ref_id in refs:
                if ref_id not in seed_ids:
                    backward_counter[ref_id] += 1
                    backward_links[ref_id].append(s["id"])

    # 3. Forward Snowballing (Artículos citantes)
    forward_works_dict = {}
    forward_links = defaultdict(list)
    if mode in ("forward", "both"):
        print("\n[Fase 3] Ejecutando Forward Snowballing (rastreo de frentes contemporáneos)...")
        for s in resolved_seeds:
            citing = fetch_forward_citations(s["id"], limit=30)
            print(f"  - Semilla {s['id']}: {len(citing)} trabajos citantes influyentes recuperados.")
            for cw in citing:
                cid = cw["id"]
                if cid not in seed_ids:
                    forward_works_dict[cid] = cw
                    forward_links[cid].append(s["id"])

    # 4. Consolidar candidatos para tamizaje
    print("\n[Fase 4] Consolidando candidatos y calculando centralidad en el grafo...")
    all_candidate_ids = set()
    for wid, count in backward_counter.items():
        if count >= min_cocitations:
            all_candidate_ids.add(wid)
    for wid in forward_works_dict.keys():
        all_candidate_ids.add(wid)

    print(f"  - Total de candidatos únicos descubiertos: {len(all_candidate_ids)}")

    # Obtener metadatos de los candidatos backward faltantes
    backward_ids_to_fetch = [wid for wid in all_candidate_ids if wid not in forward_works_dict]
    print(f"  - Recuperando metadatos de {len(backward_ids_to_fetch)} obras referenciadas...")
    backward_meta = fetch_works_metadata(backward_ids_to_fetch, ch_client)

    candidate_records = []
    for wid in all_candidate_ids:
        meta = forward_works_dict.get(wid) or backward_meta.get(wid) or {
            "id": wid, "doi": "", "title": f"Work {wid}", "year": None,
            "type": "", "authors": [], "cited_by_count": 0, "fwci": None, "source": "unresolved"
        }

        b_count = backward_counter.get(wid, 0)
        f_count = len(forward_links.get(wid, []))

        direction = "both" if (b_count > 0 and f_count > 0) else ("backward" if b_count > 0 else "forward")
        connected_seeds = list(set(backward_links.get(wid, []) + forward_links.get(wid, [])))

        # Puntaje compuesto: prioridad por co-citación recurrente + volumen de impacto
        cites = meta.get("cited_by_count") or 0
        composite_score = (b_count * 15.0) + (f_count * 10.0) + math.log1p(cites)

        rec = {
            "work_id": wid,
            "doi": meta.get("doi", ""),
            "title": meta.get("title", ""),
            "year": meta.get("year"),
            "type": meta.get("type", ""),
            "authors": meta.get("authors", []),
            "cited_by_count": cites,
            "fwci": meta.get("fwci"),
            "direction": direction,
            "co_citation_count": b_count,
            "forward_citation_count": f_count,
            "seed_connections": connected_seeds,
            "composite_score": round(composite_score, 2),
            "source_provenance": meta.get("source", "unknown")
        }
        candidate_records.append(rec)

    # Ordenar por puntaje compuesto descendente
    candidate_records.sort(key=lambda x: x["composite_score"], reverse=True)
    top_records = candidate_records[:top_candidates]

    # 5. Generar salidas PRISMA y tablas
    json_path = os.path.join(output_dir, "snowball_candidates.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "seeds": resolved_seeds,
            "mode": mode,
            "total_candidates": len(candidate_records),
            "top_candidates_count": len(top_records),
            "results": top_records
        }, f, indent=2, ensure_ascii=False)

    csv_path = os.path.join(output_dir, "snowball_candidates.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Work ID", "DOI", "Title", "Year", "Type", "Authors", "Citations", "FWCI",
            "Direction", "Co-Citations", "Seed Connections", "Score"
        ])
        for r in top_records:
            writer.writerow([
                r["work_id"], r["doi"], r["title"], r["year"], r["type"],
                "; ".join(r["authors"]), r["cited_by_count"], r["fwci"],
                r["direction"], r["co_citation_count"], "; ".join(r["seed_connections"]), r["composite_score"]
            ])

    # PRISMA flow data
    prisma_flow = {
        "identification": {
            "seeds_count": len(resolved_seeds),
            "backward_references_total": sum(backward_counter.values()),
            "backward_unique_records": len(backward_counter),
            "forward_citing_total": sum(len(v) for v in forward_links.values()),
            "forward_unique_records": len(forward_works_dict),
            "total_records_identified": len(candidate_records)
        },
        "screening": {
            "records_screened": len(top_records),
            "recommended_for_full_text": min(25, len(top_records))
        }
    }
    flow_path = os.path.join(output_dir, "prisma_flow_data.json")
    with open(flow_path, "w", encoding="utf-8") as f:
        json.dump(prisma_flow, f, indent=2)

    # Reporte Markdown
    report_path = os.path.join(output_dir, "snowball_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Informe de Snowballing de Citas (Protocolo Wohlin, 2014)\n\n")
        f.write(f"- **Artículos Semilla Analizados:** {len(resolved_seeds)}\n")
        f.write(f"- **Modo de Rastreo:** `{mode}`\n")
        f.write(f"- **Total de Candidatos Descubiertos:** {len(candidate_records)}\n")
        f.write(f"- **Candidatos Priorizados para Tamizaje PRISMA:** {len(top_records)}\n\n")

        f.write("## Diagrama de Flujo PRISMA 2020\n\n")
        f.write("```mermaid\nflowchart TD\n")
        f.write(f'    S["Conjunto Semilla (n = {len(resolved_seeds)})"] --> B["Backward Snowballing (n = {len(backward_counter)})"]\n')
        f.write(f'    S --> F["Forward Snowballing (n = {len(forward_works_dict)})"]\n')
        f.write(f'    B & F --> U["Total Candidatos Únicos (n = {len(candidate_records)})"]\n')
        f.write(f'    U --> SCR["Priorizados para Tamizaje de Resumen (n = {len(top_records)})"]\n')
        f.write("```\n\n")

        f.write("## Top 15 Artículos Candidatos por Centralidad e Impacto\n\n")
        f.write("| # | Año | Citas | Dirección | Conexiones Semilla | Título / DOI |\n")
        f.write("|---|:---:|:---:|:---:|:---:|---|\n")
        for i, r in enumerate(top_records[:15], 1):
            raw_doi = r["doi"] or ""
            if raw_doi.startswith("http"):
                doi_url = raw_doi
                doi_display = re.sub(r"^https?://(dx\.)?doi\.org/", "", raw_doi)
            elif raw_doi:
                doi_url = f"https://doi.org/{raw_doi}"
                doi_display = raw_doi
            else:
                doi_url = ""
                doi_display = r["work_id"]

            doi_link = f"[{doi_display}]({doi_url})" if doi_url else doi_display
            f.write(f"| {i} | {r['year'] or 'N/D'} | {r['cited_by_count']} | `{r['direction']}` | {len(r['seed_connections'])} semillas | **{r['title'][:80]}...**<br>{doi_link} |\n")

    print("\n" + "=" * 60)
    print(f"✅ Snowballing finalizado con éxito en '{output_dir}':")
    print("  - snowball_candidates.json")
    print("  - snowball_candidates.csv")
    print("  - prisma_flow_data.json")
    print("  - snowball_report.md")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Deep Literature Researcher - Citation Snowball CLI")
    parser.add_argument("--seeds", nargs="+", required=True, help="Lista de DOIs o OpenAlex Work IDs semilla")
    parser.add_argument("--mode", choices=["backward", "forward", "both"], default="both", help="Modo de rastreo")
    parser.add_argument("--top-citations", type=int, default=30, help="Número de candidatos principales a priorizar")
    parser.add_argument("--min-cocitations", type=int, default=1, help="Umbral mínimo de co-citaciones para incluir referencia")
    parser.add_argument("--output", type=str, default="./snowball_results", help="Directorio de salida para los resultados")

    args = parser.parse_args()
    run_snowballing(args.seeds, args.mode, args.top_citations, args.min_cocitations, args.output)


if __name__ == "__main__":
    main()
