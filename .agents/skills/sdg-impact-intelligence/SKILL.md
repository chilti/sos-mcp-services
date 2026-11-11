---
name: sdg-impact-intelligence
description: Mapeo, alineamiento, cuantificación y visualización interactiva de la producción científica en los 17 Objetivos de Desarrollo Sostenible (ODS / SDG) de la Agenda 2030 de la ONU. Opera Workspace-First consumiendo directamente ./corpus.parquet.
entrypoint: scripts/sdg_impact_cli.py
inputs:
  type: object
  properties:
    workspace:
      type: string
      description: Directorio raíz del workspace donde reside corpus.parquet y se generarán los reportes (default '.').
    input:
      type: string
      description: Ruta explícita al archivo tabular de publicaciones (.parquet, .json, .csv).
    sdg_col:
      type: string
      description: Columna con metadatos de ODS (default auto-detecta 'sdgs', 'sdg_ids', 'ODS_ID').
    title:
      type: string
      description: Título del informe y dashboard HTML interactivo.
    output_html:
      type: string
      description: Ruta del visualizador HTML interactivo (default './reportes/sdg_impact_dashboard.html').
    output_json:
      type: string
      description: Ruta del resumen JSON estructurado (default './reportes/sdg_impact_summary.json').
    output_md:
      type: string
      description: Ruta del informe ejecutivo en Markdown (default './reportes/sdg_impact_report.md').
---

# SDG Impact Intelligence: Mapeo y Visualizador de los 17 ODS de la ONU

## 1. Propósito y Fundamentación Metodológica
Esta skill formaliza la evaluación cienciométrica de impacto social y sostenibilidad de la investigación científica, cuantificando la contribución temática del corpus a los **17 Objetivos de Desarrollo Sostenible (ODS) de las Naciones Unidas (Agenda 2030)**:
- **ODS 1 al 17:** Cobertura de las metas globales (Fin de la Pobreza, Salud y Bienestar, Educación de Calidad, Igualdad de Género, Industria e Innovación, Reducción de Desigualdades, Acción por el Clima, Paz y Justicia, etc.).
- **Métricas Cuantitativas y Normalizadas:** Para cada objetivo calcula el volumen absoluto de publicaciones ($N$), porcentaje sobre el total del corpus (%), citas acumuladas, **FWCI promedio ponderado** (impacto normalizado por campo), proporción de excelencia en el **Top 10%** y tasa de **Acceso Abierto Diamante**.

---

## 2. Principio Workspace-First ("De la Cosecha al ODS")
La skill consume de manera autónoma los datos previamente descargados por las skills de cosecha (`openalex-harvester`, `openalex_search`, `arxiv-harvester`, `scopus-harvester`, `pubmed-harvester`) depositados en el workspace:

```
<workspace>/
├── corpus.parquet                <-- Archivo tabular de entrada principal
└── reportes/
    ├── sdg_impact_summary.json   <-- Resumen estructurado JSON
    ├── sdg_impact_report.md      <-- Reporte analítico con tablas y artículos clave
    └── sdg_impact_dashboard.html <-- Visualizador interactivo oficial de los 17 ODS
```

---

## 3. Visualizador Interactivo de los 17 ODS (Estética SinapsisAI / KnoMap)
Integra el visualizador interactivo diseñado en el proyecto `sinapsisai` (`lib/viz_ods.py`):
- **Cuadrícula Responsiva de 17 Tarjetas:** Despliega las imágenes oficiales de la ONU con sus códigos cromáticos canónicos.
- **Identificación de Objetivos Activos vs. Inactivos:** Los ODS sin presencia en el corpus se muestran en escala de grises atenuada (`sdg-inactive`), activándose con color al pasar el cursor.
- **Overlay de Métricas:** Porcentaje del corpus y conteo de documentos superpuesto con gradiente legible.
- **Tooltips Informativos:** Nombre formal del ODS, conteo y porcentaje al hacer hover.
- **Tabla Detallada con Semáforos FWCI:** Resumen numérico con insignias de impacto normalizado por objetivo.

---

## 4. Uso desde la Línea de Comandos (CLI)

```bash
# Ejecución estándar sobre el workspace
/home/ambientesPy/revistaslatam/bin/python scripts/sdg_impact_cli.py \
  --workspace ./ \
  --title "Alineación ODS: Producción Científica en Inteligencia Artificial y Causalidad"

# Especificando archivo de entrada explícito
/home/ambientesPy/revistaslatam/bin/python scripts/sdg_impact_cli.py \
  --input ./data/mis_publicaciones.parquet \
  --workspace ./
```

---

## 5. Salidas Generadas en `./reportes/`

1. **`sdg_impact_dashboard.html`:** Tablero interactivo autónomo (sin dependencias externas pesadas) listo para abrirse en cualquier navegador.
2. **`sdg_impact_summary.json`:** Diccionario estructurado con las estadísticas por ODS (1 a 17) para consumo por otras skills, agentes o LLMs.
3. **`sdg_impact_report.md`:** Tabla en Markdown formateada para inclusión directa en manuscritos IMRyD, reportes institucionales o Policy Briefs.
