#!/usr/bin/env /home/ambientesPy/revistaslatam/bin/python
"""
Scopus Data Harvester CLI
-------------------------
Herramienta autónoma para la consulta y extracción de publicaciones científicas
desde la API de Elsevier Scopus, con control estricto de cuota (HTTP 429 backoff)
y normalización directa al esquema tabular canónico (Parquet, JSON, CSV).
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

SCOPUS_SEARCH_URL = "https://api.elsevier.com/content/search/scopus"

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

def map_scopus_entry_to_canonical(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Mapea una entrada individual de Scopus al esquema tabular canónico."""
    # 1. Identificadores
    raw_id = entry.get("dc:identifier", "")
    work_id = raw_id.replace("SCOPUS_ID:", "") if raw_id.startswith("SCOPUS_ID:") else raw_id
    doi = entry.get("prism:doi") or ""
    
    # 2. Título
    title = entry.get("dc:title") or ""
    
    # 3. Autores
    authors_list = []
    if "author" in entry and isinstance(entry["author"], list):
        for auth in entry["author"]:
            auth_name = auth.get("authname") or auth.get("given-name", "") + " " + auth.get("surname", "")
            if auth_name.strip():
                authors_list.append(auth_name.strip())
    elif "dc:creator" in entry and entry["dc:creator"]:
        authors_list.append(str(entry["dc:creator"]).strip())
        
    authors_str = "; ".join(authors_list)
    
    # 4. Afiliaciones
    affiliations_list = []
    country_set = set()
    if "affiliation" in entry and isinstance(entry["affiliation"], list):
        for aff in entry["affiliation"]:
            aff_name = aff.get("affilname")
            if aff_name and aff_name not in affiliations_list:
                affiliations_list.append(aff_name)
            country = aff.get("affiliation-country")
            if country:
                country_set.add(country)
    elif "affiliation" in entry and isinstance(entry["affiliation"], dict):
        aff_name = entry["affiliation"].get("affilname")
        if aff_name:
            affiliations_list.append(aff_name)
        country = entry["affiliation"].get("affiliation-country")
        if country:
            country_set.add(country)
            
    affiliations_str = "; ".join(affiliations_list)
    country_codes_str = "; ".join(sorted(list(country_set)))
    
    # 5. Año y Fuente
    source_title = entry.get("prism:publicationName") or ""
    cover_date = entry.get("prism:coverDate") or ""
    year = None
    if cover_date and len(cover_date) >= 4:
        try:
            year = int(cover_date[:4])
        except ValueError:
            year = None
            
    # 6. Citas
    citedby = entry.get("citedby-count", 0)
    try:
        citations = int(citedby)
    except (ValueError, TypeError):
        citations = 0
        
    # 7. Acceso Abierto
    is_oa_val = entry.get("openaccess")
    is_oa = 1 if (is_oa_val == "1" or entry.get("openaccessFlag") is True) else 0
    oa_status = "gold" if is_oa == 1 else "closed"
    
    # 8. Resumen y Palabras clave (pueden venir o no en la búsqueda estándar)
    abstract = entry.get("dc:description") or ""
    keywords_str = entry.get("authkeywords") or ""
    if isinstance(keywords_str, list):
        keywords_str = "; ".join(keywords_str)
        
    return {
        "id": work_id,
        "title": title,
        "abstract": abstract,
        "authors": authors_str,
        "author_ids": "",
        "year": year,
        "source_title": source_title,
        "citations": citations,
        "doi": doi,
        "keywords_author": keywords_str,
        "keywords_plus": "",
        "affiliations": affiliations_str,
        "country_codes": country_codes_str,
        "oa_status": oa_status,
        "is_oa": is_oa,
        "fwci": None,  # Decisión del usuario: citas brutas sin suponer FWCI
        "percentile": None,
        "apc_paid_usd": None,
        "language": "",
        "references": ""
    }

def execute_scopus_search(query: str, api_key: str, limit: int,
                          batch_size: int = 25) -> List[Dict[str, Any]]:
    """Ejecuta búsquedas paginadas contra la API de Elsevier Scopus."""
    headers = {
        "X-ELS-APIKey": api_key,
        "Accept": "application/json"
    }
    
    results = []
    start = 0
    
    while len(results) < limit:
        count = min(batch_size, limit - len(results))
        params = {
            "query": query,
            "count": count,
            "start": start,
            "view": "STANDARD"
        }
        
        try:
            resp = requests.get(SCOPUS_SEARCH_URL, headers=headers, params=params, timeout=30)
            
            if resp.status_code == 429:
                sys.stderr.write("[Scopus Harvester] Límite de cuota alcanzado (429). Esperando 5 segundos...\n")
                time.sleep(5.0)
                continue
                
            if resp.status_code != 200:
                sys.stderr.write(f"[Scopus Harvester] Error {resp.status_code}: {resp.text}\n")
                break
                
            data = resp.json()
            search_results = data.get("search-results", {})
            total_available = int(search_results.get("opensearch:totalResults", 0))
            entries = search_results.get("entry", [])
            
            if not entries or (len(entries) == 1 and "error" in entries[0]):
                break
                
            results.extend(entries)
            start += len(entries)
            
            if start >= total_available or len(entries) < count:
                break
                
            # Pausa de cortesía
            time.sleep(0.3)
            
        except Exception as e:
            sys.stderr.write(f"[Scopus Harvester] Error de red: {e}\n")
            break
            
    return results[:limit]

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
        
    print(f"[Éxito] {len(df)} registros recolectados de Scopus guardados en {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Scopus Harvester CLI: Recolección y normalización de artículos desde la API de Elsevier Scopus."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # 1. search
    p_search = subparsers.add_parser("search", help="Búsqueda avanzada con operadores Scopus.")
    p_search.add_argument("--query", type=str, required=True, help="Consulta con sintaxis Scopus (TITLE-ABS-KEY, AUTH, etc.)")
    p_search.add_argument("--year-from", type=int, help="Año de inicio (filtro PUBYEAR > ...)")
    p_search.add_argument("--year-to", type=int, help="Año de fin")
    p_search.add_argument("--limit", type=int, default=50, help="Límite de documentos (default: 50)")
    p_search.add_argument("--output", type=str, required=True, help="Archivo de salida (.parquet, .json, .csv)")
    p_search.add_argument("--api-key", type=str, help="Clave de API Elsevier (busca SCOPUS_API_KEY en .env)")
    
    # 2. author-profile
    p_author = subparsers.add_parser("author-profile", help="Recolecta publicaciones de un autor por su AU-ID.")
    p_author.add_argument("--author-id", type=str, required=True, help="Scopus Author ID (ej. 57200234567)")
    p_author.add_argument("--limit", type=int, default=100, help="Límite de publicaciones")
    p_author.add_argument("--output", type=str, required=True, help="Archivo de salida")
    p_author.add_argument("--api-key", type=str)
    
    # 3. affil-works
    p_affil = subparsers.add_parser("affil-works", help="Recolecta publicaciones de una afiliación por su AF-ID.")
    p_affil.add_argument("--af-id", type=str, required=True, help="Scopus Affiliation ID (ej. 60028190)")
    p_affil.add_argument("--year-from", type=int, help="Año inicial")
    p_affil.add_argument("--year-to", type=int, help="Año final")
    p_affil.add_argument("--limit", type=int, default=100, help="Límite de publicaciones")
    p_affil.add_argument("--output", type=str, required=True, help="Archivo de salida")
    p_affil.add_argument("--api-key", type=str)
    
    args = parser.parse_args()
    
    api_key = args.api_key or get_env_variable("SCOPUS_API_KEY")
    if not api_key:
        sys.stderr.write("[Error] Se requiere una API Key de Elsevier. Configura SCOPUS_API_KEY en .env o usa --api-key.\n")
        sys.exit(1)
        
    query = ""
    if args.command == "search":
        query_parts = [args.query]
        if args.year_from and args.year_to:
            query_parts.append(f"PUBYEAR >= {args.year_from} AND PUBYEAR <= {args.year_to}")
        elif args.year_from:
            query_parts.append(f"PUBYEAR >= {args.year_from}")
        elif args.year_to:
            query_parts.append(f"PUBYEAR <= {args.year_to}")
        query = " AND ".join([f"({p})" for p in query_parts])
        
    elif args.command == "author-profile":
        query = f"AU-ID({args.author_id.strip()})"
        
    elif args.command == "affil-works":
        query_parts = [f"AF-ID({args.af_id.strip()})"]
        if args.year_from and args.year_to:
            query_parts.append(f"PUBYEAR >= {args.year_from} AND PUBYEAR <= {args.year_to}")
        query = " AND ".join(query_parts)
        
    print(f"[Scopus Harvester] Ejecutando consulta: {query}")
    print(f"[Scopus Harvester] Límite solicitado: {args.limit}")
    
    entries = execute_scopus_search(query=query, api_key=api_key, limit=args.limit)
    
    if not entries:
        print("[Aviso] No se obtuvieron registros de Scopus para esta consulta.")
        sys.exit(0)
        
    canonical_records = [map_scopus_entry_to_canonical(e) for e in entries]
    save_canonical_records(canonical_records, args.output)

if __name__ == "__main__":
    main()
