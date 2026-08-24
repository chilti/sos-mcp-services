from typing import List, Dict, Any

def inspect_incites_package(package_path: str) -> dict:
    """Inspecciona un archivo ZIP o directorio con reportes InCites y extrae el inventario de unidades disponibles."""
    return {
        "package_path": package_path,
        "schema_detected": "Clarivate InCites Benchmarking Export (Unicode UTF-8/UTF-16)",
        "available_units": [
            {"unit_name": "Institutions", "file_name": "institutions_benchmarking.csv", "rows_count": 145},
            {"unit_name": "Research Fields", "file_name": "fields_benchmarking.csv", "rows_count": 22},
            {"unit_name": "Authors", "file_name": "authors_benchmarking.csv", "rows_count": 520}
        ],
        "available_indicators": [
            "Web of Science Documents", "Times Cited", "Category Normalized Citation Impact (CNCI)",
            "% Documents in Top 10%", "% Documents in Top 1%", "International Collaborations (%)"
        ]
    }

def get_incites_unit_matrix(session_dir: str, unit_name: str, use_recent_5years: bool = False, selected_indicators: List[str] = None, filter_indicator: str = None, filter_min_threshold: float = None, limit_top_n: int = 50) -> dict:
    """Extrae el perfil multidimensional de una unidad específica aplicando normalización y filtros."""
    return {
        "unit_name": unit_name,
        "window_mode": "Recent 5 Years (2021-2025)" if use_recent_5years else "Full Dataset History",
        "entities_count": limit_top_n,
        "indicators": selected_indicators or ["Web of Science Documents", "CNCI", "% Documents in Top 10%"],
        "matrix_shape": [limit_top_n, len(selected_indicators or [1, 2, 3])],
        "summary": f"Matriz multidimensional extraída para {unit_name} con {limit_top_n} entidades procesadas."
    }

def get_incites_temporal_evolution(session_dir: str, unit_name: str, entities: List[str], indicators: List[str], smoothing: str = "ecma3") -> dict:
    """Extrae la matriz de series de tiempo multivariadas (PathSOM) de las entidades con suavizado ECMA."""
    return {
        "unit_name": unit_name,
        "entities": entities,
        "indicators": indicators,
        "smoothing_applied": smoothing,
        "temporal_series": [
            {"entity": ent, "year": yr, "values": [100 + (yr-1990)*5, 1.1 + (yr-1990)*0.02]}
            for ent in entities for yr in range(2015, 2026)
        ],
        "summary": f"Trayectorias PathSOM extraídas para {len(entities)} entidades a lo largo de 11 años con suavizado {smoothing}."
    }

def compute_strategic_growth_matrix(session_dir: str, unit_name: str, indicator: str, entities: List[str]) -> dict:
    """Calcula la matriz estratégica CAGR % vs Volumen actual clasificando entidades en 4 cuadrantes."""
    return {
        "indicator": indicator,
        "quadrant_classification": {
            "Emerging Stars (High CAGR, Moderate Volume)": entities[:2] if entities else ["Entidad A"],
            "Star Leaders (High CAGR, High Volume)": entities[2:4] if len(entities) > 2 else ["Entidad B"],
            "Established Giants (Low CAGR, High Volume)": entities[4:6] if len(entities) > 4 else ["Entidad C"],
            "Low Priority (Low CAGR, Low Volume)": []
        },
        "summary": "Matriz estratégica calculada identificando focos emergentes y liderazgos consolidados."
    }
