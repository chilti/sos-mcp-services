# OpenAlex Cursor Pagination Guide

Cursor pagination is the canonical and fastest mechanism for traversing millions of records without incurring memory or offset penalties (`offset`).

---

## 1. Cursor Algorithm Workflow

```mermaid
sequenceDiagram
    autonumber
    participant CLI as openalex_harvest_cli.py
    participant API as OpenAlex API /works
    CLI->>API: GET /works?filter=...&per-page=100&cursor=*
    API-->>CLI: 200 OK (100 works, meta.next_cursor = "cD0yMDIw...")
    CLI->>API: GET /works?filter=...&per-page=100&cursor=cD0yMDIw...
    API-->>CLI: 200 OK (100 works, meta.next_cursor = "cD0yMDI0...")
    Note over CLI,API: Repeat until the target limit is reached or next_cursor = null
```

---

## 2. Advantages over Numeric Page Pagination (`page=N`)

1. **O(1) performance on every hop:** The database does not scan the preceding $N \times 100$ records.
2. **Data consistency:** Records inserted or updated in real time do not shift or duplicate items across pages.
3. **Scalability:** Enables extracting 10,000+ articles in minutes with complete stability.
