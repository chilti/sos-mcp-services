---
name: revistaslatam-indicators-engine
description: Motor analítico para evaluación editorial de revistas científicas iberoamericanas, cálculo de endogamia institucional, balance multilingüe y auditoría de los 38 criterios del Catálogo 2.0 de Latindex.
---

# Revistas Latam Indicators Engine

Motor analítico autónomo e independiente para diagnosticar la salud editorial, visibilidad cienciométrica y cumplimiento normativo de revistas científicas iberoamericanas a partir de datos tabulares canónicos o manifiestos de metadatos, sin requerir la interfaz web de Revistas Latam.

---

## Capacidades

- **Perfil Cienciométrico de Revista:** Conteo de citas, citas por documento, índice H, índice G de Egghe, cociente m de Hirsch y Price Index de obsolescencia.
- **Tasa de Endogamia Editorial Institucional:** Cuantifica la proporción de autores pertenecientes a la institución editora frente a autores externos nacionales e internacionales, comparándolos con los umbrales de Latindex, SciELO y Redalyc.
- **Balance Multilingüe:** Proporción de artículos en Español, Portugués e Inglés con cálculo de la entropía de diversidad de Shannon.
- **Auditoría Catálogo 2.0 de Latindex:** Checklist automatizado de los 8 criterios básicos obligatorios y criterios adicionales de calidad digital.

---

## Interfaz CLI

Entorno de ejecución:
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/revistaslatam-indicators-engine/scripts/revistaslatam_indicators_cli.py [subcomando] [opciones]
```

### 1. Perfil cienciométrico de una revista
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/revistaslatam-indicators-engine/scripts/revistaslatam_indicators_cli.py journal-profile \
  --corpus ./articulos_revista.parquet \
  --journal-name "Revista Mexicana de Sociología" \
  --output ./perfil_revista.md
```

### 2. Medición de endogamia editorial institucional
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/revistaslatam-indicators-engine/scripts/revistaslatam_indicators_cli.py editorial-endogamy \
  --corpus ./articulos_revista.parquet \
  --host-institution "Universidad Nacional Autónoma de México" \
  --host-country "MX" \
  --output ./endogamia_reporte.json
```

### 3. Distribución lingüística de artículos
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/revistaslatam-indicators-engine/scripts/revistaslatam_indicators_cli.py multilingual-balance \
  --corpus ./articulos_revista.parquet \
  --output ./balance_idiomas.json
```

### 4. Auditoría de criterios de Latindex Catálogo 2.0
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/revistaslatam-indicators-engine/scripts/revistaslatam_indicators_cli.py latindex-audit \
  --metadata ./revista_metadata.json \
  --output ./auditoria_latindex.json
```

---

## Referencias Técnicas
- [Estándares Internacionales de Endogamia Editorial](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/revistaslatam-indicators-engine/references/editorial_endogamy_standards.md)
- [Manual de Auditoría del Catálogo 2.0 de Latindex](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/revistaslatam-indicators-engine/references/latindex_catalogo_2_audit_manual.md)
