import os
import re
import json
import duckdb
from pathlib import Path
from typing import Dict, List, Any, Optional
from shared.clickhouse import execute_safe_query

SNII_HISTORICO_PATH = Path("/home/sinapsisai/data/snii/snii_historico.parquet")
SNII_MATCHES_PATH = Path("/home/sinapsisai/data/snii_llm_verified_matches.json")
DUCKDB_ANALYTICS_PATH = Path(os.environ.get("DUCKDB_ANALYTICS_PATH", "/home/sinapsisai/data/analytics_cache.duckdb"))

NIVEL_LABELS = {
    "C": "Candidato a Investigador(a) Nacional",
    "1": "Investigador(a) Nacional Nivel I",
    "2": "Investigador(a) Nacional Nivel II",
    "3": "Investigador(a) Nacional Nivel III",
    "E": "Investigador(a) Nacional Emérito(a)",
}

LEVEL_RANK = {"C": 0, "1": 1, "2": 2, "3": 3, "E": 4}


KNOWN_CURATED_MATCHES: Dict[str, Dict[str, str]] = {
    "634": {
        "orcid": "https://orcid.org/0000-0003-2168-9073",
        "openalex_id": "https://openalex.org/A5060963552"
    }
}


def _get_verified_identifiers(cvu: Any) -> Dict[str, Optional[str]]:
    """Busca identificadores persistentes (ORCID, OpenAlex) por CVU en el archivo de matches verificados."""
    if not cvu:
        return {"orcid": None, "openalex_id": None}
    
    cvu_str = str(cvu).strip()
    if cvu_str in KNOWN_CURATED_MATCHES:
        return dict(KNOWN_CURATED_MATCHES[cvu_str])

    if not SNII_MATCHES_PATH.exists():
        return {"orcid": None, "openalex_id": None}
    try:
        con = duckdb.connect()
        # Query optimizada vía DuckDB sobre JSON
        q = f"""
            SELECT matched_orcid, matched_openalex_id
            FROM read_json('{SNII_MATCHES_PATH}')
            WHERE snii_cvu = '{cvu_str}'
            LIMIT 1
        """
        df = con.execute(q).df()
        con.close()
        if not df.empty:
            row = df.iloc[0]
            return {
                "orcid": str(row["matched_orcid"]) if pd_is_valid(row["matched_orcid"]) else None,
                "openalex_id": str(row["matched_openalex_id"]) if pd_is_valid(row["matched_openalex_id"]) else None
            }
    except Exception:
        pass
    return {"orcid": None, "openalex_id": None}


def _build_flexible_name_filter(name: str) -> str:
    """Construye un filtro flexible tokenizado para nombres hispanos y variantes de orden."""
    clean = re.sub(r"[^\w\s]", " ", name).strip()
    tokens = [t.replace("'", "''") for t in clean.split() if len(t) > 2]
    if not tokens:
        tokens = [t.replace("'", "''") for t in clean.split() if t]
    if not tokens:
        return f"nombre ILIKE '%{name.replace('\'', '\'\'')}%'"
    if len(tokens) <= 2:
        return " AND ".join([f"nombre ILIKE '%{t}%'" for t in tokens])
    all_and = " AND ".join([f"nombre ILIKE '%{t}%'" for t in tokens])
    pairs = [
        f"(nombre ILIKE '%{tokens[i]}%' AND nombre ILIKE '%{tokens[j]}%')"
        for i in range(len(tokens))
        for j in range(i + 1, len(tokens))
    ]
    return f"({all_and}) OR ({' OR '.join(pairs)})"


def resolve_snii_identity(
    fullname: str,
    institution: str = "",
    dependency: str = "",
    target_year: int = 2026
) -> Dict[str, Any]:
    """
    Resuelve la identidad oficial y desambigua investigadores en el Padrón Oficial SNII 2026
    (o año solicitado), vinculando CVU, nivel, área del conocimiento, vigencia, ORCID y OpenAlex ID.
    """
    clean_name = fullname.strip()
    if not clean_name:
        return {"status": "error", "message": "Se requiere el nombre del investigador."}

    if not SNII_HISTORICO_PATH.exists():
        return {"status": "error", "message": f"Archivo de padrón no encontrado: {SNII_HISTORICO_PATH}"}

    safe_name = clean_name.replace("'", "''")
    con = duckdb.connect()

    cvu_filter = f"CAST(cvu AS VARCHAR) = '{safe_name}'" if safe_name.isdigit() else "false"
    name_filter = _build_flexible_name_filter(clean_name)
    q_target = f"""
        SELECT year, cvu, nombre, nivel, area, disciplina, subdisciplina, especialidad,
               institucion, dependencia, subdependencia, entidad, pais, fecha_inicio, fecha_fin,
               snii_active_2025, snii_active_2026
        FROM '{SNII_HISTORICO_PATH}'
        WHERE ({name_filter} OR {cvu_filter})
          AND year = {target_year}
        LIMIT 5
    """
    df = con.execute(q_target).df()

    # Si no está en el año objetivo, buscar en todo el histórico para ver el último año activo
    was_in_target = True
    if df.empty:
        was_in_target = False
        q_latest = f"""
            SELECT year, cvu, nombre, nivel, area, disciplina, subdisciplina, especialidad,
                   institucion, dependencia, subdependencia, entidad, pais, fecha_inicio, fecha_fin,
                   snii_active_2025, snii_active_2026
            FROM '{SNII_HISTORICO_PATH}'
            WHERE ({name_filter} OR {cvu_filter})
            ORDER BY year DESC
            LIMIT 5
        """
        df = con.execute(q_latest).df()

    con.close()

    if df.empty:
        return {
            "status": "not_found",
            "query_input": {"fullname": fullname, "institution": institution, "target_year": target_year},
            "disambiguation_confidence": 0.0,
            "message": f"No se encontró a '{fullname}' en el Padrón SNII ({target_year} ni histórico 1984-2026)."
        }

    # Seleccionar la mejor coincidencia (filtrando por institución si se especifica)
    best_row = df.iloc[0]
    if institution:
        inst_matches = df[df["institucion"].str.contains(institution, case=False, na=False)]
        if not inst_matches.empty:
            best_row = inst_matches.iloc[0]

    cvu_val = str(best_row.get("cvu", ""))
    nivel_code = str(best_row.get("nivel", "")).strip()
    nivel_label = NIVEL_LABELS.get(nivel_code, f"Nivel {nivel_code}")
    active_2026 = bool(best_row.get("snii_active_2026", False)) or (best_row.get("year") == 2026)

    # Identificadores verificados (ORCID / OpenAlex)
    ext_ids = _get_verified_identifiers(cvu_val)

    # Obtener trayectoria condensada
    trajectory_meta = get_snii_historical_trajectory(cvu_val)

    active_msg = "Vigente en Padrón 2026." if active_2026 else f"Último registro activo en {best_row.get('year')}."
    return {
        "status": "success",
        "target_year": target_year,
        "active_in_target_year": was_in_target,
        "disambiguation_confidence": 0.98 if was_in_target else 0.85,
        "canonical_match": {
            "official_snii_name": str(best_row.get("nombre")),
            "cvu": cvu_val,
            "snii_level": nivel_label,
            "snii_level_code": nivel_code,
            "area_conocimiento": str(best_row.get("area", "N/A")),
            "disciplina": str(best_row.get("disciplina", "N/A")),
            "subdisciplina": str(best_row.get("subdisciplina", "N/A")),
            "especialidad": str(best_row.get("especialidad", "N/A")),
            "institution": str(best_row.get("institucion", "N/A")),
            "dependency": str(best_row.get("dependencia", "N/A")),
            "subdependency": str(best_row.get("subdependencia", "N/A")),
            "entidad": str(best_row.get("entidad", "N/A")),
            "vigencia": {
                "fecha_inicio": str(best_row.get("fecha_inicio", "")),
                "fecha_fin": str(best_row.get("fecha_fin", "")),
                "active_in_2026": active_2026
            },
            "orcid": ext_ids.get("orcid"),
            "openalex_author_id": ext_ids.get("openalex_id"),
            "historical_career": {
                "total_years_in_snii": trajectory_meta.get("career_summary", {}).get("total_years_active", 1),
                "first_registered_year": trajectory_meta.get("career_summary", {}).get("first_year"),
                "highest_level_reached": trajectory_meta.get("career_summary", {}).get("highest_level_label")
            }
        },
        "summary": (
            f"Investigador(a) '{best_row.get('nombre')}' (CVU {cvu_val}): "
            f"{nivel_label} en {best_row.get('area', '')} ({best_row.get('institucion', '')}). "
            f"{active_msg}"
        )
    }


def get_snii_historical_trajectory(name_or_cvu: str) -> Dict[str, Any]:
    """
    Recupera la trayectoria histórica completa (1984 - 2026) de un investigador en el SNII:
    Evolución anual de niveles (C, 1, 2, 3, E), cambios de adscripción institucional,
    promociones de nivel, áreas de dictaminación y permanencia total.
    """
    clean_term = str(name_or_cvu).strip()
    if not clean_term:
        return {"status": "error", "message": "Se requiere un nombre o CVU."}

    if not SNII_HISTORICO_PATH.exists():
        return {"status": "error", "message": f"Archivo de padrón no encontrado: {SNII_HISTORICO_PATH}"}

    safe_term = clean_term.replace("'", "''")
    con = duckdb.connect()

    cvu_filter = f"CAST(cvu AS VARCHAR) = '{safe_term}'" if safe_term.isdigit() else "false"
    name_filter = _build_flexible_name_filter(clean_term)
    q = f"""
        SELECT year, cvu, nombre, nivel, area, institucion, dependencia
        FROM '{SNII_HISTORICO_PATH}'
        WHERE ({cvu_filter} OR {name_filter})
        ORDER BY cvu, year ASC
    """
    df = con.execute(q).df()
    con.close()

    if df.empty:
        return {
            "status": "not_found",
            "search_term": clean_term,
            "message": f"No se encontró historial en el padrón 1984-2026 para '{clean_term}'."
        }

    # Si hay múltiples investigadores (homónimos), tomar el de mayor trayectoria o coincidencia exacta de CVU
    unique_cvus = df["cvu"].unique()
    if len(unique_cvus) > 1 and not clean_term.isdigit():
        # Tomar el CVU con más años registrados
        top_cvu = df["cvu"].value_counts().index[0]
        df = df[df["cvu"] == top_cvu]

    cvu_val = str(df["cvu"].iloc[0])
    official_name = str(df["nombre"].iloc[-1])

    timeline = []
    level_history = []
    institutions_seen = set()

    for _, row in df.iterrows():
        yr = int(row["year"])
        lvl = str(row["nivel"]).strip()
        inst = str(row["institucion"] or "N/A")
        dep = str(row["dependencia"] or "")
        area = str(row["area"] or "")

        institutions_seen.add(inst)
        level_history.append((yr, lvl))
        timeline.append({
            "year": yr,
            "nivel_code": lvl,
            "nivel_label": NIVEL_LABELS.get(lvl, f"Nivel {lvl}"),
            "area": area,
            "institution": inst,
            "dependency": dep
        })

    # Analizar transiciones de nivel
    transitions = []
    prev_lvl = None
    for yr, lvl in level_history:
        if prev_lvl is not None and lvl != prev_lvl:
            p_rank = LEVEL_RANK.get(prev_lvl, 0)
            c_rank = LEVEL_RANK.get(lvl, 0)
            t_type = "Promoción" if c_rank > p_rank else "Reclasificación"
            transitions.append({
                "year": yr,
                "transition": f"{NIVEL_LABELS.get(prev_lvl, prev_lvl)} -> {NIVEL_LABELS.get(lvl, lvl)}",
                "type": t_type
            })
        prev_lvl = lvl

    years_active = len(df)
    first_year = int(df["year"].min())
    latest_year = int(df["year"].max())
    highest_level_code = max(df["nivel"].unique(), key=lambda x: LEVEL_RANK.get(str(x).strip(), -1))
    current_2026_status = "Inactivo en 2026"
    if latest_year == 2026:
        current_lvl = str(df[df["year"] == 2026]["nivel"].iloc[0]).strip()
        current_2026_status = NIVEL_LABELS.get(current_lvl, f"Nivel {current_lvl}")

    ext_ids = _get_verified_identifiers(cvu_val)

    return {
        "status": "success",
        "search_term": clean_term,
        "official_name": official_name,
        "cvu": cvu_val,
        "orcid": ext_ids.get("orcid"),
        "openalex_id": ext_ids.get("openalex_id"),
        "career_summary": {
            "first_year": first_year,
            "latest_year": latest_year,
            "career_span_years": latest_year - first_year + 1,
            "total_years_active": years_active,
            "highest_level_code": highest_level_code,
            "highest_level_label": NIVEL_LABELS.get(highest_level_code, highest_level_code),
            "status_in_2026": current_2026_status,
            "institutions_count": len(institutions_seen),
            "institutions_list": list(institutions_seen),
            "transitions_count": len(transitions)
        },
        "level_transitions": transitions,
        "yearly_timeline": timeline,
        "summary": (
            f"Trayectoria de '{official_name}' (CVU {cvu_val}): {years_active} años en el SNII "
            f"({first_year}-{latest_year}), nivel máximo alcanzado: {NIVEL_LABELS.get(highest_level_code, highest_level_code)}. "
            f"Estado 2026: {current_2026_status}."
        )
    }


def query_snii_census_overview(
    year: int = 2026,
    institution_filter: str = "",
    area_filter: str = ""
) -> Dict[str, Any]:
    """
    Genera el censo analítico y estadísticas oficiales del Padrón SNII para un año específico (1984-2026):
    Distribución por nivel (C, 1, 2, 3, Emérito), áreas del conocimiento e instituciones líderes.
    """
    if not SNII_HISTORICO_PATH.exists():
        return {"status": "error", "message": f"Archivo de padrón no encontrado: {SNII_HISTORICO_PATH}"}

    con = duckdb.connect()

    where_clauses = [f"year = {year}"]
    if institution_filter:
        safe_inst = institution_filter.replace("'", "''")
        where_clauses.append(f"institucion ILIKE '%{safe_inst}%'")
    if area_filter:
        safe_area = area_filter.replace("'", "''")
        where_clauses.append(f"area ILIKE '%{safe_area}%'")

    where_sql = " AND ".join(where_clauses)

    # 1. Total y desglose por nivel
    q_level = f"""
        SELECT nivel, count(*) AS count
        FROM '{SNII_HISTORICO_PATH}'
        WHERE {where_sql}
        GROUP BY nivel
        ORDER BY count DESC
    """
    df_level = con.execute(q_level).df()
    total_researchers = int(df_level["count"].sum()) if not df_level.empty else 0

    level_breakdown = {}
    for _, r in df_level.iterrows():
        lvl = str(r["nivel"]).strip()
        cnt = int(r["count"])
        pct = round((cnt / total_researchers) * 100.0, 2) if total_researchers > 0 else 0.0
        level_breakdown[NIVEL_LABELS.get(lvl, f"Nivel {lvl}")] = {
            "code": lvl,
            "count": cnt,
            "share_pct": pct
        }

    # 2. Desglose por Área
    q_area = f"""
        SELECT area, count(*) AS count
        FROM '{SNII_HISTORICO_PATH}'
        WHERE {where_sql} AND area != ''
        GROUP BY area
        ORDER BY count DESC
        LIMIT 10
    """
    df_area = con.execute(q_area).df()
    areas_breakdown = [
        {"area": str(r["area"]), "count": int(r["count"]), "share_pct": round((int(r["count"]) / max(total_researchers, 1)) * 100.0, 2)}
        for _, r in df_area.iterrows()
    ]

    # 3. Top Instituciones
    q_inst = f"""
        SELECT institucion, count(*) AS count
        FROM '{SNII_HISTORICO_PATH}'
        WHERE {where_sql} AND institucion != ''
        GROUP BY institucion
        ORDER BY count DESC
        LIMIT 10
    """
    df_inst = con.execute(q_inst).df()
    top_institutions = [
        {"institution": str(r["institucion"]), "count": int(r["count"]), "share_pct": round((int(r["count"]) / max(total_researchers, 1)) * 100.0, 2)}
        for _, r in df_inst.iterrows()
    ]

    con.close()

    return {
        "status": "success",
        "year": year,
        "filters_applied": {
            "institution": institution_filter or "Todas",
            "area": area_filter or "Todas"
        },
        "total_accredited_researchers": total_researchers,
        "level_distribution": level_breakdown,
        "areas_distribution": areas_breakdown,
        "top_institutions": top_institutions,
        "summary": (
            f"Padrón Oficial SNII {year}: {total_researchers:,} investigadoras e investigadores acreditados. "
            f"Nivel I: {level_breakdown.get(NIVEL_LABELS['1'], {}).get('count', 0):,} ({level_breakdown.get(NIVEL_LABELS['1'], {}).get('share_pct', 0)}%), "
            f"Candidatos: {level_breakdown.get(NIVEL_LABELS['C'], {}).get('count', 0):,} ({level_breakdown.get(NIVEL_LABELS['C'], {}).get('share_pct', 0)}%), "
            f"Nivel II: {level_breakdown.get(NIVEL_LABELS['2'], {}).get('count', 0):,}, "
            f"Nivel III: {level_breakdown.get(NIVEL_LABELS['3'], {}).get('count', 0):,}, "
            f"Eméritos: {level_breakdown.get(NIVEL_LABELS['E'], {}).get('count', 0):,}."
        )
    }


def get_researcher_profile(
    name_fragment: str,
    target_year: int = 2026
) -> Dict[str, Any]:
    """
    Recupera el perfil cienciométrico integral de un investigador mexicano o SNII:
    Estatus oficial 2026, trayectoria histórica, métricas DuckDB (citas, FWCI, H-index, APC, Gini)
    y metadatos canónicos de ClickHouse.
    """
    clean_name = name_fragment.strip()
    if not clean_name:
        return {"status": "error", "message": "Se requiere un nombre de investigador."}

    # 1. Resolver en el Padrón SNII 2026 / Histórico
    snii_resolution = resolve_snii_identity(clean_name, target_year=target_year)
    snii_match = snii_resolution.get("canonical_match", {})
    cvu = snii_match.get("cvu")
    orcid = snii_match.get("orcid")

    # 2. Consultar métricas en DuckDB (investigador_total)
    duckdb_metrics = None
    if DUCKDB_ANALYTICS_PATH.exists():
        try:
            con = duckdb.connect(str(DUCKDB_ANALYTICS_PATH), read_only=True)
            sql = """
                SELECT academic_name, is_snii, institutions, entities, num_documents, citations,
                       fwci_avg, pct_top_10, h_index, pct_open_access, apc_paid_usd,
                       pct_international, gini_topics, top_topic, orcid
                FROM investigador_total
                WHERE academic_name ILIKE ? OR db_academic_name ILIKE ?
                ORDER BY num_documents DESC
                LIMIT 1
            """
            pattern = f"%{clean_name}%"
            df = con.execute(sql, [pattern, pattern]).df()
            con.close()
            if not df.empty:
                r = df.iloc[0]
                duckdb_metrics = {
                    "total_documents": int(r.get("num_documents", 0) or 0),
                    "total_citations": int(r.get("citations", 0) or 0),
                    "fwci_mean": round(float(r.get("fwci_avg", 0.0) or 0.0), 3),
                    "h_index": int(r.get("h_index", 0) or 0),
                    "top_10_percent_share": round(float(r.get("pct_top_10", 0.0) or 0.0), 2),
                    "open_access_share": round(float(r.get("pct_open_access", 0.0) or 0.0), 2),
                    "apc_paid_usd": round(float(r.get("apc_paid_usd", 0.0) or 0.0), 2),
                    "international_collab_share": round(float(r.get("pct_international", 0.0) or 0.0), 2),
                    "gini_topics": round(float(r.get("gini_topics", 0.0) or 0.0), 3),
                    "top_topic": str(r.get("top_topic", "N/A"))
                }
                if not orcid and pd_is_valid(r.get("orcid")):
                    orcid = str(r["orcid"])
        except Exception:
            pass

    # 3. Traer datos complementarios de ClickHouse si no hay DuckDB
    if not duckdb_metrics:
        safe_q = clean_name.replace("'", "''")
        ch_sql = f"""
            SELECT id, display_name, orcid, raw_data
            FROM rag.authors_seed_mexico
            WHERE display_name ILIKE '%{safe_q}%'
            LIMIT 1
        """
        ch_res = execute_safe_query(ch_sql)
        ch_rows = ch_res.get("data", [])
        if ch_rows:
            r = ch_rows[0]
            raw_meta = {}
            if r.get("raw_data"):
                try:
                    raw_meta = json.loads(r["raw_data"])
                except Exception:
                    pass
            stats = raw_meta.get("summary_stats", {})
            duckdb_metrics = {
                "total_documents": raw_meta.get("works_count", 0),
                "total_citations": raw_meta.get("cited_by_count", 0),
                "fwci_mean": 1.0,
                "h_index": stats.get("h_index", 0),
                "top_10_percent_share": 0.0,
                "open_access_share": 0.0,
                "apc_paid_usd": 0.0,
                "international_collab_share": 0.0,
                "gini_topics": 0.0,
                "top_topic": (raw_meta.get("topics", [{}])[0].get("display_name", "N/A")) if raw_meta.get("topics") else "N/A"
            }
            if not orcid and (r.get("orcid") or raw_meta.get("orcid")):
                orcid = r.get("orcid") or raw_meta.get("orcid")

    # 4. Trayectoria histórica
    trajectory = get_snii_historical_trajectory(cvu if cvu else clean_name)

    return {
        "status": "success",
        "search_term": clean_name,
        "official_name": snii_match.get("official_snii_name") or clean_name.title(),
        "cvu": cvu,
        "orcid": orcid,
        "openalex_id": snii_match.get("openalex_author_id"),
        "snii_2026_status": {
            "level": snii_match.get("snii_level", "No acreditado en 2026"),
            "level_code": snii_match.get("snii_level_code"),
            "area": snii_match.get("area_conocimiento", "N/A"),
            "institution": snii_match.get("institution", "N/A"),
            "dependency": snii_match.get("dependency", "N/A"),
            "active_2026": snii_match.get("vigencia", {}).get("active_in_2026", False)
        },
        "snii_historical_career": trajectory.get("career_summary", {}),
        "metrics": duckdb_metrics or {
            "total_documents": 0, "total_citations": 0, "fwci_mean": 0.0, "h_index": 0
        },
        "summary": (
            f"Perfil de {snii_match.get('official_snii_name', clean_name)}: "
            f"SNII 2026: {snii_match.get('snii_level', 'N/A')} ({snii_match.get('institution', 'N/A')}). "
            f"Trayectoria: {trajectory.get('career_summary', {}).get('total_years_active', 0)} años en el SNII. "
            f"Impacto: {duckdb_metrics.get('total_citations', 0) if duckdb_metrics else 0:,} citas, "
            f"H-index {duckdb_metrics.get('h_index', 0) if duckdb_metrics else 0}, "
            f"FWCI medio {duckdb_metrics.get('fwci_mean', 0.0) if duckdb_metrics else 0.0}."
        )
    }


def pd_is_valid(val: Any) -> bool:
    """Verifica si un valor no es None, nan ni vacío."""
    if val is None:
        return False
    s = str(val).strip().lower()
    return s not in ["", "none", "nan", "<na>", "null"]
