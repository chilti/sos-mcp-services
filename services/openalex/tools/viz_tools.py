"""
OpenAlex México Visualization Tools & Artifact Engine
Módulo de generación de artefactos visuales interactivos (HTML con Plotly.js, Redes PyVis y Tarjetas PNG)
para el servicio MCP sos_openalex.

Entorno Python: /home/ambientesPy/revistaslatam
Regla estricta: CERO JOINs en consultas ClickHouse.
"""

import os
import sys
import json
import time
import re
import datetime
from typing import Dict, List, Any, Optional, Union

try:
    import plotly.graph_objects as go
    import plotly.express as px
    import plotly.io as pio
    from plotly.subplots import make_subplots
except ImportError:
    go = None
    px = None
    pio = None
    make_subplots = None

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    from pyvis.network import Network
except ImportError:
    Network = None

from shared.clickhouse import execute_safe_query, sanitize_no_joins
from services.openalex.tools.mexico_tools import (
    openalex_aggregate_mexico,
    openalex_top_entities,
    openalex_search_works,
    normalize_author_ids,
    build_authors_condition,
)

# Paletas cienciométricas oficiales
OA_COLORS = {
    "diamond": "#00A86B",  # Verde esmeralda (Diamante / No comercial)
    "gold": "#E39918",     # Oro / Amarillo dorado (APC)
    "hybrid": "#3B82F6",   # Azul comercial
    "bronze": "#CD7F32",   # Bronce libre
    "green": "#10B981",    # Verde repositorio
    "closed": "#6B7280"    # Gris cerrado
}

THEME_BG = "#0B0F19"
THEME_CARD = "#111827"
THEME_TEXT = "#F9FAFB"
THEME_ACCENT = "#38BDF8"
THEME_MUTED = "#94A3B8"

SDG_INFO = {
    1: {"name": "Fin de la Pobreza", "color": "#E5243B"},
    2: {"name": "Hambre Cero", "color": "#DDA63A"},
    3: {"name": "Salud y Bienestar", "color": "#4C9F38"},
    4: {"name": "Educación de Calidad", "color": "#C5192D"},
    5: {"name": "Igualdad de Género", "color": "#FF3A21"},
    6: {"name": "Agua Limpia y Saneamiento", "color": "#26BDE2"},
    7: {"name": "Energía Asequible y No Contaminante", "color": "#FCC30B"},
    8: {"name": "Trabajo Decente y Crecimiento Económico", "color": "#A21942"},
    9: {"name": "Industria, Innovación e Infraestructura", "color": "#FD6925"},
    10: {"name": "Reducción de las Desigualdades", "color": "#DD1367"},
    11: {"name": "Ciudades y Comunidades Sostenibles", "color": "#FD9D24"},
    12: {"name": "Producción y Consumo Responsables", "color": "#BF8B2E"},
    13: {"name": "Acción por el Clima", "color": "#3F7E44"},
    14: {"name": "Vida Submarina", "color": "#0A97D9"},
    15: {"name": "Vida de Ecosistemas Terrestres", "color": "#56C02B"},
    16: {"name": "Paz, Justicia e Instituciones Sólidas", "color": "#00689D"},
    17: {"name": "Alianzas para Lograr los Objetivos", "color": "#19486A"}
}

REGIONAL_BLOCKS = {
    "Norteamérica": ["US", "CA"],
    "Iberoamérica": ["ES", "BR", "AR", "CO", "CL", "PE", "CU", "UY", "CR", "EC", "VE", "PA", "GT", "DO"],
    "Unión Europea": ["FR", "DE", "GB", "IT", "NL", "CH", "SE", "BE", "AT", "PT", "PL", "DK", "FI", "IE", "NO"],
    "Asia-Pacífico": ["CN", "JP", "KR", "AU", "IN", "SG", "TW", "NZ", "MY"],
}

COUNTRY_NAMES = {
    "US": "Estados Unidos", "ES": "España", "BR": "Brasil", "FR": "Francia",
    "DE": "Alemania", "GB": "Reino Unido", "IT": "Italia", "CO": "Colombia",
    "CN": "China", "CA": "Canadá", "AR": "Argentina", "CL": "Chile",
    "JP": "Japón", "AU": "Australia", "NL": "Países Bajos", "CH": "Suiza",
    "IN": "India", "BE": "Bélgica", "PT": "Portugal", "CU": "Cuba",
    "PE": "Perú", "KR": "Corea del Sur", "SE": "Suecia", "AT": "Austria"
}


def _get_embedded_styles() -> str:
    """CSS limpio, moderno y responsivo para el artefacto HTML."""
    return """
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0b0f19; color: #f3f4f6; margin: 0; padding: 0; }
    .header-card { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 1px solid #334155; border-radius: 12px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5); }
    .card { background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3); }
    .tag { display: inline-block; background-color: #0284c7; color: #ffffff; font-size: 0.75rem; font-weight: 700; padding: 4px 8px; border-radius: 6px; text-transform: uppercase; letter-spacing: 0.05em; }
    .kpi-mini { background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 12px; text-align: center; }
    .kpi-label { display: block; font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }
    .kpi-val { display: block; font-size: 1.5rem; font-weight: 900; color: #38bdf8; margin-top: 4px; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; text-align: left; }
    .data-table th { background-color: #1f2937; color: #9ca3af; font-weight: 600; padding: 12px; border-bottom: 2px solid #374151; }
    .data-table td { padding: 12px; border-bottom: 1px solid #1f2937; }
    .data-table tr:hover { background-color: #1e293b; }
    .badge { display: inline-block; font-size: 0.75rem; font-weight: 600; padding: 2px 6px; border-radius: 4px; }
    .badge-mx { background-color: #065f46; color: #6ee7b7; border: 1px solid #047857; }
    .badge-ext { background-color: #374151; color: #9ca3af; border: 1px solid #4b5563; }
    .badge-sim { background-color: #1e1b4b; color: #a5b4fc; border: 1px solid #4338ca; }
    
    .sdg-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 14px; padding: 10px 0; margin-bottom: 12px; }
    .sdg-card { position: relative; aspect-ratio: 1 / 1; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4); transition: transform 0.2s, box-shadow 0.2s; background-color: #1e293b; }
    .sdg-card:hover { transform: translateY(-4px) scale(1.02); z-index: 5; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.6); }
    .sdg-img { width: 100%; height: 100%; object-fit: cover; display: block; }
    .sdg-fallback { width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #fff; padding: 6px; box-sizing: border-box; text-align: center; }
    .sdg-fallback-num { font-size: 1.8rem; font-weight: 900; }
    .sdg-fallback-name { font-size: 0.7rem; line-height: 1.1; margin-top: 4px; font-weight: 600; }
    .sdg-overlay { position: absolute; bottom: 0; left: 0; right: 0; background: rgba(11, 15, 25, 0.88); color: #fff; padding: 6px 4px; text-align: center; line-height: 1.2; backdrop-filter: blur(2px); border-top: 1px solid rgba(255, 255, 255, 0.1); }
    .sdg-perc { font-size: 1rem; font-weight: 800; display: block; color: #38bdf8; }
    .sdg-count { font-size: 0.7rem; color: #94a3b8; display: block; margin-top: 1px; }
    .sdg-inactive { filter: grayscale(90%) opacity(0.35); }
    .sdg-inactive:hover { filter: grayscale(0%) opacity(1); }
    .sdg-badge-num { display: inline-flex; align-items: center; justify-content: center; width: 26px; height: 26px; border-radius: 50%; color: #fff; font-weight: 800; font-size: 0.75rem; }
    """


def _load_data(data_input: Any) -> Dict[str, Any]:
    """Carga y normaliza los datos provistos en memoria o archivo JSON."""
    if data_input is None:
        return {}
    if isinstance(data_input, dict):
        return data_input
    if isinstance(data_input, list):
        return {"results": data_input}
    if isinstance(data_input, str):
        if os.path.isfile(data_input):
            with open(data_input, "r", encoding="utf-8") as f:
                return json.load(f)
        try:
            return json.loads(data_input)
        except Exception:
            return {"query": data_input}
    return {}


def _resolve_output_paths(output_dir: str, prefix: str) -> tuple[str, str]:
    """Resuelve rutas absolutas seguras para HTML y PNG."""
    abs_dir = os.path.abspath(output_dir or "./reports")
    os.makedirs(abs_dir, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = os.path.join(abs_dir, f"{prefix}_{ts}.html")
    png_path = os.path.join(abs_dir, f"{prefix}_{ts}.png")
    return html_path, png_path


REPORTS_BASE_URL = os.getenv("REPORTS_BASE_URL", "https://dinamica1.fciencias.unam.mx/reports").rstrip("/")
LIBRECHAT_IFRAME_MODE = os.getenv("LIBRECHAT_IFRAME_MODE", "false").lower() in ("true", "1", "yes")


def _read_file_safe(path: str) -> str:
    """Lee el contenido completo de un archivo con manejo seguro de excepciones."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def _build_artifact_iframe_html(report_url: str, title: str) -> str:
    """
    Genera un contenedor ultraligero con iframe para clientes restringidos (ej. LibreChat con modelos pequeños).
    Se activa únicamente si LIBRECHAT_IFRAME_MODE=true en .env.
    """
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        html, body {{ margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background: #0B0F19; font-family: 'Inter', -apple-system, sans-serif; }}
        .topbar {{ height: 38px; background: #111827; border-bottom: 1px solid rgba(255,255,255,0.08); display: flex; align-items: center; justify-content: space-between; padding: 0 12px; box-sizing: border-box; }}
        .title {{ color: #F9FAFB; font-size: 12px; font-weight: 600; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; }}
        .btn {{ color: #38bdf8; text-decoration: none; font-size: 11px; font-weight: 600; padding: 2px 8px; border: 1px solid rgba(56,189,248,0.3); border-radius: 4px; transition: all 0.15s; display: inline-flex; align-items: center; gap: 4px; }}
        .btn:hover {{ background: rgba(56,189,248,0.1); border-color: #38bdf8; }}
        iframe {{ width: 100%; height: calc(100% - 38px); border: none; }}
    </style>
</head>
<body>
    <div class="topbar">
        <span class="title">📊 {title}</span>
        <a id="report-btn" class="btn" href="{report_url}" target="_blank" rel="noopener noreferrer">Abrir en pestaña completa ↗</a>
    </div>
    <iframe id="report-frame" src="{report_url}" allow="fullscreen" loading="eager" title="{title}"></iframe>
</body>
</html>"""


def _build_viz_result(
    chart_type: str,
    title: str,
    html_path: str,
    png_path: str,
    summary_kpis: Dict[str, Any],
    message: str = ""
) -> Dict[str, Any]:
    """
    Empaqueta la respuesta cienciométrica estandarizada conforme a la Tríada de Artefactos:
    1. summary_kpis: Métricas cuantitativas estructuradas para el razonamiento e interpretación del LLM.
    2. artifacts: Rutas absolutas locales al HTML autónomo interactivo y la tarjeta PNG estática.
    3. html_content: Código HTML autónomo y portable (sin depender de servidores web remotos ni iframes).
    4. public_share_url / report_url: Enlace web opcional para compartir externamente si hay servidor activo.
    """
    abs_html = os.path.abspath(html_path).replace("\\", "/")
    abs_png = os.path.abspath(png_path).replace("\\", "/") if png_path else ""
    filename = os.path.basename(html_path)
    file_uri = f"file:///{abs_html}"

    report_url = f"{REPORTS_BASE_URL}/{filename}" if REPORTS_BASE_URL else None
    standalone_html = _read_file_safe(html_path)

    if LIBRECHAT_IFRAME_MODE and report_url:
        delivered_html = _build_artifact_iframe_html(report_url, title)
    else:
        delivered_html = standalone_html

    embed_snippet = f'<agent-embed src="{file_uri}" title="{title}"></agent-embed>'
    msg = message or f"{title} generado en {html_path}"
    if report_url and report_url not in msg:
        msg = f"{msg}. Enlace de compartición: {report_url}"

    return {
        "status": "success",
        "chart_type": chart_type,
        "title": title,

        # NIVEL 1: METADATOS Y KPIS (Para el LLM)
        "summary_kpis": summary_kpis,

        # NIVEL 2: ARTEFACTOS LOCALES AUTÓNOMOS (La Tríada)
        "artifacts": {
            "html_path": abs_html,
            "png_path": abs_png,
            "file_uri": file_uri,
            "embed_snippet": embed_snippet
        },

        # NIVEL 3: CONTENIDO VISUAL AUTÓNOMO Y PORTABLE
        "html_path": abs_html,
        "png_path": abs_png,
        "html_content": delivered_html,

        # CANAL SECUNDARIO: Compartición Web Remota (Opcional)
        "public_share_url": report_url,
        "report_url": report_url,
        "message": msg
    }


PLOTLY_CDN_URL = "https://cdn.plot.ly/plotly-2.35.2.min.js"


def _compact_plotly_html(fig, div_id: str = "plot", default_height: int = 480) -> str:
    """
    Serializa una figura Plotly como bloque HTML COMPACTO y autosuficiente.

    Motivo: en LibreChat el LLM re-transcribe el `html_content` dentro de un artefacto.
    `pio.to_html` incrusta el template completo de Plotly (~10 KB de JSON), un id UUID,
    el atributo SRI y JSON indentado; el modelo lo trunca/altera y el gráfico no se dibuja.
    Aquí se elimina el template (aplicando sus colores esenciales de forma explícita),
    se emite JSON sin espacios y se carga Plotly 2.35.2 con una sola etiqueta <script>.
    """
    from plotly.utils import PlotlyJSONEncoder

    f = go.Figure(fig)  # copia: no mutar la figura original
    f.update_layout(template="none")
    if f.layout.font.color is None:
        f.update_layout(font=dict(color="#f2f5fa"))
    f.update_xaxes(gridcolor="#283442", zerolinecolor="#283442", linecolor="#506784", overwrite=False)
    f.update_yaxes(gridcolor="#283442", zerolinecolor="#283442", linecolor="#506784", overwrite=False)

    import base64
    import numpy as np

    def _decode(obj):
        """Convierte typed arrays base64 {'dtype','bdata'} de Plotly 6 en listas planas."""
        if isinstance(obj, dict):
            if "bdata" in obj and "dtype" in obj:
                arr = np.frombuffer(base64.b64decode(obj["bdata"]), dtype=np.dtype(obj["dtype"]))
                if obj.get("shape"):
                    shape = obj["shape"]
                    if isinstance(shape, str):
                        shape = [int(x) for x in shape.split(",")]
                    arr = arr.reshape(shape)
                if arr.dtype.kind == "f":
                    arr = np.round(arr, 4)
                return arr.tolist()
            return {k: _decode(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_decode(v) for v in obj]
        return obj

    def _dump(obj) -> str:
        plain = json.loads(json.dumps(obj, cls=PlotlyJSONEncoder))
        return json.dumps(
            _decode(plain), separators=(",", ":"), ensure_ascii=False
        ).replace("</", "<\\/")

    spec = f.to_plotly_json()
    for tr in spec.get("data", []):
        if tr.get("type") in ("sunburst", "treemap", "icicle") and tr.get("ids") is not None \
                and tr.get("parents") is not None:
            ids = list(tr["ids"])
            idmap = {old: str(i) for i, old in enumerate(ids)}
            tr["ids"] = [str(i) for i in range(len(ids))]
            tr["parents"] = [idmap.get(p, "") for p in tr["parents"]]
            tr["hovertemplate"] = "%{label}<br>Publicaciones: %{value}<extra></extra>"
    layout = spec.get("layout", {}) or {}
    layout.pop("template", None)
    height = layout.get("height") or default_height
    layout.setdefault("autosize", True)

    return (
        f'<script src="{PLOTLY_CDN_URL}"></script>'
        f'<div id="{div_id}" style="width:100%;height:{int(height)}px"></div>'
        f'<script>Plotly.newPlot("{div_id}",{_dump(spec.get("data", []))},{_dump(layout)},'
        f'{{"responsive":true,"displaylogo":false}});</script>'
    )


def _render_png_card(data_type: str, data: Dict[str, Any], output_png: str, title: str) -> None:
    """Genera una tarjeta estática PNG a 200 DPI con Matplotlib."""
    if plt is None:
        return
    try:
        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=180)
        fig.patch.set_facecolor(THEME_CARD)
        ax.set_facecolor(THEME_CARD)

        if data_type == "timeseries":
            results = [r for r in data.get("results", []) if str(r.get("year", r.get("dimension", ""))).isdigit()]
            results.sort(key=lambda x: int(x.get("year", x.get("dimension", 0))))
            years = [int(r.get("year", r.get("dimension", 0))) for r in results]
            works = [r.get("total_works", 0) for r in results]
            if years and works:
                ax.plot(years, works, marker="o", color="#38BDF8", linewidth=2.5, markersize=5)
                ax.fill_between(years, works, color="#38BDF8", alpha=0.15)
                ax.set_title(title or "Trayectoria Cronológica de Publicaciones", fontsize=12, fontweight="bold", pad=12)
                ax.set_xlabel("Año", fontsize=10)
                ax.set_ylabel("Artículos", fontsize=10)
        elif data_type == "oa-donut":
            results = [r for r in data.get("results", []) if r.get("dimension")]
            labels = [r["dimension"].capitalize() for r in results]
            vals = [r.get("total_works", 0) for r in results]
            colors = [OA_COLORS.get(r["dimension"].lower(), "#64748B") for r in results]
            if vals and sum(vals) > 0:
                ax.pie(vals, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90, wedgeprops=dict(width=0.45, edgecolor=THEME_CARD))
                ax.set_title(title or "Distribución de Vías de Acceso Abierto", fontsize=12, fontweight="bold")
        elif data_type in ("top-ranking", "quadrant"):
            entities = (data.get("top_entities") or data.get("results") or [])[:10][::-1]
            names = [(e.get("display_name") or e.get("institution") or "Entidad")[:25] for e in entities]
            works = [e.get("total_works", 0) for e in entities]
            if names and works:
                ax.barh(names, works, color="#38BDF8", edgecolor="#0284C7")
                ax.set_title(title or "Ranking de Entidades Líderes", fontsize=12, fontweight="bold", pad=12)
                ax.set_xlabel("Publicaciones Acumuladas", fontsize=10)
        else:
            ax.text(0.5, 0.5, title or "Artefacto Visual OpenAlex México", ha="center", va="center", color="#F9FAFB", fontsize=14)

        plt.tight_layout()
        os.makedirs(os.path.dirname(os.path.abspath(output_png)), exist_ok=True)
        plt.savefig(output_png, facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)
    except Exception as e:
        if plt:
            plt.close("all")


def detect_data_type(data: Dict[str, Any]) -> str:
    """Detecta la estructura interna del JSON devuelto por las consultas."""
    if "top_entities" in data:
        return "top-ranking"
    if "grouped_by" in data:
        gb = data.get("grouped_by")
        if gb == "publication_year":
            return "timeseries"
        if gb == "oa_status":
            return "oa-donut"
        if gb in ("topics_hierarchy", "taxonomy"):
            return "sunburst"
        if gb in ("sdg", "sdgs"):
            return "sdg-grid"
        return "general-aggregate"
    if "works" in data or (data.get("target") == "works"):
        return "dossier-works"
    return "generic"


# ==============================================================================
# 1. SERIE TEMPORAL DUAL (Publicaciones + FWCI + Citas)
# ==============================================================================
def openalex_plot_timeseries(
    data: Optional[Union[Dict[str, Any], str]] = None,
    institution_id: str = "",
    author_id: Union[str, List[str]] = "",
    query: str = "",
    start_year: int = 2010,
    end_year: int = 2026,
    title: str = "",
    output_dir: str = "./reports"
) -> Dict[str, Any]:
    """
    Genera serie temporal interactiva dual (barras de publicaciones anuales + línea de FWCI normalizado relativo
    al benchmark mundial 1.00 + citas acumuladas) con tarjetas KPI y tabla cronológica.
    """
    raw = _load_data(data)
    if not raw or "results" not in raw:
        clauses = []
        if start_year:
            clauses.append(f"publication_year >= {start_year}")
        if end_year:
            clauses.append(f"publication_year <= {end_year}")
        if query:
            clean_q = query.replace("'", "\\'")
            clauses.append(f"(ilike(title, '%{clean_q}%') OR ilike(subfield, '%{clean_q}%'))")
        if institution_id and not ("ror.org" in institution_id or institution_id.startswith("0")):
            clean_i = institution_id.replace("'", "\\'")
            clauses.append(f"has(institution_names, '{clean_i}')")

        filter_param = " AND ".join(clauses) if clauses else "1=1"
        ror_param = institution_id if ("ror.org" in institution_id or institution_id.startswith("0")) else None

        raw = openalex_aggregate_mexico(
            group_by="publication_year",
            author_id=author_id,
            filter_param=filter_param,
            institution_ror=ror_param,
            limit=100
        )

    results = raw.get("results", [])
    valid = [r for r in results if str(r.get("year", r.get("dimension", ""))).isdigit()]
    valid.sort(key=lambda x: int(x.get("year", x.get("dimension", 0))))

    if not valid:
        return {"status": "error", "message": "No se encontraron datos de series temporales para los filtros especificados."}

    years = [int(r.get("year", r.get("dimension", 0))) for r in valid]
    works = [int(r.get("total_works", 0)) for r in valid]
    cites = [int(r.get("total_citations", 0)) for r in valid]
    fwci = [round(float(r.get("avg_fwci", 0.0) or 0.0), 2) for r in valid]
    apc = [float(r.get("total_apc_paid_usd", 0.0) or 0.0) for r in valid]

    title_text = title or f"Evolución Cronológica de la Producción Científica e Impacto ({years[0]}-{years[-1]})"
    html_path, png_path = _resolve_output_paths(output_dir, "timeseries")

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=years,
            y=works,
            name="Publicaciones",
            marker=dict(color="#0284C7", opacity=0.85)
        ),
        secondary_y=False
    )
    fig.add_trace(
        go.Scatter(
            x=years,
            y=fwci,
            name="FWCI Promedio",
            mode="lines+markers",
            line=dict(color="#10B981", width=3),
            marker=dict(size=7, color="#34D399")
        ),
        secondary_y=True
    )
    fig.add_hline(
        y=1.0,
        line_dash="dash",
        line_color="#EF4444",
        secondary_y=True,
        annotation_text="Media Mundial (1.00)",
        annotation_position="bottom right"
    )

    fig.update_layout(
        title=f"<b>{title_text}</b>",
        template="plotly_dark",
        height=480,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,24,39,0.7)",
        legend=dict(orientation="h", y=1.1, x=0.3)
    )
    fig.update_xaxes(title_text="Año de publicación", dtick=1 if len(years) < 15 else 2)
    fig.update_yaxes(title_text="Artículos Publicados", secondary_y=False)
    fig.update_yaxes(title_text="FWCI Normalizado", secondary_y=True)

    plot_html = _compact_plotly_html(fig)
    tot_works = sum(works)
    tot_cites = sum(cites)
    tot_apc = sum(apc)
    avg_fwci = round(sum(fwci) / len(fwci), 2) if fwci else 1.0

    table_rows = []
    for y, w, c, f, a in zip(years, works, cites, fwci, apc):
        fwci_badge = f'<span class="font-mono text-emerald-400">{f:.2f}</span>' if f >= 1.0 else f'<span class="font-mono text-amber-400">{f:.2f}</span>'
        table_rows.append(f"""
        <tr>
            <td class="font-bold">{y}</td>
            <td class="text-right font-bold text-sky-400">{w:,}</td>
            <td class="text-right text-gray-300">{c:,}</td>
            <td class="text-right">{fwci_badge}</td>
            <td class="text-right text-amber-400 font-mono">${a:,.0f}</td>
        </tr>
        """)

    full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{title_text}</title>
    <style>{_get_embedded_styles()}</style>
</head>
<body class="bg-dark text-gray-100">
    <div class="container mx-auto p-6 max-w-6xl">
        <header class="header-card mb-6">
            <span class="tag">OpenAlex México · Trayectoria Temporal</span>
            <h1 class="text-2xl font-black text-white mt-1">{title_text}</h1>
            <div class="grid grid-cols-4 gap-4 mt-4">
                <div class="kpi-mini">
                    <span class="kpi-label">Total Publicaciones</span>
                    <span class="kpi-val">{tot_works:,}</span>
                </div>
                <div class="kpi-mini">
                    <span class="kpi-label">Citas Acumuladas</span>
                    <span class="kpi-val">{tot_cites:,}</span>
                </div>
                <div class="kpi-mini">
                    <span class="kpi-label">FWCI Medio</span>
                    <span class="kpi-val text-emerald-400">{avg_fwci}</span>
                </div>
                <div class="kpi-mini">
                    <span class="kpi-label">Gasto APC Estimado</span>
                    <span class="kpi-val text-amber-400">${tot_apc:,.0f} USD</span>
                </div>
            </div>
        </header>
        <section class="card mb-6">
            {plot_html}
        </section>
        <section class="card">
            <h2 class="text-lg font-bold text-white mb-4">Desglose Cronológico de Indicadores</h2>
            <div class="overflow-x-auto">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Año</th>
                            <th class="text-right">Publicaciones</th>
                            <th class="text-right">Citas</th>
                            <th class="text-right">FWCI Promedio</th>
                            <th class="text-right">Gasto APC (USD)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(table_rows)}
                    </tbody>
                </table>
            </div>
        </section>
    </div>
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    _render_png_card("timeseries", raw, png_path, title_text)

    return _build_viz_result(
        chart_type="timeseries",
        title=title_text,
        html_path=html_path,
        png_path=png_path,
        summary_kpis={
            "period": f"{years[0]}-{years[-1]}",
            "total_works": tot_works,
            "total_citations": tot_cites,
            "avg_fwci": avg_fwci,
            "total_apc_usd": tot_apc
        },
        message=f"Serie temporal interactiva guardada en {html_path}"
    )


# ==============================================================================
# 2. DONA DE ACCESO ABIERTO Y GASTO COMERCIAL EN APC
# ==============================================================================
def openalex_plot_oa_donut(
    data: Optional[Union[Dict[str, Any], str]] = None,
    institution_id: str = "",
    author_id: Union[str, List[str]] = "",
    query: str = "",
    year: Optional[int] = None,
    title: str = "",
    output_dir: str = "./reports"
) -> Dict[str, Any]:
    """
    Genera gráfica Donut interactiva con las 6 vías de Acceso Abierto (Diamante, Dorada APC, Híbrida, Bronce, Verde, Cerrada)
    con paleta cienciométrica oficial y desglose del gasto comercial estimado en APC (USD).
    """
    raw = _load_data(data)
    if not raw or "results" not in raw:
        clauses = []
        if year:
            clauses.append(f"publication_year = {year}")
        if query:
            clean_q = query.replace("'", "\\'")
            clauses.append(f"(ilike(title, '%{clean_q}%') OR ilike(subfield, '%{clean_q}%'))")
        if institution_id and not ("ror.org" in institution_id or institution_id.startswith("0")):
            clean_i = institution_id.replace("'", "\\'")
            clauses.append(f"has(institution_names, '{clean_i}')")

        filter_param = " AND ".join(clauses) if clauses else "1=1"
        ror_param = institution_id if ("ror.org" in institution_id or institution_id.startswith("0")) else None

        raw = openalex_aggregate_mexico(
            group_by="oa_status",
            author_id=author_id,
            filter_param=filter_param,
            institution_ror=ror_param,
            limit=50
        )

    results = raw.get("results", [])
    if not results:
        return {"status": "error", "message": "No se encontraron datos de Acceso Abierto."}

    labels, values, colors, apc_totals = [], [], [], []
    for r in results:
        oa = str(r.get("dimension", "")).lower()
        if not oa:
            continue
        labels.append(oa.capitalize())
        values.append(int(r.get("total_works", 0)))
        colors.append(OA_COLORS.get(oa, "#64748B"))
        apc_totals.append(float(r.get("total_apc_paid_usd", 0.0) or 0.0))

    title_text = title or "Distribución de Vías de Acceso Abierto y Gasto en APC"
    html_path, png_path = _resolve_output_paths(output_dir, "oa_donut")

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.45,
        marker=dict(colors=colors),
        textinfo="label+percent",
        hoverinfo="label+value+percent"
    )])
    fig.update_layout(
        title=f"<b>{title_text}</b>",
        template="plotly_dark",
        height=450,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,24,39,0.7)"
    )
    plot_html = _compact_plotly_html(fig)

    total_works = sum(values)
    total_apc = sum(apc_totals)
    diamond_works = sum(v for l, v in zip(labels, values) if l.lower() == "diamond")
    gold_works = sum(v for l, v in zip(labels, values) if l.lower() == "gold")
    diamond_pct = round((diamond_works / total_works * 100), 1) if total_works else 0.0

    full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{title_text}</title>
    <style>{_get_embedded_styles()}</style>
</head>
<body class="bg-dark text-gray-100">
    <div class="container mx-auto p-6 max-w-6xl">
        <header class="header-card mb-6">
            <span class="tag">OpenAlex México · Política de Acceso Abierto</span>
            <h1 class="text-2xl font-black text-white mt-1">{title_text}</h1>
            <div class="grid grid-cols-4 gap-4 mt-4">
                <div class="kpi-mini">
                    <span class="kpi-label">Vía Diamante (No comercial)</span>
                    <span class="kpi-val text-emerald-400">{diamond_works:,} ({diamond_pct}%)</span>
                </div>
                <div class="kpi-mini">
                    <span class="kpi-label">Vía Dorada (Con APC)</span>
                    <span class="kpi-val text-amber-400">{gold_works:,}</span>
                </div>
                <div class="kpi-mini">
                    <span class="kpi-label">Gasto Total en APC</span>
                    <span class="kpi-val text-rose-400">${total_apc:,.0f} USD</span>
                </div>
                <div class="kpi-mini">
                    <span class="kpi-label">Total Publicaciones</span>
                    <span class="kpi-val text-sky-400">{total_works:,}</span>
                </div>
            </div>
        </header>
        <section class="card mb-6">
            {plot_html}
        </section>
    </div>
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    _render_png_card("oa-donut", raw, png_path, title_text)

    return _build_viz_result(
        chart_type="oa-donut",
        title=title_text,
        html_path=html_path,
        png_path=png_path,
        summary_kpis={
            "total_works": total_works,
            "diamond_works": diamond_works,
            "diamond_percentage": diamond_pct,
            "gold_apc_works": gold_works,
            "total_apc_paid_usd": total_apc
        },
        message=f"Dona interactiva de Acceso Abierto guardada en {html_path}"
    )


# ==============================================================================
# 3. RANKING DE ENTIDADES (Barras horizontales + Escala Viridis FWCI)
# ==============================================================================
def openalex_plot_top_ranking(
    data: Optional[Union[Dict[str, Any], str]] = None,
    by: str = "authors",
    query: str = "",
    limit: int = 15,
    title: str = "",
    output_dir: str = "./reports"
) -> Dict[str, Any]:
    """
    Genera ranking de barras horizontales interactivo para instituciones o autores líderes,
    coloreado por escala Viridis según su FWCI promedio + tabla dinámica con insignias.
    """
    raw = _load_data(data)
    if not raw or "top_entities" not in raw:
        raw = openalex_top_entities(by=by, query=query, limit=limit)

    entities = raw.get("top_entities", [])
    if not entities:
        return {"status": "error", "message": "No se encontraron entidades para graficar el ranking."}

    title_text = title or f"Capacidad y Desempeño: Top {len(entities)} {by.capitalize()} en '{query or 'Producción Científica'}'"
    html_path, png_path = _resolve_output_paths(output_dir, "top_ranking")

    names = [(e.get("display_name") or e.get("institution") or "Entidad") for e in entities][::-1]
    works = [int(e.get("total_works", 0)) for e in entities][::-1]
    cites = [int(e.get("total_citations", 0)) for e in entities][::-1]
    fwci = [round(float(e.get("avg_fwci", 1.0) or 1.0), 2) for e in entities][::-1]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=names,
        x=works,
        orientation="h",
        marker=dict(
            color=fwci,
            colorscale="Viridis",
            colorbar=dict(title="FWCI Promedio", len=0.8),
            showscale=True
        ),
        text=[f"Docs: {w} | Citas: {c} | FWCI: {f}" for w, c, f in zip(works, cites, fwci)],
        hoverinfo="text+y",
        name="Producción"
    ))
    fig.update_layout(
        title=f"<b>{title_text}</b>",
        xaxis_title="Publicaciones Acumuladas",
        yaxis_title="",
        template="plotly_dark",
        height=max(450, len(entities) * 32),
        margin=dict(l=220, r=40, t=60, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,24,39,0.7)"
    )
    plot_html = _compact_plotly_html(fig)

    table_rows = []
    for e in entities:
        is_mx = e.get("is_mexican_affiliated", True)
        badge = '<span class="badge badge-mx">México</span>' if is_mx else '<span class="badge badge-ext">Internacional</span>'
        inst_label = e.get("institution") or "Sin institución registrada"
        f = float(e.get("avg_fwci", 1.0) or 1.0)
        fwci_badge = f'<span class="font-mono text-emerald-400">{f:.2f}</span>' if f >= 1.0 else f'<span class="font-mono text-amber-400">{f:.2f}</span>'
        table_rows.append(f"""
        <tr>
            <td class="font-bold">{e.get("rank", "-")}</td>
            <td class="font-semibold text-sky-400">{e.get("display_name") or e.get("institution")} {badge}</td>
            <td class="text-gray-300">{inst_label}</td>
            <td class="text-right font-bold text-white">{e.get("total_works", 0):,}</td>
            <td class="text-right text-gray-300">{e.get("total_citations", 0):,}</td>
            <td class="text-right">{fwci_badge}</td>
        </tr>
        """)

    full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{title_text}</title>
    <style>{_get_embedded_styles()}</style>
</head>
<body class="bg-dark text-gray-100">
    <div class="container mx-auto p-6 max-w-6xl">
        <header class="header-card mb-6">
            <span class="tag">OpenAlex México · Ranking de Desempeño</span>
            <h1 class="text-2xl font-black text-white mt-1">{title_text}</h1>
        </header>
        <section class="card mb-6">
            {plot_html}
        </section>
        <section class="card">
            <div class="overflow-x-auto">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Entidad / Investigador</th>
                            <th>Institución</th>
                            <th class="text-right">Publicaciones</th>
                            <th class="text-right">Citas</th>
                            <th class="text-right">FWCI</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(table_rows)}
                    </tbody>
                </table>
            </div>
        </section>
    </div>
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    _render_png_card("top-ranking", raw, png_path, title_text)

    return _build_viz_result(
        chart_type="top-ranking",
        title=title_text,
        html_path=html_path,
        png_path=png_path,
        summary_kpis={
            "entity_count": len(entities),
            "top_entity": entities[0].get("display_name") or entities[0].get("institution") if entities else "",
            "max_works": entities[0].get("total_works", 0) if entities else 0
        },
        message=f"Ranking interactivo guardado en {html_path}"
    )


# ==============================================================================
# 4. SUNBURST TAXONÓMICO JERÁRQUICO (Dominio -> Campo -> Subcampo -> Tópico)
# ==============================================================================
def openalex_plot_sunburst(
    data: Optional[Union[Dict[str, Any], str]] = None,
    institution_id: str = "",
    author_id: Union[str, List[str]] = "",
    query: str = "",
    title: str = "",
    output_dir: str = "./reports"
) -> Dict[str, Any]:
    """
    Gráfico jerárquico concéntrico multinivel de taxonomía científica (Dominio -> Campo -> Subcampo -> Tópico)
    con zoom interactivo al hacer clic en los sectores.
    """
    raw = _load_data(data)
    results = raw.get("results") or []
    if not results and "works" in raw:
        counts = {}
        for w in raw["works"]:
            top = w.get("topic") or "General"
            sub = w.get("subfield") or "General"
            fld = w.get("field") or "Multidisciplinario"
            dom = w.get("domain") or "Ciencias"
            key = (dom, fld, sub, top)
            counts[key] = counts.get(key, 0) + 1
        results = [
            {"domain": k[0], "field": k[1], "subfield": k[2], "topic": k[3], "total_works": v}
            for k, v in counts.items()
        ]

    if not results:
        # Consulta jerárquica a ClickHouse
        where_conds = ["domain != ''", "field != ''", "subfield != ''", "topic != ''"]
        if institution_id:
            where_conds.append(f"(has(institution_names, '{institution_id}') OR has(institution_rors, '{institution_id}'))")
        aids = normalize_author_ids(author_id)
        if aids:
            where_conds.append(build_authors_condition(aids))
        if query:
            where_conds.append(f"ilike(title, '%{query}%')")
        where_clause = " AND ".join(where_conds)

        sql = f"""
        SELECT domain, field, subfield, topic, count(*) as total_works
        FROM rag.works_academic_all
        WHERE {where_clause}
        GROUP BY domain, field, subfield, topic
        ORDER BY total_works DESC
        LIMIT 100
        """
        ch_res = execute_safe_query(sql)
        results = ch_res.get("data", [])

    if not results:
        return {"status": "error", "message": "No se encontraron datos taxonómicos para graficar el Sunburst."}

    df = pd.DataFrame(results)
    for col in ['domain', 'field', 'subfield', 'topic']:
        if col not in df.columns:
            df[col] = "Sin clasificar"
        else:
            df[col] = df[col].fillna("Sin clasificar").replace('', "Sin clasificar")

    if 'total_works' not in df.columns:
        df['total_works'] = 1

    df = df.sort_values('total_works', ascending=False).head(40)
    title_text = title or "Estructura de Especialización Científica (Taxonomía Concéntrica)"
    html_path, png_path = _resolve_output_paths(output_dir, "sunburst")

    fig = px.sunburst(
        df,
        path=['domain', 'field', 'subfield', 'topic'],
        values='total_works',
        color='total_works',
        color_continuous_scale='Blues',
        title=""
    )
    fig.update_layout(
        template="plotly_dark",
        margin=dict(t=30, l=10, r=10, b=20),
        height=680,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,24,39,0.7)"
    )
    plot_html = _compact_plotly_html(fig)

    top_topics_rows = []
    top_df = df.sort_values('total_works', ascending=False).head(15)
    for idx, (_, row) in enumerate(top_df.iterrows(), 1):
        top_topics_rows.append(f"""
        <tr>
            <td class="font-bold">{idx}</td>
            <td class="font-semibold text-sky-400">{row['topic']}</td>
            <td class="text-gray-300">{row['subfield']}</td>
            <td class="text-gray-400">{row['field']}</td>
            <td class="text-right font-bold text-white">{int(row['total_works']):,}</td>
        </tr>
        """)

    full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{title_text}</title>
    <style>{_get_embedded_styles()}</style>
</head>
<body class="bg-dark text-gray-100">
    <div class="container mx-auto p-6 max-w-6xl">
        <header class="header-card mb-6">
            <span class="tag">OpenAlex México · Taxonomía Científica</span>
            <h1 class="text-2xl font-black text-white mt-1">{title_text}</h1>
            <p class="text-sm text-gray-400 mt-2">Haz clic en los anillos concéntricos para explorar subcampos y tópicos específicos.</p>
        </header>
        <section class="card mb-6">
            {plot_html}
        </section>
        <section class="card">
            <h2 class="text-lg font-bold text-white mb-4">Top Tópicos Principales</h2>
            <div class="overflow-x-auto">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Tópico</th>
                            <th>Subcampo</th>
                            <th>Campo</th>
                            <th class="text-right">Publicaciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(top_topics_rows)}
                    </tbody>
                </table>
            </div>
        </section>
    </div>
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    _render_png_card("sunburst", raw, png_path, title_text)

    return _build_viz_result(
        chart_type="sunburst",
        title=title_text,
        html_path=html_path,
        png_path=png_path,
        summary_kpis={
            "total_topics_analyzed": len(df),
            "top_topic": str(top_df.iloc[0]['topic']) if not top_df.empty else ""
        },
        message=f"Sunburst taxonómico interactivo guardado en {html_path}"
    )


# ==============================================================================
# 5. MATRIZ OFICIAL DE LOS 17 ODS DE LA ONU
# ==============================================================================
def openalex_plot_sdg_grid(
    data: Optional[Union[Dict[str, Any], str]] = None,
    institution_id: str = "",
    institution_name: str = "",
    author_id: Union[str, List[str]] = "",
    author_name: str = "",
    academic_name: str = "",
    query: str = "",
    title: str = "",
    output_dir: str = "./reports"
) -> Dict[str, Any]:
    """
    Cuadrícula interactiva de los 17 Objetivos de Desarrollo Sostenible (ODS de la ONU)
    con colores oficiales, porcentaje del corpus y tabla comparativa de impacto por ODS.
    Soporta análisis a nivel nacional (México completo), institucional, de autor/investigador (ID único o lista) o temático.
    """
    raw = _load_data(data)
    results = raw.get("results") or []
    aids = normalize_author_ids(author_id)
    target_author_name = (author_name or academic_name).strip()
    target_inst = (institution_id or institution_name).strip()
    target_author_id = aids if aids else ""
    if not aids and author_id and isinstance(author_id, str) and not target_author_name:
        target_author_name = author_id.strip()

    if not results:
        clauses = []
        if query:
            clean_q = query.replace("'", "\\'")
            clauses.append(f"(ilike(title, '%{clean_q}%') OR ilike(subfield, '%{clean_q}%'))")

        filter_param = " AND ".join(clauses) if clauses else "1=1"
        ror_param = target_inst if target_inst else None

        raw = openalex_aggregate_mexico(
            group_by="sdgs",
            author_id=target_author_id,
            author_name=target_author_name,
            filter_param=filter_param,
            institution_ror=ror_param,
            limit=50
        )
        results = raw.get("results") or []

    sdg_map = {}
    if results:
        for r in results:
            dim = r.get("sdg_num") or r.get("dimension", "")
            if isinstance(dim, list):
                dims = [str(d) for d in dim]
            else:
                dims = [str(dim)]
            for d in dims:
                match = re.search(r'sdg/(\d+)|\b(\d+)\b', d, re.IGNORECASE)
                if match:
                    num = int(match.group(1) or match.group(2))
                    if 1 <= num <= 17:
                        if num not in sdg_map:
                            sdg_map[num] = dict(r)
                        else:
                            sdg_map[num]["total_works"] = sdg_map[num].get("total_works", 0) + r.get("total_works", 0)
                            sdg_map[num]["total_citations"] = sdg_map[num].get("total_citations", 0) + r.get("total_citations", 0)

    total_works_all_sdgs = sum(r.get("total_works", 0) for r in sdg_map.values())
    total_citations_all_sdgs = sum(r.get("total_citations", 0) for r in sdg_map.values())

    if not title:
        if target_author_name or target_author_id:
            auth_lbl = target_author_name or target_author_id
            title_text = f"Distribución de ODS en las publicaciones de {auth_lbl}"
        elif target_inst:
            title_text = f"Distribución de ODS en {target_inst}"
        elif query:
            title_text = f"Distribución de ODS en {query} (México)"
        else:
            title_text = "Alineación de México con los 17 Objetivos de Desarrollo Sostenible (ONU)"
    else:
        title_text = title

    html_path, png_path = _resolve_output_paths(output_dir, "sdg_grid")

    cards_html = []
    table_rows = []
    for i in range(1, 18):
        info = SDG_INFO.get(i, {"name": f"ODS {i}", "color": "#1E293B"})
        r = sdg_map.get(i, {"total_works": 0, "total_citations": 0, "avg_fwci": 0.0})
        count = int(r.get("total_works", 0))
        cites = int(r.get("total_citations", 0))
        fwci = float(r.get("avg_fwci", 0.0) or 0.0)
        pct = (count / total_works_all_sdgs * 100) if total_works_all_sdgs > 0 else 0.0
        active_class = "" if count > 0 else "sdg-inactive"
        img_url = f"https://open-sdg.github.io/sdg-translations/assets/img/goals/es/{i}.png"
        tooltip = f"ODS {i}: {info['name']} - {count:,} publicaciones ({pct:.1f}%)"

        cards_html.append(f"""
        <div class="sdg-card {active_class}" style="background-color: {info['color']};" title="{tooltip}">
            <img src="{img_url}" class="sdg-img" alt="ODS {i}" loading="lazy" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
            <div class="sdg-fallback" style="display:none; background:{info['color']};">
                <span class="sdg-fallback-num">{i}</span>
                <span class="sdg-fallback-name">{info['name']}</span>
            </div>
            <div class="sdg-overlay">
                <span class="sdg-perc">{pct:.1f}%</span>
                <span class="sdg-count">{count:,} docs</span>
            </div>
        </div>
        """)

        fwci_badge = f'<span class="font-mono text-emerald-400">{fwci:.2f}</span>' if count > 0 else '<span class="text-gray-500">-</span>'
        table_rows.append(f"""
        <tr>
            <td class="font-bold text-center">
                <span class="sdg-badge-num" style="background-color: {info['color']};">{i}</span>
            </td>
            <td class="font-semibold text-white">{info['name']}</td>
            <td class="text-right font-bold text-sky-400">{count:,}</td>
            <td class="text-right font-mono text-gray-300">{pct:.1f}%</td>
            <td class="text-right text-gray-300">{cites:,}</td>
            <td class="text-right">{fwci_badge}</td>
        </tr>
        """)

    active_sdg_count = sum(1 for i in range(1, 18) if sdg_map.get(i, {}).get("total_works", 0) > 0)

    full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{title_text}</title>
    <style>{_get_embedded_styles()}</style>
</head>
<body class="bg-dark text-gray-100">
    <div class="container mx-auto p-6 max-w-6xl">
        <header class="header-card mb-6">
            <span class="tag">OpenAlex México · Agenda 2030</span>
            <h1 class="text-2xl font-black text-white mt-1">{title_text}</h1>
            <div class="grid grid-cols-3 gap-4 mt-4">
                <div class="kpi-mini">
                    <span class="kpi-label">ODS con Actividad</span>
                    <span class="kpi-val text-emerald-400">{active_sdg_count} / 17</span>
                </div>
                <div class="kpi-mini">
                    <span class="kpi-label">Publicaciones en ODS</span>
                    <span class="kpi-val">{total_works_all_sdgs:,}</span>
                </div>
                <div class="kpi-mini">
                    <span class="kpi-label">Citas en ODS</span>
                    <span class="kpi-val text-sky-400">{total_citations_all_sdgs:,}</span>
                </div>
            </div>
        </header>
        <section class="card mb-6">
            <h2 class="text-lg font-bold text-white mb-4">Cuadrícula Oficial ODS (Agenda 2030)</h2>
            <div class="sdg-grid">
                {''.join(cards_html)}
            </div>
        </section>
        <section class="card">
            <h2 class="text-lg font-bold text-white mb-4">Tabla Desglosada por Objetivo</h2>
            <div class="overflow-x-auto">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th class="text-center">#</th>
                            <th>Objetivo de Desarrollo Sostenible</th>
                            <th class="text-right">Publicaciones</th>
                            <th class="text-right">% Corpus</th>
                            <th class="text-right">Citas</th>
                            <th class="text-right">FWCI</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(table_rows)}
                    </tbody>
                </table>
            </div>
        </section>
    </div>
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    _render_png_card("sdg-grid", raw, png_path, title_text)

    return _build_viz_result(
        chart_type="sdg-grid",
        title=title_text,
        html_path=html_path,
        png_path=png_path,
        summary_kpis={
            "active_sdgs": active_sdg_count,
            "total_sdg_works": total_works_all_sdgs
        },
        message=f"Cuadrícula interactiva de ODS guardada en {html_path}"
    )


# ==============================================================================
# 6. DOSSIER DE PUBLICACIONES CIENTÍFICAS
# ==============================================================================
def openalex_plot_dossier_works(
    data: Optional[Union[Dict[str, Any], str]] = None,
    institution_id: str = "",
    author_id: Union[str, List[str]] = "",
    query: str = "",
    limit: int = 25,
    title: str = "",
    output_dir: str = "./reports"
) -> Dict[str, Any]:
    """
    Dossier interactivo con catálogo de publicaciones, insignias de coautoría nacional/internacional,
    DOI, revista, FWCI, citas y tópicos.
    """
    raw = _load_data(data)
    works = raw.get("works") or raw.get("results") or []
    if not works:
        raw = openalex_search_works(query=query, author_id=author_id, institution_name=institution_id, limit=limit)
        works = raw.get("works") or []

    if not works:
        return {"status": "error", "message": "No se encontraron publicaciones para el dossier."}

    title_text = title or f"Dossier de Publicaciones Científicas ({len(works)} obras)"
    html_path, png_path = _resolve_output_paths(output_dir, "dossier_works")

    rows = []
    tot_cites = sum(w.get("cited_by_count", 0) for w in works)
    fwcis = [float(w["fwci"]) for w in works if w.get("fwci") is not None]
    avg_fwci = round(sum(fwcis)/len(fwcis), 2) if fwcis else 1.0

    for idx, w in enumerate(works, 1):
        oa_status = (w.get("oa_status") or "closed").lower()
        oa_color = OA_COLORS.get(oa_status, "#6B7280")
        oa_badge = f'<span class="badge" style="background-color: {oa_color}22; color: {oa_color}; border: 1px solid {oa_color}88;">{oa_status.capitalize()}</span>'
        doi_link = f'<a href="{w.get("doi")}" target="_blank" class="text-sky-400 hover:underline">DOI</a>' if w.get("doi") else ""
        cites = w.get("cited_by_count", 0)
        f_val = f"{float(w['fwci']):.2f}" if w.get("fwci") is not None else "-"

        rows.append(f"""
        <tr>
            <td class="font-bold">{idx}</td>
            <td>
                <div class="font-bold text-white">{w.get("title") or "Sin título"}</div>
                <div class="text-xs text-gray-400 mt-1">{w.get("source_name") or w.get("source_id") or ""} · {w.get("publication_year", "")} · {doi_link}</div>
            </td>
            <td class="text-center">{oa_badge}</td>
            <td class="text-right font-bold text-gray-200">{cites:,}</td>
            <td class="text-right font-mono text-emerald-400">{f_val}</td>
        </tr>
        """)

    full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{title_text}</title>
    <style>{_get_embedded_styles()}</style>
</head>
<body class="bg-dark text-gray-100">
    <div class="container mx-auto p-6 max-w-6xl">
        <header class="header-card mb-6">
            <span class="tag">OpenAlex México · Catálogo de Literatura</span>
            <h1 class="text-2xl font-black text-white mt-1">{title_text}</h1>
            <div class="grid grid-cols-3 gap-4 mt-4">
                <div class="kpi-mini">
                    <span class="kpi-label">Obras Mostradas</span>
                    <span class="kpi-val">{len(works)}</span>
                </div>
                <div class="kpi-mini">
                    <span class="kpi-label">Citas Acumuladas</span>
                    <span class="kpi-val text-sky-400">{tot_cites:,}</span>
                </div>
                <div class="kpi-mini">
                    <span class="kpi-label">FWCI Promedio</span>
                    <span class="kpi-val text-emerald-400">{avg_fwci}</span>
                </div>
            </div>
        </header>
        <section class="card">
            <div class="overflow-x-auto">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Título y Metadatos</th>
                            <th class="text-center">Vía OA</th>
                            <th class="text-right">Citas</th>
                            <th class="text-right">FWCI</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(rows)}
                    </tbody>
                </table>
            </div>
        </section>
    </div>
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    return _build_viz_result(
        chart_type="dossier-works",
        title=title_text,
        html_path=html_path,
        png_path="",
        summary_kpis={
            "works_count": len(works),
            "total_citations": tot_cites,
            "avg_fwci": avg_fwci
        },
        message=f"Dossier de publicaciones guardado en {html_path}"
    )


# ==============================================================================
# 7. RED INTERACTIVA DE COAUTORÍA (PyVis Network)
# ==============================================================================
def openalex_plot_collaboration_network(
    data: Optional[Union[Dict[str, Any], str]] = None,
    academic_name: str = "",
    institution_id: str = "",
    author_id: Union[str, List[str]] = "",
    query: str = "",
    limit_works: int = 50,
    title: str = "",
    output_dir: str = "./reports"
) -> Dict[str, Any]:
    """
    Grafo interactivo de red de coautoría científica.
    Para investigadores individuales (ej. 'Annie Pardo'), delega automáticamente a CoAuthra.
    Para tópicos amplios o instituciones, genera un grafo local en PyVis con física de resortes.
    """
    # 1. Detectar si la consulta corresponde a un investigador individual
    aids = normalize_author_ids(author_id)
    first_aid = aids[0] if aids else None
    target_author = academic_name or ("" if aids else (author_id if (author_id and isinstance(author_id, str) and not author_id.startswith("http") and not (author_id.startswith("A") and author_id[1:].isdigit())) else ""))
    if not target_author and query and not data:
        clean_q = query.strip().replace("'", "")
        chk_sql = f"SELECT id, name FROM rag.academics_all WHERE name ILIKE '%{clean_q}%' LIMIT 1"
        chk_res = execute_safe_query(chk_sql)
        if chk_res.get("data"):
            target_author = clean_q

    if target_author or first_aid:
        coauthra_res = openalex_plot_coauthra_network(
            academic_name=target_author,
            author_id=first_aid,
            title=title,
            output_dir=output_dir
        )
        if coauthra_res.get("status") == "success":
            return coauthra_res

    raw = _load_data(data)
    works = raw.get("works") or raw.get("results") or []
    if not works:
        raw = openalex_search_works(query=query, author_id=author_id, institution_name=institution_id, limit=limit_works)
        works = raw.get("works") or []

    if not works:
        # Intento final con CoAuthra si hay algún autor o query
        fallback_target = academic_name or author_id or query
        if fallback_target:
            coauthra_res = openalex_plot_coauthra_network(
                academic_name=fallback_target,
                author_id=author_id,
                title=title,
                output_dir=output_dir
            )
            if coauthra_res.get("status") == "success":
                return coauthra_res
        return {"status": "error", "message": "No hay publicaciones suficientes para construir la red de coautoría."}

    title_text = title or "Red Interactiva de Colaboración Científica"
    html_path, _ = _resolve_output_paths(output_dir, "collaboration_network")

    if Network is None:
        return {"status": "error", "message": "Librería pyvis no instalada."}

    net = Network(height="680px", width="100%", bgcolor=THEME_CARD, font_color=THEME_TEXT)
    net.force_atlas_2based()

    node_weights = {}
    edges = {}
    for w in works:
        authors = w.get("author_names", [])
        if not authors:
            continue
        for a in authors[:8]:
            node_weights[a] = node_weights.get(a, 0) + 1
        for i in range(len(authors[:8])):
            for j in range(i + 1, len(authors[:8])):
                pair = tuple(sorted([authors[i], authors[j]]))
                edges[pair] = edges.get(pair, 0) + 1

    top_nodes = sorted(node_weights.items(), key=lambda x: x[1], reverse=True)[:45]
    top_node_names = set(n[0] for n in top_nodes)

    for name, weight in top_nodes:
        net.add_node(name, label=name, value=weight, color="#38BDF8")

    for (u, v), weight in edges.items():
        if u in top_node_names and v in top_node_names:
            net.add_edge(u, v, value=weight, color="rgba(148, 163, 184, 0.4)")

    net_html = net.generate_html()
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(net_html)

    return _build_viz_result(
        chart_type="network",
        title=title_text,
        html_path=html_path,
        png_path="",
        summary_kpis={
            "nodes_count": len(top_nodes),
            "edges_count": len(edges)
        },
        message=f"Red interactiva de colaboración guardada en {html_path}"
    )


# ==============================================================================
# 8. RENDERIZADOR UNIVERSAL DESDE JSON (Auto-detect)
# ==============================================================================
def openalex_render_visualization_from_json(
    json_path_or_data: Union[str, Dict[str, Any]],
    chart_type: str = "auto",
    title: str = "",
    output_dir: str = "./reports"
) -> Dict[str, Any]:
    """
    Renderizador inteligente auto-detect que recibe la ruta a un archivo JSON o diccionario de datos
    producido por cualquier consulta de OpenAlex y genera automáticamente el artefacto HTML + tarjeta PNG.
    """
    raw = _load_data(json_path_or_data)
    if not raw:
        return {"status": "error", "message": "No se pudieron cargar los datos JSON."}

    detected = chart_type.lower() if chart_type != "auto" else detect_data_type(raw)

    if detected == "timeseries":
        return openalex_plot_timeseries(data=raw, title=title, output_dir=output_dir)
    elif detected == "oa-donut":
        return openalex_plot_oa_donut(data=raw, title=title, output_dir=output_dir)
    elif detected in ("top-ranking", "authors-ranking"):
        return openalex_plot_top_ranking(data=raw, title=title, output_dir=output_dir)
    elif detected == "sunburst":
        return openalex_plot_sunburst(data=raw, title=title, output_dir=output_dir)
    elif detected == "sdg-grid":
        return openalex_plot_sdg_grid(data=raw, title=title, output_dir=output_dir)
    elif detected == "dossier-works":
        return openalex_plot_dossier_works(data=raw, title=title, output_dir=output_dir)
    elif detected == "network":
        return openalex_plot_collaboration_network(data=raw, title=title, output_dir=output_dir)
    else:
        if "top_entities" in raw:
            return openalex_plot_top_ranking(data=raw, title=title, output_dir=output_dir)
        elif "works" in raw:
            return openalex_plot_dossier_works(data=raw, title=title, output_dir=output_dir)
        else:
            return {"status": "error", "message": f"Estructura de datos no reconocida para auto-renderizado: {list(raw.keys())}"}


# ==============================================================================
# 9. MATRIZ DE CUADRANTES VOLUMEN VS. IMPACTO (Matriz BCG Cienciométrica)
# ==============================================================================
def openalex_plot_quadrant_matrix(
    data: Optional[Union[Dict[str, Any], str]] = None,
    by: str = "authors",
    query: str = "",
    limit: int = 30,
    title: str = "",
    output_dir: str = "./reports"
) -> Dict[str, Any]:
    """
    Gráfico de dispersión 2D interactivo clasificado en 4 cuadrantes cienciométricos:
    I. Líderes Consolidados (Alto Volumen, Alto FWCI)
    II. Nichos de Excelencia (Volumen Moderado, Alto FWCI)
    III. En Desarrollo / Emergentes (Volumen Moderado, FWCI < 1.0)
    IV. Producción Extensiva (Alto Volumen, FWCI < 1.0)
    """
    raw = _load_data(data)
    if not raw or "top_entities" not in raw:
        raw = openalex_top_entities(by=by, query=query, limit=limit)

    entities = raw.get("top_entities", [])
    if not entities:
        return {"status": "error", "message": "No se encontraron entidades para generar la matriz de cuadrantes."}

    names = [e.get("display_name") or e.get("institution") or "Entidad" for e in entities]
    works = [int(e.get("total_works", 0)) for e in entities]
    fwci = [round(float(e.get("avg_fwci", 1.0) or 1.0), 2) for e in entities]
    cites = [int(e.get("total_citations", 0)) for e in entities]

    median_works = float(sorted(works)[len(works)//2]) if works else 10.0
    title_text = title or f"Matriz de Cuadrantes Volumen vs. Impacto: {by.capitalize()} en '{query or 'Producción Científica'}'"
    html_path, png_path = _resolve_output_paths(output_dir, "quadrant_matrix")

    max_cites = max(cites) if cites and max(cites) > 0 else 1
    sizes = [max(12, min(42, int((c / max_cites) * 38 + 12))) for c in cites]

    hover_texts = [
        f"<b>{n}</b><br>Publicaciones: {w:,}<br>FWCI Promedio: {f:.2f}<br>Citas Acumuladas: {c:,}"
        for n, w, f, c in zip(names, works, fwci, cites)
    ]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=works,
        y=fwci,
        mode="markers+text",
        text=[n[:16] for n in names],
        textposition="top center",
        textfont=dict(size=9, color="#94A3B8"),
        marker=dict(
            size=sizes,
            color=fwci,
            colorscale="Viridis",
            colorbar=dict(title="FWCI Promedio"),
            showscale=True,
            line=dict(width=1, color="#38BDF8")
        ),
        hovertext=hover_texts,
        hoverinfo="text"
    ))

    fig.add_hline(y=1.0, line_dash="dash", line_color="#EF4444", annotation_text="Benchmark Mundial FWCI = 1.00")
    fig.add_vline(x=median_works, line_dash="dot", line_color="#64748B", annotation_text=f"Mediana Producción ({int(median_works):,} docs)")

    max_x = max(works) * 1.05 if works else 100
    max_y = max(max(fwci) * 1.08, 2.2) if fwci else 2.5

    fig.add_annotation(x=max_x, y=max_y, text="<b>I. LÍDERES CONSOLIDADOS</b><br>(Alto Volumen, Alto Impacto)", showarrow=False, font=dict(color="#10B981", size=10), xanchor="right")
    fig.add_annotation(x=min(works) if works else 1, y=max_y, text="<b>II. NICHOS DE EXCELENCIA</b><br>(Volumen Focalizado, Alto FWCI)", showarrow=False, font=dict(color="#38BDF8", size=10), xanchor="left")
    fig.add_annotation(x=min(works) if works else 1, y=0.3, text="<b>III. EN DESARROLLO</b><br>(Emergentes)", showarrow=False, font=dict(color="#F59E0B", size=10), xanchor="left")
    fig.add_annotation(x=max_x, y=0.3, text="<b>IV. PRODUCCIÓN EXTENSIVA</b><br>(Alto Volumen, Impacto Local)", showarrow=False, font=dict(color="#A855F7", size=10), xanchor="right")

    fig.update_layout(
        title=f"<b>{title_text}</b>",
        xaxis_title="Publicaciones Acumuladas (Volumen)",
        yaxis_title="FWCI Normalizado (Impacto Mundial)",
        template="plotly_dark",
        height=580,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,24,39,0.7)"
    )
    plot_html = _compact_plotly_html(fig)

    high_fwci_count = sum(1 for f in fwci if f >= 1.0)
    top_fwci_entity = entities[fwci.index(max(fwci))].get("display_name") or entities[fwci.index(max(fwci))].get("institution") if fwci else ""
    top_volume_entity = entities[works.index(max(works))].get("display_name") or entities[works.index(max(works))].get("institution") if works else ""

    full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{title_text}</title>
    <style>{_get_embedded_styles()}</style>
</head>
<body class="bg-dark text-gray-100">
    <div class="container mx-auto p-6 max-w-6xl">
        <header class="header-card mb-6">
            <span class="tag">OpenAlex México · Matriz Cienciométrica BCG</span>
            <h1 class="text-2xl font-black text-white mt-1">{title_text}</h1>
            <div class="grid grid-cols-4 gap-4 mt-4">
                <div class="kpi-mini">
                    <span class="kpi-label">Entidades Analizadas</span>
                    <span class="kpi-val">{len(entities)}</span>
                </div>
                <div class="kpi-mini">
                    <span class="kpi-label">Sobre Media Mundial (FWCI ≥ 1.0)</span>
                    <span class="kpi-val text-emerald-400">{high_fwci_count} ({round(high_fwci_count/len(entities)*100,1)}%)</span>
                </div>
                <div class="kpi-mini">
                    <span class="kpi-label">Líder en Impacto (FWCI)</span>
                    <span class="kpi-val text-sky-400 text-sm truncate" title="{top_fwci_entity}">{top_fwci_entity[:20]}</span>
                </div>
                <div class="kpi-mini">
                    <span class="kpi-label">Líder en Volumen</span>
                    <span class="kpi-val text-amber-400 text-sm truncate" title="{top_volume_entity}">{top_volume_entity[:20]}</span>
                </div>
            </div>
        </header>
        <section class="card mb-6">
            {plot_html}
        </section>
    </div>
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    _render_png_card("quadrant", raw, png_path, title_text)

    return _build_viz_result(
        chart_type="quadrant-matrix",
        title=title_text,
        html_path=html_path,
        png_path=png_path,
        summary_kpis={
            "entities_count": len(entities),
            "high_fwci_count": high_fwci_count,
            "top_fwci_entity": top_fwci_entity,
            "top_volume_entity": top_volume_entity
        },
        message=f"Matriz de cuadrantes guardada en {html_path}"
    )


# ==============================================================================
# 10. DIAGRAMA SANKEY DE FLUJO GEOPOLÍTICO DE COAUTORÍA
# ==============================================================================
def openalex_plot_geopolitical_sankey(
    data: Optional[Union[Dict[str, Any], str]] = None,
    institution_id: str = "",
    author_id: str = "",
    query: str = "",
    title: str = "",
    output_dir: str = "./reports"
) -> Dict[str, Any]:
    """
    Diagrama de Sankey interactivo que conecta la producción científica de México (o institución)
    con los bloques regionales globales y los principales países copartícipes en coautoría internacional.
    """
    raw = _load_data(data)
    country_counts = {}

    if raw and "country_counts" in raw:
        country_counts = raw["country_counts"]
    else:
        where_conds = ["has(all_country_codes, 'MX')", "publication_year >= 2020"]
        if institution_id:
            where_conds.append(f"(has(institution_rors, '{institution_id}') OR has(institution_ids, '{institution_id}') OR has(institution_names, '{institution_id}'))")
        if query:
            where_conds.append(f"(ilike(title, '%{query}%') OR ilike(subfield, '%{query}%'))")

        where_clause = " AND ".join(where_conds)
        sql = f"""
        SELECT 
            c as country_code,
            count(*) as total_works
        FROM (
            SELECT arrayJoin(all_country_codes) as c
            FROM rag.works_academic_all
            WHERE {where_clause}
            LIMIT 15000
        )
        WHERE c != 'MX' AND c != ''
        GROUP BY country_code
        ORDER BY total_works DESC
        LIMIT 15
        """
        ch_res = execute_safe_query(sql)
        for r in ch_res.get("data", []):
            country_counts[r["country_code"]] = int(r["total_works"])

    if not country_counts:
        return {"status": "error", "message": "No se encontraron datos de coautoría internacional para graficar el flujo."}

    source_label = "México (Nacional)" if not institution_id else "Institución"
    blocks_counts = {}
    country_to_block = {}
    for ccode, cnt in country_counts.items():
        assigned = "Resto del Mundo"
        for bname, codes in REGIONAL_BLOCKS.items():
            if ccode in codes:
                assigned = bname
                break
        blocks_counts[assigned] = blocks_counts.get(assigned, 0) + cnt
        country_to_block[ccode] = assigned

    block_names = list(blocks_counts.keys())
    country_list = list(country_counts.keys())

    node_labels = [source_label] + block_names + [COUNTRY_NAMES.get(c, c) for c in country_list]
    sources = []
    targets = []
    values = []

    for i, b in enumerate(block_names, 1):
        sources.append(0)
        targets.append(i)
        values.append(blocks_counts[b])

    block_offset = 1
    country_offset = 1 + len(block_names)
    for j, ccode in enumerate(country_list):
        bname = country_to_block[ccode]
        b_idx = block_offset + block_names.index(bname)
        c_idx = country_offset + j
        sources.append(b_idx)
        targets.append(c_idx)
        values.append(country_counts[ccode])

    title_text = title or f"Flujo Geopolítico de Coautoría Internacional ({source_label})"
    html_path, png_path = _resolve_output_paths(output_dir, "geopolitical_sankey")

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=18,
            line=dict(color="#1E293B", width=0.5),
            label=node_labels,
            color="#38BDF8"
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color="rgba(56, 189, 248, 0.25)"
        )
    )])

    fig.update_layout(
        title=f"<b>{title_text}</b>",
        font_size=11,
        template="plotly_dark",
        height=540,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,24,39,0.7)"
    )
    plot_html = _compact_plotly_html(fig)

    tot_intl_collab = sum(country_counts.values())
    top_partner = COUNTRY_NAMES.get(country_list[0], country_list[0]) if country_list else ""
    top_block = sorted(blocks_counts.items(), key=lambda x: x[1], reverse=True)[0][0] if blocks_counts else ""

    full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{title_text}</title>
    <style>{_get_embedded_styles()}</style>
</head>
<body class="bg-dark text-gray-100">
    <div class="container mx-auto p-6 max-w-6xl">
        <header class="header-card mb-6">
            <span class="tag">OpenAlex México · Cartografía Geopolítica</span>
            <h1 class="text-2xl font-black text-white mt-1">{title_text}</h1>
            <div class="grid grid-cols-3 gap-4 mt-4">
                <div class="kpi-mini">
                    <span class="kpi-label">Países Socios Detectados</span>
                    <span class="kpi-val">{len(country_counts)}</span>
                </div>
                <div class="kpi-mini">
                    <span class="kpi-label">Bloque Regional Principal</span>
                    <span class="kpi-val text-emerald-400">{top_block}</span>
                </div>
                <div class="kpi-mini">
                    <span class="kpi-label">País Aliado Líder</span>
                    <span class="kpi-val text-sky-400">{top_partner}</span>
                </div>
            </div>
        </header>
        <section class="card mb-6">
            {plot_html}
        </section>
    </div>
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    return _build_viz_result(
        chart_type="geopolitical-sankey",
        title=title_text,
        html_path=html_path,
        png_path="",
        summary_kpis={
            "partner_countries_count": len(country_counts),
            "top_block": top_block,
            "top_partner": top_partner,
            "total_international_collaborations": tot_intl_collab
        },
        message=f"Diagrama de flujo geopolítico guardado en {html_path}"
    )


# ==============================================================================
# 11. RADAR CIENCIOMÉTRICO MULTIDIMENSIONAL (Huella Institucional)
# ==============================================================================
def openalex_plot_multidimensional_radar(
    institutions_or_entities: Optional[List[str]] = None,
    data: Optional[Union[Dict[str, Any], str]] = None,
    title: str = "",
    output_dir: str = "./reports"
) -> Dict[str, Any]:
    """
    Gráfico de radar / araña interactivo que compara hasta 3 instituciones en 6 dimensiones
    cienciométricas normalizadas (Excelencia, Liderazgo, Internacionalización, Soberanía Diamante,
    Diversidad Temática, e Impacto FWCI).
    """
    targets = institutions_or_entities or ["Universidad Veracruzana", "Universidad Nacional Autónoma de México"]
    dimensions = [
        "Excelencia (% Top 10%)",
        "Liderazgo (% Doméstico)",
        "Internacionalización",
        "Soberanía Diamante",
        "Diversidad Temática",
        "Impacto Relativo (FWCI)",
        "Excelencia (% Top 10%)"
    ]

    fig = go.Figure()
    palette = ["#38BDF8", "#10B981", "#F59E0B"]
    summary_data = []

    for idx, inst in enumerate(targets[:3]):
        sql = f"""
        SELECT 
            count(*) as total_works,
            round(countIf(is_top_10 = 1) / count(*) * 100, 2) as pct_top_10,
            round(countIf(length(all_country_codes) = 1) / count(*) * 100, 2) as pct_domestic,
            round(countIf(length(all_country_codes) > 1) / count(*) * 100, 2) as pct_international,
            round(countIf(lower(oa_status) = 'diamond') / count(*) * 100, 2) as pct_diamond,
            round(avg(fwci), 2) as avg_fwci,
            uniqExact(subfield) as unique_subfields
        FROM rag.works_academic_all
        WHERE (has(institution_names, '{inst}') OR has(institution_rors, '{inst}')) AND publication_year >= 2018
        """
        ch_res = execute_safe_query(sql)
        row = ch_res.get("data", [{}])[0] if ch_res.get("data") else {}

        p_t10 = float(row.get("pct_top_10", 0.0) or 0.0)
        p_dom = float(row.get("pct_domestic", 0.0) or 0.0)
        p_int = float(row.get("pct_international", 0.0) or 0.0)
        p_dia = float(row.get("pct_diamond", 0.0) or 0.0)
        u_sub = float(row.get("unique_subfields", 0) or 0)
        div_score = min(100.0, round((u_sub / 250.0) * 100.0, 1))
        f_val = float(row.get("avg_fwci", 1.0) or 1.0)
        fwci_score = min(100.0, round(f_val * 50.0, 1))

        values = [p_t10, p_dom, p_int, p_dia, div_score, fwci_score, p_t10]
        color = palette[idx % len(palette)]

        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=dimensions,
            fill="toself",
            name=inst,
            line=dict(color=color, width=2)
        ))

        summary_data.append({
            "institution": inst,
            "total_works": row.get("total_works", 0),
            "pct_top_10": p_t10,
            "pct_domestic": p_dom,
            "pct_international": p_int,
            "pct_diamond": p_dia,
            "avg_fwci": f_val
        })

    title_text = title or "Huella Cienciométrica Multidimensional Institucional"
    html_path, png_path = _resolve_output_paths(output_dir, "multidimensional_radar")

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="#334155"),
            angularaxis=dict(gridcolor="#334155")
        ),
        template="plotly_dark",
        height=540,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,24,39,0.7)",
        showlegend=True
    )
    plot_html = _compact_plotly_html(fig)

    table_rows = []
    for s in summary_data:
        table_rows.append(f"""
        <tr>
            <td class="font-bold text-sky-400">{s['institution']}</td>
            <td class="text-right">{s['total_works']:,}</td>
            <td class="text-right font-mono text-emerald-400">{s['pct_top_10']}%</td>
            <td class="text-right font-mono">{s['pct_domestic']}%</td>
            <td class="text-right font-mono">{s['pct_international']}%</td>
            <td class="text-right font-mono text-amber-400">{s['pct_diamond']}%</td>
            <td class="text-right font-bold text-white">{s['avg_fwci']:.2f}</td>
        </tr>
        """)

    full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{title_text}</title>
    <style>{_get_embedded_styles()}</style>
</head>
<body class="bg-dark text-gray-100">
    <div class="container mx-auto p-6 max-w-6xl">
        <header class="header-card mb-6">
            <span class="tag">OpenAlex México · Huella Digital de Desempeño</span>
            <h1 class="text-2xl font-black text-white mt-1">{title_text}</h1>
        </header>
        <section class="card mb-6">
            {plot_html}
        </section>
        <section class="card">
            <h2 class="text-lg font-bold text-white mb-4">Tabla Comparativa de Indicadores</h2>
            <div class="overflow-x-auto">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Institución</th>
                            <th class="text-right">Publicaciones</th>
                            <th class="text-right">% Top 10%</th>
                            <th class="text-right">% Liderazgo</th>
                            <th class="text-right">% Internacional</th>
                            <th class="text-right">% Diamante</th>
                            <th class="text-right">FWCI</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(table_rows)}
                    </tbody>
                </table>
            </div>
        </section>
    </div>
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    return _build_viz_result(
        chart_type="multidimensional-radar",
        title=title_text,
        html_path=html_path,
        png_path="",
        summary_kpis={
            "institutions_compared": len(summary_data),
            "metrics": summary_data
        },
        message=f"Radar multidimensional guardado en {html_path}"
    )


# ==============================================================================
# 12. DINÁMICA TEMPORAL DE TÓPICOS / STREAMGRAPH DE LÍNEAS DE INVESTIGACIÓN
# ==============================================================================
def openalex_plot_topic_dynamics(
    institution_id: str = "",
    author_id: Union[str, List[str]] = "",
    query: str = "",
    top_n_topics: int = 8,
    start_year: int = 2014,
    end_year: int = 2026,
    title: str = "",
    output_dir: str = "./reports"
) -> Dict[str, Any]:
    """
    Gráfico de áreas apiladas / Streamgraph temporal que ilustra la evolución y maduración
    de las líneas de investigación prioritarias a lo largo de una ventana de 12-15 años.
    """
    where_conds = [f"publication_year >= {start_year}", f"publication_year <= {end_year}", "subfield != ''"]
    if institution_id:
        where_conds.append(f"(has(institution_names, '{institution_id}') OR has(institution_rors, '{institution_id}'))")
    aids = normalize_author_ids(author_id)
    if aids:
        where_conds.append(build_authors_condition(aids))
    if query:
        where_conds.append(f"ilike(title, '%{query}%')")

    where_clause = " AND ".join(where_conds)

    sql_top = f"""
    SELECT subfield, count(*) as total
    FROM rag.works_academic_all
    WHERE {where_clause}
    GROUP BY subfield
    ORDER BY total DESC
    LIMIT {top_n_topics}
    """
    ch_top = execute_safe_query(sql_top)
    top_subfields = [r["subfield"] for r in ch_top.get("data", [])]

    if not top_subfields:
        return {"status": "error", "message": "No se encontraron subcampos para generar la dinámica temporal."}

    subfields_str = ", ".join([f"'{s}'" for s in top_subfields])
    sql_dyn = f"""
    SELECT subfield, publication_year, count(*) as works
    FROM rag.works_academic_all
    WHERE {where_clause} AND subfield IN ({subfields_str})
    GROUP BY subfield, publication_year
    ORDER BY publication_year ASC
    """
    ch_dyn = execute_safe_query(sql_dyn)
    rows = ch_dyn.get("data", [])

    df = pd.DataFrame(rows)
    all_years = list(range(start_year, end_year + 1))
    title_text = title or f"Dinámica Temporal de Líneas de Investigación ({start_year}-{end_year})"
    html_path, png_path = _resolve_output_paths(output_dir, "topic_dynamics")

    fig = go.Figure()
    palette = px.colors.qualitative.Plotly + px.colors.qualitative.Bold

    for idx, sub in enumerate(top_subfields):
        sub_df = df[df["subfield"] == sub]
        year_map = dict(zip(sub_df["publication_year"], sub_df["works"]))
        y_vals = [year_map.get(y, 0) for y in all_years]
        color = palette[idx % len(palette)]

        fig.add_trace(go.Scatter(
            x=all_years,
            y=y_vals,
            mode="lines",
            line=dict(width=0.5, color=color),
            stackgroup="one",
            name=sub,
            hoverinfo="x+y+name"
        ))

    fig.update_layout(
        title=f"<b>{title_text}</b>",
        xaxis_title="Año de Publicación",
        yaxis_title="Artículos Anuales por Subcampo",
        template="plotly_dark",
        height=540,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17,24,39,0.7)",
        legend=dict(orientation="h", y=-0.2)
    )
    plot_html = _compact_plotly_html(fig)

    full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{title_text}</title>
    <style>{_get_embedded_styles()}</style>
</head>
<body class="bg-dark text-gray-100">
    <div class="container mx-auto p-6 max-w-6xl">
        <header class="header-card mb-6">
            <span class="tag">OpenAlex México · Evolución Temática</span>
            <h1 class="text-2xl font-black text-white mt-1">{title_text}</h1>
            <div class="grid grid-cols-3 gap-4 mt-4">
                <div class="kpi-mini">
                    <span class="kpi-label">Subcampo Líder</span>
                    <span class="kpi-val text-sky-400 text-sm truncate">{top_subfields[0]}</span>
                </div>
                <div class="kpi-mini">
                    <span class="kpi-label">Subcampos Monitoreados</span>
                    <span class="kpi-val text-emerald-400">{len(top_subfields)}</span>
                </div>
                <div class="kpi-mini">
                    <span class="kpi-label">Ventana Temporal</span>
                    <span class="kpi-val">{start_year} - {end_year}</span>
                </div>
            </div>
        </header>
        <section class="card mb-6">
            {plot_html}
        </section>
    </div>
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    return _build_viz_result(
        chart_type="topic-dynamics",
        title=title_text,
        html_path=html_path,
        png_path="",
        summary_kpis={
            "top_subfield": top_subfields[0],
            "subfields_tracked": len(top_subfields),
            "period": f"{start_year}-{end_year}"
        },
        message=f"Dinámica temporal de tópicos guardada en {html_path}"
    )


# ==============================================================================
# DICCIONARIOS DE APOYO GEOGRÁFICO (ISO2 -> ISO3 Y NOMBRES EN ESPAÑOL)
# ==============================================================================
ISO2_TO_ISO3 = {
    "AF": "AFG", "AX": "ALA", "AL": "ALB", "DZ": "DZA", "AS": "ASM", "AD": "AND", "AO": "AGO", "AI": "AIA", "AQ": "ATA", "AG": "ATG",
    "AR": "ARG", "AM": "ARM", "AW": "ABW", "AU": "AUS", "AT": "AUT", "AZ": "AZE", "BS": "BHS", "BH": "BHR", "BD": "BGD", "BB": "BRB",
    "BY": "BLR", "BE": "BEL", "BZ": "BLZ", "BJ": "BEN", "BM": "BMU", "BT": "BTN", "BO": "BOL", "BQ": "BES", "BA": "BIH", "BW": "BWA",
    "BV": "BVT", "BR": "BRA", "IO": "IOT", "BN": "BRN", "BG": "BGR", "BF": "BFA", "BI": "BDI", "CV": "CPV", "KH": "KHM", "CM": "CMR",
    "CA": "CAN", "KY": "CYM", "CF": "CAF", "TD": "TCD", "CL": "CHL", "CN": "CHN", "CX": "CXR", "CC": "CCK", "CO": "COL", "KM": "COM",
    "CD": "COD", "CG": "COG", "CK": "COK", "CR": "CRI", "CI": "CIV", "HR": "HRV", "CU": "CUB", "CW": "CUW", "CY": "CYP", "CZ": "CZE",
    "DK": "DNK", "DJ": "DJI", "DM": "DMA", "DO": "DOM", "EC": "ECU", "EG": "EGY", "SV": "SLV", "GQ": "GNQ", "ER": "ERI", "EE": "EST",
    "SZ": "SWZ", "ET": "ETH", "FK": "FLK", "FO": "FRO", "FJ": "FJI", "FI": "FIN", "FR": "FRA", "GF": "GUF", "PF": "PYF", "TF": "ATF",
    "GA": "GAB", "GM": "GMB", "GE": "GEO", "DE": "DEU", "GH": "GHA", "GI": "GIB", "GR": "GRC", "GL": "GRL", "GD": "GRD", "GP": "GLP",
    "GU": "GUM", "GT": "GTM", "GG": "GGY", "GN": "GIN", "GW": "GNB", "GY": "GUY", "HT": "HTI", "HM": "HMD", "VA": "VAT", "HN": "HND",
    "HK": "HKG", "HU": "HUN", "IS": "ISL", "IN": "IND", "ID": "IDN", "IR": "IRN", "IQ": "IRQ", "IE": "IRL", "IM": "IMN", "IL": "ISR",
    "IT": "ITA", "JM": "JAM", "JP": "JPN", "JE": "JEY", "JO": "JOR", "KZ": "KAZ", "KE": "KEN", "KI": "KIR", "KP": "PRK", "KR": "KOR",
    "KW": "KWT", "KG": "KGZ", "LA": "LAO", "LV": "LVA", "LB": "LBN", "LS": "LSO", "LR": "LBR", "LY": "LBY", "LI": "LIE", "LT": "LTU",
    "LU": "LUX", "MO": "MAC", "MG": "MDG", "MW": "MWI", "MY": "MYS", "MV": "MDV", "ML": "MLI", "MT": "MLT", "MH": "MHL", "MQ": "MTQ",
    "MR": "MRT", "MU": "MUS", "YT": "MYT", "MX": "MEX", "FM": "FSM", "MD": "MDA", "MC": "MCO", "MN": "MNG", "ME": "MNE", "MS": "MSR",
    "MA": "MAR", "MZ": "MOZ", "MM": "MMR", "NA": "NAM", "NR": "NRU", "NP": "NPL", "NL": "NLD", "NC": "NCL", "NZ": "NZL", "NI": "NIC",
    "NE": "NER", "NG": "NGA", "NU": "NIU", "NF": "NFK", "MP": "MNP", "NO": "NOR", "OM": "OMN", "PK": "PAK", "PW": "PLW", "PS": "PSE",
    "PA": "PAN", "PG": "PNG", "PY": "PRY", "PE": "PER", "PH": "PHL", "PN": "PCN", "PL": "POL", "PT": "PRT", "PR": "PRI", "QA": "QAT",
    "RE": "REU", "RO": "ROU", "RU": "RUS", "RW": "RWA", "BL": "BLM", "SH": "SHN", "KN": "KNA", "LC": "LCA", "MF": "MAF", "PM": "SPM",
    "VC": "VCT", "WS": "WSM", "SM": "SMR", "ST": "STP", "SA": "SAU", "SN": "SEN", "RS": "SRB", "SC": "SYC", "SL": "SLE", "SG": "SGP",
    "SX": "SXM", "SK": "SVK", "SI": "SVN", "SB": "SLB", "SO": "SOM", "ZA": "ZAF", "GS": "SGS", "SS": "SSD", "ES": "ESP", "LK": "LKA",
    "SD": "SDN", "SR": "SUR", "SJ": "SJM", "SE": "SWE", "CH": "CHE", "SY": "SYR", "TW": "TWN", "TJ": "TJK", "TZ": "TZA", "TH": "THA",
    "TL": "TLS", "TG": "TGO", "TK": "TKL", "TO": "TON", "TT": "TTO", "TN": "TUN", "TR": "TUR", "TM": "TKM", "TC": "TCA", "TV": "TUV",
    "UG": "UGA", "UA": "UKR", "AE": "ARE", "GB": "GBR", "UM": "UMI", "US": "USA", "UY": "URY", "UZ": "UZB", "VU": "VUT", "VE": "VEN",
    "VN": "VNM", "VG": "VGB", "VI": "VIR", "WF": "WLF", "EH": "ESH", "YE": "YEM", "ZM": "ZMB", "ZW": "ZWE"
}

ISO2_TO_NAME_ES = {
    "US": "Estados Unidos", "ES": "España", "GB": "Reino Unido", "FR": "Francia", "DE": "Alemania",
    "BR": "Brasil", "CA": "Canadá", "IT": "Italia", "CN": "China", "CO": "Colombia", "CL": "Chile",
    "AR": "Argentina", "JP": "Japón", "NL": "Países Bajos", "CH": "Suiza", "AU": "Australia",
    "SE": "Suecia", "BE": "Bélgica", "PT": "Portugal", "CU": "Cuba", "PE": "Perú", "IN": "India",
    "KR": "Corea del Sur", "RU": "Rusia", "IL": "Israel", "PL": "Polonia", "DK": "Dinamarca",
    "NO": "Noruega", "AT": "Austria", "ZA": "Sudáfrica", "NZ": "Nueva Zelanda", "CR": "Costa Rica",
    "EC": "Ecuador", "UY": "Uruguay", "VE": "Venezuela", "GT": "Guatemala", "PA": "Panamá",
    "IE": "Irlanda", "FI": "Finlandia", "CZ": "República Checa", "GR": "Grecia", "TR": "Turquía",
    "SG": "Singapur", "TW": "Taiwán", "MY": "Malasia", "SA": "Arabia Saudita", "EG": "Egipto"
}


# ==============================================================================
# 13. MAPA MUNDIAL DE PAÍSES COLABORADORES (Choropleth Colaboración Internacional)
# ==============================================================================
def openalex_plot_collaborating_countries(
    author_id: Optional[Union[str, List[str]]] = None,
    orcid: Optional[str] = None,
    academic_name: Optional[str] = None,
    institution_id: Optional[str] = None,
    query: Optional[str] = None,
    title: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Genera un Mapa Mundial Coroplético interactivo (Plotly.js) que muestra la
    distribución geográfica de las naciones aliadas en coautoría científica.
    Excluye a México para resaltar los vínculos internacionales.
    """
    conds = ["length(all_country_codes) > 0"]
    entity_label = "Producción Científica Nacional"

    aids = normalize_author_ids(author_id)
    if aids:
        conds.append(build_authors_condition(aids))
        entity_label = f"Investigador ({', '.join(aids)})"
    elif orcid:
        clean_orc = orcid.replace("https://orcid.org/", "").strip()
        q_orc = f"SELECT name FROM rag.academics_all WHERE orcid = '{clean_orc}' LIMIT 1"
        res_orc = execute_safe_query(q_orc)
        if res_orc.get("data"):
            aname = res_orc["data"][0]["name"]
            conds.append(f"arrayExists(x -> x ILIKE '%{aname}%', author_names)")
            entity_label = f"{aname} (ORCID: {clean_orc})"
        else:
            entity_label = f"ORCID: {clean_orc}"
    elif academic_name:
        clean_name = academic_name.replace("'", "").strip()
        toks = [t.strip() for t in clean_name.replace(",", " ").split() if len(t.strip()) >= 2]
        if len(toks) > 1:
            t_cond = " AND ".join([f"x ILIKE '%{t}%'" for t in toks])
            conds.append(f"arrayExists(x -> ({t_cond}), author_names)")
        else:
            conds.append(f"arrayExists(x -> x ILIKE '%{clean_name}%', author_names)")
        entity_label = f"{clean_name}"
    elif institution_id:
        clean_inst = institution_id.replace("https://ror.org/", "").strip()
        conds.append(f"(arrayExists(x -> x ILIKE '%{clean_inst}%', institution_names) OR arrayExists(x -> x ILIKE '%{clean_inst}%', institution_rors))")
        entity_label = f"Institución ({clean_inst})"
    elif query:
        clean_q = query.replace("'", "").strip()
        conds.append(f"(title ILIKE '%{clean_q}%' OR topic ILIKE '%{clean_q}%')")
        entity_label = f"Tópico '{clean_q}'"

    where_str = " AND ".join(conds)
    sql = f"""
    SELECT arrayJoin(all_country_codes) AS country_code, count(*) AS papers
    FROM rag.works_academic_all
    WHERE {where_str} AND country_code != '' AND country_code != 'MX'
    GROUP BY country_code
    ORDER BY papers DESC
    LIMIT 120
    """
    ch_res = execute_safe_query(sql)
    rows = ch_res.get("data", [])

    if not rows:
        return {"status": "error", "message": f"No se detectaron países colaboradores internacionales para {entity_label}."}

    locations = []
    z_vals = []
    hover_texts = []
    table_rows = []
    total_papers_collab = 0

    for r in rows:
        c2 = r.get("country_code", "").upper().strip()
        papers = int(r.get("papers", 0))
        if not c2 or papers <= 0:
            continue
        c3 = ISO2_TO_ISO3.get(c2, c2)
        name_es = ISO2_TO_NAME_ES.get(c2, c2)
        locations.append(c3)
        z_vals.append(papers)
        hover_texts.append(f"<b>{name_es} ({c3})</b><br>{papers:,} artículos conjuntos")
        total_papers_collab += papers
        if len(table_rows) < 15:
            table_rows.append({"iso2": c2, "iso3": c3, "name": name_es, "papers": papers})

    title_text = title or f"Mapa Mundi de Países Colaboradores: {entity_label}"
    html_path, png_path = _resolve_output_paths(output_dir, "collaborating_countries")

    colorscale = [
        [0.0, "#0f172a"],
        [0.05, "#0369a1"],
        [0.2, "#0284c7"],
        [0.5, "#00f0ff"],
        [1.0, "#38bdf8"]
    ]

    fig = go.Figure(data=go.Choropleth(
        locations=locations,
        locationmode="ISO-3",
        z=z_vals,
        text=hover_texts,
        hoverinfo="text",
        colorscale=colorscale,
        autocolorscale=False,
        marker=dict(line=dict(color="rgba(255,255,255,0.18)", width=0.6)),
        colorbar=dict(
            title=dict(text="Papers", font=dict(color="#94a3b8", size=11)),
            tickfont=dict(color="#94a3b8", size=10),
            len=0.75,
            thickness=14
        )
    ))

    fig.update_layout(
        title=dict(
            text=f"<b>{title_text}</b>",
            font=dict(family="Inter, sans-serif", size=16, color=THEME_TEXT),
            x=0.03, y=0.96
        ),
        paper_bgcolor=THEME_CARD,
        plot_bgcolor=THEME_CARD,
        margin=dict(t=50, b=10, l=10, r=10),
        height=520,
        geo=dict(
            showframe=False,
            showcoastlines=True,
            coastlinecolor="rgba(255,255,255,0.15)",
            bgcolor="rgba(0,0,0,0)",
            showland=True,
            landcolor="rgba(255,255,255,0.03)",
            showocean=True,
            oceancolor="rgba(15,23,42,0.6)",
            projection=dict(type="natural earth")
        )
    )

    plot_html = _compact_plotly_html(fig)

    table_html = "".join([
        f"<tr><td class='py-2 font-mono text-cyan-400'>{r['iso3']}</td>"
        f"<td class='py-2 font-medium'>{r['name']}</td>"
        f"<td class='py-2 text-right font-bold text-white'>{r['papers']:,}</td>"
        f"<td class='py-2 text-right text-slate-400'>{round((r['papers']/total_papers_collab)*100, 1)}%</td></tr>"
        for r in table_rows
    ])

    top_country = table_rows[0]["name"] if table_rows else "N/A"
    top_papers = table_rows[0]["papers"] if table_rows else 0

    full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{title_text}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background-color: {THEME_BG}; color: {THEME_TEXT}; font-family: 'Inter', sans-serif; }}
        .card {{ background-color: {THEME_CARD}; border: 1px solid rgba(255,255,255,0.08); border-radius: 0.75rem; }}
    </style>
</head>
<body class="p-4 md:p-6">
    <div class="max-w-7xl mx-auto space-y-5">
        <header class="flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
            <div>
                <h1 class="text-xl font-bold flex items-center gap-2">
                    <span class="text-cyan-400">🗺️</span> {title_text}
                </h1>
                <p class="text-xs text-slate-400">Cartografía global de coautoría internacional ({len(locations)} naciones colaboradoras registradas).</p>
            </div>
            <div class="flex gap-2">
                <span class="px-3 py-1 bg-cyan-950 border border-cyan-800 text-cyan-300 rounded text-xs font-semibold">
                    {len(locations)} Países Aliados
                </span>
                <span class="px-3 py-1 bg-slate-800 border border-slate-700 text-slate-300 rounded text-xs font-semibold">
                    {total_papers_collab:,} Colaboraciones
                </span>
            </div>
        </header>

        <section class="card p-3 shadow-xl overflow-hidden">
            {plot_html}
        </section>

        <section class="card p-4">
            <h2 class="text-sm font-bold text-slate-200 mb-3 flex items-center gap-2">
                <span>🏆</span> Principales Naciones Socias de Coautoría
            </h2>
            <div class="overflow-x-auto">
                <table class="w-full text-xs text-left">
                    <thead>
                        <tr class="border-b border-slate-800 text-slate-400">
                            <th class="py-2">Código</th>
                            <th class="py-2">País</th>
                            <th class="py-2 text-right">Papers Conjuntos</th>
                            <th class="py-2 text-right">Participación (%)</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-850">
                        {table_html}
                    </tbody>
                </table>
            </div>
        </section>
    </div>
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    _render_png_card("collaboration-countries", {"locations": locations, "z": z_vals}, png_path, title_text)

    return _build_viz_result(
        chart_type="collaborating-countries",
        title=title_text,
        html_path=html_path,
        png_path=png_path,
        summary_kpis={
            "total_partner_countries": len(locations),
            "total_collaborations": total_papers_collab,
            "top_partner_country": top_country,
            "top_partner_papers": top_papers
        },
        message=f"Mapa mundi coroplético de países colaboradores guardado en {html_path}"
    )



# ==============================================================================
# 14. VOCABULARIO CIENTÍFICO (Nube Interactiva de Palabras y Frecuencias)
# ==============================================================================
def openalex_plot_scientific_vocabulary(
    author_id: Optional[Union[str, List[str]]] = None,
    orcid: Optional[str] = None,
    academic_name: Optional[str] = None,
    entity_name: Optional[str] = None,
    institution_id: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 80,
    title: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Genera una visualización interactiva del Vocabulario Científico (WordCloud y Frecuencias),
    inspirada en WordCloudInteractive.jsx de SinapsisAI.
    Soporta búsqueda en vivo, paleta neón por tiers de frecuencia y vista dual con gráfico de barras.
    """
    keywords_data = []
    source_label = "Producción Científica"

    # 1. Intentar consulta ultrarrápida a DuckDB de SinapsisAI si se especifica academic_name o entity_name
    duckdb_path = "/home/sinapsisai/data/analytics_cache.duckdb"
    if os.path.exists(duckdb_path) and (academic_name or entity_name):
        try:
            import duckdb
            dconn = duckdb.connect(duckdb_path, read_only=True)
            if academic_name:
                clean_aname = academic_name.replace("'", "").strip()
                d_res = dconn.execute(
                    f"SELECT keyword, freq FROM keywords_investigador WHERE academic_name ILIKE '%{clean_aname}%' ORDER BY freq DESC LIMIT {limit}"
                ).fetchall()
                if d_res:
                    keywords_data = [{"keyword": str(r[0]), "freq": int(r[1])} for r in d_res]
                    source_label = f"Investigador: {clean_aname}"
            elif entity_name:
                clean_ename = entity_name.replace("'", "").strip()
                d_res = dconn.execute(
                    f"SELECT keyword, freq FROM keywords_institucion WHERE entity_name ILIKE '%{clean_ename}%' ORDER BY freq DESC LIMIT {limit}"
                ).fetchall()
                if d_res:
                    keywords_data = [{"keyword": str(r[0]), "freq": int(r[1])} for r in d_res]
                    source_label = f"Dependencia: {clean_ename}"
            dconn.close()
        except Exception:
            pass

    # 2. Fallback a ClickHouse si no se obtuvo de DuckDB
    if not keywords_data:
        conds = ["length(keywords) > 0"]
        aids = normalize_author_ids(author_id)
        if aids:
            conds.append(build_authors_condition(aids))
            source_label = f"Investigador ({', '.join(aids)})"
        elif academic_name:
            clean_aname = academic_name.replace("'", "").strip()
            toks = [t.strip() for t in clean_aname.replace(",", " ").split() if len(t.strip()) >= 2]
            if len(toks) > 1:
                t_cond = " AND ".join([f"x ILIKE '%{t}%'" for t in toks])
                conds.append(f"arrayExists(x -> ({t_cond}), author_names)")
            else:
                conds.append(f"arrayExists(x -> x ILIKE '%{clean_aname}%', author_names)")
            source_label = f"Investigador: {clean_aname}"
        elif institution_id:
            clean_inst = institution_id.replace("https://ror.org/", "").strip()
            conds.append(f"(arrayExists(x -> x ILIKE '%{clean_inst}%', institution_names) OR arrayExists(x -> x ILIKE '%{clean_inst}%', institution_rors))")
            source_label = f"Institución ({clean_inst})"
        elif query:
            clean_q = query.replace("'", "").strip()
            conds.append(f"(title ILIKE '%{clean_q}%' OR topic ILIKE '%{clean_q}%')")
            source_label = f"Tópico '{clean_q}'"

        where_str = " AND ".join(conds)
        sql = f"""
        SELECT arrayJoin(keywords) AS keyword, count(*) AS freq
        FROM rag.works_academic_all
        WHERE {where_str} AND keyword != ''
        GROUP BY keyword
        ORDER BY freq DESC
        LIMIT {limit}
        """
        ch_res = execute_safe_query(sql)
        rows = ch_res.get("data", [])
        keywords_data = [{"keyword": str(r["keyword"]), "freq": int(r["freq"])} for r in rows if r.get("keyword")]

    if not keywords_data:
        return {"status": "error", "message": f"No se encontraron palabras clave registradas para {source_label}."}

    max_freq = max(k["freq"] for k in keywords_data) if keywords_data else 1
    total_occurrences = sum(k["freq"] for k in keywords_data)
    title_text = title or f"Vocabulario Científico: {source_label}"
    html_path, png_path = _resolve_output_paths(output_dir, "scientific_vocabulary")

    # Gráfica de barras complementaria Plotly (Top 25)
    top25 = keywords_data[:25]
    bar_y = [k["keyword"] for k in reversed(top25)]
    bar_x = [k["freq"] for k in reversed(top25)]

    fig = go.Figure(go.Bar(
        x=bar_x,
        y=bar_y,
        orientation="h",
        marker=dict(
            color=bar_x,
            colorscale=[[0, "#0369a1"], [0.5, "#00f0ff"], [1.0, "#38bdf8"]],
            line=dict(color="rgba(255,255,255,0.1)", width=0.5)
        ),
        text=[f"{v:,}" for v in bar_x],
        textposition="auto"
    ))
    fig.update_layout(
        title=dict(
            text="<b>Top 25 Términos por Frecuencia</b>",
            font=dict(family="Inter, sans-serif", size=14, color=THEME_TEXT),
            x=0.03
        ),
        paper_bgcolor=THEME_CARD,
        plot_bgcolor=THEME_CARD,
        height=480,
        margin=dict(t=40, b=20, l=150, r=30),
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)", color=THEME_MUTED),
        yaxis=dict(gridcolor="rgba(0,0,0,0)", color=THEME_TEXT)
    )
    bar_html = _compact_plotly_html(fig)

    words_json = json.dumps(keywords_data, ensure_ascii=False)

    full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{title_text}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background-color: {THEME_BG}; color: {THEME_TEXT}; font-family: 'Inter', sans-serif; }}
        .card {{ background-color: {THEME_CARD}; border: 1px solid rgba(255,255,255,0.08); border-radius: 0.75rem; }}
        .word-item {{
            display: inline-block;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
            border-radius: 0.375rem;
            padding: 0.2rem 0.5rem;
            margin: 0.25rem;
            user-select: none;
        }}
        .word-item:hover {{
            transform: scale(1.12);
            box-shadow: 0 0 16px rgba(0,240,255,0.4);
            z-index: 10;
        }}
    </style>
</head>
<body class="p-4 md:p-6">
    <div class="max-w-7xl mx-auto space-y-5">
        <header class="flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
            <div>
                <h1 class="text-xl font-bold flex items-center gap-2">
                    <span class="text-cyan-400">🔑</span> {title_text}
                </h1>
                <p class="text-xs text-slate-400">Nube de términos y conceptos clave extraídos de la producción científica ({len(keywords_data)} términos analizados).</p>
            </div>
            <div class="flex gap-2">
                <span class="px-3 py-1 bg-cyan-950 border border-cyan-800 text-cyan-300 rounded text-xs font-semibold">
                    {len(keywords_data)} Términos Únicos
                </span>
                <span class="px-3 py-1 bg-slate-800 border border-slate-700 text-slate-300 rounded text-xs font-semibold">
                    {total_occurrences:,} Ocurrencias Totales
                </span>
            </div>
        </header>

        <!-- Controles interactivos -->
        <div class="card p-3 flex flex-wrap gap-3 items-center justify-between">
            <div class="flex items-center gap-2 w-full md:w-80">
                <span class="text-slate-400 text-sm">🔍</span>
                <input id="wordSearch" type="text" placeholder="Filtrar términos en tiempo real..."
                       class="w-full bg-slate-900 border border-slate-750 text-xs text-slate-200 px-3 py-1.5 rounded focus:outline-none focus:border-cyan-400"
                       oninput="filterWords(this.value)">
            </div>
            <div class="flex items-center gap-2 text-xs text-slate-400">
                <span>Mostrar:</span>
                <button onclick="setWordLimit(40)" class="px-2 py-1 bg-slate-800 rounded hover:bg-slate-700 text-slate-300">40</button>
                <button onclick="setWordLimit(80)" class="px-2 py-1 bg-cyan-900 text-cyan-200 rounded font-bold">80</button>
                <button onclick="setWordLimit(150)" class="px-2 py-1 bg-slate-800 rounded hover:bg-slate-700 text-slate-300">Todos</button>
            </div>
        </div>

        <!-- Nube de Palabras Interactiva HTML5 -->
        <section class="card p-6 shadow-xl text-center leading-loose min-h-[340px] flex items-center justify-center flex-wrap" id="wordCloudBox">
            <!-- Palabras inyectadas dinámicamente -->
        </section>

        <!-- Gráfica de Barras Horizontal -->
        <section class="card p-3 shadow-xl">
            {bar_html}
        </section>
    </div>

    <script>
        const allWords = {words_json};
        const maxFreq = {max_freq};
        const totalOcc = {total_occurrences};
        let currentLimit = 80;
        let currentFilter = "";

        const COLOR_TIERS_DARK = [
            {{ threshold: 0.85, color: '#00f0ff', bg: 'rgba(0, 240, 255, 0.14)', weight: '800' }},
            {{ threshold: 0.65, color: '#38bdf8', bg: 'rgba(56, 189, 248, 0.12)', weight: '700' }},
            {{ threshold: 0.45, color: '#818cf8', bg: 'rgba(129, 140, 248, 0.10)', weight: '600' }},
            {{ threshold: 0.25, color: '#c084fc', bg: 'rgba(192, 132, 252, 0.10)', weight: '600' }},
            {{ threshold: 0.10, color: '#f472b6', bg: 'rgba(244, 114, 182, 0.08)', weight: '500' }},
            {{ threshold: 0.00, color: '#94a3b8', bg: 'rgba(148, 163, 184, 0.08)', weight: '500' }}
        ];

        function getTier(ratio) {{
            for (let t of COLOR_TIERS_DARK) {{
                if (ratio >= t.threshold) return t;
            }}
            return COLOR_TIERS_DARK[COLOR_TIERS_DARK.length - 1];
        }}

        function renderCloud() {{
            const box = document.getElementById('wordCloudBox');
            box.innerHTML = '';
            let filtered = allWords.filter(w => w.keyword.toLowerCase().includes(currentFilter.toLowerCase()));
            let visible = filtered.slice(0, currentLimit);

            if (visible.length === 0) {{
                box.innerHTML = '<span class="text-slate-500 text-sm">No se encontraron términos que coincidan con la búsqueda.</span>';
                return;
            }}

            visible.forEach(w => {{
                const ratio = maxFreq > 0 ? (w.freq / maxFreq) : 0.1;
                const tier = getTier(ratio);
                const fontSize = Math.max(12, Math.round(13 + Math.sqrt(ratio) * 26));

                const span = document.createElement('span');
                span.className = 'word-item';
                span.style.fontSize = fontSize + 'px';
                span.style.color = tier.color;
                span.style.backgroundColor = tier.bg;
                span.style.fontWeight = tier.weight;
                span.title = `${{w.keyword}}: ${{w.freq.toLocaleString()}} apariciones (${{((w.freq/totalOcc)*100).toFixed(1)}}%)`;
                span.innerText = w.keyword;
                box.appendChild(span);
            }});
        }}

        function filterWords(val) {{
            currentFilter = val;
            renderCloud();
        }}

        function setWordLimit(lim) {{
            currentLimit = lim;
            renderCloud();
        }}

        renderCloud();
    </script>
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    _render_png_card("scientific-vocabulary", {"keywords": keywords_data[:30]}, png_path, title_text)

    return _build_viz_result(
        chart_type="scientific-vocabulary",
        title=title_text,
        html_path=html_path,
        png_path=png_path,
        summary_kpis={
            "total_keywords_analyzed": len(keywords_data),
            "total_occurrences": total_occurrences,
            "top_keyword": keywords_data[0]["keyword"] if keywords_data else "",
            "top_keyword_freq": keywords_data[0]["freq"] if keywords_data else 0
        },
        message=f"Vocabulario científico interactivo guardado en {html_path}"
    )


# ==============================================================================
# 15. RED DE COLABORACIÓN CIENTÍFICA (Integración de CoAuthra vía ORCID / OpenAlex ID)
# ==============================================================================
def openalex_plot_coauthra_network(
    academic_name: Optional[str] = None,
    author_id: Optional[Union[str, List[str]]] = None,
    orcid: Optional[str] = None,
    query: Optional[str] = None,
    title: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    HERRAMIENTA PRINCIPAL PARA REDES DE COAUTORÍA DE INVESTIGADORES Y AUTORES INDIVIDUALES.
    Dibuja la red interactiva de colaboración científica y grafo de coautores de un investigador
    utilizando CoAuthra (física de fuerzas D3.js, comunidades y filtros por año y citas).
    Úsala siempre que el usuario pida 'red de colaboración de [investigador/autor]',
    'grafo de coautoría de [investigador]', 'colaboradores de [investigador]'.
    Acepta Nombre del investigador (ej. 'Annie Pardo'), OpenAlex ID (único o lista) o ORCID.
    """
    effective_name = academic_name or query or ""
    clean_id = ""
    display_name = effective_name or "Investigador"
    resolved_orcid = orcid or ""

    # 1. Si viene OpenAlex ID directo (único o lista)
    aids = normalize_author_ids(author_id)
    if aids:
        clean_id = aids[0]  # CoAuthra toma el ID principal para centrar la red
    # 2. Si viene ORCID
    elif orcid:
        clean_id = orcid.replace("https://orcid.org/", "").strip()
        resolved_orcid = clean_id
    # 3. Si viene nombre de académico (o query de persona), resolver en ClickHouse
    elif effective_name:
        clean_name = effective_name.replace("'", "").strip()
        sql_search = f"""
        SELECT id, name, orcid FROM rag.academics_all
        WHERE name ILIKE '%{clean_name}%'
        ORDER BY paper_count DESC
        LIMIT 1
        """
        res_ac = execute_safe_query(sql_search)
        if res_ac.get("data"):
            row = res_ac["data"][0]
            display_name = row.get("name") or clean_name
            resolved_orcid = row.get("orcid") or ""
            raw_id = row.get("id") or ""
            clean_id = raw_id.replace("https://openalex.org/", "").strip()
            if not clean_id and resolved_orcid:
                clean_id = resolved_orcid

    if not clean_id:
        return {
            "status": "error",
            "message": "Se requiere al menos author_id (OpenAlex ID, ej. A5012345678), orcid (ej. 0000-0002-1825-0097) o un academic_name resoluble para cargar CoAuthra."
        }

    coauthra_url = f"https://coauthra.com/?author={clean_id}"
    title_text = title or f"Red de Colaboración Científica: {display_name}"
    html_path, png_path = _resolve_output_paths(output_dir, "coauthra_network")

    badge_openalex = f"<span class='px-2.5 py-1 bg-cyan-950 border border-cyan-800 text-cyan-300 rounded text-xs font-mono font-semibold'>OpenAlex: {clean_id}</span>" if clean_id.startswith("A") else ""
    badge_orcid = f"<span class='px-2.5 py-1 bg-emerald-950 border border-emerald-800 text-emerald-300 rounded text-xs font-mono font-semibold'>ORCID: {resolved_orcid}</span>" if resolved_orcid else ""

    full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{title_text}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body, html {{ margin: 0; padding: 0; height: 100%; overflow: hidden; background-color: {THEME_BG}; color: {THEME_TEXT}; font-family: 'Inter', sans-serif; }}
        .header-bar {{ background-color: {THEME_CARD}; border-bottom: 1px solid rgba(255,255,255,0.08); }}
        iframe {{ width: 100%; height: calc(100vh - 86px); border: none; }}
    </style>
</head>
<body class="flex flex-col h-screen">
    <!-- Barra superior institucional estilo SinapsisAI -->
    <header class="header-bar px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 shrink-0">
        <div class="flex items-center gap-3">
            <span class="text-xl text-cyan-400">🕸️</span>
            <div>
                <h1 class="text-sm font-bold text-white leading-tight">{title_text}</h1>
                <p class="text-[11px] text-slate-400">Mapa dinámico de coautorías, agrupamiento de comunidades y autores puente.</p>
            </div>
            <div class="hidden sm:flex items-center gap-2 ml-2">
                {badge_openalex}
                {badge_orcid}
            </div>
        </div>
        <div class="flex items-center gap-3">
            <span class="text-[11px] text-slate-400 hidden lg:inline">
                Motor provisto por <strong class="text-slate-200">CoAuthra</strong> (Joe Barnier, CC BY-NC-ND 4.0)
            </span>
            <a href="{coauthra_url}" target="_blank" rel="noopener noreferrer"
               class="inline-flex items-center gap-1.5 px-3 py-1 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-xs rounded transition-all shadow-md">
                Abrir en CoAuthra.com ↗
            </a>
        </div>
    </header>

    <!-- Visor de CoAuthra con parámetro ?author= para carga directa inmediata -->
    <main class="flex-1 w-full bg-slate-950 relative">
        <iframe src="{coauthra_url}"
                allow="fullscreen"
                loading="eager"
                title="{title_text}">
        </iframe>
    </main>
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    _render_png_card("coauthra-network", {"author": clean_id, "name": display_name}, png_path, title_text)

    return _build_viz_result(
        chart_type="coauthra-network",
        title=title_text,
        html_path=html_path,
        png_path=png_path,
        summary_kpis={
            "author_id": clean_id,
            "display_name": display_name,
            "orcid": resolved_orcid,
            "coauthra_url": coauthra_url
        },
        message=f"Red interactiva CoAuthra lista y guardada en {html_path}"
    )
