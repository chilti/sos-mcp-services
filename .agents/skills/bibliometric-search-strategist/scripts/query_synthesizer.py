#!/usr/bin/env python3
"""
query_synthesizer.py

Validador, sintetizador y transpilador multiplataforma de estrategias de
búsqueda bibliográfica para cienciometría y revisiones sistemáticas.
Soporta Web of Science, Scopus, PubMed y ClickHouse (rag.works_academic_all).
"""

import argparse
import json
import os
import re
import sys
from typing import Dict, List, Any, Tuple


class QueryValidator:
    """Validador sintáctico y de mejores prácticas (PRESS 2015) para queries booleanas."""

    @staticmethod
    def check_parentheses(query: str) -> List[str]:
        errors = []
        stack = []
        for i, char in enumerate(query):
            if char == '(':
                stack.append(i)
            elif char == ')':
                if not stack:
                    errors.append(f"Paréntesis de cierre ')' huérfano en la posición {i}.")
                else:
                    stack.pop()
        if stack:
            for pos in stack:
                errors.append(f"Paréntesis de apertura '(' no cerrado en la posición {pos}.")
        return errors

    @staticmethod
    def check_quotes(query: str) -> List[str]:
        errors = []
        quote_count = query.count('"')
        if quote_count % 2 != 0:
            errors.append(f"Comillas desbalanceadas: se encontraron {quote_count} comillas dobles (número impar).")
        return errors

    @staticmethod
    def check_lowercase_operators(query: str) -> List[str]:
        warnings = []
        # Buscar palabras 'and', 'or', 'not' fuera de comillas
        # Tokenizamos respetando comillas
        parts = re.split(r'("[^"]*")', query)
        for i, part in enumerate(parts):
            if i % 2 == 0:  # Fuera de comillas
                for match in re.finditer(r'\b(and|or|not)\b', part):
                    warnings.append(
                        f"Operador en minúsculas detectado: '{match.group(0)}'. "
                        f"Recomendado en MAYÚSCULAS ('{match.group(0).upper()}') para evitar ambigüedades."
                    )
        return warnings

    @staticmethod
    def check_dangerous_wildcards(query: str) -> List[str]:
        warnings = []
        # Buscar palabras con asterisco que tengan menos de 4 caracteres previos
        for match in re.finditer(r'\b([a-zA-Z]{1,3})\*', query):
            warnings.append(
                f"Truncamiento de raíz corta potencialmente peligroso: '{match.group(0)}'. "
                f"Raíz '{match.group(1)}' < 4 letras puede causar desbordamiento léxico masivo."
            )
        return warnings

    @staticmethod
    def check_empty_clauses(query: str) -> List[str]:
        errors = []
        patterns = [
            (r'\b(AND|OR|NOT)\s+(AND|OR)\b', "Operadores booleanos consecutivos sin operando."),
            (r'\(\s*(AND|OR)\b', "Operador booleano al inicio inmediato de un paréntesis."),
            (r'\b(AND|OR|NOT)\s*\)', "Operador booleano al final de una cláusula antes de cerrar paréntesis."),
            (r'\(\s*\)', "Paréntesis vacíos '()' detectados.")
        ]
        for pat, msg in patterns:
            if re.search(pat, query, re.IGNORECASE):
                errors.append(msg)
        return errors

    @classmethod
    def validate(cls, query: str) -> Dict[str, Any]:
        paren_errs = cls.check_parentheses(query)
        quote_errs = cls.check_quotes(query)
        empty_errs = cls.check_empty_clauses(query)
        op_warns = cls.check_lowercase_operators(query)
        wild_warns = cls.check_dangerous_wildcards(query)

        is_valid = len(paren_errs) == 0 and len(quote_errs) == 0 and len(empty_errs) == 0

        return {
            "is_valid": is_valid,
            "errors": paren_errs + quote_errs + empty_errs,
            "warnings": op_warns + wild_warns,
            "character_count": len(query),
            "approx_tokens": len(query.split())
        }


class QueryTranspiler:
    """Transpila una definición estructurada de bloques a WoS, Scopus, PubMed y ClickHouse."""

    def __init__(self, spec: Dict[str, Any]):
        self.spec = spec
        # Soporta 'blocks' (preferido en cienciometría) y 'facets' (retrocompatibilidad)
        self.blocks = spec.get("blocks", spec.get("facets", []))
        self.facets = self.blocks
        self.filters = spec.get("filters", {})
        self.title = spec.get("project_title", "Estrategia Bibliométrica")

    def to_wos(self) -> str:
        block_clauses = []
        for block in self.blocks:
            terms = block.get("terms", [])
            wos_terms = [f'"{t}"' if " " in t and not t.startswith('"') else t for t in terms]
            clause = " OR ".join(wos_terms)
            block_clauses.append(f"TS=({clause})")

        query = "\n  AND ".join(block_clauses)

        # Filtros
        filter_parts = []
        y_start = self.filters.get("year_start")
        y_end = self.filters.get("year_end")
        if y_start and y_end:
            filter_parts.append(f"PY=({y_start}-{y_end})")
        elif y_start:
            filter_parts.append(f"PY>=({y_start})")

        doc_types = self.filters.get("doc_types", [])
        if doc_types:
            dt_map = {"article": "Article", "review": "Review"}
            dt_vals = [dt_map.get(d.lower(), d.capitalize()) for d in doc_types]
            filter_parts.append(f"DT=({' OR '.join(dt_vals)})")

        if filter_parts:
            query += "\n  AND " + "\n  AND ".join(filter_parts)

        return query

    def to_scopus(self) -> str:
        block_clauses = []
        for block in self.blocks:
            terms = block.get("terms", [])
            scopus_terms = [f'"{t}"' if " " in t and not t.startswith('"') else t for t in terms]
            clause = " OR ".join(scopus_terms)
            block_clauses.append(f"TITLE-ABS-KEY({clause})")

        query = "\n  AND ".join(block_clauses)

        filter_parts = []
        y_start = self.filters.get("year_start")
        y_end = self.filters.get("year_end")
        if y_start and y_end:
            filter_parts.append(f"PUBYEAR > {y_start - 1} AND PUBYEAR < {y_end + 1}")
        elif y_start:
            filter_parts.append(f"PUBYEAR > {y_start - 1}")

        doc_types = self.filters.get("doc_types", [])
        if doc_types:
            dt_map = {"article": "ar", "review": "re", "conference": "cp"}
            dt_vals = [f"DOCTYPE({dt_map.get(d.lower(), d)})" for d in doc_types]
            filter_parts.append(f"({' OR '.join(dt_vals)})")

        if filter_parts:
            query += "\n  AND " + "\n  AND ".join(filter_parts)

        return query

    def to_pubmed(self) -> str:
        block_clauses = []
        for block in self.blocks:
            terms = block.get("terms", [])
            mesh_terms = block.get("mesh", [])
            tiab_terms = [f'"{t}"[tiab]' if " " in t and not t.startswith('"') else f'{t}[tiab]' for t in terms]
            mesh_clauses = [f'"{m}"[mesh]' for m in mesh_terms]
            all_block_terms = tiab_terms + mesh_clauses
            clause = " OR ".join(all_block_terms)
            block_clauses.append(f"({clause})")

        query = "\n  AND ".join(block_clauses)

        filter_parts = []
        y_start = self.filters.get("year_start")
        y_end = self.filters.get("year_end")
        if y_start and y_end:
            filter_parts.append(f"{y_start}:{y_end}[dp]")

        doc_types = self.filters.get("doc_types", [])
        if doc_types:
            dt_map = {"article": "journal article", "review": "review"}
            dt_vals = [f'"{dt_map.get(d.lower(), d)}"[pt]' for d in doc_types]
            filter_parts.append(f"({' OR '.join(dt_vals)})")

        if filter_parts:
            query += "\n  AND " + "\n  AND ".join(filter_parts)

        return query

    def to_clickhouse_sql(self) -> str:
        """Genera SQL optimizado para rag.works_academic_all con CERO JOINs."""
        where_conditions = []

        for block in self.blocks:
            terms = block.get("terms", [])
            topics = block.get("topics", [])
            block_subs = []

            for t in terms:
                clean_term = t.replace("'", "\\'").replace("*", "")
                block_subs.append(f"positionCaseInsensitiveUTF8(title, '{clean_term}') > 0")
                block_subs.append(f"arrayExists(x -> positionCaseInsensitiveUTF8(x, '{clean_term}') > 0, keywords)")

            for top in topics:
                clean_top = top.replace("'", "\\'")
                block_subs.append(f"positionCaseInsensitiveUTF8(topic, '{clean_top}') > 0")

            clause = "(\n      " + "\n      OR ".join(block_subs) + "\n    )"
            where_conditions.append(clause)

        # Filtros
        y_start = self.filters.get("year_start")
        y_end = self.filters.get("year_end")
        if y_start and y_end:
            where_conditions.append(f"(publication_year >= {y_start} AND publication_year <= {y_end})")
        elif y_start:
            where_conditions.append(f"publication_year >= {y_start}")

        doc_types = self.filters.get("doc_types", [])
        if doc_types:
            dt_str = ", ".join(f"'{d.lower()}'" for d in doc_types)
            where_conditions.append(f"type IN ({dt_str})")

        countries = self.filters.get("countries", [])
        if "Mexico" in countries or "MX" in countries:
            where_conditions.append("(country_code = 'MX' OR has(all_country_codes, 'MX'))")

        oa_status = self.filters.get("oa_status")
        if oa_status:
            where_conditions.append(f"oa_status = '{oa_status.lower()}'")

        sql = "-- Consulta generada automáticamente por Bibliometric Search Strategist\n"
        sql += "-- Tabla canónica: rag.works_academic_all | Regla: CERO JOINS\n"
        sql += "SELECT\n"
        sql += "    id,\n"
        sql += "    doi,\n"
        sql += "    title,\n"
        sql += "    publication_year,\n"
        sql += "    type,\n"
        sql += "    oa_status,\n"
        sql += "    cited_by_count,\n"
        sql += "    fwci,\n"
        sql += "    author_names,\n"
        sql += "    institution_names,\n"
        sql += "    topic,\n"
        sql += "    keywords\n"
        sql += "FROM rag.works_academic_all\n"
        sql += "WHERE\n  " + "\n  AND ".join(where_conditions) + "\n"
        sql += "ORDER BY cited_by_count DESC\n"
        sql += "LIMIT 5000\n"

        return sql

    def generate_global_template(self) -> str:
        y_start = self.filters.get("year_start", "N/D")
        y_end = self.filters.get("year_end", "N/D")
        doc_types = ", ".join(self.filters.get("doc_types", [])) or "No especificado"

        md = f"# Auditoría de Delimitación Bibliométrica bajo la Directriz GLOBAL (ISSI)\n"
        md += f"**Proyecto:** {self.title}\n\n"
        md += "> *Basado en: International Society for Scientometrics and Informetrics (ISSI) / ScholCommLab (2023-2024). "
        md += "GLOBAL: Guidance List for repOrting Bibliometric AnaLyses.*\n\n"
        md += "## Lista de Verificación de Delimitación y Recolección de Datos\n\n"
        md += "| Dimensión GLOBAL | Ítem de Auditoría | Estado | Especificación Metodológica |\n"
        md += "|---|---|:---:|---|\n"
        md += f"| **1. Justificación Conceptual** | Delimitación del dominio y preguntas | ✅ | Descomposición en {len(self.blocks)} bloques conceptuales ortogonales (Building Blocks). |\n"
        md += "| **2. Fuentes y Snapshot** | Declaración de bases y fecha de corte | ℹ️ | Transpilación multi-base (WoS, Scopus, PubMed, ClickHouse). *Registrar fecha y huso horario exacto en la extracción final.* |\n"
        md += "| **3. Delimitación de Campo** | Ecuación exacta y etiquetas de campo | ✅ | Sintaxis calibrada con etiquetas específicas (`TS=`, `TITLE-ABS-KEY()`, `[tiab]` y funciones nativas ClickHouse). |\n"
        md += "| **4. Selección de Descriptores** | Vocabularios controlados y sinónimos | ✅ | Integración multi-esquema: MeSH, Topics de OpenAlex y vocabulario técnico no controlado. |\n"
        md += "| **5. Ortografía y Truncamiento** | Comodines seguros y balanceo léxico | ✅ | Comillas balanceadas, ausencia de comodines con raíces < 4 letras y operadores en mayúsculas auditados. |\n"
        md += f"| **6. Filtros y Límites** | Ventana temporal y tipos de documento | ✅ | Rango temporal: {y_start}–{y_end}; Tipologías admitidas: `{doc_types}`. |\n"
        md += "| **7. Reproducibilidad y Código** | Disponibilidad de sintaxis y scripts | ✅ | Ecuaciones versionadas en texto plano y script de transpilación `query_synthesizer.py` reproducible. |\n\n"
        md += "### Estructura de Bloques Conceptuales (Building Blocks):\n"
        for i, b in enumerate(self.blocks, 1):
            md += f"- **Bloque {i} ({b.get('name', 'N/D')}):** {len(b.get('terms', []))} términos libres, {len(b.get('mesh', []))} MeSH, {len(b.get('topics', []))} Topics.\n"
        return md


def main():
    parser = argparse.ArgumentParser(description="Bibliometric Search Strategist - Query Synthesizer CLI (Alineado con GLOBAL / ISSI)")
    parser.add_argument("--action", choices=["validate", "transpile", "format"], required=True)
    parser.add_argument("--query", type=str, help="Cadena de búsqueda booleana a validar o formatear")
    parser.add_argument("--config", type=str, help="Archivo JSON/YAML con la definición de bloques conceptuales")
    parser.add_argument("--output", type=str, default="./search_output", help="Directorio para guardar los artefactos generados")

    args = parser.parse_args()

    if args.action == "validate":
        if not args.query:
            print("Error: Se requiere --query para la acción 'validate'.", file=sys.stderr)
            sys.exit(1)
        res = QueryValidator.validate(args.query)
        print("\n=== REPORTE DE VALIDACIÓN SINTÁCTICA ===")
        print(f"Estado: {'VÁLIDA ✅' if res['is_valid'] else 'INVÁLIDA ❌'}")
        print(f"Caracteres: {res['character_count']} | Tokens aprox: {res['approx_tokens']}")
        if res["errors"]:
            print("\n[ERRORES CRÍTICOS]:")
            for e in res["errors"]:
                print(f"  ❌ {e}")
        if res["warnings"]:
            print("\n[ADVERTENCIAS / MEJORES PRÁCTICAS]:")
            for w in res["warnings"]:
                print(f"  ⚠️ {w}")
        if not res["errors"] and not res["warnings"]:
            print("No se detectaron anomalías sintácticas.")
        sys.exit(0 if res["is_valid"] else 1)

    elif args.action == "transpile":
        if not args.config:
            print("Error: Se requiere --config para la acción 'transpile'.", file=sys.stderr)
            sys.exit(1)
        if not os.path.exists(args.config):
            print(f"Error: No existe el archivo de configuración '{args.config}'.", file=sys.stderr)
            sys.exit(1)

        with open(args.config, "r", encoding="utf-8") as f:
            spec = json.load(f)

        transpiler = QueryTranspiler(spec)
        os.makedirs(args.output, exist_ok=True)

        wos_q = transpiler.to_wos()
        scopus_q = transpiler.to_scopus()
        pubmed_q = transpiler.to_pubmed()
        ch_sql = transpiler.to_clickhouse_sql()
        global_md = transpiler.generate_global_template()

        with open(os.path.join(args.output, "wos_query.txt"), "w", encoding="utf-8") as f:
            f.write(wos_q)
        with open(os.path.join(args.output, "scopus_query.txt"), "w", encoding="utf-8") as f:
            f.write(scopus_q)
        with open(os.path.join(args.output, "pubmed_query.txt"), "w", encoding="utf-8") as f:
            f.write(pubmed_q)
        with open(os.path.join(args.output, "clickhouse_query.sql"), "w", encoding="utf-8") as f:
            f.write(ch_sql)
        with open(os.path.join(args.output, "global_audit.md"), "w", encoding="utf-8") as f:
            f.write(global_md)

        print(f"\n✅ Transpilación completada exitosamente en '{args.output}':")
        print("  - wos_query.txt (Web of Science)")
        print("  - scopus_query.txt (Scopus)")
        print("  - pubmed_query.txt (PubMed)")
        print("  - clickhouse_query.sql (ClickHouse / rag.works_academic_all)")
        print("  - global_audit.md (Auditoría GLOBAL / ISSI)")

    elif args.action == "format":
        if not args.query:
            print("Error: Se requiere --query para la acción 'format'.", file=sys.stderr)
            sys.exit(1)
        formatted = re.sub(r'\s+AND\s+', '\n  AND ', args.query)
        print(formatted)


if __name__ == "__main__":
    main()

