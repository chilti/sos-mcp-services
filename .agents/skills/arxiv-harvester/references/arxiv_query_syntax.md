# arXiv API Query Syntax and Rules

The arXiv API (`https://export.arxiv.org/api/query`) supports Boolean queries and field prefixes.

---

## 1. Supported Field Prefixes

| Prefix | Description | Example |
|---|---|---|
| `ti` | Title | `ti:"neural network"` |
| `au` | Author | `au:LeCun` |
| `abs` | Abstract | `abs:"self-organizing maps"` |
| `cat` | Subject Category | `cat:cs.AI` |
| `all` | All fields | `all:"complex networks"` |
| `jr` | Journal reference | `jr:"Nature"` |

---

## 2. Mandatory Courtesy Rate Limit

The arXiv consortium formally requires automated clients to execute no more than **1 request every 3 seconds** (`time.sleep(3.0)`).
Violating this threshold triggers a temporary IP ban enforced by arXiv's load balancers.
