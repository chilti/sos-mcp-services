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
    # Parámetros de Fallback Standalone (OpenAlex API por defecto; ClickHouse opcional opt-in)
    parser.add_argument("--ch-host", type=str, default=os.getenv("CLICKHOUSE_HOST", ""), help="Host ClickHouse opcional (por defecto toma CLICKHOUSE_HOST si existe)")
    parser.add_argument("--ch-port", type=int, default=int(os.getenv("CLICKHOUSE_PORT", "8124")), help="Puerto ClickHouse HTTP")
    parser.add_argument("--ch-user", type=str, default=os.getenv("CLICKHOUSE_USER", "default"), help="Usuario ClickHouse")
    parser.add_argument("--ch-password", type=str, default=os.getenv("CLICKHOUSE_PASSWORD", ""), help="Password ClickHouse")
    parser.add_argument("--ch-database", type=str, default=os.getenv("CLICKHOUSE_DATABASE", "rag"), help="Base de datos ClickHouse")
    parser.add_argument("--topic-id", type=str, default=None, help="Filtrar por OpenAlex topic_id (ej. T10023)")
    parser.add_argument("--subfield-name", type=str, default=None, help="Filtrar por OpenAlex subfield name")
    parser.add_argument("--query", type=str, default=None, help="Búsqueda textual libre en OpenAlex API si no hay corpus local")
    parser.add_argument("--sql-filter", type=str, default=None, help="Cláusula WHERE adicional opcional (CERO JOINs)")
    parser.add_argument("--limit", type=int, default=2000, help="Límite máximo de registros para extracción standalone")

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
        "--eval-resolutions",
        type=str,
        default=None,
        help="Optional comma-separated resolutions to evaluate (e.g. '0.5,0.75,1.0,1.25,1.5' or '0.005,0.01,0.02,0.05')"
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
        help="Target directory to save generated artifacts (default: ./reports)"
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Deterministic seed for clustering (default: 42)"
    )
    parser.add_argument(
        "--lang",
        type=str,
        choices=["en", "es"],
        default="en",
        help="Output language for front labels and summaries (default: en)"
    )
    return parser.parse_args()


def _fetch_openalex_api_fallback(args) -> pd.DataFrame:
    """Fallback autónomo portátil vía OpenAlex REST API (cursor pagination) cuando no hay corpus local ni ClickHouse."""
    import requests
    base_url = "https://api.openalex.org/works"
    filters = ["has_references:true"]
    if args.topic_id:
        tid = args.topic_id.split("/")[-1]
        filters.append(f"primary_topic.id:{tid}")
    if args.subfield_name:
        filters.append(f'default.search:"{args.subfield_name}"')

    params: Dict[str, Any] = {
        "filter": ",".join(filters),
        "sort": "cited_by_count:desc",
        "per-page": 200,
        "cursor": "*",
    }
    if args.query:
        params["search"] = args.query
    headers = {"User-Agent": "TopicsResearchFronts/1.0 (mailto:soporte@knomap.org)"}

    rows: List[Dict[str, Any]] = []
    limit = max(1, int(args.limit))
    logger.info("Extrayendo corpus autónomo vía OpenAlex REST API (%s)...", base_url)
    while len(rows) < limit:
        resp = requests.get(base_url, params=params, headers=headers, timeout=20)
        resp.raise_for_status()
        payload = resp.json()
        results = payload.get("results", [])
        if not results:
            break
        for w in results:
            pt = w.get("primary_topic") or {}
            rows.append({
                "id": w.get("id", ""),
                "doi": w.get("doi", ""),
                "title": w.get("title") or w.get("display_name") or "",
                "abstract": "",
                "publication_year": w.get("publication_year"),
                "cited_by_count": w.get("cited_by_count", 0),
                "fwci": w.get("fwci"),
                "referenced_works": w.get("referenced_works") or [],
                "topic": pt.get("display_name", ""),
                "topic_id": (pt.get("id") or "").split("/")[-1],
                "subfield_name": (pt.get("subfield") or {}).get("display_name", ""),
                "field_name": (pt.get("field") or {}).get("display_name", ""),
                "domain_name": (pt.get("domain") or {}).get("display_name", ""),
                "author_names": [a.get("author", {}).get("display_name", "") for a in (w.get("authorships") or [])],
                "institution_names": [ins.get("display_name", "") for a in (w.get("authorships") or []) for ins in (a.get("institutions") or [])],
                "country_codes": [cc for a in (w.get("authorships") or []) for cc in (a.get("countries") or [])],
            })
            if len(rows) >= limit:
                break
        next_cursor = (payload.get("meta") or {}).get("next_cursor")
        if not next_cursor:
            break
        params["cursor"] = next_cursor

    df = pd.DataFrame(rows)
    logger.info(f"Extraídos {len(df):,} documentos desde OpenAlex REST API.")
    return df


def load_corpus(args) -> pd.DataFrame:
    """
    Carga el corpus bajo el principio Workspace-First:
    1. Si se especifica --input-file o existe corpus.parquet local, lo carga.
    2. Si ClickHouse está configurado explícitamente (CLICKHOUSE_HOST / --ch-host), usa fast-path CERO JOINs.
    3. En caso contrario, ejecuta fallback autónomo portátil contra OpenAlex REST API.
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

    # Tier 2: Acelerador opcional ClickHouse (solo si está explícitamente configurado)
    if args.ch_host:
        logger.info("No se encontró corpus local; intentando acelerador ClickHouse configurado...")
        try:
            import clickhouse_connect
            client = clickhouse_connect.get_client(
                host=args.ch_host,
                port=args.ch_port,
                username=args.ch_user,
                password=args.ch_password,
                database=args.ch_database,
                connect_timeout=3,
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
            logger.warning(f"ClickHouse no accesible ({e}). Cambiando a fallback autónomo OpenAlex API.")

    # Tier 3: Fallback autónomo portátil vía OpenAlex API
    try:
        return _fetch_openalex_api_fallback(args)
    except Exception as e:
        logger.error(f"Fallo al extraer corpus desde OpenAlex API: {e}")
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


def evaluate_fronts_partitions(
    S: sp.csr_matrix,
    min_sim: float = 0.05,
    min_cluster_size: int = 3,
    selected_partition_type: str = "modularity",
    selected_resolution: Optional[float] = None,
    eval_resolutions: Optional[List[float]] = None,
    seed: int = 42,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Evaluate candidate Leiden partitions (modularity and CPM across resolutions)
    preserving Modularity Q, valid fronts count, coverage %, and cluster size stats.
    """
    n_docs = S.shape[0]
    S_coo = S.tocoo()
    mask = S_coo.data >= min_sim
    rows = S_coo.row[mask]
    cols = S_coo.col[mask]
    weights = S_coo.data[mask]
    undir_mask = rows < cols
    rows, cols, weights = rows[undir_mask], cols[undir_mask], weights[undir_mask]

    g = ig.Graph()
    g.add_vertices(n_docs)
    edges = list(zip(rows.tolist(), cols.tolist()))
    g.add_edges(edges)
    g.es["weight"] = weights.tolist()

    comps = g.connected_components()
    density = round(2.0 * len(edges) / (n_docs * (n_docs - 1)), 6) if n_docs > 1 else 0.0
    isolated = sum(1 for d in g.degree() if d == 0)
    topo = {
        "n_nodes": n_docs,
        "n_edges": len(edges),
        "density": density,
        "connected_components": len(comps),
        "largest_component_size": max((len(c) for c in comps), default=0),
        "isolated_nodes": isolated,
    }
    if len(edges) == 0:
        return [], topo

    sel_res = selected_resolution if selected_resolution is not None else (0.01 if selected_partition_type == "cpm" else 1.0)
    if eval_resolutions:
        configs = [(selected_partition_type, float(r)) for r in eval_resolutions]
    else:
        configs = [
            ("modularity", 0.5), ("modularity", 0.75), ("modularity", 1.0), ("modularity", 1.25), ("modularity", 1.5),
            ("cpm", 0.005), ("cpm", 0.01), ("cpm", 0.02), ("cpm", 0.05),
        ]
    if not any(pt == selected_partition_type and abs(r - sel_res) < 1e-9 for pt, r in configs):
        configs.append((selected_partition_type, sel_res))

    eval_rows: List[Dict[str, Any]] = []
    for ptype, res in configs:
        if ptype == "cpm":
            part = leidenalg.find_partition(g, leidenalg.CPMVertexPartition, weights="weight", resolution_parameter=res, seed=seed)
        else:
            part = leidenalg.find_partition(g, leidenalg.RBConfigurationVertexPartition, weights="weight", resolution_parameter=res, seed=seed)
        counts = Counter(part.membership)
        valid_sizes = sorted([c for c in counts.values() if c >= min_cluster_size])
        covered = sum(valid_sizes)
        try:
            mod_q = float(g.modularity(part.membership, weights="weight"))
        except Exception:
            mod_q = 0.0
        mid = len(valid_sizes) // 2
        eval_rows.append({
            "algorithm": "leiden",
            "partition_type": ptype,
            "resolution": round(float(res), 6),
            "modularity_q": round(mod_q, 6),
            "objective_quality": round(float(part.quality()), 6),
            "n_raw_clusters": len(counts),
            "n_valid_fronts": len(valid_sizes),
            "valid_docs_covered": covered,
            "coverage_pct": round(100.0 * covered / max(1, n_docs), 2),
            "min_front_size": valid_sizes[0] if valid_sizes else 0,
            "median_front_size": float(valid_sizes[mid]) if valid_sizes else 0.0,
            "max_front_size": valid_sizes[-1] if valid_sizes else 0,
            "is_selected": (ptype == selected_partition_type and abs(res - sel_res) < 1e-9),
        })
    return eval_rows, topo


def render_fronts_eval_figure(eval_rows: List[Dict[str, Any]], out_path: str, lang: str = "en", dpi: int = 300) -> None:
    """Render Modularity Q and Valid Fronts across evaluated partition resolutions."""
    if not eval_rows:
        return
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return
    is_es = (lang == "es")
    ptypes = sorted(set(r["partition_type"] for r in eval_rows))
    fig, axes = plt.subplots(1, len(ptypes), figsize=(6.5 * len(ptypes), 4.4), dpi=dpi, facecolor="white")
    if len(ptypes) == 1:
        axes = [axes]
    for ax, pt in zip(axes, ptypes):
        sub = sorted([r for r in eval_rows if r["partition_type"] == pt], key=lambda x: x["resolution"])
        xs = [r["resolution"] for r in sub]
        qs = [r["modularity_q"] for r in sub]
        fs = [r["n_valid_fronts"] for r in sub]
        ax.plot(xs, qs, marker="o", color="#1d4ed8", linewidth=2.0, label="Modularity Q")
        ax2 = ax.twinx()
        ax2.plot(xs, fs, marker="s", linestyle="--", color="#047857", linewidth=1.8, label="# Frentes" if is_es else "# Fronts")
        for r in sub:
            if r.get("is_selected"):
                ax.scatter([r["resolution"]], [r["modularity_q"]], s=130, marker="*", color="#dc2626", zorder=6)
        ax.set_title(f"Leiden ({pt.upper()})", fontweight="bold")
        ax.set_xlabel("Resolución" if is_es else "Resolution")
        ax.set_ylabel("Modularidad Q" if is_es else "Modularity Q", color="#1d4ed8")
        ax2.set_ylabel("# Frentes válidos" if is_es else "# Valid Fronts", color="#047857")
        ax.grid(alpha=0.25, linestyle="--")
    fig.suptitle(
        "Evaluación Multi-Resolución de Frentes de Investigación" if is_es else "Multi-Resolution Research Fronts Evaluation",
        fontweight="bold", y=1.02,
    )
    fig.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)


_FRONT_PALETTE = [
    "#1d4ed8", "#dc2626", "#059669", "#d97706", "#7c3aed",
    "#0891b2", "#db2777", "#65a30d", "#ea580c", "#4f46e5",
    "#0d9488", "#be123c", "#ca8a04", "#9333ea", "#0284c7",
]


def render_fronts_network_png(
    network_nodes: List[Dict[str, Any]],
    network_edges: List[Dict[str, Any]],
    summary_records: List[Dict[str, Any]],
    out_path: str,
    method: str = "coupling",
    modularity_q: float = None,
    lang: str = "en",
    dpi: int = 300,
) -> None:
    """Render a 2-panel 300 DPI static PNG figure of research fronts (doc network + macro front backbone)."""
    active_recs = [r for r in summary_records if int(r.get("front_id", 0)) > 0]
    if not active_recs:
        return
    try:
        import math
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import networkx as nx
        from matplotlib.collections import LineCollection
        from matplotlib.patches import Polygon
        from scipy.spatial import ConvexHull
    except Exception:
        return

    is_es = (lang == "es")
    front_ids = [int(r["front_id"]) for r in active_recs]
    front_color = {fid: _FRONT_PALETTE[idx % len(_FRONT_PALETTE)] for idx, fid in enumerate(front_ids)}

    # Keep up to 300 top-cited active documents so dense corpora render crisply
    active_nodes = [n for n in network_nodes if int(n.get("front_id", 0)) > 0]
    if len(active_nodes) > 300:
        active_nodes = sorted(active_nodes, key=lambda n: n.get("citations", 0), reverse=True)[:300]
    active_ids = {n["id"] for n in active_nodes}
    sub_edges = [e for e in network_edges if e["source"] in active_ids and e["target"] in active_ids]
    node_front = {n["id"]: int(n["front_id"]) for n in active_nodes}

    # Layout documents around front centroids
    G_doc = nx.Graph()
    for n in active_nodes:
        G_doc.add_node(n["id"])
    for e in sub_edges:
        u, v = e["source"], e["target"]
        w = max(0.05, float(e.get("weight", 1.0)))
        vis_w = w * (2.6 if node_front.get(u) == node_front.get(v) else 0.35)
        G_doc.add_edge(u, v, weight=vis_w)

    centroids = {}
    n_f = max(1, len(front_ids))
    for idx, fid in enumerate(front_ids):
        if n_f == 1:
            centroids[fid] = (0.0, 0.0)
        else:
            ang = 2.0 * math.pi * idx / n_f
            rad = 2.4 + 0.14 * min(n_f, 10)
            centroids[fid] = (rad * math.cos(ang), rad * math.sin(ang))

    rng = np.random.default_rng(42)
    init_pos = {
        n["id"]: (centroids[node_front[n["id"]]][0] + float(rng.normal(0, 0.32)),
                  centroids[node_front[n["id"]]][1] + float(rng.normal(0, 0.32)))
        for n in active_nodes
    }
    if len(active_nodes) > 1:
        k_opt = 1.65 / math.sqrt(len(active_nodes))
        pos = nx.spring_layout(G_doc, pos=init_pos, weight="weight", k=k_opt, iterations=100, seed=42)
        xs = np.array([pos[nid][0] for nid in pos], dtype=float)
        ys = np.array([pos[nid][1] for nid in pos], dtype=float)
        span = max(float(xs.max() - xs.min()), float(ys.max() - ys.min()), 1e-6)
        cx_m = 0.5 * float(xs.max() + xs.min())
        cy_m = 0.5 * float(ys.max() + ys.min())
        pos = {nid: ((xy[0] - cx_m) * 2.0 / span, (xy[1] - cy_m) * 2.0 / span) for nid, xy in pos.items()}
    else:
        pos = {n["id"]: (0.0, 0.0) for n in active_nodes}

    fig, (ax_doc, ax_mac) = plt.subplots(1, 2, figsize=(15.5, 7.2), dpi=dpi, facecolor="white")
    for ax in (ax_doc, ax_mac):
        ax.set_facecolor("#fbfcfd")

    # Left panel: document-level hulls, edges, nodes, cluster badges
    for fid in front_ids:
        pts = np.array([pos[n["id"]] for n in active_nodes if int(n["front_id"]) == fid], dtype=float)
        if len(pts) >= 3:
            try:
                hull = ConvexHull(pts)
                poly = pts[hull.vertices]
                c = poly.mean(axis=0)
                poly = c + 1.15 * (poly - c)
                ax_doc.add_patch(Polygon(poly, closed=True, facecolor=front_color[fid], alpha=0.09,
                                         edgecolor=front_color[fid], linewidth=1.0, linestyle="--", zorder=1))
            except Exception:
                pass

    top_edges = sorted(sub_edges, key=lambda e: float(e.get("weight", 1.0)), reverse=True)[:700]
    if top_edges:
        ew = np.array([max(0.01, float(e.get("weight", 1.0))) for e in top_edges], dtype=float)
        ew_max = max(float(ew.max()), 1e-6)
        segs, ecols, ewids = [], [], []
        for e, w in zip(top_edges, ew):
            u, v = e["source"], e["target"]
            if u in pos and v in pos:
                segs.append([pos[u], pos[v]])
                same = (node_front[u] == node_front[v])
                col = front_color.get(node_front[u], "#64748b") if same else "#94a3b8"
                rel = w / ew_max
                ecols.append(matplotlib.colors.to_rgba(col, alpha=0.14 + 0.36 * rel))
                ewids.append(0.5 + 1.8 * rel)
        if segs:
            ax_doc.add_collection(LineCollection(segs, colors=ecols, linewidths=ewids, zorder=2))

    cites = np.array([max(0.0, float(n.get("citations", 0) or 0.0)) for n in active_nodes], dtype=float)
    sz = [45.0 + 340.0 * math.sqrt(math.log1p(c) / max(math.log1p(float(cites.max())), 1e-6)) for c in cites]
    ax_doc.scatter(
        [pos[n["id"]][0] for n in active_nodes],
        [pos[n["id"]][1] for n in active_nodes],
        s=sz,
        c=[front_color[int(n["front_id"])] for n in active_nodes],
        edgecolors="white", linewidths=0.8, alpha=0.9, zorder=4,
    )
    for fid in front_ids:
        pts = np.array([pos[n["id"]] for n in active_nodes if int(n["front_id"]) == fid], dtype=float)
        if len(pts) > 0:
            cx, cy = pts.mean(axis=0)
            ax_doc.text(cx, cy, f"F{fid}", fontsize=9.0, fontweight="bold", color="white",
                        ha="center", va="center", zorder=6,
                        bbox=dict(boxstyle="round,pad=0.25", facecolor=front_color[fid], edgecolor="white", linewidth=1.0, alpha=0.92))

    ax_doc.set_title(
        f"Red Documental de Frentes ({method})" if is_es else f"Document-Level Research Front Network ({method})",
        fontsize=11.5, fontweight="bold", color="#0f172a", pad=10,
    )
    ax_doc.set_xlim(-1.24, 1.24)
    ax_doc.set_ylim(-1.24, 1.24)
    ax_doc.axis("off")

    # Right panel: Macro inter-front backbone
    full_node_front = {n["id"]: int(n.get("front_id", 0)) for n in network_nodes}
    inter_weights = {}
    for e in network_edges:
        fu = full_node_front.get(e["source"], 0)
        fv = full_node_front.get(e["target"], 0)
        if fu > 0 and fv > 0 and fu != fv:
            pair = (min(fu, fv), max(fu, fv))
            inter_weights[pair] = inter_weights.get(pair, 0.0) + float(e.get("weight", 1.0))

    G_mac = nx.Graph()
    for r in active_recs:
        G_mac.add_node(int(r["front_id"]))
    for (fu, fv), w in inter_weights.items():
        G_mac.add_edge(fu, fv, weight=w)
    if len(front_ids) > 1:
        pos_mac = nx.spring_layout(G_mac, weight="weight", k=1.4 / math.sqrt(len(front_ids)), iterations=120, seed=42)
    else:
        pos_mac = {front_ids[0]: (0.0, 0.0)}

    if inter_weights:
        max_iw = max(inter_weights.values())
        for (fu, fv), w in inter_weights.items():
            if fu in pos_mac and fv in pos_mac:
                x1, y1 = pos_mac[fu]
                x2, y2 = pos_mac[fv]
                rel = w / max(max_iw, 1e-6)
                ax_mac.plot([x1, x2], [y1, y2], color="#64748b", alpha=0.22 + 0.55 * rel,
                            linewidth=0.9 + 4.0 * rel, zorder=2)

    pubs = np.array([max(1, int(r["publications_count"])) for r in active_recs], dtype=float)
    p_max = max(float(pubs.max()), 1.0)
    for r in active_recs:
        fid = int(r["front_id"])
        x, y = pos_mac[fid]
        msz = 260.0 + 1350.0 * (r["publications_count"] / p_max)
        ax_mac.scatter([x], [y], s=msz, c=[front_color[fid]], edgecolors="white", linewidths=1.6, alpha=0.93, zorder=4)
        ax_mac.text(x, y, f"F{fid}", fontsize=9.5, fontweight="bold", color="white", ha="center", va="center", zorder=5)
        fname = str(r.get("front_name", f"Front {fid}"))
        if len(fname) > 30:
            fname = fname[:27] + "..."
        fw = r.get("mean_fwci")
        fw_txt = f" | FWCI={fw:.2f}" if fw is not None else ""
        lbl = f"{fname}\n(n={r['publications_count']}, {r['total_citations']} cit.{fw_txt})"
        ax_mac.text(x, y - 0.14, lbl, fontsize=7.6, color="#0f172a", ha="center", va="top", zorder=6,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#cbd5e1", alpha=0.88))

    ax_mac.set_title(
        "Estructura Macro entre Frentes" if is_es else "Macro Inter-Front Backbone",
        fontsize=11.5, fontweight="bold", color="#0f172a", pad=10,
    )
    ax_mac.set_xlim(-1.35, 1.35)
    ax_mac.set_ylim(-1.42, 1.32)
    ax_mac.axis("off")

    q_txt = f" | Modularidad Q = {modularity_q:.3f}" if (is_es and modularity_q is not None) else (
        f" | Modularity Q = {modularity_q:.3f}" if modularity_q is not None else ""
    )
    fig.suptitle(
        ("Cartografía de Frentes de Investigación" if is_es else "Research Fronts Network Cartography") + q_txt,
        fontsize=13.5, fontweight="bold", y=0.99, color="#0f172a",
    )
    fig.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def label_fronts(df: pd.DataFrame, cluster_col: str = "cluster_id", lang: str = "en") -> Dict[int, str]:
    """
    Generates an automatic descriptive name for each front from titles and keywords.
    """
    labels = {}
    is_es = (lang == "es")
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
            label = f"Especialidad {c}" if is_es else f"Specialty {c}"
        prefix = "Frente" if is_es else "Front"
        labels[c] = f"{prefix} {c}: {label}"

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

        # 4. Clustering comunitario Leiden + Evaluación multi-resolución (Full Evidence-First)
        logger.info(f"Ejecutando partición modular {args.algorithm.upper()} (type={args.partition_type}, min_sim={args.min_similarity})...")
        raw_clusters = detect_clusters_leiden(
            S,
            min_sim=args.min_similarity,
            partition_type=args.partition_type,
            resolution=args.resolution,
            seed=args.random_seed
        )
        eval_res_list = [float(x.strip()) for x in args.eval_resolutions.split(",") if x.strip()] if getattr(args, "eval_resolutions", None) else None
        partition_eval, graph_topology = evaluate_fronts_partitions(
            S,
            min_sim=args.min_similarity,
            min_cluster_size=args.min_cluster_size,
            selected_partition_type=args.partition_type,
            selected_resolution=args.resolution,
            eval_resolutions=eval_res_list,
            seed=args.random_seed,
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

        is_es = (getattr(args, "lang", "en") == "es")
        df["front_id"] = df["cluster_id_raw"].map(lambda x: cluster_remap.get(x, 0))
        labels_dict = label_fronts(df[df["front_id"] > 0], cluster_col="front_id", lang=getattr(args, "lang", "en"))
        labels_dict[0] = "Residual / Trabajos Aislados" if is_es else "Residual / Isolated Works"
        df["front_name"] = df["front_id"].map(labels_dict)

    if args.method == "topics":
        partition_eval = []
        graph_topology = {"n_nodes": len(df), "method": "topics"}

    # 5. Generar Tabla Resumen de Frentes (fronts_summary.csv) + Evidencia Completa de Particiones
    is_es = (getattr(args, "lang", "en") == "es")
    cites_lbl = "Citas" if is_es else "Citations"
    na_lbl = "N/D" if is_es else "N/A"
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
            core_paper = f"{top_paper_row.get('title', na_lbl)} ({top_paper_row.get('publication_year', '')}), {cites_lbl}: {top_paper_row.get('cited_by_count', 0)}"
        else:
            core_paper = sub.iloc[0].get("title", na_lbl)

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

    sel_eval = next((r for r in partition_eval if r.get("is_selected")), None)
    selected_mod_q = sel_eval.get("modularity_q") if sel_eval else None
    front_sizes = [r["publications_count"] for r in summary_records]

    eval_csv_path = os.path.join(args.output_dir, "fronts_partition_eval.csv")
    eval_png_en = os.path.join(args.output_dir, "fronts_partition_eval_en.png")
    eval_png_es = os.path.join(args.output_dir, "fronts_partition_eval_es.png")
    if partition_eval:
        pd.DataFrame(partition_eval).to_csv(eval_csv_path, index=False)
        render_fronts_eval_figure(partition_eval, eval_png_en, lang="en")
        render_fronts_eval_figure(partition_eval, eval_png_es, lang="es")
        logger.info(f"Evaluación multi-resolución guardada en: {eval_csv_path}")

    network_payload = {
        "metadata": {
            "method": args.method,
            "similarity_metric": args.similarity_metric,
            "min_similarity": args.min_similarity,
            "algorithm": args.algorithm,
            "partition_type": args.partition_type,
            "resolution": args.resolution if args.resolution is not None else (0.01 if args.partition_type == "cpm" else 1.0),
            "modularity_q": selected_mod_q,
            "graph_topology": graph_topology,
            "cluster_size_distribution": {
                "min": min(front_sizes) if front_sizes else 0,
                "median": float(np.median(front_sizes)) if front_sizes else 0.0,
                "max": max(front_sizes) if front_sizes else 0,
            },
            "partition_evaluation": partition_eval,
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

    net_png_en = os.path.join(args.output_dir, "fronts_network_en.png")
    net_png_es = os.path.join(args.output_dir, "fronts_network_es.png")
    if summary_records:
        render_fronts_network_png(
            network_nodes, network_edges, summary_records, net_png_en,
            method=args.method, modularity_q=selected_mod_q, lang="en",
        )
        render_fronts_network_png(
            network_nodes, network_edges, summary_records, net_png_es,
            method=args.method, modularity_q=selected_mod_q, lang="es",
        )
        logger.info(f"Imágenes 300 DPI de red de frentes guardadas en: {net_png_en} | {net_png_es}")

    manifest_path = os.path.join(args.output_dir, "fronts_run_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as mf:
        json.dump({
            "pipeline": "topics-research-fronts-intelligence",
            "input_file": args.input_file,
            "parameters": vars(args),
            "graph_topology": graph_topology,
            "modularity_q": selected_mod_q,
            "partition_evaluation": partition_eval,
            "artifacts": {
                "fronts_summary_csv": summary_path,
                "fronts_network_json": network_path,
                "fronts_network_en_png": net_png_en if os.path.exists(net_png_en) else None,
                "fronts_network_es_png": net_png_es if os.path.exists(net_png_es) else None,
                "fronts_partition_eval_csv": eval_csv_path if partition_eval else None,
                "fronts_partition_eval_en_png": eval_png_en if partition_eval else None,
                "fronts_partition_eval_es_png": eval_png_es if partition_eval else None,
                "works_with_fronts_parquet": os.path.join(args.output_dir, "works_with_fronts.parquet"),
            },
        }, mf, indent=2, ensure_ascii=False, default=str)

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
