---
name: open-access-pdf-downloader
description: >-
  Automated, ethical harvesting of full-text scientific PDFs for Open Access publications (Gold, Diamond, Green, Hybrid, Bronze) using waterfall resolution (OpenAlex best OA location, arXiv, PMC, institutional repositories), strict binary verification (%PDF- magic header and byte validation), and PRISMA audit manifest generation. Operates Workspace-First consuming DOIs, OpenAlex IDs, or candidate tables (CSV/Parquet). Respond and label outputs in the user's language.
---

# Open Access PDF Downloader

Expert agent skill for the automated, legal, and ethical acquisition of scientific full-text PDFs for Open Access (OA) literature. 

It bridges the gap between bibliometric discovery (metadata, abstracts, and citation networks) and qualitative/full-text extraction (deep reading, evidence synthesis, and local RAG indexing) under the **Workspace-First principle** and the **PRISMA 2020 Full-Text Eligibility** standard.

---

## 1. Core Principles

1. **Strictly Legal Open Access Acquisition:**
   - Harvester operates exclusively over publications with verified open licensing (Creative Commons, Public Domain, Diamond Open Access) or authorized green open access repositories (arXiv, PubMed Central, Zenodo, institutional repositories).
   - Never bypasses paywalls or access controls. Closed-access articles are flagged as `PAYWALLED_CLOSED` in the audit manifest.

2. **Waterfall Resolution Algorithm:**
   For each requested identifier, candidate URLs are prioritized through a multi-tier fallback:
   - **Tier 1:** `best_oa_location.pdf_url` (highest reliability reported by OpenAlex).
   - **Tier 2:** `primary_location.pdf_url` (publisher version of record).
   - **Tier 3:** Secondary repositories (Europe PMC, Zenodo, institutional repositories).
   - **Tier 4:** Direct repository resolvers (arXiv: `https://arxiv.org/pdf/{id}.pdf`, PMC: `https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/`).

3. **Binary Verification & Anti-False-Positive Filtering:**
   - Many web servers return an HTTP 200 status code containing an HTML login page or CAPTCHA instead of the actual PDF.
   - The harvester streams the initial chunk to verify the `%PDF-` binary magic header. If an HTML `<!DOCTYPE html` or `<html` tag is detected, the attempt is immediately rejected and the waterfall falls back to the next repository.
   - Files smaller than 15 KB are rejected as stubs or corrupted downloads.

4. **PRISMA 2020 Full-Text Audit Manifest:**
   - Every execution writes `download_manifest.csv` and `download_manifest.json` recording:
     `work_id`, `doi`, `title`, `year`, `oa_status`, `status`, `pdf_filename`, `file_size_mb`, `source_type`, `resolved_url`, and `md5`.

5. **Integrated Plain-Text Extraction (Optional):**
   - With `--extract-text`, it invokes `/usr/bin/pdftotext -layout` to generate matching `.txt` files alongside `.pdf` files, ready for LLM reading, grounded evidence extraction, or vector embedding.

---

## 2. Command Line Interface: `download_oa_pdfs.py`

The primary CLI engine is located at:
`scripts/download_oa_pdfs.py`

### Python Environment:
Execute with the configured Python environment:
`/home/ambientesPy/revistaslatam/bin/python`

### CLI Options:

```text
options:
  -h, --help            Show help message and exit
  --lang {en,es}        Output language for reports and terminal logs (default: en)
  --dois DOIS [DOIS ...]
                        Explicit list of DOIs to harvest
  --works WORKS [WORKS ...]
                        Explicit list of OpenAlex Work IDs to harvest
  --input INPUT         Path to CSV, Parquet, or JSON containing DOIs or Work IDs
  --output OUTPUT       Destination directory (default: ./pdf)
  --limit LIMIT         Maximum number of publications to harvest
  --delay DELAY         Politeness delay between requests in seconds (default: 0.5)
  --timeout TIMEOUT     HTTP request timeout in seconds (default: 25)
  --extract-text        Extract plain text (.txt) alongside PDF using pdftotext
```

---

## 3. Workflow Examples

### A. Harvesting from a Prior Snowballing Result (CSV Input)
Consume candidates produced by `deep-literature-researcher`:

```bash
/home/ambientesPy/revistaslatam/bin/python \
  /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/open-access-pdf-downloader/scripts/download_oa_pdfs.py \
  --input ./reportes/cognitive_offloading_educacion/snowball_candidates.csv \
  --limit 15 \
  --output ./reportes/cognitive_offloading_educacion/fulltext_oa \
  --extract-text \
  --lang es
```

### B. Direct DOI List Harvesting
Download a set of specific landmark papers:

```bash
/home/ambientesPy/revistaslatam/bin/python \
  /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/open-access-pdf-downloader/scripts/download_oa_pdfs.py \
  --dois "10.1038/s41598-025-01676-x" "10.3390/soc15010006" "10.48550/arXiv.2506.08872" \
  --output ./pdf_harvest \
  --extract-text \
  --lang en
```

### C. Mass Harvesting from Canonical Parquet Corpus
Extract open-access PDFs for the top 50 cited works in a field delineation corpus:

```bash
/home/ambientesPy/revistaslatam/bin/python \
  /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/open-access-pdf-downloader/scripts/download_oa_pdfs.py \
  --input ./corpus.parquet \
  --limit 50 \
  --output ./pdf_corpus \
  --delay 1.0 \
  --lang es
```

---

## 4. Generated Artifacts

Executing the harvester generates a structured directory inside `--output`:

```text
<output_dir>/
├── pdf/
│   ├── W4410319159_10_1038_s41598_025_01676_x.pdf
│   ├── W4406026056_10_3390_soc15010006.pdf
│   └── ...
├── text/                        # Present if --extract-text is enabled
│   ├── W4410319159_10_1038_s41598_025_01676_x.txt
│   └── ...
├── download_manifest.csv        # Tabular audit manifest
├── download_manifest.json       # Structured metrics and metadata
└── download_report.md           # Markdown executive summary with PRISMA Mermaid flow
```

---

## 5. Methodological Guidelines for the Agent

1. **Respond in the User's Language:** If the user interacts in Spanish, emit explanations and reports in Spanish (`--lang es`), while preserving standard academic naming conventions.
2. **Never Fabricate PDF Availability:** If an article is closed-access or the direct links fail, accurately report `PAYWALLED_CLOSED` or `NO_PDF_URL_FOUND`.
3. **Workspace-First Rule:** Always save outputs inside the active workspace directory (e.g. `./reportes/...` or `./pdf/`), never in system `/tmp/` unless explicitly requested.

