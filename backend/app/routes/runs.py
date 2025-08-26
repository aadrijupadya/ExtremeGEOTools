
#Handles logic to store individual query run data
from __future__ import annotations
from typing import Any, Dict, List
import json
import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
import requests
import string

# Optional fuzzy similarity fallback
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc, func
from sqlalchemy.orm import Session

from ..services.database import get_db
from ..models.run import Run


router = APIRouter(prefix="/runs", tags=["runs"])


def _coerce_json_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []
    return [] if value is None else list(value) if isinstance(value, (tuple, set)) else []

#convert Run object to dictionary
def _serialize_run(row: Run, include_details: bool = False) -> Dict[str, Any]:
    base = {
        "id": row.id,
        "ts": row.ts.isoformat() if row.ts else None,
        "engine": row.engine,
        "model": row.model,
        "prompt_version": row.prompt_version,
        "intent": row.intent,
        "is_branded": bool(getattr(row, "is_branded", False)),
        "query": row.query,
        "status": row.status,
        "latency_ms": row.latency_ms,
        "input_tokens": row.input_tokens,
        "output_tokens": row.output_tokens,
        "cost_usd": float(row.cost_usd or 0.0),
    }
    if include_details:
        base.update(
            {
                "raw_excerpt": row.raw_excerpt or "",
                "vendors": _coerce_json_list(row.vendors),
                "links": _coerce_json_list(row.links),
                "domains": _coerce_json_list(row.domains),
                "extreme_mentioned": bool(row.extreme_mentioned),
                "extreme_rank": row.extreme_rank,
            }
        )
    else:
        base.update({"preview": (row.raw_excerpt or "")[:280]})
    return base


_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)

#normalize url to remove tracking params and www.
def _normalize_url(url: str) -> str:
    try:
        p = urlparse(url)
        # drop tracking params
        q = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not k.lower().startswith(("utm_", "gclid", "fbclid"))]
        new = p._replace(query=urlencode(q), fragment="")
        # normalize scheme/netloc casing and strip www.
        netloc = (new.netloc or "").lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        new = new._replace(netloc=netloc)
        return urlunparse(new)
    except Exception:
        return url

#get domain from url using urlparse
def _domain_from_url(url: str) -> str:
    try:
        netloc = urlparse(url).netloc.lower()
        return netloc[4:] if netloc.startswith("www.") else netloc
    except Exception:
        return ""

#fetch title from url using requests scraping
def _fetch_title(url: str, timeout: float = 2.0) -> str | None:
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0 (compatible; EGTBot/1.0)"})
        if resp.status_code >= 400:
            return None
        html = resp.text[:200000]  # guard large docs
        m = _TITLE_RE.search(html)
        if m:
            title = re.sub(r"\s+", " ", m.group(1)).strip()
            return title[:300]
    except Exception:
        return None
    return None

#enriching citations by fetching titles from urls
def _enrich_citations(links: List[str], max_titles: int = 10) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    seen = set()
    for rank, raw in enumerate(links or [], start=1):
        if not isinstance(raw, str) or not raw:
            continue
        url_n = _normalize_url(raw)
        if url_n in seen:
            continue
        seen.add(url_n)
        item = {
            "url": url_n,
            "domain": _domain_from_url(url_n),
            "rank": rank,
            "title": None,
        }
        out.append(item)

    # fetch a few titles
    for i, item in enumerate(out[:max_titles]):
        t = _fetch_title(item["url"]) or None
        if t:
            item["title"] = t
    return out

#list runs
@router.get("")
def list_runs(limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0), db: Session = Depends(get_db)) -> Dict[str, Any]:
    stmt = select(Run).where(Run.deleted.is_(False)).order_by(desc(Run.ts)).limit(limit).offset(offset)
    rows: List[Run] = list(db.scalars(stmt).all())
    data = [_serialize_run(r, include_details=False) for r in rows]
    return {"items": data, "limit": limit, "offset": offset}

#fetch run using unique id
@router.get("/{run_id}")
def get_run(run_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    row: Run | None = db.get(Run, run_id)
    if not row:
        raise HTTPException(status_code=404, detail="Run not found")
    if row.deleted:
        raise HTTPException(status_code=404, detail="Run not found")
    data = _serialize_run(row, include_details=True)

    # Use cached enrichment if available; otherwise compute and persist for future requests
    citations_cached = row.citations_enriched or []
    entities_cached = row.entities_normalized or []
    if citations_cached and entities_cached:
        data["citations"] = citations_cached
        data["entities"] = entities_cached
        return data

    # Prefer enriched citations cached at write-time; backfill if missing.
    if row.citations_enriched:
        data["citations"] = row.citations_enriched
    else:
        links = data.get("links") or []
        data["citations"] = _enrich_citations(links)
    entities = row.entities_normalized or _normalize_entities(data.get("vendors") or [])

    # persist back
    if not row.citations_enriched or not row.entities_normalized:
        try:
            row.citations_enriched = data["citations"]
            row.entities_normalized = entities
            db.add(row)
            db.commit()
        except Exception:
            db.rollback()

    data["entities"] = entities
    return data

#delete run functionality
@router.delete("/{run_id}")
def delete_run(run_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    row: Run | None = db.get(Run, run_id)
    if not row or row.deleted:
        raise HTTPException(status_code=404, detail="Run not found")
    try:
        row.deleted = True
        db.add(row)
        db.commit()
        return {"ok": True, "id": run_id}
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete run")

#extracting entities from response
def _normalize_entities(vendors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    seen = set()
    for v in vendors or []:
        name_raw = (v or {}).get("name") or ""
        if not isinstance(name_raw, str) or not name_raw.strip():
            continue
        name = name_raw.strip()
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        is_brand = (key == "extreme networks")
        out.append({
            "name": name,
            "type": "company",
            "is_brand": is_brand,
            "is_competitor": not is_brand,
        })
    return out

#lookup runs using search filters prompted by user
@router.post("/lookup")
def lookup_runs(payload: Dict[str, Any], db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Find same-day runs for the exact query text (case-insensitive), optionally filtered by engines.
    Returns latest per engine, most recent first.
    """
    query_text = (payload.get("query") or "").strip()
    engines = payload.get("engines") or []
    if not query_text:
        return {"matches": []}

    # same-day in UTC
    # WHERE date(ts AT TIME ZONE 'UTC') = CURRENT_DATE
    stmt = select(Run).where(
        func.date(func.timezone('UTC', Run.ts)) == func.current_date(),
    ).order_by(desc(Run.ts))

    rows_today: List[Run] = list(db.scalars(stmt).all())

    def _normalize_text(s: str) -> str:
        s = (s or "").lower().strip()
        # collapse whitespace
        s = re.sub(r"\s+", " ", s)
        # strip surrounding quotes
        s = s.strip("'\"")
        # remove simple punctuation except in URLs; since we compare queries, drop most punctuation
        allowed = set(string.ascii_lowercase + string.digits + " ")
        s = "".join(ch if ch in allowed else " " for ch in s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    q_norm = _normalize_text(query_text)

    # 1) Exact normalized match per engine (latest)
    exact_matches: Dict[str, Dict[str, Any]] = {}
    for r in rows_today:
        if engines and r.engine not in engines:
            continue
        if _normalize_text(r.query) == q_norm and r.engine not in exact_matches:
            exact_matches[r.engine] = {"id": r.id, "engine": r.engine, "ts": r.ts.isoformat()}

    if exact_matches:
        ordered = []
        added = set()
        for r in rows_today:
            if r.engine in exact_matches and r.engine not in added:
                ordered.append(exact_matches[r.engine])
                added.add(r.engine)
        return {"matches": ordered}

    # 2) Fuzzy fallback using TF-IDF cosine similarity
    # Build corpus: [query_norm] + unique normalized texts from today
    candidates: List[tuple[str, Run]] = []
    seen_texts = set()
    for r in rows_today:
        if engines and r.engine not in engines:
            continue
        rn = _normalize_text(r.query)
        if not rn:
            continue
        key = (rn, r.engine)
        if key in seen_texts:
            continue
        seen_texts.add(key)
        candidates.append((rn, r))

    if not candidates:
        return {"matches": []}

    corpus = [q_norm] + [c[0] for c in candidates]
    try:
        vec = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        X = vec.fit_transform(corpus)
        sims = cosine_similarity(X[0:1], X[1:]).flatten()
    except Exception:
        sims = []

    # threshold for near-duplicate queries
    THRESH = 0.90
    scored = []
    for (norm_text, run_obj), score in zip(candidates, sims):
        if score >= THRESH:
            scored.append((score, run_obj))

    # choose latest per engine among high-score matches
    fuzzy_matches: Dict[str, Dict[str, Any]] = {}
    for _, r in sorted(scored, key=lambda x: x[1].ts, reverse=True):
        if r.engine not in fuzzy_matches:
            fuzzy_matches[r.engine] = {"id": r.id, "engine": r.engine, "ts": r.ts.isoformat()}

    ordered = []
    added = set()
    for r in rows_today:
        if r.engine in fuzzy_matches and r.engine not in added:
            ordered.append(fuzzy_matches[r.engine])
            added.add(r.engine)

    return {"matches": ordered}


