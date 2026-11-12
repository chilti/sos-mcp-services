#!/usr/bin/env python3
"""
citation_snowball.py

Herramienta de Snowballing de Citas (Backward & Forward) sobre grafos de citación
académica (Wohlin, 2014) para revisiones sistemáticas de literatura PRISMA 2020.
Combina consultas locales de alta velocidad en ClickHouse (rag.works_academic_all, CERO JOINs)
con la API pública de OpenAlex para cobertura internacional completa.
Incluye adquisición opcional de texto completo en Acceso Abierto (--download-oa-pdfs).
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

# Importación dinámica del motor de descarga de PDFs en Acceso Abierto
downloader_script_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "open-access-pdf-downloader", "scripts"))
if downloader_script_dir not in sys.path:
    sys.path.insert(0, downloader_script_dir)
try:
    from download_oa_pdfs import run_oa_pdf_harvester
    HAS_DOWNLOADER = True
except ImportError:
    run_oa_pdf_harvester = None
    HAS_DOWNLOADER = False


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
    """Resuelve un DOI, arXiv ID o Work ID a un objeto Work estandarizado."""
    identifier = identifier.strip()
    is_doi = "10." in identifier
    is_openalex = identifier.startswith("W") or "openalex.org/W" in identifier

    # Autodetección de identificadores arXiv (ej. 2306.05836, arXiv:2306.05836)
    if not is_doi and not is_openalex:
        arxiv_match = re.search(r"(?:arxiv[:/]|abs/)?(\d{4}\.\d{4,5}(?:v\d+)?)", identifier, re.IGNORECASE)
        if arxiv_match:
            identifier = f"10.48550/arXiv.{arxiv_match.group(1)}"
            is_doi = True

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


def run_snowballing(
    seeds_raw: List[str],
    mode: str,
    top_candidates: int,
    min_cocitations: int,
    output_dir: str,
    download_oa_pdfs: bool = False,
    fulltext_limit: int = 10,
    extract_text: bool = True,
    lang: str = "en"
):
    os.makedirs(output_dir, exist_ok=True)
    ch_client = get_ch_client()
    is_es = (lang == "es")

    print("\n" + "=" * 60)
    print("  DEEP LITERATURE RESEARCHER: PROTOCOLO DE SNOWBALLING (WOHLIN, 2014)" if is_es else "  DEEP LITERATURE RESEARCHER: SNOWBALLING PROTOCOL (WOHLIN, 2014)")
    print("=" * 60)

    # 1. Resolve seed set
    print(f"\n[Fase 1] Resolviendo {len(seeds_raw)} artículos semilla..." if is_es else f"\n[Phase 1] Resolving {len(seeds_raw)} seed articles...")
    resolved_seeds = []
    seed_ids = set()
    for s in seeds_raw:
        seed_obj = resolve_seed(s, ch_client)
        if seed_obj:
            resolved_seeds.append(seed_obj)
            seed_ids.add(seed_obj["id"])
            print(f"  ✓ [{seed_obj['id']}] ({seed_obj.get('year', 'N/A')}) {seed_obj.get('title', '')[:70]}...")
        else:
            print(f"  ✗ {'No se pudo resolver la semilla' if is_es else 'Could not resolve seed'}: {s}", file=sys.stderr)

    if not resolved_seeds:
        print("Error: No se pudo resolver ningún artículo semilla." if is_es else "Error: Could not resolve any seed articles.", file=sys.stderr)
        sys.exit(1)

    # 2. Backward Snowballing (Cited references)
    backward_counter = Counter()
    backward_links = defaultdict(list)
    if mode in ("backward", "both"):
        print("\n[Fase 2] Ejecutando Backward Snowballing (rastreo de raíces teóricas)..." if is_es else "\n[Phase 2] Running Backward Snowballing (tracking theoretical roots)...")
        for s in resolved_seeds:
            refs = s.get("referenced_works", [])
            print(f"  - {'Semilla' if is_es else 'Seed'} {s['id']}: {len(refs)} {'referencias citadas.' if is_es else 'cited references.'}")
            for ref_id in refs:
                if ref_id not in seed_ids:
                    backward_counter[ref_id] += 1
                    backward_links[ref_id].append(s["id"])

    # 3. Forward Snowballing (Citing articles)
    forward_works_dict = {}
    forward_links = defaultdict(list)
    if mode in ("forward", "both"):
        print("\n[Fase 3] Ejecutando Forward Snowballing (rastreo de frentes contemporáneos)..." if is_es else "\n[Phase 3] Running Forward Snowballing (tracking contemporary fronts)...")
        for s in resolved_seeds:
            citing = fetch_forward_citations(s["id"], limit=30)
            print(f"  - {'Semilla' if is_es else 'Seed'} {s['id']}: {len(citing)} {'trabajos citantes influyentes recuperados.' if is_es else 'influential citing works retrieved.'}")
            for cw in citing:
                cid = cw["id"]
                if cid not in seed_ids:
                    forward_works_dict[cid] = cw
                    forward_links[cid].append(s["id"])

    # 4. Consolidate candidates for screening
    print("\n[Fase 4] Consolidando candidatos y calculando centralidad en el grafo..." if is_es else "\n[Phase 4] Consolidating candidates and computing graph centrality...")
    all_candidate_ids = set()
    for wid, count in backward_counter.items():
        if count >= min_cocitations:
            all_candidate_ids.add(wid)
    for wid in forward_works_dict.keys():
        all_candidate_ids.add(wid)

    print(f"  - {'Total de candidatos únicos descubiertos' if is_es else 'Total unique candidates discovered'}: {len(all_candidate_ids)}")

    # Fetch metadata for missing backward candidates
    backward_ids_to_fetch = [wid for wid in all_candidate_ids if wid not in forward_works_dict]
    print(f"  - {'Recuperando metadatos de' if is_es else 'Fetching metadata for'} {len(backward_ids_to_fetch)} {'obras referenciadas...' if is_es else 'referenced works...'}")
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
            "source_provenance": meta.get("source", "unknown"),
            "fulltext_status": "NOT_REQUESTED",
            "oa_status": "unknown",
            "pdf_filename": "",
            "pdf_path": "",
            "text_path": ""
        }
        candidate_records.append(rec)

    # Ordenar por puntaje compuesto descendente
    candidate_records.sort(key=lambda x: x["composite_score"], reverse=True)
    top_records = candidate_records[:top_candidates]

    # 5. Adquisición opcional de textos completos en Acceso Abierto
    fulltext_manifest_map = {}
    fulltext_success_count = 0
    fulltext_paywalled_count = 0

    if download_oa_pdfs:
        print("\n" + "=" * 60)
        print("  [Fase 5] Cosecha de Textos Completos en Acceso Abierto..." if is_es else "  [Phase 5] Harvesting Open Access Full-Text PDFs...")
        print("=" * 60)
        if HAS_DOWNLOADER and run_oa_pdf_harvester:
            top_ids_to_download = [r["work_id"] for r in top_records[:fulltext_limit]]
            run_oa_pdf_harvester(
                identifiers=top_ids_to_download,
                output_dir=output_dir,
                limit=fulltext_limit,
                delay=0.5,
                extract_text=extract_text,
                timeout=25,
                lang=lang
            )
            manifest_json_path = os.path.join(output_dir, "download_manifest.json")
            if os.path.exists(manifest_json_path):
                try:
                    with open(manifest_json_path, "r", encoding="utf-8") as f_man:
                        mdata = json.load(f_man)
                        fulltext_success_count = mdata.get("successful_downloads", 0)
                        fulltext_paywalled_count = mdata.get("paywalled_closed", 0)
                        for rec in mdata.get("records", []):
                            w_ident = clean_work_id(rec.get("work_id", ""))
                            fulltext_manifest_map[w_ident] = rec
                except Exception as e:
                    print(f"[Aviso] No se pudo leer download_manifest.json: {e}", file=sys.stderr)
        else:
            print("[Aviso] El motor 'open-access-pdf-downloader' no está disponible.", file=sys.stderr)

    # Enriquecer los registros top con la información de texto completo
    for r in top_records:
        wid = clean_work_id(r["work_id"])
        man_entry = fulltext_manifest_map.get(wid)
        if man_entry:
            r["fulltext_status"] = man_entry.get("status", "NOT_REQUESTED")
            r["oa_status"] = man_entry.get("oa_status", "unknown")
            r["pdf_filename"] = man_entry.get("pdf_filename", "")
            r["pdf_path"] = man_entry.get("pdf_path", "")
            if extract_text and man_entry.get("text_extracted") and r["pdf_filename"]:
                txt_name = r["pdf_filename"].rsplit(".", 1)[0] + ".txt"
                r["text_path"] = os.path.join(output_dir, "text", txt_name)

    # 6. Generar salidas PRISMA y tablas
    json_path = os.path.join(output_dir, "snowball_candidates.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "seeds": resolved_seeds,
            "mode": mode,
            "total_candidates": len(candidate_records),
            "top_candidates_count": len(top_records),
            "fulltext_harvested": download_oa_pdfs,
            "fulltext_success_count": fulltext_success_count,
            "results": top_records
        }, f, indent=2, ensure_ascii=False)

    csv_path = os.path.join(output_dir, "snowball_candidates.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Work ID", "DOI", "Title", "Year", "Type", "Authors", "Citations", "FWCI",
            "Direction", "Co-Citations", "Seed Connections", "Score",
            "OA Status", "FullText Status", "PDF Path", "Text Path"
        ])
        for r in top_records:
            writer.writerow([
                r["work_id"], r["doi"], r["title"], r["year"], r["type"],
                "; ".join(r["authors"]), r["cited_by_count"], r["fwci"],
                r["direction"], r["co_citation_count"], "; ".join(r["seed_connections"]), r["composite_score"],
                r.get("oa_status", ""), r.get("fulltext_status", ""), r.get("pdf_path", ""), r.get("text_path", "")
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
    if download_oa_pdfs:
        prisma_flow["full_text_eligibility"] = {
            "requested_for_harvest": min(fulltext_limit, len(top_records)),
            "oa_fulltext_retrieved": fulltext_success_count,
            "paywalled_or_closed": fulltext_paywalled_count
        }

    flow_path = os.path.join(output_dir, "prisma_flow_data.json")
    with open(flow_path, "w", encoding="utf-8") as f:
        json.dump(prisma_flow, f, indent=2)

    # Markdown Report
    report_path = os.path.join(output_dir, "snowball_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        if is_es:
            f.write("# Informe de Snowballing de Citas (Protocolo Wohlin, 2014)\n\n")
            f.write(f"- **Artículos Semilla Analizados:** {len(resolved_seeds)}\n")
            f.write(f"- **Modo de Rastreo:** `{mode}`\n")
            f.write(f"- **Total de Candidatos Descubiertos:** {len(candidate_records)}\n")
            f.write(f"- **Candidatos Priorizados para Tamizaje PRISMA:** {len(top_records)}\n")
            if download_oa_pdfs:
                f.write(f"- **Textos Completos en OA Descargados:** {fulltext_success_count}/{min(fulltext_limit, len(top_records))}\n\n")
            else:
                f.write("\n")

            f.write("## Diagrama de Flujo PRISMA 2020\n\n")
            f.write("```mermaid\nflowchart TD\n")
            f.write(f'    S["Conjunto Semilla (n = {len(resolved_seeds)})"] --> B["Backward Snowballing (n = {len(backward_counter)})"]\n')
            f.write(f'    S --> F["Forward Snowballing (n = {len(forward_works_dict)})"]\n')
            f.write(f'    B & F --> U["Total Candidatos Únicos (n = {len(candidate_records)})"]\n')
            f.write(f'    U --> SCR["Priorizados para Tamizaje (n = {len(top_records)})"]\n')
            if download_oa_pdfs:
                f.write(f'    SCR --> FT["Textos Completos OA Recuperados (n = {fulltext_success_count})"]\n')
                f.write(f'    SCR --> CLO["Excluidos: Muro de Pago / Cerrados (n = {fulltext_paywalled_count})"]\n')
            f.write("```\n\n")

            f.write("## Top 15 Artículos Candidatos por Centralidad e Impacto\n\n")
            if download_oa_pdfs:
                f.write("| # | Año | Citas | Dirección | Texto Completo | Título / DOI |\n")
                f.write("|---|:---:|:---:|:---:|:---:|---|\n")
            else:
                f.write("| # | Año | Citas | Dirección | Conexiones Semilla | Título / DOI |\n")
                f.write("|---|:---:|:---:|:---:|:---:|---|\n")
        else:
            f.write("# Citation Snowballing Report (Wohlin Protocol, 2014)\n\n")
            f.write(f"- **Seed Articles Analyzed:** {len(resolved_seeds)}\n")
            f.write(f"- **Tracking Mode:** `{mode}`\n")
            f.write(f"- **Total Candidates Discovered:** {len(candidate_records)}\n")
            f.write(f"- **Prioritized Candidates for PRISMA Screening:** {len(top_records)}\n")
            if download_oa_pdfs:
                f.write(f"- **OA Full-Text PDFs Harvested:** {fulltext_success_count}/{min(fulltext_limit, len(top_records))}\n\n")
            else:
                f.write("\n")

            f.write("## PRISMA 2020 Flow Diagram\n\n")
            f.write("```mermaid\nflowchart TD\n")
            f.write(f'    S["Seed Set (n = {len(resolved_seeds)})"] --> B["Backward Snowballing (n = {len(backward_counter)})"]\n')
            f.write(f'    S --> F["Forward Snowballing (n = {len(forward_works_dict)})"]\n')
            f.write(f'    B & F --> U["Total Unique Candidates (n = {len(candidate_records)})"]\n')
            f.write(f'    U --> SCR["Prioritized for Screening (n = {len(top_records)})"]\n')
            if download_oa_pdfs:
                f.write(f'    SCR --> FT["OA Full-Text Retrieved (n = {fulltext_success_count})"]\n')
                f.write(f'    SCR --> CLO["Excluded: Closed / Paywalled (n = {fulltext_paywalled_count})"]\n')
            f.write("```\n\n")

            f.write("## Top 15 Candidate Articles by Centrality and Impact\n\n")
            if download_oa_pdfs:
                f.write("| # | Year | Citations | Direction | Full Text | Title / DOI |\n")
                f.write("|---|:---:|:---:|:---:|:---:|---|\n")
            else:
                f.write("| # | Year | Citations | Direction | Seed Connections | Title / DOI |\n")
                f.write("|---|:---:|:---:|:---:|:---:|---|\n")

        seed_unit = "semillas" if is_es else "seeds"
        na_lbl = "N/D" if is_es else "N/A"
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

            if download_oa_pdfs:
                ft_status = r.get("fulltext_status", "NOT_REQUESTED")
                if "SUCCESS" in ft_status:
                    pdf_rel = os.path.relpath(r["pdf_path"], output_dir) if r.get("pdf_path") else ""
                    txt_rel = os.path.relpath(r["text_path"], output_dir) if r.get("text_path") else ""
                    ft_cell = f"`OA ({r.get('oa_status', '')})`"
                    links = []
                    if pdf_rel:
                        links.append(f"[PDF]({pdf_rel})")
                    if txt_rel:
                        links.append(f"[TXT]({txt_rel})")
                    if links:
                        ft_cell += "<br>" + " · ".join(links)
                elif "PAYWALLED" in ft_status or "CLOSED" in ft_status:
                    ft_cell = "`Paywalled`" if not is_es else "`Cerrado`"
                else:
                    ft_cell = f"`{ft_status[:15]}`"
                f.write(f"| {i} | {r['year'] or na_lbl} | {r['cited_by_count']} | `{r['direction']}` | {ft_cell} | **{r['title'][:80]}...**<br>{doi_link} |\n")
            else:
                f.write(f"| {i} | {r['year'] or na_lbl} | {r['cited_by_count']} | `{r['direction']}` | {len(r['seed_connections'])} {seed_unit} | **{r['title'][:80]}...**<br>{doi_link} |\n")

    print("\n" + "=" * 60)
    print(f"✅ {'Snowballing finalizado con éxito en' if is_es else 'Snowballing completed successfully in'} '{output_dir}':")
    print("  - snowball_candidates.json")
    print("  - snowball_candidates.csv")
    print("  - prisma_flow_data.json")
    print("  - snowball_report.md")
    if download_oa_pdfs:
        print(f"  - pdf/ ({fulltext_success_count} {'PDFs descargados' if is_es else 'PDFs downloaded'})")
        if extract_text:
            print("  - text/ (textos planos extraídos)")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Deep Literature Researcher - Citation Snowball CLI")
    parser.add_argument("--lang", choices=["en", "es"], default="en", help="Output language for reports and messages (default: en)")
    parser.add_argument("--seeds", nargs="+", required=True, help="List of seed DOIs or OpenAlex Work IDs")
    parser.add_argument("--mode", choices=["backward", "forward", "both"], default="both", help="Tracking mode")
    parser.add_argument("--top-citations", type=int, default=30, help="Number of top candidates to prioritize")
    parser.add_argument("--min-cocitations", type=int, default=1, help="Minimum co-citation threshold to include reference")
    parser.add_argument("--output", type=str, default="./snowball_results", help="Output directory for results")
    parser.add_argument("--download-oa-pdfs", action="store_true", help="Download open-access full-text PDFs for top prioritized candidates")
    parser.add_argument("--fulltext-limit", type=int, default=10, help="Maximum number of candidate full-text PDFs to download (default: 10)")
    parser.add_argument("--extract-text", action="store_true", default=True, help="Extract plain text (.txt) from downloaded PDFs (default: True)")

    args = parser.parse_args()
    run_snowballing(
        seeds_raw=args.seeds,
        mode=args.mode,
        top_candidates=args.top_citations,
        min_cocitations=args.min_cocitations,
        output_dir=args.output,
        download_oa_pdfs=args.download_oa_pdfs,
        fulltext_limit=args.fulltext_limit,
        extract_text=args.extract_text,
        lang=args.lang
    )


if __name__ == "__main__":
    main()
