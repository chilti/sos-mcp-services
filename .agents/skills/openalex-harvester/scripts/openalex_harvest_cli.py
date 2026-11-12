#!/usr/bin/env python3
"""
OpenAlex Data Harvester CLI
---------------------------
Standalone tool for harvesting, cursor-paginating, and standardizing scientific
publications from OpenAlex (public API or local endpoint) into the canonical
tabular schema (Parquet, JSON, CSV).
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

MESSAGES = {
    "en": {
        "local_unavailable": "[OpenAlex Harvester] Local endpoint ({base_url}) unavailable ({code}). Connecting to {default_url}...\n",
        "local_error": "[OpenAlex Harvester] Local endpoint error: {e}. Retrying at {default_url}...\n",
        "public_failed": "[Error] Connection to public OpenAlex failed: {e2}\n",
        "page_error": "[Warning] Connection error on page {page}: {e}\n",
        "saved": "[Success] {n} records harvested and saved to {path}",
        "connecting": "[OpenAlex Harvester] Connecting to {base_url}...",
        "query_params": "[OpenAlex Harvester] Query parameters: {params}",
        "no_results": "[Notice] No results found matching the provided filters.",
    },
    "es": {
        "local_unavailable": "[OpenAlex Harvester] Endpoint local ({base_url}) no disponible ({code}). Conectando a {default_url}...\n",
        "local_error": "[OpenAlex Harvester] Error en endpoint local: {e}. Reintentando en {default_url}...\n",
        "public_failed": "[Error] Falló conexión a OpenAlex público: {e2}\n",
        "page_error": "[Advertencia] Error de conexión en página {page}: {e}\n",
        "saved": "[Éxito] {n} registros recolectados y guardados en {path}",
        "connecting": "[OpenAlex Harvester] Conectando a {base_url}...",
        "query_params": "[OpenAlex Harvester] Parámetros de consulta: {params}",
        "no_results": "[Aviso] No se encontraron resultados con los filtros proporcionados.",
    }
}

def get_env_variable(key: str, default: Optional[str] = None) -> Optional[str]:
    """Look up an environment variable in os.environ or common .env files."""
    if os.environ.get(key):
        return os.environ.get(key)
    env_paths = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[3] / ".env",
        Path.cwd() / ".env"
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
    """Reconstruct continuous abstract text from OpenAlex abstract_inverted_index."""
    if not abstract_inverted_index or not isinstance(abstract_inverted_index, dict):
        return ""
    token_positions = []
    for word, positions in abstract_inverted_index.items():
        for pos in positions:
            token_positions.append((pos, word))
    token_positions.sort(key=lambda x: x[0])
    return " ".join(word for _, word in token_positions)

def map_openalex_work_to_canonical(work: Dict[str, Any]) -> Dict[str, Any]:
    """Map an OpenAlex work object to the canonical tabular schema."""
    # 1. Identifiers
    work_id = work.get("id", "")
    if work_id.startswith("https://openalex.org/"):
        work_id = work_id.replace("https://openalex.org/", "")
    doi = work.get("doi") or ""
    if doi.startswith("https://doi.org/"):
        doi = doi.replace("https://doi.org/", "")
    
    # 2. Title and Abstract
    title = work.get("title") or ""
    abstract = reconstruct_abstract(work.get("abstract_inverted_index"))
    
    # 3. Authors and Affiliations
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
    
    # 4. Source / Journal
    primary_loc = work.get("primary_location") or {}
    source = primary_loc.get("source") or {}
    source_title = source.get("display_name") or ""
    
    # 5. Year and Citations
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
        
    # 6. Keywords / Concepts / Topics
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
            
    # Include primary topic if available
    primary_topic = work.get("primary_topic") or {}
    topic_name = primary_topic.get("display_name")
    if topic_name and topic_name not in keywords_plus_list:
        keywords_plus_list.insert(0, topic_name)
        
    keywords_author_str = "; ".join(keywords_author_list)
    keywords_plus_str = "; ".join(keywords_plus_list)
    
    # 7. Open Access
    oa_info = work.get("open_access") or {}
    oa_status = (oa_info.get("oa_status") or "closed").lower()
    is_oa = 1 if oa_info.get("is_oa") else 0
    
    # 8. Advanced Metrics (FWCI, Percentile, APC)
    fwci = work.get("fwci")
    if fwci is not None:
        try:
            fwci = float(fwci)
        except (ValueError, TypeError):
            fwci = None
            
    percentile_data = work.get("citation_normalized_percentile") or {}
    percentile_val = percentile_data.get("value")
    if percentile_val is not None:
        try:
            percentile_val = float(percentile_val)
        except (ValueError, TypeError):
            percentile_val = None
            
    apc_paid_usd = None
    apc_paid_data = work.get("apc_paid")
    if isinstance(apc_paid_data, dict):
        val = apc_paid_data.get("value_usd")
        if val is not None:
            try:
                apc_paid_usd = float(val)
            except (ValueError, TypeError):
                apc_paid_usd = None
                
    # 9. References
    referenced_works = work.get("referenced_works") or []
    references_str = "; ".join([r.replace("https://openalex.org/", "") for r in referenced_works])
    
    # 10. Language
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
                          mailto: str = "agent@knomap.org", lang: str = "en") -> List[Dict[str, Any]]:
    """Download records using OpenAlex cursor pagination."""
    msg = MESSAGES.get(lang, MESSAGES["en"])
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
                sys.stderr.write(msg["local_unavailable"].format(
                    base_url=base_url, code=resp.status_code, default_url=DEFAULT_API_URL
                ))
                current_url = f"{DEFAULT_API_URL.rstrip('/')}/{endpoint.lstrip('/')}"
                resp = requests.get(current_url, params=params, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            if base_url != DEFAULT_API_URL and current_url != f"{DEFAULT_API_URL.rstrip('/')}/{endpoint.lstrip('/')}":
                sys.stderr.write(msg["local_error"].format(e=e, default_url=DEFAULT_API_URL))
                current_url = f"{DEFAULT_API_URL.rstrip('/')}/{endpoint.lstrip('/')}"
                try:
                    resp = requests.get(current_url, params=params, headers=headers, timeout=30)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e2:
                    sys.stderr.write(msg["public_failed"].format(e2=e2))
                    break
            else:
                sys.stderr.write(msg["page_error"].format(page=page, e=e))
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
                
        # Gentle courtesy delay
        time.sleep(0.1 if api_key else 0.25)
        
    return all_works[:limit]

def save_canonical_records(records: List[Dict[str, Any]], output_path: str, lang: str = "en") -> None:
    """Save normalized records in Parquet, JSON, or CSV format according to file extension."""
    msg = MESSAGES.get(lang, MESSAGES["en"])
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
        
    print(msg["saved"].format(n=len(df), path=output_path))

def main():
    parser = argparse.ArgumentParser(
        description="OpenAlex Harvester CLI: Download and normalize scientific literature from OpenAlex."
    )
    parser.add_argument(
        "--lang",
        type=str,
        choices=["en", "es"],
        default="en",
        help="Output language for labels/messages (en or es)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # 1. fetch-works
    p_works = subparsers.add_parser("fetch-works", help="Harvest works by general query, topics, or filters.")
    p_works.add_argument("--query", type=str, help="Search terms in title and abstract")
    p_works.add_argument("--author-id", type=str, help="OpenAlex Author ID (e.g., A5023888391) or ORCID")
    p_works.add_argument("--ror", type=str, help="Institutional ROR ID (e.g., 012gw1n35)")
    p_works.add_argument("--issn", type=str, help="Journal or source ISSN")
    p_works.add_argument("--topic", type=str, help="OpenAlex Topic ID (e.g., T10001)")
    p_works.add_argument("--year-from", type=int, help="Start year (inclusive)")
    p_works.add_argument("--year-to", type=int, help="End year (inclusive)")
    p_works.add_argument("--oa-status", type=str, choices=["gold", "diamond", "green", "hybrid", "bronze", "closed"],
                         help="Filter by Open Access route")
    p_works.add_argument("--limit", type=int, default=50, help="Maximum number of articles to harvest (default: 50)")
    p_works.add_argument("--output", type=str, required=True, help="Output file path (.parquet, .json, .csv)")
    p_works.add_argument("--api-url", type=str, help="Base OpenAlex API URL (default: https://api.openalex.org)")
    p_works.add_argument("--api-key", type=str, help="OpenAlex API Key (optional, checks OPENALEX_API_KEY in .env)")
    p_works.add_argument("--lang", type=str, choices=["en", "es"], default="en", help="Output language for labels/messages (en or es)")
    
    # 2. fetch-author-works
    p_author = subparsers.add_parser("fetch-author-works", help="Harvest the complete scientific output of an author.")
    p_author.add_argument("--author-id", type=str, required=True, help="Researcher OpenAlex ID or ORCID")
    p_author.add_argument("--limit", type=int, default=200, help="Maximum number of works (default: 200)")
    p_author.add_argument("--output", type=str, required=True, help="Output file path")
    p_author.add_argument("--api-url", type=str, help="Base OpenAlex API URL")
    p_author.add_argument("--api-key", type=str, help="OpenAlex API Key")
    p_author.add_argument("--lang", type=str, choices=["en", "es"], default="en", help="Output language for labels/messages (en or es)")
    
    # 3. fetch-institution-works
    p_inst = subparsers.add_parser("fetch-institution-works", help="Harvest works affiliated with an institution.")
    p_inst.add_argument("--ror", type=str, required=True, help="ROR identifier (e.g., 012gw1n35 for UNAM)")
    p_inst.add_argument("--year-from", type=int, help="Start year")
    p_inst.add_argument("--year-to", type=int, help="End year")
    p_inst.add_argument("--limit", type=int, default=200, help="Maximum number of works (default: 200)")
    p_inst.add_argument("--output", type=str, required=True, help="Output file path")
    p_inst.add_argument("--api-url", type=str, help="Base OpenAlex API URL")
    p_inst.add_argument("--api-key", type=str, help="OpenAlex API Key")
    p_inst.add_argument("--lang", type=str, choices=["en", "es"], default="en", help="Output language for labels/messages (en or es)")

    args = parser.parse_args()
    lang = getattr(args, "lang", "en") or "en"
    msg = MESSAGES.get(lang, MESSAGES["en"])
    
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
        
    print(msg["connecting"].format(base_url=base_url))
    print(msg["query_params"].format(params=params))
    
    raw_works = fetch_openalex_records(
        base_url=base_url,
        endpoint="works",
        params=params,
        api_key=api_key,
        limit=args.limit,
        lang=lang
    )
    
    if not raw_works:
        print(msg["no_results"])
        sys.exit(0)
        
    canonical_records = [map_openalex_work_to_canonical(w) for w in raw_works]
    save_canonical_records(canonical_records, args.output, lang=lang)

if __name__ == "__main__":
    main()
