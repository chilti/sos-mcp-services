# Methodological Guide to Field Delineation in Scientometrics

Based on:
* Huang, C., Schiebel, E., & Porter, A. L. (2011). *A multi-stage approach to mapping emerging technologies: the case of DNA sequencing technology*. Scientometrics, 87(2), 241-260.
* Glänzel, W., Schlemmer, B., & Du Plessis, B. (2009). *A hybrid approach for addressing the problem of "field delineation" in scientometric studies*. Scientometrics, 79(1), 3-17.
* Zitt, M., & Bassecoulard, E. (2006). *Challenges for scientometric indicators: the data delimitation issue*. Scientometrics, 67(1), 145-160.

---

## 1. The Scientific Field Delineation Problem

In scientometrics, delineating the corpus of a research field (*Field Delineation*) is the most critical step of any bibliometric study. Flawed delineation produces:
* **False Silence (Low *Recall*):** Omitting key works that use alternative or metaphorical vocabulary, distorting networks and underestimating impact.
* **Massive Noise (Low *Precision*):** Including irrelevant literature due to polysemous terms, skewing collaboration metrics and thematic clusters.

---

## 2. The Three Canonical Delineation Approaches

```mermaid
flowchart TD
    subgraph Approach1 ["1. Modular Lexical Approach (Huang & Porter, 2011)"]
        L1["Core Terms (Core Search)"] --> L2["Related-Term Expansion"]
        L2 --> L3["Co-occurrence Noise Filtering"]
    end

    subgraph Approach2 ["2. Topological Citation Approach (Klavans & Boyack)"]
        C1["Canonical Seed Articles"] --> C2["Bibliographic Coupling / Co-citation"]
        C2 --> C3["Global Graph Partitioning (Leiden)"]
    end

    subgraph Approach3 ["3. Hybrid Causal-Lexical Approach (Glänzel et al., 2009)"]
        H1["Seed / Boolean Lexical Core"] --> H2["Citation Network Expansion (1st order)"]
        H2 --> H3["Core Density Filter (Cites >= k seeds)"]
    end
```

---

## 3. Huang, Schiebel & Porter (2011) Multi-Stage Protocol

Designed specifically for emerging or interdisciplinary domains, this protocol consists of 4 structured stages:

### Stage 1: High-Precision Core Definition (Core Search)
- Selection of strict, unambiguous, and undisputed terms that define the technology or theory (e.g., proprietary algorithm names, formalized equations, or exclusive lexical constructs).
- Objective: Guarantee near-100% precision, even if initial *recall* is moderate.

### Stage 2: Systematic Expansion (Modular Expansion)
- From the core corpus, analyze author keywords and classification schemes (OpenAlex Topics, MeSH Headings, WoS Categories).
- Incorporate technological variants, associated computational tools, and terminology from connected subfields via conceptual building blocks (`OR`).

### Stage 3: Noise Filtering and Exclusion (Noise Removal)
- Audit polysemous words that cause thematic contamination.
- **Scientometric rule:** Never use the `NOT` operator in isolation without evaluating whether it removes seminal literature. Instead, use:
  1. Unrelated subject category restrictions (`NOT WC="Surgery"` if the study is purely in computer science).
  2. Co-occurrence thresholds: an ambiguous term is admitted only if it co-occurs with at least one term from the conceptual core.

### Stage 4: Validation and Calibration
- Verify the retrieval rate of seminal works (*golden standard*).
- Manually inspect the top decile of most-cited publications to confirm they belong to the target domain.

---

## 4. Glänzel et al. (2009) Hybrid Causal-Lexical Approach

To solve the runaway expansion problem in citation tracking (*citation snowballing*):

$$\text{Hybrid Inclusion Criterion}: \quad d \in \text{Corpus} \iff d \in \text{Core}_{\text{lexical}} \quad \lor \quad |\text{Citations}(d, \text{Core}_{\text{lexical}})| \ge k$$

Where $k$ is the **core citation density threshold** (typically $k=2$ or $k=3$):
* If an external document was discovered by citing or being cited by a seed, **it is retained only if it connects simultaneously to at least $k$ documents in the initial core**.
* This acts as a topological barrier preventing the search from leaking into tangential disciplines.
