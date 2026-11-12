# Hispanic Name Permutation Rules

In international corpora such as OpenAlex, Hispanic names undergo various transformations due to the lack of standardization across indexing systems:

1. **Hyphenated Compound Surnames:**
   - Original name: `Rafael Torres Córdoba`
   - Common forms in journals: `Rafael Torres-Córdoba`, `Torres-Córdoba, R.`, `Torres Córdoba, Rafael`.
2. **Inversion or Omission of the Second Surname:**
   - Frequently, the maternal surname is assumed to be the primary surname or is omitted: `Torres, Rafael`, `Córdoba, Rafael Torres`.
3. **Multiple Given Names:**
   - `José Luis Jiménez Andrade` $\to$ `Jiménez-Andrade, José Luis`, `Jiménez, José Luis`, `Jimenez Andrade, J. L.`.

The `openalex_mexico_cli.py` CLI automatically generates these combinations to maximize recall in ClickHouse.
