---
name: deep-literature-researcher
description: Deep search and systematic review of scientometric literature (5-phase framework of Zupic & Čater / Aria & Cuccurullo, PRIBA/PRISMA 2020, hybrid Boolean + 768d Nomic vector search, citation snowballing with Glänzel et al. core density filter, and hallucination-free evidence matrices). Respond and label outputs in the user's language.
metadata:
  python: ">=3.10"
  script: "scripts/citation_snowball.py"
---
# Deep Literature Researcher

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

Specialist in deep systematic reviews of scientific literature, evidence synthesis, and state-of-the-art mapping, integrating the methodological standards of **scientometrics and the Science of Science**: the 5-phase framework of **Zupic & Čater (2015)** and **Aria & Cuccurullo (2017)**, the **PRIBA** (Koo & Lin, 2022) / **PRISMA 2020** reporting guidelines, the **Citation Snowballing protocol (Wohlin, 2014)** enriched with the **Core Density Filter of Glänzel et al. (2009)**, and hybrid search architectures (symbolic Boolean + dense 768-dimensional semantic vector search).

---

## 1. Integrated Methodological Framework for Science Mapping and Synthesis

Unlike purely clinical biomedical protocols, deep reviews in scientometrics and computational science operate under the **5-Phase Workflow of Zupic & Čater (2015)** and **Aria & Cuccurullo (2017)**, audited via the adapted **PRIBA / PRISMA 2020** flow diagram:

```mermaid
flowchart TD
    subgraph Phase1 ["1. Study Design"]
        D1["Research Questions"] --> D2["Unit of Analysis (Docs, Authors, Concepts)"]
        D2 --> D3["Explicit Eligibility Criteria (IC / EC)"]
    end

    subgraph Phase2 ["2. Hybrid Collection & Delineation (Data Collection)"]
        D3 --> H1["Boolean Search (OpenAlex API / WoS / Scopus / Optional Local Snapshot)"]
        D3 --> H2["Semantic Vector Search (Optional 768d Local Embeddings)"]
        D3 --> H3["Snowballing with Glänzel Density Filter (k >= 2)"]
        H1 & H2 & H3 --> DUP["Deduplication & Unique Consolidation"]
    end

    subgraph Phase3 ["3. PRIBA Screening & Eligibility (Screening)"]
        DUP --> SCR["Title & Abstract Screening"]
        SCR -->|Grounded Exclusion| EXC["Excluded with Explicit Reason"]
        SCR -->|Approved| FULL["Full-Text Assessment"]
    end

    subgraph Phase4 ["4. Analysis & Structuring (Analysis & Mapping)"]
        FULL --> INC["Final Included Studies"]
        INC --> SYN["Evidence Extraction & Synthesis Matrix"]
        INC --> NET["Co-Citation & Bibliographic Coupling Networks"]
    end

    subgraph Phase5 ["5. Narrative Synthesis & Draft Generation"]
        SYN --> GAP["Detection of Consensuses, Controversies & Research Gaps"]
        GAP --> DRAFT["Extended Narrative Draft (literature_review_draft.md)"]
    end
```

### Explicit Eligibility Criteria (PCC / PICOS Framework)

Before initiating retrieval, the agent must formalize:

1. **Inclusion Criteria (IC):**
   - **IC1 (Domain/Concept):** Theoretical construct, formal model, or technology under analysis.
   - **IC2 (Methodological Approach):** Empirical studies, benchmarks, mathematical formalizations, or systematic reviews.
   - **IC3 (Time Window):** Relevant publication year range.
   - **IC4 (Document Typology):** Peer-reviewed journal articles, top-tier conference proceedings (*core conferences*), or reviews.
2. **Exclusion Criteria (EC):**
   - **EC1:** Works without an available abstract or without reproducible empirical/formal data.
   - **EC2:** Editorials, prefaces, non-peer-reviewed short letters, or popular science notes.
   - **EC3:** Works treating the concept solely as a tangential mention, metaphor, or incidental background.

---

## 2. Hybrid Retrieval Pipeline

To overcome the limitations of lexical silence (synonyms or terminological shifts) and the imprecision of pure latent vector spaces, a 3-tier hybrid pipeline is implemented:

$$
\text{Combined Score (RRF)}: \quad \text{RRF}(d) = \sum_{m \in \{\text{Boolean}, \text{Semantic}\}} \frac{1}{60 + r_m(d)}
$$

1. **Symbolic Tier (Boolean Recall):**
   - Built with [`bibliometric-search-strategist`](../bibliometric-search-strategist/SKILL.md) and executed against **OpenAlex API** (portable default), WoS, or Scopus —or against an optional local OpenAlex ClickHouse snapshot when configured (`CLICKHOUSE_HOST`).
2. **Dense Semantic Tier (768d Embeddings — Optional Local Accelerator):**
   - When available locally (Nomic Embed v1.5 / 768 dimensions via ClickHouse/LM Studio), identifies conceptually related publications expressed with divergent vocabulary.
3. **Reciprocal Rank Fusion (RRF, $k=60$):**
   - Combines both rankings, prioritizing documents at the intersection of both layers.

---

## 3. Snowballing Protocol with Core Density Filter (Glänzel et al., 2009)

Citation tracking across academic graphs maps theoretical roots and contemporary evolution (Wohlin, 2014). However, to prevent **topic drift**, the density criterion proposed by Wolfgang Glänzel is enforced:

$$
\text{Inclusion Criterion}: \quad d \in \text{Candidates} \iff |\text{Connections}(d, \text{Seeds})| \ge k
$$

```mermaid
flowchart LR
    subgraph Past ["Theoretical Roots"]
        B1["Common Reference A"]
        B2["Common Reference B"]
    end

    subgraph Seeds ["Seed Set (Golden Standard)"]
        S1["Seed 1 (CRL / Theoretical)"]
        S2["Seed 2 (Survey / LLM)"]
        S3["Seed 3 (Formal Benchmark)"]
    end

    subgraph Future ["Contemporary Active Fronts"]
        F1["Convergent Citing Work\n(Cites S1, S2, and S3)"]
        F2["Tangential Citing Work\n(Cites only S1 -> DISCARDED)"]
    end

    B1 & B2 <==|Backward Snowballing\n(Co-citation >= k)| S1 & S2 & S3
    S1 & S2 & S3 ==>|Forward Snowballing\n(Density >= k)| F1
    S1 -.->|Filter k < 2| F2
```

### Operational Rules

1. **Seed Core Selection:** Between 3 and 8 canonical landmark articles in the discipline.
2. **Backward Snowballing (Retrospective Tracking):**
   - Extract `referenced_works` from the seeds.
   - Identify works with recurrent co-citation (cited by 2 or more seeds simultaneously).
3. **Forward Snowballing (Prospective Tracking):**
   - Extract publications citing the primary seeds (`cited_by`).
   - Apply the **core density threshold** ($k \ge 2$): prioritize works that simultaneously connect to multiple seeds.
4. **Saturation Criterion:** Stop tracking when an additional snowballing round yields fewer than 5% new eligible articles.

---

## 4. Evidence Extraction and Synthesis Matrix

All extracted evidence must be structured in the **Canonical Synthesis Matrix**:

| Identifier (DOI) | Authors (Year)       | Approach / Theoretical Dimension | Methodology / Benchmark | Sample / Corpus ($N$) | Main Findings                                           | Stated Limitations & Author Future Work                       | Open Research Gap                              |
| ---------------- | -------------------- | -------------------------------- | ----------------------- | ----------------------- | ------------------------------------------------------- | ------------------------------------------------------------- | ---------------------------------------------- |
| `10.xxxx/...`  | Author et al. (2023) | Symbolic / Causal networks       | Synthetic SCMs          | 10,000 queries          | 94% accuracy on Rung 1; collapse on Rung 3 without SCM. | Everyday variable names; authors call for multi-step tool use. | Evaluate autonomous agents on abstract graphs. |

### Inviolable Anti-Hallucination Principle (Grounded Extraction)

- **Strict Rule:** If a datum (sample size, statistical metric, limitation, or author-proposed future work) is not explicitly stated in the retrieved metadata, abstract, or harvested full text, the agent must rigorously record `N/A` (Not Available in text/abstract).
- **Full-Text Prioritization:** When `--download-oa-pdfs` is enabled, the agent must inspect the layout-preserved text files in `<output>/text/` (including *Limitations*, *Discussion*, *Conclusion*, and *Future Work* sections) to extract exact empirical sample sizes ($N$), experimental conditions, stated limitations, and explicit author-signaled future directions before falling back to `N/A`.
- **Absolute Prohibition:** Never conjecture or fabricate unverified metrics, sample sizes, or conclusions.

---

## 5. Extended Narrative Literature Review Draft (`literature_review_draft.md`)

In addition to structured tables, the agent must synthesize the evidence into an **extensive, publication-grade narrative draft** saved as `literature_review_draft.md` in the output directory. This document is intentionally thorough and modular so it can serve both as a standalone State-of-the-Art working paper and as rich source material to be condensed later into the *Introduction*, *Theoretical Framework*, or *Related Work* section of a manuscript.

### Narrative Writing Standards

- **Thematic Synthesis Over Paper-by-Paper Summaries:** Organize prose around **conceptual themes, methodological families, and empirical debates**, comparing and contrasting multiple authors within each paragraph rather than listing disconnected one-paragraph study summaries or bullet lists.
- **Grounded Quantitative Depth:** Integrate exact sample sizes ($N$), benchmark metrics, effect directions, and methodological limitations directly verified from `<output>/text/`, `snowball_candidates.json`, and the Canonical Synthesis Matrix (enforcing `N/A` whenever a figure is absent).
- **1:1 OpenAlex Reference Fidelity:** Every in-text citation in the narrative draft must correspond 1:1 to a complete entry verified against `snowball_candidates.json` or OpenAlex (`https://api.openalex.org/works`) with exact authors, year, title, venue, and official DOI.

### Recommended Modular Structure

1. **Search Scope and Retrieval Traceability:** Concise methodological account summarizing Boolean/semantic queries, seed set, Glänzel density filtering ($k \ge 2$), PRIBA/PRISMA flow counts (`prisma_flow_data.json`), and full-text OA coverage.
2. **Intellectual Genealogy and Conceptual Evolution:** Narrative tracing how foundational landmark works gave rise to contemporary research lines.
3. **Thematic State-of-the-Art Synthesis (3–5 Core Subsections):** Deep, comparative academic prose analyzing competing approaches, architectures, datasets/benchmarks, and empirical findings across the reviewed literature.
4. **Community Consensuses, Controversies, and Cross-Cutting Limitations:**
   - **Community Consensus Points:** Findings independently validated across multiple groups.
   - **Methodological Controversies:** Open theoretical or empirical disagreements between schools of thought.
   - **Cross-Cutting Limitations:** Recurrent evaluation gaps, contamination risks, or scope restrictions.
5. **Future Directions: Author-Signaled Work vs. Agent-Assessed Unexplored Paths:** A dedicated analytical section that explicitly separates:
   - **Future Work Signaled by Original Authors:** Specific extensions, hypotheses, and pending experiments explicitly proposed by authors in the *Discussion*, *Conclusion*, or *Future Work* sections of the inspected papers (cited per paper from `<output>/text/` or abstracts, never attributed without textual evidence).
   - **Unexplored Paths Diagnosed by the Agent:** Untested methodological intersections, neglected baselines, scale/domain blind spots, and structural gaps identified across the corpus as a whole — explicitly labeled as cross-corpus analytical synthesis by the agent, with a brief rationale on scientific relevance, feasibility, and how they position a downstream manuscript or experimental agenda.
6. **Canonical Synthesis Table and Verified Reference List:** Embedded comparative evidence matrix plus complete OpenAlex-verified bibliography.

### Optional Formatted Export (`.docx` / `.pdf`)

When compiling a shareable review draft (or when requested by the user), convert `literature_review_draft.md` to Word (`.docx` via `pandoc`) and PDF (`.pdf` via `pandoc`/`xelatex` or LibreOffice headless) alongside the Markdown source.

---

## 6. Automated Tool: `scripts/citation_snowball.py`

Standalone CLI for backward/forward snowballing over global **OpenAlex API** (autonomous portable default), with optional local ClickHouse fast-path when `CLICKHOUSE_HOST` is set and optional automated Open Access full-text harvesting:

```bash
# Backward and forward snowballing with density filter over seeds
/home/ambientesPy/revistaslatam/bin/python \
  /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/deep-literature-researcher/scripts/citation_snowball.py \
  --seeds "10.1109/JPROC.2021.3058954" "10.48550/arxiv.2305.00050" "10.48550/arxiv.2306.05836" \
  --mode both \
  --top-citations 35 \
  --min-cocitations 1 \
  --output ./snowball_results/

# Advanced full-text pipeline: Snowballing + automated Open Access PDF acquisition
/home/ambientesPy/revistaslatam/bin/python \
  /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/deep-literature-researcher/scripts/citation_snowball.py \
  --seeds "10.1038/s41598-025-01676-x" "10.1111/bjet.13544" \
  --mode both \
  --top-citations 20 \
  --download-oa-pdfs \
  --fulltext-limit 10 \
  --extract-text \
  --output ./snowball_fulltext/ \
  --lang es
```

### Generated Outputs:

* `snowball_candidates.json`: Deduplicated candidates with metadata, seed connections, composite scores, and local full-text paths.
* `snowball_candidates.csv`: Exportable table for tabular screening with `OA Status`, `FullText Status`, and file paths.
* `prisma_flow_data.json`: Quantitative flow metrics for the PRIBA / PRISMA 2020 diagram, including Full-Text Eligibility counts.
* `snowball_report.md`: Report with Mermaid diagram, Top ranking of articles by centrality, and direct markdown links to local PDFs and texts.
* `pdf/`: (Optional, when `--download-oa-pdfs` is active) Harvested Open Access PDF documents.
* `text/`: (Optional, when `--extract-text` is active) Plain-text extractions for agent reading.

---

## 7. Bibliographic References

* Aria, M., & Cuccurullo, C. (2017). bibliometrix: An R-tool for comprehensive science mapping analysis. *Journal of Informetrics*, 11(4), 959–975. https://doi.org/10.1016/j.joi.2017.08.007
* Glänzel, W., Schlemmer, B., & Du Plessis, B. (2009). A hybrid approach for addressing the problem of "field delineation" in scientometric studies. *Scientometrics*, 79(1), 3–17. https://doi.org/10.1007/s11192-009-0401-7
* Koo, M., & Lin, S. C. (2022). Preferred reporting items for bibliometric analysis (PRIBA): A proposal for reporting bibliometric reviews. *Journal of Medical Sciences*, 42(3), 115–123.
* Page, M. J., McKenzie, J. E., Bossuyt, P. M., Boutron, I., Hoffmann, T. C., Mulrow, C. D., ... & Moher, D. (2021). The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. *BMJ*, 372, n71. https://doi.org/10.1136/bmj.n71
* Wohlin, C. (2014). Guidelines for snowballing in systematic literature studies and a replication in software engineering. In *Proceedings of the 18th International Conference on Evaluation and Assessment in Software Engineering* (EASE '14), Article 38, 1–10. https://doi.org/10.1145/2601248.2601268
* Zupic, I., & Čater, T. (2015). Bibliometric methods in management and organization. *Organizational Research Methods*, 18(3), 429–472. https://doi.org/10.1177/1094428114562629
