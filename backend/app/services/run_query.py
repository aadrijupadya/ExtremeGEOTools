from __future__ import annotations
import json
import time
from typing import List
from datetime import datetime

from ..schemas.query_schemas import QueryRequest, RunResponse
from .engines import call_engine
from .extract import extract_competitors, extract_links, to_domains
from .pricing import estimate_cost
from .csv_writer import append_run_to_csv
from ..routes.runs import _enrich_citations, _normalize_entities
from ..models.run import Run
from ..services.database import get_db

#script to run engine objects, extract competitors, links, and domains, and append to csv

def make_run_id(engine: str) -> str:
    return f"run_{engine}_{int(time.time() * 1000)}"


def run_single_engine(req: QueryRequest, eng: str, ts_iso: str) -> RunResponse:
    # Choose model per engine with sensible fallbacks
    selected_model = None
    if eng == 'openai':
        selected_model = getattr(req, 'openai_model', None) or getattr(req, 'model', None)
    elif eng == 'perplexity':
        selected_model = getattr(req, 'perplexity_model', None) or getattr(req, 'model', None)
    norm = call_engine(eng, req.query, req.temperature, selected_model)
    text = norm.get("text", "") or ""
    model = norm.get("model", "") or eng
    input_tokens = int(norm.get("input_tokens", 0) or 0)
    output_tokens = int(norm.get("output_tokens", 0) or 0)
    latency_ms = int(norm.get("latency_ms", 0) or 0)
    cost_raw = norm.get("cost_usd", None)
    cost_usd = estimate_cost(input_tokens, output_tokens, cost_raw, model)

    vendors = extract_competitors(text)
    links = extract_links(text)
    domains = to_domains(links)

    # Enrichment at write-time to avoid extra work on first view
    # Speed path: compute normalized citations without fetching titles; titles can be filled on first view
    citations_enriched = _enrich_citations(links, max_titles=0)
    entities_normalized = _normalize_entities([v.model_dump() for v in vendors])

    extreme_rank = None
    extreme_mentioned = False
    for idx, v in enumerate(vendors, start=1):
        if v.name.lower() == "extreme networks":
            extreme_mentioned = True
            extreme_rank = idx
            break

    run_id = make_run_id(eng)

    csv_row = {
        "ts": ts_iso,
        "run_id": run_id,
        "engine": eng,
        "model": model,
        "prompt_version": req.prompt_version,
        "intent": req.intent,
        "query": req.query,
        "status": "ok",
        "latency_ms": latency_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost_usd,
        "raw_excerpt": text,  # store full answer; UI will preview
        "vendors": [v.model_dump() for v in vendors],
        "links": links,
        "domains": domains,
        "citations_enriched": citations_enriched,
        "entities_normalized": entities_normalized,
        "extreme_mentioned": extreme_mentioned,
        "extreme_rank": extreme_rank,
    }
    
    # Save to CSV (legacy)
    append_run_to_csv(csv_row)
    
    # Save to database
    try:
        db = next(get_db())
        db_run = Run(
            id=run_id,
            ts=datetime.fromisoformat(ts_iso.replace('Z', '+00:00')),
            query=req.query,
            engine=eng,
            model=model,
            prompt_version=req.prompt_version,
            intent=req.intent,
            status="ok",
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            raw_excerpt=text[:1000],
            vendors=[v.model_dump() for v in vendors],
            links=links,
            domains=domains,
            citations_enriched=citations_enriched,
            entities_normalized=entities_normalized,
            extreme_mentioned=extreme_mentioned,
            extreme_rank=extreme_rank,
            deleted=False,
            source="manual"  # Mark as manual query
        )
        db.add(db_run)
        db.commit()
        print(f"✅ Saved manual run {run_id} to database")
    except Exception as e:
        print(f"⚠️  Failed to save to database: {e}")
        # Continue with CSV fallback

    return RunResponse(
        id=run_id,
        ts=ts_iso,
        query=req.query,
        intent=req.intent,
        engine=eng,
        model=model,
        prompt_version=req.prompt_version,
        status="ok",
        latency_ms=latency_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
        raw_excerpt=text[:1000],
        extreme_mentioned=extreme_mentioned,
        extreme_rank=extreme_rank,
        vendors=vendors,
        links=links,
        domains=domains,
    )


def run_single_engine_error(req: QueryRequest, eng: str, ts_iso: str, exc: Exception) -> RunResponse:
    run_id = make_run_id(eng)

    csv_row = {
        "ts": ts_iso,
        "run_id": run_id,
        "engine": eng,
        "model": "",
        "prompt_version": req.prompt_version,
        "intent": req.intent,
        "query": req.query,
        "status": f"error: {type(exc).__name__}",
        "latency_ms": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": 0.0,
        "raw_excerpt": str(exc),
        "vendors": json.dumps([]),
        "links": json.dumps([]),
        "domains": json.dumps([]),
        "extreme_mentioned": False,
        "extreme_rank": None,
    }
    append_run_to_csv(csv_row)

    return RunResponse(
        id=run_id,
        ts=ts_iso,
        query=req.query,
        intent=req.intent,
        engine=eng,
        model="",
        prompt_version=req.prompt_version,
        status="error",
        latency_ms=0,
        input_tokens=0,
        output_tokens=0,
        cost_usd=0.0,
        raw_excerpt="",
        extreme_mentioned=False,
        extreme_rank=None,
        vendors=[],
        links=[],
        domains=[],
    )