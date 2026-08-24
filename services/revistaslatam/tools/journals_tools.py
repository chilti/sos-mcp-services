from typing import List, Dict, Any

def get_journal_impact_profile(journal_issn_or_name: str) -> dict:
    """Recupera el perfil cienciométrico integral de una revista científica (FWCI, percentiles, OA, indexación)."""
    return {
        "journal_identifier": journal_issn_or_name,
        "display_name": "Revista Iberoamericana de Evaluación Científica",
        "issn_l": "1234-5678",
        "metrics": {
            "mean_fwci": 1.18,
            "cites_per_paper_2yr": 2.45,
            "percentile_in_field": 78.5,
            "top_10_percent_share": 14.2,
            "top_1_percent_share": 2.1
        },
        "open_access_profile": {
            "is_oa": True,
            "oa_pathway": "Diamond Open Access (No APC)",
            "license": "CC-BY-NC-ND",
            "doaj_indexed": True,
            "scielo_indexed": True,
            "redalyc_indexed": True
        },
        "multilingual_balance": {
            "spanish_pct": 65.0,
            "english_pct": 25.0,
            "portuguese_pct": 10.0
        },
        "summary": f"Revista con FWCI de 1.18 (+18% sobre la media mundial) en Acceso Abierto Diamante sin cobro de APC."
    }

def compare_journals_benchmarking(journal_identifiers: List[str]) -> dict:
    """Compara simultáneamente un conjunto de revistas científicas en FWCI, producción, internacionalización y OA."""
    benchmarking = []
    for idx, j_id in enumerate(journal_identifiers):
        benchmarking.append({
            "journal": j_id,
            "fwci": round(1.0 + (idx * 0.15) - 0.2, 2),
            "works_annual": 45 + (idx * 20),
            "international_coauthorship_pct": round(25.0 + (idx * 8.5), 1),
            "oa_type": "Diamond" if idx % 2 == 0 else "Gold (APC)"
        })
    
    return {
        "comparison_count": len(journal_identifiers),
        "comparison_table": benchmarking,
        "top_performing_journal": sorted(benchmarking, key=lambda x: x["fwci"], reverse=True)[0] if benchmarking else None
    }

def analyze_country_editorial_landscape(country_code: str = "MX") -> dict:
    """Analiza el ecosistema editorial de un país: proporción Diamante vs Gold y diversidad lingüística."""
    return {
        "country_code": country_code.upper(),
        "total_active_journals": 340 if country_code.upper() == "MX" else 150,
        "diamond_oa_percentage": 78.4,
        "gold_apc_percentage": 15.2,
        "subscription_percentage": 6.4,
        "doaj_seal_share": 18.5,
        "scielo_indexed_share": 62.0,
        "language_breakdown": {
            "spanish_only": 45.0,
            "bilingual_es_en": 40.0,
            "english_only": 15.0
        },
        "editorial_sovereignty_index": "Alto (Prevalencia del modelo Diamante universitario sin fines de lucro)"
    }
