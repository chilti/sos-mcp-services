---
name: snii-identity-resolver
description: Resolución de identidad, desambiguación de homónimos y verificación oficial de investigadoras e investigadores en el Padrón SNII 2025 de México (nivel, área, vigencia, ORCID y Scopus ID).
dependencies:
  - python: "/home/ambientesPy/revistaslatam"
  - script: "scripts/snii_resolver_cli.py"
---

# SNII Identity Resolver

Módulo de verificación y desambiguación canónica de investigadores contra el Padrón Oficial del Sistema Nacional de Investigadoras e Investigadores (SNII 2025).

## Overview
Diferencia a científicos homónimos, certifica su nivel de acreditación oficial (Candidato a Emérito), área temática de dictaminación (I a IX) y vincula sus identificadores persistentes (ORCID y OpenAlex Author ID) para respaldar diagnósticos cienciométricos nacionales.

## Dependencies
- Entorno Python: `/home/ambientesPy/revistaslatam`
- Script ejecutable: [`scripts/snii_resolver_cli.py`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/snii-identity-resolver/scripts/snii_resolver_cli.py)

## Scripts & CLI Tools

### Resolver Identidad (`resolve`)
Desambigua a un autor contra el padrón oficial:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/snii_resolver_cli.py resolve \
  --name "Rafael Torres Córdoba" \
  --institution "UNAM" \
  --output /ruta/a/identidad_torres.json
```

### Consultar Perfil SNII (`profile`)
Recupera el perfil institucional y métricas asociadas:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/snii_resolver_cli.py profile \
  --name "Torres Córdoba" \
  --output /ruta/a/perfil_snii.json
```

## Workflow Steps
1. **Identificar Autor:** Recibir nombre de autor proveniente de OpenAlex o de un corpus bibliográfico.
2. **Validar SNII:** Ejecutar `resolve` para confirmar si está acreditado en el padrón nacional y recuperar su nivel oficial.
3. **Paso a Enriquecimiento:** Conectar el ORCID resuelto con [`infotlachia-scholar-intelligence`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/infotlachia-scholar-intelligence/SKILL.md).

## References
- [Esquema del Padrón Oficial SNII](references/snii_padron_2025_schema.md)
- [Taxonomía de Áreas del Conocimiento CONAHCYT](references/conahcyt_areas_taxonomy.md)

## Troubleshooting & Edge Cases
- **Variaciones de Nombres:** El CLI normaliza acentos y evalúa sufijos institucionales para garantizar alta confianza en la desambiguación (`disambiguation_confidence >= 0.90`).
