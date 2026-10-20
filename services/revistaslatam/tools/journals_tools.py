import re
import json
from typing import List, Dict, Any, Optional
from shared.clickhouse import execute_safe_query


def get_journal_impact_profile(journal_issn_or_name: str) -> Dict[str, Any]:
    """
    Recupera el perfil cienciométrico integral de una revista científica
    (FWCI medio, citas, percentiles Top 10%, OA, indexación DOAJ, país y tipo).
    Consulta ClickHouse (rag.sources, rag.cube_sources_yearly, rag.works_academic_all).
    """
    clean_id = journal_issn_or_name.strip()
    if not clean_id:
        return {"status": "error", "message": "Se requiere el ISSN o nombre de la revista."}

    safe_q = clean_id.replace("'", "''")

    # 1. Buscar en catálogo canónico rag.sources
    sql_source = f"""
    SELECT id, display_name, issn_l, type, works_count, cited_by_count, country_code, raw_data
    FROM rag.sources
    WHERE (issn_l = '{safe_q}' OR display_name ILIKE '%{safe_q}%')
    ORDER BY works_count DESC
    LIMIT 1
    """
    res_source = execute_safe_query(sql_source)
    source_rows = res_source.get("data", [])

    if not source_rows:
        return {
            "status": "not_found",
            "journal_identifier": clean_id,
            "message": f"No se localizó la revista con identificador '{clean_id}' en el catálogo canónico rag.sources."
        }

    s = source_rows[0]
    source_id = s.get("id", "")
    display_name = s.get("display_name", "")
    issn_l = s.get("issn_l", "")
    country_code = s.get("country_code", "")
    total_works = s.get("works_count", 0)
    total_cits = s.get("cited_by_count", 0)

    # 2. Consultar agregaciones anuales en rag.cube_sources_yearly
    safe_source_id = source_id.replace("'", "''")
    sql_cube = f"""
    SELECT 
        sum(doc_count) AS total_docs,
        sum(cits_sum) AS total_cits,
        round(sum(fwci_sum) / greatest(sum(doc_count), 1), 3) AS mean_fwci,
        round(sum(top_10_sum) * 100.0 / greatest(sum(doc_count), 1), 2) AS top_10_percent_share,
        round(sum(top_1_sum) * 100.0 / greatest(sum(doc_count), 1), 2) AS top_1_percent_share,
        round(sum(oa_total_sum) * 100.0 / greatest(sum(doc_count), 1), 2) AS oa_percentage
    FROM rag.cube_sources_yearly
    WHERE source_id = '{safe_source_id}'
    """
    res_cube = execute_safe_query(sql_cube)
    cube_data = res_cube.get("data", [{}])[0] if res_cube.get("data") else {}

    mean_fwci = cube_data.get("mean_fwci") or (round(total_cits / max(total_works, 1), 2) if total_works > 0 else 1.0)
    top_10_share = cube_data.get("top_10_percent_share", 0.0)
    oa_share = cube_data.get("oa_percentage", 0.0)

    # 3. Metadatos de Open Access e Indexación en rag.works_academic_all si está disponible
    sql_oa = f"""
    SELECT 
        countIf(lower(oa_status) = 'diamond') AS diamond_docs,
        countIf(lower(oa_status) = 'gold') AS gold_docs,
        countIf(is_doaj_journal = 1 OR journal_is_in_doaj = 1) AS doaj_docs,
        count() AS total_local_docs
    FROM rag.works_academic_all
    WHERE source_id = '{safe_source_id}'
    """
    res_oa = execute_safe_query(sql_oa)
    oa_data = res_oa.get("data", [{}])[0] if res_oa.get("data") else {}

    diamond_docs = oa_data.get("diamond_docs", 0)
    gold_docs = oa_data.get("gold_docs", 0)
    is_doaj = oa_data.get("doaj_docs", 0) > 0

    oa_pathway = "Diamante (Sin cobro APC)" if diamond_docs > gold_docs else ("Dorada (Gold APC)" if gold_docs > 0 else "Híbrida / Mixta")

    return {
        "status": "success",
        "journal_identifier": clean_id,
        "source_id": source_id,
        "display_name": display_name,
        "issn_l": issn_l,
        "country_code": country_code,
        "source_type": s.get("type", "journal"),
        "metrics": {
            "total_works": total_works,
            "total_citations": total_cits,
            "mean_fwci": mean_fwci,
            "top_10_percent_share": top_10_share,
            "top_1_percent_share": cube_data.get("top_1_percent_share", 0.0)
        },
        "open_access_profile": {
            "oa_percentage": oa_share,
            "predominant_oa_pathway": oa_pathway,
            "doaj_indexed": is_doaj
        },
        "summary": f"Revista '{display_name}' ({country_code or 'Global'}, ISSN {issn_l}): {total_works:,} artículos, FWCI medio {mean_fwci}, {oa_share}% Acceso Abierto ({oa_pathway})."
    }


def compare_journals_benchmarking(journal_identifiers: List[str]) -> Dict[str, Any]:
    """
    Compara simultáneamente un conjunto de revistas científicas en FWCI, producción,
    citas, percentiles de excelencia y vía de acceso abierto sobre ClickHouse.
    """
    if not journal_identifiers:
        return {"status": "error", "message": "Se requiere al menos un identificador de revista."}

    benchmarking = []
    for j_id in journal_identifiers[:10]:
        profile = get_journal_impact_profile(j_id)
        if profile.get("status") == "success":
            m = profile.get("metrics", {})
            oa = profile.get("open_access_profile", {})
            benchmarking.append({
                "journal": profile.get("display_name"),
                "issn_l": profile.get("issn_l"),
                "country": profile.get("country_code"),
                "total_works": m.get("total_works", 0),
                "total_citations": m.get("total_citations", 0),
                "mean_fwci": m.get("mean_fwci", 0.0),
                "top_10_share_pct": m.get("top_10_percent_share", 0.0),
                "oa_pct": oa.get("oa_percentage", 0.0),
                "oa_pathway": oa.get("predominant_oa_pathway", "N/A")
            })

    if not benchmarking:
        return {
            "status": "not_found",
            "comparison_count": 0,
            "comparison_table": [],
            "summary": "No se encontraron perfiles de revistas para los identificadores proporcionados."
        }

    sorted_table = sorted(benchmarking, key=lambda x: x.get("mean_fwci", 0.0), reverse=True)

    return {
        "status": "success",
        "comparison_count": len(sorted_table),
        "comparison_table": sorted_table,
        "top_performing_journal": sorted_table[0] if sorted_table else None,
        "summary": f"Comparación completada para {len(sorted_table)} revistas. Líder por impacto FWCI: '{sorted_table[0]['journal']}' ({sorted_table[0]['mean_fwci']})."
    }


def analyze_country_editorial_landscape(country_code: str = "MX") -> Dict[str, Any]:
    """
    Analiza el ecosistema editorial de un país en ClickHouse:
    Total de revistas activas en rag.sources, volumen de producción, impacto y desglose de Acceso Abierto.
    """
    cc = country_code.upper().strip()
    safe_cc = cc.replace("'", "''")

    # 1. Revistas indexadas del país
    sql_journals = f"""
    SELECT 
        count() AS total_journals,
        sum(works_count) AS total_papers,
        sum(cited_by_count) AS total_citations
    FROM rag.sources
    WHERE country_code = '{safe_cc}'
    """
    res_j = execute_safe_query(sql_journals)
    j_data = res_j.get("data", [{}])[0] if res_j.get("data") else {}

    total_journals = j_data.get("total_journals", 0)
    total_papers = j_data.get("total_papers", 0)
    total_citations = j_data.get("total_citations", 0)

    # 2. Desglose de Acceso Abierto y Vías en rag.works_academic_all
    sql_oa = f"""
    SELECT 
        count() AS total_national_works,
        countIf(is_oa IN ('1', 'true')) AS total_oa_works,
        round(countIf(is_oa IN ('1', 'true')) * 100.0 / greatest(count(), 1), 1) AS oa_share_pct,
        countIf(lower(oa_status) = 'diamond') AS diamond_works,
        round(countIf(lower(oa_status) = 'diamond') * 100.0 / greatest(countIf(is_oa IN ('1', 'true')), 1), 1) AS diamond_share_pct,
        countIf(lower(oa_status) = 'gold') AS gold_works,
        round(countIf(lower(oa_status) = 'gold') * 100.0 / greatest(countIf(is_oa IN ('1', 'true')), 1), 1) AS gold_share_pct,
        round(avg(fwci), 2) AS mean_national_fwci
    FROM rag.works_academic_all
    WHERE has(all_country_codes, '{safe_cc}')
    """
    res_oa = execute_safe_query(sql_oa)
    oa_data = res_oa.get("data", [{}])[0] if res_oa.get("data") else {}

    oa_pct = oa_data.get("oa_share_pct", 0.0)
    diamond_pct = oa_data.get("diamond_share_pct", 0.0)
    gold_pct = oa_data.get("gold_share_pct", 0.0)
    fwci = oa_data.get("mean_national_fwci", 0.0)

    return {
        "status": "success",
        "country_code": cc,
        "total_active_journals": total_journals,
        "total_articles_published": total_papers,
        "total_citations": total_citations,
        "open_access_landscape": {
            "overall_oa_percentage": oa_pct,
            "diamond_open_access_percentage": diamond_pct,
            "gold_apc_percentage": gold_pct,
            "other_oa_percentage": round(max(0.0, 100.0 - diamond_pct - gold_pct), 1)
        },
        "mean_national_fwci": fwci,
        "summary": f"Ecosistema editorial de {cc}: {total_journals:,} revistas activas en rag.sources con {total_papers:,} artículos. El {oa_pct}% de la producción científica está en Acceso Abierto, con una fuerte presencia Diamante ({diamond_pct}% de las publicaciones OA)."
    }
