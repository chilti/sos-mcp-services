#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Open Access PDF Downloader CLI (Ethical & Robust Full-Text Harvester)
Ecosystem: KnoMap / TlachIA / sos-mcp-services

Harvests full-text scientific PDFs for Open Access publications using
waterfall resolution (OpenAlex best OA location, arXiv, PMC, institutional repositories),
strict binary verification (%PDF- header and size validation), and PRISMA audit logging.
"""

import os
import sys
import re
import time
import json
import csv
import math
import hashlib
import argparse
import subprocess
from typing import List, Dict, Any, Optional, Tuple
import requests

# Default configuration
USER_AGENT = "AcademicOpenAccessHarvester/1.0 (mailto:investigacion@labsom.org; Polite-Crawler)"
OPENALEX_API_BASE = "https://api.openalex.org/works"
MIN_PDF_BYTES = 15000  # Minimum 15 KB to reject empty/stub error pages


def clean_identifier(raw_id: str) -> str:
    """Standardizes DOI, arXiv ID, or OpenAlex ID."""
    raw_id = raw_id.strip()
    # Clean URLs
    raw_id = re.sub(r"^https?://(dx\.)?doi\.org/", "", raw_id)
    raw_id = re.sub(r"^https?://openalex\.org/", "", raw_id)
    return raw_id


def sanitize_filename(name: str) -> str:
    """Converts a DOI or ID into a clean filesystem filename."""
    clean = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
    clean = re.sub(r"_+", "_", clean)
    return clean[:120].strip("_")


def calculate_md5(filepath: str) -> str:
    """Calculates MD5 checksum of a local file."""
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_identifiers_from_file(file_path: str) -> List[str]:
    """Extracts DOIs or OpenAlex IDs from CSV, Parquet, or JSON."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    identifiers = []

    if ext == ".csv":
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = [k.lower().strip() for k in (reader.fieldnames or [])]
            doi_col = next((c for c in reader.fieldnames or [] if c.lower().strip() in ("doi", "article_doi", "work_doi")), None)
            id_col = next((c for c in reader.fieldnames or [] if c.lower().strip() in ("work id", "work_id", "openalex_id", "id")), None)

            for row in reader:
                val = ""
                if doi_col and row.get(doi_col) and row[doi_col].strip():
                    val = row[doi_col].strip()
                elif id_col and row.get(id_col) and row[id_col].strip():
                    val = row[id_col].strip()
                if val:
                    identifiers.append(val)

    elif ext == ".parquet":
        try:
            import pyarrow.parquet as pq
            table = pq.read_table(file_path)
            cols = [c.lower() for c in table.column_names]
            target_col = None
            for c in table.column_names:
                if c.lower() in ("doi", "id", "work_id", "openalex_id"):
                    target_col = c
                    break
            if target_col:
                series = table[target_col].to_pylist()
                identifiers = [str(x).strip() for x in series if x and str(x).strip()]
        except Exception as e:
            print(f"[Warning] Failed to read Parquet directly: {e}", file=sys.stderr)

    elif ext == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = data.get("results") or data.get("candidates") or data.get("works") or []

            for item in items:
                if isinstance(item, str):
                    identifiers.append(item.strip())
                elif isinstance(item, dict):
                    val = item.get("doi") or item.get("work_id") or item.get("id")
                    if val:
                        identifiers.append(str(val).strip())

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for item in identifiers:
        c = clean_identifier(item)
        if c and c not in seen:
            seen.add(c)
            deduped.append(c)

    return deduped


def fetch_openalex_metadata_batch(identifiers: List[str]) -> Dict[str, Dict[str, Any]]:
    """Retrieves full OpenAlex OA metadata for a list of DOIs or Work IDs in batches of 50."""
    metadata_map = {}
    headers = {"User-Agent": USER_AGENT}

    # Separate into Work IDs (W...) and DOIs
    work_ids = [clean_identifier(x) for x in identifiers if clean_identifier(x).startswith("W") and clean_identifier(x)[1:].isdigit()]
    dois = [clean_identifier(x) for x in identifiers if "10." in clean_identifier(x)]
    other_ids = [clean_identifier(x) for x in identifiers if x not in work_ids and x not in dois]

    # Process Work IDs
    chunk_size = 50
    for i in range(0, len(work_ids), chunk_size):
        chunk = work_ids[i:i + chunk_size]
        pipe_ids = "|".join([f"https://openalex.org/{wid}" for wid in chunk])
        params = {"filter": f"openalex_id:{pipe_ids}", "per-page": len(chunk)}
        try:
            resp = requests.get(OPENALEX_API_BASE, params=params, headers=headers, timeout=15)
            if resp.status_code == 200:
                for item in resp.json().get("results", []):
                    wid = clean_identifier(item.get("id", ""))
                    metadata_map[wid] = item
                    if item.get("doi"):
                        metadata_map[clean_identifier(item["doi"])] = item
            time.sleep(0.1)
        except Exception as e:
            print(f"[Error] OpenAlex batch query failed for Work IDs: {e}", file=sys.stderr)

    # Process DOIs
    for i in range(0, len(dois), chunk_size):
        chunk = dois[i:i + chunk_size]
        pipe_dois = "|".join([f"https://doi.org/{d}" for d in chunk])
        params = {"filter": f"doi:{pipe_dois}", "per-page": len(chunk)}
        try:
            resp = requests.get(OPENALEX_API_BASE, params=params, headers=headers, timeout=15)
            if resp.status_code == 200:
                for item in resp.json().get("results", []):
                    d_clean = clean_identifier(item.get("doi", ""))
                    wid = clean_identifier(item.get("id", ""))
                    metadata_map[d_clean] = item
                    if wid:
                        metadata_map[wid] = item
            time.sleep(0.1)
        except Exception as e:
            print(f"[Error] OpenAlex batch query failed for DOIs: {e}", file=sys.stderr)

    # Handle remaining individual identifiers (e.g. arXiv, standalone DOIs not found in batch)
    for ident in other_ids + [d for d in dois if d not in metadata_map]:
        try:
            if "10." in ident:
                url = f"{OPENALEX_API_BASE}/https://doi.org/{ident}"
            elif ident.startswith("W"):
                url = f"{OPENALEX_API_BASE}/{ident}"
            else:
                url = f"{OPENALEX_API_BASE}/{ident}"
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                item = resp.json()
                metadata_map[ident] = item
                if item.get("doi"):
                    metadata_map[clean_identifier(item["doi"])] = item
                if item.get("id"):
                    metadata_map[clean_identifier(item["id"])] = item
            time.sleep(0.1)
        except Exception:
            pass

    return metadata_map


def resolve_pdf_urls_waterfall(work_meta: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    """
    Builds an ordered waterfall list of candidate PDF download URLs.
    Returns list of tuples: (url, source_type, version)
    """
    candidates = []
    seen_urls = set()

    def add_candidate(url: Optional[str], src_type: str, ver: str):
        if not url:
            return
        url_clean = url.strip()
        if not url_clean.startswith("http"):
            return
        if url_clean in seen_urls:
            return
        seen_urls.add(url_clean)
        candidates.append((url_clean, src_type, ver))

    # 1. Best Open Access Location (Highest reliability from OpenAlex)
    best_oa = work_meta.get("best_oa_location") or {}
    if best_oa.get("pdf_url"):
        add_candidate(best_oa.get("pdf_url"), "best_oa_location", best_oa.get("version", "unknown"))

    # 2. Primary Location (if OA)
    prim_loc = work_meta.get("primary_location") or {}
    if prim_loc.get("is_oa") and prim_loc.get("pdf_url"):
        add_candidate(prim_loc.get("pdf_url"), "primary_location", prim_loc.get("version", "publishedVersion"))

    # 3. All other available OA locations (Institutional repos, PMC, Zenodo, Europe PMC)
    locations = work_meta.get("locations") or []
    for loc in locations:
        if loc.get("is_oa") and loc.get("pdf_url"):
            src_desc = loc.get("source", {}).get("display_name") or "repository"
            add_candidate(loc.get("pdf_url"), f"repo:{src_desc}", loc.get("version", "unknown"))

    # 4. Check for direct arXiv resolution
    doi = work_meta.get("doi") or ""
    ids_dict = work_meta.get("ids") or {}
    arxiv_id = ""

    if "10.48550/arxiv." in doi.lower():
        arxiv_match = re.search(r"arxiv\.(\d{4}\.\d{4,5}(?:v\d+)?)", doi, re.IGNORECASE)
        if arxiv_match:
            arxiv_id = arxiv_match.group(1)
    elif "arxiv" in ids_dict:
        arxiv_raw = ids_dict["arxiv"]
        arxiv_match = re.search(r"(\d{4}\.\d{4,5}(?:v\d+)?)", arxiv_raw)
        if arxiv_match:
            arxiv_id = arxiv_match.group(1)

    if arxiv_id:
        arxiv_pdf = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        add_candidate(arxiv_pdf, "arxiv_direct", "submittedVersion")

    # 5. Check for PubMed Central (PMC) direct URL
    pmcid = ids_dict.get("pmcid")
    if pmcid:
        clean_pmc = pmcid.replace("https://www.ncbi.nlm.nih.gov/pmc/articles/", "").replace("/", "")
        pmc_pdf = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{clean_pmc}/pdf/"
        add_candidate(pmc_pdf, "pmc_direct", "publishedVersion")

    # 6. Fallback landing page if it ends with .pdf
    for loc in locations:
        landing = loc.get("landing_page_url") or ""
        if landing.lower().endswith(".pdf"):
            add_candidate(landing, "landing_direct_pdf", "unknown")

    return candidates


def download_single_pdf(
    url_waterfall: List[Tuple[str, str, str]],
    destination_path: str,
    timeout: int = 25
) -> Tuple[bool, str, Optional[str], Optional[str], int]:
    """
    Attempts to download a valid PDF walking down the waterfall list.
    Verifies %PDF- magic bytes and minimum file size.
    Returns: (success, status_message, winning_url, winning_source, bytes_downloaded)
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/pdf,application/xhtml+xml,text/html;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,es;q=0.8"
    }

    last_error = "NO_CANDIDATE_URLS"

    for url, src_type, ver in url_waterfall:
        try:
            with requests.get(url, headers=headers, stream=True, timeout=timeout, allow_redirects=True) as resp:
                if resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "").lower()

                    # Stream initial chunk to inspect magic bytes
                    chunks = resp.iter_content(chunk_size=8192)
                    first_chunk = next(chunks, b"")

                    # Check for %PDF magic header
                    is_pdf_bytes = first_chunk.startswith(b"%PDF-") or (b"%PDF-" in first_chunk[:1024])
                    is_pdf_content_type = "application/pdf" in content_type

                    # Rejection heuristic: HTML doctype or landing page
                    if b"<!doctype html" in first_chunk.lower() or b"<html" in first_chunk.lower():
                        last_error = f"HTML_REDIRECT_OR_LOGIN ({src_type})"
                        continue

                    if not (is_pdf_bytes or is_pdf_content_type):
                        last_error = f"NOT_A_PDF ({src_type}: {content_type})"
                        continue

                    # Write chunks to file
                    temp_dest = destination_path + ".tmp"
                    total_bytes = len(first_chunk)
                    with open(temp_dest, "wb") as f_out:
                        f_out.write(first_chunk)
                        for chunk in chunks:
                            if chunk:
                                f_out.write(chunk)
                                total_bytes += len(chunk)

                    # Validate final size
                    if total_bytes < MIN_PDF_BYTES:
                        if os.path.exists(temp_dest):
                            os.remove(temp_dest)
                        last_error = f"FILE_TOO_SMALL_STUB ({total_bytes} bytes)"
                        continue

                    # Atomic rename
                    if os.path.exists(destination_path):
                        os.remove(destination_path)
                    os.rename(temp_dest, destination_path)

                    return (True, "SUCCESS", url, src_type, total_bytes)

                elif resp.status_code == 403:
                    last_error = f"HTTP_403_FORBIDDEN ({src_type})"
                elif resp.status_code == 404:
                    last_error = f"HTTP_404_NOT_FOUND ({src_type})"
                elif resp.status_code == 429:
                    last_error = f"HTTP_429_RATE_LIMITED ({src_type})"
                    time.sleep(2.0)
                else:
                    last_error = f"HTTP_{resp.status_code} ({src_type})"

        except requests.exceptions.Timeout:
            last_error = f"TIMEOUT ({src_type})"
        except requests.exceptions.RequestException as e:
            last_error = f"NETWORK_ERROR ({src_type}: {type(e).__name__})"
        except Exception as e:
            last_error = f"DOWNLOAD_EXCEPTION ({str(e)})"

    return (False, last_error, None, None, 0)


def extract_text_from_pdf(pdf_path: str, txt_path: str) -> bool:
    """Uses /usr/bin/pdftotext to produce a layout-preserved plain text file."""
    if not os.path.exists(pdf_path):
        return False
    try:
        res = subprocess.run(
            ["pdftotext", "-layout", pdf_path, txt_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30
        )
        return res.returncode == 0 and os.path.exists(txt_path) and os.path.getsize(txt_path) > 0
    except Exception:
        return False


def run_oa_pdf_harvester(
    identifiers: List[str],
    output_dir: str,
    limit: Optional[int] = None,
    delay: float = 0.5,
    extract_text: bool = False,
    timeout: int = 25,
    lang: str = "en"
):
    """Main orchestration pipeline for Open Access PDF harvesting."""
    is_es = (lang == "es")
    os.makedirs(output_dir, exist_ok=True)
    pdf_dir = os.path.join(output_dir, "pdf")
    os.makedirs(pdf_dir, exist_ok=True)

    txt_dir = os.path.join(output_dir, "text")
    if extract_text:
        os.makedirs(txt_dir, exist_ok=True)

    print("\n" + "=" * 65)
    print("  OPEN ACCESS PDF HARVESTER (ETHICAL FULL-TEXT ACQUISITION)" if not is_es else "  COSECHADOR DE PDF EN ACCESO ABIERTO (ADQUISICIÓN ÉTICA)")
    print("=" * 65)

    if limit and limit > 0:
        identifiers = identifiers[:limit]

    print(f"\n[Fase 1] Resolviendo metadatos de Acceso Abierto para {len(identifiers)} publicaciones..." if is_es else f"\n[Phase 1] Resolving Open Access metadata for {len(identifiers)} publications...")
    metadata_map = fetch_openalex_metadata_batch(identifiers)
    print(f"  ✓ {len(metadata_map)} metadatos de obras indexados exitosamente." if is_es else f"  ✓ {len(metadata_map)} work metadata records indexed successfully.")

    # Process download queue
    manifest_records = []
    success_count = 0
    paywalled_count = 0
    failed_count = 0
    total_bytes_downloaded = 0

    print(f"\n[Fase 2] Descarga secuencial con validación binaria y cascada de fuentes..." if is_es else f"\n[Phase 2] Sequential downloading with binary validation and waterfall resolution...")

    for idx, ident in enumerate(identifiers, 1):
        clean_id = clean_identifier(ident)
        meta = metadata_map.get(clean_id) or {}

        wid = clean_identifier(meta.get("id", clean_id))
        doi = clean_identifier(meta.get("doi", "")) if meta.get("doi") else (clean_id if "10." in clean_id else "")
        title = meta.get("title") or meta.get("display_name") or f"Work {clean_id}"
        year = meta.get("publication_year")

        oa_info = meta.get("open_access") or {}
        is_oa = oa_info.get("is_oa", False)
        oa_status = oa_info.get("oa_status", "unknown").lower()

        # Build clean filename
        name_seed = wid if wid.startswith("W") else (doi if doi else clean_id)
        file_base = sanitize_filename(f"{wid}_{doi}" if (wid and doi and wid != doi) else name_seed)
        pdf_filename = f"{file_base}.pdf"
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        txt_path = os.path.join(txt_dir, f"{file_base}.txt") if extract_text else None

        print(f"\n[{idx}/{len(identifiers)}] ({oa_status.upper()}) {title[:65]}...")

        # If already downloaded and valid
        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) >= MIN_PDF_BYTES:
            size_bytes = os.path.getsize(pdf_path)
            md5_val = calculate_md5(pdf_path)
            success_count += 1
            total_bytes_downloaded += size_bytes
            print(f"  ✓ {'Ya existente en disco' if is_es else 'Already existing on disk'} ({round(size_bytes / (1024*1024), 2)} MB): {pdf_filename}")
            
            txt_status = False
            if extract_text and txt_path and not os.path.exists(txt_path):
                txt_status = extract_text_from_pdf(pdf_path, txt_path)

            manifest_records.append({
                "work_id": wid,
                "doi": doi,
                "title": title,
                "year": year,
                "oa_status": oa_status,
                "status": "SUCCESS_ALREADY_EXISTS",
                "pdf_filename": pdf_filename,
                "pdf_path": pdf_path,
                "text_extracted": os.path.exists(txt_path) if txt_path else False,
                "source_type": "local_cache",
                "resolved_url": "",
                "file_size_mb": round(size_bytes / (1024 * 1024), 2),
                "md5": md5_val
            })
            continue

        # If not OA according to index
        if not is_oa and oa_status in ("closed", "paywalled"):
            paywalled_count += 1
            print(f"  ✗ {'Acceso cerrado / Muro de pago (Paywalled)' if is_es else 'Closed Access / Paywalled'}: No Open Access license declared.")
            manifest_records.append({
                "work_id": wid,
                "doi": doi,
                "title": title,
                "year": year,
                "oa_status": oa_status,
                "status": "PAYWALLED_CLOSED",
                "pdf_filename": "",
                "pdf_path": "",
                "text_extracted": False,
                "source_type": "none",
                "resolved_url": "",
                "file_size_mb": 0.0,
                "md5": ""
            })
            continue

        # Resolve waterfall candidates
        candidates = resolve_pdf_urls_waterfall(meta)
        if not candidates:
            failed_count += 1
            print(f"  ✗ {'No se encontraron URLs de descarga directa de PDF' if is_es else 'No direct PDF download URLs found in OA metadata'}.")
            manifest_records.append({
                "work_id": wid,
                "doi": doi,
                "title": title,
                "year": year,
                "oa_status": oa_status,
                "status": "NO_PDF_URL_FOUND",
                "pdf_filename": "",
                "pdf_path": "",
                "text_extracted": False,
                "source_type": "none",
                "resolved_url": "",
                "file_size_mb": 0.0,
                "md5": ""
            })
            continue

        # Attempt download
        print(f"  → {'Probando cascada de' if is_es else 'Trying waterfall of'} {len(candidates)} {'enlaces OA...' if is_es else 'OA candidate URLs...'}")
        success, status_msg, win_url, win_src, downloaded_bytes = download_single_pdf(
            candidates, pdf_path, timeout=timeout
        )

        if success:
            success_count += 1
            total_bytes_downloaded += downloaded_bytes
            md5_val = calculate_md5(pdf_path)
            size_mb = round(downloaded_bytes / (1024 * 1024), 2)
            print(f"  ✓ {'Descargado exitosamente' if is_es else 'Successfully downloaded'} [{win_src}] ({size_mb} MB) -> {pdf_filename}")

            txt_ok = False
            if extract_text and txt_path:
                txt_ok = extract_text_from_pdf(pdf_path, txt_path)
                if txt_ok:
                    print(f"    ✓ {'Texto plano extraído' if is_es else 'Plain text extracted'} ({round(os.path.getsize(txt_path)/1024, 1)} KB).")

            manifest_records.append({
                "work_id": wid,
                "doi": doi,
                "title": title,
                "year": year,
                "oa_status": oa_status,
                "status": "SUCCESS",
                "pdf_filename": pdf_filename,
                "pdf_path": pdf_path,
                "text_extracted": txt_ok,
                "source_type": win_src,
                "resolved_url": win_url,
                "file_size_mb": size_mb,
                "md5": md5_val
            })
        else:
            failed_count += 1
            print(f"  ✗ {'Fallo de descarga' if is_es else 'Download failed'}: {status_msg}")
            manifest_records.append({
                "work_id": wid,
                "doi": doi,
                "title": title,
                "year": year,
                "oa_status": oa_status,
                "status": f"FAILED_{status_msg}",
                "pdf_filename": "",
                "pdf_path": "",
                "text_extracted": False,
                "source_type": "none",
                "resolved_url": "",
                "file_size_mb": 0.0,
                "md5": ""
            })

        time.sleep(delay)

    # 3. Write outputs: Manifest CSV, JSON, and Summary Report
    manifest_csv = os.path.join(output_dir, "download_manifest.csv")
    with open(manifest_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "work_id", "doi", "title", "year", "oa_status", "status",
            "pdf_filename", "pdf_path", "text_extracted", "source_type",
            "resolved_url", "file_size_mb", "md5"
        ])
        writer.writeheader()
        writer.writerows(manifest_records)

    manifest_json = os.path.join(output_dir, "download_manifest.json")
    with open(manifest_json, "w", encoding="utf-8") as f:
        json.dump({
            "total_requested": len(identifiers),
            "successful_downloads": success_count,
            "paywalled_closed": paywalled_count,
            "failed_or_missing": failed_count,
            "total_megabytes": round(total_bytes_downloaded / (1024 * 1024), 2),
            "records": manifest_records
        }, f, indent=2, ensure_ascii=False)

    # Markdown Summary Report
    report_md = os.path.join(output_dir, "download_report.md")
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(f"# {'Reporte de Cosecha de Textos Completos en Acceso Abierto' if is_es else 'Open Access Full-Text Harvesting Report'}\n\n")
        f.write(f"- **{'Publicaciones Solicitadas' if is_es else 'Total Requested Works'}:** {len(identifiers)}\n")
        f.write(f"- **{'Descargas Exitosas' if is_es else 'Successfully Harvested PDFs'}:** {success_count} ({round((success_count / len(identifiers) * 100), 1) if identifiers else 0}%)\n")
        f.write(f"- **{'Cerrados / Muro de Pago' if is_es else 'Paywalled / Closed Access'}:** {paywalled_count}\n")
        f.write(f"- **{'Fallidos o Sin Enlace Directo' if is_es else 'Failed / Missing Direct Links'}:** {failed_count}\n")
        f.write(f"- **{'Volumen Total Descargado' if is_es else 'Total Harvested Volume'}:** {round(total_bytes_downloaded / (1024 * 1024), 2)} MB\n\n")

        f.write(f"## {'Diagrama de Elegibilidad de Texto Completo (PRISMA 2020)' if is_es else 'PRISMA 2020 Full-Text Eligibility Flow'}\n\n")
        f.write("```mermaid\nflowchart TD\n")
        f.write(f'    REQ["Total Obras Identificadas para Texto Completo (n = {len(identifiers)})"]\n')
        f.write(f'    REQ --> SUC["PDFs en Acceso Abierto Recuperados (n = {success_count})"]\n')
        f.write(f'    REQ --> CLO["Excluidos: Muro de Pago / Cerrados (n = {paywalled_count})"]\n')
        if failed_count > 0:
            f.write(f'    REQ --> FAI["Excluidos: Enlaces Rotos / Sin PDF (n = {failed_count})"]\n')
        f.write(f'    SUC --> SYN["Disponibles para Extracción Cualitativa y Síntesis Grounded (n = {success_count})"]\n')
        f.write("```\n\n")

        f.write(f"## {'Detalle de Artículos Descargados' if is_es else 'Harvested Articles Details'}\n\n")
        f.write("| # | OA Status | Tamaño | Estado | DOI / Título | Archivo |\n" if is_es else "| # | OA Status | Size | Status | DOI / Title | File |\n")
        f.write("|---|:---:|:---:|:---:|---|---|\n")

        for i, r in enumerate(manifest_records, 1):
            doi_link = f"[{r['doi']}](https://doi.org/{r['doi']})" if r['doi'] else r['work_id']
            title_trunc = (r['title'][:60] + "...") if len(r['title']) > 60 else r['title']
            pdf_disp = f"`{r['pdf_filename']}`" if r['pdf_filename'] else "—"
            f.write(f"| {i} | `{r['oa_status']}` | {r['file_size_mb']} MB | `{r['status']}` | **{title_trunc}**<br>{doi_link} | {pdf_disp} |\n")

    print("\n" + "=" * 65)
    print(f"✅ {'Cosecha finalizada con éxito en' if is_es else 'Harvest completed successfully in'}: '{output_dir}':")
    print(f"   - {success_count}/{len(identifiers)} {'PDFs descargados' if is_es else 'PDFs downloaded'} ({round(total_bytes_downloaded/(1024*1024), 2)} MB)")
    print(f"   - Manifiesto CSV: {manifest_csv}")
    print(f"   - Manifiesto JSON: {manifest_json}")
    print(f"   - Reporte PRISMA: {report_md}")
    print("=" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Open Access PDF Downloader CLI (Ethical & Robust Full-Text Harvester)"
    )
    parser.add_argument(
        "--lang", choices=["en", "es"], default="en",
        help="Output language for reports and terminal logs (default: en)"
    )
    parser.add_argument(
        "--dois", nargs="+", default=[],
        help="List of DOIs to harvest"
    )
    parser.add_argument(
        "--works", nargs="+", default=[],
        help="List of OpenAlex Work IDs to harvest"
    )
    parser.add_argument(
        "--input", default=None,
        help="Path to CSV, Parquet, or JSON containing DOIs or Work IDs"
    )
    parser.add_argument(
        "--output", default="./pdf",
        help="Destination directory for harvested PDFs and manifest (default: ./pdf)"
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Maximum number of articles to download"
    )
    parser.add_argument(
        "--delay", type=float, default=0.5,
        help="Politeness delay between downloads in seconds (default: 0.5)"
    )
    parser.add_argument(
        "--timeout", type=int, default=25,
        help="HTTP request timeout in seconds (default: 25)"
    )
    parser.add_argument(
        "--extract-text", action="store_true",
        help="Extract plain text (.txt) alongside PDF using pdftotext"
    )

    args = parser.parse_args()

    # Collect identifiers
    identifiers = []
    if args.input:
        identifiers.extend(load_identifiers_from_file(args.input))
    if args.dois:
        identifiers.extend(args.dois)
    if args.works:
        identifiers.extend(args.works)

    # Deduplicate
    seen = set()
    clean_ids = []
    for item in identifiers:
        c = clean_identifier(item)
        if c and c not in seen:
            seen.add(c)
            clean_ids.append(c)

    if not clean_ids:
        print("Error: No identifiers provided. Use --dois, --works, or --input <file>.", file=sys.stderr)
        sys.exit(1)

    run_oa_pdf_harvester(
        identifiers=clean_ids,
        output_dir=args.output,
        limit=args.limit,
        delay=args.delay,
        extract_text=args.extract_text,
        timeout=args.timeout,
        lang=args.lang
    )


if __name__ == "__main__":
    main()

