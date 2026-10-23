import os
import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

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
    from tlachia_parser import (
        build_tlachia_inventory,
        parse_single_unit_from_session,
        read_tlachia_file,
        clean_val
    )
    HAS_TLACHIA_PARSER = True
except Exception:
    HAS_TLACHIA_PARSER = False


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
    if HAS_TLACHIA_PARSER:
        res = build_tlachia_inventory(session_dir_or_zip)
        if res.get("success"):
            s_dir = res.get("session_dir")
            inv_p = os.path.join(s_dir, "inventory.json")
            if os.path.exists(inv_p):
                with open(inv_p, 'r', encoding='utf-8') as f:
                    inv_data = json.load(f)
                return s_dir, inv_data
            return s_dir, res

    return None, None


def inspect_tlachia_package(package_path: str) -> Dict[str, Any]:
    """
    Inspecciona un archivo ZIP o directorio exportado desde TlachIA Metrics (openalex_indicators_engine).
    Extrae el inventario de entidades analíticas disponibles (Locations, Organizations, Publication Sources, etc.),
    los metadatos del corpus y la ubicación del archivo de obras/documentos para redes bibliométricas.
    """
    if not os.path.exists(package_path):
        return {"status": "error", "message": f"No se encontró el paquete en la ruta: {package_path}"}

    session_dir, inv_data = _resolve_session(package_path)
    if not session_dir or not inv_data:
        return {
            "status": "error",
            "message": "No se pudo interpretar el archivo como paquete canónico de TlachIA Metrics."
        }

    units_dict = inv_data.get("units", {})
    available_units = sorted(list(units_dict.keys()))

    # Información de las obras/documentos (works file)
    works_info = inv_data.get("openalex_data") or {}
    works_file_path = inv_data.get("works_file_path")

    # Muestreo rápido de indicadores disponibles en Locations u Organizations
    sample_indicators = []
    if HAS_TLACHIA_PARSER and available_units:
        first_unit = "Locations" if "Locations" in available_units else available_units[0]
        parsed_unit = parse_single_unit_from_session(session_dir, first_unit)
        if parsed_unit.get("success"):
            sample_indicators = parsed_unit.get("unit", {}).get("indicators", [])

    return {
        "status": "success",
        "package_path": package_path,
        "session_dir": session_dir,
        "schema_detected": "TlachIA Metrics Canonical Multi-Entity Package",
        "available_units": available_units,
        "manifest": inv_data.get("manifest"),
        "works_file": {
            "has_works": bool(works_file_path),
            "file_path": works_file_path,
            "document_count": works_info.get("document_count", 0),
            "file_name": os.path.basename(works_file_path) if works_file_path else None
        },
        "sample_indicators_count": len(sample_indicators),
        "sample_indicators": sample_indicators[:12],
        "summary": (
            f"Paquete TlachIA Metrics inspeccionado exitosamente. "
            f"Contiene {len(available_units)} unidades analíticas ({', '.join(available_units)}) "
            f"y un archivo de metadatos de {works_info.get('document_count', 0)} documentos para redes bibliométricas."
        )
    }


def get_tlachia_unit_matrix(
    session_dir_or_zip: str,
    unit_name: str = "Locations",
    period_mode: str = "Whole",
    selected_indicators: Optional[List[str]] = None,
    limit_top_n: int = 100,
    min_documents: float = 0.0
) -> Dict[str, Any]:
    """
    Extrae la matriz multidimensional limpia [N x D] de una unidad analítica específica
    (ej. Locations / países, Organizations / universidades, Publication Sources / revistas)
    lista para ingresar al dimensionamiento espectral (suggest_grid_size) y entrenamiento (train_som).
    """
    session_dir, inv_data = _resolve_session(session_dir_or_zip)
    if not session_dir:
        return {"status": "error", "message": f"Sesión inválida o paquete no encontrado: {session_dir_or_zip}"}

    if not HAS_TLACHIA_PARSER:
        return {"status": "error", "message": "Motor tlachia_parser no disponible en el entorno."}

    parsed = parse_single_unit_from_session(session_dir, unit_name)
    if not parsed.get("success"):
        return {"status": "error", "message": f"Error al parsear unidad '{unit_name}': {parsed.get('error')}"}

    unit_data = parsed.get("unit", {})
    available_indicators = unit_data.get("indicators", [])

    # Seleccionar perfil según el modo temporal
    if period_mode.lower() in ("5years", "recent"):
        raw_rows = unit_data.get("profile_5years") or unit_data.get("profile") or []
    else:
        raw_rows = unit_data.get("profile") or []

    if not raw_rows:
        return {"status": "error", "message": f"No se encontraron registros de perfil para la unidad {unit_name}."}

    # Filtrar por producción mínima de documentos si aplica
    filtered_rows = []
    for r in raw_rows:
        doc_val = float(clean_val(r.get("Documents", r.get("Total Documents", 0))))
        if doc_val >= min_documents:
            filtered_rows.append(r)

    # Limitar a top N
    filtered_rows = filtered_rows[:limit_top_n]
    if not filtered_rows:
        return {"status": "error", "message": f"Ninguna entidad cumplió el filtro de min_documents={min_documents}."}

    # Determinar indicadores a extraer
    if selected_indicators:
        final_indicators = [ind for ind in selected_indicators if any(ind in r for r in filtered_rows)]
    else:
        # Batería multidimensional recomendada por som-methodological-expert si no se especifican indicadores
        default_candidates = [
            'Field-Weighted Citation Impact (FWCI)',
            'Citation Impact',
            '% Documents in Top 10%',
            '% Documents in Top 1%',
            'Average Percentile',
            '% All Open Access Documents',
            '% Free to Read / Diamond Documents',
            '% International Collaborations',
            '% Industry Collaborations',
            'Share'
        ]
        final_indicators = [c for c in default_candidates if c in available_indicators]
        if not final_indicators:
            # Tomar las primeras columnas numéricas que no sean identificadores
            final_indicators = [c for c in available_indicators if c.lower() not in ('rank', 'id')][:8]

    # Construir etiquetas y matriz numérica [N x D]
    labels = []
    matrix_data = []

    for r in filtered_rows:
        ent_name = str(r.get("entity", "")).strip()
        if not ent_name:
            continue
        labels.append(ent_name)
        vec = []
        for ind in final_indicators:
            val = r.get(ind, 0.0)
            vec.append(float(clean_val(val)))
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
            f"Matriz de {len(labels)} entidades de '{unit_name}' ({period_mode}) "
            f"con {len(final_indicators)} indicadores cienciométricos extraída con éxito. "
            f"Estructura lista para suggest_grid_size y train_som."
        )
    }


def get_tlachia_temporal_evolution(
    session_dir_or_zip: str,
    unit_name: str = "Locations",
    entities: Optional[List[str]] = None,
    indicators: Optional[List[str]] = None,
    smoothing: str = "ecma3"
) -> Dict[str, Any]:
    """
    Extrae series de tiempo multivariadas y trayectorias anuales para las entidades de interés
    con suavizado exponencial ponderado (ECMA-3, ECMA-5 o raw), listo para som-trajectory-mapping
    (máximo 5 entidades recomendadas en visualización).
    """
    session_dir, inv_data = _resolve_session(session_dir_or_zip)
    if not session_dir or not HAS_TLACHIA_PARSER:
        return {"status": "error", "message": "Sesión inválida o parser no disponible."}

    parsed = parse_single_unit_from_session(session_dir, unit_name)
    if not parsed.get("success"):
        return {"status": "error", "message": f"Error parseando unidad {unit_name}."}

    unit_data = parsed.get("unit", {})
    ts_dict = unit_data.get("time_series", {})

    if not ts_dict:
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
                "values": [round(float(v), 4) for v in vals]
            })
            if filter_entities and len(filtered_series) >= len(filter_entities):
                break
        temporal_results[ind] = filtered_series

    return {
        "status": "success",
        "unit_name": unit_name,
        "smoothing_applied": smoothing,
        "indicators": list(temporal_results.keys()),
        "time_series": temporal_results,
        "summary": (
            f"Series temporales de '{unit_name}' extraídas con suavizado {smoothing} "
            f"para {len(chosen_indicators)} indicadores cienciométricos."
        )
    }


def get_tlachia_works_metadata(session_dir_or_zip: str) -> Dict[str, Any]:
    """
    Localiza y valida el archivo canónico de metadatos de documentos científicos (CSV / Parquet de OpenAlex)
    contenido dentro del paquete de TlachIA Metrics, extrayendo columnas clave para su posterior
    uso en análisis de redes bibliométricas (coautoría, acoplamiento bibliográfico y coocurrencia).
    """
    session_dir, inv_data = _resolve_session(session_dir_or_zip)
    if not session_dir or not inv_data:
        return {"status": "error", "message": "No se pudo acceder a la sesión de TlachIA Metrics."}

    works_file_path = inv_data.get("works_file_path")
    if not works_file_path or not os.path.exists(works_file_path):
        return {
            "status": "error",
            "message": "El paquete no incluye un archivo de obras/documentos completos (openalex_works.csv)."
        }

    # Inspeccionar columnas y formato rápidamente
    columns = []
    doc_count = inv_data.get("openalex_data", {}).get("document_count", 0)

    try:
        import pandas as pd
        if works_file_path.lower().endswith('.parquet'):
            df_sample = pd.read_parquet(works_file_path)
            columns = list(df_sample.columns)
            doc_count = len(df_sample)
        else:
            df_sample = pd.read_csv(works_file_path, nrows=5)
            columns = list(df_sample.columns)
    except Exception as e:
        return {"status": "error", "message": f"Error leyendo encabezado de obras: {e}"}

    cols_lower = [c.lower() for c in columns]

    has_authors = any(c in cols_lower for c in ['author_ids', 'author_names', 'authorships', 'authors'])
    has_institutions = any(c in cols_lower for c in ['institution_ids', 'institution_names', 'institution_rors'])
    has_references = any(c in cols_lower for c in ['referenced_works', 'references', 'citations'])
    has_keywords = any(c in cols_lower for c in ['keywords', 'concepts', 'mesh', 'topics'])
    has_countries = any(c in cols_lower for c in ['country_codes', 'country_code', 'countries'])

    return {
        "status": "success",
        "works_file_path": works_file_path,
        "file_name": os.path.basename(works_file_path),
        "document_count": doc_count,
        "columns_count": len(columns),
        "columns": columns,
        "bibliometric_capabilities": {
            "coauthorship": has_authors,
            "institution_collaboration": has_institutions,
            "international_collaboration": has_countries,
            "bibliographic_coupling": has_references,
            "keyword_cooccurrence": has_keywords
        },
        "ready_for_biblio_network": has_authors or has_references or has_keywords,
        "summary": (
            f"Archivo canónico de metadatos de documentos localizado con éxito: '{os.path.basename(works_file_path)}' "
            f"con {doc_count:,} registros. Dispone de campos para coautoría ({has_authors}), "
            f"acoplamiento bibliográfico ({has_references}) y coocurrencia temática ({has_keywords})."
        )
    }
