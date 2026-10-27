#!/usr/bin/env python3
"""
CLI Helper: Bibliometrix Python Orchestrator & Bridge
Orquesta el análisis de mapeo científico con R bibliometrix o genera
recetas reproducibles y diagramas temáticos de Callon (1991).

Uso:
  python scripts/bibliometrix_cli.py generate-script --input corpus.csv --output run_analysis.R --analysis thematic
  python scripts/bibliometrix_cli.py run --input corpus.csv --command summary --output summary.json
  python scripts/bibliometrix_cli.py callon-map --input corpus.parquet --output callon_themes.json --plot-output callon.png
"""

import sys
import os
import json
import argparse
import subprocess
import shutil
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Any, Optional

import numpy as np


def check_rscript_available() -> bool:
    """Verifica si Rscript está en el PATH del sistema."""
    return shutil.which("Rscript") is not None


def generate_r_recipe(input_path: str, output_path: str, analysis: str, field: str = "DE") -> str:
    """Genera un script de R listo para ejecutar en RStudio o terminal."""
    clean_input = input_path.replace("\\", "/")
    clean_output = output_path.replace("\\", "/")

    script_template = f"""# ==============================================================================
# Script Reproducible de Bibliometrix
# Generado automáticamente por bibliometrix_cli.py (SOS MCP Services - UNAM)
# ==============================================================================

if (!require("bibliometrix")) install.packages("bibliometrix")
library(bibliometrix)

# 1. Carga y conversión de datos
archivo_datos <- "{clean_input}"
cat("Cargando dataset:", archivo_datos, "\\n")

# Detectar formato por extensión
formato <- if (grepl("\\\\.csv$", archivo_datos, ignore.case = TRUE)) "csv" else "plaintext"
fuente <- if (grepl("scopus", archivo_datos, ignore.case = TRUE)) "scopus" else "wos"

M <- convert2df(file = archivo_datos, dbsource = fuente, format = formato)
cat("Dimensiones del corpus:", nrow(M), "documentos y", ncol(M), "variables.\\n")

# 2. Análisis seleccionado: {analysis}
"""

    if analysis == "summary":
        script_template += """
results <- biblioAnalysis(M, sep = ";")
S <- summary(results, k = 10, pause = FALSE)
plot(x = results, k = 10, pause = FALSE)
cat("Análisis descriptivo finalizado.\\n")
"""
    elif analysis == "co-citation":
        script_template += """
# Red de Co-citación
NetMatrix <- biblioNetwork(M, analysis = "co-citation", network = "references", sep = ";")
net <- networkPlot(NetMatrix, n = 40, Title = "Red de Co-citación de Referencias",
                   type = "fruchterman", size = TRUE, labelsize = 0.8)
"""
    elif analysis == "collaboration":
        script_template += """
# Red de Colaboración entre Autores
NetMatrix <- biblioNetwork(M, analysis = "collaboration", network = "authors", sep = ";")
net <- networkPlot(NetMatrix, n = 50, Title = "Red de Colaboración Científica",
                   type = "kamada", size = TRUE, labelsize = 0.8)
"""
    elif analysis == "thematic":
        script_template += f"""
# Diagrama Estratégico de Callon (1991)
Map <- thematicMap(M, field = "{field}", n = 250, minfreq = 3,
                  stemming = FALSE, size = 0.5, n.labels = 3, repel = TRUE)
plot(Map$map)
cat("Mapa temático de Callon renderizado con éxito.\\n")
"""
    elif analysis == "evolution":
        script_template += f"""
# Evolución Temática Longitudinal
nexus <- thematicEvolution(M, field = "{field}", n = 100, minFreq = 3)
plotThematicEvolution(nexus$Nodes, nexus$Edges)
"""
    elif analysis == "biblioshiny":
        script_template += """
# Lanzar interfaz web interactiva Biblioshiny
biblioshiny()
"""

    return script_template


def cmd_callon_map(args):
    """Calcula nativamente en Python el Diagrama Estratégico de Callon (Centralidad vs Densidad)."""
    input_path = args.input
    if not os.path.exists(input_path):
        sys.stderr.write(f"Error: No existe el archivo de entrada: {input_path}\n")
        sys.exit(1)

    # Cargar datos desde parquet, csv o json
    records = []
    if input_path.endswith(".parquet"):
        import pandas as pd
        df = pd.read_parquet(input_path)
        records = df.to_dict(orient="records")
    elif input_path.endswith(".csv"):
        import csv
        with open(input_path, "r", encoding="utf-8-sig", errors="replace") as f:
            records = list(csv.DictReader(f))
    elif input_path.endswith(".json"):
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            records = data.get("records", data) if isinstance(data, dict) else data

    if not records:
        sys.stderr.write("Error: El archivo de entrada no contiene registros legibles.\n")
        sys.exit(1)

    field_name = args.field or "keywords"
    # Extraer términos de palabras clave
    co_occurrences = defaultdict(int)
    term_counts = Counter()
    doc_keywords = []

    for r in records:
        raw_kw = (
            r.get("keywords") or r.get("Keywords") or r.get("DE") or r.get("ID") or
            r.get("author_keywords") or r.get("concepts") or ""
        )
        if isinstance(raw_kw, list):
            kws = [str(k).strip().lower() for k in raw_kw if str(k).strip()]
        else:
            kws = [k.strip().lower() for k in str(raw_kw).replace(",", ";").split(";") if k.strip()]

        # Filtrar términos muy cortos o genéricos
        kws = [k for k in kws if len(k) > 2]
        if kws:
            doc_keywords.append(kws)
            for k in kws:
                term_counts[k] += 1
            # Pares de coocurrencia
            for i in range(len(kws)):
                for j in range(i + 1, len(kws)):
                    t1, t2 = sorted([kws[i], kws[j]])
                    co_occurrences[(t1, t2)] += 1

    top_terms = [t for t, c in term_counts.most_common(args.top_terms)]
    if len(top_terms) < 4:
        sys.stderr.write("Error: Vocabulario de palabras clave insuficiente para clusterizar.\n")
        sys.exit(1)

    top_set = set(top_terms)
    # Construir grafo simple para clustering
    adj = defaultdict(dict)
    for (t1, t2), weight in co_occurrences.items():
        if t1 in top_set and t2 in top_set and weight >= args.min_freq:
            adj[t1][t2] = weight
            adj[t2][t1] = weight

    # Comunidades con algoritmo voraz o componentes conexas
    assigned_cluster = {}
    cluster_id = 1
    for term in top_terms:
        if term not in assigned_cluster:
            # BFS simple para agrupar términos fuertemente conectados
            neighbors = sorted(adj[term].items(), key=lambda x: -x[1])
            cluster_terms = [term] + [nb for nb, w in neighbors[:5] if nb not in assigned_cluster]
            for ct in cluster_terms:
                assigned_cluster[ct] = cluster_id
            cluster_id += 1

    # Agrupar clusters
    clusters_map = defaultdict(list)
    for t, cid in assigned_cluster.items():
        clusters_map[cid].append(t)

    # Calcular Callon Centrality y Callon Density por cluster
    cluster_metrics = []
    for cid, terms in clusters_map.items():
        if len(terms) < 2:
            continue
        term_set = set(terms)
        internal_edges = 0
        external_edges = 0

        for t in terms:
            for nb, w in adj[t].items():
                if nb in term_set:
                    internal_edges += w
                else:
                    external_edges += w

        # Callon formulas:
        # Centrality = 10 * sum(e_external)
        # Density = 100 * (sum(e_internal) / 2) / len(terms)
        centrality = round(float(external_edges * 10.0), 2)
        density = round(float((internal_edges / 2.0 * 100.0) / len(terms)), 2)

        cluster_metrics.append({
            "cluster_id": cid,
            "label": terms[0].title(),
            "terms": terms,
            "size": len(terms),
            "callon_centrality": centrality,
            "callon_density": density
        })

    if not cluster_metrics:
        sys.stderr.write("Error: No fue posible calcular métricas de clusters de Callon.\n")
        sys.exit(1)

    # Medianas para delimitar cuadrantes
    med_cent = float(np.median([c["callon_centrality"] for c in cluster_metrics]))
    med_dens = float(np.median([c["callon_density"] for c in cluster_metrics]))

    for c in cluster_metrics:
        high_cent = c["callon_centrality"] >= med_cent
        high_dens = c["callon_density"] >= med_dens

        if high_cent and high_dens:
            quadrant = "Cuadrante I: Temas Motores (Motor Themes)"
        elif not high_cent and high_dens:
            quadrant = "Cuadrante II: Temas de Nicho / Especializados (Niche Themes)"
        elif not high_cent and not high_dens:
            quadrant = "Cuadrante III: Temas Emergentes o Declinantes (Emerging/Declining)"
        else:
            quadrant = "Cuadrante IV: Temas Básicos y Transversales (Basic Themes)"

        c["quadrant"] = quadrant

    result = {
        "analysis": "Callon Strategic Diagram (Thematic Map)",
        "framework": "Callon (1991) / Aria & Cuccurullo (2017)",
        "total_documents_analyzed": len(records),
        "total_unique_keywords": len(term_counts),
        "median_centrality": round(med_cent, 2),
        "median_density": round(med_dens, 2),
        "clusters_count": len(cluster_metrics),
        "clusters": cluster_metrics
    }

    # Graficar si se solicita
    if args.plot_output:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        os.makedirs(os.path.dirname(os.path.abspath(args.plot_output)), exist_ok=True)
        plt.figure(figsize=(9, 7))

        cents = [c["callon_centrality"] for c in cluster_metrics]
        dens = [c["callon_density"] for c in cluster_metrics]
        sizes = [c["size"] * 50 for c in cluster_metrics]

        plt.scatter(cents, dens, s=sizes, color="#3b82f6", alpha=0.6, edgecolors="#1d4ed8", linewidth=1.5, zorder=3)

        for c in cluster_metrics:
            plt.annotate(c["label"], (c["callon_centrality"], c["callon_density"]),
                         fontsize=9, weight="bold", ha="center", va="bottom",
                         xytext=(0, 6), textcoords="offset points")

        # Líneas de cuadrantes en las medianas
        plt.axvline(med_cent, color="#dc2626", linestyle="--", alpha=0.7, label=f"Mediana Centralidad ({med_cent:.1f})")
        plt.axhline(med_dens, color="#16a34a", linestyle="--", alpha=0.7, label=f"Mediana Densidad ({med_dens:.1f})")

        # Cuadrantes anotaciones
        xlim = plt.xlim()
        ylim = plt.ylim()
        plt.text(xlim[1] * 0.95, ylim[1] * 0.95, "I. Motores", color="#1e3a8a", fontsize=11, weight="bold", ha="right", va="top")
        plt.text(xlim[0] + (xlim[1] - xlim[0]) * 0.05, ylim[1] * 0.95, "II. Nicho", color="#701a75", fontsize=11, weight="bold", ha="left", va="top")
        plt.text(xlim[0] + (xlim[1] - xlim[0]) * 0.05, ylim[0] + (ylim[1] - ylim[0]) * 0.05, "III. Emergentes", color="#854d0e", fontsize=11, weight="bold", ha="left", va="bottom")
        plt.text(xlim[1] * 0.95, ylim[0] + (ylim[1] - ylim[0]) * 0.05, "IV. Básicos", color="#14532d", fontsize=11, weight="bold", ha="right", va="bottom")

        plt.xlabel("Centralidad de Callon (Enlaces Externos Transversales)", fontsize=11)
        plt.ylabel("Densidad de Callon (Cohesión Interna del Tema)", fontsize=11)
        plt.title("Diagrama Estratégico de Callon (Mapa Temático Bibliometrix)", fontsize=13, weight="bold")
        plt.grid(True, linestyle=":", alpha=0.6)
        plt.legend(loc="upper left")
        plt.tight_layout()
        plt.savefig(args.plot_output, dpi=200)
        plt.close()
        result["plot_path"] = args.plot_output

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Callon Map calculado con éxito: {len(cluster_metrics)} clusters identificados. Output: {args.output}")


def cmd_generate_script(args):
    """Genera un script de R listo para usar."""
    script_content = generate_r_recipe(
        input_path=args.input,
        output_path=args.output,
        analysis=args.analysis,
        field=args.field
    )
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(script_content)
    print(f"Script de R generado exitosamente en: {args.output}")


def cmd_run(args):
    """Invoca Rscript si está disponible o emite el script para ejecución."""
    runner_r = Path(__file__).resolve().parent / "bibliometrix_runner.R"
    if not runner_r.exists():
        sys.stderr.write(f"Error: No se encontró el runner de R en: {runner_r}\n")
        sys.exit(1)

    if not check_rscript_available():
        print("Aviso: 'Rscript' no se encuentra disponible en el PATH del sistema.", file=sys.stderr)
        print("Generando script reproducible de R para ejecución manual o en servidor...", file=sys.stderr)
        recipe_out = Path(args.output).with_suffix(".R")
        script_code = generate_r_recipe(args.input, str(recipe_out), args.command, field=args.field)
        recipe_out.write_text(script_code, encoding="utf-8")
        print(f"Script R guardado en: {recipe_out}")
        sys.exit(0)

    # Si Rscript está disponible, ejecutar
    cmd = [
        "Rscript", str(runner_r),
        "--command", args.command,
        "--input", args.input,
        "--output", args.output,
        "--field", args.field
    ]
    if args.plot_output:
        cmd.extend(["--plot-output", args.plot_output])

    print(f"Ejecutando: {' '.join(cmd)}")
    subprocess.check_call(cmd)


def main():
    parser = argparse.ArgumentParser(description="CLI Helper: Bibliometrix Orchestrator & Callon Map")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # Subcomando: callon-map (cálculo nativo y autónomo)
    p_map = subparsers.add_parser("callon-map", help="Calcula el Diagrama Estratégico de Callon (Centralidad vs Densidad)")
    p_map.add_argument("--input", required=True, help="Ruta al archivo corpus (.parquet, .csv o .json)")
    p_map.add_argument("--output", required=True, help="Ruta para el JSON de resultados")
    p_map.add_argument("--plot-output", help="Ruta opcional para guardar el gráfico en PNG")
    p_map.add_argument("--field", default="DE", help="Campo de términos (DE: author keywords, ID: keywords plus)")
    p_map.add_argument("--top-terms", type=int, default=50, help="Número de términos más frecuentes a clusterizar")
    p_map.add_argument("--min-freq", type=int, default=2, help="Frecuencia mínima de coocurrencia")
    p_map.set_defaults(func=cmd_callon_map)

    # Subcomando: generate-script
    p_gen = subparsers.add_parser("generate-script", help="Genera un script de R listo para ejecutar")
    p_gen.add_argument("--input", required=True, help="Ruta al archivo de datos de entrada")
    p_gen.add_argument("--output", required=True, help="Ruta del script .R de salida")
    p_gen.add_argument("--analysis", default="thematic", choices=["summary", "co-citation", "collaboration", "thematic", "evolution", "biblioshiny"])
    p_gen.add_argument("--field", default="DE", help="Campo de términos (DE, ID)")
    p_gen.set_defaults(func=cmd_generate_script)

    # Subcomando: run
    p_run = subparsers.add_parser("run", help="Ejecuta bibliometrix_runner.R vía Rscript")
    p_run.add_argument("--input", required=True, help="Ruta al archivo de datos de entrada")
    p_run.add_argument("--command", default="summary", choices=["summary", "network", "thematic"])
    p_run.add_argument("--output", required=True, help="Ruta para el JSON de resultados")
    p_run.add_argument("--plot-output", help="Ruta opcional para el gráfico PNG")
    p_run.add_argument("--field", default="DE", help="Campo de términos")
    p_run.set_defaults(func=cmd_run)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
