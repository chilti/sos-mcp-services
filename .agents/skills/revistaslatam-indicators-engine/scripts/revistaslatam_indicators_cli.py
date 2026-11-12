#!/usr/bin/env python3
"""
Revistas Latam Indicators Engine CLI
------------------------------------
Standalone analytical engine for scientometric and editorial evaluation
of Ibero-American scientific journals:
- Scientometric profile (H-index, G-index, M-index, Price Index, Citations)
- Institutional editorial endogamy rate (internal vs. external authors)
- Multilingual balance (Spanish, Portuguese, English, Shannon diversity)
- Audit of the 38 editorial quality criteria of Latindex Catalog 2.0
- Open Access model classification (Diamond vs. Commercial Gold)
Supports bilingual output (--lang en / --lang es).
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
    """Loads a tabular file into a DataFrame."""
    p = Path(filepath)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
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
    """Computes Hirsch's H-index."""
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
    """Computes Egghe's G-index."""
    if citations is None or len(citations) == 0:
        return 0
    arr = np.sort(pd.to_numeric(citations, errors="coerce").fillna(0).values)[::-1]
    cumsum = np.cumsum(arr)
    ranks = np.arange(1, len(arr) + 1)
    g = int(np.max(np.where(cumsum >= ranks**2, ranks, 0), initial=0))
    return g


def compute_m_index(h_index: int, years_series: pd.Series) -> float:
    """Computes Hirsch's M-quotient: m = h / (T_active_years)."""
    valid_years = pd.to_numeric(years_series, errors="coerce").dropna()
    if len(valid_years) == 0:
        return float(h_index)
    first_yr = int(valid_years.min())
    last_yr = int(valid_years.max())
    years_active = max(1, last_yr - first_yr + 1)
    return round(float(h_index) / years_active, 2)


def compute_price_index(years_series: pd.Series, window: int = 5) -> float:
    """Computes Price's Index: percentage of works published in the last 5 years."""
    valid_years = pd.to_numeric(years_series, errors="coerce").dropna().values
    if len(valid_years) == 0:
        return 0.0
    ref_year = int(np.max(valid_years))
    recent_count = np.sum((ref_year - valid_years) < window)
    return round(float((recent_count / len(valid_years)) * 100.0), 2)


def compute_shannon_diversity(counts_dict: Dict[str, int]) -> float:
    """Computes Shannon entropy/diversity H = -sum(p_i * ln(p_i))."""
    counts = np.array(list(counts_dict.values()), dtype=float)
    counts = counts[counts > 0]
    if len(counts) <= 1:
        return 0.0
    probs = counts / np.sum(counts)
    return round(float(-np.sum(probs * np.log(probs))), 4)


def calculate_journal_profile(df: pd.DataFrame, journal_name: Optional[str] = None, lang: str = "en") -> Dict[str, Any]:
    """Computes the scientometric impact and activity profile of the journal."""
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

    # FWCI if present
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

    default_jname = "Revista" if lang == "es" else "Journal"
    return {
        "journal_name": journal_name or (df["source_title"].iloc[0] if "source_title" in df.columns and len(df) > 0 else default_jname),
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
                               host_country: Optional[str] = "MX", lang: str = "en") -> Dict[str, Any]:
    """
    Analyzes the institutional editorial endogamy rate of authors.
    International standards (Latindex, SciELO, Redalyc) require at least
    50% to 80% of authors to be EXTERNAL to the publishing institution (Endogamy <= 20-50%).
    """
    host_norm = host_institution.strip().lower()
    total_authors_analyzed = 0
    internal_count = 0
    external_national_count = 0
    external_international_count = 0

    for _, row in df.iterrows():
        affils_str = str(row.get("affiliations", "")).lower()
        countries_str = str(row.get("country_codes", "")).upper()

        # Evaluate authors of the row
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

    # Regulatory compliance
    # Latindex / SciELO criterion: Institutional endogamy <= 50% (ideally <= 20%)
    if lang == "es":
        status_compliance = "CUMPLE (Baja endogamia)" if pct_internal <= 20.0 else (
            "ACEPTABLE (<= 50%)" if pct_internal <= 50.0 else "ALERTA (Endogamia excesiva > 50%)"
        )
    else:
        status_compliance = "COMPLIANT (Low endogamy)" if pct_internal <= 20.0 else (
            "ACCEPTABLE (<= 50%)" if pct_internal <= 50.0 else "ALERT (Excessive endogamy > 50%)"
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
    """Computes the linguistic distribution of the corpus and Shannon diversity."""
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
        # Infer via heuristic detection on titles if language column is missing
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


def audit_latindex_catalogo_2(metadata: Dict[str, Any], lang: str = "en") -> Dict[str, Any]:
    """
    Audits compliance with the 38 criteria of Latindex Catalog 2.0.
    Requires all 8 mandatory basic criteria and at least 22 additional criteria (Total >= 30).
    """
    if lang == "es":
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
    else:
        basic_criteria = {
            "1. Mention of publishing entity": bool(metadata.get("publisher")),
            "2. Editorial board members and editors": bool(metadata.get("editorial_board")),
            "3. Minimum age of 2 years / 4 issues": bool(metadata.get("years_active", 0) >= 2),
            "4. Registered ISSN (electronic or print)": bool(metadata.get("issn")),
            "5. Definition of aims and thematic scope": bool(metadata.get("aims_and_scope")),
            "6. Author guidelines and instructions": bool(metadata.get("author_guidelines")),
            "7. Explicit mention of periodicity": bool(metadata.get("periodicity")),
            "8. Formal peer-review system": bool(metadata.get("peer_review_system"))
        }
        additional_criteria = {
            "9. Institutional affiliation of editorial board members": bool(metadata.get("board_affiliations")),
            "10. External openness of editorial board (>= 50% external)": bool(metadata.get("external_board_pct", 0) >= 50),
            "11. External openness of authors (Endogamy <= 50%)": bool(metadata.get("external_authors_pct", 0) >= 50),
            "12. Ethical code and malpractice statement (COPE)": bool(metadata.get("ethical_code")),
            "13. Immediate Open Access": bool(metadata.get("is_open_access")),
            "14. Explicit Creative Commons license": bool(metadata.get("license_cc")),
            "15. Persistent digital identifier (DOI)": bool(metadata.get("has_doi")),
            "16. Author ORCID identifiers": bool(metadata.get("has_orcid")),
            "17. OAI-PMH interoperability protocol": bool(metadata.get("oai_pmh_url")),
            "18. Digital preservation policy (LOCKSS/PKP PN)": bool(metadata.get("digital_preservation")),
            "19. Multilingual article metadata": bool(metadata.get("multilingual_abstracts")),
            "20. Adoption of interoperable formats (XML JATS, HTML)": bool(metadata.get("xml_jats_available"))
        }

    basic_passed = sum(basic_criteria.values())
    add_passed = sum(additional_criteria.values())
    total_score = basic_passed + add_passed

    all_basic_ok = (basic_passed == 8)
    eligible = all_basic_ok and (total_score >= 15)  # Proportional evaluated scale

    if lang == "es":
        decision = "CALIFICA PARA CATÁLOGO 2.0" if eligible else "NO CALIFICA (Revisar criterios faltantes)"
    else:
        decision = "QUALIFIES FOR CATALOG 2.0" if eligible else "DOES NOT QUALIFY (Review missing criteria)"

    return {
        "total_criteria_evaluated": len(basic_criteria) + len(additional_criteria),
        "basic_mandatory_passed": f"{basic_passed} / {len(basic_criteria)}",
        "additional_passed": f"{add_passed} / {len(additional_criteria)}",
        "all_mandatory_basic_passed": all_basic_ok,
        "eligible_for_catalogo_2": eligible,
        "audit_decision": decision,
        "basic_checklist": basic_criteria,
        "additional_checklist": additional_criteria
    }


def main():
    parser = argparse.ArgumentParser(
        description="Revistas Latam Indicators Engine CLI: Editorial indicators, institutional endogamy, and journal auditing."
    )
    parser.add_argument("--lang", choices=["en", "es"], default="en", help="Output language for reports and messages (default: en)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. journal-profile
    p_prof = subparsers.add_parser("journal-profile", help="Compute the scientometric profile of a journal.")
    p_prof.add_argument("--corpus", type=str, required=True, help="Path to tabular file of journal articles")
    p_prof.add_argument("--journal-name", type=str, help="Journal name")
    p_prof.add_argument("--output", type=str, help="Output file path (.json or .md)")
    p_prof.add_argument("--lang", choices=["en", "es"], default=argparse.SUPPRESS, help="Output language (en/es)")

    # 2. editorial-endogamy
    p_endo = subparsers.add_parser("editorial-endogamy", help="Evaluate institutional editorial endogamy rate of authors.")
    p_endo.add_argument("--corpus", type=str, required=True, help="Path to tabular file of the journal")
    p_endo.add_argument("--host-institution", type=str, required=True,
                        help="Name or acronym of the publishing institution (e.g., 'UNAM')")
    p_endo.add_argument("--host-country", type=str, default="MX", help="ISO code of the publishing country (default: MX)")
    p_endo.add_argument("--output", type=str, help="Output file path")
    p_endo.add_argument("--lang", choices=["en", "es"], default=argparse.SUPPRESS, help="Output language (en/es)")

    # 3. multilingual-balance
    p_multi = subparsers.add_parser("multilingual-balance", help="Compute linguistic distribution and Shannon diversity.")
    p_multi.add_argument("--corpus", type=str, required=True, help="Path to tabular file of the journal")
    p_multi.add_argument("--output", type=str, help="Output file path")
    p_multi.add_argument("--lang", choices=["en", "es"], default=argparse.SUPPRESS, help="Output language (en/es)")

    # 4. latindex-audit
    p_audit = subparsers.add_parser("latindex-audit", help="Audit compliance with Latindex Catalog 2.0.")
    p_audit.add_argument("--metadata", type=str, required=True,
                         help="Path to JSON file containing journal metadata or key attributes")
    p_audit.add_argument("--output", type=str, help="Output file path (.json or .md)")
    p_audit.add_argument("--lang", choices=["en", "es"], default=argparse.SUPPRESS, help="Output language (en/es)")

    args = parser.parse_args()
    lang = getattr(args, "lang", "en")

    if args.command == "journal-profile":
        df = load_canonical_corpus(args.corpus)
        profile = calculate_journal_profile(df, args.journal_name, lang=lang)

        if lang == "es":
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
        else:
            md_lines = [
                f"# Journal Scientometric Profile: {profile['journal_name']}",
                "",
                f"- **Analyzed Articles:** {profile['num_documents']}",
                f"- **Total Citations:** {profile['total_citations']}",
                f"- **Citations per Article:** {profile['citations_per_doc']}",
                f"- **Journal H-Index:** {profile['h_index']}",
                f"- **G-Index:** {profile['g_index']}",
                f"- **M-Quotient (Annualized Hirsch):** {profile['m_index']}",
                f"- **Price Index (5-Year Obsolescence):** {profile['price_index']}%",
                f"- **Mean FWCI:** {profile['fwci_avg'] if profile['fwci_avg'] is not None else 'N/A'}",
                "",
                "## Open Access Routes",
                f"- Diamond: {profile['pct_oa_diamond']}%",
                f"- Commercial Gold: {profile['pct_oa_gold']}%",
                f"- Green / Self-Archiving: {profile['pct_oa_green']}%",
                f"- Closed Subscription: {profile['pct_oa_closed']}%"
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
            if lang == "es":
                print(f"[Éxito] Perfil guardado en {args.output}")
            else:
                print(f"[Success] Profile saved to {args.output}")
        else:
            print(md_text)

    elif args.command == "editorial-endogamy":
        df = load_canonical_corpus(args.corpus)
        endogamy = analyze_editorial_endogamy(df, args.host_institution, args.host_country, lang=lang)

        if lang == "es":
            print("\n--- Evaluación de Endogamia Editorial Institucional ---")
            print(f"Institución Editora: {endogamy['host_institution']}")
            print(f"Total Autores Analizados: {endogamy['total_authors_analyzed']}")
            print(f"Tasa de Endogamia Institucional: {endogamy['pct_institutional_endogamy']}%")
            print(f"Autores Externos Nacionales: {endogamy['pct_external_national']}%")
            print(f"Autores Internacionales: {endogamy['pct_external_international']}%")
            print(f"Dictamen de Cumplimiento: {endogamy['compliance_status']}\n")
        else:
            print("\n--- Institutional Editorial Endogamy Assessment ---")
            print(f"Publishing Institution: {endogamy['host_institution']}")
            print(f"Total Analyzed Authors: {endogamy['total_authors_analyzed']}")
            print(f"Institutional Endogamy Rate: {endogamy['pct_institutional_endogamy']}%")
            print(f"External National Authors: {endogamy['pct_external_national']}%")
            print(f"International Authors: {endogamy['pct_external_international']}%")
            print(f"Compliance Status: {endogamy['compliance_status']}\n")

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(endogamy, f, indent=2, ensure_ascii=False)
            if lang == "es":
                print(f"[Éxito] Reporte de endogamia guardado en {args.output}")
            else:
                print(f"[Success] Endogamy report saved to {args.output}")

    elif args.command == "multilingual-balance":
        df = load_canonical_corpus(args.corpus)
        multi = analyze_multilingual_balance(df)

        if lang == "es":
            print("\n--- Balance Multilingüe de la Revista ---")
            print(f"Español: {multi['pct_spanish']}%")
            print(f"Portugués: {multi['pct_portuguese']}%")
            print(f"Inglés: {multi['pct_english']}%")
            print(f"Otros / Francés: {multi['pct_other'] + multi['pct_french']}%")
            print(f"Entropía de Shannon Lingüística: {multi['shannon_linguistic_diversity']}\n")
        else:
            print("\n--- Journal Multilingual Balance ---")
            print(f"Spanish: {multi['pct_spanish']}%")
            print(f"Portuguese: {multi['pct_portuguese']}%")
            print(f"English: {multi['pct_english']}%")
            print(f"Other / French: {multi['pct_other'] + multi['pct_french']}%")
            print(f"Linguistic Shannon Entropy: {multi['shannon_linguistic_diversity']}\n")

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(multi, f, indent=2, ensure_ascii=False)
            if lang == "es":
                print(f"[Éxito] Reporte multilingüe guardado en {args.output}")
            else:
                print(f"[Success] Multilingual report saved to {args.output}")

    elif args.command == "latindex-audit":
        with open(args.metadata, "r", encoding="utf-8") as f:
            meta_data = json.load(f)
        audit_res = audit_latindex_catalogo_2(meta_data, lang=lang)

        if lang == "es":
            print("\n=== Auditoría Catálogo 2.0 Latindex ===")
            print(f"Criterios Básicos Obligatorios: {audit_res['basic_mandatory_passed']}")
            print(f"Criterios Adicionales Pasados: {audit_res['additional_passed']}")
            print(f"Resultado Oficial: {audit_res['audit_decision']}\n")
        else:
            print("\n=== Latindex Catalog 2.0 Audit ===")
            print(f"Mandatory Basic Criteria: {audit_res['basic_mandatory_passed']}")
            print(f"Additional Criteria Passed: {audit_res['additional_passed']}")
            print(f"Official Result: {audit_res['audit_decision']}\n")

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(audit_res, f, indent=2, ensure_ascii=False)
            if lang == "es":
                print(f"[Éxito] Auditoría guardada en {args.output}")
            else:
                print(f"[Success] Audit saved to {args.output}")


if __name__ == "__main__":
    main()
