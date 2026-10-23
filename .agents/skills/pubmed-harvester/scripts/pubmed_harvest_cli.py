#!/usr/bin/env python3
"""
PubMed Data Harvester CLI
-------------------------
Herramienta autónoma para la recolección, paginación y estandarización de
literatura biomédica y clínica desde la API oficial NCBI E-utilities (PubMed)
hacia el esquema tabular canónico (Parquet, JSON, CSV).
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

# Agregar el directorio raíz del proyecto para importar módulos compartidos
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from shared.canonical_schema import save_canonical_corpus, normalize_record_to_canonical
except ImportError:
    # Fallback si se ejecuta de forma aislada
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


def get_ncbi_env_variable(key: str, default: Optional[str] = None) -> Optional[str]:
    """Obtiene claves desde variables de entorno o archivo .env."""
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
    """Ejecuta esearch.fcgi para obtener la lista de identificadores PMID."""
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
    batch_size: int = 150
) -> List[Dict[str, Any]]:
    """Descarga los metadatos documentales de un lote de PMIDs mediante esummary.fcgi."""
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

                # Extraer DOI y PMCID de articleids
                doi = None
                pmcid = None
                for aid in doc.get("articleids", []):
                    idtype = aid.get("idtype")
                    val = aid.get("value")
                    if idtype == "doi" and not doi:
                        doi = val
                    elif idtype in ("pmc", "pmcid") and not pmcid:
                        pmcid = val.replace("pmc-id: ", "").split(";")[0].strip()

                # Extraer año de publicación
                pubdate = doc.get("pubdate", "")
                pub_year = None
                for part in pubdate.split():
                    if part.isdigit() and len(part) == 4:
                        pub_year = int(part)
                        break

                # Autores
                authors = [a.get("name") for a in doc.get("authors", []) if a.get("name")]

                # Estado de Acceso Abierto:
                # Si tiene PMCID en PubMed Central, es Open Access disponible en repositorio público
                has_pmc = bool(pmcid)
                oa_status = "green" if has_pmc else "closed"

                record = {
                    "id": f"pmid:{pmid}",
                    "doi": doi,
                    "pmid": pmid,
                    "pmcid": pmcid,
                    "title": doc.get("title", ""),
                    "abstract": "",
                    "publication_year": pub_year,
                    "publication_date": pubdate,
                    "journal_name": doc.get("fulljournalname") or doc.get("source"),
                    "issn": doc.get("issn"),
                    "publisher": None,
                    "cited_by_count": 0,  # PubMed no incluye citas acumuladas en esummary
                    "is_oa": has_pmc,
                    "oa_status": oa_status,
                    "apc_paid_usd": 0.0,
                    "author_names": authors,
                    "author_ids": [],
                    "affiliations": [],
                    "countries": [],
                    "keywords": [],
                    "mesh_terms": [],
                    "topics": [],
                    "fwci": None,
                    "is_top_10": 0,
                    "references": [],
                    "source_harvester": "pubmed"
                }
                all_records.append(record)

        except Exception as e:
            sys.stderr.write(f"[PubMed Harvester] Error en lote {i}-{i+batch_size}: {e}\n")

        # Control de tasa de peticiones NCBI
        time.sleep(0.35 if not api_key else 0.12)

    return all_records


def main():
    parser = argparse.ArgumentParser(description="PubMed Data Harvester CLI (knoMap Scientometrics Suite)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. Subcomando: fetch-works
    p_works = subparsers.add_parser("fetch-works", help="Recolecta publicaciones de PubMed por consulta temática")
    p_works.add_argument("--query", "-q", type=str, required=True, help="Términos de búsqueda Entrez (ej. 'microplastics AND water')")
    p_works.add_argument("--affiliation", "-a", type=str, help="Filtro de afiliación o país (ej. 'Mexico[Affiliation]')")
    p_works.add_argument("--year-from", type=int, help="Año de inicio de publicación")
    p_works.add_argument("--year-to", type=int, help="Año final de publicación")
    p_works.add_argument("--limit", "-l", type=int, default=100, help="Límite máximo de obras a cosechar (default: 100)")
    p_works.add_argument("--output", "-o", type=str, required=True, help="Ruta de salida (.parquet, .json, .csv)")
    p_works.add_argument("--api-key", type=str, help="Clave de API NCBI (opcional)")

    # 2. Subcomando: fetch-author-works
    p_author = subparsers.add_parser("fetch-author-works", help="Recolecta publicaciones de un autor específico")
    p_author.add_argument("--author", type=str, required=True, help="Nombre del autor en formato PubMed (ej. 'Pardo Annie' o 'Pardo A')")
    p_author.add_argument("--affiliation", type=str, help="Filtro opcional de institución (ej. 'UNAM' o 'Mexico')")
    p_author.add_argument("--year-from", type=int, help="Año de inicio")
    p_author.add_argument("--year-to", type=int, help="Año final")
    p_author.add_argument("--limit", "-l", type=int, default=200, help="Límite de obras (default: 200)")
    p_author.add_argument("--output", "-o", type=str, required=True, help="Ruta de salida (.parquet, .json, .csv)")
    p_author.add_argument("--api-key", type=str, help="Clave de API NCBI (opcional)")

    args = parser.parse_args()

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

    sys.stdout.write(f"[PubMed Harvester] Consultando Entrez con: '{full_query}' (Límite: {args.limit})...\n")
    pmids = search_pubmed_pmids(
        term=full_query,
        limit=args.limit,
        api_key=api_key,
        year_from=args.year_from,
        year_to=args.year_to
    )

    sys.stdout.write(f"[PubMed Harvester] {len(pmids)} PMIDs encontrados. Descargando metadatos documentales...\n")
    if not pmids:
        sys.stdout.write("[PubMed Harvester] No se encontraron registros coincidentes.\n")
        return

    records = fetch_pubmed_summaries(pmids, api_key=api_key)
    out_file = save_canonical_corpus(records, args.output, default_source="pubmed")
    sys.stdout.write(f"[PubMed Harvester] Éxito: {len(records)} registros guardados en '{out_file}'.\n")


if __name__ == "__main__":
    main()
