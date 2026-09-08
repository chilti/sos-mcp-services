---
name: geopolitical-collaboration-analyst
description: Análisis de cartografía geopolítica de la ciencia, matrices de coautoría internacional (ISO-3166-1 alpha-3), similitud bilateral de Salton, análisis por bloques regionales (Iberoamérica, Sur Global, OCDE, BRICS) y tasa de liderazgo científico.
dependencies:
  - python: "/home/ambientesPy/revistaslatam"
  - script: "scripts/geopolitical_collab_cli.py"
---

# Geopolitical Collaboration Analyst

Módulo cuantitativo de cartografía geopolítica de la ciencia y diplomacia científica internacional para analizar redes de cooperación entre países y evaluar la asimetría de liderazgo epistemológico.

## Overview
Desacoplado de los análisis de Acceso Abierto y ODS, este módulo se enfoca con precisión en los flujos internacionales de coautoría, aplicando normalización de países con ISO-3166-1 alpha-3, Coseno de Salton bilateral y cálculo de soberanía investigativa mediante el porcentaje de primeros autores nacionales.

## Dependencies
- Entorno Python: `/home/ambientesPy/revistaslatam`
- Script ejecutable: [`scripts/geopolitical_collab_cli.py`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/geopolitical-collaboration-analyst/scripts/geopolitical_collab_cli.py)

## Scripts & CLI Tools

### Matriz País-País (`country-matrix`)
Genera la red de colaboración internacional y similitud de Salton respecto a un país ancla:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/geopolitical_collab_cli.py country-matrix \
  --input /ruta/al/corpus.parquet \
  --anchor-country MEX \
  --top-n 25 \
  --output /ruta/a/matriz_paises_mexico.json
```

### Benchmarking Regional (`regional-benchmark`)
Calcula la cuota de colaboración capturada por bloques geopolíticos clave:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/geopolitical_collab_cli.py regional-benchmark \
  --matrix-file /ruta/a/matriz_paises_mexico.json \
  --region Iberoamerica \
  --anchor-country MEX \
  --output /ruta/a/benchmark_iberoamerica.json
```
Opciones de región: `Iberoamerica`, `GlobalSouth`, `OECD`, `BRICS`.

### Tasa de Liderazgo Científico (`scientific-leadership`)
Mide la soberanía evaluando si el primer autor pertenece a la institución nacional:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/geopolitical_collab_cli.py scientific-leadership \
  --input /ruta/al/corpus.parquet \
  --country MEX \
  --output /ruta/a/liderazgo_mexico.json
```

## Workflow Steps
1. **Calcular Matriz:** Ejecutar `country-matrix` con el país ancla.
2. **Segmentar por Bloques:** Ejecutar `regional-benchmark` para comparar la intensidad con Iberoamérica vs OCDE.
3. **Evaluar Soberanía:** Ejecutar `scientific-leadership` para verificar el balance de dirección en las colaboraciones.

## References
- [Diccionario ISO-3166-1 Alpha-3](references/iso_3166_alpha3_dictionary.md)
- [Métricas de Liderazgo y Asimetría Norte-Sur](references/scientific_leadership_metrics.md)

## Troubleshooting & Edge Cases
- **Múltiples Afiliaciones por Autor:** Si un autor reporta afiliaciones en más de un país, ambos países se acreditan en la coautoría bilateral.
- **Normalización de Nombres Históricos:** El diccionario resuelve automáticamente variaciones de nombres comunes (`UK`/`England` $\to$ `GBR`, `USA`/`United States` $\to$ `USA`).
