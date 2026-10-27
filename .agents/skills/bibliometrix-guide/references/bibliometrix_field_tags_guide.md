# Diccionario de Etiquetas de Campo Canónicas en `bibliometrix`

Al cargar y convertir cualquier conjunto de datos bibliográficos con `convert2df()`, `bibliometrix` normaliza todas las columnas a un conjunto estándar de etiquetas de dos letras heredadas del formato clásico de Web of Science / ISI.

---

## 1. Tabla de Correspondencia de Etiquetas Principales

| Etiqueta | Nombre del Campo | Descripción y Uso | Formato habitual |
|:---:|:---|:---|:---|
| **`AU`** | Authors | Lista de autores del documento | `Apellido, N.; Apellido, N.M.` |
| **`AF`** | Author Full Names | Nombres completos de autores | `Apellido, Nombre Segundo` |
| **`TI`** | Document Title | Título del artículo o capítulo | Texto en inglés o idioma original |
| **`SO`** | Publication Source | Título de la revista, congreso o libro | Nombre estándar de la fuente |
| **`PY`** | Publication Year | Año de publicación | Entero de 4 dígitos (ej. `2024`) |
| **`DE`** | Author Keywords | Palabras clave asignadas por los autores | Separadas por punto y coma `;` |
| **`ID`** | Keywords Plus | Palabras clave generadas algorítmicamente por WoS/Scopus | Términos derivados de títulos citados |
| **`AB`** | Abstract | Resumen o abstract del documento | Texto libre estructurado |
| **`C1`** | Author Affiliations | Direcciones y afiliaciones institucionales de autores | Formato institucional con país |
| **`RP`** | Reprint Address | Dirección del autor de correspondencia | Afiliación y correo de contacto |
| **`CR`** | Cited References | Lista exhaustiva de referencias bibliográficas citadas | `Autor, Año, Revista, V, P, DOI` |
| **`TC`** | Times Cited | Citas globales recibidas en la base | Entero $\ge 0$ |
| **`UT`** | Unique Identifier | Identificador único del registro (WOS ID, Scopus EID, DOI) | Alfanumérico |
| **`DI`** | Digital Object Identifier | DOI del trabajo | `10.xxxx/...` |
| **`DT`** | Document Type | Tipo de documento (`Article`, `Review`, `Editorial`, etc.) | Cadena normalizada |
| **`LA`** | Language | Idioma del texto completo (`English`, `Spanish`, etc.) | Nombre del idioma |

---

## 2. Diferencia Crítica: `DE` (Author Keywords) vs. `ID` (Keywords Plus)

* **`DE` (Author Keywords):** Términos elegidos conscientemente por los autores para indexar su trabajo. Reflejan el **vocabulario nativo del frente de investigación**. Es el campo recomendado para `thematicMap(field = "DE")`.
* **`ID` (Keywords Plus):** Términos extraídos automáticamente por algoritmos de indexación de Clarivate a partir de los títulos de los artículos que aparecen en la bibliografía citada (`CR`). Tienden a ser más generales y frecuentes, pero pueden introducir ruido conceptual en mapas temáticos de nicho.

---

## 3. Estructura del Campo de Referencias Citadas (`CR`)

El campo `CR` es el insumo indispensable para:
1. **Co-citación (`analysis = "co-citation"`):** Dos documentos citados conjuntamente por un tercero.
2. **Acoplamiento Bibliográfico (`analysis = "coupling"`):** Dos documentos que comparten referencias en su bibliografía.
3. **Índice de Price y Vida Media:** Cálculo de la edad de las referencias.

Cada registro en `CR` se formatea típicamente como una lista separada por punto y coma `;`:
```text
SMITH J, 2020, SCIENTOMETRICS, V125, P450, DOI 10.1007/s11192-020-03650-1;
GARCIA A, 2018, J INFORMETR, V12, P110, DOI 10.1016/j.joi.2017.12.002
```

---

## 4. Fuentes de Datos Soportadas en `convert2df()`

| Base de Datos | Formato de Exportación Recomendado | Argumento `dbsource` | Argumento `format` |
|:---|:---|:---:|:---:|
| **Scopus** | CSV o BibTeX | `"scopus"` | `"csv"` o `"bibtex"` |
| **Web of Science** | Plain Text o BibTeX (Full Record and Cited References) | `"wos"` | `"plaintext"` o `"bibtex"` |
| **PubMed** | Formato de texto nativo PubMed / MEDLINE | `"pubmed"` | `"pubmed"` |
| **Dimensions** | Archivo CSV exportado desde la plataforma Dimensions | `"dimensions"` | `"csv"` |
| **Cochrane Library** | Plain text export | `"cochrane"` | `"plaintext"` |
| **OpenAlex** | JSON exportado vía API o ClickHouse | `"openalex"` | `"json"` (bibliometrix $\ge 4.2$) |
