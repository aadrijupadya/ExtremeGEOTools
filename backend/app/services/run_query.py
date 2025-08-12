from __future__ import annotations
import json
import time
from typing import List

from ..schemas.query_schemas import QueryRequest, RunResponse
from .engines import call_engine
from .extract import extract_competitors, extract_links, to_domains
from .pricing import estimate_cost
from .csv_writer import append_run_to_csv


def make_run_id(engine: str) -> str:
    return f"run_{engine}_{int(time.time() * 1000)}"


def run_single_engine(req: QueryRequest, eng: str, ts_iso: str) -> RunResponse:
    norm = call_engine(eng, req.query, req.temperature)
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
        "raw_excerpt": text[:1500],
        "vendors": json.dumps([v.model_dump() for v in vendors]),
        "links": json.dumps(links),
        "domains": json.dumps(domains),
        "extreme_mentioned": extreme_mentioned,
        "extreme_rank": extreme_rank,
    }
    append_run_to_csv(csv_row)

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
        "raw_excerpt": "",
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