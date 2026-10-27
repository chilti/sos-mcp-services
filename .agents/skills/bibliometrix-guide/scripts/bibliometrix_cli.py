#!/usr/bin/env python3
"""
CLI Helper: Bibliometrix Python Orchestrator & Bridge
Orquesta el análisis de mapeo científico con R bibliometrix o genera
recetas reproducibles, resúmenes cienciométricos y diagramas temáticos de Callon (1991).

Uso:
  python scripts/bibliometrix_cli.py summary --input savedrecs.txt --output summary.json
  python scripts/bibliometrix_cli.py callon-map --input savedrecs.txt --output callon.json --plot-output callon.png
  python scripts/bibliometrix_cli.py convert --input savedrecs.txt --output corpus.csv
  python scripts/bibliometrix_cli.py generate-script --input savedrecs.txt --output run_analysis.R --analysis thematic
"""

import sys
import os
import json
import csv
import argparse
import subprocess
import shutil
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Any, Optional

import numpy as np


def find_rscript_path() -> Optional[str]:
    """Busca el ejecutable Rscript en el PATH o en ubicaciones estándar de Windows/Linux."""
    which_path = shutil.which("Rscript")
    if which_path:
        return which_path

    if sys.platform == "win32":
        candidates = sorted(Path("C:/Program Files/R").glob("R-*/bin/Rscript.exe"), reverse=True)
        if candidates and candidates[0].exists():
            return str(candidates[0])
    return None


def check_rscript_available() -> bool:
    """Verifica si Rscript está disponible en el sistema."""
    return find_rscript_path() is not None


def parse_wos_plaintext(filepath: str) -> List[Dict[str, Any]]:
    """Parsea archivos de texto plano etiquetados de Web of Science (savedrecs.txt)."""
    records = []
    current_rec = {}
    current_tag = None

    with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
        for line in f:
            line_str = line.rstrip("\r\n")
            if not line_str:
                continue
            if line_str == "ER" or line_str.startswith("ER "):
                if current_rec:
                    rec_clean = {}
                    for tag, val in current_rec.items():
                        if isinstance(val, list):
                            if tag in ("AU", "AF", "CR", "C1"):
                                rec_clean[tag] = "; ".join(val)
                            else:
                                rec_clean[tag] = " ".join(val)
                        else:
                            rec_clean[tag] = val

                    # Campos canónicos y alias
                    rec_clean["title"] = rec_clean.get("TI", "")
                    rec_clean["authors"] = rec_clean.get("AU", "")
                    rec_clean["author_keywords"] = rec_clean.get("DE", "")
                    rec_clean["keywords"] = rec_clean.get("DE", "") or rec_clean.get("ID", "")
                    rec_clean["source_title"] = rec_clean.get("SO", "")
                    rec_clean["year"] = rec_clean.get("PY", "")
                    rec_clean["references"] = rec_clean.get("CR", "")
                    rec_clean["doi"] = rec_clean.get("DI", "")
                    rec_clean["abstract"] = rec_clean.get("AB", "")
                    rec_clean["times_cited"] = rec_clean.get("TC", "0")
                    records.append(rec_clean)
                    current_rec = {}
                current_tag = None
                continue

            if line_str.startswith("   ") and current_tag:
                val = line_str.strip()
                if current_tag in current_rec:
                    if isinstance(current_rec[current_tag], list):
                        current_rec[current_tag].append(val)
                    else:
                        current_rec[current_tag] = [current_rec[current_tag], val]
            elif len(line_str) >= 2 and line_str[:2].isupper() and (len(line_str) == 2 or line_str[2] == " "):
                tag = line_str[:2]
                val = line_str[3:].strip()
                current_tag = tag
                current_rec[tag] = [val] if tag in ("AU", "AF", "CR", "C1") else val

    return records


def load_corpus_records(filepath: str) -> List[Dict[str, Any]]:
    """Carga registros desde Parquet, CSV, JSON o Web of Science Plain Text (.txt)."""
    lower = filepath.lower()
    if lower.endswith(".parquet"):
        import pandas as pd
        df = pd.read_parquet(filepath)
        return df.to_dict(orient="records")
    elif lower.endswith(".csv"):
        with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
            return list(csv.DictReader(f))
    elif lower.endswith(".json"):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("records", data) if isinstance(data, dict) else data
    elif lower.endswith(".txt"):
        # Detectar si es WoS plain text
        return parse_wos_plaintext(filepath)

    sys.stderr.write(f"Error: Formato no soportado para el archivo: {filepath}\n")
    sys.exit(1)


def generate_r_recipe(input_path: str, output_path: str, analysis: str, field: str = "DE") -> str:
    """Genera un script de R listo para ejecutar en RStudio o terminal."""
    clean_input = input_path.replace("\\", "/")

    # Detectar fuente y formato
    if clean_input.lower().endswith(".txt"):
        formato = "plaintext"
        fuente = "wos"
    elif clean_input.lower().endswith(".csv"):
        formato = "csv"
        fuente = "scopus" if "scopus" in clean_input.lower() else "wos"
    else:
        formato = "csv"
        fuente = "scopus"

    script_template = f"""# ==============================================================================
# Script Reproducible de Bibliometrix
# Generado automáticamente por bibliometrix_cli.py (SOS MCP Services - UNAM)
# ==============================================================================

if (!require("bibliometrix")) install.packages("bibliometrix")
library(bibliometrix)

# 1. Carga y conversión de datos
archivo_datos <- "{clean_input}"
cat("Cargando dataset:", archivo_datos, "\\n")

M <- convert2df(file = archivo_datos, dbsource = "{fuente}", format = "{formato}")
cat(sprintf("Dimensiones del corpus: %d documentos y %d variables.\\n", nrow(M), ncol(M)))

# 2. Análisis seleccionado: {analysis}
"""

    if analysis == "summary":
        script_template += """
results <- biblioAnalysis(M, sep = ";")
S <- summary(results, k = 10, pause = FALSE)
plot(x = results, k = 10, pause = FALSE)
cat("Análisis descriptivo finalizado con éxito.\\n")
"""
    elif analysis == "co-citation":
        script_template += """
NetMatrix <- biblioNetwork(M, analysis = "co-citation", network = "references", sep = ";")
net <- networkPlot(NetMatrix, n = 40, Title = "Red de Co-citación de Referencias",
                   type = "fruchterman", size = TRUE, labelsize = 0.8)
"""
    elif analysis == "collaboration":
        script_template += """
NetMatrix <- biblioNetwork(M, analysis = "collaboration", network = "authors", sep = ";")
net <- networkPlot(NetMatrix, n = 50, Title = "Red de Colaboración Científica entre Autores",
                   type = "kamada", size = TRUE, labelsize = 0.8)
"""
    elif analysis == "thematic":
        script_template += f"""
Map <- thematicMap(M, field = "{field}", n = 250, minfreq = 3,
                  stemming = FALSE, size = 0.5, n.labels = 3, repel = TRUE)
plot(Map$map)
cat("Diagrama Estratégico de Callon renderizado con éxito.\\n")
"""
    elif analysis == "evolution":
        script_template += f"""
nexus <- thematicEvolution(M, field = "{field}", n = 100, minFreq = 3)
plotThematicEvolution(nexus$Nodes, nexus$Edges)
"""
    elif analysis == "biblioshiny":
        script_template += """
# Lanzar interfaz web interactiva Biblioshiny en el navegador
biblioshiny()
"""

    return script_template


def cmd_summary(args):
    """Calcula un resumen descriptivo completo del corpus bibliográfico."""
    records = load_corpus_records(args.input)
    if not records:
        sys.stderr.write("Error: El archivo no contiene registros válidos.\n")
        sys.exit(1)

    years = []
    sources = Counter()
    authors_counter = Counter()
    keywords_counter = Counter()
    doc_author_counts = []
    total_citations = 0

    for r in records:
        yr = r.get("year") or r.get("PY")
        if yr:
            try:
                y_int = int(str(yr)[:4])
                if 1900 <= y_int <= 2030:
                    years.append(y_int)
            except (ValueError, TypeError):
                pass

        src = r.get("source_title") or r.get("SO") or ""
        if src:
            sources[src.strip().upper()] += 1

        raw_auth = r.get("authors") or r.get("AU") or ""
        auth_list = [a.strip() for a in str(raw_auth).split(";") if a.strip()]
        doc_author_counts.append(len(auth_list))
        for a in auth_list:
            authors_counter[a] += 1

        raw_kw = r.get("keywords") or r.get("DE") or r.get("ID") or ""
        kw_list = [k.strip().lower() for k in str(raw_kw).replace(",", ";").split(";") if k.strip()]
        for kw in kw_list:
            keywords_counter[kw] += 1

        try:
            tc = int(r.get("times_cited") or r.get("TC") or 0)
            total_citations += tc
        except (ValueError, TypeError):
            pass

    n_docs = len(records)
    total_authors = len(authors_counter)
    single_author_docs = sum(1 for c in doc_author_counts if c == 1)
    multi_author_docs = n_docs - single_author_docs
    avg_authors_per_doc = round(sum(doc_author_counts) / n_docs, 2) if n_docs > 0 else 0.0
    collab_index = round(total_authors / multi_author_docs, 2) if multi_author_docs > 0 else 0.0

    min_yr = min(years) if years else None
    max_yr = max(years) if years else None
    cagr = 0.0
    if min_yr and max_yr and max_yr > min_yr:
        cnt_min = years.count(min_yr)
        cnt_max = years.count(max_yr)
        span = max_yr - min_yr
        if cnt_min > 0 and cnt_max > 0 and span > 0:
            cagr = round(((cnt_max / cnt_min) ** (1.0 / span) - 1.0) * 100.0, 2)

    summary_data = {
        "analysis": "Bibliometric Descriptive Summary",
        "total_documents": n_docs,
        "timespan": f"{min_yr} - {max_yr}" if min_yr else "N/A",
        "annual_growth_rate_percent": cagr,
        "total_authors": total_authors,
        "single_authored_documents": single_author_docs,
        "multi_authored_documents": multi_author_docs,
        "average_authors_per_doc": avg_authors_per_doc,
        "collaboration_index": collab_index,
        "total_citations_accumulated": total_citations,
        "average_citations_per_doc": round(total_citations / n_docs, 2) if n_docs > 0 else 0.0,
        "top_sources": [{"source": s, "articles": c} for s, c in sources.most_common(10)],
        "top_authors": [{"author": a, "articles": c} for a, c in authors_counter.most_common(10)],
        "top_keywords": [{"keyword": k, "frequency": c} for k, c in keywords_counter.most_common(15)]
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)

    print("\n" + "="*70)
    print("RESUMEN BIBLIOMÉTRICO (BIBLIOMETRIX DESCRIPTIVE ANALYSIS)")
    print("="*70)
    print(f"Total de Documentos Analizados: {n_docs}")
    print(f"Periodo Cronológico:           {summary_data['timespan']}")
    print(f"Tasa de Crecimiento Anual:     {cagr}%")
    print(f"Total de Autores:              {total_authors}")
    print(f"Documentos con Autor Único:    {single_author_docs}")
    print(f"Promedio de Autores por Doc:   {avg_authors_per_doc}")
    print(f"Índice de Colaboración:        {collab_index}")
    print(f"Citas Totales Acumuladas:      {total_citations} (Promedio: {summary_data['average_citations_per_doc']} citas/doc)")
    print("\nTop 5 Revistas Más Productivas:")
    for idx, s in enumerate(summary_data["top_sources"][:5], 1):
        print(f"  {idx}. {s['source']} ({s['articles']} artículos)")
    print("\nTop 5 Autores Más Prolíficos:")
    for idx, a in enumerate(summary_data["top_authors"][:5], 1):
        print(f"  {idx}. {a['author']} ({a['articles']} artículos)")
    print("\nTop 5 Palabras Clave Principales:")
    for idx, k in enumerate(summary_data["top_keywords"][:5], 1):
        print(f"  {idx}. {k['keyword']} (frecuencia: {k['frequency']})")
    print("="*70)
    print(f"Reporte JSON guardado en: {args.output}\n")


def cmd_callon_map(args):
    """Calcula nativamente el Diagrama Estratégico de Callon (Centralidad vs Densidad)."""
    records = load_corpus_records(args.input)
    if not records:
        sys.stderr.write("Error: El archivo de entrada no contiene registros legibles.\n")
        sys.exit(1)

    co_occurrences = defaultdict(int)
    term_counts = Counter()
    doc_keywords = []

    for r in records:
        raw_kw = (
            r.get("keywords") or r.get("Keywords") or r.get("DE") or r.get("ID") or
            r.get("author_keywords") or ""
        )
        if isinstance(raw_kw, list):
            kws = [str(k).strip().lower() for k in raw_kw if str(k).strip()]
        else:
            kws = [k.strip().lower() for k in str(raw_kw).replace(",", ";").split(";") if k.strip()]

        kws = [k for k in kws if len(k) > 2]
        if kws:
            doc_keywords.append(kws)
            for k in kws:
                term_counts[k] += 1
            for i in range(len(kws)):
                for j in range(i + 1, len(kws)):
                    t1, t2 = sorted([kws[i], kws[j]])
                    co_occurrences[(t1, t2)] += 1

    top_terms = [t for t, c in term_counts.most_common(args.top_terms)]
    if len(top_terms) < 4:
        sys.stderr.write("Error: Vocabulario de palabras clave insuficiente para clusterizar.\n")
        sys.exit(1)

    top_set = set(top_terms)
    adj = defaultdict(dict)
    for (t1, t2), weight in co_occurrences.items():
        if t1 in top_set and t2 in top_set and weight >= args.min_freq:
            adj[t1][t2] = weight
            adj[t2][t1] = weight

    # Clustering de comunidades
    assigned_cluster = {}
    cluster_id = 1
    for term in top_terms:
        if term not in assigned_cluster:
            neighbors = sorted(adj[term].items(), key=lambda x: -x[1])
            cluster_terms = [term] + [nb for nb, w in neighbors[:5] if nb not in assigned_cluster]
            for ct in cluster_terms:
                assigned_cluster[ct] = cluster_id
            cluster_id += 1

    clusters_map = defaultdict(list)
    for t, cid in assigned_cluster.items():
        clusters_map[cid].append(t)

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
        sys.stderr.write("Error: No fue posible calcular clusters con los umbrales indicados.\n")
        sys.exit(1)

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

    if args.plot_output:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        os.makedirs(os.path.dirname(os.path.abspath(args.plot_output)), exist_ok=True)
        plt.figure(figsize=(9, 7))

        cents = [c["callon_centrality"] for c in cluster_metrics]
        dens = [c["callon_density"] for c in cluster_metrics]
        sizes = [c["size"] * 80 for c in cluster_metrics]

        plt.scatter(cents, dens, s=sizes, color="#2563eb", alpha=0.6, edgecolors="#1d4ed8", linewidth=1.5, zorder=3)

        for c in cluster_metrics:
            plt.annotate(c["label"], (c["callon_centrality"], c["callon_density"]),
                         fontsize=10, weight="bold", ha="center", va="bottom",
                         xytext=(0, 7), textcoords="offset points")

        plt.axvline(med_cent, color="#dc2626", linestyle="--", alpha=0.7, label=f"Mediana Centralidad ({med_cent:.1f})")
        plt.axhline(med_dens, color="#16a34a", linestyle="--", alpha=0.7, label=f"Mediana Densidad ({med_dens:.1f})")

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


def cmd_convert(args):
    """Convierte el archivo a CSV, Parquet o JSON canónico."""
    records = load_corpus_records(args.input)
    if not records:
        sys.stderr.write("Error: El archivo no contiene registros para convertir.\n")
        sys.exit(1)

    out_lower = args.output.lower()
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)

    if out_lower.endswith(".csv"):
        all_keys = set()
        for r in records:
            all_keys.update(r.keys())
        fieldnames = sorted(all_keys)
        with open(args.output, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(records)
    elif out_lower.endswith(".parquet"):
        import pandas as pd
        df = pd.DataFrame(records)
        df.to_parquet(args.output, index=False)
    elif out_lower.endswith(".json"):
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

    print(f"Conversión finalizada: {len(records)} documentos guardados en: {args.output}")


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

    rscript_bin = find_rscript_path()
    if not rscript_bin:
        print("Aviso: 'Rscript' no se encuentra instalado o disponible en el sistema.", file=sys.stderr)
        recipe_out = Path(args.output).with_suffix(".R")
        script_code = generate_r_recipe(args.input, str(recipe_out), args.command, field=args.field)
        recipe_out.write_text(script_code, encoding="utf-8")
        print(f"Script R generado para ejecución en RStudio: {recipe_out}")
        sys.exit(0)

    # Auto-detección de formato y dbsource
    input_lower = args.input.lower()
    if input_lower.endswith(".txt"):
        dbsource = "wos"
        fmt = "plaintext"
    elif "scopus" in input_lower:
        dbsource = "scopus"
        fmt = "csv"
    else:
        dbsource = "wos"
        fmt = "csv"

    cmd = [
        rscript_bin, str(runner_r),
        "--command", args.command,
        "--input", args.input,
        "--output", args.output,
        "--dbsource", dbsource,
        "--format", fmt,
        "--field", args.field
    ]
    if args.plot_output:
        cmd.extend(["--plot-output", args.plot_output])

    print(f"Ejecutando R bibliometrix con: {rscript_bin}")
    subprocess.check_call(cmd)


def main():
    parser = argparse.ArgumentParser(description="CLI Helper: Bibliometrix Orchestrator & Callon Map")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # Subcomando: summary
    p_sum = subparsers.add_parser("summary", help="Calcula el resumen bibliométrico descriptivo completo")
    p_sum.add_argument("--input", required=True, help="Ruta al archivo corpus (.txt, .csv, .parquet, .json)")
    p_sum.add_argument("--output", required=True, help="Ruta para el JSON de resultados")
    p_sum.set_defaults(func=cmd_summary)

    # Subcomando: callon-map
    p_map = subparsers.add_parser("callon-map", help="Calcula el Diagrama Estratégico de Callon (Centralidad vs Densidad)")
    p_map.add_argument("--input", required=True, help="Ruta al archivo corpus (.txt, .parquet, .csv o .json)")
    p_map.add_argument("--output", required=True, help="Ruta para el JSON de resultados")
    p_map.add_argument("--plot-output", help="Ruta opcional para guardar el gráfico en PNG")
    p_map.add_argument("--field", default="DE", help="Campo de términos (DE: author keywords, ID: keywords plus)")
    p_map.add_argument("--top-terms", type=int, default=50, help="Número de términos más frecuentes a clusterizar")
    p_map.add_argument("--min-freq", type=int, default=2, help="Frecuencia mínima de coocurrencia")
    p_map.set_defaults(func=cmd_callon_map)

    # Subcomando: convert
    p_con = subparsers.add_parser("convert", help="Convierte WoS plaintext a CSV, Parquet o JSON estructurado")
    p_con.add_argument("--input", required=True, help="Ruta al archivo de entrada (.txt)")
    p_con.add_argument("--output", required=True, help="Ruta del archivo de salida (.csv, .parquet o .json)")
    p_con.set_defaults(func=cmd_convert)

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
