"""
Shared Workspace-First utilities, environment/config resolution, embedded QueryValidator fallback,
canonical schema bridge (CANONICAL_COLUMNS), and local-first embedding client.
"""
from __future__ import annotations

import importlib.util
import os
import re
import unicodedata
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_CFG = SKILL_DIR / "configs" / "template_domain.yaml"

CANONICAL_COLUMNS = [
    "id", "doi", "pmid", "pmcid", "title", "abstract", "publication_year",
    "publication_date", "journal_name", "issn", "publisher", "cited_by_count",
    "is_oa", "oa_status", "apc_paid_usd", "author_names", "author_ids",
    "affiliations", "countries", "keywords", "mesh_terms", "topics",
    "fwci", "is_top_10", "references", "source_harvester",
]


class EmbeddedQueryValidator:
    """Self-contained PRESS/GLOBAL syntax validator when bibliometric-search-strategist is absent."""

    @staticmethod
    def validate(query: str, lang: str = "en") -> dict[str, Any]:
        errors, warnings = [], []
        stack = []
        for i, ch in enumerate(query):
            if ch == "(":
                stack.append(i)
            elif ch == ")":
                if not stack:
                    errors.append(f"Orphan closing parenthesis at {i}")
                else:
                    stack.pop()
        if stack:
            errors.append(f"Unclosed parenthesis at {stack[0]}")
        if query.count('"') % 2 != 0:
            errors.append("Unbalanced double quotes")
        parts = re.split(r'("[^"]*")', query)
        for i, part in enumerate(parts):
            if i % 2 == 0:
                for m in re.finditer(r"\b([a-zA-ZáéíóúñÁÉÍÓÚÑ]{1,3})\*", part):
                    warnings.append(f"Short wildcard stem < 4 chars: {m.group(0)}")
                for m in re.finditer(r"\b(and|or|not)\b", part):
                    warnings.append(f"Lowercase operator '{m.group(0)}'")
        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def load_query_validator():
    """Loads QueryValidator from sibling bibliometric-search-strategist skill if present, else embedded fallback."""
    candidates = [
        SKILL_DIR.parent / "bibliometric-search-strategist" / "scripts" / "query_synthesizer.py",
        Path.home() / ".gemini" / "config" / "skills" / "bibliometric-search-strategist" / "scripts" / "query_synthesizer.py",
    ]
    for p in candidates:
        if p.exists():
            try:
                spec = importlib.util.spec_from_file_location("query_synthesizer", p)
                mod = importlib.util.module_from_spec(spec)
                assert spec.loader is not None
                spec.loader.exec_module(mod)
                return mod.QueryValidator
            except Exception:
                pass
    return EmbeddedQueryValidator


def resolve_workdir(workdir: str | None) -> Path:
    wd = Path(workdir or ".").resolve()
    wd.mkdir(parents=True, exist_ok=True)
    return wd


def load_env_vars(workdir: Path, cfg: dict | None = None) -> dict[str, str]:
    env: dict[str, str] = {}
    search_files = [
        workdir / ".env",
        SKILL_DIR.parent.parent.parent / ".env",
    ]
    cfg_env = ((cfg or {}).get("endpoints") or {}).get("env_file")
    if cfg_env and Path(cfg_env).exists():
        search_files.insert(0, Path(cfg_env))

    for p in search_files:
        if p.exists():
            for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                ln = line.strip()
                if not ln or ln.startswith("#") or "=" not in ln:
                    continue
                k, v = ln.split("=", 1)
                env.setdefault(k.strip(), v.strip().strip('"').strip("'"))

    for k, v in os.environ.items():
        if v:
            env[k] = v
    return env


def load_or_create_config(
    workdir: Path,
    config_path: str | None = None,
    topic_en: str | None = None,
    topic_es: str | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    country: str | None = None,
    country_name: str | None = None,
    biomedical: bool | None = None,
    llm_base_url: str | None = None,
    llm_model: str | None = None,
    embedding_base_url: str | None = None,
    embedding_model: str | None = None,
) -> tuple[dict[str, Any], Path]:
    cfg_file = Path(config_path) if config_path else (workdir / "delineation_config.yaml")
    created_new = not cfg_file.exists()
    if cfg_file.exists():
        cfg = yaml.safe_load(cfg_file.read_text(encoding="utf-8"))
    else:
        cfg = yaml.safe_load(TEMPLATE_CFG.read_text(encoding="utf-8"))

    if topic_en:
        cfg["domain"]["seed_topic_en"] = topic_en
        slug = re.sub(r"[^a-z0-9]+", "_", topic_en.lower()).strip("_")[:48]
        cfg["domain"]["project_slug"] = slug or "custom_field"
    if topic_es:
        cfg["domain"]["seed_topic_es"] = topic_es
    elif topic_en and cfg["domain"].get("seed_topic_es") == "Tu tema cientifico":
        cfg["domain"]["seed_topic_es"] = topic_en
    if year_from is not None:
        cfg["scope"]["year_start"] = int(year_from)
    if year_to is not None:
        cfg["scope"]["year_end"] = int(year_to)
    if country is not None:
        c_up = country.strip().upper()
        cfg["scope"]["geo_country_code"] = c_up
        cfg["geography_rescue"]["iso_code"] = c_up
        if country_name:
            cfg["scope"]["geo_country_name"] = country_name
    elif country_name:
        cfg["scope"]["geo_country_name"] = country_name
    if biomedical is not None:
        cfg["domain"]["is_biomedical"] = bool(biomedical)

    # Apply env overrides only on initial creation (so explicit per-workspace YAML edits persist)
    env = load_env_vars(workdir, cfg)
    if created_new:
        if env.get("LM_STUDIO_URL"):
            cfg["endpoints"]["llm_base_url"] = env["LM_STUDIO_URL"]
            cfg["endpoints"]["embedding_base_url"] = env["LM_STUDIO_URL"]
        if env.get("OPENALEX_MAILTO") or env.get("OPENALEX_EMAIL"):
            cfg["endpoints"]["openalex_mailto"] = env.get("OPENALEX_MAILTO") or env.get("OPENALEX_EMAIL")

    if llm_base_url:
        cfg["endpoints"]["llm_base_url"] = llm_base_url
    if llm_model:
        cfg["endpoints"]["llm_model"] = llm_model
    if embedding_base_url:
        cfg["endpoints"]["embedding_base_url"] = embedding_base_url
    if embedding_model:
        cfg["endpoints"]["embedding_model"] = embedding_model

    if created_new or any(x is not None for x in (topic_en, topic_es, year_from, year_to, country, country_name, biomedical, llm_base_url, llm_model, embedding_base_url, embedding_model)):
        cfg_file.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return cfg, cfg_file


def phase_dir(workdir: Path, phase_name: str) -> Path:
    p = workdir / "delineation" / phase_name
    p.mkdir(parents=True, exist_ok=True)
    return p


def strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", str(text or "")) if not unicodedata.combining(c))


def norm_doi(val: Any) -> str:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    s = str(val).strip().lower()
    s = re.sub(r"^https?://(dx\.)?doi\.org/", "", s)
    s = re.sub(r"^doi:\s*", "", s)
    return s if "/" in s else ""


def norm_pmid(val: Any) -> str:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    s = re.sub(r"\D+", "", str(val).split(".")[0])
    return s if 4 <= len(s) <= 10 else ""


def norm_oa_id(val: Any) -> str:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    m = re.search(r"(W\d+)", str(val).strip(), flags=re.IGNORECASE)
    return m.group(1).upper() if m else ""


def norm_title(val: Any) -> str:
    s = strip_accents(str(val or "")).lower()
    s = re.sub(r"^\[+|\]+$", "", s.strip())
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def first_author_surname(val: Any) -> str:
    s = strip_accents(str(val or "")).lower().strip()
    if not s:
        return ""
    first = re.split(r"[;|]", s)[0].strip()
    if "," in first:
        return re.sub(r"[^a-z]", "", first.split(",")[0])
    parts = re.findall(r"[a-z]{2,}", first)
    return parts[-1] if parts else ""


def _split_list(val: Any, sep_rx: str = r"[;|,]+") -> list[str]:
    if isinstance(val, (list, np.ndarray)):
        return [str(x).strip() for x in val if str(x or "").strip()]
    s = str(val or "").strip()
    if not s:
        return []
    return [p.strip() for p in re.split(sep_rx, s) if p.strip()]


def to_canonical_corpus(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts the internal Phase 5 dataframe into a canonical Parquet table matching
    sos-mcp-services shared/canonical_schema.py (27 CANONICAL_COLUMNS) while preserving
    delineation audit columns (final_corpus_layer, zona_triaje, margin_score, rrf_score, domain, field, subfield, language, doc_type_norm).
    """
    out = pd.DataFrame(index=df.index)
    oids = df.get("oa_id", pd.Series("", index=df.index)).fillna("").astype(str).tolist()
    uids = df.get("work_uid", pd.Series("", index=df.index)).fillna("").astype(str).tolist()
    out["id"] = [f"https://openalex.org/{o}" if o else u for o, u in zip(oids, uids)]
    out["doi"] = df.get("doi_norm", pd.Series("", index=df.index)).replace("", None)
    out["pmid"] = df.get("pmid_norm", pd.Series("", index=df.index)).replace("", None)
    out["pmcid"] = df.get("pmcid", pd.Series("", index=df.index)).replace("", None)
    out["title"] = df.get("title", pd.Series("", index=df.index)).fillna("").astype(str)
    out["abstract"] = df.get("abstract_final", pd.Series("", index=df.index)).fillna("").astype(str)
    out["publication_year"] = pd.to_numeric(df.get("publication_year", 0), errors="coerce").astype("Int64")
    out["publication_date"] = out["publication_year"].apply(lambda y: f"{int(y)}-01-01" if pd.notna(y) and y > 0 else None)
    out["journal_name"] = df.get("source_venue", pd.Series("", index=df.index)).replace("", None)
    out["issn"] = None
    out["publisher"] = None
    out["cited_by_count"] = pd.to_numeric(df.get("cited_by_count", 0), errors="coerce").fillna(0).astype("int64")
    raw_oa = df.get("is_oa", pd.Series(False, index=df.index)).astype(str).str.lower()
    out["is_oa"] = raw_oa.isin(["true", "1", "yes", "open access", "gold", "diamond", "green", "hybrid", "bronze"])
    out["oa_status"] = df.get("oa_status", pd.Series("closed", index=df.index)).replace("", "closed").astype(str).str.lower()
    out["apc_paid_usd"] = pd.to_numeric(df.get("apc_paid_usd", 0.0), errors="coerce").fillna(0.0).astype(float)
    out["author_names"] = df.get("author_names", pd.Series("", index=df.index)).apply(lambda x: _split_list(x, r"[;|]+"))
    out["author_ids"] = [[] for _ in range(len(df))]
    out["affiliations"] = df.get("affiliations_raw", pd.Series("", index=df.index)).apply(lambda x: _split_list(x, r"[|]+"))
    out["countries"] = df.get("country_codes", pd.Series("", index=df.index)).apply(lambda x: _split_list(x, r"[,;\s|]+"))
    out["keywords"] = df.get("keywords", pd.Series("", index=df.index)).apply(lambda x: _split_list(x, r"[,;]+"))
    out["mesh_terms"] = [[] for _ in range(len(df))]
    out["topics"] = df.get("topic", pd.Series("", index=df.index)).apply(lambda x: _split_list(x, r"[;|]+"))
    out["fwci"] = pd.to_numeric(df.get("fwci", 0.0), errors="coerce").fillna(0.0).astype(float)
    out["is_top_10"] = 0
    out["references"] = [[] for _ in range(len(df))]
    out["source_harvester"] = df.get("sources_list", pd.Series("hybrid_delineation", index=df.index)).astype(str)

    # Extra metadata & delineation layer columns for downstream stratified filtering
    for extra in [
        "work_uid", "oa_id", "language", "doc_type_norm", "domain", "field", "subfield",
        "final_corpus_layer", "zona_triaje", "via_captacion", "margin_score", "rrf_score",
        "lex_score", "llm_decision", "snowball_rescued",
    ]:
        if extra in df.columns:
            out[extra] = df[extra].values
    return out
