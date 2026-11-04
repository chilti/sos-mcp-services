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
        help="Directorio destino para guardar los artefactos (default: ./reports)"
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

    # Emparejamiento intertemporal y cálculo de eventos
    events_records = []
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
        w_prev_label = windows[w_idx][0]
        w_curr_label = windows[w_idx + 1][0]
        fronts_prev = window_fronts_data[w_idx]
        fronts_curr = window_fronts_data[w_idx + 1]

        # Calcular matriz de similitud de Jaccard entre frentes
        for f_p_id, f_p in fronts_prev.items():
            outgoing_transitions = []
            for f_c_id, f_c in fronts_curr.items():
                # Jaccard sobre referencias compartidas
                u_refs = f_p["refs"].union(f_c["refs"])
                i_refs = f_p["refs"].intersection(f_c["refs"])
                j_score = (len(i_refs) / len(u_refs)) if u_refs else 0.0

                # Solapamiento directo de documentos
                u_docs = f_p["doc_ids"].union(f_c["doc_ids"])
                i_docs = f_p["doc_ids"].intersection(f_c["doc_ids"])
                doc_overlap = (len(i_docs) / len(u_docs)) if u_docs else 0.0

                # Score combinado
                combined_score = (0.7 * j_score) + (0.3 * doc_overlap)

                if combined_score >= args.min_similarity:
                    outgoing_transitions.append((f_c_id, f_c["name"], combined_score, len(i_refs) + len(i_docs)))

            # Clasificación de eventos
            if len(outgoing_transitions) == 1:
                target_id, target_name, score, flow_weight = outgoing_transitions[0]
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
                # Evento Split (Bifurcación)
                for target_id, target_name, score, flow_weight in outgoing_transitions:
                    events_records.append({
                        "source_window": w_prev_label,
                        "source_front": f_p["name"],
                        "target_window": w_curr_label,
                        "target_front": target_name,
                        "event_type": "Split (Bifurcación)",
                        "similarity_score": round(score, 4),
                        "flow_weight": max(1, flow_weight)
                    })
                    sankey_links.append({
                        "source": sankey_node_map[(w_idx, f_p_id)],
                        "target": sankey_node_map[(w_idx + 1, target_id)],
                        "value": max(1, flow_weight)
                    })
            else:
                # Evento Dissolution / Decay
                events_records.append({
                    "source_window": w_prev_label,
                    "source_front": f_p["name"],
                    "target_window": w_curr_label,
                    "target_front": "None (Disolución)",
                    "event_type": "Decay (Disolución)",
                    "similarity_score": 0.0,
                    "flow_weight": 0
                })

        # Identificar eventos Genesis (Emergencia) en ventana actual
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
                    "source_front": "None (Génesis)",
                    "target_window": w_curr_label,
                    "target_front": f_c["name"],
                    "event_type": "Genesis (Emergencia)",
                    "similarity_score": 0.0,
                    "flow_weight": 0
                })

    # Guardar Tabla Resumen de Eventos (lineages_summary.csv)
    events_df = pd.DataFrame(events_records)
    lineages_path = os.path.join(args.output_dir, "lineages_summary.csv")
    events_df.to_csv(lineages_path, index=False)
    logger.info(f"Tabla de linajes longitudinales guardada en: {lineages_path} ({len(events_df)} transiciones registradas).")

    # Renderizar Diagrama Aluvial Interactivo en HTML con Plotly
    if sankey_links and sankey_nodes:
        logger.info("Construyendo Diagrama Aluvial interactivo con Plotly...")
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

        fig.update_layout(
            title_text="<b>Dinámica Longitudinal de Linajes Temáticos (Diagrama Aluvial de Frentes)</b><br><sup>Seguimiento temporal de eventos evolutivos (Persistencia, Bifurcación, Fusión, Emergencia)</sup>",
            font_size=12,
            font_family="Arial, sans-serif",
            width=1200,
            height=700,
            template="plotly_white"
        )

        alluvial_html_path = os.path.join(args.output_dir, "alluvial_lineages.html")
        fig.write_html(alluvial_html_path, include_plotlyjs="cdn")
        logger.info(f"Diagrama Aluvial interactivo guardado en: {alluvial_html_path}")
    else:
        logger.warning("No se generaron enlaces suficientes para renderizar el diagrama aluvial Sankey.")

    logger.info("=== SEGUIMIENTO LONGITUDINAL DE LINAJES COMPLETADO EXITOSAMENTE ===")


if __name__ == "__main__":
    main()
