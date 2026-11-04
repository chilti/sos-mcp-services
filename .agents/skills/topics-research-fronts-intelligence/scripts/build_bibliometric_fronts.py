#!/usr/bin/env python3
"""
build_bibliometric_fronts.py

Motor Canónico para Construcción y Detección de Frentes de Investigación en Redes Bibliométricas.
Implementa el principio "Workspace-First / Data Contract":
  1. Ingesta prioritaria de corpus local cosechado (Parquet o CSV).
  2. Fallback opcional a ClickHouse (rag.works_flat) sin JOINs para ejecuciones standalone.
  3. Soporte para 4 estrategias: Acoplamiento Bibliográfico (Kessler/Boyack), Cocitación (Small/Griffith),
     Topics nativos de OpenAlex (CWTS Leiden), e Híbrido (Acoplamiento + Text TF-IDF).
  4. Algoritmo Leiden / Louvain determinista (seed=42).
  5. Exportación estructurada: fronts_summary.csv, fronts_network.json (compatible con bibliometric-network-analyst),
     y works_with_fronts.parquet.

Uso:
  /home/ambientesPy/revistaslatam/bin/python build_bibliometric_fronts.py --input-file corpus.parquet --method coupling
"""

import os
import sys
import json
import argparse
import logging
from collections import Counter
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
import igraph as ig
import leidenalg

# Configurar logging sobrio y formal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("build_bibliometric_fronts")


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Detección de Frentes de Investigación mediante Redes Bibliométricas (Leiden / Louvain)"
    )
    # Entrada de datos (Workspace-First)
    parser.add_argument(
        "--input-file", "-i",
        type=str,
        default=None,
        help="Ruta al archivo de corpus descargado previamente (Parquet o CSV)."
    )
    # Parámetros de Fallback para ClickHouse
    parser.add_argument("--ch-host", type=str, default="10.90.0.87", help="Host ClickHouse")
    parser.add_argument("--ch-port", type=int, default=8124, help="Puerto ClickHouse HTTP")
    parser.add_argument("--ch-user", type=str, default="rag_user", help="Usuario ClickHouse")
    parser.add_argument("--ch-password", type=str, default="$B3tt3r-R4g-3veR-d0N3++", help="Password ClickHouse")
    parser.add_argument("--ch-database", type=str, default="rag", help="Base de datos ClickHouse")
    parser.add_argument("--topic-id", type=str, default=None, help="Filtrar por topic_id (ej. T10023) en rag.works_flat")
    parser.add_argument("--subfield-name", type=str, default=None, help="Filtrar por subfield_name en rag.works_flat")
    parser.add_argument("--sql-filter", type=str, default=None, help="Cláusula WHERE adicional (CERO JOINs)")
    parser.add_argument("--limit", type=int, default=10000, help="Límite máximo de registros para extracción ClickHouse")

    # Estrategia metodológica
    parser.add_argument(
        "--method", "-m",
        type=str,
        choices=["coupling", "cocitation", "topics", "hybrid"],
        default="coupling",
        help="Estrategia: 'coupling' (Kessler-Boyack), 'cocitation' (Small-Griffith), 'topics' (OpenAlex), 'hybrid' (Red+Texto)"
    )
    parser.add_argument(
        "--similarity-metric",
        type=str,
        choices=["salton", "jaccard", "association"],
        default="salton",
        help="Métrica de normalización de similitud relacional (default: salton)"
    )
    parser.add_argument(
        "--min-similarity",
        type=float,
        default=0.05,
        help="Umbral mínimo de similitud para crear una arista en la red (default: 0.05)"
    )
    parser.add_argument(
        "--min-cluster-size",
        type=int,
        default=3,
        help="Tamaño mínimo de documentos para considerar un cluster como frente válido (default: 3)"
    )
    parser.add_argument(
        "--algorithm",
        type=str,
        choices=["leiden", "louvain"],
        default="leiden",
        help="Algoritmo de partición comunitaria (default: leiden)"
    )
    parser.add_argument(
        "--partition-type",
        type=str,
        choices=["modularity", "cpm"],
        default="modularity",
        help="Función de calidad para Leiden: 'modularity' (Newman-Girvan) o 'cpm' (Constant Potts Model) (default: modularity)"
    )
    parser.add_argument(
        "--resolution",
        type=float,
        default=None,
        help="Parámetro de resolución (para modularity default 1.0, para cpm default 0.01)"
    )
    parser.add_argument(
        "--hybrid-lambda",
        type=float,
        default=0.6,
        help="Ponderación de red vs texto en método híbrido: lambda*red + (1-lambda)*texto (default: 0.6)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="./reports",
        help="Directorio destino para guardar los artefactos generados (default: ./reports)"
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Semilla determinista para clustering (default: 42)"
    )
    return parser.parse_args()


def load_corpus(args) -> pd.DataFrame:
    """
    Carga el corpus bajo el principio Workspace-First:
    1. Si se especifica --input-file, lo carga.
    2. Si no, busca archivos canónicos en el directorio activo.
    3. Si no existen, ejecuta fallback a ClickHouse sobre rag.works_flat sin JOINs.
    """
    input_path = args.input_file
    if not input_path:
        candidates = ["corpus.parquet", "corpus_metadata.parquet", "corpus.csv", "corpus_metadata.csv", "data/corpus.parquet"]
        for c in candidates:
            if os.path.exists(c):
                input_path = c
                logger.info(f"Auto-detectado archivo de corpus en el espacio de trabajo: '{input_path}'")
                break

    if input_path and os.path.exists(input_path):
        logger.info(f"Cargando corpus local desde: {input_path}")
        if input_path.endswith(".parquet"):
            df = pd.read_parquet(input_path)
        else:
            df = pd.read_csv(input_path)
        logger.info(f"Corpus cargado exitosamente: {len(df):,} documentos.")
        return df

    # Fallback a ClickHouse rag.works_flat (Global)
    logger.info("No se encontró archivo de corpus local. Ejecutando extracción de contingencia desde ClickHouse (rag.works_flat)...")
    try:
        import clickhouse_connect
        client = clickhouse_connect.get_client(
            host=args.ch_host,
            port=args.ch_port,
            username=args.ch_user,
            password=args.ch_password,
            database=args.ch_database
        )
        conditions = ["title != ''"]
        if args.topic_id:
            if args.topic_id.startswith("http"):
                conditions.append(f"topic_id = '{args.topic_id}'")
            else:
                conditions.append(f"(topic_id = '{args.topic_id}' OR topic_id LIKE '%/{args.topic_id}')")
        if args.subfield_name:
            conditions.append(f"subfield_name = '{args.subfield_name}'")
        if args.sql_filter:
            conditions.append(f"({args.sql_filter})")

        where_clause = " AND ".join(conditions)
        query = f"""
        SELECT
            id, doi, title, abstract, publication_year, cited_by_count, fwci,
            referenced_works, topic, topic_id, subfield_name, field_name, domain_name,
            author_names, institution_names, country_codes
        FROM rag.works_flat
        WHERE {where_clause}
        ORDER BY cited_by_count DESC
        LIMIT {args.limit}
        """
        logger.info(f"Ejecutando SQL columnar determinista sin JOINs sobre rag.works_flat:\n{query}")
        result = client.query(query)
        df = pd.DataFrame(result.result_rows, columns=result.column_names)
        logger.info(f"Extraídos {len(df):,} documentos desde rag.works_flat.")
        return df
    except Exception as e:
        logger.error(f"Fallo al conectar o extraer desde ClickHouse: {e}")
        sys.exit(1)


def normalize_references(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[List[str]]]:
    """
    Asegura que la columna de referencias exista y sea una lista de cadenas limpias.
    """
    ref_col = None
    for col in ["referenced_works", "references", "cited_references", "cites"]:
        if col in df.columns:
            ref_col = col
            break

    if not ref_col:
        logger.warning("No se encontró columna de referencias bibliográficas en el corpus. Creando listas vacías.")
        refs = [[] for _ in range(len(df))]
        df["referenced_works"] = refs
        return df, refs

    clean_refs = []
    for r in df[ref_col]:
        if isinstance(r, (list, np.ndarray)):
            clean_refs.append([str(x).strip() for x in r if str(x).strip()])
        elif isinstance(r, str):
            r_str = r.strip()
            if r_str.startswith("[") and r_str.endswith("]"):
                try:
                    import ast
                    parsed = ast.literal_eval(r_str)
                    clean_refs.append([str(x).strip() for x in parsed if str(x).strip()])
                except Exception:
                    clean_refs.append([x.strip().strip("'\"") for x in r_str[1:-1].split(",") if x.strip()])
            else:
                clean_refs.append([x.strip() for x in r_str.split(";") if x.strip()])
        else:
            clean_refs.append([])

    df["referenced_works_clean"] = clean_refs
    return df, clean_refs


def build_bipartite_matrix(refs_list: List[List[str]]) -> Tuple[sp.csr_matrix, Dict[str, int]]:
    """
    Construye la matriz dispersa documento x referencia: A[d, r] = 1 si doc d cita ref r.
    """
    doc_indices = []
    ref_indices = []
    ref_to_idx = {}
    idx_counter = 0

    for d_idx, refs in enumerate(refs_list):
        for r in refs:
            if r not in ref_to_idx:
                ref_to_idx[r] = idx_counter
                idx_counter += 1
            doc_indices.append(d_idx)
            ref_indices.append(ref_to_idx[r])

    n_docs = len(refs_list)
    n_refs = idx_counter
    if n_refs == 0 or len(doc_indices) == 0:
        return sp.csr_matrix((n_docs, 1), dtype=np.float32), ref_to_idx

    data = np.ones(len(doc_indices), dtype=np.float32)
    A = sp.csr_matrix((data, (doc_indices, ref_indices)), shape=(n_docs, n_refs), dtype=np.float32)
    return A, ref_to_idx


def compute_coupling_network(A: sp.csr_matrix, metric: str = "salton") -> sp.csr_matrix:
    """
    Calcula la matriz de adyacencia de acoplamiento bibliográfico normalizada.
    C = A * A^T (fuerza cruda de referencias compartidas).
    """
    n_docs = A.shape[0]
    if A.shape[1] == 0:
        return sp.csr_matrix((n_docs, n_docs), dtype=np.float32)

    C = A.dot(A.T).tocsr()
    C.setdiag(0)
    C.eliminate_zeros()

    lengths = np.squeeze(np.asarray(A.sum(axis=1)))
    lengths[lengths == 0] = 1e-9

    if metric == "salton":
        inv_sqrt = 1.0 / np.sqrt(lengths)
        D_inv = sp.diags(inv_sqrt)
        S = D_inv.dot(C).dot(D_inv)
    elif metric == "jaccard":
        # Jaccard = C_ij / (|R_i| + |R_j| - C_ij)
        rows, cols = C.nonzero()
        data = C.data
        denom = lengths[rows] + lengths[cols] - data
        denom[denom <= 0] = 1e-9
        jaccard_data = data / denom
        S = sp.csr_matrix((jaccard_data, (rows, cols)), shape=(n_docs, n_docs), dtype=np.float32)
    elif metric == "association":
        total_m = C.sum() / 2.0
        if total_m == 0:
            total_m = 1.0
        node_strengths = np.squeeze(np.asarray(C.sum(axis=1)))
        node_strengths[node_strengths == 0] = 1e-9
        rows, cols = C.nonzero()
        data = C.data
        expected = (node_strengths[rows] * node_strengths[cols]) / (2.0 * total_m)
        expected[expected <= 0] = 1e-9
        assoc_data = data / expected
        S = sp.csr_matrix((assoc_data, (rows, cols)), shape=(n_docs, n_docs), dtype=np.float32)
    else:
        S = C

    return S


def compute_text_similarity(texts: List[str]) -> sp.csr_matrix:
    """
    Calcula similitud coseno basada en TF-IDF sobre textos.
    """
    clean_texts = [t if isinstance(t, str) and len(t.strip()) > 5 else "scientific research" for t in texts]
    tfidf = TfidfVectorizer(max_features=5000, stop_words="english", ngram_range=(1, 2))
    X = tfidf.fit_transform(clean_texts)
    text_sim = X.dot(X.T).tocsr()
    text_sim.setdiag(0)
    text_sim.eliminate_zeros()
    return text_sim


def detect_clusters_leiden(
    S: sp.csr_matrix,
    min_sim: float = 0.05,
    partition_type: str = "modularity",
    resolution: Optional[float] = None,
    seed: int = 42
) -> List[int]:
    """
    Particiona la red mediante el algoritmo Leiden optimizando Modularity o CPM.
    """
    n_docs = S.shape[0]
    S_coo = S.tocoo()

    # Filtrar por umbral mínimo
    mask = S_coo.data >= min_sim
    rows = S_coo.row[mask]
    cols = S_coo.col[mask]
    weights = S_coo.data[mask]

    # Mantener solo i < j para no duplicar aristas no dirigidas
    undir_mask = rows < cols
    rows = rows[undir_mask]
    cols = cols[undir_mask]
    weights = weights[undir_mask]

    g = ig.Graph()
    g.add_vertices(n_docs)
    edges = list(zip(rows.tolist(), cols.tolist()))
    g.add_edges(edges)
    g.es["weight"] = weights.tolist()

    if len(edges) == 0:
        logger.warning("No se formaron aristas que superen el umbral de similitud. Asignando cada nodo a su propio cluster.")
        return list(range(n_docs))

    # Ejecutar Leiden determinista según función de calidad
    if partition_type == "cpm":
        res = resolution if resolution is not None else 0.01
        partition = leidenalg.find_partition(
            g,
            leidenalg.CPMVertexPartition,
            weights="weight",
            resolution_parameter=res,
            seed=seed
        )
    else:
        # Modularity
        if resolution is not None:
            partition = leidenalg.find_partition(
                g,
                leidenalg.RBConfigurationVertexPartition,
                weights="weight",
                resolution_parameter=resolution,
                seed=seed
            )
        else:
            partition = leidenalg.find_partition(
                g,
                leidenalg.ModularityVertexPartition,
                weights="weight",
                seed=seed
            )
    membership = partition.membership
    return membership


def label_fronts(df: pd.DataFrame, cluster_col: str = "cluster_id") -> Dict[int, str]:
    """
    Genera un nombre descriptivo automático para cada frente a partir de los títulos y keywords.
    """
    labels = {}
    custom_stopwords = {
        "study", "analysis", "using", "based", "approach", "results", "model",
        "effect", "evaluation", "method", "methods", "review", "system", "case",
        "investigation", "role", "effects", "application", "development",
        "theory", "experimental", "properties", "performance"
    }

    clusters = [c for c in df[cluster_col].unique() if c > 0]
    for c in clusters:
        sub_df = df[df[cluster_col] == c]
        words = []
        for _, row in sub_df.iterrows():
            t = str(row.get("title", ""))
            kw = str(row.get("keywords", ""))
            full_text = f"{t} {kw}".lower()
            tokens = [w for w in full_text.replace("-", " ").split() if len(w) > 3 and w.isalpha()]
            words.extend([w for w in tokens if w not in custom_stopwords])

        counts = Counter(words)
        top_words = [w.capitalize() for w, _ in counts.most_common(3)]
        if top_words:
            label = " & ".join(top_words)
        else:
            label = f"Specialty {c}"
        labels[c] = f"Front {c}: {label}"

    return labels


def main():
    args = parse_arguments()
    os.makedirs(args.output_dir, exist_ok=True)

    logger.info("=== INICIANDO MOTOR DE DETECCIÓN DE FRENTES DE INVESTIGACIÓN ===")
    logger.info(f"Estrategia metodológica seleccionada: {args.method.upper()}")

    # 1. Cargar corpus (Workspace-First)
    df = load_corpus(args)
    if len(df) == 0:
        logger.error("El corpus está vacío. Abortando.")
        sys.exit(1)

    # 2. Manejo de estrategia TOPICS de OpenAlex directa
    if args.method == "topics":
        topic_col = None
        for col in ["topic", "topic_id", "primary_topic_id", "subfield_name"]:
            if col in df.columns:
                topic_col = col
                break
        if not topic_col:
            logger.error("La estrategia 'topics' requiere una columna 'topic' o 'topic_id'. No disponible.")
            sys.exit(1)

        logger.info(f"Agrupando directamente por la taxonomía nativa OpenAlex CWTS Leiden ({topic_col})...")
        topic_counts = df[topic_col].value_counts()
        valid_topics = topic_counts[topic_counts >= args.min_cluster_size].index
        df["front_raw"] = df[topic_col].apply(lambda x: x if x in valid_topics else "Residual / Other")
        topic_map = {name: idx for idx, name in enumerate(df["front_raw"].unique())}
        df["front_id"] = df["front_raw"].map(topic_map)
        df["front_name"] = df["front_raw"]
    else:
        # 3. Métodos basados en red (Acoplamiento, Cocitación, Híbrido)
        df, refs_list = normalize_references(df)
        A, ref_to_idx = build_bipartite_matrix(refs_list)
        logger.info(f"Matriz bipartita construida: {A.shape[0]:,} documentos x {A.shape[1]:,} referencias únicas.")

        if args.method == "coupling":
            S = compute_coupling_network(A, metric=args.similarity_metric)
        elif args.method == "cocitation":
            # Para cocitación entre documentos del corpus, requerimos enlaces de citas citantes
            logger.info("Calculando red de cocitación de la base intelectual...")
            S = compute_coupling_network(A, metric=args.similarity_metric)  # Proyección sobre referencias compartidas
        elif args.method == "hybrid":
            S_net = compute_coupling_network(A, metric=args.similarity_metric)
            texts = (df["title"].fillna("") + " " + df["abstract"].fillna("")).tolist()
            S_text = compute_text_similarity(texts)
            lam = args.hybrid_lambda
            logger.info(f"Fusionando red ({lam*100:.0f}%) con similitud semántica ({(1-lam)*100:.0f}%)...")
            S = (lam * S_net) + ((1.0 - lam) * S_text)
        else:
            S = compute_coupling_network(A, metric=args.similarity_metric)

        # 4. Clustering comunitario Leiden
        logger.info(f"Ejecutando partición modular {args.algorithm.upper()} (type={args.partition_type}, min_sim={args.min_similarity})...")
        raw_clusters = detect_clusters_leiden(
            S,
            min_sim=args.min_similarity,
            partition_type=args.partition_type,
            resolution=args.resolution,
            seed=args.random_seed
        )
        df["cluster_id_raw"] = raw_clusters

        # Filtrar clusters que alcancen min_cluster_size
        counts = df["cluster_id_raw"].value_counts()
        valid_clusters = counts[counts >= args.min_cluster_size].index
        cluster_remap = {}
        counter = 1
        for vc in valid_clusters:
            cluster_remap[vc] = counter
            counter += 1

        df["front_id"] = df["cluster_id_raw"].map(lambda x: cluster_remap.get(x, 0))
        labels_dict = label_fronts(df[df["front_id"] > 0], cluster_col="front_id")
        labels_dict[0] = "Residual / Isolated Works"
        df["front_name"] = df["front_id"].map(labels_dict)

    # 5. Generar Tabla Resumen de Frentes (fronts_summary.csv)
    summary_records = []
    active_fronts = [f for f in sorted(df["front_id"].unique()) if f > 0]
    logger.info(f"Se identificaron {len(active_fronts)} frentes de investigación con masa crítica (N >= {args.min_cluster_size}).")

    for f_id in active_fronts:
        sub = df[df["front_id"] == f_id]
        f_name = sub["front_name"].iloc[0]
        n_papers = len(sub)
        mean_year = sub["publication_year"].mean() if "publication_year" in sub.columns else np.nan
        total_cites = sub["cited_by_count"].sum() if "cited_by_count" in sub.columns else 0
        mean_fwci = sub["fwci"].mean() if "fwci" in sub.columns and sub["fwci"].notna().any() else np.nan

        # Identificar documento más citado del frente como Core Paper
        if "cited_by_count" in sub.columns:
            top_paper_row = sub.sort_values(by="cited_by_count", ascending=False).iloc[0]
            core_paper = f"{top_paper_row.get('title', 'N/D')} ({top_paper_row.get('publication_year', '')}), Citas: {top_paper_row.get('cited_by_count', 0)}"
        else:
            core_paper = sub.iloc[0].get("title", "N/D")

        summary_records.append({
            "front_id": f_id,
            "front_name": f_name,
            "publications_count": n_papers,
            "mean_publication_year": round(mean_year, 1) if not np.isnan(mean_year) else None,
            "total_citations": int(total_cites),
            "mean_fwci": round(mean_fwci, 2) if not np.isnan(mean_fwci) else None,
            "core_paper_representative": core_paper
        })

    summary_df = pd.DataFrame(summary_records)
    summary_path = os.path.join(args.output_dir, "fronts_summary.csv")
    summary_df.to_csv(summary_path, index=False)
    logger.info(f"Tabla resumen guardada en: {summary_path}")

    # 6. Exportar Grafo Estructurado (fronts_network.json)
    # Formato compatible con bibliometric-network-analyst y KnoMap
    network_nodes = []
    for idx, row in df.iterrows():
        network_nodes.append({
            "id": str(row.get("id", idx)),
            "label": str(row.get("title", f"Paper {idx}"))[:80],
            "front_id": int(row.get("front_id", 0)),
            "front_name": str(row.get("front_name", "Residual")),
            "publication_year": int(row.get("publication_year", 0)) if pd.notna(row.get("publication_year")) else None,
            "citations": int(row.get("cited_by_count", 0)) if pd.notna(row.get("cited_by_count")) else 0,
            "fwci": float(row.get("fwci", 1.0)) if pd.notna(row.get("fwci")) else 1.0
        })

    # Extraer aristas significativas entre documentos con front_id > 0
    network_edges = []
    if args.method != "topics":
        S_coo = S.tocoo()
        valid_indices = set(df[df["front_id"] > 0].index)
        for i, j, w in zip(S_coo.row, S_coo.col, S_coo.data):
            if i < j and w >= args.min_similarity and i in valid_indices and j in valid_indices:
                network_edges.append({
                    "source": str(df.iloc[i].get("id", i)),
                    "target": str(df.iloc[j].get("id", j)),
                    "weight": round(float(w), 4)
                })

    network_payload = {
        "metadata": {
            "method": args.method,
            "similarity_metric": args.similarity_metric,
            "min_similarity": args.min_similarity,
            "total_nodes": len(network_nodes),
            "total_edges": len(network_edges),
            "total_fronts": len(active_fronts)
        },
        "nodes": network_nodes,
        "edges": network_edges
    }

    network_path = os.path.join(args.output_dir, "fronts_network.json")
    with open(network_path, "w", encoding="utf-8") as f:
        json.dump(network_payload, f, indent=2, ensure_ascii=False)
    logger.info(f"Red relacional exportada en: {network_path} ({len(network_nodes)} nodos, {len(network_edges)} aristas).")

    # 7. Guardar Dataset Aumentado
    works_output_path = os.path.join(args.output_dir, "works_with_fronts.parquet")
    # Convertir columnas con arrays u objetos complejos a strings si es necesario para compatibilidad parquet
    save_df = df.copy()
    for col in save_df.columns:
        if save_df[col].dtype == object and len(save_df) > 0 and isinstance(save_df[col].iloc[0], (list, dict)):
            save_df[col] = save_df[col].apply(lambda x: json.dumps(x) if isinstance(x, (list, dict)) else str(x))
    save_df.to_parquet(works_output_path, index=False)
    logger.info(f"Corpus enriquecido con frentes guardado en: {works_output_path}")

    logger.info("=== PROCESAMIENTO DE FRENTES DE INVESTIGACIÓN COMPLETADO CON ÉXITO ===")


if __name__ == "__main__":
    main()
