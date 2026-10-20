import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import networkx as nx
from networkx.algorithms.community import louvain_communities, modularity

# Asegurar KnoMap Engine en sys.path
KNOMAP_ENGINE_DIR = Path("/home/labsom/knomap/engine")
if str(KNOMAP_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(KNOMAP_ENGINE_DIR))

try:
    from bibliometrics_parser import read_and_generate_bibliometrics
    HAS_BIBLIO_PARSER = True
except Exception:
    HAS_BIBLIO_PARSER = False


def parse_bibliographic_file(
    filepath: str,
    network_type: str = "co-occurrence",
    custom_tag: str = "DE",
    max_terms: int = 100,
    min_cooccurrence: int = 2,
    counting_method: str = "full",
    thesaurus_filepath: Optional[str] = None
) -> Dict[str, Any]:
    """
    Procesa un archivo bibliográfico (WoS plano/tab, Scopus CSV, RIS, PubMed XML, OpenAlex JSON/Parquet)
    y genera una red bibliométrica VOSviewer con matriz de adyacencia y fuerza de asociación.
    """
    if not os.path.exists(filepath):
        return {
            "status": "error",
            "message": f"Archivo no encontrado: '{filepath}'",
            "filepath": filepath
        }

    if HAS_BIBLIO_PARSER:
        try:
            res = read_and_generate_bibliometrics(
                file_path=filepath,
                network_type=network_type,
                max_terms=max_terms,
                min_cooccurrence=min_cooccurrence
            )
            if res.get("matrix"):
                terms = res.get("terms", [])
                matrix = res.get("matrix", [])
                nodes = [{"id": i, "label": t, "weight": sum(matrix[i]) if i < len(matrix) else 1} for i, t in enumerate(terms)]
                links = []
                for i in range(len(terms)):
                    for j in range(i + 1, len(terms)):
                        w = matrix[i][j] if i < len(matrix) and j < len(matrix[i]) else 0
                        if w > 0:
                            links.append({"source": i, "target": j, "strength": w})

                return {
                    "status": "success",
                    "filepath": filepath,
                    "network_type": network_type,
                    "extracted_nodes_count": len(nodes),
                    "extracted_edges_count": len(links),
                    "network_data": {
                        "nodes": nodes,
                        "links": links
                    },
                    "terms": terms,
                    "matrix": matrix,
                    "summary": f"Red de {network_type} extraída exitosamente con {len(nodes)} términos y {len(links)} relaciones de co-ocurrencia."
                }
        except Exception as e:
            pass

    return {
        "status": "error",
        "message": "No se pudo procesar el archivo bibliográfico con el parser de KnoMap.",
        "filepath": filepath
    }


def detect_louvain_communities(
    vosviewer_json: Dict[str, Any],
    resolution: float = 1.0,
    min_cluster_size: int = 2
) -> Dict[str, Any]:
    """
    Ejecuta detección real de comunidades de Louvain sobre un grafo o red VOSviewer,
    calculando la modularidad Newman-Girvan Q exacta y asignando etiquetas de cluster a cada nodo.
    """
    network_data = vosviewer_json.get("network_data", vosviewer_json)
    nodes = network_data.get("nodes", network_data.get("items", []))
    links = network_data.get("links", network_data.get("edges", []))

    if not nodes:
        return {
            "status": "error",
            "message": "No se encontraron nodos en el objeto de red proporcionado.",
            "modularity_q": 0.0,
            "clusters_found": 0
        }

    G = nx.Graph()
    node_labels = {}
    for n in nodes:
        nid = n.get("id", n.get("label"))
        lbl = n.get("label", str(nid))
        node_labels[nid] = lbl
        G.add_node(nid, label=lbl, weight=n.get("weight", 1))

    for e in links:
        src = e.get("source", e.get("from"))
        tgt = e.get("target", e.get("to"))
        weight = float(e.get("strength", e.get("weight", 1.0)))
        if src in G and tgt in G and src != tgt:
            G.add_edge(src, tgt, weight=weight)

    if G.number_of_edges() == 0:
        return {
            "status": "success",
            "modularity_q": 0.0,
            "resolution": resolution,
            "clusters_found": 1,
            "cluster_sizes": {"Cluster 1": len(nodes)},
            "summary": "Grafo sin aristas interconectadas. Todos los nodos asignados a un cluster único."
        }

    # Algoritmo Louvain con peso
    try:
        communities = list(louvain_communities(G, weight="weight", resolution=resolution, seed=42))
        q = float(modularity(G, communities, weight="weight"))
    except Exception as e:
        communities = [set(G.nodes())]
        q = 0.0

    # Filtrar por tamaño mínimo
    filtered_comms = [c for c in communities if len(c) >= min_cluster_size]
    if not filtered_comms:
        filtered_comms = communities

    cluster_sizes = {}
    node_assignments = {}
    for c_idx, c_nodes in enumerate(filtered_comms, 1):
        cluster_name = f"Cluster {c_idx}"
        cluster_sizes[cluster_name] = len(c_nodes)
        for nid in c_nodes:
            node_assignments[str(nid)] = {
                "label": node_labels.get(nid, str(nid)),
                "cluster_id": c_idx
            }

    return {
        "status": "success",
        "modularity_q": round(q, 4),
        "resolution": resolution,
        "clusters_found": len(filtered_comms),
        "cluster_sizes": cluster_sizes,
        "node_assignments": node_assignments,
        "summary": f"Detección Louvain completada con éxito: {len(filtered_comms)} comunidades detectadas con modularidad Q={q:.4f}."
    }
