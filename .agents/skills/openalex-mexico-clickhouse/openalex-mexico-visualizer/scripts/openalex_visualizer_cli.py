#!/usr/bin/env python3
"""
CLI Helper: OpenAlex México Visualizer & Artifact Engine
Transforma los datos JSON producidos por las skills analíticas de OpenAlex México
en artefactos visuales interactivos (Dashboards HTML con Plotly.js, Redes PyVis y Tarjetas PNG).

Entorno Python: /home/ambientesPy/revistaslatam
"""

import sys
import os
import json
import argparse
from typing import Dict, List, Any, Optional

try:
    import plotly.graph_objects as go
    import plotly.express as px
    import plotly.io as pio
except ImportError:
    print("Error: plotly no instalado. Use /home/ambientesPy/revistaslatam", file=sys.stderr)
    sys.exit(1)

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


# Paleta Cienciométrica Oficial (UNAM / OpenAlex / Acceso Abierto)
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


def detect_data_type(data: Dict[str, Any]) -> str:
    """Detecta automáticamente la estructura del JSON devuelto por las skills."""
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
    if "target" in data and data.get("target") == "works":
        return "dossier-works"
    if "target" in data and data.get("target") == "authors":
        return "authors-ranking"
    if "works" in data:
        return "dossier-works"
    if "authors" in data:
        return "authors-ranking"
    return "generic"


def render_top_ranking_html(data: Dict[str, Any], title: str) -> str:
    """Genera dashboard interactivo para rankings de autores o instituciones."""
    entities = data.get("top_entities", [])
    if not entities:
        return "<p class='text-gray-400'>No hay datos disponibles para graficar.</p>"

    query = data.get("query", "")
    by = data.get("by", "entidades")
    title_text = title or f"Capacidad y Desempeño: Top {len(entities)} {by.capitalize()} en '{query}'"

    names = [e.get("display_name") or e.get("institution") for e in entities][::-1]
    works = [e.get("total_works", 0) for e in entities][::-1]
    cites = [e.get("total_citations", 0) for e in entities][::-1]
    fwci = [e.get("avg_fwci", 1.0) for e in entities][::-1]
    insts = [e.get("institution", "") for e in entities][::-1]

    # Gráfica de barras horizontal interactiva coloreada por FWCI
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

    # Tabla resumen de métricas
    table_rows = []
    for e in entities:
        is_mx = e.get("is_mexican_affiliated", True)
        badge = '<span class="badge badge-mx">México</span>' if is_mx else '<span class="badge badge-ext">Internacional</span>'
        inst_label = e.get("institution") or "Sin institución registrada"
        table_rows.append(f"""
        <tr>
            <td class="font-bold">{e.get("rank", "-")}</td>
            <td class="font-semibold text-sky-400">{e.get("display_name") or e.get("institution")} {badge}</td>
            <td class="text-gray-300">{inst_label}</td>
            <td class="text-right">{e.get("total_works", 0):,}</td>
            <td class="text-right">{e.get("total_citations", 0):,}</td>
            <td class="text-right font-mono text-emerald-400">{e.get("avg_fwci", 0.0):.2f}</td>
            <td class="text-right font-mono text-amber-400">{e.get("pct_top_10", 0.0):.1f}%</td>
        </tr>
        """)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>{title_text}</title>
        <style>{get_embedded_styles()}</style>
    </head>
    <body class="bg-dark text-gray-100">
        <div class="container mx-auto p-6 max-w-6xl">
            <header class="header-card mb-6">
                <div class="flex items-center justify-between">
                    <div>
                        <span class="tag">OpenAlex México · Artefacto Cienciométrico</span>
                        <h1 class="text-2xl font-black text-white mt-1">{title_text}</h1>
                        <p class="text-sm text-gray-400 mt-1">Evaluación de capacidad instalada e impacto relativo normalizado.</p>
                    </div>
                    <div class="kpi-mini">
                        <span class="kpi-label">Entidades Evaluadas</span>
                        <span class="kpi-val">{len(entities)}</span>
                    </div>
                </div>
            </header>

            <section class="card mb-6">
                {plot_html}
            </section>

            <section class="card">
                <h3 class="text-lg font-bold text-white mb-3">Detalle Granular de Indicadores</h3>
                <div class="overflow-x-auto">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Nombre / Entidad</th>
                                <th>Institución</th>
                                <th class="text-right">Publicaciones</th>
                                <th class="text-right">Citas</th>
                                <th class="text-right">FWCI Promedio</th>
                                <th class="text-right">Top 10%</th>
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
    </html>
    """
    return html_content


def render_timeseries_html(data: Dict[str, Any], title: str) -> str:
    """Genera serie de tiempo dual: publicaciones anuales + FWCI."""
    results = data.get("results", [])
    if not results:
        return "<p class='text-gray-400'>No hay datos de series temporales.</p>"

    # Ordenar cronológicamente
    valid_results = [r for r in results if str(r.get("dimension", "")).isdigit()]
    valid_results.sort(key=lambda x: int(x["dimension"]))

    years = [int(r["dimension"]) for r in valid_results]
    works = [r.get("total_works", 0) for r in valid_results]
    cites = [r.get("total_citations", 0) for r in valid_results]
    fwci = [r.get("avg_fwci", 0.0) for r in valid_results]
    apc = [r.get("total_apc_paid_usd", 0.0) for r in valid_results]

    title_text = title or "Evolución Cronológica de la Producción Científica e Impacto"

    # Gráfica dual: barras de publicaciones + línea de FWCI
    from plotly.subplots import make_subplots
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

    # Línea benchmark mundial en FWCI = 1.00
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

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>{title_text}</title>
        <style>{get_embedded_styles()}</style>
    </head>
    <body class="bg-dark text-gray-100">
        <div class="container mx-auto p-6 max-w-6xl">
            <header class="header-card mb-6">
                <span class="tag">OpenAlex México · Trayectoria Temporal</span>
                <h1 class="text-2xl font-black text-white mt-1">{title_text}</h1>
                <div class="grid grid-cols-3 gap-4 mt-4">
                    <div class="kpi-mini">
                        <span class="kpi-label">Total Publicaciones</span>
                        <span class="kpi-val">{tot_works:,}</span>
                    </div>
                    <div class="kpi-mini">
                        <span class="kpi-label">Citas Acumuladas</span>
                        <span class="kpi-val">{tot_cites:,}</span>
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
        </div>
    </body>
    </html>
    """
    return html_content


def render_oa_donut_html(data: Dict[str, Any], title: str) -> str:
    """Genera gráfico Donut de distribución por modalidades de Acceso Abierto."""
    results = data.get("results", [])
    title_text = title or "Distribución de Vías de Acceso Abierto y Gasto en APC"

    labels = []
    values = []
    colors = []
    apc_totals = []

    for r in results:
        oa = str(r.get("dimension", "")).lower()
        if not oa:
            continue
        labels.append(oa.capitalize())
        values.append(r.get("total_works", 0))
        colors.append(OA_COLORS.get(oa, "#64748B"))
        apc_totals.append(r.get("total_apc_paid_usd", 0.0))

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
    total_apc = sum(apc_totals)
    diamond_works = sum(v for l, v in zip(labels, values) if l.lower() == "diamond")
    gold_works = sum(v for l, v in zip(labels, values) if l.lower() == "gold")

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>{title_text}</title>
        <style>{get_embedded_styles()}</style>
    </head>
    <body class="bg-dark text-gray-100">
        <div class="container mx-auto p-6 max-w-6xl">
            <header class="header-card mb-6">
                <span class="tag">OpenAlex México · Política de Acceso Abierto</span>
                <h1 class="text-2xl font-black text-white mt-1">{title_text}</h1>
                <div class="grid grid-cols-3 gap-4 mt-4">
                    <div class="kpi-mini">
                        <span class="kpi-label">Vía Diamante (No comercial)</span>
                        <span class="kpi-val text-emerald-400">{diamond_works:,}</span>
                    </div>
                    <div class="kpi-mini">
                        <span class="kpi-label">Vía Dorada (Con APC)</span>
                        <span class="kpi-val text-amber-400">{gold_works:,}</span>
                    </div>
                    <div class="kpi-mini">
                        <span class="kpi-label">Gasto Total en APC</span>
                        <span class="kpi-val text-rose-400">${total_apc:,.0f} USD</span>
                    </div>
                </div>
            </header>

            <section class="card mb-6">
                {plot_html}
            </section>
        </div>
    </body>
    </html>
    """
    return html_content


def render_dossier_works_html(data: Dict[str, Any], title: str) -> str:
    """Genera dossier analítico interactivo con tabla de publicaciones y desglose de autores."""
    works = data.get("works") or data.get("results") or []
    query = data.get("query", "")
    title_text = title or f"Dossier de Publicaciones Científicas: {query or 'Recuperación de Obras'}"

    # Construir filas de la tabla con coautoría desambiguada
    rows = []
    tot_cites = 0
    top10_count = 0
    fwci_vals = []

    for idx, w in enumerate(works, 1):
        cites = w.get("cited_by_count", 0)
        tot_cites += cites
        is_t10 = w.get("is_top_10", False)
        if is_t10:
            top10_count += 1
        if w.get("fwci") is not None:
            fwci_vals.append(float(w["fwci"]))

        oa_status = (w.get("oa_status") or "closed").lower()
        oa_color = OA_COLORS.get(oa_status, "#6B7280")
        oa_badge = f'<span class="badge" style="background-color: {oa_color}22; color: {oa_color}; border: 1px solid {oa_color}88;">{oa_status.capitalize()}</span>'

        # Desglose de autores
        auth_disambig = w.get("authors_disambiguated", {})
        mx_authors = auth_disambig.get("mexican_affiliated_authors", [])
        ext_authors = auth_disambig.get("international_collaborators", [])

        mx_names = ", ".join([a.get("name", "") for a in mx_authors[:3]])
        if len(mx_authors) > 3:
            mx_names += f" (+{len(mx_authors)-3})"

        ext_badge = ""
        if ext_authors:
            ext_badge = f'<span class="badge badge-ext">+{len(ext_authors)} intl</span>'

        sim_badge = ""
        if "semantic_similarity" in w:
            sim = w["semantic_similarity"]
            sim_badge = f'<span class="badge badge-sim">Similitud: {sim:.2%}</span>'

        rows.append(f"""
        <tr>
            <td class="font-bold">{idx}</td>
            <td>
                <div class="font-semibold text-white">{w.get("title")}</div>
                <div class="text-xs text-gray-400 mt-1">
                    <span class="text-sky-300">{mx_names or 'Autoría no desglosada'}</span> {ext_badge}
                </div>
            </td>
            <td>{w.get("publication_year", "-")}</td>
            <td>{oa_badge}</td>
            <td class="text-right font-bold text-white">{cites:,}</td>
            <td class="text-right font-mono text-emerald-400">{w.get("fwci", 0.0) or 0.0:.2f}</td>
            <td>{sim_badge}</td>
        </tr>
        """)

    avg_fwci = sum(fwci_vals) / len(fwci_vals) if fwci_vals else 0.0

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>{title_text}</title>
        <style>{get_embedded_styles()}</style>
    </head>
    <body class="bg-dark text-gray-100">
        <div class="container mx-auto p-6 max-w-6xl">
            <header class="header-card mb-6">
                <span class="tag">OpenAlex México · Dossier de Obras</span>
                <h1 class="text-2xl font-black text-white mt-1">{title_text}</h1>
                <div class="grid grid-cols-4 gap-4 mt-4">
                    <div class="kpi-mini">
                        <span class="kpi-label">Obras Listadas</span>
                        <span class="kpi-val">{len(works)}</span>
                    </div>
                    <div class="kpi-mini">
                        <span class="kpi-label">Citas Totales</span>
                        <span class="kpi-val">{tot_cites:,}</span>
                    </div>
                    <div class="kpi-mini">
                        <span class="kpi-label">FWCI Promedio</span>
                        <span class="kpi-val text-emerald-400">{avg_fwci:.2f}</span>
                    </div>
                    <div class="kpi-mini">
                        <span class="kpi-label">Artículos Top 10%</span>
                        <span class="kpi-val text-amber-400">{top10_count} ({top10_count/max(1, len(works)):.1%})</span>
                    </div>
                </div>
            </header>

            <section class="card">
                <h3 class="text-lg font-bold text-white mb-3">Publicaciones Científicas</h3>
                <div class="overflow-x-auto">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Título y Autores Desambiguados</th>
                                <th>Año</th>
                                <th>Vía OA</th>
                                <th class="text-right">Citas</th>
                                <th class="text-right">FWCI</th>
                                <th>Métrica</th>
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
    </html>
    """
    return html_content


def render_sunburst_html(data: Dict[str, Any], title: str) -> str:
    """Genera diagrama Sunburst interactivo para la taxonomía jerárquica de investigación."""
    import pandas as pd

    results = data.get("results") or []
    if not results and "works" in data:
        counts = {}
        for w in data["works"]:
            top = w.get("topic") or "General"
            sub = w.get("subfield") or "General"
            key = ("Ciencias", "Multidisciplinario", sub, top)
            counts[key] = counts.get(key, 0) + 1
        results = [
            {"domain": k[0], "field": k[1], "subfield": k[2], "topic": k[3], "total_works": v}
            for k, v in counts.items()
        ]

    if not results:
        return "<p class='text-gray-400'>No hay datos disponibles para generar el Sunburst taxonómico.</p>"

    df = pd.DataFrame(results)
    for col in ['domain', 'field', 'subfield', 'topic']:
        if col not in df.columns:
            df[col] = "Sin clasificar"
        else:
            df[col] = df[col].fillna("Sin clasificar").replace('', "Sin clasificar")

    if 'total_works' not in df.columns:
        df['total_works'] = 1

    df = df.sort_values('total_works', ascending=False).head(150)
    title_text = title or "Estructura de Especialización Científica (Taxonomía Jerárquica)"

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

    total_works_sum = int(df['total_works'].sum())
    unique_domains = df['domain'].nunique()
    unique_fields = df['field'].nunique()
    unique_topics = df['topic'].nunique()

    top_topics_rows = []
    top_df = df.sort_values('total_works', ascending=False).head(20)
    for idx, (_, row) in enumerate(top_df.iterrows(), 1):
        fwci_val = f"{row.get('avg_fwci', 1.0):.2f}" if 'avg_fwci' in row and pd.notna(row['avg_fwci']) else "-"
        cites_val = f"{int(row.get('total_citations', 0)):,}" if 'total_citations' in row and pd.notna(row['total_citations']) else "-"
        top_topics_rows.append(f"""
        <tr>
            <td class="font-bold">{idx}</td>
            <td class="font-semibold text-sky-400">{row['topic']}</td>
            <td class="text-gray-300">{row['subfield']}</td>
            <td class="text-gray-400">{row['field']}</td>
            <td class="text-right font-bold text-white">{int(row['total_works']):,}</td>
            <td class="text-right text-gray-300">{cites_val}</td>
            <td class="text-right font-mono text-emerald-400">{fwci_val}</td>
        </tr>
        """)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>{title_text}</title>
        <style>{get_embedded_styles()}</style>
    </head>
    <body class="bg-dark text-gray-100">
        <div class="container mx-auto p-6 max-w-6xl">
            <header class="header-card mb-6">
                <span class="tag">OpenAlex México · Taxonomía y Especialización</span>
                <h1 class="text-2xl font-black text-white mt-1">{title_text}</h1>
                <p class="text-sm text-gray-400 mt-1">Exploración jerárquica multinivel: Dominio → Campo → Subcampo → Tópico. Haz clic en los sectores concéntricos para hacer zoom.</p>
                <div class="grid grid-cols-4 gap-4 mt-4">
                    <div class="kpi-mini">
                        <span class="kpi-label">Obras Analizadas</span>
                        <span class="kpi-val">{total_works_sum:,}</span>
                    </div>
                    <div class="kpi-mini">
                        <span class="kpi-label">Dominios</span>
                        <span class="kpi-val text-sky-400">{unique_domains}</span>
                    </div>
                    <div class="kpi-mini">
                        <span class="kpi-label">Campos Disciplinares</span>
                        <span class="kpi-val text-emerald-400">{unique_fields}</span>
                    </div>
                    <div class="kpi-mini">
                        <span class="kpi-label">Tópicos Especializados</span>
                        <span class="kpi-val text-amber-400">{unique_topics}</span>
                    </div>
                </div>
            </header>

            <section class="card mb-6">
                {plot_html}
            </section>

            <section class="card">
                <h3 class="text-lg font-bold text-white mb-3">Top 20 Tópicos de Mayor Actividad Científica</h3>
                <div class="overflow-x-auto">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Tópico Especializado</th>
                                <th>Subcampo</th>
                                <th>Campo</th>
                                <th class="text-right">Publicaciones</th>
                                <th class="text-right">Citas</th>
                                <th class="text-right">FWCI Promedio</th>
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
    </html>
    """
    return html_content


def render_sdg_grid_html(data: Dict[str, Any], title: str) -> str:
    """Genera la matriz de los 17 Objetivos de Desarrollo Sostenible (ODS de la ONU)."""
    import re

    results = data.get("results") or []
    sdg_map = {}

    if results:
        for r in results:
            dim = str(r.get("sdg_num") or r.get("dimension", "")).strip()
            match = re.search(r'\d+', dim)
            if match:
                num = int(match.group())
                sdg_map[num] = r
    elif "works" in data:
        for w in data["works"]:
            sdg_ids = w.get("sdg_ids", [])
            for sid in sdg_ids:
                match = re.search(r'\d+', str(sid))
                if match:
                    num = int(match.group())
                    if num not in sdg_map:
                        sdg_map[num] = {"dimension": str(num), "sdg_num": num, "total_works": 0, "total_citations": 0, "fwci_list": []}
                    sdg_map[num]["total_works"] += 1
                    sdg_map[num]["total_citations"] += w.get("cited_by_count", 0)
                    if w.get("fwci") is not None:
                        sdg_map[num]["fwci_list"].append(float(w["fwci"]))
        for num, v in sdg_map.items():
            flist = v.pop("fwci_list", [])
            v["avg_fwci"] = round(sum(flist) / len(flist), 3) if flist else 1.0

    total_works_all_sdgs = sum(r.get("total_works", 0) for r in sdg_map.values())
    total_citations_all_sdgs = sum(r.get("total_citations", 0) for r in sdg_map.values())

    title_text = title or "Alineación Científica con los 17 Objetivos de Desarrollo Sostenible (ONU)"

    cards_html = []
    table_rows = []

    for i in range(1, 18):
        info = SDG_INFO.get(i, {"name": f"ODS {i}", "color": "#1E293B"})
        r = sdg_map.get(i, {"total_works": 0, "total_citations": 0, "avg_fwci": 0.0})
        count = r.get("total_works", 0)
        cites = r.get("total_citations", 0)
        fwci = r.get("avg_fwci", 0.0)
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

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>{title_text}</title>
        <style>{get_embedded_styles()}</style>
    </head>
    <body class="bg-dark text-gray-100">
        <div class="container mx-auto p-6 max-w-6xl">
            <header class="header-card mb-6">
                <span class="tag">OpenAlex México · Agenda 2030 ONU</span>
                <h1 class="text-2xl font-black text-white mt-1">{title_text}</h1>
                <p class="text-sm text-gray-400 mt-1">Cuantificación del aporte y alineación de la investigación científica en las metas de desarrollo sostenible.</p>
                <div class="grid grid-cols-4 gap-4 mt-4">
                    <div class="kpi-mini">
                        <span class="kpi-label">Publicaciones en ODS</span>
                        <span class="kpi-val text-sky-400">{total_works_all_sdgs:,}</span>
                    </div>
                    <div class="kpi-mini">
                        <span class="kpi-label">ODS con Presencia</span>
                        <span class="kpi-val text-emerald-400">{active_sdg_count} / 17</span>
                    </div>
                    <div class="kpi-mini">
                        <span class="kpi-label">Citas en Temáticas ODS</span>
                        <span class="kpi-val text-purple-400">{total_citations_all_sdgs:,}</span>
                    </div>
                    <div class="kpi-mini">
                        <span class="kpi-label">Cobertura de la Agenda</span>
                        <span class="kpi-val text-amber-400">{(active_sdg_count / 17.0 * 100):.1f}%</span>
                    </div>
                </div>
            </header>

            <section class="card mb-6">
                <h3 class="text-lg font-bold text-white mb-4">Matriz Oficial de los 17 Objetivos</h3>
                <div class="sdg-grid">
                    {''.join(cards_html)}
                </div>
            </section>

            <section class="card">
                <h3 class="text-lg font-bold text-white mb-3">Balance Cuantitativo por Objetivo de Desarrollo Sostenible</h3>
                <div class="overflow-x-auto">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th class="text-center">ODS</th>
                                <th>Nombre del Objetivo</th>
                                <th class="text-right">Publicaciones</th>
                                <th class="text-right">% Relativo</th>
                                <th class="text-right">Citas</th>
                                <th class="text-right">FWCI Promedio</th>
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
    </html>
    """
    return html_content


def render_network_html(data: Dict[str, Any], title: str) -> str:
    """Genera grafo interactivo de coautoría o colaboración institucional con PyVis."""
    try:
        from pyvis.network import Network
    except ImportError:
        return "<p class='text-gray-400'>pyvis no está instalado para renderizar redes.</p>"

    title_text = title or "Red de Colaboración Científica"
    net = Network(height="600px", width="100%", bgcolor=THEME_CARD, font_color=THEME_TEXT)
    net.force_atlas_2based()

    # Extraer pares de coautoría a partir de works
    works = data.get("works") or data.get("results") or []
    node_weights = {}
    edges = {}

    for w in works:
        authors = w.get("author_names", [])
        for a in authors[:10]:
            node_weights[a] = node_weights.get(a, 0) + 1

        for i in range(len(authors[:10])):
            for j in range(i + 1, len(authors[:10])):
                pair = tuple(sorted([authors[i], authors[j]]))
                edges[pair] = edges.get(pair, 0) + 1

    # Agregar nodos principales
    top_nodes = sorted(node_weights.items(), key=lambda x: x[1], reverse=True)[:50]
    top_node_names = set(n[0] for n in top_nodes)

    for name, weight in top_nodes:
        net.add_node(name, label=name, value=weight, color="#38BDF8")

    # Agregar aristas entre los nodos principales
    for (u, v), weight in edges.items():
        if u in top_node_names and v in top_node_names:
            net.add_edge(u, v, value=weight, color="rgba(148, 163, 184, 0.4)")

    net_html = net.generate_html()
    return net_html


def render_png_card(data: Dict[str, Any], output_png: str, title: str) -> None:
    """Genera una tarjeta gráfica estática PNG con Matplotlib para incrustar en el chat."""
    if plt is None:
        return

    data_type = detect_data_type(data)
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=180)
    fig.patch.set_facecolor(THEME_CARD)
    ax.set_facecolor(THEME_CARD)

    if data_type == "top-ranking":
        entities = data.get("top_entities", [])[:10][::-1]
        names = [(e.get("display_name") or e.get("institution") or "Entidad")[:25] for e in entities]
        works = [e.get("total_works", 0) for e in entities]
        bars = ax.barh(names, works, color="#38BDF8", edgecolor="#0284C7")
        ax.set_title(title or f"Top {len(entities)} Entidades en '{data.get('query','')}'", fontsize=12, fontweight="bold", pad=12)
        ax.set_xlabel("Publicaciones Acumuladas", fontsize=10)

    elif data_type == "oa-donut":
        results = [r for r in data.get("results", []) if r.get("dimension")]
        labels = [r["dimension"].capitalize() for r in results]
        vals = [r.get("total_works", 0) for r in results]
        colors = [OA_COLORS.get(r["dimension"].lower(), "#64748B") for r in results]
        ax.pie(vals, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90, wedgeprops=dict(width=0.45, edgecolor=THEME_CARD))
        ax.set_title(title or "Distribución de Vías de Acceso Abierto", fontsize=12, fontweight="bold")

    elif data_type == "timeseries":
        results = [r for r in data.get("results", []) if str(r.get("dimension", "")).isdigit()]
        results.sort(key=lambda x: int(x["dimension"]))
        years = [int(r["dimension"]) for r in results]
        works = [r.get("total_works", 0) for r in results]
        ax.plot(years, works, marker="o", color="#38BDF8", linewidth=2.5, markersize=5)
        ax.fill_between(years, works, color="#38BDF8", alpha=0.15)
        ax.set_title(title or "Trayectoria Cronológica de Publicaciones", fontsize=12, fontweight="bold", pad=12)
        ax.set_xlabel("Año", fontsize=10)
        ax.set_ylabel("Artículos", fontsize=10)

    elif data_type == "sunburst":
        results = data.get("results", [])[:10][::-1]
        names = [r.get("topic", "Tópico")[:25] for r in results]
        works = [r.get("total_works", 0) for r in results]
        ax.barh(names, works, color="#38BDF8", edgecolor="#0284C7")
        ax.set_title(title or "Top Tópicos de Especialización", fontsize=12, fontweight="bold", pad=12)
        ax.set_xlabel("Publicaciones", fontsize=10)

    elif data_type == "sdg-grid":
        results = [r for r in data.get("results", []) if r.get("total_works", 0) > 0]
        results.sort(key=lambda x: x.get("total_works", 0), reverse=True)
        top_sdgs = results[:10][::-1]
        names = [f"ODS {r.get('sdg_num', r.get('dimension', ''))}: {SDG_INFO.get(int(r.get('sdg_num', r.get('dimension', 0))), {}).get('name', '')[:20]}" for r in top_sdgs]
        works = [r.get("total_works", 0) for r in top_sdgs]
        colors = [SDG_INFO.get(int(r.get("sdg_num", r.get("dimension", 0))), {}).get("color", "#38BDF8") for r in top_sdgs]
        ax.barh(names, works, color=colors, edgecolor="#1E293B")
        ax.set_title(title or "Top Objetivos de Desarrollo Sostenible (ODS)", fontsize=12, fontweight="bold", pad=12)
        ax.set_xlabel("Publicaciones", fontsize=10)

    else:
        ax.text(0.5, 0.5, "Resumen Visual Generado", ha="center", va="center", color="#F9FAFB", fontsize=14)

    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_png)), exist_ok=True)
    plt.savefig(output_png, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    print(f"Tarjeta gráfica PNG generada en: {output_png}")


def get_embedded_styles() -> str:
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
    
    /* Estilos específicos para la Matriz ODS (Agenda 2030) */
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


def main():
    parser = argparse.ArgumentParser(description="CLI de Visualización y Generación de Artefactos de OpenAlex México")
    parser.add_argument("--input", required=True, help="Ruta al archivo JSON con los datos de entrada")
    parser.add_argument("--type", choices=["auto", "top-ranking", "timeseries", "oa-donut", "dossier-works", "network", "sunburst", "sdg-grid"], default="auto", help="Tipo de visualización a forzar (default: auto)")
    parser.add_argument("--title", default="", help="Título personalizado para el artefacto")
    parser.add_argument("--output", required=True, help="Ruta de guardado para el archivo HTML interactivo")
    parser.add_argument("--png", help="Ruta opcional para generar también una tarjeta estática en PNG")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: El archivo de entrada '{args.input}' no existe.", file=sys.stderr)
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    target_type = args.type
    if target_type == "auto":
        target_type = detect_data_type(data)
        print(f"Tipo de datos detectado automáticamente: '{target_type}'")

    if target_type == "top-ranking" or target_type == "authors-ranking":
        html_out = render_top_ranking_html(data, args.title)
    elif target_type == "timeseries":
        html_out = render_timeseries_html(data, args.title)
    elif target_type == "oa-donut":
        html_out = render_oa_donut_html(data, args.title)
    elif target_type == "dossier-works":
        html_out = render_dossier_works_html(data, args.title)
    elif target_type == "network":
        html_out = render_network_html(data, args.title)
    elif target_type == "sunburst":
        html_out = render_sunburst_html(data, args.title)
    elif target_type == "sdg-grid":
        html_out = render_sdg_grid_html(data, args.title)
    else:
        html_out = render_top_ranking_html(data, args.title)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html_out)

    print(f"Artefacto visual interactivo ({target_type}) generado con éxito en: {args.output}")

    if args.png:
        render_png_card(data, args.png, args.title)

    sys.exit(0)


if __name__ == "__main__":
    main()
