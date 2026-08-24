"""
data_scientist_agent.py - Agente Especialista en Datos Científicos Masivos y GraphRAG
"""
import sys
import os
from typing import Dict, Any, List, Optional

from agent.swarm.base_agent import BaseSpecialistAgent
from lib.episodic_memory import episodic_memory

try:
    from smolagents import tool
except ImportError:
    def tool(fn): return fn


def get_data_scientist_tools(session_id: Optional[str] = None) -> List[Any]:
    """Crea y envuelve las herramientas de datos científicos con trazabilidad CoE."""
    tools = []

    # 1. ClickHouse Safe SQL Query
    @tool
    def query_clickhouse_analytics(sql_query: str, purpose: str = "") -> str:
        """
        Ejecuta consultas analíticas SQL en ClickHouse sobre 569M de papers de OpenAlex y tablas pre-materializadas.
        Args:
            sql_query: Consulta SQL que inicie con SELECT.
            purpose: Justificación o propósito del dato solicitado.
        """
        from agent.tools_interpreter import query_clickhouse_safe_sql
        res = query_clickhouse_safe_sql.invoke({'sql_query': sql_query})
        if session_id:
            episodic_memory.record_evidence(
                session_id=session_id,
                claim_type="numerical",
                claim_text=f"ClickHouse Query: {sql_query[:80]}...",
                evidence_source="clickhouse",
                evidence_payload={"sql": sql_query, "result_preview": str(res)[:300]}
            )
        return res
    tools.append(query_clickhouse_analytics)

    # 2. Local Academic Parquet Cache
    @tool
    def query_parquet_academic_cache(table_type: str, institution: str = "", academic: str = "", top_n: int = 10) -> str:
        """
        Consulta tablas estructuradas Parquet de métricas anuales de instituciones y académicos (FWCI, documentos, citas).
        Args:
            table_type: Tipo de tabla ('institucion_annual', 'investigador_annual', 'papers_profesor', 'topics', 'umap_investigadores').
            institution: Nombre de la institución (ej. 'UNIVERSIDAD NACIONAL AUTONOMA DE MEXICO').
            academic: Nombre del investigador.
            top_n: Número de filas.
        """
        from agent.tools_interpreter import query_academic_cache
        inst = institution if institution else None
        ac = academic if academic else None
        res = query_academic_cache.invoke({
            'table_type': table_type,
            'institution': inst,
            'academic': ac,
            'sort_by': None,
            'top_n': top_n
        })
        if session_id:
            episodic_memory.record_evidence(
                session_id=session_id,
                claim_type="numerical",
                claim_text=f"Parquet Cache ({table_type}): {institution or academic}",
                evidence_source="parquet",
                evidence_payload={"table": table_type, "filter": institution or academic, "data": str(res)[:300]}
            )
        return res
    tools.append(query_parquet_academic_cache)

    # 3. Hybrid Researcher Impact Profile
    @tool
    def get_consolidated_scholar_summary(academic_name: str, institution_name: str = "") -> str:
        """
        Obtiene el resumen consolidado de impacto de un investigador cruzando Neo4j, SNII y ClickHouse.
        Args:
            academic_name: Nombre completo del investigador.
            institution_name: Institución de filiación.
        """
        from agent.tools_interpreter import get_scientometric_summary
        inst = institution_name if institution_name else None
        res = get_scientometric_summary.invoke({'academic_name': academic_name, 'institution_name': inst})
        if session_id:
            episodic_memory.record_evidence(
                session_id=session_id,
                claim_type="numerical",
                claim_text=f"Perfil de Investigador: {academic_name}",
                evidence_source="neo4j_clickhouse",
                evidence_payload={"academic": academic_name, "summary": str(res)[:300]}
            )
        return res
    tools.append(get_consolidated_scholar_summary)

    return tools


class DataScientistAgent(BaseSpecialistAgent):
    """Agente especialista en ingesta, consultas masivas ClickHouse, GraphRAG y evidencia empírica."""
    def __init__(self, session_id: Optional[str] = None, **kwargs):
        tools = get_data_scientist_tools(session_id=session_id)
        role = ("Experto en extracción masiva de datos bibliométricos desde ClickHouse (569M trabajos de OpenAlex), "
                "Grafos de Conocimiento Neo4j (investigadores SNII), búsqueda vectorial en Qdrant y tablas Parquet. "
                "Garantiza que ningún dato sea inventado y registra cada fuente en la cadena de evidencia CoE.")
        super().__init__(name="DataScientistAgent", role_description=role, tools=tools, **kwargs)
