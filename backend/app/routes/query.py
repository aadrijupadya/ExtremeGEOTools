#Query management endpoint with tools for running queries and logging them
from __future__ import annotations
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query as FQuery
from starlette.responses import StreamingResponse
import json
import time
import traceback
import os
import requests

from ..schemas.query_schemas import QueryRequest, QueryResponse
from ..services.run_query import run_single_engine, run_single_engine_error
from ..services.adapters.chatgpt_api import _get_openai_client
from ..services.extract import extract_competitors, extract_links, to_domains
from ..services.pricing import estimate_cost
from ..services.db_writer import persist_run_to_db
from ..services.run_query import make_run_id
from .runs import _enrich_citations, _normalize_entities

#query endpoint 
router = APIRouter(prefix="/query", tags=["query"])

#run query endpoint is when user provides a custom query and we run it through the provided model
@router.post("/run", response_model=QueryResponse)
def run_query(req: QueryRequest) -> QueryResponse:
    if not req.query or len(req.query.strip()) < 3: #validating query length
        raise HTTPException(status_code=400, detail="Query too short.")

    ts_iso = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    runs = []

    for eng in req.engines:
        try:
            runs.append(run_single_engine(req, eng, ts_iso))
        except Exception as e:
            runs.append(run_single_engine_error(req, eng, ts_iso, e))

    return QueryResponse(status="ok", runs=runs)

#endpoint to provide live streaming of query response (as model provides the tokens)
@router.get("/stream")
def stream_query(
    query: str = FQuery(min_length=3),
    model: str | None = None,
    intent: str | None = "unlabeled",
    temperature: float = 0.2,
    prompt_version: str = "v1",
    engine: str = "openai",
):
    """Stream OpenAI output via SSE (Chat Completions path). On completion, persist run and emit final run_id.

    Note: Currently optimized for non-GPT-5 models (e.g., gpt-4o-search-preview). GPT-5 streaming via Responses
    can be added once stable and supported consistently.
    """

    def sse_event(event: str, data: dict | str):
        payload = data if isinstance(data, str) else json.dumps(data)
        return f"event: {event}\ndata: {payload}\n\n"

    def gen():
        t0 = time.time()
        client = _get_openai_client()
        run_id = make_run_id("openai" if engine == "openai" else "perplexity")
        ts_iso = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        yield sse_event("start", {"run_id": run_id, "ts": ts_iso})

        full_text_parts: list[str] = []
        input_tokens = 0
        output_tokens = 0
        model_id = model or ("gpt-4o-search-preview" if engine == "openai" else "sonar")

        if engine == "openai":
            try:
                stream = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": "You are an AI search assistant. Include full URLs inline."},
                        {"role": "user", "content": query},
                    ],
                    max_tokens=500,
                    stream=True,
                    stream_options={"include_usage": True},
                )

                for chunk in stream:
                    try:
                        choices = getattr(chunk, "choices", None) or []
                        delta = None
                        if choices:
                            first = choices[0]
                            msg_delta = getattr(first, "delta", None)
                            if msg_delta is None and isinstance(first, dict):
                                msg_delta = first.get("delta")
                            delta = getattr(msg_delta, "content", None) if msg_delta is not None else None
                            if delta is None and isinstance(msg_delta, dict):
                                delta = msg_delta.get("content")
                        if isinstance(delta, str) and delta:
                            full_text_parts.append(delta)
                            yield sse_event("delta", {"text": delta})
                        # capture usage if included in streaming chunks (final chunk usually)
                        try:
                            u = getattr(chunk, "usage", None)
                            if u:
                                input_tokens = int(getattr(u, "prompt_tokens", 0) or 0)
                                output_tokens = int(getattr(u, "completion_tokens", 0) or 0)
                        except Exception:
                            pass
                    except Exception:
                        continue

                # Persist final run
                text = "".join(full_text_parts)
                vendors = extract_competitors(text)
                links = extract_links(text)
                domains = to_domains(links)
                citations_enriched = _enrich_citations(links, max_titles=0)
                entities_normalized = _normalize_entities([v.model_dump() for v in vendors])

                latency_ms = int((time.time() - t0) * 1000)
                cost_usd = estimate_cost(input_tokens, output_tokens, None, model_id)

                csv_row = {
                    "ts": ts_iso,
                    "run_id": run_id,
                    "engine": "openai",
                    "model": model_id,
                    "prompt_version": prompt_version,
                    "intent": intent,
                    "query": query,
                    "status": "ok",
                    "latency_ms": latency_ms,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_usd": cost_usd,
                    "raw_excerpt": text,
                    "vendors": [v.model_dump() for v in vendors],
                    "links": links,
                    "domains": domains,
                    "citations_enriched": citations_enriched,
                    "entities_normalized": entities_normalized,
                    "extreme_mentioned": any((v.name or "").lower() == "extreme networks" for v in vendors),
                    "extreme_rank": next((i for i, v in enumerate(vendors, start=1) if (v.name or "").lower() == "extreme networks"), None),
                }
                persist_run_to_db(csv_row)
                yield sse_event("done", {"run_id": run_id})
            except Exception as e:
                # Log full traceback for visibility
                try:
                    print("STREAM ERROR:", repr(e))
                    traceback.print_exc()
                except Exception:
                    pass
                # Fallback: non-streaming completion
                try:
                    resp = client.chat.completions.create(
                        model=model_id,
                        messages=[
                            {"role": "system", "content": "You are an AI search assistant. Include full URLs inline."},
                            {"role": "user", "content": query},
                        ],
                        max_tokens=500,
                    )
                    content = ""
                    try:
                        choices = getattr(resp, "choices", None) or []
                        if choices:
                            first = choices[0]
                            msg = getattr(first, "message", None)
                            if msg is None and isinstance(first, dict):
                                msg = first.get("message")
                            content = getattr(msg, "content", None) if msg is not None else None
                            if content is None and isinstance(msg, dict):
                                content = msg.get("content")
                            if not isinstance(content, str):
                                content = ""
                    except Exception:
                        content = ""
                    if content:
                        yield sse_event("delta", {"text": content})
                        full_text_parts.append(content)
                    # usage if provided
                    try:
                        usage = getattr(resp, "usage", None)
                        if usage:
                            input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
                            output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
                    except Exception:
                        pass
                    # Persist final run after fallback
                    text = "".join(full_text_parts)
                    vendors = extract_competitors(text)
                    links = extract_links(text)
                    domains = to_domains(links)
                    citations_enriched = _enrich_citations(links, max_titles=0)
                    entities_normalized = _normalize_entities([v.model_dump() for v in vendors])
                    latency_ms = int((time.time() - t0) * 1000)
                    cost_usd = estimate_cost(input_tokens, output_tokens, None, model_id)
                    csv_row = {
                        "ts": ts_iso,
                        "run_id": run_id,
                        "engine": "openai",
                        "model": model_id,
                        "prompt_version": prompt_version,
                        "intent": intent,
                        "query": query,
                        "status": "ok",
                        "latency_ms": latency_ms,
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "cost_usd": cost_usd,
                        "raw_excerpt": text,
                        "vendors": [v.model_dump() for v in vendors],
                        "links": links,
                        "domains": domains,
                        "citations_enriched": citations_enriched,
                        "entities_normalized": entities_normalized,
                        "extreme_mentioned": any((v.name or "").lower() == "extreme networks" for v in vendors),
                        "extreme_rank": next((i for i, v in enumerate(vendors, start=1) if (v.name or "").lower() == "extreme networks"), None),
                    }
                    persist_run_to_db(csv_row)
                    yield sse_event("done", {"run_id": run_id})
                except Exception as e2:
                    # Include error type and message for frontend visibility
                    err_payload = {"message": str(e2), "type": type(e2).__name__}
                    try:
                        err_payload["trace"] = traceback.format_exc()[:2000]
                    except Exception:
                        pass
                    yield sse_event("error", err_payload)
        else:
            # Perplexity branch
            api_key = os.getenv('PERPLEXITY_API_KEY')
            if not api_key:
                yield sse_event("error", {"message": "PERPLEXITY_API_KEY not set"})
                return
            url = 'https://api.perplexity.ai/chat/completions'
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            }
            payload = {
                'model': model_id,
                'messages': [
                    {'role': 'user', 'content': query},
                ],
                'stream': True,
            }
            try:
                with requests.post(url, headers=headers, json=payload, stream=True, timeout=60) as resp:
                    resp.raise_for_status()
                    for raw_line in resp.iter_lines(decode_unicode=True):
                        if not raw_line:
                            continue
                        if raw_line.startswith(':'):
                            continue
                        if raw_line.startswith('data:'):
                            data_str = raw_line[5:].strip()
                            if data_str == '[DONE]':
                                break
                            try:
                                evt = json.loads(data_str)
                            except Exception:
                                continue
                            try:
                                choices = evt.get('choices') or []
                                if choices:
                                    ch0 = choices[0]
                                    delta = (ch0.get('delta') or {}).get('content')
                                    if isinstance(delta, str) and delta:
                                        full_text_parts.append(delta)
                                        yield sse_event('delta', {'text': delta})
                            except Exception:
                                pass
                            try:
                                usage = evt.get('usage') or {}
                                input_tokens = int(usage.get('prompt_tokens', input_tokens) or input_tokens)
                                output_tokens = int(usage.get('completion_tokens', output_tokens) or output_tokens)
                            except Exception:
                                pass
                # persist
                text = ''.join(full_text_parts)
                vendors = extract_competitors(text)
                links = extract_links(text)
                domains = to_domains(links)
                citations_enriched = _enrich_citations(links, max_titles=0)
                entities_normalized = _normalize_entities([v.model_dump() for v in vendors])
                latency_ms = int((time.time() - t0) * 1000)
                cost_usd = estimate_cost(input_tokens, output_tokens, None, model_id)
                csv_row = {
                    'ts': ts_iso,
                    'run_id': run_id,
                    'engine': 'perplexity',
                    'model': model_id,
                    'prompt_version': prompt_version,
                    'intent': intent,
                    'query': query,
                    'status': 'ok',
                    'latency_ms': latency_ms,
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens,
                    'cost_usd': cost_usd,
                    'raw_excerpt': text,
                    'vendors': [v.model_dump() for v in vendors],
                    'links': links,
                    'domains': domains,
                    'citations_enriched': citations_enriched,
                    'entities_normalized': entities_normalized,
                    'extreme_mentioned': any((v.name or '').lower() == 'extreme networks' for v in vendors),
                    'extreme_rank': next((i for i, v in enumerate(vendors, start=1) if (v.name or '').lower() == 'extreme networks'), None),
                }
                persist_run_to_db(csv_row)
                yield sse_event('done', {'run_id': run_id})
            except Exception as e:
                try:
                    print('PPLX STREAM ERROR:', repr(e))
                    traceback.print_exc()
                except Exception:
                    pass
                yield sse_event('error', {'message': str(e), 'type': type(e).__name__})

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

#separate logic for perplexity straming
@router.get("/stream_pplx")
def stream_query_perplexity(
    query: str = FQuery(min_length=3),
    model: str | None = None,
    intent: str | None = "unlabeled",
    temperature: float = 0.2,
    prompt_version: str = "v1",
):
    """Stream Perplexity tokens via SSE and persist the run on completion."""

    def sse_event(event: str, data: dict | str):
        payload = data if isinstance(data, str) else json.dumps(data)
        return f"event: {event}\ndata: {payload}\n\n"

    def gen():
        t0 = time.time()
        api_key = os.getenv('PERPLEXITY_API_KEY')
        if not api_key:
            yield sse_event("error", {"message": "PERPLEXITY_API_KEY not set"})
            return
        run_id = make_run_id("perplexity")
        ts_iso = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        yield sse_event("start", {"run_id": run_id, "ts": ts_iso})

        url = 'https://api.perplexity.ai/chat/completions'
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }
        payload = {
            'model': model or 'sonar',
            'messages': [
                {'role': 'user', 'content': query},
            ],
            # Some Perplexity models may ignore temperature; include only if non-null
            **({'temperature': float(temperature)} if temperature is not None else {}),
            'stream': True,
        }

        input_tokens = 0
        output_tokens = 0
        full_text_parts: list[str] = []

        try:
            with requests.post(url, headers=headers, json=payload, stream=True, timeout=60) as resp:
                resp.raise_for_status()
                for raw_line in resp.iter_lines(decode_unicode=True):
                    if not raw_line:
                        continue
                    if raw_line.startswith(':'):
                        # SSE comment/heartbeat
                        continue
                    if raw_line.startswith('data:'):
                        data_str = raw_line[5:].strip()
                        if data_str == '[DONE]':
                            break
                        try:
                            evt = json.loads(data_str)
                        except Exception:
                            continue
                        # standard OpenAI-compatible shape
                        try:
                            choices = evt.get('choices') or []
                            if choices:
                                ch0 = choices[0]
                                delta = (ch0.get('delta') or {}).get('content')
                                if isinstance(delta, str) and delta:
                                    full_text_parts.append(delta)
                                    yield sse_event('delta', {'text': delta})
                        except Exception:
                            pass
                        # usage occasionally present at end
                        try:
                            usage = evt.get('usage') or {}
                            input_tokens = int(usage.get('prompt_tokens', input_tokens) or input_tokens)
                            output_tokens = int(usage.get('completion_tokens', output_tokens) or output_tokens)
                        except Exception:
                            pass

            # persist final run
            text = ''.join(full_text_parts)
            vendors = extract_competitors(text)
            links = extract_links(text)
            domains = to_domains(links)
            citations_enriched = _enrich_citations(links, max_titles=0)
            entities_normalized = _normalize_entities([v.model_dump() for v in vendors])
            latency_ms = int((time.time() - t0) * 1000)
            cost_usd = estimate_cost(input_tokens, output_tokens, None, model or 'sonar')

            csv_row = {
                'ts': ts_iso,
                'run_id': run_id,
                'engine': 'perplexity',
                'model': model or 'sonar',
                'prompt_version': prompt_version,
                'intent': intent,
                'query': query,
                'status': 'ok',
                'latency_ms': latency_ms,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'cost_usd': cost_usd,
                'raw_excerpt': text,
                'vendors': [v.model_dump() for v in vendors],
                'links': links,
                'domains': domains,
                'citations_enriched': citations_enriched,
                'entities_normalized': entities_normalized,
                'extreme_mentioned': any((v.name or '').lower() == 'extreme networks' for v in vendors),
                'extreme_rank': next((i for i, v in enumerate(vendors, start=1) if (v.name or '').lower() == 'extreme networks'), None),
            }
            persist_run_to_db(csv_row)
            yield sse_event('done', {'run_id': run_id})
        except Exception as e:
            try:
                print('PPLX STREAM ERROR:', repr(e))
                traceback.print_exc()
            except Exception:
                pass
            yield sse_event('error', {'message': str(e), 'type': type(e).__name__})

    return StreamingResponse(
        gen(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        },
    )