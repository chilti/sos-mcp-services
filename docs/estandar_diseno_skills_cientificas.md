# Estándar Canónico de Diseño y Calidad para Skills Científicas y Analíticas
## Ecosistema UNAM (KnoMap · TlachIA-Hands · RevistasLATAM · sos-mcp-services)
**Inspirado y alineado con Google DeepMind (`workflow-skill-creator`) y Antigravity Customizations (`agy-customizations`)**

---

## 1. Justificación y Propósito

El ecosistema analítico de la UNAM combina bases de datos columnares masivas (ClickHouse con >500M de registros), motores neurocomputacionales de reducción dimensional (Kohonen SOM, UMAP, MLE) y pipelines cienciométricos longitudinales. 

Para que los agentes de IA (Antigravity IDE, TlachIA-Hands, OpenHands) operen con máxima precisión, determinismo y eficiencia de contexto, **todas las skills del repositorio `.agents/skills/` deben satisfacer rigurosamente este estándar de diseño**.

Este documento condensa las mejores prácticas identificadas en la skill de referencia de Google DeepMind (`workflow-skill-creator`) adaptadas a la infraestructura científica y servidores de la UNAM.

---

## 2. Los 7 Principios Canónicos de Implementación

### Regla 1: Principio *File-Output First* (Ahorro Estricto de Contexto)
> **Principio:** Los scripts CLI y las herramientas MCP **NUNCA** deben volcar payloads masivos a `stdout` o al contexto del chat del LLM.

* **El Problema:** Volcar miles de líneas de JSON o tablas de texto satura rápidamente la ventana de contexto del LLM, provoca truncamientos indeseados y eleva innecesariamente el consumo de tokens.
* **La Solución:** Toda operación de extracción, agregación, modelado o visualización **debe escribir su resultado en disco** (`.json`, `.parquet`, `.csv`, `.html`) en una ruta de sesión o directorio de artefactos (`scratch/` o `brain/`).
* **Salida de Terminal:** La salida a terminal o el retorno MCP debe limitarse a un objeto ligero con:
  1. Estado (`status: "success"`).
  2. Dimensiones y conteos clave (`matrix_shape: [50, 10]`, `total_entities: 50`).
  3. Ruta del archivo generado (`output_file: "/ruta/a/resultado.json"`).
  4. Resumen ejecutivo conciso en lenguaje natural (2–4 líneas).

---

### Regla 2: Sección Canónica `## Dependencies` (Reutilización y Cadena de Valor)
> **Principio:** No reimplementar lo que otra skill ya resuelve. Toda skill debe declarar explícitamente qué habilidades la preceden (upstream) y cuáles la suceden (downstream).

En el archivo `SKILL.md`, incluir obligatoriamente la sección `## Dependencies` indicando:
* **Habilidades Previas:** Qué skill proporciona los datos de entrada limpios (ej. `scientometrics-incites-expert` o `tlachia-metrics-handler`).
* **Habilidades Complementarias:** Qué herramientas orquestan el cálculo de fondo (ej. `som-methodological-expert` para la calibración espectral SVD).
* **Entorno y Recursos:** Entorno Python requerido (`/home/ambientesPy/revistaslatam`) y herramientas MCP invocables.

---

### Regla 3: Sección Canónica `## Common Mistakes` (Anti-Patrones y Trampas Frecuentes)
> **Principio:** Los LLMs tienden a repetir errores sutiles de dominio salvo que se les advierta explícitamente de ellos.

Cada `SKILL.md` debe incluir una sección `## Common Mistakes` documentando entre 3 y 5 fallas frecuentes, tales como:
* Errores de formato (ej. saltar cabeceras de metadatos en CSVs de InCites).
* Violaciones de arquitectura (ej. formular `JOIN`s en ClickHouse en lugar de funciones de arrays).
* Errores metodológicos (ej. conectar puntos anuales con rectas en lugar de splines continuas; promediar sin ponderar ratios de impacto).
* Sobrecarga visual (ej. mapear más de 5 entidades simultáneas en trayectorias o dibujar etiquetas sin umbral de legibilidad).

---

### Regla 4: Argumentos Explícitos y Ausencia de Defaults Silenciosos
> **Principio:** El agente debe ser consciente de cuándo está trabajando sobre una muestra y cuándo sobre el universo total.

* Parámetros como `--limit`, `--min-documents`, `--window` o `--threshold` **no deben recortar datos en silencio sin que el agente o el usuario lo sepan**.
* Si un comando CLI aplica un límite, este debe especificarse como argumento explícito (ej. `--limit 100`) o retornar en el reporte: `"limit_applied": 100`, `"total_available_entities": 1540`.
* Esto previene que el agente afirme que "procesó todas las instituciones de México" cuando en realidad sólo leyó las primeras 50 de una tabla truncada.

---

### Regla 5: Patrón CLI con Subcomandos (`argparse` / `uv run`)
> **Principio:** Toda habilidad que involucre cómputo, consulta a base de datos, parsing de archivos o generación de visualizaciones requiere código ejecutable.

* Alojar los scripts auxiliares en `scripts/<skill_name>_cli.py` o en `shared_scripts/`.
* Estructurar mediante subcomandos de `argparse` claros y verbos de acción: `inspect`, `extract`, `train`, `visualize`, `evaluate`.
* Todos los subcomandos deben aceptar `--output` obligatorio.
* Usar `json.dump(..., indent=2)` para guardar archivos estructurados legibles.

---

### Regla 6: Resiliencia, Diagnóstico Detallado y Autocorrección
> **Principio:** Si una operación falla, el mensaje de error debe contener información accionable para que el agente pueda autocorregirse de inmediato.

* Nunca retornar únicamente un código opaco (`Error 400` o `Fallo en consulta`).
* Incluir el fragmento de la consulta causante del error, la sugerencia de corrección y el contexto relevante (ej. *"Violación de política: la consulta contiene JOIN. Utilice arrayExists(...) sobre la columna 'author_names'"*).
* En peticiones HTTP o conexiones a ClickHouse, utilizar `time.monotonic()` y reintentos con retroceso exponencial (*exponential backoff*) ante desconexiones transitorias.

---

### Regla 7: Divulgación Progresiva (*Progressive Disclosure*)
> **Principio:** El archivo `SKILL.md` debe ser una hoja de ruta concisa y accionable, no una enciclopedia ilegible.

* Mantener el `SKILL.md` entre 150 y 350 líneas bien organizadas.
* Desacoplar diccionarios de variables, tablas de 250 categorías WoS, demostraciones matemáticas o esquemas DDL exhaustivos en subdirectorios `references/*.md`.
* Vincular estos recursos mediante enlaces markdown clickeables con formato `file:///...`.

---

## 3. Plantilla Canónica de `SKILL.md`

Todo nuevo archivo `SKILL.md` o archivo actualizado debe ceñirse a la siguiente estructura:

```markdown
---
name: {identificador-en-kebab-case}
description: >-
  {Descripción concisa en tercera persona (máximo 1024 caracteres).
   Explica con precisión QUÉ HACE la skill y CUÁNDO debe activarse.}
metadata:
  python: "/home/ambientesPy/revistaslatam" # o ruta de entorno
  tools: ["servicio_mcp_asociado"]
---

# {Título de la Habilidad}

## 1. Overview y Propósito
{Descripción general del dominio, marco metodológico y objetivo del flujo.}

## 2. Dependencies y Cadena de Valor
- **Habilidades Upstream:** `{skill-origen}` -> {Motivo de dependencia}
- **Habilidades Downstream:** `{skill-destino}` -> {Siguiente fase en el pipeline}
- **Herramientas de Software:** {Rutas a scripts CLI o herramientas MCP}

## 3. Protocolo de Ejecución Paso a Paso
{Instrucciones claras, comandos CLI con `--output` o llamadas a funciones MCP.}

### 3.1 Subcomando A (`extract`)
```bash
python scripts/{script_name}.py extract \
  --input /ruta/datos.csv \
  --output /ruta/matriz_procesada.json \
  --limit 100
```

### 3.2 Subcomando B (`analyze`)
...

## 4. Batería de Indicadores / Especificación de Datos
{Tablas de variables, fórmulas matemáticas, campos columnares o unidades analíticas.}

## 5. Common Mistakes y Anti-Patrones (Evitar Errores Frecuentes)
- ❌ **Anti-patrón 1:** {Descripción del error}.  
  **Solución:** {Cómo hacerlo correctamente}.
- ❌ **Anti-patrón 2:** {Descripción del error}.  
  **Solución:** {Cómo hacerlo correctamente}.
- ❌ **Anti-patrón 3:** {Descripción del error}.  
  **Solución:** {Cómo hacerlo correctamente}.

## 6. Referencias Técnicas y Metodológicas
- [{Documento de Referencia}](file:///ruta/a/referencia.md)
- [{Script Principal}](file:///ruta/a/script.py)
```

---

## 4. Matriz de Aplicación Inmediata en el Repositorio

| Skill | Áreas Clave de Enriquecimiento según este Estándar |
| :--- | :--- |
| **`scientometrics-incites-expert`** | Incorporar `## Dependencies` (hacia SOM y PathSOM) y `## Common Mistakes` (cabeceras Clarivate, agregación de tópicos, encoding UTF-16). |
| **`som-methodological-expert`** | Incorporar `## Dependencies` y `## Common Mistakes` (topología hexagonal vs cuadrada, sobremalla 20N, normalización z-score). |
| **`som-trajectory-mapping`** | Incorporar `## Dependencies` y `## Common Mistakes` (límite de 5 entidades, splines continuas vs rectas, saturación de etiquetas). |
| **`neural-longitudinal-mapping`** | Incorporar `## Dependencies` y `## Common Mistakes` (Warm-Start 1/10 épocas vs reentrenamiento PCA, deriva sináptica $\Delta W$). |
| **`openalex-mexico-clickhouse`** | Crear `SKILL.md` unificado raíz del paquete con catálogo de los 7 módulos, regla CERO JOINs y `## Common Mistakes`. |

---

*Directrices aprobadas para su observancia general en todas las skills analíticas de sos-mcp-services y TlachIA-Hands.*
