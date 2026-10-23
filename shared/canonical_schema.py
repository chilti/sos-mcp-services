"""
Canonical Scientometrics Schema
--------------------------------
Esquema canónico unificado para la estandarización de publicaciones científicas
provenientes de cualquier fuente (OpenAlex, PubMed, Scopus, The Lens, arXiv, Crossref).
"""

from typing import List, Dict, Any, Optional
import pandas as pd

CANONICAL_COLUMNS = [
    "id",
    "doi",
    "pmid",
    "pmcid",
    "title",
    "abstract",
    "publication_year",
    "publication_date",
    "journal_name",
    "issn",
    "publisher",
    "cited_by_count",
    "is_oa",
    "oa_status",
    "apc_paid_usd",
    "author_names",
    "author_ids",
    "affiliations",
    "countries",
    "keywords",
    "mesh_terms",
    "topics",
    "fwci",
    "is_top_10",
    "references",
    "source_harvester"
]


def create_empty_canonical_dataframe() -> pd.DataFrame:
    """Crea un DataFrame vacío con las columnas del esquema canónico."""
    return pd.DataFrame({col: pd.Series(dtype=object) for col in CANONICAL_COLUMNS})


def normalize_record_to_canonical(record: Dict[str, Any], default_source: str = "unknown") -> Dict[str, Any]:
    """
    Asegura que un diccionario de publicación contenga todas las claves
    del esquema canónico con tipos y valores por defecto coherentes.
    """
    return {
        "id": str(record.get("id") or ""),
        "doi": record.get("doi") or None,
        "pmid": record.get("pmid") or None,
        "pmcid": record.get("pmcid") or None,
        "title": str(record.get("title") or "").strip(),
        "abstract": record.get("abstract") or "",
        "publication_year": int(record["publication_year"]) if record.get("publication_year") is not None and str(record["publication_year"]).isdigit() else None,
        "publication_date": record.get("publication_date") or None,
        "journal_name": record.get("journal_name") or record.get("source_name") or None,
        "issn": record.get("issn") or None,
        "publisher": record.get("publisher") or None,
        "cited_by_count": int(record.get("cited_by_count") or 0),
        "is_oa": bool(record.get("is_oa", False)),
        "oa_status": str(record.get("oa_status") or "closed").lower(),
        "apc_paid_usd": float(record["apc_paid_usd"]) if record.get("apc_paid_usd") is not None else 0.0,
        "author_names": list(record.get("author_names") or []),
        "author_ids": list(record.get("author_ids") or []),
        "affiliations": list(record.get("affiliations") or []),
        "countries": list(record.get("countries") or []),
        "keywords": list(record.get("keywords") or []),
        "mesh_terms": list(record.get("mesh_terms") or []),
        "topics": list(record.get("topics") or []),
        "fwci": float(record["fwci"]) if record.get("fwci") is not None else None,
        "is_top_10": int(record.get("is_top_10", 0)),
        "references": list(record.get("references") or []),
        "source_harvester": record.get("source_harvester") or default_source
    }


def save_canonical_corpus(records: List[Dict[str, Any]], output_path: str, default_source: str = "unknown") -> str:
    """
    Guarda una lista de registros normalizados en formato Parquet, JSON o CSV
    según la extensión del archivo de salida.
    """
    normalized = [normalize_record_to_canonical(r, default_source=default_source) for r in records]
    df = pd.DataFrame(normalized)
    
    # Asegurar tipos canónicos en pandas
    if "publication_year" in df.columns:
        df["publication_year"] = pd.to_numeric(df["publication_year"], errors="coerce").astype("Int64")
    if "cited_by_count" in df.columns:
        df["cited_by_count"] = pd.to_numeric(df["cited_by_count"], errors="coerce").fillna(0).astype("int64")
    if "is_oa" in df.columns:
        df["is_oa"] = df["is_oa"].astype(bool)
    if "is_top_10" in df.columns:
        df["is_top_10"] = pd.to_numeric(df["is_top_10"], errors="coerce").fillna(0).astype("int32")

    path_lower = output_path.lower()
    if path_lower.endswith(".parquet"):
        df.to_parquet(output_path, index=False)
    elif path_lower.endswith(".json"):
        df.to_json(output_path, orient="records", force_ascii=False, indent=2)
    elif path_lower.endswith(".csv"):
        # Convertir listas a strings para CSV
        csv_df = df.copy()
        for col in ["author_names", "author_ids", "affiliations", "countries", "keywords", "mesh_terms", "topics", "references"]:
            if col in csv_df.columns:
                csv_df[col] = csv_df[col].apply(lambda x: "; ".join(x) if isinstance(x, list) else str(x or ""))
        csv_df.to_csv(output_path, index=False, encoding="utf-8")
    else:
        # Default a parquet
        out = output_path if output_path.endswith(".parquet") else f"{output_path}.parquet"
        df.to_parquet(out, index=False)
        return out

    return output_path
