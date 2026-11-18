#!/usr/bin/env python3
"""
track_longitudinal_lineages.py

Seguimiento de Linajes Temáticos Longitudinales y Generador de Diagramas Aluviales (Alluvial Diagrams).
Implementa el marco formal de Rosvall & Bergstrom (2010) y Shibata et al. (2011):
  1. Segmentación en ventanas cronológicas móviles solapadas (default: width=3 años, step=1 año).
  2. Emparejamiento intertemporal mediante Índice de Jaccard sobre referencias compartidas y Métrica AMI.
  3. Clasificación formal de 5 eventos evolutivos:
     - Persistencia (Continuidad)
     - Escisión (Bifurcación / Split)
     - Fusión (Convergencia / Merge)
     - Génesis (Emergencia de frente de ruptura)
     - Disolución (Obsolescencia / Decay)
  4. Generación de artefacto interactivo HTML autónomo (Plotly Sankey/Alluvial) y tabla lineages_summary.csv.

Uso:
  /home/ambientesPy/revistaslatam/bin/python track_longitudinal_lineages.py --input-file reports/works_with_fronts.parquet
"""

import os
import sys
import json
import argparse
import logging
from typing import List, Dict, Any, Tuple, Set, Optional

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_mutual_info_score
import plotly.graph_objects as go

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("track_longitudinal_lineages")


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Seguimiento de Linajes Longitudinales y Generación de Diagramas Aluviales"
    )
    parser.add_argument(
        "--input-file", "-i",
        type=str,
        default=None,
        help="Ruta al archivo enriquecido con frentes (works_with_fronts.parquet o CSV)."
    )
    parser.add_argument(
        "--window-width", "-w",
        type=int,
        default=3,
        help="Ancho de cada ventana temporal en años (default: 3)"
    )
    parser.add_argument(
        "--step-size", "-s",
        type=int,
        default=1,
        help="Desplazamiento anual entre ventanas sucesivas (default: 1)"
    )
    parser.add_argument(
        "--min-similarity",
        type=float,
        default=0.12,
        help="Umbral mínimo de similitud para registrar transición/flujo aluvial (default: 0.12)"
    )
    parser.add_argument(
        "--persistence-threshold",
        type=float,
        default=0.30,
        help="Umbral de similitud para considerar persistencia unívoca (default: 0.30)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="./reports",
        help="Target directory to save generated artifacts (default: ./reports)"
    )
    parser.add_argument(
        "--lang",
        type=str,
        choices=["en", "es"],
        default="en",
        help="Output language for alluvial chart and event labels (default: en)"
    )
    return parser.parse_args()


def load_data(input_file: Optional[str]) -> pd.DataFrame:
    path = input_file
    if not path:
        candidates = [
            "reports/works_with_fronts.parquet",
            "works_with_fronts.parquet",
            "corpus_with_fronts.parquet",
            "reports/works_with_fronts.csv",
            "corpus.parquet"
        ]
        for c in candidates:
            if os.path.exists(c):
                path = c
                break

    if not path or not os.path.exists(path):
        logger.error(f"No se encontró archivo de entrada en: {path}. Ejecute primero build_bibliometric_fronts.py.")
        sys.exit(1)

    logger.info(f"Cargando dataset enriquecido con frentes desde: {path}")
    if path.endswith(".parquet"):
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path)

    # Validar columnas críticas
    if "publication_year" not in df.columns:
        logger.error("El dataset no cuenta con columna 'publication_year'. Abortando.")
        sys.exit(1)

    # Asegurar columna front_id
    if "front_id" not in df.columns:
        if "topic_id" in df.columns:
            df["front_id"] = df["topic_id"]
            df["front_name"] = df.get("topic", df["topic_id"])
        else:
            logger.error("No se encontró columna 'front_id' ni 'topic_id'. Ejecute primero build_bibliometric_fronts.py.")
            sys.exit(1)

    df["publication_year"] = pd.to_numeric(df["publication_year"], errors="coerce")
    df = df[df["publication_year"].notna() & (df["publication_year"] > 1950)].copy()
    df["publication_year"] = df["publication_year"].astype(int)

    return df


def extract_references_set(series) -> Set[str]:
    """Extrae conjunto de referencias bibliográficas únicas de un grupo."""
    refs = set()
    for item in series:
        if isinstance(item, (list, np.ndarray)):
            for x in item:
                if str(x).strip():
                    refs.add(str(x).strip())
        elif isinstance(item, str):
            item_str = item.strip()
            if item_str.startswith("[") and item_str.endswith("]"):
                try:
                    import json
                    parsed = json.loads(item_str.replace("'", '"'))
                    refs.update([str(x).strip() for x in parsed if str(x).strip()])
                except Exception:
                    refs.update([x.strip().strip("'\"") for x in item_str[1:-1].split(",") if x.strip()])
            else:
                refs.update([x.strip() for x in item_str.split(";") if x.strip()])
    return refs


def compute_windows(df: pd.DataFrame, width: int, step: int) -> List[Tuple[str, int, int]]:
    min_year = df["publication_year"].min()
    max_year = df["publication_year"].max()

    if max_year - min_year < width:
        width = max(1, max_year - min_year + 1)
        step = 1

    windows = []
    current_start = min_year
    while current_start + width - 1 <= max_year:
        end_year = current_start + width - 1
        label = f"W_{current_start}_{end_year}"
        windows.append((label, current_start, end_year))
        current_start += step

    return windows


def main():
    args = parse_arguments()
    os.makedirs(args.output_dir, exist_ok=True)

    logger.info("=== INICIANDO RASTREO LONGITUDINAL DE LINAJES ALUVIALES (AMI) ===")
    df = load_data(args.input_file)
    logger.info(f"Total documentos analizados: {len(df):,}")

    windows = compute_windows(df, args.window_width, args.step_size)
    if len(windows) < 2:
        logger.warning(f"Rango temporal insuficiente para construir múltiples ventanas solapadas ({len(windows)} ventana). Se requieren al menos 2 ventanas.")
        # Forzar ventanas dividiendo el rango
        min_y, max_y = df["publication_year"].min(), df["publication_year"].max()
        mid_y = (min_y + max_y) // 2
        windows = [
            (f"W_{min_y}_{mid_y}", min_y, mid_y),
            (f"W_{mid_y+1}_{max_y}", mid_y + 1, max_y)
        ]
        logger.info(f"Ventanas adaptativas generadas: {windows}")

    logger.info(f"Ventanas cronológicas generadas ({len(windows)} ventanas):")
    for w_label, y_start, y_end in windows:
        n_w = len(df[(df["publication_year"] >= y_start) & (df["publication_year"] <= y_end)])
        logger.info(f"  - {w_label} ({y_start}–{y_end}): {n_w:,} documentos")

    # Mapear clusters y referencias por ventana
    ref_col = "referenced_works_clean" if "referenced_works_clean" in df.columns else ("referenced_works" if "referenced_works" in df.columns else None)

    window_fronts_data = {}  # w_idx -> { front_id -> { "name": ..., "docs": df_sub, "refs": set() } }

    for w_idx, (w_label, y_start, y_end) in enumerate(windows):
        sub_w = df[(df["publication_year"] >= y_start) & (df["publication_year"] <= y_end)]
        active_f = [f for f in sub_w["front_id"].unique() if str(f) not in ["0", "Residual / Isolated Works"]]
        window_fronts_data[w_idx] = {}

        for f_id in active_f:
            f_docs = sub_w[sub_w["front_id"] == f_id]
            f_name = f_docs["front_name"].iloc[0] if "front_name" in f_docs.columns else f"Front {f_id}"
            refs = extract_references_set(f_docs[ref_col]) if ref_col else set(f_docs["id"].astype(str))
            window_fronts_data[w_idx][f_id] = {
                "name": f_name,
                "count": len(f_docs),
                "refs": refs,
                "doc_ids": set(f_docs["id"].astype(str))
            }

    # Emparejamiento intertemporal, matriz completa y cálculo AMI
    events_records = []
    similarity_matrix_records = []
    ami_window_records = []
    sankey_nodes = []
    sankey_node_map = {}  # (w_idx, front_id) -> sankey_idx
    sankey_links = []
    node_counter = 0

    # Crear nodos para Sankey
    for w_idx, (w_label, y_start, y_end) in enumerate(windows):
        for f_id, f_data in window_fronts_data[w_idx].items():
            label = f"[{y_start}-{y_end}] {f_data['name']} (N={f_data['count']})"
            sankey_nodes.append(label)
            sankey_node_map[(w_idx, f_id)] = node_counter
            node_counter += 1

    # Analizar transiciones entre ventanas contiguas
    for w_idx in range(len(windows) - 1):
        w_prev_label, p_s, p_e = windows[w_idx]
        w_curr_label, c_s, c_e = windows[w_idx + 1]
        fronts_prev = window_fronts_data[w_idx]
        fronts_curr = window_fronts_data[w_idx + 1]

        # AMI / NMI entre particiones de ventanas contiguas sobre documentos compartidos
        sub_p = df[(df["publication_year"] >= p_s) & (df["publication_year"] <= p_e)]
        sub_c = df[(df["publication_year"] >= c_s) & (df["publication_year"] <= c_e)]
        map_p = {str(r["id"]): int(r["front_id"]) for _, r in sub_p.iterrows() if str(r.get("front_id", 0)) not in ["0", "Residual / Isolated Works"]}
        map_c = {str(r["id"]): int(r["front_id"]) for _, r in sub_c.iterrows() if str(r.get("front_id", 0)) not in ["0", "Residual / Isolated Works"]}
        shared_ids = sorted(set(map_p.keys()).intersection(map_c.keys()))
        ami_val, nmi_val = 0.0, 0.0
        if len(shared_ids) >= 2:
            try:
                from sklearn.metrics import adjusted_mutual_info_score, normalized_mutual_info_score
                l_p = [map_p[k] for k in shared_ids]
                l_c = [map_c[k] for k in shared_ids]
                ami_val = round(float(adjusted_mutual_info_score(l_p, l_c)), 6)
                nmi_val = round(float(normalized_mutual_info_score(l_p, l_c)), 6)
            except Exception:
                pass
        ami_window_records.append({
            "source_window": w_prev_label,
            "target_window": w_curr_label,
            "n_fronts_prev": len(fronts_prev),
            "n_fronts_curr": len(fronts_curr),
            "shared_docs": len(shared_ids),
            "ami": ami_val,
            "nmi": nmi_val,
        })

        # Calcular matriz de similitud completa entre frentes (Full Evidence-First)
        for f_p_id, f_p in fronts_prev.items():
            outgoing_transitions = []
            for f_c_id, f_c in fronts_curr.items():
                u_refs = f_p["refs"].union(f_c["refs"])
                i_refs = f_p["refs"].intersection(f_c["refs"])
                j_score = (len(i_refs) / len(u_refs)) if u_refs else 0.0

                u_docs = f_p["doc_ids"].union(f_c["doc_ids"])
                i_docs = f_p["doc_ids"].intersection(f_c["doc_ids"])
                doc_overlap = (len(i_docs) / len(u_docs)) if u_docs else 0.0

                combined_score = (0.7 * j_score) + (0.3 * doc_overlap)
                passed = combined_score >= args.min_similarity
                similarity_matrix_records.append({
                    "source_window": w_prev_label,
                    "source_front_id": f_p_id,
                    "source_front": f_p["name"],
                    "target_window": w_curr_label,
                    "target_front_id": f_c_id,
                    "target_front": f_c["name"],
                    "jaccard_refs": round(j_score, 6),
                    "jaccard_docs": round(doc_overlap, 6),
                    "combined_score": round(combined_score, 6),
                    "shared_refs_count": len(i_refs),
                    "shared_docs_count": len(i_docs),
                    "passed_threshold": passed,
                })

                if passed:
                    outgoing_transitions.append((f_c_id, f_c["name"], combined_score, len(i_refs) + len(i_docs)))

            # Event classification
            is_es = (getattr(args, "lang", "en") == "es")
            if len(outgoing_transitions) == 1:
                target_id, target_name, score, flow_weight = outgoing_transitions[0]
                if is_es:
                    event_type = "Persistencia" if score >= args.persistence_threshold else "Evolución"
                else:
                    event_type = "Persistence" if score >= args.persistence_threshold else "Evolution"
                events_records.append({
                    "source_window": w_prev_label,
                    "source_front": f_p["name"],
                    "target_window": w_curr_label,
                    "target_front": target_name,
                    "event_type": event_type,
                    "similarity_score": round(score, 4),
                    "flow_weight": max(1, flow_weight)
                })
                sankey_links.append({
                    "source": sankey_node_map[(w_idx, f_p_id)],
                    "target": sankey_node_map[(w_idx + 1, target_id)],
                    "value": max(1, flow_weight)
                })
            elif len(outgoing_transitions) > 1:
                # Split event
                for target_id, target_name, score, flow_weight in outgoing_transitions:
                    events_records.append({
                        "source_window": w_prev_label,
                        "source_front": f_p["name"],
                        "target_window": w_curr_label,
                        "target_front": target_name,
                        "event_type": "Split (Bifurcación)" if is_es else "Split (Bifurcation)",
                        "similarity_score": round(score, 4),
                        "flow_weight": max(1, flow_weight)
                    })
                    sankey_links.append({
                        "source": sankey_node_map[(w_idx, f_p_id)],
                        "target": sankey_node_map[(w_idx + 1, target_id)],
                        "value": max(1, flow_weight)
                    })
            else:
                # Dissolution / Decay event
                events_records.append({
                    "source_window": w_prev_label,
                    "source_front": f_p["name"],
                    "target_window": w_curr_label,
                    "target_front": "None (Disolución)" if is_es else "None (Dissolution)",
                    "event_type": "Decay (Disolución)" if is_es else "Decay (Dissolution)",
                    "similarity_score": 0.0,
                    "flow_weight": 0
                })

        # Identify Genesis (Emergence) events in current window
        is_es = (getattr(args, "lang", "en") == "es")
        for f_c_id, f_c in fronts_curr.items():
            incoming_scores = []
            for f_p_id, f_p in fronts_prev.items():
                u_refs = f_p["refs"].union(f_c["refs"])
                i_refs = f_p["refs"].intersection(f_c["refs"])
                score = (len(i_refs) / len(u_refs)) if u_refs else 0.0
                incoming_scores.append(score)

            if not incoming_scores or max(incoming_scores) < args.min_similarity:
                events_records.append({
                    "source_window": w_prev_label,
                    "source_front": "None (Génesis)" if is_es else "None (Genesis)",
                    "target_window": w_curr_label,
                    "target_front": f_c["name"],
                    "event_type": "Genesis (Emergencia)" if is_es else "Genesis (Emergence)",
                    "similarity_score": 0.0,
                    "flow_weight": 0
                })

    # Save Events Summary Table + Full Similarity Matrix + AMI Window Summary
    events_df = pd.DataFrame(events_records)
    lineages_path = os.path.join(args.output_dir, "lineages_summary.csv")
    events_df.to_csv(lineages_path, index=False)
    logger.info(f"Tabla de linajes longitudinales guardada en: {lineages_path} ({len(events_df)} transiciones registradas).")

    sim_mat_path = os.path.join(args.output_dir, "lineage_similarity_matrix.csv")
    pd.DataFrame(similarity_matrix_records).to_csv(sim_mat_path, index=False)
    ami_path = os.path.join(args.output_dir, "ami_window_summary.csv")
    pd.DataFrame(ami_window_records).to_csv(ami_path, index=False)
    logger.info(f"Matriz completa de similitud ({len(similarity_matrix_records)} pares) y AMI por ventana guardadas en: {sim_mat_path}, {ami_path}")

    alluvial_html_path = os.path.join(args.output_dir, "alluvial_lineages.html")
    # Render Interactive Alluvial Diagram in HTML with Plotly
    if sankey_links and sankey_nodes:
        logger.info("Construyendo Diagrama Aluvial interactivo con Plotly...")
        is_es = (getattr(args, "lang", "en") == "es")
        fig = go.Figure(data=[go.Sankey(
            arrangement="snap",
            node=dict(
                pad=18,
                thickness=25,
                line=dict(color="#2c3e50", width=0.8),
                label=sankey_nodes,
                color="rgba(31, 119, 180, 0.85)"
            ),
            link=dict(
                source=[link["source"] for link in sankey_links],
                target=[link["target"] for link in sankey_links],
                value=[link["value"] for link in sankey_links],
                color="rgba(149, 165, 166, 0.45)"
            )
        )])

        title_html = (
            "<b>Dinámica Longitudinal de Linajes Temáticos (Diagrama Aluvial de Frentes)</b><br><sup>Seguimiento temporal de eventos evolutivos (Persistencia, Bifurcación, Fusión, Emergencia)</sup>"
            if is_es
            else "<b>Longitudinal Dynamics of Thematic Lineages (Research Fronts Alluvial Diagram)</b><br><sup>Temporal tracking of evolutionary events (Persistence, Split, Merge, Genesis)</sup>"
        )
        fig.update_layout(
            title_text=title_html,
            font_size=12,
            font_family="Arial, sans-serif",
            width=1200,
            height=700,
            template="plotly_white"
        )

        fig.write_html(alluvial_html_path, include_plotlyjs="cdn")
        logger.info(f"Diagrama Aluvial interactivo guardado en: {alluvial_html_path}")
    else:
        logger.warning("No se generaron enlaces suficientes para renderizar el diagrama aluvial Sankey.")

    # Render static 300 DPI Alluvial / Sankey PNGs (EN & ES) without kaleido dependency
    alluvial_png_en = os.path.join(args.output_dir, "alluvial_lineages_en.png")
    alluvial_png_es = os.path.join(args.output_dir, "alluvial_lineages_es.png")

    def _render_alluvial_png(out_png: str, fig_lang: str) -> bool:
        if not window_fronts_data or not windows:
            return False
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from matplotlib.patches import FancyBboxPatch, PathPatch
            from matplotlib.path import Path as MplPath
        except Exception:
            return False

        is_es_fig = (fig_lang == "es")
        palette = [
            "#1d4ed8", "#059669", "#d97706", "#7c3aed", "#dc2626",
            "#0891b2", "#db2777", "#65a30d", "#ea580c", "#4f46e5",
        ]
        n_w = len(windows)
        fig_w = max(12.0, 3.3 * n_w)
        fig_ax, ax = plt.subplots(figsize=(fig_w, 7.6), dpi=300, facecolor="white")
        ax.set_facecolor("#fbfcfd")

        # Compute vertical positions per window proportional to front document count
        bar_w = 0.22
        x_positions = [i * 1.4 for i in range(n_w)]
        node_boxes = {}  # (w_idx, f_id) -> (x0, x1, y0, y1, color, count, name)
        max_col_total = max(
            [sum(fd["count"] for fd in window_fronts_data[wi].values()) for wi in range(n_w)] + [1]
        )

        # Assign consistent color by front_id across windows
        all_fids = sorted({fid for wi in range(n_w) for fid in window_fronts_data[wi].keys()})
        fid_color = {fid: palette[idx % len(palette)] for idx, fid in enumerate(all_fids)}

        for wi in range(n_w):
            items = sorted(window_fronts_data[wi].items(), key=lambda kv: kv[1]["count"], reverse=True)
            col_total = max(1, sum(fd["count"] for _, fd in items))
            gap = 0.045 * max_col_total
            total_span = col_total + max(0, len(items) - 1) * gap
            y_cursor = max_col_total * 1.18
            scale = (max_col_total * 0.95) / max(total_span, 1e-6)
            x0 = x_positions[wi] - bar_w / 2.0
            x1 = x_positions[wi] + bar_w / 2.0

            for fid, fd in items:
                h = max(0.025 * max_col_total, fd["count"] * scale)
                y1 = y_cursor
                y0 = y1 - h
                y_cursor = y0 - gap * scale
                col = fid_color[fid]
                node_boxes[(wi, fid)] = (x0, x1, y0, y1, col, fd["count"], fd["name"])
                ax.add_patch(FancyBboxPatch(
                    (x0, y0), bar_w, h, boxstyle="round,pad=0.0,rounding_size=0.02",
                    facecolor=col, edgecolor="white", linewidth=1.0, alpha=0.90, zorder=4
                ))
                lbl_name = fd["name"] if len(fd["name"]) <= 24 else fd["name"][:21] + "..."
                lbl_txt = f"{lbl_name}\n(N={fd['count']})"
                tx = x1 + 0.03 if wi < n_w - 1 else x0 - 0.03
                ha = "left" if wi < n_w - 1 else "right"
                ax.text(tx, 0.5 * (y0 + y1), lbl_txt, fontsize=7.5, color="#0f172a",
                        ha=ha, va="center", zorder=6,
                        bbox=dict(boxstyle="round,pad=0.14", facecolor="white", edgecolor="#e2e8f0", alpha=0.84))

            w_lbl, ys, ye = windows[wi]
            ax.text(x_positions[wi], max_col_total * 1.24, f"{ys}–{ye}", fontsize=10.5,
                    fontweight="bold", color="#0f172a", ha="center", va="bottom")

        # Track cumulative offsets on source/target rectangles for clean Bezier ribbons
        idx_to_wf = {idx: wf for wf, idx in sankey_node_map.items()}
        src_used = {k: 0.0 for k in node_boxes}
        tgt_used = {k: 0.0 for k in node_boxes}
        src_tot = {k: 0.0 for k in node_boxes}
        tgt_tot = {k: 0.0 for k in node_boxes}
        for lk in sankey_links:
            s_wf = idx_to_wf.get(lk["source"])
            t_wf = idx_to_wf.get(lk["target"])
            if s_wf in node_boxes and t_wf in node_boxes:
                val = max(1.0, float(lk["value"]))
                src_tot[s_wf] += val
                tgt_tot[t_wf] += val

        for lk in sankey_links:
            s_wf = idx_to_wf.get(lk["source"])
            t_wf = idx_to_wf.get(lk["target"])
            if s_wf not in node_boxes or t_wf not in node_boxes:
                continue
            sx0, sx1, sy0, sy1, scol, _, _ = node_boxes[s_wf]
            tx0, tx1, ty0, ty1, _, _, _ = node_boxes[t_wf]
            val = max(1.0, float(lk["value"]))
            sh = (sy1 - sy0) * (val / max(src_tot[s_wf], val))
            th = (ty1 - ty0) * (val / max(tgt_tot[t_wf], val))
            sy_top = sy1 - src_used[s_wf]
            sy_bot = sy_top - sh
            src_used[s_wf] += sh
            ty_top = ty1 - tgt_used[t_wf]
            ty_bot = ty_top - th
            tgt_used[t_wf] += th

            xm = 0.5 * (sx1 + tx0)
            verts = [
                (sx1, sy_top),
                (xm, sy_top), (xm, ty_top), (tx0, ty_top),
                (tx0, ty_bot),
                (xm, ty_bot), (xm, sy_bot), (sx1, sy_bot),
                (sx1, sy_top),
            ]
            codes = [
                MplPath.MOVETO,
                MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
                MplPath.LINETO,
                MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
                MplPath.CLOSEPOLY,
            ]
            ax.add_patch(PathPatch(MplPath(verts, codes), facecolor=scol, edgecolor="none", alpha=0.32, zorder=2))

        # Annotate AMI between consecutive window columns
        for wi, ami_r in enumerate(ami_window_records):
            if wi < n_w - 1:
                x_mid = 0.5 * (x_positions[wi] + x_positions[wi + 1])
                ami_txt = f"AMI={ami_r['ami']:.3f}\nNMI={ami_r['nmi']:.3f}"
                ax.text(x_mid, max_col_total * 1.24, ami_txt, fontsize=8.0, color="#1e293b",
                        ha="center", va="bottom",
                        bbox=dict(boxstyle="round,pad=0.2", facecolor="#f1f5f9", edgecolor="#cbd5e1"))

        ax.set_title(
            "Dinámica Longitudinal de Frentes de Investigación (Diagrama Aluvial)" if is_es_fig
            else "Longitudinal Dynamics of Research Fronts (Alluvial Diagram)",
            fontsize=13.0, fontweight="bold", pad=22, color="#0f172a",
        )
        ax.set_xlim(x_positions[0] - 0.55, x_positions[-1] + 0.55)
        ax.set_ylim(-0.08 * max_col_total, max_col_total * 1.38)
        ax.axis("off")
        fig_ax.tight_layout()
        fig_ax.savefig(out_png, dpi=300, bbox_inches="tight", facecolor="white")
        plt.close(fig_ax)
        return os.path.exists(out_png)

    has_png_en = _render_alluvial_png(alluvial_png_en, "en")
    has_png_es = _render_alluvial_png(alluvial_png_es, "es")
    if has_png_en or has_png_es:
        logger.info(f"Diagrama Aluvial 300 DPI PNG guardado en: {alluvial_png_en} | {alluvial_png_es}")

    manifest_path = os.path.join(args.output_dir, "lineages_run_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as mf:
        json.dump({
            "pipeline": "track-longitudinal-lineages",
            "parameters": vars(args),
            "windows": [{"label": w[0], "start": int(w[1]), "end": int(w[2])} for w in windows],
            "ami_window_summary": ami_window_records,
            "artifacts": {
                "lineages_summary_csv": lineages_path,
                "lineage_similarity_matrix_csv": sim_mat_path,
                "ami_window_summary_csv": ami_path,
                "alluvial_lineages_html": alluvial_html_path if (sankey_links and sankey_nodes) else None,
                "alluvial_lineages_en_png": alluvial_png_en if has_png_en else None,
                "alluvial_lineages_es_png": alluvial_png_es if has_png_es else None,
            },
        }, mf, indent=2, ensure_ascii=False, default=str)

    logger.info("=== SEGUIMIENTO LONGITUDINAL DE LINAJES COMPLETADO EXITOSAMENTE ===")


if __name__ == "__main__":
    main()
