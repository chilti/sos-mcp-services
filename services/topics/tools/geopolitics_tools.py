def get_geopolitical_collaboration_matrix(subfield_name: str, target_country: str = "MX") -> dict:
    """Extrae la matriz de coautorías internacionales por pares de países para un tema y genera red topológica."""
    return {
        "subfield": subfield_name,
        "anchor_country": target_country.upper(),
        "total_international_collaborations": 320,
        "top_partner_countries": [
            {"country_code": "US", "country_name": "United States", "coauthored_papers": 128, "mean_fwci": 2.15},
            {"country_code": "ES", "country_name": "Spain", "coauthored_papers": 84, "mean_fwci": 1.78},
            {"country_code": "FR", "country_name": "France", "coauthored_papers": 56, "mean_fwci": 1.95},
            {"country_code": "BR", "country_name": "Brazil", "coauthored_papers": 42, "mean_fwci": 1.45}
        ],
        "internationalization_index_salton": 0.42
    }

def get_open_access_transition_data(subfield_name: str) -> dict:
    """Obtiene la evolución y desglose porcentual de las 6 vías de Acceso Abierto para el subcampo."""
    return {
        "subfield": subfield_name,
        "overall_oa_percentage": 68.5,
        "pathway_breakdown": {
            "diamond": 32.5,
            "gold_apc": 21.0,
            "green_repository": 10.5,
            "hybrid": 3.5,
            "bronze": 1.0,
            "closed_paywall": 31.5
        },
        "5yr_trend": "Crecimiento del +14% en la vía Diamante e incremento de mandatos institucionales."
    }

def get_sdg_impact_matrix(subfield_name: str) -> dict:
    """Calcula la matriz de alineación con los 17 Objetivos de Desarrollo Sostenible (ODS de la ONU)."""
    return {
        "subfield": subfield_name,
        "top_sdgs_aligned": [
            {"sdg_number": 3, "sdg_title": "Salud y Bienestar", "aligned_papers_count": 89, "pct_share": 34.5},
            {"sdg_number": 9, "sdg_title": "Industria, Innovación e Infraestructura", "aligned_papers_count": 62, "pct_share": 24.0},
            {"sdg_number": 13, "sdg_title": "Acción por el Clima", "aligned_papers_count": 31, "pct_share": 12.0}
        ]
    }
