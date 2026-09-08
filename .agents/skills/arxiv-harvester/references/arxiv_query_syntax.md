# Sintaxis de Consultas y Reglas de la API de arXiv

La API de arXiv (`https://export.arxiv.org/api/query`) admite consultas booleanas y prefijos de campo.

---

## 1. Prefijos de Campo Admitidos

| Prefijo | Descripción | Ejemplo |
|---|---|---|
| `ti` | Título | `ti:"neural network"` |
| `au` | Autor | `au:LeCun` |
| `abs` | Resumen | `abs:"self-organizing maps"` |
| `cat` | Categoría temática | `cat:cs.AI` |
| `all` | Todos los campos | `all:"complex networks"` |
| `jr` | Referencia de revista | `jr:"Nature"` |

---

## 2. Regla de Cortesía Obligatoria

El consorcio de arXiv exige formalmente que los clientes automatizados no ejecuten más de **1 solicitud cada 3 segundos** (`time.sleep(3.0)`).
Violar este umbral provoca el bloqueo temporal de la dirección IP de origen por parte de los balanceadores de carga de arXiv.
