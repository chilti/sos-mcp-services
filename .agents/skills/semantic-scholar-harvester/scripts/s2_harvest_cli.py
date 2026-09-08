#!/usr/bin/env /home/ambientesPy/revistaslatam/bin/python
"""
Semantic Scholar Data Harvester CLI
-----------------------------------
Herramienta autónoma e independiente para la consulta y extracción de publicaciones
y grafos de citas desde la API Graph de Semantic Scholar (S2), con soporte de
búsqueda temática, citas entrantes/salientes y normalización al esquema tabular canónico.
"""

import sys
import os
import argparse
import json
import time
import requests
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional

S2_BASE_URL = "https://api.semanticscholar.org/graph/v1"

DEFAULT_PAPER_FIELDS = (
    "paperId,title,abstract,year,citationCount,influentialCitationCount,"
    "venue,publicationVenue,fieldsOfStudy,s2FieldsOfStudy,authors,openAccessPdf,externalIds"
)

def get_env_variable(key: str, default: Optional[str] = None) -> Optional[str]:
    """Obtiene variable de entorno o busca en archivos .env locales."""
    if os.environ.get(key):
        return os.environ.get(key)
    env_paths = [
        Path.cwd() / ".env",
        Path("/mnt/expansion/desplegados/sos-mcp-services/.env"),
        Path("/mnt/expansion/desplegados/TlachIA-Metrics/.env")
    ]
    for p in env_paths:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith(f"{key}="):
                            return line.split("=", 1)[1].strip().strip('"').strip("'")
            except Exception:
                pass
    return default

def map_s2_paper_to_canonical(paper: Dict[str, Any]) -> Dict[str, Any]:
    """Mapea un trabajo de Semantic Scholar al esquema canónico."""
    # 1. Identificadores
    paper_id = paper.get("paperId") or ""
    external_ids = paper.get("externalIds") or {}
    doi = external_ids.get("DOI") or ""
    
    # 2. Título y Resumen
    title = paper.get("title") or ""
    abstract = paper.get("abstract") or ""
    
    # 3. Autores y Afiliaciones
    authors_list = []
    author_ids_list = []
    affiliations_list = []
    for auth in paper.get("authors", []):
        name = auth.get("name")
        if name:
            authors_list.append(name.strip())
        aid = auth.get("authorId")
        if aid:
            author_ids_list.append(str(aid))
            
    # 4. Fuente y Año
    source_title = paper.get("venue") or ""
    if not source_title and isinstance(paper.get("publicationVenue"), dict):
        source_title = paper["publicationVenue"].get("name") or ""
        
    year = paper.get("year")
    try:
        year = int(year) if year is not None else None
    except (ValueError, TypeError):
        year = None
        
    # 5. Citas
    citation_count = paper.get("citationCount", 0)
    try:
        citations = int(citation_count) if citation_count is not None else 0
    except (ValueError, TypeError):
        citations = 0
        
    # 6. Campos temáticos / Palabras clave
    keywords_author = []
    fields = paper.get("fieldsOfStudy") or []
    if isinstance(fields, list):
        keywords_author = [f for f in fields if isinstance(f, str)]
        
    keywords_plus = []
    s2_fields = paper.get("s2FieldsOfStudy") or []
    if isinstance(s2_fields, list):
        for sf in s2_fields:
            if isinstance(sf, dict) and "category" in sf:
                keywords_plus.append(sf["category"])
                
    # 7. Acceso Abierto
    oa_pdf = paper.get("openAccessPdf")
    is_oa = 1 if oa_pdf else 0
    oa_status = "gold" if is_oa == 1 else "closed"
    
    # 8. Referencias si vienen incluidas
    references_list = []
    refs = paper.get("references") or []
    if isinstance(refs, list):
        for r in refs:
            if isinstance(r, dict) and r.get("paperId"):
                references_list.append(r["paperId"])
                
    return {
        "id": paper_id,
        "title": title,
        "abstract": abstract,
        "authors": "; ".join(authors_list),
        "author_ids": "; ".join(author_ids_list),
        "year": year,
        "source_title": source_title,
        "citations": citations,
        "doi": doi,
        "keywords_author": "; ".join(keywords_author),
        "keywords_plus": "; ".join(keywords_plus),
        "affiliations": "; ".join(affiliations_list),
        "country_codes": "",
        "oa_status": oa_status,
        "is_oa": is_oa,
        "fwci": None,  # Reporte de citas brutas conforme a especificación
        "percentile": None,
        "apc_paid_usd": None,
        "language": "",
        "references": "; ".join(references_list)
    }

def fetch_s2_search_papers(query: str, year_range: Optional[str],
                           limit: int, api_key: Optional[str]) -> List[Dict[str, Any]]:
    """Busca artículos usando S2 Graph API /paper/search con paginación por offset."""
    url = f"{S2_BASE_URL}/paper/search"
    headers = {"User-Agent": "KnoMap-S2Harvester/1.0"}
    if api_key:
        headers["x-api-key"] = api_key
        
    params = {
        "query": query,
        "fields": DEFAULT_PAPER_FIELDS,
        "limit": min(limit, 100),
        "offset": 0
    }
    if year_range:
        params["year"] = year_range
        
    papers = []
    delay = 0.2 if api_key else 1.0  # Respetar rate limiting de S2
    
    while len(papers) < limit:
        batch_limit = min(100, limit - len(papers))
        params["limit"] = batch_limit
        
        retries_429 = 0
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            while resp.status_code == 429 and retries_429 < 3:
                retries_429 += 1
                sys.stderr.write(f"[S2 Harvester] Rate limit público alcanzado (429). Reintento {retries_429}/3 esperando 3.0s...\n")
                time.sleep(3.0)
                resp = requests.get(url, headers=headers, params=params, timeout=30)
                
            if resp.status_code == 429:
                sys.stderr.write("[S2 Harvester] Límite de la API pública de Semantic Scholar agotado. Se sugiere configurar S2_API_KEY en .env.\n")
                break
                
            resp.raise_for_status()
            data = resp.json()
            batch = data.get("data", [])
            if not batch:
                break
                
            papers.extend(batch)
            params["offset"] += len(batch)
            total = data.get("total", 0)
            
            if params["offset"] >= total or len(batch) < batch_limit:
                break
                
            time.sleep(delay)
            
        except Exception as e:
            sys.stderr.write(f"[S2 Harvester] Error de consulta: {e}\n")
            break
            
    return papers[:limit]

def fetch_s2_citation_graph(paper_id: str, api_key: Optional[str]) -> Dict[str, Any]:
    """Obtiene el artículo, sus citas entrantes y sus referencias para análisis de red."""
    url = f"{S2_BASE_URL}/paper/{paper_id}"
    headers = {"User-Agent": "KnoMap-S2Harvester/1.0"}
    if api_key:
        headers["x-api-key"] = api_key
        
    fields = f"{DEFAULT_PAPER_FIELDS},citations.paperId,citations.title,citations.year,citations.citationCount,references.paperId,references.title,references.year,references.citationCount"
    params = {"fields": fields}
    
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()

def save_canonical_records(records: List[Dict[str, Any]], output_path: str) -> None:
    """Guarda registros en Parquet, JSON o CSV."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(records)
    
    ext = out.suffix.lower()
    if ext == ".parquet":
        df.to_parquet(out, index=False, engine="pyarrow")
    elif ext == ".csv":
        df.to_csv(out, index=False, encoding="utf-8")
    elif ext == ".json":
        df.to_json(out, orient="records", force_ascii=False, indent=2)
    else:
        df.to_parquet(out.with_suffix(".parquet"), index=False, engine="pyarrow")
        
    print(f"[Éxito] {len(df)} registros recolectados de Semantic Scholar guardados en {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Semantic Scholar Harvester CLI: Extracción de artículos y grafos de citación desde S2 Graph API."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # 1. search-papers
    p_search = subparsers.add_parser("search-papers", help="Búsqueda temática de artículos en Semantic Scholar.")
    p_search.add_argument("--query", type=str, required=True, help="Texto o términos booleanos de búsqueda")
    p_search.add_argument("--year-from", type=int, help="Año inicial")
    p_search.add_argument("--year-to", type=int, help="Año final")
    p_search.add_argument("--limit", type=int, default=50, help="Límite máximo de artículos (default: 50)")
    p_search.add_argument("--output", type=str, required=True, help="Ruta de guardado (.parquet, .json, .csv)")
    p_search.add_argument("--api-key", type=str, help="Clave de API de S2 (opcional, busca S2_API_KEY en .env)")
    
    # 2. citation-graph
    p_graph = subparsers.add_parser("citation-graph", help="Descarga el artículo, sus citas y sus referencias.")
    p_graph.add_argument("--paper-id", type=str, required=True, help="ID de S2, DOI o arXiv ID (ej. 10.1038/nature12345)")
    p_graph.add_argument("--output", type=str, required=True, help="Ruta de guardado del grafo (.parquet, .json)")
    p_graph.add_argument("--api-key", type=str)
    
    # 3. author-papers
    p_auth = subparsers.add_parser("author-papers", help="Descarga las publicaciones de un autor por su S2 Author ID.")
    p_auth.add_argument("--author-id", type=str, required=True, help="Semantic Scholar Author ID")
    p_auth.add_argument("--limit", type=int, default=100, help="Límite máximo de artículos")
    p_auth.add_argument("--output", type=str, required=True, help="Ruta de guardado")
    p_auth.add_argument("--api-key", type=str)

    args = parser.parse_args()
    api_key = args.api_key or get_env_variable("S2_API_KEY")
    
    if args.command == "search-papers":
        year_range = None
        if args.year_from and args.year_to:
            year_range = f"{args.year_from}-{args.year_to}"
        elif args.year_from:
            year_range = f"{args.year_from}-"
        elif args.year_to:
            year_range = f"-{args.year_to}"
            
        print(f"[S2 Harvester] Buscando: '{args.query}' (Rango años: {year_range}, Límite: {args.limit})")
        raw_papers = fetch_s2_search_papers(
            query=args.query,
            year_range=year_range,
            limit=args.limit,
            api_key=api_key
        )
        if not raw_papers:
            print("[Aviso] No se encontraron artículos en Semantic Scholar.")
            sys.exit(0)
            
        canonical_records = [map_s2_paper_to_canonical(p) for p in raw_papers]
        save_canonical_records(canonical_records, args.output)
        
    elif args.command == "citation-graph":
        print(f"[S2 Harvester] Extrayendo grafo de citas para: {args.paper_id}")
        graph_data = fetch_s2_citation_graph(paper_id=args.paper_id, api_key=api_key)
        
        # Combinar el artículo raíz con sus citas y referencias en una sola tabla normalizada
        root_rec = map_s2_paper_to_canonical(graph_data)
        records = [root_rec]
        
        # Añadir citas entrantes
        for cit in graph_data.get("citations", []):
            if cit.get("paperId"):
                records.append({
                    "id": cit["paperId"],
                    "title": cit.get("title") or "",
                    "abstract": "",
                    "authors": "",
                    "author_ids": "",
                    "year": cit.get("year"),
                    "source_title": "",
                    "citations": cit.get("citationCount", 0) or 0,
                    "doi": "",
                    "keywords_author": "",
                    "keywords_plus": "",
                    "affiliations": "",
                    "country_codes": "",
                    "oa_status": "",
                    "is_oa": 0,
                    "fwci": None,
                    "percentile": None,
                    "apc_paid_usd": None,
                    "language": "",
                    "references": args.paper_id  # Apunta al artículo raíz
                })
                
        # Añadir referencias salientes
        for ref in graph_data.get("references", []):
            if ref.get("paperId"):
                records.append({
                    "id": ref["paperId"],
                    "title": ref.get("title") or "",
                    "abstract": "",
                    "authors": "",
                    "author_ids": "",
                    "year": ref.get("year"),
                    "source_title": "",
                    "citations": ref.get("citationCount", 0) or 0,
                    "doi": "",
                    "keywords_author": "",
                    "keywords_plus": "",
                    "affiliations": "",
                    "country_codes": "",
                    "oa_status": "",
                    "is_oa": 0,
                    "fwci": None,
                    "percentile": None,
                    "apc_paid_usd": None,
                    "language": "",
                    "references": ""
                })
                
        save_canonical_records(records, args.output)
        
    elif args.command == "author-papers":
        url = f"{S2_BASE_URL}/author/{args.author_id}/papers"
        headers = {"User-Agent": "KnoMap-S2Harvester/1.0"}
        if api_key:
            headers["x-api-key"] = api_key
        params = {"fields": DEFAULT_PAPER_FIELDS, "limit": min(args.limit, 100)}
        
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        raw_papers = resp.json().get("data", [])
        
        canonical_records = [map_s2_paper_to_canonical(p) for p in raw_papers]
        save_canonical_records(canonical_records, args.output)

if __name__ == "__main__":
    main()
