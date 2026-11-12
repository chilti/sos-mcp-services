#!/usr/bin/env python3
"""
PubMed Data Harvester CLI
-------------------------
Standalone tool for harvesting, paginating, and standardizing biomedical
and clinical literature from the official NCBI E-utilities (PubMed) API
into the canonical tabular schema (Parquet, JSON, CSV).
"""

import sys
import os
import argparse
import time
import urllib.request
import urllib.parse
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root directory to import shared modules
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from shared.canonical_schema import save_canonical_corpus, normalize_record_to_canonical
except ImportError:
    # Fallback when executed standalone
    def save_canonical_corpus(records, output_path, default_source="pubmed"):
        import pandas as pd
        df = pd.DataFrame(records)
        if output_path.endswith(".parquet"):
            df.to_parquet(output_path, index=False)
        elif output_path.endswith(".json"):
            df.to_json(output_path, orient="records", force_ascii=False, indent=2)
        else:
            df.to_csv(output_path, index=False)
        return output_path

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

MESSAGES = {
    "en": {
        "batch_error": "[PubMed Harvester] Error in batch {start}-{end}: {e}\n",
        "querying": "[PubMed Harvester] Querying Entrez with: '{query}' (Limit: {limit})...\n",
        "pmids_found": "[PubMed Harvester] {n} PMIDs found. Downloading document metadata...\n",
        "no_results": "[PubMed Harvester] No matching records found.\n",
        "saved": "[PubMed Harvester] Success: {n} records saved to '{path}'.\n",
    },
    "es": {
        "batch_error": "[PubMed Harvester] Error en lote {start}-{end}: {e}\n",
        "querying": "[PubMed Harvester] Consultando Entrez con: '{query}' (Límite: {limit})...\n",
        "pmids_found": "[PubMed Harvester] {n} PMIDs encontrados. Descargando metadatos documentales...\n",
        "no_results": "[PubMed Harvester] No se encontraron registros coincidentes.\n",
        "saved": "[PubMed Harvester] Éxito: {n} registros guardados en '{path}'.\n",
    }
}


def get_ncbi_env_variable(key: str, default: Optional[str] = None) -> Optional[str]:
    """Retrieve keys from environment variables or .env file."""
    if os.environ.get(key):
        return os.environ.get(key)
    env_file = project_root / ".env"
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f"{key}="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            pass
    return default


def search_pubmed_pmids(
    term: str,
    limit: int = 100,
    api_key: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None
) -> List[str]:
    """Execute esearch.fcgi to retrieve the list of PMID identifiers."""
    params = {
        "db": "pubmed",
        "term": term,
        "retmax": min(limit, 10000),
        "retmode": "json",
        "tool": "knoMap-Harvester",
        "email": get_ncbi_env_variable("EMAIL_ADDRESS", "agent@knomap.org")
    }
    if api_key:
        params["api_key"] = api_key
    if year_from:
        params["mindate"] = str(year_from)
        params["datetype"] = "pdat"
    if year_to:
        params["maxdate"] = str(year_to)
        params["datetype"] = "pdat"

    query_str = urllib.parse.urlencode(params)
    url = f"{BASE_URL}/esearch.fcgi?{query_str}"

    req = urllib.request.Request(url, headers={"User-Agent": "knoMap-Harvester/1.0"})
    with urllib.request.urlopen(req, timeout=15) as res:
        data = json.loads(res.read().decode("utf-8"))

    id_list = data.get("esearchresult", {}).get("idlist", [])
    return id_list[:limit]


def fetch_pubmed_summaries(
    pmids: List[str],
    api_key: Optional[str] = None,
    batch_size: int = 150,
    lang: str = "en"
) -> List[Dict[str, Any]]:
    """Download document metadata for a batch of PMIDs via esummary.fcgi."""
    msg = MESSAGES.get(lang, MESSAGES["en"])
    all_records = []
    total = len(pmids)

    for i in range(0, total, batch_size):
        batch = pmids[i : i + batch_size]
        ids_str = ",".join(batch)
        params = {
            "db": "pubmed",
            "id": ids_str,
            "retmode": "json",
            "tool": "knoMap-Harvester",
            "email": get_ncbi_env_variable("EMAIL_ADDRESS", "agent@knomap.org")
        }
        if api_key:
            params["api_key"] = api_key

        query_str = urllib.parse.urlencode(params)
        url = f"{BASE_URL}/esummary.fcgi?{query_str}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "knoMap-Harvester/1.0"})
            with urllib.request.urlopen(req, timeout=20) as res:
                data = json.loads(res.read().decode("utf-8"))

            result_dict = data.get("result", {})
            for pmid in batch:
                doc = result_dict.get(pmid)
                if not doc:
                    continue

                # Extract DOI and PMCID from articleids
                doi = None
                pmcid = None
                for aid in doc.get("articleids", []):
                    idtype = aid.get("idtype")
                    val = aid.get("value")
                    if idtype == "doi" and not doi:
                        doi = val
                    elif idtype in ("pmc", "pmcid") and not pmcid:
                        pmcid = val.replace("pmc-id: ", "").split(";")[0].strip()

                # Extract publication year
                pubdate = doc.get("pubdate", "")
                pub_year = None
                for part in pubdate.split():
                    if part.isdigit() and len(part) == 4:
                        pub_year = int(part)
                        break

                # Authors
                authors = [a.get("name") for a in doc.get("authors", []) if a.get("name")]

                # Open Access status:
                # If a PMCID is available in PubMed Central, it is Green OA in a public repository
                has_pmc = bool(pmcid)
                oa_status = "green" if has_pmc else "closed"

                journal_str = doc.get("fulljournalname") or doc.get("source") or ""
                record = {
                    "id": f"pmid:{pmid}",
                    "doi": doi or "",
                    "pmid": pmid,
                    "pmcid": pmcid,
                    "title": doc.get("title", ""),
                    "abstract": "",
                    "year": pub_year,
                    "publication_year": pub_year,
                    "publication_date": pubdate,
                    "doc_type": "article",
                    "type": "article",
                    "language": "en",
                    "source_title": journal_str,
                    "journal_name": journal_str,
                    "issn": doc.get("issn"),
                    "publisher": None,
                    "citations": 0,
                    "cited_by_count": 0,
                    "is_oa": has_pmc,
                    "oa_status": oa_status,
                    "apc_list_usd": 0.0,
                    "apc_paid_usd": 0.0,
                    "authors": "; ".join(authors),
                    "author_names": authors,
                    "author_ids": [],
                    "affiliations": "",
                    "country_codes": "",
                    "countries": [],
                    "keywords_author": "",
                    "keywords_plus": "",
                    "keywords": [],
                    "mesh_terms": [],
                    "topics": [],
                    "fwci": None,
                    "percentile": None,
                    "is_top_10": False,
                    "is_top_1": False,
                    "referenced_works": [],
                    "references": [],
                    "source_db": "PubMed",
                    "source_harvester": "pubmed"
                }
                all_records.append(record)

        except Exception as e:
            sys.stderr.write(msg["batch_error"].format(start=i, end=i+batch_size, e=e))

        # NCBI rate-limit control
        time.sleep(0.35 if not api_key else 0.12)

    return all_records


def main():
    parser = argparse.ArgumentParser(description="PubMed Data Harvester CLI (knoMap Scientometrics Suite)")
    parser.add_argument(
        "--lang",
        type=str,
        choices=["en", "es"],
        default="en",
        help="Output language for labels/messages (en or es)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. Subcommand: fetch-works
    p_works = subparsers.add_parser("fetch-works", help="Harvest PubMed publications by thematic query")
    p_works.add_argument("--query", "-q", type=str, required=True, help="Entrez search terms (e.g., 'microplastics AND water')")
    p_works.add_argument("--affiliation", "-a", type=str, help="Affiliation or country filter (e.g., 'Mexico[Affiliation]')")
    p_works.add_argument("--year-from", type=int, help="Start publication year")
    p_works.add_argument("--year-to", type=int, help="End publication year")
    p_works.add_argument("--limit", "-l", type=int, default=100, help="Maximum number of works to harvest (default: 100)")
    p_works.add_argument("--output", "-o", type=str, required=True, help="Output file path (.parquet, .json, .csv)")
    p_works.add_argument("--api-key", type=str, help="NCBI API Key (optional)")
    p_works.add_argument("--lang", type=str, choices=["en", "es"], default="en", help="Output language for labels/messages (en or es)")

    # 2. Subcommand: fetch-author-works
    p_author = subparsers.add_parser("fetch-author-works", help="Harvest publications by a specific author")
    p_author.add_argument("--author", type=str, required=True, help="Author name in PubMed format (e.g., 'Pardo Annie' or 'Pardo A')")
    p_author.add_argument("--affiliation", type=str, help="Optional institution filter (e.g., 'UNAM' or 'Mexico')")
    p_author.add_argument("--year-from", type=int, help="Start year")
    p_author.add_argument("--year-to", type=int, help="End year")
    p_author.add_argument("--limit", "-l", type=int, default=200, help="Maximum number of works (default: 200)")
    p_author.add_argument("--output", "-o", type=str, required=True, help="Output file path (.parquet, .json, .csv)")
    p_author.add_argument("--api-key", type=str, help="NCBI API Key (optional)")
    p_author.add_argument("--lang", type=str, choices=["en", "es"], default="en", help="Output language for labels/messages (en or es)")

    args = parser.parse_args()
    lang = getattr(args, "lang", "en") or "en"
    msg = MESSAGES.get(lang, MESSAGES["en"])

    api_key = args.api_key or get_ncbi_env_variable("NCBI_API_KEY")

    if args.command == "fetch-works":
        query_parts = [args.query]
        if args.affiliation:
            query_parts.append(f"{args.affiliation}[Affiliation]")
        full_query = " AND ".join(query_parts)
    elif args.command == "fetch-author-works":
        query_parts = [f"{args.author}[Author]"]
        if args.affiliation:
            query_parts.append(f"{args.affiliation}[Affiliation]")
        full_query = " AND ".join(query_parts)
    else:
        full_query = ""

    sys.stdout.write(msg["querying"].format(query=full_query, limit=args.limit))
    pmids = search_pubmed_pmids(
        term=full_query,
        limit=args.limit,
        api_key=api_key,
        year_from=args.year_from,
        year_to=args.year_to
    )

    sys.stdout.write(msg["pmids_found"].format(n=len(pmids)))
    if not pmids:
        sys.stdout.write(msg["no_results"])
        return

    records = fetch_pubmed_summaries(pmids, api_key=api_key, lang=lang)
    out_file = save_canonical_corpus(records, args.output, default_source="pubmed")
    sys.stdout.write(msg["saved"].format(n=len(records), path=out_file))


if __name__ == "__main__":
    main()
