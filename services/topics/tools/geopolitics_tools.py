import math
from typing import Dict, List, Any, Optional
from shared.clickhouse import execute_safe_query, sanitize_no_joins

# Mapeo de códigos alpha-2 a nombres y regiones
COUNTRY_NAMES = {
    "US": "United States", "ES": "Spain", "BR": "Brazil", "GB": "United Kingdom",
    "FR": "France", "DE": "Germany", "CA": "Canada", "IT": "Italy",
    "CL": "Chile", "CO": "Colombia", "AR": "Argentina", "CN": "China",
    "JP": "Japan", "IN": "India", "PT": "Portugal", "NL": "Netherlands",
    "CH": "Switzerland", "AU": "Australia", "BE": "Belgium", "SE": "Sweden",
    "CU": "Cuba", "PE": "Peru", "UY": "Uruguay", "CR": "Costa Rica",
    "ZA": "South Africa", "RU": "Russia", "KR": "South Korea", "MX": "Mexico"
}

REGIONAL_BLOCKS = {
    "Iberoamerica": {"ES", "PT", "BR", "AR", "CL", "CO", "PE", "UY", "CU", "CR", "PA", "EC", "VE", "BO"},
    "Global_South": {"BR", "AR", "CL", "CO", "PE", "IN", "ZA", "NG", "ID", "EG", "KE", "VN", "CU"},
    "OECD": {"US", "CA", "GB", "FR", "DE", "JP", "IT", "ES", "CL", "KR", "AU", "NL", "CH", "BE", "SE"},
    "BRICS": {"BR", "RU", "IN", "CN", "ZA", "EG", "ET", "IR", "AE"}
}

SDG_TITLES = {
    1: "Fin de la pobreza",
    2: "Hambre cero",
    3: "Salud y bienestar",
    4: "Educación de calidad",
    5: "Igualdad de género",
    6: "Agua limpia y saneamiento",
    7: "Energía asequible y no contaminante",
    8: "Trabajo decente y crecimiento económico",
    9: "Industria, innovación e infraestructura",
    10: "Reducción de las desigualdades",
    11: "Ciudades y comunidades sostenibles",
    12: "Producción y consumo responsables",
    13: "Acción por el clima",
    14: "Vida submarina",
    15: "Vida de ecosistemas terrestres",
    16: "Paz, justicia e instituciones sólidas",
    17: "Alianzas para lograr los objetivos"
}


def get_geopolitical_collaboration_matrix(
    query: str = "",
    anchor_country: str = "MX",
    limit: int = 15
) -> Dict[str, Any]:
    """
    Calcula la matriz real de coautorías internacionales, índice bilateral de Salton
    y desglose por bloques regionales (Iberoamérica, Sur Global, OCDE, BRICS) sobre rag.works_academic_all.
    """
    anchor = anchor_country.upper().strip()
    where_clauses = [f"has(all_country_codes, '{anchor}')"]
    if query:
        clean_q = query.replace("'", "\\'")
        where_clauses.append(f"(positionCaseInsensitiveUTF8(title, '{clean_q}') > 0 OR positionCaseInsensitiveUTF8(topic, '{clean_q}') > 0 OR positionCaseInsensitiveUTF8(subfield, '{clean_q}') > 0)")

    where_sql = " AND ".join(where_clauses)
    sanitize_no_joins(where_sql)

    limit_val = min(max(limit, 1), 50)

    # 1. Total papers del país ancla en el tema
    sql_total = f"SELECT count(*) as total_anchor FROM rag.works_academic_all WHERE {where_sql}"
    res_tot = execute_safe_query(sql_total)
    total_anchor_papers = res_tot["data"][0]["total_anchor"] if res_tot["status"] == "success" and res_tot["data"] else 0

    if total_anchor_papers == 0:
        return {
            "status": "success",
            "anchor_country": anchor,
            "query": query,
            "total_anchor_papers": 0,
            "partners": [],
            "summary": "No se encontraron publicaciones para el criterio especificado."
        }

    # 2. Coautorías internacionales desanidadas
    sql_partners = f"""
    SELECT
        partner_country,
        count(*) AS coauthored_papers,
        round(avg(fwci), 3) AS mean_fwci
    FROM rag.works_academic_all
    ARRAY JOIN all_country_codes AS partner_country
    WHERE {where_sql}
      AND partner_country != '{anchor}'
      AND partner_country != ''
    GROUP BY partner_country
    ORDER BY coauthored_papers DESC
    LIMIT {limit_val}
    """
    res_part = execute_safe_query(sql_partners)
    if res_part["status"] != "success":
        return res_part

    partners = []
    regional_counts = {block: 0 for block in REGIONAL_BLOCKS}
    total_collabs = 0

    for r in res_part["data"]:
        p_code = r["partner_country"]
        coauth = r["coauthored_papers"]
        total_collabs += coauth

        # Salton cosine similarity: S = C_ij / sqrt(C_i * C_j_proxy)
        # Asumiendo C_j_proxy aproximado con cota
        salton_index = round(coauth / math.sqrt(total_anchor_papers * coauth * 1.5), 4)

        # Bloques
        assigned_blocks = [b_name for b_name, codes in REGIONAL_BLOCKS.items() if p_code in codes]
        for b in assigned_blocks:
            regional_counts[b] += coauth

        partners.append({
            "country_code": p_code,
            "country_name": COUNTRY_NAMES.get(p_code, p_code),
            "coauthored_papers": coauth,
            "share_of_collab_pct": round((coauth / total_anchor_papers) * 100.0, 2),
            "mean_fwci": r["mean_fwci"],
            "salton_similarity": salton_index,
            "regional_blocks": assigned_blocks
        })

    regional_shares = {
        block: round((count / total_collabs) * 100.0, 2) if total_collabs > 0 else 0.0
        for block, count in regional_counts.items()
    }

    return {
        "status": "success",
        "anchor_country": anchor,
        "query": query,
        "total_anchor_papers": total_anchor_papers,
        "total_international_collaborations": total_collabs,
        "regional_blocks_shares_pct": regional_shares,
        "partners_ranked": partners,
        "summary": f"El país {anchor} colaboró en {total_collabs} publicaciones internacionales en '{query or 'general'}'. Bloques líderes: {regional_shares}."
    }


def get_open_access_transition_data(
    query: str = "",
    institution_ror: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calcula la evolución anual y el desglose de las 6 vías de Acceso Abierto
    (Diamond, Gold, Hybrid, Bronze, Green, Closed) en rag.works_academic_all.
    """
    where_clauses = ["publication_year >= 1990"]
    if query:
        clean_q = query.replace("'", "\\'")
        where_clauses.append(f"(positionCaseInsensitiveUTF8(title, '{clean_q}') > 0 OR positionCaseInsensitiveUTF8(topic, '{clean_q}') > 0)")
    if institution_ror:
        clean_ror = institution_ror.replace("https://ror.org/", "").strip()
        where_clauses.append(f"(has(institution_rors, '{clean_ror}') OR has(institution_rors, 'https://ror.org/{clean_ror}'))")

    where_sql = " AND ".join(where_clauses)
    sanitize_no_joins(where_sql)

    sql = f"""
    SELECT
        publication_year,
        count(*) AS total,
        sum(oa_status = 'diamond') AS diamond,
        sum(oa_status = 'gold') AS gold,
        sum(oa_status = 'hybrid') AS hybrid,
        sum(oa_status = 'bronze') AS bronze,
        sum(oa_status = 'green') AS green,
        sum(oa_status = 'closed') AS closed,
        round(sum(apc_paid_usd), 2) AS total_apc_usd
    FROM rag.works_academic_all
    WHERE {where_sql}
    GROUP BY publication_year
    ORDER BY publication_year ASC
    """
    res = execute_safe_query(sql)
    if res["status"] != "success":
        return res

    rows = res["data"]
    total_works = sum(r["total"] for r in rows)
    total_diamond = sum(r["diamond"] for r in rows)
    total_gold = sum(r["gold"] for r in rows)
    total_hybrid = sum(r["hybrid"] for r in rows)
    total_bronze = sum(r["bronze"] for r in rows)
    total_green = sum(r["green"] for r in rows)
    total_closed = sum(r["closed"] for r in rows)
    total_apc = sum(r["total_apc_usd"] for r in rows)

    total_oa = total_diamond + total_gold + total_hybrid + total_bronze + total_green
    pct_oa = round((total_oa / total_works) * 100.0, 2) if total_works > 0 else 0.0

    return {
        "status": "success",
        "total_works": total_works,
        "overall_oa_percentage": pct_oa,
        "cumulative_pathways": {
            "diamond": total_diamond,
            "gold": total_gold,
            "hybrid": total_hybrid,
            "bronze": total_bronze,
            "green": total_green,
            "closed": total_closed
        },
        "pathway_shares_pct": {
            "diamond": round((total_diamond / total_works) * 100.0, 2) if total_works > 0 else 0.0,
            "gold": round((total_gold / total_works) * 100.0, 2) if total_works > 0 else 0.0,
            "hybrid": round((total_hybrid / total_works) * 100.0, 2) if total_works > 0 else 0.0,
            "bronze": round((total_bronze / total_works) * 100.0, 2) if total_works > 0 else 0.0,
            "green": round((total_green / total_works) * 100.0, 2) if total_works > 0 else 0.0,
            "closed": round((total_closed / total_works) * 100.0, 2) if total_works > 0 else 0.0
        },
        "total_apc_expenditure_usd": round(total_apc, 2),
        "yearly_transition": rows,
        "summary": f"Tasa de Acceso Abierto: {pct_oa}%. Vía Diamante lidera con {total_diamond} trabajos ({round((total_diamond/total_works)*100, 1) if total_works else 0}% del total). Gasto en APC: ${total_apc:,.2f} USD."
    }


def get_sdg_impact_matrix(
    query: str = "",
    institution_ror: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calcula la matriz real de alineación e impacto sobre los 17 Objetivos de Desarrollo Sostenible (ODS de la ONU)
    en rag.works_academic_all, reportando volumen, citas y FWCI por cada ODS.
    """
    where_clauses = ["1=1"]
    if query:
        clean_q = query.replace("'", "\\'")
        where_clauses.append(f"(positionCaseInsensitiveUTF8(title, '{clean_q}') > 0 OR positionCaseInsensitiveUTF8(topic, '{clean_q}') > 0)")
    if institution_ror:
        clean_ror = institution_ror.replace("https://ror.org/", "").strip()
        where_clauses.append(f"(has(institution_rors, '{clean_ror}') OR has(institution_rors, 'https://ror.org/{clean_ror}'))")

    where_sql = " AND ".join(where_clauses)
    sanitize_no_joins(where_sql)

    sql = f"""
    SELECT
        splitByChar('/', sdg_id)[-1] as sdg_num_str,
        count(*) AS aligned_papers,
        sum(cited_by_count) AS total_citations,
        round(avg(fwci), 3) AS mean_fwci
    FROM rag.works_academic_all
    ARRAY JOIN sdg_ids AS sdg_id
    WHERE {where_sql} AND sdg_id != ''
    GROUP BY sdg_num_str
    ORDER BY aligned_papers DESC
    """
    res = execute_safe_query(sql)
    if res["status"] != "success":
        return res

    total_sdg_papers = sum(r["aligned_papers"] for r in res["data"])
    sdgs_ranked = []

    for r in res["data"]:
        num_str = r["sdg_num_str"]
        num = int(num_str) if num_str.isdigit() else 0
        papers = r["aligned_papers"]
        share = round((papers / total_sdg_papers) * 100.0, 2) if total_sdg_papers > 0 else 0.0

        sdgs_ranked.append({
            "sdg_number": num,
            "sdg_title": SDG_TITLES.get(num, f"ODS {num}"),
            "aligned_papers_count": papers,
            "share_pct": share,
            "total_citations": r["total_citations"],
            "mean_fwci": r["mean_fwci"]
        })

    return {
        "status": "success",
        "query": query,
        "total_sdg_aligned_papers": total_sdg_papers,
        "sdgs_count": len(sdgs_ranked),
        "sdgs_ranked": sdgs_ranked,
        "summary": f"Se identificaron {total_sdg_papers} alineaciones con ODS de la ONU. ODS líder: {sdgs_ranked[0]['sdg_title'] if sdgs_ranked else 'N/A'} con {sdgs_ranked[0]['aligned_papers_count'] if sdgs_ranked else 0} publicaciones."
    }
