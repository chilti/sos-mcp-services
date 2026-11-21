"""
Modular English Visual Artifact Generator (Standalone Phase Reports + Incremental Master Dashboard)
Workspace-First (`--workdir .`):
  - <workdir>/reports/fase0_visual_report.html .. fase5_visual_report.html
  - <workdir>/reports/hybrid_delineation_dashboard.html
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common_io import load_or_create_config, resolve_workdir

BASE_CSS = """
:root {
  --bg: #f8fafc; --card: #ffffff; --ink: #0f172a; --muted: #475569;
  --border: #e2e8f0; --accent: #0284c7; --green: #059669;
  --amber: #d97706; --red: #dc2626; --purple: #7c3aed;
}
* { box-sizing: border-box; }
body {
  margin: 0; padding: 24px 32px;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg); color: var(--ink); line-height: 1.5;
}
.header-bar {
  background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
  color: #fff; padding: 24px 28px; border-radius: 14px; margin-bottom: 24px;
  box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.18);
}
.header-bar h1 { margin: 0 0 6px 0; font-size: 1.55rem; font-weight: 700; }
.header-bar p { margin: 0; color: #cbd5e1; font-size: 0.92rem; }
.badge-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.badge { background: rgba(255,255,255,0.14); color: #f8fafc; padding: 4px 11px; border-radius: 999px; font-size: 0.78rem; font-weight: 600; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(195px, 1fr)); gap: 14px; margin-bottom: 22px; }
.kpi-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 16px 18px; box-shadow: 0 2px 6px rgba(15,23,42,0.04); }
.kpi-label { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); font-weight: 600; }
.kpi-val { font-size: 1.65rem; font-weight: 800; margin: 4px 0 2px 0; color: var(--ink); }
.kpi-sub { font-size: 0.8rem; color: var(--muted); }
.chart-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(480px, 1fr)); gap: 18px; margin-bottom: 22px; }
.chart-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 16px 18px; box-shadow: 0 2px 6px rgba(15,23,42,0.04); }
.chart-card.full-width { grid-column: 1 / -1; }
.chart-card h3 { margin: 0 0 10px 0; font-size: 1.02rem; color: var(--ink); border-bottom: 1px solid var(--border); padding-bottom: 8px; }
pre.query-box { background: #0f172a; color: #e2e8f0; padding: 12px 14px; border-radius: 8px; font-size: 0.78rem; overflow-x: auto; max-height: 240px; white-space: pre-wrap; }
.stepper { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
.step-pill { padding: 8px 16px; border-radius: 10px; font-size: 0.84rem; font-weight: 600; border: 1px solid var(--border); background: #fff; color: var(--muted); cursor: pointer; }
.step-pill.done { border-color: #10b981; background: #ecfdf5; color: #065f46; }
.step-pill.active { background: #0284c7; color: #fff; border-color: #0284c7; }
.tab-section { display: none; }
.tab-section.active { display: block; }
"""

ZONE_DISPLAY = {"ZONA_VERDE": "GREEN ZONE", "ZONA_GRIS": "GRAY ZONE", "ZONA_ROJA": "RED ZONE"}


def _wrap_html(title: str, subtitle: str, badges: list[str], body_html: str, extra_js: str = "") -> str:
    b_html = "".join(f'<span class="badge">{html.escape(b)}</span>' for b in badges)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>{html.escape(title)}</title>
  <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
  <style>{BASE_CSS}</style>
</head>
<body>
  <div class="header-bar">
    <h1>{html.escape(title)}</h1>
    <p>{html.escape(subtitle)} — Updated: {ts}</p>
    <div class="badge-row">{b_html}</div>
  </div>
  {body_html}
  <script>{extra_js}</script>
</body>
</html>
"""


def _kpi(label: str, val: str, sub: str = "", color: str = "") -> str:
    st = f' style="color:{color};"' if color else ""
    return f'<div class="kpi-card"><div class="kpi-label">{html.escape(label)}</div><div class="kpi-val"{st}>{html.escape(val)}</div><div class="kpi-sub">{html.escape(sub)}</div></div>'


def _plotly_div(div_id: str, traces: list[dict], layout: dict, height: int = 360) -> tuple[str, str]:
    lay = {"margin": {"t": 32, "r": 20, "b": 48, "l": 55}, "paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "#f8fafc", "font": {"family": "Inter, sans-serif", "size": 12}, **layout}
    html_div = f'<div id="{div_id}" style="width:100%;height:{height}px;"></div>'
    js = f"Plotly.newPlot('{div_id}', {json.dumps(traces, ensure_ascii=False)}, {json.dumps(lay, ensure_ascii=False)}, {{responsive: true, displaylogo: false}});"
    return html_div, js


def build_phase0_section(delin_dir: Path, cfg: dict) -> tuple[str, str, bool]:
    f0 = delin_dir / "fase0_estrategia"
    audit_csv = f0 / "audit_terminos_especificidad.csv"
    if not audit_csv.exists():
        return "<p>Phase 0 pending execution.</p>", "", False

    adf = pd.read_csv(audit_csv)
    tdf = pd.read_csv(f0 / "propuesta_topics_descubiertos.csv") if (f0 / "propuesta_topics_descubiertos.csv").exists() else pd.DataFrame()
    bdf = pd.read_csv(f0 / "propuesta_revistas_bradford.csv") if (f0 / "propuesta_revistas_bradford.csv").exists() else pd.DataFrame()

    n_free = int((adf["final_action"] == "FREE_OR").sum())
    n_coup = int((adf["final_action"] == "COUPLE_PROXIMITY").sum())
    n_drop = int(adf["final_action"].astype(str).str.startswith("DROP").sum())
    n_top_inc = int(tdf["llm_class"].isin(["INCLUDE_CORE", "INCLUDE_ADJACENT"]).sum()) if not tdf.empty else 0
    n_brad_pure = int((bdf["source_class"] == "PURE_DOMAIN_JOURNAL").sum()) if not bdf.empty else 0

    kpis = [
        _kpi("FREE_OR Terms", f"{n_free}", "Validated bilingual specificity", "#059669"),
        _kpi("COUPLE_PROXIMITY Terms", f"{n_coup}", "Paired via NEAR/5 / W/5 with domain anchors", "#d97706"),
        _kpi("Pruned Terms (DROP)", f"{n_drop}", "Low-specificity traps dropped", "#dc2626"),
        _kpi("Included OpenAlex Topics", f"{n_top_inc}", f"Out of {len(tdf)} discovered (no domain cutoff)", "#0284c7"),
        _kpi("Core Bradford Journals", f"{n_brad_pure}", "Pure domain sources (>70% share)", "#7c3aed"),
    ]

    js_parts = []
    grp = adf.groupby(["lang", "final_action"]).size().unstack(fill_value=0)
    colors1 = {"FREE_OR": "#059669", "COUPLE_PROXIMITY": "#d97706", "DROP_LOW_SPEC": "#dc2626", "DROP_ZERO_HITS": "#94a3b8"}
    traces1 = [{"type": "bar", "name": col, "x": grp.index.str.upper().tolist(), "y": grp[col].tolist(), "marker": {"color": colors1.get(col, "#64748b")}} for col in grp.columns]
    div1, js1 = _plotly_div("f0_terms_bar", traces1, {"barmode": "group", "xaxis": {"title": "Language"}, "yaxis": {"title": "Number of Terms"}}, 340)
    js_parts.append(js1)

    hit_col = "sample_hits" if "sample_hits" in adf.columns else ("mx_hits" if "mx_hits" in adf.columns else None)
    traces2 = []
    if hit_col:
        adf_plot = adf[adf[hit_col] > 0].copy()
        for act, col in [("FREE_OR", "#059669"), ("COUPLE_PROXIMITY", "#d97706"), ("DROP_LOW_SPEC", "#dc2626")]:
            sub = adf_plot[adf_plot["final_action"] == act]
            if not sub.empty:
                traces2.append({"type": "scatter", "mode": "markers", "name": act, "x": sub[hit_col].tolist(), "y": sub["topic_specificity"].tolist(), "text": (sub["term"] + " (" + sub["lang"] + ")").tolist(), "marker": {"size": 8, "color": col, "opacity": 0.75}})
    div2, js2 = _plotly_div("f0_spec_scatter", traces2, {"xaxis": {"title": "Sample Frequency / Hits (log scale)", "type": "log"}, "yaxis": {"title": "Thematic Specificity [0-1]"}}, 340)
    js_parts.append(js2)

    q_geo = "country" if (f0 / "queries" / "country").exists() else "global"
    q_dir = f0 / "queries" / q_geo
    q_html = ""
    if q_dir.exists():
        q_boxes = []
        for qf, lbl in [
            ("wos_broad_100recall.txt", f"Web of Science ({q_geo.upper()})"),
            ("scopus_broad.txt", f"Scopus ({q_geo.upper()})"),
            ("pubmed_broad.txt", f"PubMed NCBI ({q_geo.upper()})"),
            ("openalex_web_manual.txt", f"OpenAlex Web UI — Manual CSV & 1-Click Links ({q_geo.upper()})"),
            ("clickhouse_broad.sql", f"ClickHouse SQL ({q_geo.upper()})"),
        ]:
            p = q_dir / qf
            if p.exists():
                q_boxes.append(f'<div><strong>{html.escape(lbl)}</strong><pre class="query-box">{html.escape(p.read_text(encoding="utf-8"))}</pre></div>')
        if q_boxes:
            q_html = f'<div class="chart-card full-width"><h3>Compiled & Validated Multi-Database Queries (Phase 0)</h3><div class="chart-grid">{"".join(q_boxes)}</div></div>'

    return f'<div class="kpi-grid">{"".join(kpis)}</div><div class="chart-grid"><div class="chart-card"><h3>Bilingual Term Distribution by Action</h3>{div1}</div><div class="chart-card"><h3>Term Specificity vs. Sample Frequency Audit</h3>{div2}</div>{q_html}</div>', "\n".join(js_parts), True


def build_phase1_section(delin_dir: Path, cfg: dict) -> tuple[str, str, bool]:
    f1 = delin_dir / "fase1_corpus"
    man_json = f1 / "fase1_ingesta_manifest.json"
    dedup_pq = f1 / "corpus_bruto_dedup.parquet"
    if not man_json.exists():
        return "<p>Phase 1 pending execution.</p>", "", False

    man = json.loads(man_json.read_text(encoding="utf-8"))
    ds = man.get("dedup_stats", {})
    raw_tot, dedup_tot = ds.get("raw_total", 0), ds.get("dedup_total", 0)
    l1, l2, l3, l4 = ds.get("level1_doi_merges", 0), ds.get("level2_pmid_merges", 0), ds.get("level3_title_year_merges", 0), ds.get("level4_bilingual_semantic_merges", 0)
    abs_cov = man.get("abstract_coverage", 0) * 100.0

    kpis = [
        _kpi("Raw Multi-Source Records", f"{raw_tot:,}", "Pre-deduplication union", "#0284c7"),
        _kpi("Unique Corpus (Post-4 Levels)", f"{dedup_tot:,}", f"Removed {raw_tot - dedup_tot:,} duplicates", "#059669"),
        _kpi("Level 1-3 Merges", f"{l1 + l2 + l3:,}", f"DOI={l1:,} | PMID={l2:,} | Title+Year={l3:,}", "#475569"),
        _kpi("Level 4 Bilingual Semantic", f"{l4:,}", "EN/ES pairs cos >= 0.95", "#7c3aed"),
        _kpi("Abstract Coverage", f"{abs_cov:.1f}%", "Post Open Recovery Cascade", "#0d9488"),
    ]

    js_parts = []
    src_counts = man.get("source_counts_raw", {})
    div1, js1 = _plotly_div("f1_sources_bar", [{"type": "bar", "x": list(src_counts.keys()), "y": list(src_counts.values()), "text": [f"{v:,}" for v in src_counts.values()], "textposition": "auto", "marker": {"color": "#0284c7"}}], {"xaxis": {"title": "Source"}, "yaxis": {"title": "Records"}}, 340)
    js_parts.append(js1)

    stages = ["1. Raw Union", "2. Post-L1 (DOI)", "3. Post-L2 (PMID)", "4. Post-L3 (Title+Year)", "5. Post-L4 (Semantic >=0.95)"]
    vals = [raw_tot, raw_tot - l1, raw_tot - l1 - l2, raw_tot - l1 - l2 - l3, dedup_tot]
    div2, js2 = _plotly_div("f1_dedup_funnel", [{"type": "bar", "x": stages, "y": vals, "text": [f"{v:,}" for v in vals], "textposition": "auto", "marker": {"color": ["#64748b", "#0284c7", "#0ea5e9", "#0d9488", "#059669"]}}], {"yaxis": {"title": "Unique Records Remaining"}}, 340)
    js_parts.append(js2)

    div3_card = ""
    if dedup_pq.exists():
        df1 = pd.read_parquet(dedup_pq, columns=["sources_list", "abstract_source"])
        top_combos = df1["sources_list"].value_counts().head(10)
        div3, js3 = _plotly_div("f1_combos_bar", [{"type": "bar", "orientation": "h", "y": top_combos.index.tolist()[::-1], "x": top_combos.values.tolist()[::-1], "text": [f"{v:,}" for v in top_combos.values.tolist()[::-1]], "textposition": "auto", "marker": {"color": "#7c3aed"}}], {"margin": {"t": 25, "r": 25, "b": 45, "l": 220}, "xaxis": {"title": "Unique Works"}}, 350)
        js_parts.append(js3)

        abs_src = df1["abstract_source"].replace("", "no_abstract").value_counts()
        div4, js4 = _plotly_div("f1_abs_src_pie", [{"type": "pie", "labels": abs_src.index.tolist(), "values": abs_src.values.tolist(), "hole": 0.42}], {"margin": {"t": 25, "r": 20, "b": 25, "l": 20}}, 350)
        js_parts.append(js4)
        div3_card = f'<div class="chart-card"><h3>Multi-Database Overlap (Top Source Combinations)</h3>{div3}</div><div class="chart-card"><h3>Abstract Recovery Sources (Open Cascade)</h3>{div4}</div>'

    return f'<div class="kpi-grid">{"".join(kpis)}</div><div class="chart-grid"><div class="chart-card"><h3>Raw Harvest by Source</h3>{div1}</div><div class="chart-card"><h3>4-Level Hybrid Deduplication Cascade</h3>{div2}</div>{div3_card}</div>', "\n".join(js_parts), True


def build_phase2_section(delin_dir: Path, cfg: dict) -> tuple[str, str, bool]:
    f2 = delin_dir / "fase2_scoring"
    m_json = f2 / "fase2_oof_metrics.json"
    sc_pq = f2 / "corpus_scored_rrf.parquet"
    if not m_json.exists() or not sc_pq.exists():
        return "<p>Phase 2 pending execution.</p>", "", False

    m = json.loads(m_json.read_text(encoding="utf-8"))
    oof, vias = m.get("oof_calibration", {}), m.get("via_counts", {})
    df2 = pd.read_parquet(sc_pq, columns=["seed_role", "margin_score"])

    kpis = [
        _kpi("S+ / S- Stratified Seeds", f"{oof.get('n_pos_seeds', 0):,} / {oof.get('n_neg_seeds', 0):,}", "Co-constructed from corpus signals", "#0284c7"),
        _kpi("OOF PR-AUC (5-Fold)", f"{oof.get('oof_margin_pr_auc', 0):.4f}", f"LogReg PR-AUC: {oof.get('oof_logreg_pr_auc', 0):.4f}", "#059669"),
        _kpi("OOF ROC-AUC (5-Fold)", f"{oof.get('oof_margin_roc_auc', 0):.4f}", f"FPR@Rec90: {oof.get('oof_margin_fpr_at_rec90', 0)*100:.2f}%", "#059669"),
        _kpi("Abstract vs. No-Abstract Gap", f"{oof.get('oof_abs_gap', 0):.4f}", "Target < 0.0200", "#0d9488"),
        _kpi("Semantic-Only Rescue", f"{vias.get('SEM_ONLY_RESCUE', 0):,}", f"Lex+Sem Convergence: {vias.get('BOTH_LEX_AND_SEM', 0):,}", "#7c3aed"),
    ]

    traces1 = []
    for role, name, col in [("S_POS", "S+ Seeds (Positive)", "#059669"), ("S_NEG", "S- Seeds (Hard Negative)", "#dc2626"), ("NONE", "Unlabeled Candidates", "#94a3b8")]:
        sub = df2[df2["seed_role"] == role]["margin_score"].dropna()
        if not sub.empty:
            traces1.append({"type": "histogram", "name": name, "x": sub.sample(n=min(6000, len(sub)), random_state=42).round(4).tolist(), "opacity": 0.65, "marker": {"color": col}, "nbinsx": 60})
    div1, js1 = _plotly_div("f2_margin_hist", traces1, {"barmode": "overlay", "xaxis": {"title": "Contrastive Margin m(d) = Sim(S+) - Sim(S-)"}, "yaxis": {"title": "Frequency"}}, 350)
    div2, js2 = _plotly_div("f2_vias_bar", [{"type": "bar", "x": list(vias.keys()), "y": list(vias.values()), "text": [f"{v:,}" for v in vias.values()], "textposition": "auto", "marker": {"color": ["#059669", "#d97706", "#0284c7", "#94a3b8"]}}], {"xaxis": {"title": "Capture Pathway"}, "yaxis": {"title": "Works"}}, 350)
    return f'<div class="kpi-grid">{"".join(kpis)}</div><div class="chart-grid"><div class="chart-card"><h3>Contrastive Separability: Margin m(d)</h3>{div1}</div><div class="chart-card"><h3>Hybrid Capture Pathways (RRF k=60)</h3>{div2}</div></div>', f"{js1}\n{js2}", True


def build_phase3_section(delin_dir: Path, cfg: dict) -> tuple[str, str, bool]:
    f3 = delin_dir / "fase3_manifold"
    m_json = f3 / "fase3_manifold_metrics.json"
    tr_pq = f3 / "corpus_triaged_leiden.parquet"
    if not m_json.exists() or not tr_pq.exists():
        return "<p>Phase 3 pending execution.</p>", "", False

    m = json.loads(m_json.read_text(encoding="utf-8"))
    id_st, zc = m.get("intrinsic_dimension", {}), m.get("zone_counts", {})
    df3 = pd.read_parquet(tr_pq, columns=["umap_x", "umap_y", "zona_triaje", "leiden_cluster", "title"])
    cards = pd.read_csv(f3 / "leiden_cluster_cards.csv") if (f3 / "leiden_cluster_cards.csv").exists() else pd.DataFrame()
    d_id = id_st.get("umap_d_id_selected", 13)

    kpis = [
        _kpi("Intrinsic Dimension d_ID", f"{d_id}D", f"TwoNN={id_st.get('d_twonn', 0)} | MLE_p95={id_st.get('d_mle_p95_k20', 0)}", "#0284c7"),
        _kpi("Leiden Communities", f"{m.get('n_clusters', 0)}", f"Optimal gamma={m.get('best_gamma', 1.5)} (0% orphans)", "#7c3aed"),
        _kpi("GREEN ZONE (Auto-Core)", f"{zc.get('ZONA_VERDE', 0):,}", f"{zc.get('ZONA_VERDE', 0)/max(1, len(df3))*100:.1f}% of corpus", "#059669"),
        _kpi("GRAY ZONE (Boundary)", f"{zc.get('ZONA_GRIS', 0):,}", f"Includes {m.get('red_zone_outliers_rescued', 0):,} rescued from Red Zone", "#d97706"),
        _kpi("RED ZONE (Pruned Noise)", f"{zc.get('ZONA_ROJA', 0):,}", "High-confidence out-of-domain noise", "#dc2626"),
    ]

    samp = df3.sample(n=min(12000, len(df3)), random_state=42) if len(df3) > 12000 else df3
    traces1 = []
    for zname, col in [("ZONA_GRIS", "#eab308"), ("ZONA_ROJA", "#dc2626"), ("ZONA_VERDE", "#059669")]:
        sub = samp[samp["zona_triaje"] == zname]
        if not sub.empty:
            traces1.append({"type": "scattergl", "mode": "markers", "name": f"{ZONE_DISPLAY[zname]} (n={zc.get(zname, len(sub)):,})", "x": sub["umap_x"].round(3).tolist(), "y": sub["umap_y"].round(3).tolist(), "text": (sub["title"].fillna("").astype(str).str[:95] + " [C" + sub["leiden_cluster"].astype(str) + "]").tolist(), "marker": {"size": 4.5, "color": col, "opacity": 0.65}})
    div1, js1 = _plotly_div("f3_umap_scatter", traces1, {"xaxis": {"title": f"UMAP-1 (from {d_id}D manifold)"}, "yaxis": {"title": f"UMAP-2 (from {d_id}D manifold)"}}, 440)

    div2_card, js2 = "", ""
    if not cards.empty:
        traces2 = []
        for zname, col in [("ZONA_VERDE", "#059669"), ("ZONA_GRIS", "#eab308"), ("ZONA_ROJA", "#dc2626")]:
            sub = cards[cards["zona_inicial"] == zname]
            if not sub.empty:
                traces2.append({"type": "scatter", "mode": "markers", "name": ZONE_DISPLAY[zname], "x": sub["median_margin"].tolist(), "y": sub["pct_title_free_hits"].tolist(), "text": ("Cluster C" + sub["leiden_cluster"].astype(str) + " (n=" + sub["n_docs"].astype(str) + "): " + sub["c_tfidf_terms"].fillna("").astype(str)).tolist(), "marker": {"size": np.clip(np.sqrt(sub["n_docs"].values) * 1.4, 6, 36).round(1).tolist(), "color": col, "opacity": 0.75}})
        div2, js2 = _plotly_div("f3_clusters_bubble", traces2, {"xaxis": {"title": "Cluster Median Contrastive Margin"}, "yaxis": {"title": "% Works with Free Domain Term in Title"}}, 440)
        div2_card = f'<div class="chart-card"><h3>Leiden Communities Topology (Size, Margin & Title Purity)</h3>{div2}</div>'

    return f'<div class="kpi-grid">{"".join(kpis)}</div><div class="chart-grid"><div class="chart-card"><h3>2D Topological Manifold (UMAP {d_id}D -> 2D)</h3>{div1}</div>{div2_card}</div>', f"{js1}\n{js2}", True


def build_phase4_section(delin_dir: Path, cfg: dict) -> tuple[str, str, bool]:
    f4 = delin_dir / "fase4_llm_snowball"
    m_json = f4 / "fase4_llm_metrics.json"
    tr_pq = f4 / "corpus_triage_completo.parquet"
    if not m_json.exists() or not tr_pq.exists():
        return "<p>Phase 4 pending execution.</p>", "", False

    m = json.loads(m_json.read_text(encoding="utf-8"))
    zg = m.get("zona_gris_llm_counts", {})
    df4 = pd.read_parquet(tr_pq, columns=["zona_triaje", "llm_decision", "margin_score"])

    kpis = [
        _kpi("Gray Zone Evaluated", f"{sum(zg.values()):,}", f"Judge mode: {m.get('judge_mode', 'agent').upper()}", "#0284c7"),
        _kpi("Gray -> INCLUDE_CORE", f"{zg.get('INCLUDE_CORE', 0):,}", "Promoted to STRICT_CORE", "#059669"),
        _kpi("Gray -> INCLUDE_PERIPHERY", f"{zg.get('INCLUDE_PERIPHERY', 0):,}", "Interdisciplinary boundary", "#d97706"),
        _kpi("Gray -> EXCLUDE", f"{zg.get('EXCLUDE', 0):,}", "Homonyms & noise pruned", "#dc2626"),
        _kpi("1-Hop Snowball Rescue", f"{m.get('snowball_rescued', 0):,}", "k >= 2 Green links + margin", "#7c3aed"),
    ]

    labels1 = ["INCLUDE_CORE", "INCLUDE_PERIPHERY", "EXCLUDE"]
    div1, js1 = _plotly_div("f4_judge_pie", [{"type": "pie", "labels": labels1, "values": [zg.get(k, 0) for k in labels1], "hole": 0.42, "marker": {"colors": ["#059669", "#d97706", "#dc2626"]}}], {"margin": {"t": 25, "r": 20, "b": 25, "l": 20}}, 350)

    g_sub = df4[df4["zona_triaje"] == "ZONA_GRIS"]
    traces2 = []
    for dec, col in [("INCLUDE_CORE", "#059669"), ("INCLUDE_PERIPHERY", "#d97706"), ("EXCLUDE", "#dc2626")]:
        s = g_sub[g_sub["llm_decision"] == dec]["margin_score"].dropna()
        if not s.empty:
            traces2.append({"type": "box", "name": dec, "y": s.sample(n=min(4000, len(s)), random_state=42).round(4).tolist(), "marker": {"color": col}})
    div2, js2 = _plotly_div("f4_margin_box", traces2, {"xaxis": {"title": "Judge Decision"}, "yaxis": {"title": "Contrastive Margin m(d) in Gray Zone"}}, 350)
    return f'<div class="kpi-grid">{"".join(kpis)}</div><div class="chart-grid"><div class="chart-card"><h3>Gray Zone Agent-as-a-Judge Decision Breakdown</h3>{div1}</div><div class="chart-card"><h3>Geometric Margin m(d) vs. Judge Decision</h3>{div2}</div></div>', f"{js1}\n{js2}", True


def build_phase5_section(delin_dir: Path, cfg: dict) -> tuple[str, str, bool]:
    f5 = delin_dir / "fase5_corpus_final"
    man_json = f5 / "fase5_global_manifest.json"
    corp_pq = delin_dir.parent / "corpus.parquet"
    if not man_json.exists():
        return "<p>Phase 5 pending execution.</p>", "", False

    man = json.loads(man_json.read_text(encoding="utf-8"))
    cnt = man.get("counts", {})
    doms, dtypes = man.get("domains_represented_no_cutoff", {}), man.get("doc_types", {})
    y0, y1 = man.get("year_range", [1980, 2025])

    kpis = [
        _kpi("Canonical Citable Corpus", f"{cnt.get('final_corpus_total', 0):,}", "Exported as ./corpus.parquet", "#059669"),
        _kpi("STRICT_CORE Layer", f"{cnt.get('strict_core_count', 0):,}", "Direct disciplinary core", "#0284c7"),
        _kpi("EXTENDED_INTERDISCIPLINARY", f"{cnt.get('extended_interdisciplinary_count', 0):,}", "Bridge + 1-hop Snowball", "#0d9488"),
        _kpi("Separated Conferences", f"{cnt.get('conference_proceedings_separated_count', 0):,}", "Exported as ./corpus_conferences.parquet", "#7c3aed"),
        _kpi("Noise & Retracted Pruned", f"{cnt.get('excluded_noise_count', 0):,}", f"Retracted/paratext: {cnt.get('excluded_retracted_count', 0)}", "#dc2626"),
    ]

    raw_n = man.get("phase_summaries", {}).get("fase1", {}).get("dedup_stats", {}).get("raw_total", cnt.get("fase1_dedup_broad_candidates", 0))
    stages = ["1. Raw Harvest", "2. Unique Post-Dedup", "3. Canonical Citable Corpus", "4. STRICT_CORE", "5. Conferences (Annex)"]
    vals = [raw_n, cnt.get("fase1_dedup_broad_candidates", 0), cnt.get("final_corpus_total", 0), cnt.get("strict_core_count", 0), cnt.get("conference_proceedings_separated_count", 0)]
    div1, js1 = _plotly_div("f5_prisma_funnel", [{"type": "bar", "x": stages, "y": vals, "text": [f"{v:,}" for v in vals], "textposition": "auto", "marker": {"color": ["#64748b", "#0284c7", "#059669", "#0d9488", "#7c3aed"]}}], {"yaxis": {"title": "Works"}}, 350)
    div2, js2 = _plotly_div("f5_domains_pie", [{"type": "pie", "labels": list(doms.keys()), "values": list(doms.values()), "hole": 0.42}], {"margin": {"t": 25, "r": 20, "b": 25, "l": 20}}, 350)
    js_parts = [js1, js2]

    div3_card = ""
    if corp_pq.exists():
        dfc = pd.read_parquet(corp_pq, columns=["publication_year", "final_corpus_layer"])
        yr_grp = dfc[(dfc["publication_year"] >= y0) & (dfc["publication_year"] <= y1)].groupby(["publication_year", "final_corpus_layer"]).size().unstack(fill_value=0)
        traces3 = [{"type": "bar", "name": lyr, "x": yr_grp.index.tolist(), "y": yr_grp[lyr].tolist(), "marker": {"color": col}} for lyr, col in [("STRICT_CORE", "#059669"), ("EXTENDED_INTERDISCIPLINARY", "#0284c7")] if lyr in yr_grp.columns]
        div3, js3 = _plotly_div("f5_yearly_trend", traces3, {"barmode": "stack", "xaxis": {"title": "Publication Year"}, "yaxis": {"title": "Citable Works"}}, 350)
        div4, js4 = _plotly_div("f5_doctypes_bar", [{"type": "bar", "x": list(dtypes.keys()), "y": list(dtypes.values()), "text": [f"{v:,}" for v in dtypes.values()], "textposition": "auto", "marker": {"color": "#0d9488"}}], {"xaxis": {"title": "Document Type"}, "yaxis": {"title": "Citable Works"}}, 350)
        js_parts.extend([js3, js4])
        div3_card = f'<div class="chart-card"><h3>Longitudinal Evolution ({y0}-{y1})</h3>{div3}</div><div class="chart-card"><h3>Peer-Reviewed Document Types (GLOBAL Guideline)</h3>{div4}</div>'

    return f'<div class="kpi-grid">{"".join(kpis)}</div><div class="chart-grid"><div class="chart-card"><h3>PRISMA-S / GLOBAL Hybrid Delineation Funnel</h3>{div1}</div><div class="chart-card"><h3>Scientific Domain Distribution (Zero Blind Domains)</h3>{div2}</div>{div3_card}</div>', "\n".join(js_parts), True


PHASE_BUILDERS = [
    (0, "Phase 0: Bilingual Strategy & Pearl Growing", "fase0_visual_report.html", build_phase0_section),
    (1, "Phase 1: Multi-Source Harvest & 4-Level Dedup", "fase1_visual_report.html", build_phase1_section),
    (2, "Phase 2: S+/S- Seeds, OOF Calibration & RRF", "fase2_visual_report.html", build_phase2_section),
    (3, "Phase 3: UMAP(d_ID -> 2D) Manifold & Leiden", "fase3_visual_report.html", build_phase3_section),
    (4, "Phase 4: Agent-as-a-Judge & 1-Hop Snowball", "fase4_visual_report.html", build_phase4_section),
    (5, "Phase 5: Canonical Corpus & PRISMA-S Audit", "fase5_visual_report.html", build_phase5_section),
]


def update_incremental_dashboard(workdir: Path, cfg: dict) -> Path:
    delin_dir = workdir / "delineation"
    rep_dir = workdir / "reports"
    rep_dir.mkdir(parents=True, exist_ok=True)
    topic = cfg["domain"]["seed_topic_en"]
    geo = cfg["scope"].get("geo_country_code") or "Global"
    y0, y1 = cfg["scope"]["year_start"], cfg["scope"]["year_end"]

    pills, sections, all_js = [], [], []
    completed_count, last_done_idx = 0, 0
    rendered = []
    for idx, title, _, fn in PHASE_BUILDERS:
        sec_html, sec_js, is_done = fn(delin_dir, cfg)
        if is_done:
            completed_count += 1
            last_done_idx = idx
        rendered.append((idx, title, sec_html, sec_js, is_done))

    for idx, title, sec_html, sec_js, is_done in rendered:
        active_cls = " active" if idx == last_done_idx else ""
        done_cls = " done" if is_done else ""
        icon = "✓ " if is_done else "○ "
        pills.append(f'<button class="step-pill{done_cls}{active_cls}" onclick="showPhase({idx})" id="pill_{idx}">{icon}{html.escape(title)}</button>')
        sections.append(f'<div class="tab-section{active_cls}" id="sec_{idx}">{sec_html}</div>')
        if sec_js:
            all_js.append(sec_js)

    tab_js = """
    function showPhase(idx) {
      document.querySelectorAll('.tab-section').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.step-pill').forEach(el => el.classList.remove('active'));
      const sec = document.getElementById('sec_' + idx);
      const pill = document.getElementById('pill_' + idx);
      if (sec) sec.classList.add('active');
      if (pill) pill.classList.add('active');
      window.dispatchEvent(new Event('resize'));
    }
    """
    master_path = rep_dir / "hybrid_delineation_dashboard.html"
    master_html = _wrap_html(
        "Incremental Master Dashboard — Hybrid Scientific Field Delineation",
        f"Domain: {topic} | Scope: {geo} ({y0}-{y1}) | Completed Phases: {completed_count}/6",
        [f"Active Phases: {completed_count}/6", "Workspace-First (./corpus.parquet)", "UMAP(d_ID -> 2D) + Leiden", "Agent-as-a-Judge + Horvitz-Thompson"],
        f'<div class="stepper">{"".join(pills)}</div>{"".join(sections)}',
        "\n".join(all_js) + "\n" + tab_js,
    )
    master_path.write_text(master_html, encoding="utf-8")
    return master_path


def generate_phase_visuals(phase_idx: int, workdir: Path, cfg: dict | None = None) -> Path:
    if cfg is None:
        cfg, _ = load_or_create_config(workdir)
    matches = [p for p in PHASE_BUILDERS if p[0] == phase_idx]
    if not matches:
        raise ValueError(f"Invalid phase index: {phase_idx}")
    idx, title, fname, fn = matches[0]
    delin_dir = workdir / "delineation"
    rep_dir = workdir / "reports"
    rep_dir.mkdir(parents=True, exist_ok=True)
    sec_html, sec_js, _ = fn(delin_dir, cfg)
    out_file = rep_dir / fname
    topic = cfg["domain"]["seed_topic_en"]
    geo = cfg["scope"].get("geo_country_code") or "Global"
    y0, y1 = cfg["scope"]["year_start"], cfg["scope"]["year_end"]
    standalone_html = _wrap_html(
        f"{title} — Standalone Visual Report",
        f"Domain: {topic} | Scope: {geo} ({y0}-{y1})",
        [f"Phase {idx}", "Standalone Report", "GLOBAL / PRISMA-S"],
        sec_html,
        sec_js,
    )
    out_file.write_text(standalone_html, encoding="utf-8")
    master_path = update_incremental_dashboard(workdir, cfg)
    print(f"  [Phase {idx} Visual] {out_file.name} | Master: {master_path.name}")
    return out_file


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", type=str, default=".")
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--phase", type=str, default="all", help="0..5 or 'all'")
    args = parser.parse_args()

    wd = resolve_workdir(args.workdir)
    cfg, _ = load_or_create_config(wd, config_path=args.config)
    if args.phase == "all":
        for idx, _, _, _ in PHASE_BUILDERS:
            generate_phase_visuals(idx, wd, cfg)
    else:
        generate_phase_visuals(int(args.phase), wd, cfg)


if __name__ == "__main__":
    main()
