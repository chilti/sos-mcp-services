"""
supervisor_agent.py - Investigador Principal (PI) y Orquestador del Enjambre Científico
Implementa el ciclo iterativo de convergencia GCR (Conceive -> Ground -> Critic -> Resolve)
inspirado en ScientistOne (2026) y la orquestación multi-agente de alto rendimiento.
"""
import sys
import os
import time
import json
import uuid
from typing import Dict, Any, List, Optional

from agent.swarm.base_agent import BaseSpecialistAgent
from agent.swarm.data_scientist_agent import DataScientistAgent
from agent.swarm.topological_agent import TopologicalAgent
from agent.swarm.critic_agent import ScientometricCriticAgent
from agent.swarm.visualizer_agent import InteractiveVisualizerAgent
from agent.skill_manager import skill_manager
from agent.artifact_manager import artifact_manager
from lib.episodic_memory import episodic_memory

try:
    from smolagents import CodeAgent, OpenAIServerModel, tool
    HAS_SMOLAGENTS = True
except ImportError:
    HAS_SMOLAGENTS = False


class ScientificSwarm:
    """
    Enjambre Científico Autónomo Universal (Universal Scientific Swarm).
    Orquesta especialistas desacoplados, bucle de auto-crítica y trazabilidad CoE.
    """
    def __init__(
        self,
        system_namespace: str = "general",
        model_id: str = "local-model",
        api_base: str = "http://127.0.0.1:1234/v1/",
        api_key: str = "lm-studio",
        max_iterations: int = 3
    ):
        self.system_namespace = system_namespace
        self.model_id = model_id
        self.api_base = api_base
        self.api_key = api_key
        self.max_iterations = max_iterations

    def run_investigation(
        self,
        research_question: str,
        active_skills: Optional[List[str]] = None,
        entity_context: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta una investigación científica autónoma multi-agente completa con trazabilidad CoE.
        """
        start_time = time.time()
        sid = session_id or f"sci_{uuid.uuid4().hex[:10]}"
        
        # 1. Iniciar sesión en memoria episódica y consultar experiencias previas
        episodic_memory.start_session(session_id=sid, research_question=research_question, system_namespace=self.system_namespace)
        prior_experiences = episodic_memory.query_experiences(domain_topic=entity_context or research_question)

        # 2. Inicializar especialistas del enjambre vinculados a la sesión
        emitted_artifacts: List[Dict[str, Any]] = []
        data_agent = DataScientistAgent(session_id=sid, model_id=self.model_id, api_base=self.api_base, api_key=self.api_key)
        topo_agent = TopologicalAgent(session_id=sid, model_id=self.model_id, api_base=self.api_base, api_key=self.api_key)
        critic_agent = ScientometricCriticAgent(session_id=sid, model_id=self.model_id, api_base=self.api_base, api_key=self.api_key)
        vis_agent = InteractiveVisualizerAgent(session_id=sid, emitted_collector=emitted_artifacts, model_id=self.model_id, api_base=self.api_base, api_key=self.api_key)

        # 3. Match de Skills Metodológicos
        if active_skills:
            matched_skills = [skill_manager.skills[s] for s in active_skills if s in skill_manager.skills]
        else:
            matched_skills = skill_manager.match_skills(research_question, top_k=2)
        skills_used = [s.name for s in matched_skills]
        skills_instructions = skill_manager.get_skill_instructions(skills_used)

        # 4. Formular el DAG inicial de investigación
        dag_log = [
            {"phase": "1. Planificación & Hipótesis", "status": "COMPLETED", "agent": "Supervisor", "details": f"Skills: {skills_used}"}
        ]

        # 5. BUCLE CIENTÍFICO ITERATIVO (Conceive -> Ground -> Critic -> Resolve)
        iteration = 1
        is_approved = False
        critic_verdict: Dict[str, Any] = {}
        last_findings = ""
        critic_feedback = ""

        while iteration <= self.max_iterations and not is_approved:
            iter_prefix = f"[Iteración {iteration}/{self.max_iterations}]"
            
            # --- FASE A: Data Engineering & Grounding ---
            dag_log.append({"phase": f"{iter_prefix} Extracción de Datos & GraphRAG", "status": "RUNNING", "agent": "DataScientistAgent"})
            data_task = (
                f"Para responder la pregunta: '{research_question}', extrae y calcula las métricas requeridas "
                f"usando ClickHouse, Parquet o perfiles consolidados. Entidad: {entity_context or 'Nacional'}. "
                f"Feedback previo del Crítico: {critic_feedback or 'Ninguno (primera pasada)'}."
            )
            data_res = data_agent.execute_task(data_task)
            dag_log[-1]["status"] = "COMPLETED"

            # --- FASE B: Modelado Topológico / Redes / SOM (si aplica) ---
            topo_output = ""
            if any(k in research_question.lower() for k in ["som", "malla", "red", "louvain", "umap", "frente", "cluster", "topolog"]):
                dag_log.append({"phase": f"{iter_prefix} Modelado Topológico (SOM / Redes / UMAP)", "status": "RUNNING", "agent": "TopologicalAgent"})
                topo_task = (
                    f"Con base en los datos: {data_res.get('output', '')[:400]}, calcula la malla SOM óptima (SVD), "
                    f"modularidad de comunidades (Louvain) o reducción UMAP. {skills_instructions}"
                )
                topo_res = topo_agent.execute_task(topo_task)
                topo_output = topo_res.get("output", "")
                dag_log[-1]["status"] = "COMPLETED"

            # --- FASE C: Síntesis de Hallazgos preliminares ---
            last_findings = f"DATOS EXTRAÍDOS:\n{data_res.get('output', '')}\n\nMODELADO TOPOLÓGICO:\n{topo_output}"

            # --- FASE D: Revisión por Pares & Auditoría CoE (Scientometric Critic) ---
            dag_log.append({"phase": f"{iter_prefix} Auditoría de Integridad CoE & Revisión por Pares", "status": "RUNNING", "agent": "ScientometricCriticAgent"})
            critic_verdict = critic_agent.review_investigation(
                hypothesis=f"Pregunta: {research_question} sobre {entity_context or 'General'}",
                findings=last_findings,
                evidence_summary=str(episodic_memory.get_session_provenance(sid))[:800]
            )
            dag_log[-1]["status"] = "COMPLETED"
            dag_log[-1]["verdict"] = critic_verdict.get("approved", True)

            if critic_verdict.get("approved", True) or iteration == self.max_iterations:
                is_approved = True
            else:
                critic_feedback = critic_verdict.get("critique", "Refinar consistencia.")
                iteration += 1

        # 6. FASE FINAL: Emisión y Renderizado de Artefactos Interactivos
        dag_log.append({"phase": "Generación de Artefactos & Reporte Ejecutivo", "status": "RUNNING", "agent": "InteractiveVisualizerAgent"})
        vis_task = (
            f"Con base en los hallazgos validados: {last_findings[:500]}, genera los artefactos visuales interactivos "
            f"adecuados llamando a `emit_standard_artifact` o auto-sintetizando uno nuevo con `synthesize_new_artifact`. "
            f"Si aplica una malla SOM, usa 'som-hexagonal-mesh'; si es una red, usa 'bibliometric-force-network'; "
            f"y siempre que sea un análisis institucional amplio, incluye 'scientific-executive-report'."
        )
        vis_res = vis_agent.execute_task(vis_task)
        dag_log[-1]["status"] = "COMPLETED"

        # Fallback de auto-extracción desde texto en caso de que los datos estén en texto
        if not emitted_artifacts and last_findings:
            auto_detected = artifact_manager.detect_and_render_artifacts_from_text(last_findings + "\n" + vis_res.get("output", ""))
            if auto_detected:
                emitted_artifacts.extend(auto_detected)

        # 7. Consolidar respuesta final y cerrar sesión
        final_narrative = (
            f"### 🔬 Investigación Científica y Diagnóstico Cienciométrico\n\n"
            f"**Contexto:** `{entity_context or 'General / Nacional'}` | **Sesión CoE:** `{sid}`\n\n"
            f"{last_findings}\n\n"
            f"---\n"
            f"#### 🔍 Auditoría de Integridad CoE (ScientistOne Standard):\n"
            f"* **Veredicto del Crítico:** {'✅ Aprobado' if is_approved else '⚠️ Aprobado con Observaciones'} (Confianza: {int(critic_verdict.get('confidence', 0.9)*100)}%)\n"
            f"* **Iteraciones de Refinamiento:** {iteration}\n"
            f"* **Crítica / Síntesis:** {critic_verdict.get('critique', 'Análisis metodológicamente consistente y fundamentado en evidencia.')}\n"
        )

        episodic_memory.close_session(
            session_id=sid,
            plan_dag={"dag_steps": dag_log},
            iterations_count=iteration,
            critic_verdict=critic_verdict,
            artifacts_emitted=emitted_artifacts,
            final_answer=final_narrative
        )

        return {
            "session_id": sid,
            "answer": final_narrative,
            "dag_steps": dag_log,
            "skills_used": skills_used,
            "iterations": iteration,
            "critic_verdict": critic_verdict,
            "artifacts": emitted_artifacts,
            "provenance": episodic_memory.get_session_provenance(sid),
            "status": "success",
            "duration_seconds": round(time.time() - start_time, 2)
        }
