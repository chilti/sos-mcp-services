# Modelo Económico de APC y Ahorro Diamante

El ecosistema TlachIA modela el flujo financiero de la publicación científica para contrastar el gasto transferido a editoriales comerciales oligopólicas frente a la infraestructura pública de Acceso Abierto Diamante.

---

## 1. Parámetros Financieros Base

- **Tarifa Base de APC:** Extraída directamente de la base de datos de OpenAlex (`apc_paid.value_usd`).
- **Costo de Oportunidad Diamante:** \$1,800 USD por publicación. Corresponde a la mediana ponderada de APC en revistas híbridas/gold de las principales editoriales (Elsevier, Springer-Nature, Wiley).

---

## 2. Indicadores Económicos Derivados

1. **Gasto Total Devengado:** $\sum \text{APC}_{\text{USD}}$.
2. **Gasto Medio por Documento:** $\frac{\sum \text{APC}_{\text{USD}}}{N_{\text{total}}}$.
3. **Retorno Social Institucional:** Ahorro acumulado que las universidades públicas retienen al sostener plataformas editoriales universitarias Diamante.
