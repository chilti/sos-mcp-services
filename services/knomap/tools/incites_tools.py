import os
import sys
import re
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

# Agregar KnoMap Engine al path tanto en Windows como en entornos Linux
KNOMAP_ENGINE_CANDIDATES = [
    Path(r"c:\Users\jlja\Documents\Proyectos\knomap\engine"),
    Path(__file__).resolve().parent.parent.parent.parent / "knomap" / "engine",
    Path("/home/labsom/knomap/engine")
]
for p in KNOMAP_ENGINE_CANDIDATES:
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    from incites_parser import (
        build_incites_inventory,
        parse_single_unit_from_session,
        clean_and_read_file,
        calculate_ecma
    )
    HAS_INCITES_PARSER = True
except Exception:
    HAS_INCITES_PARSER = False


def clean_val(val: Any) -> float:
    """Limpia cadenas numéricas con comas, porcentajes o formatos regionales."""
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).replace('%', '').replace(',', '').strip()
    try:
        return float(s)
    except Exception:
        return 0.0


def _resolve_session(session_dir_or_zip: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Resuelve o crea un directorio de sesión a partir de una ruta a ZIP o directorio existente."""
    if not os.path.exists(session_dir_or_zip):
        return None, None

    # Si es un directorio de sesión activo con inventory.json
    inv_file = os.path.join(session_dir_or_zip, "inventory.json")
    if os.path.isdir(session_dir_or_zip) and os.path.exists(inv_file):
        try:
            with open(inv_file, 'r', encoding='utf-8') as f:
                inv_data = json.load(f)
            return session_dir_or_zip, inv_data
        except Exception:
            pass

    # Si es un archivo .zip o directorio crudo
    if HAS_INCITES_PARSER:
        res = build_incites_inventory(session_dir_or_zip)
        if res.get("success"):
            s_dir = res.get("session_dir")
            inv_p = os.path.join(s_dir, "inventory.json")
            if os.path.exists(inv_p):
                with open(inv_p, 'r', encoding='utf-8') as f:
                    inv_data = json.load(f)
                return s_dir, inv_data
            return s_dir, res

    return None, None


def inspect_incites_package(package_path: str) -> Dict[str, Any]:
    """
    Inspecciona un archivo ZIP o directorio con reportes exportados de Clarivate InCites Benchmarking.
    Extrae el inventario de entidades analíticas (Organizations, Locations, Researchers, WoS Categories,
    Publication Sources, Research Areas ESI/SDG/Topic, Funding Agencies, etc.) y detecta metadatos del corpus.
    """
    if not os.path.exists(package_path):
        return {"status": "error", "message": f"No se encontró el paquete en la ruta: {package_path}"}

    session_dir, inv_data = _resolve_session(package_path)
    if not session_dir or not inv_data:
        # Fallback informativo si no se pudo parsear
        return {
            "status": "warning",
            "package_path": package_path,
            "schema_detected": "Clarivate InCites Benchmarking Export (Unicode UTF-8/UTF-16)",
            "message": "No se pudo interpretar el archivo como paquete canónico de InCites o el parser no está disponible.",
            "available_units": ["Organizations", "Locations", "Researchers", "WoS Categories", "Publication Sources"],
            "canonical_indicators": [
                "Web of Science Documents", "Times Cited", "Category Normalized Citation Impact (CNCI)",
                "Journal Normalized Citation Impact (JNCI)", "% Documents in Top 10%", "% Documents in Top 1%",
                "International Collaborations (%)", "% All Open Access Documents"
            ]
        }

    units_dict = inv_data.get("units", {})
    available_units = sorted(list(units_dict.keys()))

    sample_indicators = []
    if HAS_INCITES_PARSER and available_units:
        first_unit = "Organizations" if "Organizations" in available_units else available_units[0]
        parsed_unit = parse_single_unit_from_session(session_dir, first_unit)
        if parsed_unit.get("success"):
            sample_indicators = parsed_unit.get("unit", {}).get("indicators", [])

    return {
        "status": "success",
        "package_path": package_path,
        "session_dir": session_dir,
        "schema_detected": "Clarivate InCites Benchmarking Canonical Export",
        "available_units": available_units,
        "baseline": inv_data.get("baseline"),
        "manifest": inv_data.get("manifest"),
        "openalex_data": inv_data.get("openalex_data"),
        "sample_indicators_count": len(sample_indicators),
        "sample_indicators": sample_indicators[:12],
        "summary": (
            f"Paquete InCites inspeccionado exitosamente. "
            f"Contiene {len(available_units)} unidades analíticas ({', '.join(available_units)}). "
            f"Listo para extracción de matrices [N x D] y modelado neurocomputacional SOM."
        )
    }


def get_incites_unit_matrix(
    session_dir_or_zip: str,
    unit_name: str = "Organizations",
    period_mode: str = "Whole",
    selected_indicators: Optional[List[str]] = None,
    filter_indicator: Optional[str] = None,
    filter_min_threshold: Optional[float] = None,
    limit_top_n: int = 100
) -> Dict[str, Any]:
    """
    Extrae la matriz multidimensional limpia [N x D] de una unidad analítica específica de InCites
    (ej. Organizations, Locations, Researchers, WoS Categories, Publication Sources),
    lista para ingresar al dimensionamiento espectral (suggest_grid_size) y entrenamiento (train_som).
    """
    session_dir, inv_data = _resolve_session(session_dir_or_zip)
    if not session_dir:
        return {"status": "error", "message": f"Sesión inválida o paquete no encontrado: {session_dir_or_zip}"}

    if not HAS_INCITES_PARSER:
        return {"status": "error", "message": "Motor incites_parser no disponible en el entorno."}

    parsed = parse_single_unit_from_session(session_dir, unit_name)
    if not parsed.get("success"):
        return {"status": "error", "message": f"Error al parsear unidad InCites '{unit_name}': {parsed.get('error')}"}

    unit_data = parsed.get("unit", {})
    available_indicators = unit_data.get("indicators", [])

    # Seleccionar perfil según el modo temporal
    if period_mode.lower() in ("5years", "recent", "recent 5 years"):
        raw_rows = unit_data.get("profile_5years") or unit_data.get("profile") or []
    else:
        raw_rows = unit_data.get("profile") or []

    if not raw_rows:
        return {"status": "error", "message": f"No se encontraron registros de perfil para la unidad {unit_name}."}

    # Filtrado por umbral mínimo si se especifica
    filtered_rows = []
    for r in raw_rows:
        if filter_indicator and filter_min_threshold is not None:
            val = clean_val(r.get(filter_indicator, 0))
            if val < filter_min_threshold:
                continue
        filtered_rows.append(r)

    # Limitar al top N
    filtered_rows = filtered_rows[:limit_top_n]
    if not filtered_rows:
        return {"status": "error", "message": f"Ninguna entidad cumplió el filtro de {filter_indicator} >= {filter_min_threshold}."}

    # Determinar indicadores a extraer
    if selected_indicators:
        final_indicators = [ind for ind in selected_indicators if any(ind in r for r in filtered_rows)]
    else:
        # Batería canónica multidimensional InCites recomendada por som-methodological-expert
        default_candidates = [
            'Web of Science Documents',
            'Times Cited',
            'Category Normalized Citation Impact (CNCI)',
            'Journal Normalized Citation Impact (JNCI)',
            '% Documents in Top 10%',
            '% Documents in Top 1%',
            'Average Percentile',
            'International Collaborations (%)',
            '% All Open Access Documents',
            'Industry Collaborations (%)',
            'Share'
        ]
        final_indicators = [c for c in default_candidates if c in available_indicators]
        if not final_indicators:
            final_indicators = [c for c in available_indicators if c.lower() not in ('rank', 'id', 'name', 'entity')][:8]

    # Construir etiquetas y matriz numérica [N x D]
    labels = []
    matrix_data = []

    for r in filtered_rows:
        ent_name = str(r.get("entity", r.get("name", ""))).strip()
        if not ent_name:
            continue
        labels.append(ent_name)
        vec = []
        for ind in final_indicators:
            val = r.get(ind, 0.0)
            vec.append(clean_val(val))
        matrix_data.append(vec)

    return {
        "status": "success",
        "unit_name": unit_name,
        "period_mode": period_mode,
        "session_dir": session_dir,
        "total_entities": len(labels),
        "labels": labels,
        "indicators": final_indicators,
        "matrix_shape": [len(matrix_data), len(final_indicators)],
        "data": matrix_data,
        "summary": (
            f"Matriz InCites de {len(labels)} entidades de '{unit_name}' ({period_mode}) "
            f"con {len(final_indicators)} indicadores cienciométricos extraída con éxito. "
            f"Estructura lista para suggest_grid_size y train_som."
        )
    }


def get_incites_temporal_evolution(
    session_dir_or_zip: str,
    unit_name: str = "Organizations",
    entities: Optional[List[str]] = None,
    indicators: Optional[List[str]] = None,
    smoothing: str = "ecma3"
) -> Dict[str, Any]:
    """
    Extrae series de tiempo multivariadas y trayectorias anuales para las entidades de interés
    con suavizado exponencial ponderado (ECMA-3, ECMA-5 o raw), listo para som-trajectory-mapping (PathSOM).
    """
    session_dir, inv_data = _resolve_session(session_dir_or_zip)
    if not session_dir or not HAS_INCITES_PARSER:
        return {"status": "error", "message": "Sesión inválida o parser de InCites no disponible."}

    parsed = parse_single_unit_from_session(session_dir, unit_name)
    if not parsed.get("success"):
        return {"status": "error", "message": f"Error parseando unidad {unit_name}."}

    unit_data = parsed.get("unit", {})
    ts_dict = unit_data.get("time_series", {})
    profile_evolution = unit_data.get("profile_evolution", {})

    if not ts_dict and not profile_evolution:
        return {"status": "error", "message": f"La unidad {unit_name} no contiene series anuales (Trend.csv)."}

    chosen_indicators = indicators or list(ts_dict.keys())[:5]
    filter_entities = set([e.strip().upper() for e in entities]) if entities else None

    temporal_results = {}
    for ind in chosen_indicators:
        if ind not in ts_dict:
            continue
        series_list = ts_dict[ind]
        filtered_series = []
        for s in series_list:
            e_name = str(s.get("entity", "")).strip()
            if filter_entities and e_name.upper() not in filter_entities:
                continue
            vals = s.get(smoothing, s.get("raw", []))
            filtered_series.append({
                "entity": e_name,
                "times": s.get("times", []),
                "values": [round(clean_val(v), 4) for v in vals]
            })
            if filter_entities and len(filtered_series) >= len(filter_entities):
                break
        temporal_results[ind] = filtered_series

    # Filtrar también profile_evolution si está disponible para PathSOM
    pathsom_evolution = []
    if profile_evolution:
        target_evo = profile_evolution.get(smoothing, profile_evolution.get("raw", []))
        for row in target_evo:
            r_ent = str(row.get("entity", ""))
            # Formato "2020_UNAM" -> extraer entidad después del guion bajo
            parts = r_ent.split("_", 1)
            raw_ent = parts[1] if len(parts) > 1 else r_ent
            if not filter_entities or raw_ent.upper() in filter_entities:
                pathsom_evolution.append(row)

    return {
        "status": "success",
        "unit_name": unit_name,
        "smoothing_applied": smoothing,
        "time_series_by_indicator": temporal_results,
        "pathsom_evolution_records": pathsom_evolution[:500],
        "total_pathsom_points": len(pathsom_evolution),
        "summary": (
            f"Series multivariadas para {unit_name} extraídas exitosamente ({smoothing}). "
            f"Contiene {len(temporal_results)} indicadores monitoreados y {len(pathsom_evolution)} "
            f"puntos temporales listos para trazado de trayectorias con som-trajectory-mapping."
        )
    }


def compute_strategic_growth_matrix(
    session_dir_or_zip: str,
    unit_name: str = "Organizations",
    indicator: str = "Web of Science Documents",
    entities: Optional[List[str]] = None,
    cagr_years: int = 5
) -> Dict[str, Any]:
    """
    Calcula la matriz estratégica de crecimiento (CAGR % vs Volumen Actual) clasificando
    las entidades analizadas en 4 cuadrantes estratégicos de desempeño:
    1. Star Leaders (Alto Volumen, Alto CAGR %)
    2. Emerging Stars (Volumen Moderado, Alto CAGR %)
    3. Established Giants (Alto Volumen, Bajo CAGR %)
    4. Low Priority (Bajo Volumen, Bajo CAGR %)
    """
    session_dir, inv_data = _resolve_session(session_dir_or_zip)
    if not session_dir or not HAS_INCITES_PARSER:
        return {"status": "error", "message": "Sesión inválida o parser no disponible."}

    parsed = parse_single_unit_from_session(session_dir, unit_name)
    if not parsed.get("success"):
        return {"status": "error", "message": f"Error al parsear unidad {unit_name}."}

    unit_data = parsed.get("unit", {})
    ts_dict = unit_data.get("time_series", {})

    target_series = None
    for k in ts_dict.keys():
        if indicator.lower() in k.lower():
            target_series = ts_dict[k]
            break

    if not target_series and ts_dict:
        target_series = list(ts_dict.values())[0]

    if not target_series:
        return {"status": "error", "message": f"No se encontraron series de tiempo para el indicador '{indicator}'."}

    filter_entities = set([e.strip().upper() for e in entities]) if entities else None

    entity_metrics = []
    for s in target_series:
        e_name = str(s.get("entity", "")).strip()
        if filter_entities and e_name.upper() not in filter_entities:
            continue
        vals = s.get("raw", [])
        times = s.get("times", [])
        if len(vals) < 2:
            continue

        # Usar la ventana de los últimos cagr_years
        window_vals = vals[-cagr_years:] if len(vals) >= cagr_years else vals
        v0 = float(window_vals[0])
        vn = float(window_vals[-1])
        n_years = len(window_vals) - 1

        if v0 > 0 and n_years > 0:
            cagr = ((vn / v0) ** (1.0 / n_years) - 1.0) * 100.0
        else:
            cagr = 0.0

        entity_metrics.append({
            "entity": e_name,
            "current_volume": round(vn, 2),
            "initial_volume": round(v0, 2),
            "cagr_pct": round(cagr, 2),
            "years_window": f"{times[-len(window_vals)]} - {times[-1]}" if times else f"{n_years} years"
        })

    if not entity_metrics:
        return {"status": "error", "message": "No se encontraron suficientes datos anuales para calcular el CAGR."}

    # Calcular umbrales basados en la mediana
    volumes = [m["current_volume"] for m in entity_metrics]
    cagrs = [m["cagr_pct"] for m in entity_metrics]

    med_vol = float(sorted(volumes)[len(volumes) // 2])
    med_cagr = max(0.0, float(sorted(cagrs)[len(cagrs) // 2]))

    quadrants = {
        "Star Leaders (High Volume, High CAGR)": [],
        "Emerging Stars (Moderate Volume, High CAGR)": [],
        "Established Giants (High Volume, Low CAGR)": [],
        "Low Priority (Low Volume, Low CAGR)": []
    }

    for m in entity_metrics:
        is_high_vol = m["current_volume"] >= med_vol
        is_high_cagr = m["cagr_pct"] >= med_cagr

        if is_high_vol and is_high_cagr:
            quadrants["Star Leaders (High Volume, High CAGR)"].append(m)
        elif not is_high_vol and is_high_cagr:
            quadrants["Emerging Stars (Moderate Volume, High CAGR)"].append(m)
        elif is_high_vol and not is_high_cagr:
            quadrants["Established Giants (High Volume, Low CAGR)"].append(m)
        else:
            quadrants["Low Priority (Low Volume, Low CAGR)"].append(m)

    return {
        "status": "success",
        "unit_name": unit_name,
        "indicator": indicator,
        "cagr_window_years": cagr_years,
        "thresholds": {
            "volume_median": round(med_vol, 2),
            "cagr_pct_median": round(med_cagr, 2)
        },
        "quadrant_classification": quadrants,
        "total_entities_analyzed": len(entity_metrics),
        "summary": (
            f"Matriz estratégica calculada para {len(entity_metrics)} entidades de {unit_name}. "
            f"Líderes estrella: {len(quadrants['Star Leaders (High Volume, High CAGR)'])} | "
            f"Estrellas emergentes: {len(quadrants['Emerging Stars (Moderate Volume, High CAGR)'])} | "
            f"Gigantes consolidados: {len(quadrants['Established Giants (High Volume, Low CAGR)'])}."
        )
    }

