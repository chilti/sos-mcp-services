---
name: openalex-mexico-institutions
description: Consulta y mapeo del catálogo nacional de instituciones, universidades y centros de investigación de México sobre rag.institutions_seed_mexico, resolviendo identificadores ROR, acrónimos institucionales (UNAM, IPN, UAM, Cinvestav), estados y dependencias.
metadata:
  python: ">=3.10"
  script: "scripts/openalex_mexico_cli.py"
---

# OpenAlex México Institutions

Búsqueda, desambiguación y geolocalización de las instituciones y centros científicos de México en la tabla `rag.institutions_seed_mexico`.

## Overview

Facilita la identificación de universidades públicas y privadas, centros públicos de investigación CONAHCyT e institutos de salud, resolviendo sus códigos ROR oficiales, acrónimos conocidos y dependencias matriz.

## Dependencies

- **Entorno Python:** Python 3.10+ (`clickhouse-connect`)
- **Script CLI:** [`scripts/openalex_mexico_cli.py`](scripts/openalex_mexico_cli.py)
- **Tabla ClickHouse:** `rag.institutions_seed_mexico`

## CLI Interface

### 1. Búsqueda por Acrónimo
Localiza la institución y extrae su ROR canónico:
```bash
python scripts/openalex_mexico_cli.py get-institution \
  --acronym "UNAM" \
  --limit 5 \
  --output /ruta/a/unam_institucion.json
```

### 2. Búsqueda por Nombre o Texto Libre
```bash
python scripts/openalex_mexico_cli.py get-institution \
  --query "Instituto Politécnico Nacional" \
  --output /ruta/a/ipn_institucion.json
```

### 3. Filtrado por Entidad Federativa (Estado)
Recupera los centros de investigación de un estado determinado:
```bash
python scripts/openalex_mexico_cli.py get-institution \
  --state "Jalisco" \
  --limit 20 \
  --output /ruta/a/instituciones_jalisco.json
```

### 4. Consulta Directa por Identificador ROR
```bash
python scripts/openalex_mexico_cli.py get-institution \
  --ror "01tmp8f25" \
  --output /ruta/a/institucion_detalle.json
```

## Workflow de Vinculación

1. **Resolver Institución:** Usar `get-institution` para obtener el ROR unívoco (`https://ror.org/...`).
2. **Consultar Producción:** Alimentar dicho ROR en [`openalex-mexico-works-search`](../openalex-mexico-works-search/SKILL.md) para extraer todas las publicaciones de la universidad.
3. **Evaluar Indicadores:** Alimentar el ROR en [`openalex-mexico-aggregations`](../openalex-mexico-aggregations/SKILL.md) para calcular su cuota OA y gasto en APC.

## References

- [Catálogo de Principales Instituciones Mexicanas y Códigos ROR](references/institutions_mexico_catalog.md)

## Common Mistakes y Anti-Patrones (Evitar Errores Frecuentes)

- ❌ **Anti-patrón 1: Tratar campus específicos como instituciones no vinculadas**  
  Buscar el Tec de Monterrey o la UAM y tratar sedes o campus individuales como entidades aisladas sin considerar la institución matriz.  
  **Solución:** Consultar el campo `parent_name` y `parent_ror` para consolidar o desglosar la producción según el alcance del estudio.
- ❌ **Anti-patrón 2: Asumir que toda institución tiene acrónimo registrado**  
  Buscar solo por `--acronym "INSP"` en instituciones pequeñas o centros estatales que solo están registradas por nombre completo.  
  **Solución:** Si `--acronym` no arroja resultados, probar con `--query "Nombre Completo o Parcial"`.
- ❌ **Anti-patrón 3: Violación de File-Output First**  
  Omitir `--output`, provocando que el JSON de metadatos se imprima en stdout.  
  **Solución:** Guardar siempre en archivo (`--output ./data/institucion.json`).
