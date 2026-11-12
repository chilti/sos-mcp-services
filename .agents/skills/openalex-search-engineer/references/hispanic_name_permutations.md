# Hispanic Name Permutations and Disambiguation

In Anglo-Saxon bibliographic databases (Scopus, WoS, OpenAlex), Ibero-American names suffer from systematic indexing inconsistencies across dual surnames (paternal and maternal) and compound given names.

---

## 1. Common Variation Patterns

For an author named `Rafael Torres Córdoba`:

1. **Direct Form:** `Rafael Torres Córdoba`
2. **Inverted Form with Comma:** `Torres Córdoba, Rafael`
3. **Hyphenated Form (Anglo-Saxon Unification):** `Rafael Torres-Córdoba`
4. **Inverted Hyphenated Form:** `Torres-Córdoba, Rafael`
5. **Omission of Maternal Surname:** `Torres, Rafael` or `Rafael Torres`
6. **Abbreviation of Compound Given Names:** `Torres-Córdoba, R.` or `Torres, R.`

---

## 2. CLI Strategy

The `search-authors` subcommand automatically generates these syntactic permutations and queries them sequentially in ClickHouse using `positionCaseInsensitiveUTF8`, merging results by unique ID so that publications indexed under different name variants are never lost.
