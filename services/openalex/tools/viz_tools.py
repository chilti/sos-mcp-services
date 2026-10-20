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
    author_id: str = "",
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

    plot_html = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")
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

    return {
        "status": "success",
        "chart_type": "timeseries",
        "title": title_text,
        "html_path": html_path,
        "html_content": full_html,
        "png_path": png_path,
        "summary_kpis": {
            "period": f"{years[0]}-{years[-1]}",
            "total_works": tot_works,
            "total_citations": tot_cites,
            "avg_fwci": avg_fwci,
            "total_apc_usd": tot_apc
        },
        "message": f"Serie temporal interactiva guardada en {html_path}"
    }


# ==============================================================================
# 2. DONA DE ACCESO ABIERTO Y GASTO COMERCIAL EN APC
# ==============================================================================
def openalex_plot_oa_donut(
    data: Optional[Union[Dict[str, Any], str]] = None,
    institution_id: str = "",
    author_id: str = "",
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
    plot_html = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")

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

    return {
        "status": "success",
        "chart_type": "oa-donut",
        "title": title_text,
        "html_path": html_path,
        "html_content": full_html,
        "png_path": png_path,
        "summary_kpis": {
            "total_works": total_works,
            "diamond_works": diamond_works,
            "diamond_percentage": diamond_pct,
            "gold_apc_works": gold_works,
            "total_apc_paid_usd": total_apc
        },
        "message": f"Dona interactiva de Acceso Abierto guardada en {html_path}"
    }


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
    plot_html = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")

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

    return {
        "status": "success",
        "chart_type": "top-ranking",
        "title": title_text,
        "html_path": html_path,
        "html_content": full_html,
        "png_path": png_path,
        "summary_kpis": {
            "entity_count": len(entities),
            "top_entity": entities[0].get("display_name") or entities[0].get("institution") if entities else "",
            "max_works": entities[0].get("total_works", 0) if entities else 0
        },
        "message": f"Ranking interactivo guardado en {html_path}"
    }


# ==============================================================================
# 4. SUNBURST TAXONÓMICO JERÁRQUICO (Dominio -> Campo -> Subcampo -> Tópico)
# ==============================================================================
def openalex_plot_sunburst(
    data: Optional[Union[Dict[str, Any], str]] = None,
    institution_id: str = "",
    author_id: str = "",
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

    df = df.sort_values('total_works', ascending=False).head(150)
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
    plot_html = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")

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

    return {
        "status": "success",
        "chart_type": "sunburst",
        "title": title_text,
        "html_path": html_path,
        "html_content": full_html,
        "png_path": png_path,
        "summary_kpis": {
            "total_topics_analyzed": len(df),
            "top_topic": str(top_df.iloc[0]['topic']) if not top_df.empty else ""
        },
        "message": f"Sunburst taxonómico interactivo guardado en {html_path}"
    }


# ==============================================================================
# 5. MATRIZ OFICIAL DE LOS 17 ODS DE LA ONU
# ==============================================================================
def openalex_plot_sdg_grid(
    data: Optional[Union[Dict[str, Any], str]] = None,
    institution_id: str = "",
    author_id: str = "",
    query: str = "",
    title: str = "",
    output_dir: str = "./reports"
) -> Dict[str, Any]:
    """
    Cuadrícula interactiva de los 17 Objetivos de Desarrollo Sostenible (ODS de la ONU)
    con colores oficiales, porcentaje del corpus y tabla comparativa de impacto por ODS.
    """
    raw = _load_data(data)
    results = raw.get("results") or []
    if not results:
        clauses = []
        if query:
            clean_q = query.replace("'", "\\'")
            clauses.append(f"(ilike(title, '%{clean_q}%') OR ilike(subfield, '%{clean_q}%'))")
        if institution_id and not ("ror.org" in institution_id or institution_id.startswith("0")):
            clean_i = institution_id.replace("'", "\\'")
            clauses.append(f"has(institution_names, '{clean_i}')")

        filter_param = " AND ".join(clauses) if clauses else "1=1"
        ror_param = institution_id if ("ror.org" in institution_id or institution_id.startswith("0")) else None

        raw = openalex_aggregate_mexico(
            group_by="sdg",
            author_id=author_id,
            filter_param=filter_param,
            institution_ror=ror_param,
            limit=50
        )
        results = raw.get("results") or []

    sdg_map = {}
    if results:
        for r in results:
            dim = str(r.get("sdg_num") or r.get("dimension", "")).strip()
            match = re.search(r'\d+', dim)
            if match:
                num = int(match.group())
                sdg_map[num] = r

    total_works_all_sdgs = sum(r.get("total_works", 0) for r in sdg_map.values())
    total_citations_all_sdgs = sum(r.get("total_citations", 0) for r in sdg_map.values())
    title_text = title or "Alineación Científica con los 17 Objetivos de Desarrollo Sostenible (ONU)"
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

    return {
        "status": "success",
        "chart_type": "sdg-grid",
        "title": title_text,
        "html_path": html_path,
        "html_content": full_html,
        "png_path": png_path,
        "summary_kpis": {
            "active_sdgs": active_sdg_count,
            "total_sdg_works": total_works_all_sdgs
        },
        "message": f"Cuadrícula interactiva de ODS guardada en {html_path}"
    }


# ==============================================================================
# 6. DOSSIER DE PUBLICACIONES CIENTÍFICAS
# ==============================================================================
def openalex_plot_dossier_works(
    data: Optional[Union[Dict[str, Any], str]] = None,
    institution_id: str = "",
    author_id: str = "",
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

    return {
        "status": "success",
        "chart_type": "dossier-works",
        "title": title_text,
        "html_path": html_path,
        "html_content": full_html,
        "summary_kpis": {
            "works_count": len(works),
            "total_citations": tot_cites,
            "avg_fwci": avg_fwci
        },
        "message": f"Dossier de publicaciones guardado en {html_path}"
    }


# ==============================================================================
# 7. RED INTERACTIVA DE COAUTORÍA (PyVis Network)
# ==============================================================================
def openalex_plot_collaboration_network(
    data: Optional[Union[Dict[str, Any], str]] = None,
    institution_id: str = "",
    author_id: str = "",
    query: str = "",
    limit_works: int = 50,
    title: str = "",
    output_dir: str = "./reports"
) -> Dict[str, Any]:
    """
    Grafo interactivo de red de coautoría científica o interinstitucional con física de partículas (PyVis).
    """
    raw = _load_data(data)
    works = raw.get("works") or raw.get("results") or []
    if not works:
        raw = openalex_search_works(query=query, author_id=author_id, institution_name=institution_id, limit=limit_works)
        works = raw.get("works") or []

    if not works:
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

    return {
        "status": "success",
        "chart_type": "network",
        "title": title_text,
        "html_path": html_path,
        "html_content": full_html,
        "summary_kpis": {
            "nodes_count": len(top_nodes),
            "edges_count": len(edges)
        },
        "message": f"Red interactiva de colaboración guardada en {html_path}"
    }


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
    plot_html = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")

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

    return {
        "status": "success",
        "chart_type": "quadrant-matrix",
        "title": title_text,
        "html_path": html_path,
        "html_content": full_html,
        "png_path": png_path,
        "summary_kpis": {
            "entities_count": len(entities),
            "high_fwci_count": high_fwci_count,
            "top_fwci_entity": top_fwci_entity,
            "top_volume_entity": top_volume_entity
        },
        "message": f"Matriz de cuadrantes guardada en {html_path}"
    }


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
    plot_html = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")

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

    return {
        "status": "success",
        "chart_type": "geopolitical-sankey",
        "title": title_text,
        "html_path": html_path,
        "html_content": full_html,
        "summary_kpis": {
            "partner_countries_count": len(country_counts),
            "top_block": top_block,
            "top_partner": top_partner,
            "total_international_collaborations": tot_intl_collab
        },
        "message": f"Diagrama de flujo geopolítico guardado en {html_path}"
    }


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
    plot_html = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")

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

    return {
        "status": "success",
        "chart_type": "multidimensional-radar",
        "title": title_text,
        "html_path": html_path,
        "html_content": full_html,
        "summary_kpis": {
            "institutions_compared": len(summary_data),
            "metrics": summary_data
        },
        "message": f"Radar multidimensional guardado en {html_path}"
    }


# ==============================================================================
# 12. DINÁMICA TEMPORAL DE TÓPICOS / STREAMGRAPH DE LÍNEAS DE INVESTIGACIÓN
# ==============================================================================
def openalex_plot_topic_dynamics(
    institution_id: str = "",
    author_id: str = "",
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
    if author_id:
        where_conds.append(f"has(author_names, '{author_id}')")
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
    plot_html = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")

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

    return {
        "status": "success",
        "chart_type": "topic-dynamics",
        "title": title_text,
        "html_path": html_path,
        "html_content": full_html,
        "summary_kpis": {
            "top_subfield": top_subfields[0],
            "subfields_tracked": len(top_subfields),
            "period": f"{start_year}-{end_year}"
        },
        "message": f"Dinámica temporal de tópicos guardada en {html_path}"
    }
