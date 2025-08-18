from __future__ import annotations
import time
from typing import Any, Dict

from .adapters import chatgpt_api as openai_adapter
from .adapters import perplexity as perplexity_adapter

#normalizes openai and perplexity responses to a common dict, and uses system prompt to guide responses

SYSTEM_PROMPT = (
    "You are an AI search assistant specializing in competitive intelligence and market research. "
    "Provide the most accurate answer and ALWAYS include specific URLs, website addresses, and "
    "source links when mentioning companies, products, or industry reports. "
    "Format URLs as: 'Visit https://company.com' or 'Check https://report.com'. "
    "Include official company websites, industry publication URLs, and source links whenever possible. "
    "If unsure about a specific URL, be conservative and avoid fabrication, but still provide "
    "the company name and suggest visiting their official website."
)


def _normalize_openai(resp: Any, started_at: float) -> Dict[str, Any]:
    """Normalize OpenAI chat response to a common dict."""
    text = ""
    model = ""
    input_tokens = 0
    output_tokens = 0
    cost_usd = None

    try:
        # Prefer the convenience property if present
        text = getattr(resp, "output_text", None)
        if not text:
            outputs = getattr(resp, "output", None) or []
            parts = []
            for blk in outputs:
                c = blk.get("content") if isinstance(blk, dict) else None
                if isinstance(c, list):
                    for item in c:
                        # Responses API usually uses type: "text"
                        if isinstance(item, dict):
                            if item.get("type") == "text" and item.get("text"):
                                parts.append(item.get("text"))
                            elif item.get("type") == "output_text" and item.get("text"):
                                parts.append(item.get("text"))
                elif isinstance(c, str):
                    parts.append(c)
            text = "\n".join([p for p in parts if p])
        text = text or ""
    except Exception:
        text = str(resp)

    try:
        model = getattr(resp, "model", "") or getattr(resp, "model_name", "") or "gpt-5-mini"
    except Exception:
        model = "gpt-5-mini"

    try:
        usage = getattr(resp, "usage", None)
        if usage:
            # Responses API usage fields
            input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
            output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
            cost_usd = getattr(usage, "total_cost", None) or getattr(usage, "cost", None)
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

    print(f"DEBUG: Perplexity response type: {type(resp)}")  # Debug
    print(f"DEBUG: Perplexity response keys: {resp.keys() if isinstance(resp, dict) else 'Not a dict'}")  # Debug

    if isinstance(resp, dict):
        # Perplexity API returns choices[0].message.content structure
        if "choices" in resp and len(resp["choices"]) > 0:
            text = resp["choices"][0].get("message", {}).get("content", "")
        else:
            text = str(resp.get("text") or resp.get("response") or "")
        
        model = resp.get("model") or model
        usage = resp.get("usage") or {}
        input_tokens = int(usage.get("prompt_tokens", 0) or 0)
        output_tokens = int(usage.get("completion_tokens", 0) or 0)
        cost_usd = usage.get("cost_usd")
    else:
        text = str(resp)

    print(f"DEBUG: Extracted text length: {len(text)}")  # Debug

    latency_ms = int((time.time() - started_at) * 1000)
    return {
        "text": text,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_ms": latency_ms,
        "cost_usd": cost_usd,
    }


def call_engine(engine: str, prompt: str, temperature: float, model: str | None = None) -> Dict[str, Any]:
    """Call the specified engine and return a normalized dict.
    { text, model, input_tokens, output_tokens, latency_ms, cost_usd (optional) }
    """
    t0 = time.time()

    if engine == "openai":
        # Pass the raw user query; adapter sets concise instructions and caps output length.
        resp = openai_adapter.run_query(prompt, model=model or "gpt-5-nano-2025-08-07")
        return _normalize_openai(resp, t0)

    if engine == "perplexity":
        resp = perplexity_adapter.run_query(prompt, temperature=temperature, model=model or 'sonar')
        return _normalize_perplexity(resp, t0)

    raise ValueError(f"Unsupported engine: {engine}")