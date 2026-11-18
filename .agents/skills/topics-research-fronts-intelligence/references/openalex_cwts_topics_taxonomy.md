# Canonical OpenAlex Topics Taxonomy and CWTS Leiden Methodology

### *Multi-Level Hierarchical Structure, OpenAlex API & Optional ClickHouse Mapping, and Query Rules*

---

## 1. Origin and CWTS Leiden Methodology

In January 2024, **OpenAlex** replaced its legacy "Concepts" system (inherited from Microsoft Academic Graph) with an open, hierarchical, and reproducible **Topics** taxonomy developed in direct collaboration with the **Centre for Science and Technology Studies (CWTS)** at Leiden University.

### 1.1. Construction Procedure
1. **Global Direct Citation Graph:** CWTS processed OpenAlex's global direct citation graph (over 250 million publications interconnected by explicit citations).
2. **Leiden Algorithm with CPM Model:**
   The Leiden algorithm (Traag, Waltman & van Eck, 2019) was applied by optimizing the *Constant Potts Model* (CPM) quality function across multiple modular resolution levels ($\gamma$). This guaranteed:
   - That all resulting clusters are internally connected (no isolated subcommunities).
   - Complete freedom from the resolution limit of traditional modularity.
3. **Labeling and Classification with Large Language Models (LLMs):**
   For each identified cluster, the most discriminative keywords were extracted and advanced language models were used to assign a formal descriptive title to the Topic.
4. **Text- and Citation-Based Classifier:**
   For recent works or preprints not yet linked by citations in the graph, a deep neural classifier was trained to predict the most probable Topic from the title, abstract, source venue, and outgoing citations.

---

## 2. 4-Level Taxonomic Hierarchy

The taxonomy organizes the entirety of global scientific knowledge into four strict hierarchical levels:

```mermaid
graph TD
    Domain["1. Global Domain (4 Domains)<br><i>Physical Sciences, Life Sciences, Health Sciences, Social Sciences</i>"]
    Field["2. Scientific Field (26 Fields)<br><i>Computer Science, Physics, Medicine, Mathematics, etc.</i>"]
    Subfield["3. Specialized Subfield (252 Subfields)<br><i>Artificial Intelligence, Condensed Matter, Immunology, etc.</i>"]
    Topic["4. Canonical Front / Topic (~4,516 Topics)<br><i>T10023: Polariton Condensation, T10142: Causal Inference, etc.</i>"]

    Domain --> Field
    Field --> Subfield
    Subfield --> Topic
```

### 2.1. The 4 Global Domains
1. **Physical Sciences:** Physics, Astronomy, Chemistry, Computer Science, Mathematics, Engineering, and Earth Sciences.
2. **Life Sciences:** Molecular Biology, Biochemistry, Genetics, Neuroscience, Agricultural Sciences, and Ecology.
3. **Health Sciences:** Medicine, Dentistry, Pharmacology, Nursing, and Public Health.
4. **Social Sciences:** Economics, Sociology, Psychology, Education, Law, Humanities, and Arts.

---

## 3. Field Mapping in OpenAlex (API & Optional ClickHouse `rag.works_flat`)

In OpenAlex (`./corpus.parquet` via `openalex-harvester`, REST API `primary_topic.*`, or the optional global snapshot `rag.works_flat`), taxonomy levels map as follows:

| Hierarchical Level | Portable OpenAlex / Parquet Column | API Filter Field | Optional ClickHouse Column (`rag.works_flat`) |
| :--- | :--- | :--- | :--- |
| **Domain** | `domain` (`domain_name`) | `primary_topic.domain.display_name` | `domain_name` (`LowCardinality(String)`) |
| **Field** | `field` (`field_name`) | `primary_topic.field.display_name` | `field_name` (`LowCardinality(String)`) |
| **Subfield**| `subfield` (`subfield_name`) | `primary_topic.subfield.display_name` | `subfield_name` (`LowCardinality(String)`) |
| **Canonical Topic** | `topic` / `topic_id` | `primary_topic.id` (e.g., `T10023`) | `topic`, `topic_id`, `primary_topic_id` |
| **All Topics** | `topics` / `all_topics` | `topics.id` | `all_topics` (`Array(LowCardinality(String))`) |

> [!TIP]
> **Columnar Optimization (When Using Optional ClickHouse Accelerator):**
> Never perform a `JOIN` with external topic tables. Filter directly using `subfield_name = 'Artificial Intelligence'` or `topic_id = 'T10142'`, and `has(all_topics, 'T10142')` for secondary topics.

---

## 4. When to Use OpenAlex Topics vs. Ad-Hoc Bibliographic Coupling

| Analysis Scenario | Recommended Choice | Technical Reason |
| :--- | :--- | :--- |
| **University- or Country-wide Mapping** | **OpenAlex Topics (`primary_topic` / `topic_id`)** | Evaluates thousands of publications rapidly without reconstructing citation graphs. |
| **Thematic Concentration Sunburst Diagram** | **OpenAlex Hierarchy (Domain $\to$ Field $\to$ Subfield $\to$ Topic)** | 100% precomputed multi-level structure directly compatible with Plotly `go.Sunburst`. |
| **Delineating a Specific Emerging Research Front (micro-front)** | **Ad-Hoc Contemporary Bibliographic Coupling** | Fine granularity. OpenAlex Topics group ~50 to 200 papers per year; ad-hoc coupling isolates specific frontier clusters of 10 to 30 articles. |
| **Temporal Evolution of a Multidisciplinary Topic** | **Hybrid: Subfield/Topic Filtering + AMI Lineages** | Extracts the subfield literature and tracks annual bifurcations and merges using the AMI metric. |
