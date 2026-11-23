"""
Phase 0: Discipline-Agnostic, Clean-Room Bilingual Search Strategy Builder.
Works for ANY scientific topic (`--topic-en`, `--topic-es`), time window, and geographic scope (`--country`).
Supports both local OpenAI-compatible LLM (`--llm-mode auto|local`) and Host-Agent prompt/response mode (`--llm-mode agent`).
Zero extra OpenAlex /works API calls during term specificity audit (in-memory evaluation over Pearl-Growing samples).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, ENGLISH_STOP_WORDS

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common_io import filter_safe_homonyms, load_env_vars, load_or_create_config, load_query_validator, phase_dir, resolve_workdir


def http_get_json(url: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "hybrid-field-delineation/1.0"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as he:
            if he.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(2.0 * (attempt + 1))
                continue
            raise
        except Exception:
            if attempt < 3:
                time.sleep(2.0 * (attempt + 1))
                continue
            raise
    return {}


def llm_endpoint_alive(base_url: str, api_key: str = "") -> bool:
    try:
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        req = urllib.request.Request(base_url.rstrip("/") + "/models", headers=headers)
        with urllib.request.urlopen(req, timeout=4) as r:
            return r.status == 200
    except Exception:
        return False


def llm_chat_json(base_url: str, api_key: str, model: str, system_prompt: str, user_prompt: str) -> dict:
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "temperature": 0.0,
        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=240) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
                msg = raw["choices"][0]["message"]
                content = (msg.get("content") or "").strip()
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
                content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.IGNORECASE | re.DOTALL).strip()
                m = re.search(r"\{.*\}", content, flags=re.DOTALL)
                if m:
                    return json.loads(m.group(0))
        except Exception:
            time.sleep(2.0 * (attempt + 1))
    return {}


def default_rule_facets(topic_en: str, topic_es: str, is_bio: bool) -> dict[str, Any]:
    """Deterministic zero-LLM fallback facets derived directly from the user's seed topic."""
    words_en = [w for w in re.findall(r"[a-zA-Z0-9\-]{3,}", topic_en.lower()) if w not in {"and", "the", "for", "with", "from"}]
    words_es = [w for w in re.findall(r"[a-zA-ZáéíóúñÁÉÍÓÚÑ0-9\-]{3,}", topic_es.lower()) if w not in {"de", "del", "las", "los", "para", "con"}]
    return {
        "topic_search_queries": list(dict.fromkeys([topic_en, *words_en[:5], f"{topic_en} research", f"{topic_en} clinical" if is_bio else f"{topic_en} applications"])),
        "anatomical_anchors_en": list(dict.fromkeys([topic_en.lower(), *words_en[:6]])),
        "anatomical_anchors_es": list(dict.fromkeys([topic_es.lower(), *words_es[:6]])),
        "scope_inclusion_criteria": f"Direct theoretical, empirical, methodological, or applied research centered on {topic_en}.",
        "scope_exclusion_traps": f"Homonyms, metaphorical uses, or tangential mentions where {topic_en} is not the primary object of study.",
        "lexical_homonyms_to_avoid": [],
        "mesh_root_terms": [],
    }


def generate_initial_discovery_facets(cfg: dict, api_key: str, out_dir: Path, llm_mode: str) -> dict[str, Any]:
    dom = cfg["domain"]
    ep = cfg["endpoints"]
    sys_p = (
        "You are an expert scientometrician and information retrieval specialist. "
        "Given any scientific field/topic, return ONLY strict valid JSON containing bilingual discovery facets "
        "with zero domain assumptions outside what the topic requires."
    )
    usr_p = f"""Design initial clean-room OpenAlex discovery facets for:
- English topic: "{dom['seed_topic_en']}"
- Spanish topic: "{dom['seed_topic_es']}"
- Biomedical domain flag: {dom.get('is_biomedical', False)}

Return JSON with keys:
- "topic_search_queries": 10-14 short English search phrases for OpenAlex /topics endpoint covering core + adjacent interdisciplinary subfields.
- "anatomical_anchors_en": 4-8 core English anchor phrases/roots identifying the domain when coupled with ambiguous terms.
- "anatomical_anchors_es": 4-8 core Spanish anchor phrases/roots.
- "scope_inclusion_criteria": 2-sentence clear inclusion rubric for Phase 4 judging.
- "scope_exclusion_traps": 2-sentence exclusion rubric describing likely homonyms or adjacent false positives.
- "lexical_homonyms_to_avoid": 6-12 short English/Spanish homonyms from OTHER disciplines (NEVER include core terms or subfields of the target topic).
- "mesh_root_terms": 3-6 official MeSH headings if biomedical (else empty list []).
"""
    if llm_mode in ("auto", "local") and llm_endpoint_alive(ep["llm_base_url"], api_key):
        res = llm_chat_json(ep["llm_base_url"], api_key, ep["llm_model"], sys_p, usr_p)
        if res and "topic_search_queries" in res:
            prot = [dom["seed_topic_en"], dom["seed_topic_es"], *(res.get("anatomical_anchors_en") or []), *(res.get("anatomical_anchors_es") or [])]
            res["lexical_homonyms_to_avoid"] = filter_safe_homonyms(res.get("lexical_homonyms_to_avoid") or [], prot)
            return res

    if llm_mode == "agent":
        pdir = out_dir / "agent_prompts"
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir / "01_facets_prompt.json").write_text(json.dumps({"system": sys_p, "user": usr_p, "target_file": str(out_dir / "facets_init.json")}, indent=2), encoding="utf-8")
        print("  [Host-Agent Mode] No local LLM used; generated deterministic facets baseline + prompt in agent_prompts/01_facets_prompt.json.")
    return default_rule_facets(dom["seed_topic_en"], dom["seed_topic_es"], bool(dom.get("is_biomedical")))


def discover_openalex_topics(queries: list[str], email: str, oa_key: str | None) -> pd.DataFrame:
    seen: dict[str, dict[str, Any]] = {}
    for q in queries:
        params: dict[str, str] = {"search": q, "per-page": "25", "mailto": email}
        if oa_key:
            params["api_key"] = oa_key
        url = "https://api.openalex.org/topics?" + urllib.parse.urlencode(params)
        try:
            data = http_get_json(url)
        except Exception:
            if "api_key" in params:
                params.pop("api_key", None)
                try:
                    data = http_get_json("https://api.openalex.org/topics?" + urllib.parse.urlencode(params))
                except Exception:
                    continue
            else:
                continue
        for t in data.get("results", []):
            tid = str(t.get("id", "")).split("/")[-1]
            if not tid:
                continue
            kw_items = [k.get("display_name", "") if isinstance(k, dict) else str(k) for k in (t.get("keywords") or [])]
            row = {
                "topic_id": tid,
                "display_name": t.get("display_name", ""),
                "description": (t.get("description") or "")[:300],
                "keywords": "; ".join(k for k in kw_items if k),
                "subfield": (t.get("subfield") or {}).get("display_name", ""),
                "field": (t.get("field") or {}).get("display_name", ""),
                "domain": (t.get("domain") or {}).get("display_name", ""),
                "works_count": int(t.get("works_count") or 0),
                "matched_query": q,
            }
            seen.setdefault(tid, row)
    return pd.DataFrame(list(seen.values())).sort_values("works_count", ascending=False).reset_index(drop=True) if seen else pd.DataFrame()


def classify_topics(topics_df: pd.DataFrame, cfg: dict, facets_init: dict, api_key: str, out_dir: Path, llm_mode: str) -> pd.DataFrame:
    if topics_df.empty:
        return topics_df
    ep = cfg["endpoints"]
    topic_en = cfg["domain"]["seed_topic_en"]
    use_llm = llm_mode in ("auto", "local") and llm_endpoint_alive(ep["llm_base_url"], api_key)

    if not use_llm:
        # Deterministic lexical similarity scoring across topic name + description + keywords when offline from local LLM
        anchors = [a.lower().replace("*", "") for a in (facets_init.get("anatomical_anchors_en", []) + facets_init.get("topic_search_queries", [])[:6])]
        rx = re.compile("|".join(re.escape(a) for a in anchors if len(a) >= 3), flags=re.IGNORECASE) if anchors else re.compile(re.escape(topic_en), flags=re.IGNORECASE)
        cls = []
        for r in topics_df.itertuples(index=False):
            txt = f"{r.display_name} {r.keywords} {r.description}"
            hits = len(set(m.lower() for m in rx.findall(txt)))
            if hits >= 2 or topic_en.lower() in str(r.display_name).lower():
                cls.append("INCLUDE_CORE")
            elif hits == 1:
                cls.append("INCLUDE_ADJACENT")
            else:
                cls.append("EXCLUDE")
        topics_df["llm_class"] = cls
        topics_df["llm_reason"] = "lexical_relevance_fallback"
        return topics_df

    sys_p = (
        f"You are classifying OpenAlex Topics for the scientific field '{topic_en}'. "
        "Keep cross-disciplinary topics relevant to this domain even outside its main primary discipline (no domain cutoff). "
        "Return strict JSON: {\"items\": [{\"topic_id\": \"...\", \"class\": \"INCLUDE_CORE|INCLUDE_ADJACENT|EXCLUDE\", \"reason\": \"...\"}]}"
    )
    decisions: dict[str, tuple[str, str]] = {}
    rows = topics_df.to_dict("records")
    for start in range(0, len(rows), 25):
        batch = [{"topic_id": r["topic_id"], "display_name": r["display_name"], "subfield": r["subfield"], "domain": r["domain"], "keywords": r["keywords"][:160]} for r in rows[start : start + 25]]
        res = llm_chat_json(ep["llm_base_url"], api_key, ep["llm_model"], sys_p, "Classify:\n" + json.dumps(batch, ensure_ascii=False))
        for it in res.get("items", []):
            if it.get("topic_id"):
                decisions[it["topic_id"]] = (it.get("class", "EXCLUDE"), it.get("reason", ""))
    topics_df["llm_class"] = [decisions.get(tid, ("EXCLUDE", ""))[0] for tid in topics_df["topic_id"]]
    topics_df["llm_reason"] = [decisions.get(tid, ("EXCLUDE", ""))[1] for tid in topics_df["topic_id"]]
    return topics_df


def fetch_mesh_entry_terms(mesh_roots: list[str]) -> dict[str, list[str]]:
    descriptors, entry_terms = [], []
    for root in mesh_roots[:8]:
        try:
            q = urllib.parse.urlencode({"db": "mesh", "term": f'"{root}"[MeSH Terms]', "retmax": "120", "retmode": "json"})
            ids = http_get_json(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{q}").get("esearchresult", {}).get("idlist", [])
            if not ids:
                continue
            req = urllib.request.Request(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=mesh&id={','.join(ids[:120])}&retmode=xml")
            with urllib.request.urlopen(req, timeout=30) as resp:
                xml_txt = resp.read().decode("utf-8", errors="ignore")
            for m in re.findall(r"<DescriptorName><String>(.*?)</String></DescriptorName>", xml_txt):
                descriptors.append(m.strip())
            for m in re.findall(r"<Term[^>]*><String>(.*?)</String>", xml_txt):
                t = m.strip()
                if "," not in t and 3 <= len(t) <= 60:
                    entry_terms.append(t.lower())
        except Exception:
            continue
    return {"descriptors": list(dict.fromkeys(descriptors)), "entry_terms": list(dict.fromkeys(entry_terms))}


def discover_bradford_sources(core_topic_ids: list[str], email: str, oa_key: str | None) -> pd.DataFrame:
    if not core_topic_ids:
        return pd.DataFrame()
    top_str = "|".join(core_topic_ids[:25])
    params: dict[str, str] = {"filter": f"primary_topic.id:{top_str},publication_year:2000-2025", "group_by": "primary_location.source.id", "per-page": "100", "mailto": email}
    if oa_key:
        params["api_key"] = oa_key
    try:
        groups = http_get_json("https://api.openalex.org/works?" + urllib.parse.urlencode(params)).get("group_by", [])
    except Exception:
        groups = []
    rows = []
    for g in groups[:35]:
        sid = str(g.get("key", "")).split("/")[-1]
        if not sid.startswith("S"):
            continue
        cnt = int(g.get("count") or 0)
        try:
            s_info = http_get_json(f"https://api.openalex.org/sources/{sid}?" + urllib.parse.urlencode({"mailto": email}))
            tot_works = int(s_info.get("works_count") or 1)
            rows.append({
                "source_id": sid,
                "display_name": s_info.get("display_name", g.get("key_display_name", "")),
                "works_in_core_topics": cnt,
                "total_works_count": tot_works,
                "core_share": round(cnt / max(1, tot_works), 3),
                "source_class": "PURE_DOMAIN_JOURNAL" if (cnt / max(1, tot_works)) >= 0.50 else "MULTIDISCIPLINARY_OR_MIXED",
            })
        except Exception:
            continue
    return pd.DataFrame(rows)


def differential_pearl_growing(core_topic_ids: list[str], email: str, oa_key: str | None, cfg: dict, sample_n: int = 800) -> dict[str, Any]:
    y0, y1 = cfg["scope"]["year_start"], cfg["scope"]["year_end"]
    cc = (cfg["scope"].get("geo_country_code") or "").strip().upper()
    cc_flt = f",authorships.countries:{cc}" if cc else ""
    top_str = "|".join(core_topic_ids[:25])

    def _fetch_texts(flt: str, target_n: int, seed: int) -> list[str]:
        texts, cursor = [], "*"
        while len(texts) < target_n and cursor:
            params: dict[str, str] = {"filter": flt, "per-page": "200", "cursor": cursor, "select": "title,abstract_inverted_index,keywords", "mailto": email}
            if oa_key:
                params["api_key"] = oa_key
            try:
                data = http_get_json("https://api.openalex.org/works?" + urllib.parse.urlencode(params), timeout=25)
            except Exception:
                if "api_key" in params:
                    params.pop("api_key", None)
                    try:
                        data = http_get_json("https://api.openalex.org/works?" + urllib.parse.urlencode(params), timeout=25)
                    except Exception:
                        break
                else:
                    break
            res = data.get("results", [])
            if not res:
                break
            for w in res:
                inv = w.get("abstract_inverted_index") or {}
                pairs = sorted((pos, word) for word, poss in inv.items() for pos in poss)
                ab = " ".join(word for _, word in pairs)
                kw = " ".join((k.get("display_name", "") if isinstance(k, dict) else str(k)) for k in (w.get("keywords") or []))
                texts.append(f"{w.get('title', '')} {ab} {kw}".strip())
            cursor = (data.get("meta") or {}).get("next_cursor")
            if len(res) < 200:
                break
        return texts[:target_n]

    cc_name = (cfg["scope"].get("geo_country_name") or "").strip().lower()
    cc_code = (cfg["scope"].get("geo_country_code") or "").strip().lower()
    extra_geo_stops = {x for x in (cc_name, cc_code, "mexico", "méxico") if x}
    SPANISH_AND_ACADEMIC_STOPWORDS = frozenset(ENGLISH_STOP_WORDS) | extra_geo_stops | frozenset({
        "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un", "para",
        "con", "no", "una", "su", "al", "lo", "como", "mas", "más", "pero", "sus", "le", "ya",
        "o", "este", "si", "sí", "porque", "esta", "entre", "cuando", "muy", "sin", "sobre",
        "tambien", "también", "me", "hasta", "hay", "donde", "quien", "desde", "todo", "nos",
        "durante", "todos", "uno", "les", "ni", "contra", "otros", "ese", "eso", "ante", "ellos",
        "e", "esto", "mi", "antes", "algunos", "unos", "yo", "otro", "otras", "otra", "el", "él",
        "tanto", "esa", "estos", "mucho", "quienes", "nada", "muchos", "cual", "poco", "ella",
        "estar", "estas", "algunas", "algo", "nosotros", "mis", "tu", "te", "ti", "ellas", "nosotras",
        "vosotros", "vosotras", "os", "mia", "mía", "mio", "mío", "tuyo", "tuya", "suyo", "suya",
        "nuestro", "nuestra", "vuestro", "vuestra", "esos", "esas", "estoy", "estas", "esta", "está",
        "estamos", "estan", "están", "estuve", "estuvo", "estuvieron", "era", "eramos", "eran",
        "fue", "fuimos", "fueron", "ser", "es", "son", "sido", "siendo", "sea", "sean", "han",
        "ha", "he", "hemos", "habia", "había", "hubo", "mediante", "hacia", "bajo", "tras",
        "segun", "según", "embargo", "ademas", "además", "cada", "todas", "solo", "sólo", "mismo",
        "misma", "mismos", "mismas", "puede", "pueden", "pudo", "cuales", "donde", "dónde", "cuya",
        "cuyo", "cuyos", "cuyas", "aqui", "aquí", "asi", "así", "aunque", "debido", "respecto",
        "patients", "patient", "study", "studies", "results", "result", "methods", "method",
        "conclusions", "conclusion", "background", "objective", "objectives", "year", "years",
        "using", "used", "use", "based", "analysis", "analyses", "group", "groups", "factor",
        "factors", "risk", "data", "case", "cases", "control", "controls", "associated",
        "significantly", "significant", "evaluated", "assessed", "compared", "included", "total",
        "mean", "high", "higher", "low", "lower", "showed", "found", "observed", "however",
        "although", "therefore", "introduction", "discussion", "abstract", "clinical", "disease",
        "diseases", "severe", "acute", "chronic", "treatment", "diagnosis", "prevalence",
        "severity", "symptoms", "review", "effect", "effects", "level", "levels", "rate", "rates",
        "day", "days", "week", "weeks", "month", "months", "time", "times", "age", "ages",
        "child", "children", "adult", "adults", "women", "men", "human", "humans", "sample",
        "samples", "population", "populations", "care", "hospital", "hospitalized", "mortality",
        "cell", "cells", "trial", "trials", "mexico", "méxico",
        "estudio", "estudios", "resultados", "resultado", "objetivo", "objetivos", "conclusiones",
        "conclusion", "conclusión", "metodos", "métodos", "metodo", "método", "pacientes",
        "paciente", "grupo", "grupos", "analisis", "análisis", "datos", "casos", "caso",
        "tratamiento", "diagnostico", "diagnóstico", "prevalencia", "factores", "factor",
        "riesgo", "clinico", "clínico", "clinica", "clínica", "enfermedad", "enfermedades",
        "asociado", "asociada", "asociados", "asociadas", "presenta", "presentan", "mayor",
        "menor", "altos", "bajos", "total", "nivel", "niveles", "efecto", "efectos", "revision",
        "revisión", "articulo", "artículo", "resumen", "introduccion", "introducción",
    })

    pos_en = _fetch_texts(f"primary_topic.id:{top_str},publication_year:{y0}-{y1},has_abstract:true,language:en{cc_flt}", max(100, sample_n // 2), 11) if top_str else []
    pos_es = _fetch_texts(f"primary_topic.id:{top_str},publication_year:{y0}-{y1},language:es{cc_flt}", max(80, sample_n // 3), 12) if top_str else []
    excl_top = ",".join(f"primary_topic.id:!{t}" for t in core_topic_ids[:10])
    bg_flt = f"publication_year:{y0}-{y1},has_abstract:true,language:en{cc_flt}" + (f",{excl_top}" if excl_top else "")
    bg_en = _fetch_texts(bg_flt, max(100, sample_n // 2), 13)
    bg_es_flt = f"publication_year:{y0}-{y1},language:es{cc_flt}" + (f",{excl_top}" if excl_top else "")
    bg_es = _fetch_texts(bg_es_flt, max(80, sample_n // 3), 14)

    def extract_top_log_odds(pos_docs: list[str], bg_docs: list[str], min_df: int = 4, top_k: int = 60) -> list[str]:
        if len(pos_docs) < 15 or len(bg_docs) < 15:
            return []
        vec = CountVectorizer(ngram_range=(1, 2), min_df=min_df, max_df=0.65, token_pattern=r"(?u)\b[a-zA-ZáéíóúñÁÉÍÓÚÑ][a-zA-Z0-9áéíóúñÁÉÍÓÚÑ\-]{2,}\b")
        X = vec.fit_transform(pos_docs + bg_docs)
        terms = vec.get_feature_names_out()
        n_p = len(pos_docs)
        c_p = np.asarray(X[:n_p].sum(axis=0)).ravel()
        c_b = np.asarray(X[n_p:].sum(axis=0)).ravel()
        alpha = 10.0
        p1 = (c_p + alpha) / (c_p.sum() + alpha * len(terms))
        p2 = (c_b + alpha) / (c_b.sum() + alpha * len(terms))
        z = (np.log(p1 / (1 - p1)) - np.log(p2 / (1 - p2))) / np.sqrt(1.0 / (c_p + alpha) + 1.0 / (c_b + alpha))
        out = []
        for idx in np.argsort(-z):
            t = terms[idx].lower().strip()
            toks = t.split()
            if t in SPANISH_AND_ACADEMIC_STOPWORDS or all(w in SPANISH_AND_ACADEMIC_STOPWORDS for w in toks):
                continue
            if len(toks) == 2 and (toks[0] in SPANISH_AND_ACADEMIC_STOPWORDS or toks[1] in SPANISH_AND_ACADEMIC_STOPWORDS):
                continue
            if len(t) < 4 or t.isdigit() or c_p[idx] < min_df:
                continue
            out.append(t)
            if len(out) >= top_k:
                break
        return out

    return {
        "en_terms": extract_top_log_odds(pos_en, bg_en, min_df=5, top_k=60),
        "es_terms": extract_top_log_odds(pos_es, bg_es, min_df=3, top_k=45),
        "sample_corpus": {"pos_en": pos_en, "pos_es": pos_es, "bg_en": bg_en, "bg_es": bg_es},
    }


def synthesize_bilingual_blocks(cfg: dict, api_key: str, mesh_data: dict, topics_df: pd.DataFrame, pearl_terms: dict, facets_init: dict, out_dir: Path, llm_mode: str) -> dict[str, list[str]]:
    ep = cfg["endpoints"]
    topic_en = cfg["domain"]["seed_topic_en"]
    topic_es = cfg["domain"]["seed_topic_es"]
    top_names = topics_df[topics_df["llm_class"].isin(["INCLUDE_CORE", "INCLUDE_ADJACENT"])]["display_name"].tolist() if not topics_df.empty else []

    sys_p = (
        f"You are an expert information retrieval specialist creating a ~100% RECALL bilingual search dictionary for '{topic_en}' / '{topic_es}'. "
        "Never use wildcard '*' on a stem shorter than 4 chars. Place short acronyms (<=3 chars), country names, or generic/ambiguous cross-domain single words "
        "(e.g., cell, cells, cancer, care, days, children, hospital, therapy, expression, mortality, model, water, energy) in coupled_context_terms_*. "
        "Put ONLY field-specific terms in free_terms_*. Output ONLY strict valid JSON."
    )
    usr_p = f"""Synthesize clean bilingual search blocks from these clean-room inputs:
Topics ({len(top_names)}): {', '.join(top_names[:25])}
MeSH Descriptors: {', '.join(mesh_data.get('descriptors', [])[:25])}
MeSH Entry Terms: {', '.join(mesh_data.get('entry_terms', [])[:25])}
Pearl Growing EN (Log-Odds): {', '.join(pearl_terms.get('en_terms', [])[:45])}
Pearl Growing ES (Log-Odds): {', '.join(pearl_terms.get('es_terms', [])[:35])}
Anchors EN: {', '.join(facets_init.get('anatomical_anchors_en', []))}
Anchors ES: {', '.join(facets_init.get('anatomical_anchors_es', []))}

Return strict JSON with keys: "free_terms_en", "free_terms_es", "coupled_context_terms_en", "coupled_context_terms_es".
"""
    if llm_mode in ("auto", "local") and llm_endpoint_alive(ep["llm_base_url"], api_key):
        res = llm_chat_json(ep["llm_base_url"], api_key, ep["llm_model"], sys_p, usr_p)
        if res and ("free_terms_en" in res or "free_terms_es" in res):
            return res

    if llm_mode == "agent":
        pdir = out_dir / "agent_prompts"
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir / "02_lex_blocks_prompt.json").write_text(json.dumps({"system": sys_p, "user": usr_p, "target_file": str(out_dir / "lex_blocks_raw.json")}, indent=2), encoding="utf-8")

    # Deterministic synthesis directly from Pearl Growing + MeSH + Topic names + User facets
    free_en = list(dict.fromkeys([topic_en.lower()] + facets_init.get("anatomical_anchors_en", []) + pearl_terms.get("en_terms", [])[:45] + mesh_data.get("entry_terms", [])[:25]))
    free_es = list(dict.fromkeys([topic_es.lower()] + facets_init.get("anatomical_anchors_es", []) + pearl_terms.get("es_terms", [])[:35]))
    return {
        "free_terms_en": [t for t in free_en if len(t) >= 4],
        "free_terms_es": [t for t in free_es if len(t) >= 4],
        "coupled_context_terms_en": [t for t in free_en if len(t) <= 3],
        "coupled_context_terms_es": [t for t in free_es if len(t) <= 3],
    }


def audit_term_specificity(
    terms: list[str],
    lang_lbl: str,
    role_proposed: str,
    topic_ids: list[str],
    cfg: dict,
    email: str,
    oa_key: str | None,
    pearl_terms: dict | None,
    online_term_audit: bool = False,
) -> list[dict]:
    th = cfg["strategy_generation"]
    sample_corpus = (pearl_terms or {}).get("sample_corpus") or {}
    pos_docs = [str(x).lower() for x in (sample_corpus.get("pos_es" if lang_lbl == "es" else "pos_en") or [])]
    bg_docs = [str(x).lower() for x in (sample_corpus.get("bg_es" if lang_lbl == "es" else "bg_en") or [])]

    def _local_sample_counts(t_norm: str, has_wc: bool) -> tuple[int, int, float]:
        if not pos_docs and not bg_docs:
            return 25, 23, 0.92
        base = re.escape(t_norm.replace("*", ""))
        rx = re.compile(rf"\b{base}" + (r"\w*" if has_wc else r"\b"), flags=re.IGNORECASE)
        p_hits = sum(1 for d in pos_docs if rx.search(d))
        b_hits = sum(1 for d in bg_docs if rx.search(d))
        tot = p_hits + b_hits
        if tot == 0:
            return 1, 1, 0.85
        return tot, p_hits, float((p_hits + 0.5) / (tot + 1.0))

    audit_stopwords = frozenset(ENGLISH_STOP_WORDS) | frozenset({
        "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un", "para",
        "con", "no", "una", "su", "al", "lo", "como", "mas", "más", "pero", "sus", "le", "ya",
        "este", "si", "sí", "porque", "esta", "entre", "cuando", "muy", "sin", "sobre", "tambien",
        "también", "hasta", "hay", "donde", "desde", "todo", "durante", "todos", "uno", "contra",
        "otros", "ese", "eso", "ante", "ellos", "esto", "antes", "algunos", "unos", "otro", "otras",
        "otra", "tanto", "esa", "estos", "están", "fue", "fueron", "ser", "son", "sido", "siendo",
        "mediante", "hacia", "bajo", "tras", "segun", "según", "embargo", "ademas", "además",
        "patients", "study", "studies", "results", "methods", "conclusions", "background",
        "objective", "year", "years", "using", "based", "analysis", "group", "groups", "factors",
        "estudio", "resultados", "objetivo", "conclusiones", "pacientes", "metodos", "métodos",
    })
    rows = []
    for raw_t in dict.fromkeys(terms):
        t = str(raw_t).strip()
        if not t:
            continue
        unsafe = any(len(part) < th["min_truncation_stem_chars"] for part in re.findall(r"([a-zA-ZáéíóúñÁÉÍÓÚÑ]+)\*", t))
        q_clean = t.replace("*", "").strip()
        q_low = q_clean.lower()
        q_toks = q_low.split()
        has_cjk = bool(re.search(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]", q_clean))
        min_len = 2 if has_cjk else 3
        if len(q_clean) < min_len or unsafe:
            rows.append({"term": t, "lang": lang_lbl, "proposed_role": role_proposed, "sample_hits": 0, "sample_pos_hits": 0, "topic_specificity": 0.0, "final_action": "REJECT_UNSAFE_WILDCARD" if unsafe else "REJECT_TOO_SHORT"})
            continue
        if q_low in audit_stopwords or (q_toks and all(w in audit_stopwords for w in q_toks)):
            rows.append({"term": t, "lang": lang_lbl, "proposed_role": role_proposed, "sample_hits": 0, "sample_pos_hits": 0, "topic_specificity": 0.0, "final_action": "REJECT_STOPWORD"})
            continue
        if role_proposed == "FREE_OR_EXTRA":
            rows.append({"term": t, "lang": lang_lbl, "proposed_role": role_proposed, "sample_hits": -1, "sample_pos_hits": -1, "topic_specificity": 0.95, "final_action": "FREE_OR"})
            continue
        has_wc = "*" in t
        if (not has_cjk and " " not in q_clean and not has_wc and len(q_clean) <= 3) or role_proposed == "COUPLED":
            rows.append({"term": t, "lang": lang_lbl, "proposed_role": role_proposed, "sample_hits": -1, "sample_pos_hits": -1, "topic_specificity": 0.35 if role_proposed != "COUPLED" else -1.0, "final_action": "COUPLE_PROXIMITY"})
            continue
        if " " in q_clean and not has_wc:
            rows.append({"term": t, "lang": lang_lbl, "proposed_role": role_proposed, "sample_hits": -1, "sample_pos_hits": -1, "topic_specificity": 0.95, "final_action": "FREE_OR"})
            continue

        tot, phits, spec = _local_sample_counts(q_clean, has_wc)
        b_hits = max(0, tot - phits)
        bg_rate = b_hits / max(1, len(bg_docs)) if bg_docs else 0.0
        est_global_hits = int(round(bg_rate * 1200000))
        max_free_hits = int(th.get("max_hits_for_free_or", 8500))
        single_word_min_spec = max(0.88, float(th["min_topic_specificity_for_free_or"]))
        if (
            (has_wc and spec < 0.50)
            or (tot >= 40 and spec < th["min_topic_specificity_for_free_or"])
            or (" " not in q_clean and tot >= 20 and spec < single_word_min_spec)
            or (" " not in q_clean and est_global_hits > max_free_hits and spec < 0.96)
        ):
            action = "COUPLE_PROXIMITY"
        else:
            action = "FREE_OR"
        rows.append({"term": t, "lang": lang_lbl, "proposed_role": role_proposed, "sample_hits": tot, "sample_pos_hits": phits, "topic_specificity": round(spec, 3), "final_action": action})
    print(f"   [Audit {lang_lbl}/{role_proposed} (LOCAL_0_API_CALLS)] {len(rows)} terms verified.")
    return rows


def translate_core_terms_multilingual(
    core_en_terms: list[str], extra_langs: list[str], cfg: dict, api_key: str, out_dir: Path, llm_mode: str
) -> dict[str, list[str]]:
    """Translates high-specificity FREE_OR core terms into extra target languages/scripts (zh, pt, fr, ru, ja, etc.)."""
    langs = [lc.strip().lower() for lc in extra_langs if lc.strip() and lc.strip().lower() not in ("en", "es")]
    if not langs or not core_en_terms:
        return {}
    seed_terms = [t.replace("*", "").strip() for t in core_en_terms if len(t.replace("*", "").strip()) >= 4][:15]
    if not seed_terms:
        return {}

    ep = cfg["endpoints"]
    topic_en = cfg["domain"]["seed_topic_en"]
    sys_p = (
        f"You are an expert multilingual scientific terminologist for '{topic_en}'. "
        "Translate unambiguous core scientific descriptors into each requested target language/script "
        "without wildcards '*'. Keep only high-specificity technical phrases (avoid broad common words). Return strict valid JSON."
    )
    usr_p = (
        f"Target language ISO codes: {', '.join(langs)}\n"
        f"Source English core terms ({len(seed_terms)}): {', '.join(seed_terms)}\n"
        "Return a JSON object mapping each ISO code key (e.g., \"zh\", \"pt\", \"fr\", \"ru\", \"ja\") "
        "to a list of 6-12 concise scientific equivalents in that script."
    )
    if llm_mode in ("auto", "local") and llm_endpoint_alive(ep["llm_base_url"], api_key):
        res = llm_chat_json(ep["llm_base_url"], api_key, ep["llm_model"], sys_p, usr_p)
        if isinstance(res, dict):
            out = {lc: [str(x).replace("*", "").strip() for x in (res.get(lc) or []) if str(x).strip()] for lc in langs}
            if any(out.values()):
                (out_dir / "extra_lang_translations.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
                return {k: v for k, v in out.items() if v}

    if llm_mode == "agent":
        pdir = out_dir / "agent_prompts"
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir / "03_extra_lang_prompt.json").write_text(json.dumps({"system": sys_p, "user": usr_p, "target_file": str(out_dir / "extra_lang_translations.json")}, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  [Host-Agent Mode] Emitted extra-language translation prompt for {langs} -> agent_prompts/03_extra_lang_prompt.json.")
    elif (out_dir / "extra_lang_translations.json").exists():
        loaded = json.loads((out_dir / "extra_lang_translations.json").read_text(encoding="utf-8"))
        return {lc: [str(x).strip() for x in (loaded.get(lc) or []) if str(x).strip()] for lc in langs if loaded.get(lc)}
    return {}


def fmt_q(term: str) -> str:
    return f'"{term}"' if (" " in term and not term.startswith('"')) else term


def compile_queries(
    audit_df: pd.DataFrame,
    anchors_en: list[str],
    anchors_es: list[str],
    topic_ids: list[str],
    pure_source_ids: list[str],
    pure_source_names: list[str],
    mesh_roots: list[str],
    cfg: dict,
    out_dir: Path,
) -> dict[str, dict[str, str]]:
    QueryValidator = load_query_validator()
    sc = cfg["scope"]
    y0, y1 = sc["year_start"], sc["year_end"]
    win = cfg["strategy_generation"]["proximity_window_words"]
    cc = (sc.get("geo_country_code") or "").strip().upper()
    c_name = (sc.get("geo_country_name") or cc).strip()

    free_en = audit_df[(audit_df["lang"] == "en") & (audit_df["final_action"] == "FREE_OR")]["term"].tolist()
    free_es = audit_df[(audit_df["lang"] == "es") & (audit_df["final_action"] == "FREE_OR")]["term"].tolist()
    coup_en = audit_df[(audit_df["lang"] == "en") & (audit_df["final_action"] == "COUPLE_PROXIMITY")]["term"].tolist()
    coup_es = audit_df[(audit_df["lang"] == "es") & (audit_df["final_action"] == "COUPLE_PROXIMITY")]["term"].tolist()
    extra_df = audit_df[(~audit_df["lang"].isin(["en", "es"])) & (audit_df["final_action"] == "FREE_OR")]
    free_extra_map: dict[str, list[str]] = {
        str(lg): grp["term"].tolist() for lg, grp in extra_df.groupby("lang")
    } if not extra_df.empty else {}

    anc_en_clean = [a for a in anchors_en if a not in set(coup_en + coup_es)] or anchors_en
    anc_es_clean = [a for a in anchors_es if a not in set(coup_en + coup_es)] or anchors_es
    free_en_str = " OR ".join(fmt_q(t) for t in free_en)
    free_es_str = " OR ".join(fmt_q(t) for t in free_es)
    anc_en_str = " OR ".join(fmt_q(t) for t in anc_en_clean)
    anc_es_str = " OR ".join(fmt_q(t) for t in anc_es_clean)
    coup_en_str = " OR ".join(fmt_q(t) for t in coup_en)
    coup_es_str = " OR ".join(fmt_q(t) for t in coup_es)
    clean_venues = [v.replace('"', "").strip() for v in pure_source_names if str(v).strip()][:25]
    venue_or_str = " OR ".join(f'"{v}"' for v in clean_venues)

    def _split_ch_terms(term_list: list[str]) -> tuple[str, list[str]]:
        re_parts, phrases = [], []
        for t in term_list:
            ts = t.strip()
            if not ts:
                continue
            wc = ts.endswith("*")
            base = ts[:-1] if wc else ts
            if " " in base:
                phrases.append(base.replace("'", ""))
            else:
                esc = re.escape(base).replace("'", "")
                re_parts.append(esc if wc else esc + r"\b")
        return ("(?i)\\b(?:" + "|".join(dict.fromkeys(re_parts)) + ")" if re_parts else ""), list(dict.fromkeys(phrases))

    geos = ["global"] + (["country"] if cc else [])
    results: dict[str, dict[str, str]] = {}
    for geo in geos:
        gdir = out_dir / "queries" / geo
        gdir.mkdir(parents=True, exist_ok=True)
        is_c = geo == "country" and bool(cc)

        # 1) Web of Science
        wos_clauses = []
        if venue_or_str:
            wos_clauses.append(f"SO=({venue_or_str})")
        if free_en_str:
            wos_clauses.append(f"TS=({free_en_str})")
        if free_es_str:
            wos_clauses.append(f"TS=({free_es_str})")
        if coup_en_str and anc_en_str:
            wos_clauses.append(f"TS=(({coup_en_str}) NEAR/{win} ({anc_en_str}))")
        if coup_es_str and anc_es_str:
            wos_clauses.append(f"TS=(({coup_es_str}) NEAR/{win} ({anc_es_str}))")
        wos_full = "(\n  " + "\n  OR ".join(wos_clauses) + f"\n)\nAND PY=({y0}-{y1})" + (f"\nAND CU=({c_name})" if is_c else "")
        (gdir / "wos_broad_100recall.txt").write_text(wos_full, encoding="utf-8")

        # 2) Scopus
        scp_clauses = []
        if venue_or_str:
            scp_clauses.append(f"SRCTITLE({venue_or_str})")
        if free_en_str:
            scp_clauses.append(f"TITLE-ABS-KEY({free_en_str})")
        if free_es_str:
            scp_clauses.append(f"TITLE-ABS-KEY({free_es_str})")
        if coup_en_str and anc_en_str:
            scp_clauses.append(f"TITLE-ABS-KEY(({coup_en_str}) W/{win} ({anc_en_str}))")
        if coup_es_str and anc_es_str:
            scp_clauses.append(f"TITLE-ABS-KEY(({coup_es_str}) W/{win} ({anc_es_str}))")
        scp_full = "(\n  " + "\n  OR ".join(scp_clauses) + f"\n)\nAND PUBYEAR > {y0 - 1} AND PUBYEAR < {y1 + 1}" + (f"\nAND AFFILCOUNTRY({c_name})" if is_c else "")
        (gdir / "scopus_broad.txt").write_text(scp_full, encoding="utf-8")

        # 3) PubMed
        pm_clauses = [f'"{m}"[MeSH Terms]' for m in mesh_roots]
        for t in free_en + free_es:
            pm_clauses.append(f"{fmt_q(t)}[tiab]")
        if coup_en and anc_en_clean:
            pm_clauses.append(f"(({' OR '.join(f'{fmt_q(t)}[tiab]' for t in coup_en)}) AND ({' OR '.join(f'{fmt_q(t)}[tiab]' for t in anc_en_clean)}))")
        if coup_es and anc_es_clean:
            pm_clauses.append(f"(({' OR '.join(f'{fmt_q(t)}[tiab]' for t in coup_es)}) AND ({' OR '.join(f'{fmt_q(t)}[tiab]' for t in anc_es_clean)}))")
        pm_full = "(\n  " + "\n  OR ".join(pm_clauses) + f"\n)\nAND ({y0}:{y1}[dp])"
        if is_c:
            neg_c = f' NOT "New {c_name}"[Affiliation]' if c_name.lower() == "mexico" else ""
            pm_full += f"\nAND ({c_name}[Affiliation]{neg_c})"
        (gdir / "pubmed_broad.txt").write_text(pm_full, encoding="utf-8")

        # 4) ClickHouse SQL (Optional local accelerator, ZERO JOINs)
        free_re, free_phr = _split_ch_terms(free_en + free_es)
        coup_re, coup_phr = _split_ch_terms(coup_en + coup_es)
        anc_re, anc_phr = _split_ch_terms(sorted(set(anc_en_clean + anc_es_clean)))
        use_mx_enriched = is_c and cc == "MX"
        ch_table = "rag.works_mexico_abstracts_enriched FINAL" if use_mx_enriched else "rag.works_flat"
        ch_text_col = (
            "concat(title, ' ', abstract_final, ' ', arrayStringConcat(keywords, ' '), ' ', arrayStringConcat(author_keywords, ' '))"
            if use_mx_enriched
            else "concat(title, ' ', abstract, ' ', arrayStringConcat(keywords, ' '))"
        )

        def _ch_re_phr(rx_s: str, phrs: list[str]) -> list[str]:
            parts = []
            if rx_s:
                parts.append(f"match({ch_text_col}, '{rx_s.replace(chr(92), chr(92)*2)}')")
            if phrs:
                phr_arr = ", ".join(f"'{p}'" for p in phrs)
                parts.append(f"multiSearchAnyCaseInsensitiveUTF8({ch_text_col}, [{phr_arr}])")
            return parts

        ch_conds = _ch_re_phr(free_re, free_phr)
        coup_parts = _ch_re_phr(coup_re, coup_phr)
        anc_parts = _ch_re_phr(anc_re, anc_phr)
        if coup_parts and anc_parts:
            ch_conds.append(f"(({' OR '.join(coup_parts)}) AND ({' OR '.join(anc_parts)}))")
        if pure_source_ids:
            ch_conds.append("replaceOne(source_id, 'https://openalex.org/', '') IN (" + ", ".join(f"'{sid}'" for sid in pure_source_ids) + ")")

        if use_mx_enriched:
            ch_select = "id, doi, pmid, pmcid, publication_year, type, language, is_oa, source_id, title, author_keywords, keywords, abstract_final, abstract_source, embedding_qwen"
            c_where = ""
            flat_topic_cond = ("replaceOne(topic_id, 'https://openalex.org/', '') IN (" + ", ".join(f"'{tid}'" for tid in topic_ids) + ")") if topic_ids else ""
            enriched_where = f"(publication_year BETWEEN {y0} AND {y1}) AND (\n    " + ("\n    OR ".join(ch_conds) if ch_conds else "1=0") + "\n  )"
            flat_topics_where = (
                f"(publication_year BETWEEN {y0} AND {y1}) AND has(country_codes, 'MX') AND ({flat_topic_cond})"
                if flat_topic_cond
                else ""
            )
            ch_sql = (
                f"-- ClickHouse Broad Query (MX Enriched, ZERO JOINs, Precomputed Qwen3-0.6B 1024d / Nomic 768d)\n"
                f"-- Note: embedding_nomic (Array(Float32), 768d) is also materialized in rag.works_mexico_abstracts_enriched.\n"
                f"SELECT {ch_select}\n"
                f"FROM {ch_table}\n"
                f"WHERE {enriched_where};\n"
            )
            if flat_topics_where:
                ch_sql += (
                    f"\n-- Companion OpenAlex Topic IDs slice from rag.works_flat (ZERO JOINs; merge IDs in Python):\n"
                    f"SELECT id\nFROM rag.works_flat\nWHERE {flat_topics_where};\n"
                )
        else:
            if topic_ids:
                ch_conds.append("replaceOne(topic_id, 'https://openalex.org/', '') IN (" + ", ".join(f"'{tid}'" for tid in topic_ids) + ")")
            c_where = f" AND has(country_codes, '{cc}')" if is_c else ""
            enriched_where = f"(publication_year BETWEEN {y0} AND {y1}){c_where} AND (\n    " + ("\n    OR ".join(ch_conds) if ch_conds else "1=0") + "\n  )"
            flat_topics_where = ""
            ch_sql = (
                f"-- Optional ClickHouse Broad Query ({geo.upper()}) | ZERO JOINs | No domain cutoff\n"
                f"SELECT id, doi, pmid, publication_year, type, language, source_id, title\n"
                f"FROM rag.works_flat\n"
                f"WHERE {enriched_where};\n"
            )
        (gdir / "clickhouse_broad.sql").write_text(ch_sql, encoding="utf-8")

        # 5) OpenAlex Web UI Manual Download Guide + 1-Click URLs
        oa_free_list = list(dict.fromkeys([fmt_q(t) for t in free_en + free_es]))
        geo_flt = f",authorships.institutions.country_code:{cc.lower()}" if is_c else ""
        top_pipe = "|".join(f"https://openalex.org/topics/{tid}" for tid in topic_ids[:45])
        src_pipe = "|".join(f"https://openalex.org/sources/{sid}" for sid in pure_source_ids[:25])
        url_topics = "https://openalex.org/works?page=1&filter=" + urllib.parse.quote(f"publication_year:{y0}-{y1}{geo_flt},primary_topic.id:{top_pipe}", safe=":,|/") if top_pipe else ""
        url_sources = "https://openalex.org/works?page=1&filter=" + urllib.parse.quote(f"publication_year:{y0}-{y1}{geo_flt},primary_location.source.id:{src_pipe}", safe=":,|/") if src_pipe else ""
        oa_free_chunk1 = " OR ".join(oa_free_list[:45])
        url_lex = "https://openalex.org/works?page=1&filter=" + urllib.parse.quote(f"publication_year:{y0}-{y1}{geo_flt},title_and_abstract.search.exact:({oa_free_chunk1})", safe=":()") if oa_free_chunk1 else ""

        oa_lines = [
            f"=== OPENALEX WEB UI — MANUAL DOWNLOAD ({geo.upper()}, {y0}-{y1}) ===",
            "Portal: https://openalex.org/works",
            "1. Open https://openalex.org/works and sign in (free) to enable Export -> CSV (up to 100,000 rows/export).",
            f"2. Filters: Year={y0}-{y1}" + (f", Institution Country={c_name} ({cc})" if is_c else ", Global (no country filter)") + ". Do NOT filter by Domain.",
            "3. Save exported CSV files into: ./delineation/inputs/openalex/ (ingested automatically in Phase 1).",
            "",
            "--- FREE-TERM SUB-QUERY (No wildcards: direct paste into OpenAlex Title & Abstract search) ---",
            " OR ".join(fmt_q(t.replace("*", "")) for t in (free_en + free_es) if len(t.replace("*", "")) >= 4),
            "",
            "--- DIRECT 1-CLICK BROWSER LINKS ---",
        ]
        if url_topics:
            oa_lines.append(f"[Link 1 - Discovered Topics ({min(45, len(topic_ids))})]:\n{url_topics}")
        if url_sources:
            oa_lines.append(f"\n[Link 2 - Core Bradford Journals ({min(25, len(pure_source_ids))})]:\n{url_sources}")
        if url_lex:
            oa_lines.append(f"\n[Link 3 - Exact Title&Abstract Lexical Probe]:\n{url_lex}")
        if free_extra_map:
            extra_terms_flat = [fmt_q(t) for ts in free_extra_map.values() for t in ts][:30]
            if extra_terms_flat:
                url_extra = "https://openalex.org/works?page=1&filter=" + urllib.parse.quote(
                    f"publication_year:{y0}-{y1}{geo_flt},title_and_abstract.search:({' OR '.join(extra_terms_flat)})",
                    safe=":()",
                )
                oa_lines.append(f"\n[Link 4 - Extra Languages Probe ({','.join(free_extra_map.keys())})]:\n{url_extra}")
        (gdir / "openalex_web_manual.txt").write_text("\n".join(oa_lines), encoding="utf-8")

        # 6) OpenAlex REST API Spec
        oa_api_spec = {
            "geo_scope": geo,
            "base_filter": f"publication_year:{y0}-{y1}" + (f",authorships.countries:{cc}" if is_c else ""),
            "per_page": 200,
            "topic_ids": topic_ids,
            "pure_source_ids": pure_source_ids,
            "free_terms_en": free_en,
            "free_terms_es": free_es,
            "free_terms_extra": free_extra_map,
            "coupled_terms_en": coup_en,
            "coupled_terms_es": coup_es,
            "anchors_en": anc_en_clean,
            "anchors_es": anc_es_clean,
            "clickhouse": {
                "table": ch_table,
                "is_mx_enriched": use_mx_enriched,
                "enriched_where": enriched_where,
                "flat_topics_where": flat_topics_where,
            },
        }
        (gdir / "openalex_api_broad.json").write_text(json.dumps(oa_api_spec, indent=2, ensure_ascii=False), encoding="utf-8")

        vw = QueryValidator.validate(wos_full, lang="en")
        vs = QueryValidator.validate(scp_full, lang="en")
        results[geo] = {"wos_valid": str(vw["is_valid"]), "scopus_valid": str(vs["is_valid"])}
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", type=str, default=".")
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--topic-en", type=str, default=None)
    parser.add_argument("--topic-es", type=str, default=None)
    parser.add_argument("--year-from", type=int, default=None)
    parser.add_argument("--year-to", type=int, default=None)
    parser.add_argument("--country", type=str, default=None, help="Optional ISO-2 code e.g. MX, BR, US, or '' for Global")
    parser.add_argument("--country-name", type=str, default=None)
    parser.add_argument("--biomedical", choices=["true", "false"], default=None)
    parser.add_argument("--llm-base-url", type=str, default=None)
    parser.add_argument("--llm-model", type=str, default=None)
    parser.add_argument("--embedding-base-url", type=str, default=None)
    parser.add_argument("--embedding-model", type=str, default=None)
    parser.add_argument("--llm-mode", choices=["auto", "local", "agent"], default="auto", help="auto=use local LLM if online else deterministic+agent prompts; agent=zero local LLM required")
    parser.add_argument("--extra-langs", type=str, default="", help="Optional comma-separated extra ISO languages/scripts to translate core FREE_OR terms (e.g. pt,fr,zh,ru)")
    parser.add_argument("--reuse-stage4", action="store_true")
    parser.add_argument("--reuse-audit", action="store_true")
    args = parser.parse_args()

    wd = resolve_workdir(args.workdir)
    bio_flag = (args.biomedical == "true") if args.biomedical else None
    cfg, cfg_file = load_or_create_config(
        wd, config_path=args.config, topic_en=args.topic_en, topic_es=args.topic_es,
        year_from=args.year_from, year_to=args.year_to, country=args.country,
        country_name=args.country_name, biomedical=bio_flag,
        llm_base_url=args.llm_base_url, llm_model=args.llm_model,
        embedding_base_url=args.embedding_base_url, embedding_model=args.embedding_model,
    )
    env = load_env_vars(wd, cfg)
    api_key = env.get("LLM_API_KEY", "lm-studio")
    oa_key = env.get("OPENALEX_API_KEY")
    email = cfg["endpoints"]["openalex_mailto"]
    out_dir = phase_dir(wd, "fase0_estrategia")

    print(f"=== PHASE 0: STRATEGY CONSTRUCTION FOR '{cfg['domain']['seed_topic_en']}' (workdir={wd.name}) ===")
    if args.reuse_stage4 and (out_dir / "facets_init.json").exists() and (out_dir / "propuesta_topics_descubiertos.csv").exists():
        facets_init = json.loads((out_dir / "facets_init.json").read_text(encoding="utf-8"))
        topics_curated = pd.read_csv(out_dir / "propuesta_topics_descubiertos.csv")
        sources_df = pd.read_csv(out_dir / "propuesta_revistas_bradford.csv") if (out_dir / "propuesta_revistas_bradford.csv").exists() else pd.DataFrame()
        pearl_terms = json.loads((out_dir / "pearl_growing_terms.json").read_text(encoding="utf-8")) if (out_dir / "pearl_growing_terms.json").exists() else {"en_terms": [], "es_terms": [], "sample_corpus": {}}
        mesh_data = {"descriptors": [], "entry_terms": []}
    else:
        facets_init = generate_initial_discovery_facets(cfg, api_key, out_dir, args.llm_mode)
        (out_dir / "facets_init.json").write_text(json.dumps(facets_init, indent=2, ensure_ascii=False), encoding="utf-8")

        topics_raw = discover_openalex_topics(facets_init.get("topic_search_queries", []), email, oa_key)
        topics_curated = classify_topics(topics_raw, cfg, facets_init, api_key, out_dir, args.llm_mode)
        topics_curated.to_csv(out_dir / "propuesta_topics_descubiertos.csv", index=False)

        inc_topics_tmp = topics_curated[topics_curated["llm_class"].isin(["INCLUDE_CORE", "INCLUDE_ADJACENT"])] if not topics_curated.empty else pd.DataFrame()
        core_topics_tmp = topics_curated[topics_curated["llm_class"] == "INCLUDE_CORE"] if not topics_curated.empty else pd.DataFrame()
        mesh_roots = cfg["domain"].get("mesh_root_terms") or facets_init.get("mesh_root_terms", [])
        mesh_data = fetch_mesh_entry_terms(mesh_roots) if cfg["domain"].get("is_biomedical") and mesh_roots else {"descriptors": [], "entry_terms": []}
        sources_df = discover_bradford_sources(core_topics_tmp["topic_id"].tolist() if not core_topics_tmp.empty else [], email, oa_key)
        sources_df.to_csv(out_dir / "propuesta_revistas_bradford.csv", index=False)

        pearl_terms = differential_pearl_growing(
            core_topics_tmp["topic_id"].tolist() if not core_topics_tmp.empty else [],
            email, oa_key, cfg, sample_n=cfg["strategy_generation"]["pearl_growing_sample_size"],
        )
        (out_dir / "pearl_growing_terms.json").write_text(json.dumps(pearl_terms, indent=2, ensure_ascii=False), encoding="utf-8")

    inc_topics = topics_curated[topics_curated["llm_class"].isin(["INCLUDE_CORE", "INCLUDE_ADJACENT"])] if not topics_curated.empty else pd.DataFrame()
    pure_sources = sources_df[sources_df["source_class"] == "PURE_DOMAIN_JOURNAL"] if not sources_df.empty else pd.DataFrame()

    if args.reuse_audit and (out_dir / "lex_blocks_raw.json").exists() and (out_dir / "audit_terminos_especificidad.csv").exists():
        lex_blocks = json.loads((out_dir / "lex_blocks_raw.json").read_text(encoding="utf-8"))
        audit_df = pd.read_csv(out_dir / "audit_terminos_especificidad.csv")
    else:
        lex_blocks = synthesize_bilingual_blocks(cfg, api_key, mesh_data, topics_curated, pearl_terms, facets_init, out_dir, args.llm_mode)
        (out_dir / "lex_blocks_raw.json").write_text(json.dumps(lex_blocks, indent=2, ensure_ascii=False), encoding="utf-8")
        top_ids = inc_topics["topic_id"].tolist() if not inc_topics.empty else []
        coup_set = set(lex_blocks.get("coupled_context_terms_en", []) + lex_blocks.get("coupled_context_terms_es", []))
        en_free = [t for t in dict.fromkeys(facets_init.get("anatomical_anchors_en", []) + lex_blocks.get("free_terms_en", [])) if t not in coup_set]
        es_free = [t for t in dict.fromkeys(facets_init.get("anatomical_anchors_es", []) + lex_blocks.get("free_terms_es", [])) if t not in coup_set]
        rows = []
        rows.extend(audit_term_specificity(en_free, "en", "FREE_OR", top_ids, cfg, email, oa_key, pearl_terms))
        rows.extend(audit_term_specificity(es_free, "es", "FREE_OR", top_ids, cfg, email, oa_key, pearl_terms))
        rows.extend(audit_term_specificity(lex_blocks.get("coupled_context_terms_en", []), "en", "COUPLED", top_ids, cfg, email, oa_key, pearl_terms))
        rows.extend(audit_term_specificity(lex_blocks.get("coupled_context_terms_es", []), "es", "COUPLED", top_ids, cfg, email, oa_key, pearl_terms))
        audit_df = pd.DataFrame(rows).drop_duplicates(subset=["term", "lang"])

    extra_langs = [x.strip().lower() for x in args.extra_langs.split(",") if x.strip() and x.strip().lower() not in ("en", "es")]
    if extra_langs:
        core_en_free = audit_df[(audit_df["lang"] == "en") & (audit_df["final_action"] == "FREE_OR")]["term"].tolist()
        trans_map = translate_core_terms_multilingual(core_en_free, extra_langs, cfg, api_key, out_dir, args.llm_mode)
        extra_rows = []
        top_ids = inc_topics["topic_id"].tolist() if not inc_topics.empty else []
        for lg, tlist in trans_map.items():
            extra_rows.extend(audit_term_specificity(tlist, lg, "FREE_OR_EXTRA", top_ids, cfg, email, oa_key, pearl_terms))
        if extra_rows:
            audit_df = pd.concat([audit_df, pd.DataFrame(extra_rows)], ignore_index=True).drop_duplicates(subset=["term", "lang"])

    if not audit_df.empty and env.get("CLICKHOUSE_HOST"):
        try:
            import clickhouse_connect
            ch_pwd = (env.get("CLICKHOUSE_PASSWORD") or env.get("CLICKHOUSE_CLEAN_PASSWORD") or "").replace("$$", "$")
            ch_client = clickhouse_connect.get_client(
                host=env.get("CLICKHOUSE_HOST") or "localhost",
                port=int(env.get("CLICKHOUSE_PORT") or 8123),
                username=env.get("CLICKHOUSE_USER") or "default",
                password=ch_pwd,
                database=env.get("CLICKHOUSE_DATABASE") or "rag",
                connect_timeout=5,
                send_receive_timeout=60,
            )
            max_free_hits = int(cfg["strategy_generation"].get("max_hits_for_free_or", 8500))
            free_mask = (audit_df["final_action"] == "FREE_OR") & (~audit_df["term"].astype(str).str.strip().str.contains(" ", regex=False))
            cand_idx = audit_df[free_mask].index.tolist()
            if len(cand_idx) > 2:
                exprs = []
                for idx_r in cand_idx:
                    t_raw = str(audit_df.at[idx_r, "term"]).strip()
                    wc = t_raw.endswith("*")
                    base = re.escape(t_raw[:-1] if wc else t_raw).replace("'", "")
                    pat = (f"(?i)\\\\b{base}" if wc else f"(?i)\\\\b{base}\\\\b")
                    exprs.append(f"countIf(match(concat(title, ' ', abstract_final), '{pat}')) AS c_{idx_r}")
                q_cnt = f"SELECT {', '.join(exprs)} FROM rag.works_mexico_abstracts_enriched FINAL"
                row_cnt = ch_client.query(q_cnt).result_rows[0]
                hits_by_idx = {idx_r: int(val) for idx_r, val in zip(cand_idx, row_cnt)}
                # Keep at least top 2 most specific unigrams per language in FREE_OR
                protected_idx: set[int] = set()
                for lg_k, grp in audit_df.loc[cand_idx].groupby("lang"):
                    top2 = grp.sort_values(["topic_specificity", "sample_pos_hits"], ascending=[False, False]).head(2).index.tolist()
                    protected_idx.update(top2)
                demoted = 0
                for idx_r, ch_hits in hits_by_idx.items():
                    if ch_hits > max_free_hits and idx_r not in protected_idx:
                        audit_df.at[idx_r, "final_action"] = "COUPLE_PROXIMITY"
                        demoted += 1
                if demoted:
                    print(f"   [ClickHouse Frequency Guard] Demoted {demoted} hyper-frequent FREE_OR unigrams (> {max_free_hits:,} hits) to COUPLE_PROXIMITY.")
        except Exception as exc:
            print(f"   [ClickHouse Frequency Guard skipped] {exc}")

    audit_df.to_csv(out_dir / "audit_terminos_especificidad.csv", index=False)

    val = compile_queries(
        audit_df,
        facets_init.get("anatomical_anchors_en", []),
        facets_init.get("anatomical_anchors_es", []),
        inc_topics["topic_id"].tolist() if not inc_topics.empty else [],
        pure_sources["source_id"].tolist() if not pure_sources.empty else [],
        pure_sources["display_name"].tolist() if not pure_sources.empty else [],
        cfg["domain"].get("mesh_root_terms") or facets_init.get("mesh_root_terms", []),
        cfg,
        out_dir,
    )
    print(f"   Config saved: {cfg_file.name} | Query validation: {val}")

    from visual_artifacts import generate_phase_visuals
    generate_phase_visuals(0, wd, cfg)


if __name__ == "__main__":
    main()
