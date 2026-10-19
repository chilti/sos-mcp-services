# Reglas de Permutación de Nombres Hispanos

En corpus internacionales como OpenAlex, los nombres hispanos sufren diversas transformaciones debido a la falta de estandarización entre los sistemas de indización:

1. **Apellidos Compuestos con Guion:**
   - Nombre original: `Rafael Torres Córdoba`
   - Formas comunes en revistas: `Rafael Torres-Córdoba`, `Torres-Córdoba, R.`, `Torres Córdoba, Rafael`.
2. **Inversión o Pérdida del Segundo Apellido:**
   - Frecuentemente el apellido materno se asume como primer apellido o se omite: `Torres, Rafael`, `Córdoba, Rafael Torres`.
3. **Múltiples Nombres de Pila:**
   - `José Luis Jiménez Andrade` $\to$ `Jiménez-Andrade, José Luis`, `Jiménez, José Luis`, `Jimenez Andrade, J. L.`.

El CLI `openalex_mexico_cli.py` genera estas combinaciones de forma automática para maximizar la exhaustividad de la recuperación en ClickHouse.
