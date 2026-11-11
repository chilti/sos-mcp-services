#!/usr/bin/env python3
"""
SDG Impact Intelligence CLI (sdg_impact_cli.py)
-----------------------------------------------
Mapeo, cuantificación y visualización de la alineación de la producción
científica con los 17 Objetivos de Desarrollo Sostenible (ODS / SDG) de la ONU (Agenda 2030).

Principios y salidas:
- Workspace-First: Consume `./corpus.parquet` directamente del workspace.
- Salida Dual Científica:
  1. `sdg_impact_dashboard.html`: Dashboard interactivo HTML para exploración (estética SinapsisAI).
  2. `sdg_grid_es.png` (300 DPI): Cuadrícula pura de los 17 ODS para artículos en español.
  3. `sdg_grid_en.png` (300 DPI): Cuadrícula pura de los 17 ODS para artículos científicos en inglés (e.g. Q1 journals).
  4. `sdg_impact_summary.json` y `sdg_impact_report.md`: Tablas y métricas estructuradas.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from PIL import Image, ImageEnhance, ImageOps

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

CURRENT_DIR = Path(__file__).resolve().parent
RESOURCES_DIR = CURRENT_DIR.parent / "resources"
ICONS_ES_DIR = RESOURCES_DIR / "icons_es"
ICONS_EN_DIR = RESOURCES_DIR / "icons_en"

SDG_INFO: Dict[int, Dict[str, str]] = {
    1: {"name": "Fin de la Pobreza", "name_en": "No Poverty", "color": "#E5243B"},
    2: {"name": "Hambre Cero", "name_en": "Zero Hunger", "color": "#DDA63A"},
    3: {"name": "Salud y Bienestar", "name_en": "Good Health & Well-being", "color": "#4C9F38"},
    4: {"name": "Educación de Calidad", "name_en": "Quality Education", "color": "#C5192D"},
    5: {"name": "Igualdad de Género", "name_en": "Gender Equality", "color": "#FF3A21"},
    6: {"name": "Agua Limpia y Saneamiento", "name_en": "Clean Water & Sanitation", "color": "#26BDE2"},
    7: {"name": "Energía Asequible", "name_en": "Affordable & Clean Energy", "color": "#FCC30B"},
    8: {"name": "Trabajo Decente", "name_en": "Decent Work & Economic Growth", "color": "#A21942"},
    9: {"name": "Industria e Innovación", "name_en": "Industry, Innovation & Infra", "color": "#FD6925"},
    10: {"name": "Reducción de Desigualdades", "name_en": "Reduced Inequalities", "color": "#DD1367"},
    11: {"name": "Ciudades Sostenibles", "name_en": "Sustainable Cities & Communities", "color": "#FD9D24"},
    12: {"name": "Producción Responsable", "name_en": "Responsible Consumption", "color": "#BF8B2E"},
    13: {"name": "Acción por el Clima", "name_en": "Climate Action", "color": "#3F7E44"},
    14: {"name": "Vida Submarina", "name_en": "Life Below Water", "color": "#0A97D9"},
    15: {"name": "Vida de Ecosistemas", "name_en": "Life on Land", "color": "#56C02B"},
    16: {"name": "Paz y Justicia", "name_en": "Peace, Justice & Institutions", "color": "#00689D"},
    17: {"name": "Alianzas para los Objetivos", "name_en": "Partnerships for the Goals", "color": "#19486A"},
}

BASE_IMG_URL = "https://open-sdg.github.io/sdg-translations/assets/img/goals/es"


def resolve_input_path(workspace: Path, input_arg: Optional[str]) -> Path:
    if input_arg:
        p = Path(input_arg)
        if not p.is_absolute():
            p = (workspace / p).resolve()
        if p.exists():
            return p
        raise FileNotFoundError(f"Archivo de entrada no encontrado: {p}")

    candidates = [
        workspace / "corpus.parquet",
        workspace / "data" / "corpus.parquet",
        workspace / "corpus.json",
        workspace / "corpus.csv",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(
        f"No se encontró corpus bibliográfico en {workspace}. "
        "Asegúrate de que exista ./corpus.parquet o especifica --input."
    )


def load_corpus(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix in (".json", ".jsonl"):
        try:
            return pd.read_json(path)
        except Exception:
            return pd.read_json(path, lines=True)
    if suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Formato no soportado: {suffix}")


def extract_sdg_number(val: Any) -> List[int]:
    """Extrae números de ODS (1 a 17) de cadenas, listas o arrays."""
    if val is None:
        return []

    if isinstance(val, (list, tuple, np.ndarray, pd.Series)):
        res = []
        for item in val:
            res.extend(extract_sdg_number(item))
        return list(set(res))

    try:
        if pd.isna(val):
            return []
    except Exception:
        pass

    s = str(val).strip()
    if not s or s.lower() in ("none", "nan", "null", "[]"):
        return []

    found = []
    matches = re.findall(r'(?:sdg|ods)[/-]?\s*(\d+)|(?:^|\b)(\d+)(?:\b|$)', s, re.IGNORECASE)
    for m in matches:
        num_str = m[0] or m[1]
        if num_str and num_str.isdigit():
            n = int(num_str)
            if 1 <= n <= 17:
                found.append(n)
    return list(set(found))


def compute_sdg_metrics(df: pd.DataFrame, custom_sdg_col: Optional[str] = None) -> Dict[str, Any]:
    """Calcula las métricas agregadas por cada uno de los 17 ODS."""
    total_docs = len(df)
    
    sdg_col = None
    if custom_sdg_col and custom_sdg_col in df.columns:
        sdg_col = custom_sdg_col
    else:
        for cand in ("sdgs", "sdg_ids", "ODS_ID", "sdg", "ods", "sdg_names", "ODS_Nombre"):
            if cand in df.columns:
                sdg_col = cand
                break

    stats = {
        i: {
            "sdg_num": i,
            "name": SDG_INFO[i]["name"],
            "name_en": SDG_INFO[i]["name_en"],
            "color": SDG_INFO[i]["color"],
            "publications_count": 0,
            "total_citations": 0,
            "fwci_list": [],
            "top_10_count": 0,
            "open_access_count": 0,
            "diamond_oa_count": 0,
            "sample_papers": [],
        }
        for i in range(1, 18)
    }

    if sdg_col is None:
        return {
            "total_docs": total_docs,
            "docs_with_sdg": 0,
            "coverage_pct": 0.0,
            "sdg_stats": stats,
            "note": "No se detectó columna de ODS en el corpus.",
        }

    docs_with_sdg = 0
    cite_col = "cited_by_count" if "cited_by_count" in df.columns else ("citations" if "citations" in df.columns else None)
    fwci_col = "fwci" if "fwci" in df.columns else None
    top10_col = "is_in_top_10_percent" if "is_in_top_10_percent" in df.columns else ("is_top_10" if "is_top_10" in df.columns else None)
    oa_col = "oa_status" if "oa_status" in df.columns else None
    title_col = "title" if "title" in df.columns else None
    doi_col = "doi" if "doi" in df.columns else None
    year_col = "publication_year" if "publication_year" in df.columns else ("year" if "year" in df.columns else None)

    for _, row in df.iterrows():
        sdgs_found = extract_sdg_number(row[sdg_col])
        if sdgs_found:
            docs_with_sdg += 1
            cites = int(row[cite_col]) if cite_col and pd.notna(row[cite_col]) else 0
            fwci_val = float(row[fwci_col]) if fwci_col and pd.notna(row[fwci_col]) else None
            is_top10 = bool(row[top10_col]) if top10_col and pd.notna(row[top10_col]) else False
            oa_val = str(row[oa_col]).lower() if oa_col and pd.notna(row[oa_col]) else ""
            is_oa = oa_val not in ("", "closed", "none")
            is_diamond = oa_val == "diamond"
            t_str = str(row[title_col]) if title_col and pd.notna(row[title_col]) else "Sin título"
            d_str = str(row[doi_col]) if doi_col and pd.notna(row[doi_col]) else ""
            y_val = int(row[year_col]) if year_col and pd.notna(row[year_col]) else None

            for num in sdgs_found:
                st = stats[num]
                st["publications_count"] += 1
                st["total_citations"] += cites
                if fwci_val is not None:
                    st["fwci_list"].append(fwci_val)
                if is_top10:
                    st["top_10_count"] += 1
                if is_oa:
                    st["open_access_count"] += 1
                if is_diamond:
                    st["diamond_oa_count"] += 1
                if len(st["sample_papers"]) < 3:
                    st["sample_papers"].append({
                        "title": t_str,
                        "year": y_val,
                        "citations": cites,
                        "doi": d_str,
                    })

    for num, st in stats.items():
        cnt = st["publications_count"]
        st["share_pct"] = round((cnt / total_docs * 100.0), 2) if total_docs > 0 else 0.0
        st["mean_citations"] = round(st["total_citations"] / cnt, 2) if cnt > 0 else 0.0
        fw_list = st.pop("fwci_list", [])
        st["mean_fwci"] = round(float(np.mean(fw_list)), 3) if fw_list else 1.00
        st["top_10_pct"] = round((st["top_10_count"] / cnt * 100.0), 2) if cnt > 0 else 0.0
        st["oa_pct"] = round((st["open_access_count"] / cnt * 100.0), 2) if cnt > 0 else 0.0
        st["diamond_pct"] = round((st["diamond_oa_count"] / cnt * 100.0), 2) if cnt > 0 else 0.0

    return {
        "total_docs": total_docs,
        "docs_with_sdg": docs_with_sdg,
        "coverage_pct": round((docs_with_sdg / total_docs * 100.0), 2) if total_docs > 0 else 0.0,
        "sdg_stats": stats,
    }


def render_sdg_grid_image(
    data: Dict[str, Any],
    out_png: Path,
    lang: str = "es",
    dpi: int = 300,
) -> None:
    """
    Genera la cuadrícula limpia de los 17 ODS como imagen pura PNG de alta resolución (300 DPI)
    diseñada para ser incrustada directamente en artículos científicos (sin bordes web, títulos ni tablas).
    
    Disposición: 6 columnas x 3 filas (17 ODS + 1 celda de resumen de la Agenda 2030).
    """
    stats = data["sdg_stats"]
    total_docs = data["total_docs"]
    icons_dir = ICONS_EN_DIR if lang == "en" else ICONS_ES_DIR

    n_cols = 6
    n_rows = 3
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, 8.5), dpi=dpi)
    fig.patch.set_facecolor("#ffffff")

    for i in range(1, 19):
        r_idx = (i - 1) // n_cols
        c_idx = (i - 1) % n_cols
        ax = axes[r_idx, c_idx]
        ax.axis("off")

        if i <= 17:
            s = stats[i]
            cnt = s["publications_count"]
            pct = s["share_pct"]
            color = s["color"]
            name = s["name_en"] if lang == "en" else s["name"]

            # Cargar icono oficial
            icon_file = icons_dir / f"{i}.png"
            if icon_file.exists():
                try:
                    img = Image.open(icon_file).convert("RGBA")
                    if cnt == 0:
                        # Desaturar y atenuar si no tiene publicaciones en el corpus
                        gray = ImageOps.grayscale(img.convert("RGB"))
                        img = ImageEnhance.Brightness(gray.convert("RGBA")).enhance(0.85)
                        img.putalpha(80)
                    ax.imshow(img)
                except Exception:
                    ax.text(0.5, 0.5, f"SDG {i}", ha="center", va="center", fontsize=12, fontweight="bold", color=color)
            else:
                rect = patches.FancyBboxPatch((0.05, 0.05), 0.9, 0.9, boxstyle="round,pad=0.04", facecolor=color, edgecolor="none")
                ax.add_patch(rect)
                ax.text(0.5, 0.65, str(i), ha="center", va="center", fontsize=28, fontweight="black", color="white")
                ax.text(0.5, 0.25, name[:22], ha="center", va="center", fontsize=8, fontweight="bold", color="white")

            # Superposición inferior de métricas (limpia y tipográficamente clara)
            overlay_h = 0.26
            overlay_color = "#0f172a" if cnt > 0 else "#64748b"
            rect_bg = patches.Rectangle((0, 0), 1, overlay_h, transform=ax.transAxes, facecolor=overlay_color, alpha=0.92, zorder=3)
            ax.add_patch(rect_bg)

            # Texto de métrica en idioma correspondiente
            metric_text = f"{cnt:,} papers ({pct:.1f}%)" if lang == "en" else f"{cnt:,} docs ({pct:.1f}%)"
            if cnt == 0:
                metric_text = "0 papers" if lang == "en" else "0 docs"

            ax.text(
                0.5,
                overlay_h / 2.0,
                metric_text,
                transform=ax.transAxes,
                ha="center",
                va="center",
                fontsize=9.5,
                fontweight="heavy",
                color="#ffffff",
                zorder=4,
            )

        else:
            # Celda 18: Tarjeta de Resumen / Global UN 2030 Agenda
            active_count = sum(1 for s in stats.values() if s["publications_count"] > 0)
            cov_pct = data.get("coverage_pct", 0.0)
            rect = patches.FancyBboxPatch((0.02, 0.02), 0.96, 0.96, boxstyle="round,pad=0.03", facecolor="#1e293b", edgecolor="#0284c7", lw=1.5)
            ax.add_patch(rect)

            header_txt = "UN 2030 AGENDA" if lang == "en" else "AGENDA 2030 ONU"
            sub_txt = "Corpus Coverage:" if lang == "en" else "Cobertura del Corpus:"
            active_txt = f"{active_count} of 17 SDGs" if lang == "en" else f"{active_count} de 17 ODS"

            ax.text(0.5, 0.80, header_txt, ha="center", va="center", fontsize=11, fontweight="black", color="#38bdf8")
            ax.text(0.5, 0.58, f"{cov_pct:.1f}%", ha="center", va="center", fontsize=24, fontweight="black", color="#ffffff")
            ax.text(0.5, 0.38, sub_txt, ha="center", va="center", fontsize=8.5, color="#94a3b8")
            ax.text(0.5, 0.20, active_txt, ha="center", va="center", fontsize=9.5, fontweight="bold", color="#34d399")

    plt.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02, wspace=0.06, hspace=0.06)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png, dpi=dpi, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)


def render_html_dashboard(data: Dict[str, Any], title: str) -> str:
    """Renderiza el visualizador autónomo con la cuadrícula interactiva de 17 ODS de SinapsisAI."""
    stats = data["sdg_stats"]
    total_docs = data["total_docs"]
    docs_sdg = data["docs_with_sdg"]
    cov_pct = data["coverage_pct"]

    active_count = sum(1 for s in stats.values() if s["publications_count"] > 0)
    top_sdg = max(stats.values(), key=lambda x: x["publications_count"]) if active_count > 0 else None

    cards_html = []
    table_rows = []

    for i in range(1, 18):
        s = stats[i]
        cnt = s["publications_count"]
        pct = s["share_pct"]
        cites = s["total_citations"]
        fwci = s["mean_fwci"]
        color = s["color"]
        name = s["name"]

        active_class = "" if cnt > 0 else "sdg-inactive"
        img_url = f"{BASE_IMG_URL}/{i}.png"
        tooltip = f"ODS {i}: {name} - {cnt:,} documentos ({pct:.1f}% del corpus)"

        cards_html.append(f"""
        <div class="sdg-card {active_class}" style="background-color: {color};" title="{tooltip}">
            <img src="{img_url}" class="sdg-img" alt="ODS {i}" loading="lazy" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
            <div class="sdg-fallback" style="display:none; background:{color};">
                <span class="sdg-fallback-num">{i}</span>
                <span class="sdg-fallback-name">{name}</span>
            </div>
            <div class="sdg-overlay">
                <span class="sdg-perc">{pct:.1f}%</span>
                <span class="sdg-count">{cnt:,} docs</span>
            </div>
        </div>
        """)

        fwci_badge = f'<span class="fwci-tag fwci-high">{fwci:.2f}</span>' if fwci >= 1.0 else f'<span class="fwci-tag fwci-low">{fwci:.2f}</span>'
        if cnt == 0:
            fwci_badge = '<span class="text-muted">-</span>'

        table_rows.append(f"""
        <tr class="{active_class}">
            <td style="text-align: center;"><span class="sdg-badge-num" style="background-color: {color};">{i}</span></td>
            <td style="font-weight: 600; color: #f8fafc;">{name}</td>
            <td style="text-align: right; font-weight: bold; color: #38bdf8;">{cnt:,}</td>
            <td style="text-align: right; font-family: monospace;">{pct:.1f}%</td>
            <td style="text-align: right;">{cites:,}</td>
            <td style="text-align: right;">{fwci_badge}</td>
            <td style="text-align: right;">{s['top_10_pct']:.1f}%</td>
            <td style="text-align: right; color: #34d399;">{s['diamond_pct']:.1f}%</td>
        </tr>
        """)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        :root {{
            --bg-dark: #0f172a;
            --card-bg: #1e293b;
            --border-color: #334155;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #0284c7;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-main);
            padding: 24px;
            line-height: 1.5;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header-card {{
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        }}
        .tag {{
            display: inline-block;
            background: rgba(2, 132, 199, 0.2);
            color: #38bdf8;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 9999px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
        }}
        h1 {{ font-size: 1.75rem; font-weight: 800; color: #ffffff; margin-bottom: 6px; }}
        .subtitle {{ font-size: 0.95rem; color: var(--text-muted); margin-bottom: 20px; }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
        }}
        .kpi-card {{
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 14px 16px;
        }}
        .kpi-label {{ display: block; font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); font-weight: 600; }}
        .kpi-val {{ font-size: 1.5rem; font-weight: 800; color: #38bdf8; }}
        
        .sdg-section {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 28px;
        }}
        .section-title {{
            font-size: 1.15rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .sdg-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
            gap: 14px;
            padding: 6px 0;
        }}
        .sdg-card {{
            position: relative;
            aspect-ratio: 1 / 1;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
            transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.2s;
            cursor: pointer;
            background-color: #334155;
        }}
        .sdg-card:hover {{
            transform: translateY(-4px) scale(1.03);
            z-index: 10;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
        }}
        .sdg-img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }}
        .sdg-fallback {{
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 8px;
            text-align: center;
        }}
        .sdg-fallback-num {{ font-size: 2rem; font-weight: 900; color: #ffffff; line-height: 1; }}
        .sdg-fallback-name {{ font-size: 0.7rem; color: #ffffff; font-weight: 600; margin-top: 4px; }}
        .sdg-overlay {{
            position: absolute;
            bottom: 0; left: 0; right: 0;
            background: linear-gradient(180deg, rgba(15, 23, 42, 0.0) 0%, rgba(15, 23, 42, 0.92) 50%, #0f172a 100%);
            color: white;
            padding: 6px 4px 4px 4px;
            text-align: center;
            line-height: 1.1;
        }}
        .sdg-perc {{ font-size: 1.05rem; font-weight: 800; display: block; color: #ffffff; }}
        .sdg-count {{ font-size: 0.72rem; color: #94a3b8; font-weight: 600; }}
        .sdg-inactive {{
            filter: grayscale(100%) opacity(0.35);
        }}
        .sdg-inactive:hover {{
            filter: grayscale(0%) opacity(1);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.88rem;
            margin-top: 10px;
        }}
        th {{
            background-color: rgba(15, 23, 42, 0.8);
            color: var(--text-muted);
            text-transform: uppercase;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            padding: 10px 12px;
            border-bottom: 1px solid var(--border-color);
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid rgba(51, 65, 85, 0.5);
        }}
        tr:hover td {{
            background-color: rgba(51, 65, 85, 0.3);
        }}
        .sdg-badge-num {{
            display: inline-block;
            width: 26px;
            height: 26px;
            line-height: 26px;
            border-radius: 50%;
            color: white;
            font-weight: 800;
            font-size: 0.78rem;
        }}
        .fwci-tag {{
            display: inline-block;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 700;
            font-family: monospace;
            font-size: 0.8rem;
        }}
        .fwci-high {{ background: rgba(52, 211, 153, 0.15); color: #34d399; }}
        .fwci-low {{ background: rgba(239, 68, 68, 0.15); color: #f87171; }}
        .text-muted {{ color: var(--text-muted); }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header-card">
            <span class="tag">Cienciometría & Agenda 2030 ONU · KnoMap / SinapsisAI</span>
            <h1>{title}</h1>
            <p class="subtitle">Monitoreo, cobertura e impacto científico normalizado en los 17 Objetivos de Desarrollo Sostenible.</p>
            <div class="kpi-grid">
                <div class="kpi-card">
                    <span class="kpi-label">Corpus Total Evaluado</span>
                    <span class="kpi-val">{total_docs:,}</span>
                </div>
                <div class="kpi-card">
                    <span class="kpi-label">Artículos con ODS Asignado</span>
                    <span class="kpi-val">{docs_sdg:,} <span style="font-size: 0.85rem; color: #94a3b8;">({cov_pct:.1f}%)</span></span>
                </div>
                <div class="kpi-card">
                    <span class="kpi-label">ODS con Presencia Activa</span>
                    <span class="kpi-val">{active_count} <span style="font-size: 0.85rem; color: #94a3b8;">/ 17</span></span>
                </div>
                <div class="kpi-card">
                    <span class="kpi-label">ODS Dominante</span>
                    <span class="kpi-val" style="font-size: 1.15rem; color: {top_sdg['color'] if top_sdg else '#38bdf8'};">
                        {f"ODS {top_sdg['sdg_num']}: {top_sdg['name'][:20]}" if top_sdg and top_sdg['publications_count'] > 0 else "N/A"}
                    </span>
                </div>
            </div>
        </header>

        <section class="sdg-section">
            <div class="section-title">
                <span>Cuadrícula Interactiva de los 17 ODS</span>
                <span style="font-size: 0.8rem; color: var(--text-muted); font-weight: normal;">Pasa el cursor para ver detalles</span>
            </div>
            <div class="sdg-grid">
                {''.join(cards_html)}
            </div>
        </section>

        <section class="sdg-section">
            <div class="section-title">
                <span>Distribución Detallada e Indicadores de Impacto Normalizado</span>
            </div>
            <table>
                <thead>
                    <tr>
                        <th style="text-align: center; width: 60px;">ODS</th>
                        <th style="text-align: left;">Objetivo de Desarrollo Sostenible</th>
                        <th style="text-align: right;">Publicaciones</th>
                        <th style="text-align: right;">% Corpus</th>
                        <th style="text-align: right;">Citas Totales</th>
                        <th style="text-align: right;">FWCI Promedio</th>
                        <th style="text-align: right;">Top 10%</th>
                        <th style="text-align: right;">OA Diamante</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(table_rows)}
                </tbody>
            </table>
        </section>
    </div>
</body>
</html>
"""
    return html


def generate_markdown_report(data: Dict[str, Any], title: str) -> str:
    stats = data["sdg_stats"]
    total_docs = data["total_docs"]
    docs_sdg = data["docs_with_sdg"]
    cov_pct = data["coverage_pct"]

    active_sdgs = [s for s in stats.values() if s["publications_count"] > 0]
    active_sdgs.sort(key=lambda x: x["publications_count"], reverse=True)

    lines = [
        f"# {title}",
        "",
        "## Resumen Ejecutivo de Alineación ODS (Agenda 2030 ONU)",
        f"- **Corpus Total Analizado:** {total_docs:,} publicaciones.",
        f"- **Publicaciones vinculadas a ODS:** {docs_sdg:,} ({cov_pct:.2f}% de cobertura temática).",
        f"- **ODS con Presencia Activa:** {len(active_sdgs)} de 17 objetivos.",
        "",
        "| ODS | Objetivo de Desarrollo Sostenible | Publicaciones | % del Total | Citas Totales | FWCI Promedio | Top 10% (%) | OA Diamante (%) |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]

    for s in active_sdgs:
        lines.append(
            f"| **ODS {s['sdg_num']}** | {s['name']} | {s['publications_count']:,} | {s['share_pct']:.2f}% | "
            f"{s['total_citations']:,} | {s['mean_fwci']:.2f} | {s['top_10_pct']:.1f}% | {s['diamond_pct']:.1f}% |"
        )

    lines.append("")
    lines.append("## Artículos Clave por ODS Prioritarios")
    for s in active_sdgs[:5]:
        lines.append(f"### ODS {s['sdg_num']}: {s['name']} ({s['publications_count']} docs, FWCI={s['mean_fwci']:.2f})")
        for p in s["sample_papers"]:
            doi_str = f" [DOI: {p['doi']}]" if p.get("doi") else ""
            lines.append(f"- *{p['title']}* ({p['year'] or 'S/A'}). Citas: {p['citations']}.{doi_str}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="SDG Impact Intelligence CLI: Mapeo y generación dual (HTML interactivo + PNG 300 DPI ES/EN)."
    )
    parser.add_argument(
        "--workspace",
        "-w",
        default=".",
        help="Directorio del workspace (default: directorio actual).",
    )
    parser.add_argument(
        "--input",
        "-i",
        default=None,
        help="Ruta al archivo tabular (.parquet, .json, .csv). Si se omite, busca corpus.parquet en el workspace.",
    )
    parser.add_argument(
        "--sdg-col",
        default=None,
        help="Nombre explícito de la columna de ODS (default: auto-detecta 'sdgs', 'sdg_ids', 'ODS_ID', etc.).",
    )
    parser.add_argument(
        "--title",
        default="Alineación Científica con los 17 Objetivos de Desarrollo Sostenible (Agenda 2030)",
        help="Título del reporte y dashboard HTML.",
    )
    parser.add_argument(
        "--output-html",
        default=None,
        help="Ruta del archivo HTML resultante (default: <workspace>/reportes/sdg_impact_dashboard.html).",
    )
    parser.add_argument(
        "--output-png-es",
        default=None,
        help="Ruta de la imagen de publicación en español (default: <workspace>/reportes/sdg_grid_es.png).",
    )
    parser.add_argument(
        "--output-png-en",
        default=None,
        help="Ruta de la imagen de publicación en inglés (default: <workspace>/reportes/sdg_grid_en.png).",
    )
    parser.add_argument(
        "--output-json",
        default=None,
        help="Ruta del archivo JSON de métricas (default: <workspace>/reportes/sdg_impact_summary.json).",
    )
    parser.add_argument(
        "--output-md",
        default=None,
        help="Ruta del archivo Markdown resultante (default: <workspace>/reportes/sdg_impact_report.md).",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Resolución DPI para las imágenes de publicación PNG (default: 300).",
    )

    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    reports_dir = workspace / "reportes"
    reports_dir.mkdir(parents=True, exist_ok=True)

    input_path = resolve_input_path(workspace, args.input)
    print(f"[*] Leyendo corpus desde: {input_path}")
    df = load_corpus(input_path)
    print(f"[*] Registros cargados: {len(df):,}")

    data = compute_sdg_metrics(df, custom_sdg_col=args.sdg_col)
    data["input_path"] = str(input_path)
    data["title"] = args.title

    html_path = Path(args.output_html) if args.output_html else reports_dir / "sdg_impact_dashboard.html"
    png_es_path = Path(args.output_png_es) if args.output_png_es else reports_dir / "sdg_grid_es.png"
    png_en_path = Path(args.output_png_en) if args.output_png_en else reports_dir / "sdg_grid_en.png"
    json_path = Path(args.output_json) if args.output_json else reports_dir / "sdg_impact_summary.json"
    md_path = Path(args.output_md) if args.output_md else reports_dir / "sdg_impact_report.md"

    # 1. Guardar JSON
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[+] Resumen JSON guardado en: {json_path}")

    # 2. Guardar Markdown
    md_content = generate_markdown_report(data, args.title)
    md_path.write_text(md_content, encoding="utf-8")
    print(f"[+] Reporte Markdown guardado en: {md_path}")

    # 3. Guardar HTML Dashboard interactivo
    html_content = render_html_dashboard(data, args.title)
    html_path.write_text(html_content, encoding="utf-8")
    print(f"[+] Dashboard interactivo HTML guardado en: {html_path}")

    # 4. Guardar Cuadrículas PNG de Publicación a 300 DPI (ES y EN)
    render_sdg_grid_image(data, png_es_path, lang="es", dpi=args.dpi)
    print(f"[+] Cuadrícula PNG para publicación (ES, {args.dpi} DPI): {png_es_path}")

    render_sdg_grid_image(data, png_en_path, lang="en", dpi=args.dpi)
    print(f"[+] Cuadrícula PNG para publicación (EN, {args.dpi} DPI): {png_en_path}")

    print("\n--- RESUMEN EJECUTIVO ODS ---")
    print(f"Total documentos: {data['total_docs']:,}")
    print(f"Documentos con ODS: {data['docs_with_sdg']:,} ({data['coverage_pct']}%)")
    active_sdgs = sorted(
        [s for s in data["sdg_stats"].values() if s["publications_count"] > 0],
        key=lambda x: x["publications_count"],
        reverse=True,
    )
    for s in active_sdgs[:5]:
        print(f"  - ODS {s['sdg_num']} ({s['name']}): {s['publications_count']:,} docs ({s['share_pct']}%), FWCI={s['mean_fwci']:.2f}")


if __name__ == "__main__":
    main()
