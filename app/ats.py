"""Transparent ATS-readiness estimate using BM25-style relevance plus evidence checks."""
import math
import re
from collections import Counter

STOP = {"the","and","for","with","from","that","this","you","your","are","our","will","job","role","team","years","year","work","skills","have","has","using","into","their","who","all","not","but","a","an","of","to","in","on","at","is","as","be","or","we"}
VERBS = {"built","led","designed","developed","implemented","improved","reduced","increased","created","delivered","managed","optimized","launched","analyzed","automated","collaborated","engineered","directed","deployed"}

def words(text): return [w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9+#.\-]{1,}", text) if w.lower() not in STOP]
def flatten(resume): return resume.get("raw_text") or resume.get("summary", "")

def analyze(resume, job_description):
    text = flatten(resume); resume_terms = words(text); jd_terms = words(job_description)
    tf, qtf = Counter(resume_terms), Counter(jd_terms)
    ranked = [term for term, _ in qtf.most_common(45) if len(term) > 2]
    # Robertson BM25 term-frequency saturation (k1=1.2, b=0.75), normalized to 0..100.
    k1, b, dl, avgdl = 1.2, 0.75, max(len(resume_terms), 1), 650
    relevance, maximum = 0.0, 0.0
    for term in ranked:
        weight = 1.0 + math.log1p(qtf[term])
        value = tf[term] * (k1 + 1) / (tf[term] + k1 * (1 - b + b * dl / avgdl)) if tf[term] else 0
        relevance += weight * min(value, 1.0); maximum += weight
    relevance_score = round(100 * relevance / max(maximum, 1))
    matched = [term for term in ranked if tf[term]]; missing = [term for term in ranked if not tf[term]]
    lines = [line.strip(" •\t") for line in text.splitlines() if line.strip()]
    bullets = [line for line in lines if len(line) > 35 and (line[0] in "•-" or any(line.lower().startswith(v) for v in VERBS))]
    quantified = sum(bool(re.search(r"\d|%|\+", line)) for line in bullets)
    action_led = sum(any(line.lower().lstrip("•- ").startswith(v) for v in VERBS) for line in bullets)
    evidence_score = round(50 * quantified / max(len(bullets), 1) + 50 * action_led / max(len(bullets), 1))
    structure_terms = ("education", "experience", "skills", "project")
    structure_score = round(100 * sum(bool(re.search(rf"(?im)^.*{term}.*$", text)) for term in structure_terms) / len(structure_terms))
    score = round(0.70 * relevance_score + 0.20 * evidence_score + 0.10 * structure_score)
    return {
        "score": score,
        "formula": {"bm25_job_relevance": relevance_score, "evidence_quality": evidence_score, "resume_structure": structure_score, "weights": "70% BM25 relevance + 20% evidence + 10% structure"},
        "disclaimer": "Transparent ATS-readiness estimate; hiring platforms use proprietary parsers and do not publish a universal ATS score.",
        "matched_keywords": matched[:18], "missing_keywords": missing[:15],
        "bullet_metrics": {"total":len(bullets), "quantified":quantified, "action_led":action_led},
        "sources": [
            {"label":"Robertson & Zaragoza — BM25 and Beyond","url":"https://doi.org/10.1561/1500000019"},
            {"label":"O*NET occupational skills data","url":"https://www.onetcenter.org/content.html"}
        ],
        "recommendations": ["Add a missing skill only when it truthfully reflects your background.", "Use action-led, quantified bullets where the underlying evidence exists."]
    }
