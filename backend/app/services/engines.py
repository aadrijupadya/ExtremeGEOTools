from __future__ import annotations
import time
from typing import Any, Dict
import os

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
    debug_meta: Dict[str, Any] = {
        "source": "openai.responses",
        "output_text_len": 0,
        "has_output_blocks": False,
        "num_blocks": 0,
        "item_types": [],
    }
    preview_parts: list[str] = []

    try:
        # Prefer the convenience property if present (Responses API)
        maybe_text = getattr(resp, "output_text", None)
        if isinstance(maybe_text, str) and maybe_text:
            text = maybe_text
            debug_meta["output_text_len"] = len(maybe_text)
            preview_parts.append((maybe_text or "")[:500])
        else:
            # Fallback: traverse resp.output[*].content[*] for text
            parts: list[str] = []
            outputs = getattr(resp, "output", None) or []
            debug_meta["has_output_blocks"] = bool(outputs)
            debug_meta["num_blocks"] = len(outputs or [])
            for blk in outputs:
                # Support both dicts and SDK objects
                c = getattr(blk, "content", None)
                if c is None and isinstance(blk, dict):
                    c = blk.get("content")
                if isinstance(c, list):
                    for item in c:
                        item_type = getattr(item, "type", None)
                        if item_type is None and isinstance(item, dict):
                            item_type = item.get("type")
                        if item_type and item_type not in debug_meta["item_types"]:
                            debug_meta["item_types"].append(item_type)
                        # Try common text value fields across SDK/dict forms
                        val = (
                            getattr(item, "text", None)
                            or getattr(item, "value", None)
                            or (item.get("text") if isinstance(item, dict) else None)
                            or (item.get("value") if isinstance(item, dict) else None)
                        )
                        if isinstance(val, str) and val:
                            if item_type in (None, "text", "output_text"):
                                parts.append(val)
                                preview_parts.append(val[:200])
                elif isinstance(c, str):
                    parts.append(c)
                    preview_parts.append(c[:200])
            text = "\n".join([p for p in parts if p])
        # Chat Completions fallback: choices[*].message.content
        if not text:
            try:
                choices = getattr(resp, "choices", None)
                if choices and len(choices) > 0:
                    # choices entries may be objects or dicts
                    first = choices[0]
                    msg = getattr(first, "message", None)
                    if msg is None and isinstance(first, dict):
                        msg = first.get("message")
                    content = getattr(msg, "content", None) if msg is not None else None
                    if content is None and isinstance(msg, dict):
                        content = msg.get("content")
                    if isinstance(content, str) and content:
                        text = content
                        if "choices" not in debug_meta["item_types"]:
                            debug_meta["item_types"].append("choices")
                        preview_parts.append(content[:500])
            except Exception:
                pass
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
            debug_meta["usage"] = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }
    except Exception:
        pass

    latency_ms = int((time.time() - started_at) * 1000)
    # Optional debug summary (no full text)
    if os.getenv("EGT_DEBUG_OPENAI"):
        try:
            print(
                "OPENAI NORMALIZED:",
                {
                    "model": model,
                    "len_text": len(text or ""),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "latency_ms": latency_ms,
                    "item_types": debug_meta.get("item_types"),
                    "num_blocks": debug_meta.get("num_blocks"),
                },
            )
        except Exception:
            pass
    return {
        "text": text,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_ms": latency_ms,
        "cost_usd": cost_usd,
        "debug_meta": debug_meta,
        "raw_preview": ("\n".join(preview_parts))[:2000],
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
        # Respect requested model if provided; otherwise fall back to env default or adapter default.
        resp = openai_adapter.run_query(prompt, model=model, max_output_tokens=500, temperature=temperature)
        norm = _normalize_openai(resp, t0)
        if not (norm.get("text") or "").strip():
            # Persist a concise debug summary so it shows up on runs/{id}
            meta = norm.get("debug_meta") or {}
            usage = f"in {norm.get('input_tokens', 0)}, out {norm.get('output_tokens', 0)}"
            types = ",".join((meta.get("item_types") or [])[:5])
            blocks = meta.get("num_blocks")
            model_name = norm.get("model") or "openai"
            debug_str = (
                f"[No text returned by {model_name}. Tokens: {usage}. "
                f"blocks: {blocks}, types: {types}]"
            )
            preview = norm.get("raw_preview") or ""
            norm["text"] = debug_str + ("\n" + preview if preview else "")
            try:
                print("OPENAI WARNING: Empty text from model.", {"model": model_name, "usage": usage, "blocks": blocks, "types": types})
                if preview:
                    print("OPENAI OUTPUT PREVIEW:", preview[:500])
            except Exception:
                pass
        return norm

    if engine == "perplexity":
        resp = perplexity_adapter.run_query(prompt, temperature=temperature, model=model or 'sonar')
        return _normalize_perplexity(resp, t0)

    raise ValueError(f"Unsupported engine: {engine}")