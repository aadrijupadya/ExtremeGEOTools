from __future__ import annotations
import time
from typing import Any, Dict

from .adapters import chatgpt_api as openai_adapter
from .adapters import perplexity as perplexity_adapter

SYSTEM_PROMPT = (
    "You are an AI search assistant. Provide the most accurate answer and "
    "include sources or citations (publications, reports, websites) when relevant. "
    "If unsure, be conservative and avoid fabrication."
)


def _normalize_openai(resp: Any, started_at: float) -> Dict[str, Any]:
    """Normalize OpenAI chat response to a common dict."""
    text = ""
    model = ""
    input_tokens = 0
    output_tokens = 0
    cost_usd = None

    try:
        text = getattr(resp.choices[0].message, "content", "") or ""
    except Exception:
        text = str(resp)

    try:
        model = getattr(resp, "model", "") or getattr(resp, "model_name", "") or "gpt-4o"
    except Exception:
        model = "gpt-4o"

    try:
        usage = getattr(resp, "usage", None)
        if usage:
            input_tokens = int(getattr(usage, "prompt_tokens", 0))
            output_tokens = int(getattr(usage, "completion_tokens", 0))
            cost_usd = getattr(usage, "cost", None)
            if isinstance(cost_usd, dict):
                cost_usd = cost_usd.get("usd")
    except Exception:
        pass

    latency_ms = int((time.time() - started_at) * 1000)
    return {
        "text": text,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_ms": latency_ms,
        "cost_usd": cost_usd,
    }


def _normalize_perplexity(resp: Any, started_at: float) -> Dict[str, Any]:
    """Normalize Perplexity adapter output (dict or str) to a common dict."""
    text = ""
    model = "perplexity"
    input_tokens = 0
    output_tokens = 0
    cost_usd = None

    if isinstance(resp, dict):
        text = str(resp.get("text") or resp.get("response") or "")
        model = resp.get("model") or model
        usage = resp.get("usage") or {}
        input_tokens = int(usage.get("prompt_tokens", 0) or 0)
        output_tokens = int(usage.get("completion_tokens", 0) or 0)
        cost_usd = usage.get("cost_usd")
    else:
        text = str(resp)

    latency_ms = int((time.time() - started_at) * 1000)
    return {
        "text": text,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_ms": latency_ms,
        "cost_usd": cost_usd,
    }


def call_engine(engine: str, prompt: str, temperature: float) -> Dict[str, Any]:
    """Call the specified engine and return a normalized dict.
    { text, model, input_tokens, output_tokens, latency_ms, cost_usd (optional) }
    """
    t0 = time.time()

    if engine == "openai":
        full_prompt = f"{SYSTEM_PROMPT}\n\nUser:\n{prompt}"
        resp = openai_adapter.run_query(full_prompt, model="gpt-4o", temperature=temperature)
        return _normalize_openai(resp, t0)

    if engine == "perplexity":
        resp = perplexity_adapter.run_query(prompt, temperature=temperature)
        return _normalize_perplexity(resp, t0)

    raise ValueError(f"Unsupported engine: {engine}")