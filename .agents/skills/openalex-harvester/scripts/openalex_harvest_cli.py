#!/usr/bin/env /home/ambientesPy/revistaslatam/bin/python
"""
OpenAlex Data Harvester CLI
---------------------------
Herramienta autónoma e independiente para la recolección, paginación por cursor y
estandarización de publicaciones científicas desde OpenAlex (API pública o endpoint local)
hacia el esquema tabular canónico (Parquet, JSON, CSV).
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

DEFAULT_API_URL = "https://api.openalex.org"

def get_env_variable(key: str, default: Optional[str] = None) -> Optional[str]:
    """Busca una variable en el entorno o en archivos .env comunes."""
    if os.environ.get(key):
        return os.environ.get(key)
    # Buscar en archivos .env cercanos
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

def reconstruct_abstract(abstract_inverted_index: Optional[Dict[str, List[int]]]) -> str:
    """Reconstruye el texto continuo de un resumen a partir del abstract_inverted_index de OpenAlex."""
    if not abstract_inverted_index or not isinstance(abstract_inverted_index, dict):
        return ""
    token_positions = []
    for word, positions in abstract_inverted_index.items():
        for pos in positions:
            token_positions.append((pos, word))
    token_positions.sort(key=lambda x: x[0])
    return " ".join(word for _, word in token_positions)

def map_openalex_work_to_canonical(work: Dict[str, Any]) -> Dict[str, Any]:
    """Mapea un objeto de trabajo de OpenAlex al esquema tabular canónico."""
    # 1. Identificadores
    work_id = work.get("id", "")
    if work_id.startswith("https://openalex.org/"):
        work_id = work_id.replace("https://openalex.org/", "")
    doi = work.get("doi") or ""
    if doi.startswith("https://doi.org/"):
        doi = doi.replace("https://doi.org/", "")
    
    # 2. Título y Resumen
    title = work.get("title") or ""
    abstract = reconstruct_abstract(work.get("abstract_inverted_index"))
    
    # 3. Autores y Afiliaciones
    authors_list = []
    author_ids_list = []
    affiliations_list = []
    country_codes_set = set()
    
    for auth in work.get("authorships", []):
        author_data = auth.get("author", {})
        display_name = author_data.get("display_name")
        if display_name:
            authors_list.append(display_name)
        aid = author_data.get("id", "")
        if aid:
            author_ids_list.append(aid.replace("https://openalex.org/", ""))
            
        for inst in auth.get("institutions", []):
            inst_name = inst.get("display_name")
            if inst_name and inst_name not in affiliations_list:
                affiliations_list.append(inst_name)
            cc = inst.get("country_code")
            if cc:
                country_codes_set.add(cc)
                
        for cc in auth.get("countries", []):
            if cc:
                country_codes_set.add(cc)
                
    authors_str = "; ".join(authors_list)
    affiliations_str = "; ".join(affiliations_list)
    country_codes_str = "; ".join(sorted(list(country_codes_set)))
    
    # 4. Fuente / Revista
    primary_loc = work.get("primary_location") or {}
    source = primary_loc.get("source") or {}
    source_title = source.get("display_name") or ""
    
    # 5. Año y Citas
    year = work.get("publication_year")
    try:
        year = int(year) if year is not None else None
    except (ValueError, TypeError):
        year = None
    citations = work.get("cited_by_count", 0)
    try:
        citations = int(citations)
    except (ValueError, TypeError):
        citations = 0
        
    # 6. Palabras clave / Conceptos / Tópicos
    keywords_author_list = []
    keywords_plus_list = []
    
    for kw in work.get("keywords", []):
        kw_name = kw.get("display_name")
        if kw_name:
            keywords_author_list.append(kw_name)
            
    for concept in work.get("concepts", []):
        concept_name = concept.get("display_name")
        if concept_name:
            keywords_plus_list.append(concept_name)
            
    # Si viene tópico primario
    primary_topic = work.get("primary_topic") or {}
    topic_name = primary_topic.get("display_name")
    if topic_name and topic_name not in keywords_plus_list:
        keywords_plus_list.insert(0, topic_name)
        
    keywords_author_str = "; ".join(keywords_author_list)
    keywords_plus_str = "; ".join(keywords_plus_list)
    
    # 7. Acceso Abierto
    oa_info = work.get("open_access") or {}
    oa_status = (oa_info.get("oa_status") or "closed").lower()
    is_oa = 1 if oa_info.get("is_oa") else 0
    
    # 8. Métricas avanzadas (FWCI, Percentil, APC)
    fwci = work.get("fwci")
    if fwci is not None:
        try:
            fwci = float(fwci)
        except (ValueError, TypeError):
            fwci = None
            
    # Percentil de citas si está disponible en citation_normalized_percentile
    percentile_data = work.get("citation_normalized_percentile") or {}
    percentile_val = percentile_data.get("value")
    if percentile_val is not None:
        try:
            percentile_val = float(percentile_val)
        except (ValueError, TypeError):
            percentile_val = None
            
    # APC estimado
    apc_paid_usd = None
    apc_paid_data = work.get("apc_paid")
    if isinstance(apc_paid_data, dict):
        val = apc_paid_data.get("value_usd")
        if val is not None:
            try:
                apc_paid_usd = float(val)
            except (ValueError, TypeError):
                apc_paid_usd = None
                
    # 9. Referencias
    referenced_works = work.get("referenced_works") or []
    references_str = "; ".join([r.replace("https://openalex.org/", "") for r in referenced_works])
    
    # 10. Idioma
    language = work.get("language") or ""
    
    return {
        "id": work_id,
        "title": title,
        "abstract": abstract,
        "authors": authors_str,
        "author_ids": "; ".join(author_ids_list),
        "year": year,
        "source_title": source_title,
        "citations": citations,
        "doi": doi,
        "keywords_author": keywords_author_str,
        "keywords_plus": keywords_plus_str,
        "affiliations": affiliations_str,
        "country_codes": country_codes_str,
        "oa_status": oa_status,
        "is_oa": is_oa,
        "fwci": fwci,
        "percentile": percentile_val,
        "apc_paid_usd": apc_paid_usd,
        "language": language,
        "references": references_str
    }

def fetch_openalex_records(base_url: str, endpoint: str, params: Dict[str, Any],
                          api_key: Optional[str], limit: int,
                          mailto: str = "agent@knomap.org") -> List[Dict[str, Any]]:
    """Descarga registros usando cursor pagination de OpenAlex."""
    headers = {"User-Agent": f"KnoMap-Harvester/1.0 (mailto:{mailto})"}
    if api_key:
        headers["api-key"] = api_key
        
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    params["per-page"] = min(limit, 100)
    params["cursor"] = "*"
    
    all_works = []
    page = 1
    current_url = url
    
    while len(all_works) < limit:
        remaining = limit - len(all_works)
        if remaining < params["per-page"]:
            params["per-page"] = remaining
            
        try:
            resp = requests.get(current_url, params=params, headers=headers, timeout=30)
            if resp.status_code == 429:
                time.sleep(2.0)
                continue
            if resp.status_code >= 500 and base_url != DEFAULT_API_URL:
                sys.stderr.write(f"[OpenAlex Harvester] Endpoint local ({base_url}) no disponible ({resp.status_code}). Conectando a {DEFAULT_API_URL}...\n")
                current_url = f"{DEFAULT_API_URL.rstrip('/')}/{endpoint.lstrip('/')}"
                resp = requests.get(current_url, params=params, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            if base_url != DEFAULT_API_URL and current_url != f"{DEFAULT_API_URL.rstrip('/')}/{endpoint.lstrip('/')}":
                sys.stderr.write(f"[OpenAlex Harvester] Error en endpoint local: {e}. Reintentando en {DEFAULT_API_URL}...\n")
                current_url = f"{DEFAULT_API_URL.rstrip('/')}/{endpoint.lstrip('/')}"
                try:
                    resp = requests.get(current_url, params=params, headers=headers, timeout=30)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e2:
                    sys.stderr.write(f"[Error] Falló conexión a OpenAlex público: {e2}\n")
                    break
            else:
                sys.stderr.write(f"[Advertencia] Error de conexión en página {page}: {e}\n")
                break
            
        results = data.get("results", [])
        if not results:
            break
            
        all_works.extend(results)
        
        meta = data.get("meta", {})
        next_cursor = meta.get("next_cursor")
        if len(all_works) >= limit:
            break
            
        if next_cursor:
            params["cursor"] = next_cursor
        else:
            page += 1
            params.pop("cursor", None)
            params["page"] = page
            total_count = meta.get("count")
            if total_count is not None and len(all_works) >= total_count:
                break
                
        # Pausa suave
        time.sleep(0.1 if api_key else 0.25)
        
    return all_works[:limit]

def save_canonical_records(records: List[Dict[str, Any]], output_path: str) -> None:
    """Guarda los registros normalizados en Parquet, JSON o CSV según la extensión."""
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
        
    print(f"[Éxito] {len(df)} registros recolectados y guardados en {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description="OpenAlex Harvester CLI: Descarga y normalización de literatura científica desde OpenAlex."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # 1. fetch-works
    p_works = subparsers.add_parser("fetch-works", help="Recolecta trabajos por consulta general, tópicos o filtros.")
    p_works.add_argument("--query", type=str, help="Términos de búsqueda en título y resumen")
    p_works.add_argument("--author-id", type=str, help="ID de autor OpenAlex (ej. A5023888391) o ORCID")
    p_works.add_argument("--ror", type=str, help="ID ROR institucional (ej. 012gw1n35)")
    p_works.add_argument("--issn", type=str, help="ISSN de revista o fuente")
    p_works.add_argument("--topic", type=str, help="ID de Tópico OpenAlex (ej. T10001)")
    p_works.add_argument("--year-from", type=int, help="Año de inicio (inclusive)")
    p_works.add_argument("--year-to", type=int, help="Año de fin (inclusive)")
    p_works.add_argument("--oa-status", type=str, choices=["gold", "diamond", "green", "hybrid", "bronze", "closed"],
                         help="Filtrar por vía de Acceso Abierto")
    p_works.add_argument("--limit", type=int, default=50, help="Número máximo de artículos a recolectar (default: 50)")
    p_works.add_argument("--output", type=str, required=True, help="Ruta del archivo de salida (.parquet, .json, .csv)")
    p_works.add_argument("--api-url", type=str, help="URL base de la API OpenAlex (default: https://api.openalex.org)")
    p_works.add_argument("--api-key", type=str, help="API Key de OpenAlex (opcional, busca OPENALEX_API_KEY en .env)")
    
    # 2. fetch-author-works
    p_author = subparsers.add_parser("fetch-author-works", help="Recolecta la producción científica completa de un autor.")
    p_author.add_argument("--author-id", type=str, required=True, help="ID OpenAlex o ORCID del investigador")
    p_author.add_argument("--limit", type=int, default=200, help="Límite máximo de trabajos (default: 200)")
    p_author.add_argument("--output", type=str, required=True, help="Ruta del archivo de salida")
    p_author.add_argument("--api-url", type=str)
    p_author.add_argument("--api-key", type=str)
    
    # 3. fetch-institution-works
    p_inst = subparsers.add_parser("fetch-institution-works", help="Recolecta trabajos afiliados a una institución.")
    p_inst.add_argument("--ror", type=str, required=True, help="Identificador ROR (ej. 012gw1n35 para UNAM)")
    p_inst.add_argument("--year-from", type=int, help="Año inicial")
    p_inst.add_argument("--year-to", type=int, help="Año final")
    p_inst.add_argument("--limit", type=int, default=200, help="Límite máximo de trabajos (default: 200)")
    p_inst.add_argument("--output", type=str, required=True, help="Ruta del archivo de salida")
    p_inst.add_argument("--api-url", type=str)
    p_inst.add_argument("--api-key", type=str)

    args = parser.parse_args()
    
    base_url = args.api_url or get_env_variable("OPENALEX_API_URL") or DEFAULT_API_URL
    api_key = args.api_key or get_env_variable("OPENALEX_API_KEY")
    
    filter_parts = []
    params = {}
    
    if args.command == "fetch-works":
        if args.query:
            params["search"] = args.query
        if args.author_id:
            aid = args.author_id.strip()
            if aid.startswith("0000-") or aid.startswith("https://orcid.org/"):
                filter_parts.append(f"author.orcid:{aid}")
            else:
                filter_parts.append(f"author.id:{aid}")
        if args.ror:
            filter_parts.append(f"institutions.ror:{args.ror}")
        if args.issn:
            filter_parts.append(f"primary_location.source.issn:{args.issn}")
        if args.topic:
            filter_parts.append(f"primary_topic.id:{args.topic}")
        if args.year_from and args.year_to:
            filter_parts.append(f"publication_year:{args.year_from}-{args.year_to}")
        elif args.year_from:
            filter_parts.append(f"from_publication_date:{args.year_from}-01-01")
        elif args.year_to:
            filter_parts.append(f"to_publication_date:{args.year_to}-12-31")
        if args.oa_status:
            filter_parts.append(f"open_access.oa_status:{args.oa_status}")
            
    elif args.command == "fetch-author-works":
        aid = args.author_id.strip()
        if aid.startswith("0000-") or aid.startswith("https://orcid.org/"):
            filter_parts.append(f"author.orcid:{aid}")
        else:
            filter_parts.append(f"author.id:{aid}")
            
    elif args.command == "fetch-institution-works":
        filter_parts.append(f"institutions.ror:{args.ror.strip()}")
        if args.year_from and args.year_to:
            filter_parts.append(f"publication_year:{args.year_from}-{args.year_to}")
        elif args.year_from:
            filter_parts.append(f"from_publication_date:{args.year_from}-01-01")
        elif args.year_to:
            filter_parts.append(f"to_publication_date:{args.year_to}-12-31")

    if filter_parts:
        params["filter"] = ",".join(filter_parts)
        
    print(f"[OpenAlex Harvester] Conectando a {base_url}...")
    print(f"[OpenAlex Harvester] Parámetros de consulta: {params}")
    
    raw_works = fetch_openalex_records(
        base_url=base_url,
        endpoint="works",
        params=params,
        api_key=api_key,
        limit=args.limit
    )
    
    if not raw_works:
        print("[Aviso] No se encontraron resultados con los filtros proporcionados.")
        sys.exit(0)
        
    canonical_records = [map_openalex_work_to_canonical(w) for w in raw_works]
    save_canonical_records(canonical_records, args.output)

if __name__ == "__main__":
    main()
