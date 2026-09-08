#!/usr/bin/env /home/ambientesPy/revistaslatam/bin/python
"""
arXiv Data Harvester CLI
------------------------
Herramienta autónoma para la consulta y descarga de metadatos de preprints desde
el API Atom XML de arXiv (export.arxiv.org/api/query), con respeto del retardo
obligatorio de cortesía de 3.0 segundos y normalización al esquema tabular canónico.
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

def parse_arxiv_entry_to_canonical(entry: ET.Element) -> Dict[str, Any]:
    """Convierte un elemento XML <entry> de arXiv al esquema tabular canónico."""
    # 1. Identificador
    id_elem = entry.find("atom:id", ATOM_NS)
    raw_id = id_elem.text.strip() if id_elem is not None and id_elem.text else ""
    # Extraer formato limpio e.g. '2101.12345'
    arxiv_id = raw_id.split("/abs/")[-1] if "/abs/" in raw_id else raw_id
    
    # 2. Título
    title_elem = entry.find("atom:title", ATOM_NS)
    title = " ".join(title_elem.text.split()) if title_elem is not None and title_elem.text else ""
    
    # 3. Resumen
    summary_elem = entry.find("atom:summary", ATOM_NS)
    abstract = " ".join(summary_elem.text.split()) if summary_elem is not None and summary_elem.text else ""
    
    # 4. Fecha y Año
    pub_elem = entry.find("atom:published", ATOM_NS)
    year = None
    if pub_elem is not None and pub_elem.text:
        try:
            year = int(pub_elem.text[:4])
        except ValueError:
            year = None
            
    # 5. Autores y Afiliaciones
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
                
    # 6. Categorías y Tópicos
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
            
    # 7. DOI y Referencia de Revista
    doi = ""
    doi_elem = entry.find("arxiv:doi", ATOM_NS)
    if doi_elem is not None and doi_elem.text:
        doi = doi_elem.text.strip()
        
    journal_ref = ""
    jref_elem = entry.find("arxiv:journal_ref", ATOM_NS)
    if jref_elem is not None and jref_elem.text:
        journal_ref = jref_elem.text.strip()
    source_title = journal_ref if journal_ref else f"arXiv:{primary_cat}"
    
    # 8. Metadatos de Ciencia Abierta
    # Los preprints de arXiv constituyen Acceso Abierto por vía Verde (Green OA)
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
        "citations": 0,  # arXiv no provee conteo nativo de citas
        "doi": doi,
        "keywords_author": primary_cat,
        "keywords_plus": "; ".join(categories),
        "affiliations": "; ".join(affiliations_list),
        "country_codes": "",
        "oa_status": oa_status,
        "is_oa": is_oa,
        "fwci": None,  # Reporte conforme a la respuesta del usuario
        "percentile": None,
        "apc_paid_usd": 0.0,  # Depósito sin costo APC en arXiv
        "language": "en",
        "references": ""
    }

def fetch_arxiv_records(search_query: str, id_list: Optional[str],
                        limit: int, batch_size: int = 100) -> List[Dict[str, Any]]:
    """Descarga registros del API Atom XML de arXiv respetando el delay de 3 segundos."""
    headers = {"User-Agent": "KnoMap-ArXivHarvester/1.0 (mailto:admin@knomap.org)"}
    
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
                # Omitir entradas dummy sin id
                if rec["id"]:
                    results.append(rec)
                    
            start += len(entries)
            
            if len(entries) < max_results:
                break
                
            # Regla de cortesía estricta de arXiv: pausa de 3.0 segundos
            time.sleep(3.0)
            
        except Exception as e:
            sys.stderr.write(f"[arXiv Harvester] Error de consulta: {e}\n")
            break
            
    return results[:limit]

def save_canonical_records(records: List[Dict[str, Any]], output_path: str) -> None:
    """Guarda registros normalizados en Parquet, JSON o CSV."""
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
        
    print(f"[Éxito] {len(df)} preprints de arXiv guardados en {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description="arXiv Harvester CLI: Descarga y normalización de preprints desde el API de arXiv."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # 1. search
    p_search = subparsers.add_parser("search", help="Búsqueda temática o categórica en arXiv.")
    p_search.add_argument("--query", type=str, help="Términos generales de búsqueda (en todos los campos)")
    p_search.add_argument("--category", type=str, help="Categoría arXiv (ej. cs.AI, stat.ML, physics.soc-ph)")
    p_search.add_argument("--author", type=str, help="Nombre del autor")
    p_search.add_argument("--title", type=str, help="Términos en el título")
    p_search.add_argument("--limit", type=int, default=50, help="Límite máximo de preprints (default: 50)")
    p_search.add_argument("--output", type=str, required=True, help="Ruta del archivo de salida (.parquet, .json, .csv)")
    
    # 2. fetch-by-ids
    p_ids = subparsers.add_parser("fetch-by-ids", help="Descarga preprints específicos por lista de IDs de arXiv.")
    p_ids.add_argument("--id-list", type=str, required=True, help="Lista de IDs separados por coma (ej. '2101.12345,2304.01234')")
    p_ids.add_argument("--output", type=str, required=True, help="Ruta del archivo de salida")

    args = parser.parse_args()
    
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
            sys.stderr.write("[Error] Debes especificar al menos un criterio (--query, --category, --author, --title).\n")
            sys.exit(1)
            
        full_query = " AND ".join(query_parts)
        print(f"[arXiv Harvester] Consultando: {full_query} (Límite: {args.limit})")
        records = fetch_arxiv_records(search_query=full_query, id_list=None, limit=args.limit)
        
    elif args.command == "fetch-by-ids":
        cleaned_ids = ",".join([i.strip() for i in args.id_list.split(",") if i.strip()])
        print(f"[arXiv Harvester] Descargando IDs: {cleaned_ids}")
        records = fetch_arxiv_records(search_query="", id_list=cleaned_ids, limit=len(cleaned_ids.split(",")))
        
    if not records:
        print("[Aviso] No se encontraron preprints en arXiv.")
        sys.exit(0)
        
    save_canonical_records(records, args.output)

if __name__ == "__main__":
    main()
