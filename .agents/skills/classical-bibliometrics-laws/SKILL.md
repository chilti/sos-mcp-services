---
name: classical-bibliometrics-laws
description: Modelado matemático y validación empírica de leyes bibliométricas clásicas (Ley de Lotka con conteo full/frac y prueba KS, Ley de Bradford con formulación continua de Egghe, Índice de Price de obsolescencia y ajuste de curvas de crecimiento exponencial vs logístico).
dependencies:
  - python: "/home/ambientesPy/revistaslatam"
  - script: "scripts/bibliometric_laws_cli.py"
---

# Classical Bibliometrics Laws

Módulo cuantitativo especializado en modelar distribuciones bibliométricas clásicas, dispersión de literatura, tasas de obsolescencia citacional y fases de madurez científica.

## Overview
Las leyes clásicas de la cienciometría permiten determinar si una disciplina se comporta como una ciencia consolidada, detectar el núcleo de revistas esenciales (*Core Journals*), cuantificar la vida media de citas y predecir la saturación de un campo de investigación.

## Dependencies
- Entorno Python: `/home/ambientesPy/revistaslatam`
- Paquetes clave: `numpy`, `scipy`, `matplotlib`
- Script ejecutable: [`scripts/bibliometric_laws_cli.py`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/classical-bibliometrics-laws/scripts/bibliometric_laws_cli.py)

## Scripts & CLI Tools

### Ley de Lotka (`lotka`)
Ajusta la distribución de productividad de autores y evalúa la bondad de ajuste con Kolmogorov-Smirnov:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/bibliometric_laws_cli.py lotka \
  --input /ruta/al/corpus.parquet \
  --counting full \
  --plot-output /ruta/al/grafico_lotka.png \
  --output /ruta/a/resultado_lotka.json
```
Opciones:
- `--counting`: `full` (1 crédito por coautor, estándar) o `fractional` ($1/k$).
- `--plot-output`: Ruta opcional para guardar el gráfico log-log en PNG.

### Ley de Bradford (`bradford`)
Divide las fuentes en 3 zonas de igual producción aplicando la formulación continua de Egghe:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/bibliometric_laws_cli.py bradford \
  --input /ruta/al/corpus.parquet \
  --output /ruta/a/zonas_bradford.json
```

### Índice de Price y Obsolescencia (`price-index`)
Calcula el porcentaje de referencias con $\le 5$ años de antigüedad y la vida media de citación:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/bibliometric_laws_cli.py price-index \
  --input /ruta/al/corpus.parquet \
  --output /ruta/a/indice_price.json
```

### Fases de Crecimiento de la Ciencia (`growth-phase`)
Compara el ajuste Exponencial vs Logístico para diagnosticar la fase de madurez:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/bibliometric_laws_cli.py growth-phase \
  --input /ruta/al/corpus.parquet \
  --plot-output /ruta/al/grafico_crecimiento.png \
  --output /ruta/a/diagnostico_fase.json
```

## Workflow Steps
1. **Evaluar Productividad:** Ejecutar `lotka` para verificar la concentración de autorías.
2. **Identificar Núcleo de Revistas:** Ejecutar `bradford` para extraer las revistas del Core.
3. **Medir Envejecimiento:** Ejecutar `price-index` para caracterizar la velocidad de recambio teórico.
4. **Determinar Fase:** Ejecutar `growth-phase` para conocer si el campo se encuentra en expansión activa o saturación.

## References
- [Fundamentos Matemáticos de Leyes Clásicas](references/classical_laws_mathematical_foundations.md)
- [Formulación Continua de Bradford (Egghe)](references/egghe_continuous_bradford.md)

## Troubleshooting & Edge Cases
- **Baja Variación en Años:** El comando `growth-phase` requiere al menos 4 años distintos con publicaciones para converger en el ajuste no lineal de la curva logística.
- **Referencias sin Año Explícito:** Expresiones regulares analizan los 4 dígitos cronológicos de las referencias (`19xx`/`20xx`); las referencias no fechadas se descartan del cálculo del índice de Price sin romper el pipeline.
