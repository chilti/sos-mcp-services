#!/usr/bin/env python3
"""
arXiv Data Harvester CLI
------------------------
Standalone tool for querying and downloading preprint metadata from the
arXiv Atom XML API (export.arxiv.org/api/query), enforcing the mandatory
3.0-second courtesy delay and normalizing records into the canonical tabular schema.
"""

import sys
import os
import argparse
import time
import requests
import pandas as pd
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Optional

ARXIV_API_URL = "https://export.arxiv.org/api/query"

ATOM_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom"
}

MESSAGES = {
    "en": {
        "query_error": "[arXiv Harvester] Query error: {e}\n",
        "saved": "[Success] {n} arXiv preprints saved to {path}",
        "missing_criteria": "[Error] You must specify at least one criterion (--query, --category, --author, --title).\n",
        "querying": "[arXiv Harvester] Querying: {q} (Limit: {limit})",
        "downloading_ids": "[arXiv Harvester] Downloading IDs: {ids}",
        "no_results": "[Notice] No preprints found in arXiv.",
    },
    "es": {
        "query_error": "[arXiv Harvester] Error de consulta: {e}\n",
        "saved": "[Éxito] {n} preprints de arXiv guardados en {path}",
        "missing_criteria": "[Error] Debes especificar al menos un criterio (--query, --category, --author, --title).\n",
        "querying": "[arXiv Harvester] Consultando: {q} (Límite: {limit})",
        "downloading_ids": "[arXiv Harvester] Descargando IDs: {ids}",
        "no_results": "[Aviso] No se encontraron preprints en arXiv.",
    }
}

def parse_arxiv_entry_to_canonical(entry: ET.Element) -> Dict[str, Any]:
    """Convert an arXiv XML <entry> element into the canonical tabular schema."""
    # 1. Identifier
    id_elem = entry.find("atom:id", ATOM_NS)
    raw_id = id_elem.text.strip() if id_elem is not None and id_elem.text else ""
    # Extract clean ID format e.g. '2101.12345'
    arxiv_id = raw_id.split("/abs/")[-1] if "/abs/" in raw_id else raw_id
    
    # 2. Title
    title_elem = entry.find("atom:title", ATOM_NS)
    title = " ".join(title_elem.text.split()) if title_elem is not None and title_elem.text else ""
    
    # 3. Abstract
    summary_elem = entry.find("atom:summary", ATOM_NS)
    abstract = " ".join(summary_elem.text.split()) if summary_elem is not None and summary_elem.text else ""
    
    # 4. Date and Year
    pub_elem = entry.find("atom:published", ATOM_NS)
    year = None
    if pub_elem is not None and pub_elem.text:
        try:
            year = int(pub_elem.text[:4])
        except ValueError:
            year = None
            
    # 5. Authors and Affiliations
    authors_list = []
    affiliations_list = []
    for author_node in entry.findall("atom:author", ATOM_NS):
        name_node = author_node.find("atom:name", ATOM_NS)
        if name_node is not None and name_node.text:
            authors_list.append(name_node.text.strip())
        aff_node = author_node.find("arxiv:affiliation", ATOM_NS)
        if aff_node is not None and aff_node.text:
            aff_text = aff_node.text.strip()
            if aff_text and aff_text not in affiliations_list:
                affiliations_list.append(aff_text)
                
    # 6. Categories and Topics
    categories = []
    primary_cat = ""
    prim_elem = entry.find("arxiv:primary_category", ATOM_NS)
    if prim_elem is not None and prim_elem.get("term"):
        primary_cat = prim_elem.get("term")
        categories.append(primary_cat)
        
    for cat_node in entry.findall("atom:category", ATOM_NS):
        term = cat_node.get("term")
        if term and term not in categories:
            categories.append(term)
            
    # 7. DOI and Journal Reference
    doi = ""
    doi_elem = entry.find("arxiv:doi", ATOM_NS)
    if doi_elem is not None and doi_elem.text:
        doi = doi_elem.text.strip()
        
    journal_ref = ""
    jref_elem = entry.find("arxiv:journal_ref", ATOM_NS)
    if jref_elem is not None and jref_elem.text:
        journal_ref = jref_elem.text.strip()
    source_title = journal_ref if journal_ref else f"arXiv:{primary_cat}"
    
    # 8. Open Science Metadata
    # arXiv preprints constitute Green Open Access (Green OA)
    oa_status = "green"
    is_oa = 1
    
    return {
        "id": arxiv_id,
        "title": title,
        "abstract": abstract,
        "authors": "; ".join(authors_list),
        "author_ids": "",
        "year": year,
        "source_title": source_title,
        "citations": 0,  # arXiv does not provide native citation counts
        "doi": doi,
        "keywords_author": primary_cat,
        "keywords_plus": "; ".join(categories),
        "affiliations": "; ".join(affiliations_list),
        "country_codes": "",
        "oa_status": oa_status,
        "is_oa": is_oa,
        "fwci": None,
        "percentile": None,
        "apc_paid_usd": 0.0,  # Zero APC deposit in arXiv
        "language": "en",
        "references": ""
    }

def fetch_arxiv_records(search_query: str, id_list: Optional[str],
                        limit: int, batch_size: int = 100, lang: str = "en") -> List[Dict[str, Any]]:
    """Download records from the arXiv Atom XML API enforcing the 3-second courtesy delay."""
    headers = {"User-Agent": "KnoMap-ArXivHarvester/1.0 (mailto:admin@knomap.org)"}
    msg = MESSAGES.get(lang, MESSAGES["en"])
    
    results = []
    start = 0
    
    while len(results) < limit:
        max_results = min(batch_size, limit - len(results))
        params = {
            "start": start,
            "max_results": max_results
        }
        if search_query:
            params["search_query"] = search_query
        if id_list:
            params["id_list"] = id_list
            
        try:
            resp = requests.get(ARXIV_API_URL, params=params, headers=headers, timeout=45)
            resp.raise_for_status()
            
            root = ET.fromstring(resp.content)
            entries = root.findall("atom:entry", ATOM_NS)
            
            if not entries:
                break
                
            for e in entries:
                rec = parse_arxiv_entry_to_canonical(e)
                # Skip dummy entries without id
                if rec["id"]:
                    results.append(rec)
                    
            start += len(entries)
            
            if len(entries) < max_results:
                break
                
            # Strict arXiv courtesy rule: 3.0-second pause
            time.sleep(3.0)
            
        except Exception as e:
            sys.stderr.write(msg["query_error"].format(e=e))
            break
            
    return results[:limit]

def save_canonical_records(records: List[Dict[str, Any]], output_path: str, lang: str = "en") -> None:
    """Save normalized records in Parquet, JSON, or CSV format."""
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
        description="arXiv Harvester CLI: Download and normalize preprints from the arXiv API."
    )
    parser.add_argument(
        "--lang",
        type=str,
        choices=["en", "es"],
        default="en",
        help="Output language for labels/messages (en or es)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # 1. search
    p_search = subparsers.add_parser("search", help="Thematic or categorical search in arXiv.")
    p_search.add_argument("--query", type=str, help="General search terms (across all fields)")
    p_search.add_argument("--category", type=str, help="arXiv category (e.g., cs.AI, stat.ML, physics.soc-ph)")
    p_search.add_argument("--author", type=str, help="Author name")
    p_search.add_argument("--title", type=str, help="Terms in the title")
    p_search.add_argument("--limit", type=int, default=50, help="Maximum number of preprints (default: 50)")
    p_search.add_argument("--output", type=str, required=True, help="Output file path (.parquet, .json, .csv)")
    p_search.add_argument("--lang", type=str, choices=["en", "es"], default="en", help="Output language for labels/messages (en or es)")
    
    # 2. fetch-by-ids
    p_ids = subparsers.add_parser("fetch-by-ids", help="Download specific preprints by a list of arXiv IDs.")
    p_ids.add_argument("--id-list", type=str, required=True, help="Comma-separated list of IDs (e.g., '2101.12345,2304.01234')")
    p_ids.add_argument("--output", type=str, required=True, help="Output file path")
    p_ids.add_argument("--lang", type=str, choices=["en", "es"], default="en", help="Output language for labels/messages (en or es)")

    args = parser.parse_args()
    lang = getattr(args, "lang", "en") or "en"
    msg = MESSAGES.get(lang, MESSAGES["en"])
    
    if args.command == "search":
        query_parts = []
        if args.query:
            query_parts.append(f"all:{args.query}")
        if args.category:
            query_parts.append(f"cat:{args.category}")
        if args.author:
            query_parts.append(f"au:{args.author}")
        if args.title:
            query_parts.append(f"ti:{args.title}")
            
        if not query_parts:
            sys.stderr.write(msg["missing_criteria"])
            sys.exit(1)
            
        full_query = " AND ".join(query_parts)
        print(msg["querying"].format(q=full_query, limit=args.limit))
        records = fetch_arxiv_records(search_query=full_query, id_list=None, limit=args.limit, lang=lang)
        
    elif args.command == "fetch-by-ids":
        cleaned_ids = ",".join([i.strip() for i in args.id_list.split(",") if i.strip()])
        print(msg["downloading_ids"].format(ids=cleaned_ids))
        records = fetch_arxiv_records(search_query="", id_list=cleaned_ids, limit=len(cleaned_ids.split(",")), lang=lang)
        
    if not records:
        print(msg["no_results"])
        sys.exit(0)
        
    save_canonical_records(records, args.output, lang=lang)

if __name__ == "__main__":
    main()
