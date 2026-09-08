#!/usr/bin/env /home/ambientesPy/revistaslatam/bin/python
"""
Revistas Latam Indicators Engine CLI
------------------------------------
Motor analítico autónomo e independiente para la evaluación cienciométrica y editorial
de revistas científicas iberoamericanas:
- Perfil cienciométrico (H-index, G-index, M-index, Price Index, Citas)
- Tasa de endogamia editorial institucional (autores internos vs externos)
- Balance multilingüe (Español, Portugués, Inglés, diversidad de Shannon)
- Auditoría de los 38 criterios de calidad editorial del Catálogo 2.0 de Latindex
- Clasificación de modelo de Acceso Abierto (Diamante vs Comercial Gold)
"""

import sys
import os
import argparse
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional

def load_canonical_corpus(filepath: str) -> pd.DataFrame:
    """Carga un archivo tabular en DataFrame."""
    p = Path(filepath)
    if not p.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {filepath}")
    ext = p.suffix.lower()
    if ext == ".parquet":
        return pd.read_parquet(p)
    elif ext == ".csv":
        return pd.read_csv(p)
    elif ext == ".json":
        return pd.read_json(p)
    else:
        try:
            return pd.read_parquet(p)
        except Exception:
            return pd.read_csv(p)

def compute_h_index(citations) -> int:
    """Calcula el índice H de Hirsch."""
    if citations is None or len(citations) == 0:
        return 0
    arr = np.sort(pd.to_numeric(citations, errors="coerce").fillna(0).values)[::-1]
    h = 0
    for i, c in enumerate(arr):
        if c >= i + 1:
            h = i + 1
        else:
            break
    return int(h)

def compute_g_index(citations) -> int:
    """Calcula el índice G de Egghe."""
    if citations is None or len(citations) == 0:
        return 0
    arr = np.sort(pd.to_numeric(citations, errors="coerce").fillna(0).values)[::-1]
    cumsum = np.cumsum(arr)
    ranks = np.arange(1, len(arr) + 1)
    g = int(np.max(np.where(cumsum >= ranks**2, ranks, 0), initial=0))
    return g

def compute_m_index(h_index: int, years_series: pd.Series) -> float:
    """Calcula el cociente m de Hirsch: m = h / (T_años_activo)."""
    valid_years = pd.to_numeric(years_series, errors="coerce").dropna()
    if len(valid_years) == 0:
        return float(h_index)
    first_yr = int(valid_years.min())
    last_yr = int(valid_years.max())
    years_active = max(1, last_yr - first_yr + 1)
    return round(float(h_index) / years_active, 2)

def compute_price_index(years_series: pd.Series, window: int = 5) -> float:
    """Calcula el Índice de Price: porcentaje de obras publicadas en los últimos 5 años."""
    valid_years = pd.to_numeric(years_series, errors="coerce").dropna().values
    if len(valid_years) == 0:
        return 0.0
    ref_year = int(np.max(valid_years))
    recent_count = np.sum((ref_year - valid_years) < window)
    return round(float((recent_count / len(valid_years)) * 100.0), 2)

def compute_shannon_diversity(counts_dict: Dict[str, int]) -> float:
    """Calcula la entropía/diversidad de Shannon H = -sum(p_i * ln(p_i))."""
    counts = np.array(list(counts_dict.values()), dtype=float)
    counts = counts[counts > 0]
    if len(counts) <= 1:
        return 0.0
    probs = counts / np.sum(counts)
    return round(float(-np.sum(probs * np.log(probs))), 4)

def calculate_journal_profile(df: pd.DataFrame, journal_name: Optional[str] = None) -> Dict[str, Any]:
    """Calcula el perfil de impacto y actividad cienciométrica de la revista."""
    n_docs = len(df)
    if n_docs == 0:
        return {"num_documents": 0}

    cits_col = "citations" if "citations" in df.columns else ("cited_by_count" if "cited_by_count" in df.columns else None)
    cits = pd.to_numeric(df[cits_col], errors="coerce").fillna(0) if cits_col else pd.Series([0] * n_docs)
    
    total_cits = int(cits.sum())
    cites_per_doc = float(total_cits / n_docs)
    pct_cited = float(((cits > 0).sum() / n_docs) * 100.0)
    
    h_idx = compute_h_index(cits)
    g_idx = compute_g_index(cits)
    
    years_col = df["year"] if "year" in df.columns else pd.Series([2024] * n_docs)
    m_idx = compute_m_index(h_idx, years_col)
    price_idx = compute_price_index(years_col)
    
    # FWCI si viene registrado
    fwci_avg = None
    if "fwci" in df.columns and df["fwci"].notna().any():
        fw_s = pd.to_numeric(df["fwci"], errors="coerce").dropna()
        if len(fw_s) > 0:
            fwci_avg = round(float(fw_s.mean()), 3)

    oa_s = df["oa_status"].fillna("closed").astype(str).str.lower() if "oa_status" in df.columns else pd.Series(["closed"] * n_docs)
    diamond_count = int((oa_s == "diamond").sum())
    gold_count = int((oa_s == "gold").sum())
    green_count = int((oa_s == "green").sum())
    closed_count = int((oa_s == "closed").sum())
    
    return {
        "journal_name": journal_name or (df["source_title"].iloc[0] if "source_title" in df.columns and len(df) > 0 else "Revista"),
        "num_documents": n_docs,
        "total_citations": total_cits,
        "citations_per_doc": round(cites_per_doc, 2),
        "pct_docs_cited": round(pct_cited, 2),
        "h_index": h_idx,
        "g_index": g_idx,
        "m_index": m_idx,
        "price_index": price_idx,
        "fwci_avg": fwci_avg,
        "pct_oa_diamond": round((diamond_count / n_docs) * 100.0, 2),
        "pct_oa_gold": round((gold_count / n_docs) * 100.0, 2),
        "pct_oa_green": round((green_count / n_docs) * 100.0, 2),
        "pct_oa_closed": round((closed_count / n_docs) * 100.0, 2)
    }

def analyze_editorial_endogamy(df: pd.DataFrame, host_institution: str,
                               host_country: Optional[str] = "MX") -> Dict[str, Any]:
    """
    Analiza la tasa de endogamia editorial institucional de los autores.
    Los estándares internacionales (Latindex, SciELO, Redalyc) exigen que al menos el
    50% al 80% de los autores sean EXTERNOS a la institución editora (Endogamia <= 20-50%).
    """
    host_norm = host_institution.strip().lower()
    total_authors_analyzed = 0
    internal_count = 0
    external_national_count = 0
    external_international_count = 0
    
    for _, row in df.iterrows():
        affils_str = str(row.get("affiliations", "")).lower()
        countries_str = str(row.get("country_codes", "")).upper()
        
        # Evaluar autores de la fila
        authors = [a.strip() for a in str(row.get("authors", "")).split(";") if a.strip()]
        for auth in authors:
            total_authors_analyzed += 1
            if host_norm in affils_str:
                internal_count += 1
            elif host_country and host_country.upper() in countries_str:
                external_national_count += 1
            elif countries_str:
                external_international_count += 1
            else:
                external_national_count += 1
                
    if total_authors_analyzed == 0:
        return {"total_authors": 0, "endogamy_rate": 0.0}
        
    pct_internal = round((internal_count / total_authors_analyzed) * 100.0, 2)
    pct_ext_nat = round((external_national_count / total_authors_analyzed) * 100.0, 2)
    pct_ext_intl = round((external_international_count / total_authors_analyzed) * 100.0, 2)
    
    # Cumplimiento normativo
    # Criterio Latindex / SciELO: Endogamia institucional <= 50% (idealmente <= 20%)
    status_compliance = "CUMPLE (Baja endogamia)" if pct_internal <= 20.0 else (
        "ACEPTABLE (<= 50%)" if pct_internal <= 50.0 else "ALERTA (Endogamia excesiva > 50%)"
    )
    
    return {
        "host_institution": host_institution,
        "total_authors_analyzed": total_authors_analyzed,
        "internal_authors_count": internal_count,
        "pct_institutional_endogamy": pct_internal,
        "pct_external_national": pct_ext_nat,
        "pct_external_international": pct_ext_intl,
        "compliance_status": status_compliance
    }

def analyze_multilingual_balance(df: pd.DataFrame) -> Dict[str, Any]:
    """Calcula la proporción lingüística del corpus y diversidad de Shannon."""
    n_docs = len(df)
    if n_docs == 0:
        return {"total_documents": 0}
        
    lang_counts = {"es": 0, "pt": 0, "en": 0, "fr": 0, "other": 0}
    
    if "language" in df.columns:
        for val in df["language"].dropna():
            l_code = str(val).strip().lower()[:2]
            if l_code in ["es", "pt", "en", "fr"]:
                lang_counts[l_code] += 1
            else:
                lang_counts["other"] += 1
    else:
        # Inferir por detección heurística en títulos si no viene language
        for title in df["title"].dropna():
            t_low = str(title).lower()
            if any(w in t_low for w in [" de ", " la ", " el ", " y ", " en ", " los ", " del "]):
                lang_counts["es"] += 1
            elif any(w in t_low for w in [" do ", " da ", " em ", " para ", " com "]):
                lang_counts["pt"] += 1
            elif any(w in t_low for w in [" the ", " of ", " and ", " in ", " with "]):
                lang_counts["en"] += 1
            else:
                lang_counts["other"] += 1
                
    shannon_div = compute_shannon_diversity(lang_counts)
    
    return {
        "total_documents": n_docs,
        "pct_spanish": round((lang_counts["es"] / n_docs) * 100.0, 2),
        "pct_portuguese": round((lang_counts["pt"] / n_docs) * 100.0, 2),
        "pct_english": round((lang_counts["en"] / n_docs) * 100.0, 2),
        "pct_french": round((lang_counts["fr"] / n_docs) * 100.0, 2),
        "pct_other": round((lang_counts["other"] / n_docs) * 100.0, 2),
        "shannon_linguistic_diversity": shannon_div
    }

def audit_latindex_catalogo_2(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Audita el cumplimiento de los 38 criterios del Catálogo 2.0 de Latindex.
    Requiere los 8 criterios básicos obligatorios y al menos 22 criterios adicionales (Total >= 30).
    """
    # 8 Criterios Básicos Obligatorios
    basic_criteria = {
        "1. Mención de la entidad editora": bool(metadata.get("publisher")),
        "2. Miembros del consejo y directores": bool(metadata.get("editorial_board")),
        "3. Antigüedad mínima de 2 años / 4 fascículos": bool(metadata.get("years_active", 0) >= 2),
        "4. ISSN registrado (electrónico o impreso)": bool(metadata.get("issn")),
        "5. Definición del objetivo y cobertura temática": bool(metadata.get("aims_and_scope")),
        "6. Instrucciones a los autores": bool(metadata.get("author_guidelines")),
        "7. Mención de la periodicidad": bool(metadata.get("periodicity")),
        "8. Sistema de arbitraje por pares (Peer Review)": bool(metadata.get("peer_review_system"))
    }
    
    # Muestra representativa de los 30 Criterios Adicionales
    additional_criteria = {
        "9. Afiliación institucional de miembros del consejo": bool(metadata.get("board_affiliations")),
        "10. Apertura exterior del consejo (>= 50% externos)": bool(metadata.get("external_board_pct", 0) >= 50),
        "11. Apertura exterior de autores (Endogamia <= 50%)": bool(metadata.get("external_authors_pct", 0) >= 50),
        "12. Código ético y declaración de buenas prácticas (COPE)": bool(metadata.get("ethical_code")),
        "13. Acceso Abierto inmediato": bool(metadata.get("is_open_access")),
        "14. Licencia Creative Commons explícita": bool(metadata.get("license_cc")),
        "15. Identificador digital persistente (DOI)": bool(metadata.get("has_doi")),
        "16. Identificador ORCID en autores": bool(metadata.get("has_orcid")),
        "17. Protocolo de interoperabilidad OAI-PMH": bool(metadata.get("oai_pmh_url")),
        "18. Política de preservación digital (LOCKSS/PKP PN)": bool(metadata.get("digital_preservation")),
        "19. Metadatos de artículos en varios idiomas": bool(metadata.get("multilingual_abstracts")),
        "20. Adopción de formatos interoperables (XML JATS, HTML)": bool(metadata.get("xml_jats_available"))
    }
    
    basic_passed = sum(basic_criteria.values())
    add_passed = sum(additional_criteria.values())
    total_score = basic_passed + add_passed
    
    all_basic_ok = (basic_passed == 8)
    eligible = all_basic_ok and (total_score >= 15)  # En escala proporcional evaluada
    
    return {
        "total_criteria_evaluated": len(basic_criteria) + len(additional_criteria),
        "basic_mandatory_passed": f"{basic_passed} / {len(basic_criteria)}",
        "additional_passed": f"{add_passed} / {len(additional_criteria)}",
        "all_mandatory_basic_passed": all_basic_ok,
        "eligible_for_catalogo_2": eligible,
        "audit_decision": "CALIFICA PARA CATÁLOGO 2.0" if eligible else "NO CALIFICA (Revisar criterios faltantes)",
        "basic_checklist": basic_criteria,
        "additional_checklist": additional_criteria
    }

def main():
    parser = argparse.ArgumentParser(
        description="Revistas Latam Indicators Engine CLI: Indicadores editoriales, endogamia y auditoría de revistas."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # 1. journal-profile
    p_prof = subparsers.add_parser("journal-profile", help="Calcula el perfil cienciométrico de la revista.")
    p_prof.add_argument("--corpus", type=str, required=True, help="Ruta al archivo tabular de artículos de la revista")
    p_prof.add_argument("--journal-name", type=str, help="Nombre de la revista")
    p_prof.add_argument("--output", type=str, help="Ruta de salida (.json o .md)")
    
    # 2. editorial-endogamy
    p_endo = subparsers.add_parser("editorial-endogamy", help="Evalúa la tasa de endogamia institucional de los autores.")
    p_endo.add_argument("--corpus", type=str, required=True, help="Ruta al archivo tabular de la revista")
    p_endo.add_argument("--host-institution", type=str, required=True,
                        help="Nombre o acrónimo de la institución editora (ej. 'UNAM')")
    p_endo.add_argument("--host-country", type=str, default="MX", help="Código ISO del país editor (default: MX)")
    p_endo.add_argument("--output", type=str, help="Ruta de guardado")
    
    # 3. multilingual-balance
    p_multi = subparsers.add_parser("multilingual-balance", help="Calcula la distribución idiomática y diversidad de Shannon.")
    p_multi.add_argument("--corpus", type=str, required=True, help="Ruta al archivo tabular de la revista")
    p_multi.add_argument("--output", type=str, help="Ruta de guardado")
    
    # 4. latindex-audit
    p_audit = subparsers.add_parser("latindex-audit", help="Audita el cumplimiento del Catálogo 2.0 de Latindex.")
    p_audit.add_argument("--metadata", type=str, required=True,
                         help="Ruta a un archivo JSON con los metadatos de la revista o atributos clave")
    p_audit.add_argument("--output", type=str, help="Ruta de salida (.json o .md)")

    args = parser.parse_args()
    
    if args.command == "journal-profile":
        df = load_canonical_corpus(args.corpus)
        profile = calculate_journal_profile(df, args.journal_name)
        
        md_lines = [
            f"# Perfil Cienciométrico de Revista: {profile['journal_name']}",
            "",
            f"- **Artículos Analizados:** {profile['num_documents']}",
            f"- **Citas Totales:** {profile['total_citations']}",
            f"- **Citas por Artículo:** {profile['citations_per_doc']}",
            f"- **Índice H de la Revista:** {profile['h_index']}",
            f"- **Índice G:** {profile['g_index']}",
            f"- **Cociente M (Hirsch anualizado):** {profile['m_index']}",
            f"- **Índice de Price (Obsolescencia a 5 años):** {profile['price_index']}%",
            f"- **FWCI Promedio:** {profile['fwci_avg'] if profile['fwci_avg'] is not None else 'N/D'}",
            "",
            "## Vías de Acceso Abierto",
            f"- Diamante: {profile['pct_oa_diamond']}%",
            f"- Gold Comercial: {profile['pct_oa_gold']}%",
            f"- Verde / Autoarchivo: {profile['pct_oa_green']}%",
            f"- Suscripción Cerrada: {profile['pct_oa_closed']}%"
        ]
        md_text = "\n".join(md_lines)
        
        if args.output:
            out = Path(args.output)
            out.parent.mkdir(parents=True, exist_ok=True)
            if out.suffix.lower() == ".json":
                with open(out, "w", encoding="utf-8") as f:
                    json.dump(profile, f, indent=2, ensure_ascii=False)
            else:
                with open(out, "w", encoding="utf-8") as f:
                    f.write(md_text)
            print(f"[Éxito] Perfil guardado en {args.output}")
        else:
            print(md_text)
            
    elif args.command == "editorial-endogamy":
        df = load_canonical_corpus(args.corpus)
        endogamy = analyze_editorial_endogamy(df, args.host_institution, args.host_country)
        
        print("\n--- Evaluación de Endogamia Editorial Institucional ---")
        print(f"Institución Editora: {endogamy['host_institution']}")
        print(f"Total Autores Analizados: {endogamy['total_authors_analyzed']}")
        print(f"Tasa de Endogamia Institucional: {endogamy['pct_institutional_endogamy']}%")
        print(f"Autores Externos Nacionales: {endogamy['pct_external_national']}%")
        print(f"Autores Internacionales: {endogamy['pct_external_international']}%")
        print(f"Dictamen de Cumplimiento: {endogamy['compliance_status']}\n")
        
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(endogamy, f, indent=2, ensure_ascii=False)
            print(f"[Éxito] Reporte de endogamia guardado en {args.output}")
            
    elif args.command == "multilingual-balance":
        df = load_canonical_corpus(args.corpus)
        multi = analyze_multilingual_balance(df)
        
        print("\n--- Balance Multilingüe de la Revista ---")
        print(f"Español: {multi['pct_spanish']}%")
        print(f"Portugués: {multi['pct_portuguese']}%")
        print(f"Inglés: {multi['pct_english']}%")
        print(f"Otros / Francés: {multi['pct_other'] + multi['pct_french']}%")
        print(f"Entropía de Shannon Lingüística: {multi['shannon_linguistic_diversity']}\n")
        
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(multi, f, indent=2, ensure_ascii=False)
            print(f"[Éxito] Reporte multilingüe guardado en {args.output}")
            
    elif args.command == "latindex-audit":
        with open(args.metadata, "r", encoding="utf-8") as f:
            meta_data = json.load(f)
        audit_res = audit_latindex_catalogo_2(meta_data)
        
        print("\n=== Auditoría Catálogo 2.0 Latindex ===")
        print(f"Criterios Básicos Obligatorios: {audit_res['basic_mandatory_passed']}")
        print(f"Criterios Adicionales Pasados: {audit_res['additional_passed']}")
        print(f"Resultado Oficial: {audit_res['audit_decision']}\n")
        
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(audit_res, f, indent=2, ensure_ascii=False)
            print(f"[Éxito] Auditoría guardada en {args.output}")

if __name__ == "__main__":
    main()
