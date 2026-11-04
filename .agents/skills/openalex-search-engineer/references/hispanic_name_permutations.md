# Permutaciones y Desambiguación de Nombres Hispanos

En bases de datos anglosajonas (Scopus, WoS, OpenAlex), los nombres iberoamericanos sufren inconsistencias sistemáticas en la indexación de los dos apellidos (paterno y materno) y nombres compuestos.

---

## 1. Patrones de Variación Comunes

Para un autor llamado `Rafael Torres Córdoba`:

1. **Forma Directa:** `Rafael Torres Córdoba`
2. **Forma Invertida con Coma:** `Torres Córdoba, Rafael`
3. **Forma con Guion (Unificación Anglosajona):** `Rafael Torres-Córdoba`
4. **Forma Invertida con Guion:** `Torres-Córdoba, Rafael`
5. **Omisión del Apellido Materno:** `Torres, Rafael` o `Rafael Torres`
6. **Abreviatura de Nombres Compuestos:** `Torres-Córdoba, R.` o `Torres, R.`

---

## 2. Estrategia del CLI

El subcomando `search-authors` genera automáticamente estas permutaciones sintácticas y las consulta secuencialmente en ClickHouse mediante `positionCaseInsensitiveUTF8`, fusionando los resultados por ID unívoco para no perder publicaciones indexadas bajo distintas variantes.
