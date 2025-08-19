from openai import OpenAI
from dotenv import load_dotenv
import os
try:
    # SDK v1 provides BadRequestError; fall back gracefully if unavailable
    from openai import BadRequestError  # type: ignore
except Exception:  # pragma: no cover
    class BadRequestError(Exception):
        pass

load_dotenv()

def _get_openai_client() -> OpenAI:
    # Single source of truth: OPENAI_API_KEY
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return OpenAI(api_key=api_key)
    # Fallback to default env discovery (OpenAI SDK will look up env vars internally)
    return OpenAI()

SYSTEM_PROMPT = """
You are an AI search assistant.
- Keep responses concise and scannable (<= 500 tokens). Prefer short paragraphs and 3–7 bullet points.
- ALWAYS include full, direct URLs inline (no [1][2] style). Use plain https:// links.
- If unsure, respond conservatively and avoid fabricating.
"""

def run_query(prompt: str, model: str | None = None, max_output_tokens: int = 500, temperature: float | None = None):
    # Responses API migration: https://platform.openai.com/docs/guides/migrate-to-responses
    # Prefer structured input blocks for Responses API
    input_blocks = [
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
            ],
        }
    ]

    # Preferred default model via env, fallback to nano ID, with alias support
    env_default = os.getenv("OPENAI_MODEL_ID", "gpt-4o-search-preview")
    requested = model or env_default
    model_alias = {
        # prefer undated ids
        "gpt-5-mini": "gpt-5-mini",
        "gpt-5-mini-2025-08-07": "gpt-5-mini",
        "gpt-5-mini-latest": "gpt-5-mini",
        # route all nano variants to mini (temporary mitigation for blank outputs)
        "gpt-5-nano": "gpt-5-mini",
        "gpt-5-nano-2025-08-07": "gpt-5-mini",
        "gpt-5-nano-latest": "gpt-5-mini",
        # legacy mini search preview → current search preview
        "gpt-4o-mini-search-preview-2025-03-11": "gpt-4o-search-preview",
        # keep explicit other ids as-is
        "gpt-4o-search-preview": "gpt-4o-search-preview",
    }
    resolved_model = model_alias.get(requested, requested)

    client = _get_openai_client()
    # Use Responses API for GPT-5 family; use Chat Completions for older/search-preview models
    if str(resolved_model).startswith("gpt-5"):
        try:
            # Primary: structured input blocks + instructions
            resp = client.responses.create(
                model=resolved_model,
                instructions=SYSTEM_PROMPT.strip(),
                input=input_blocks,
                max_output_tokens=max_output_tokens,
                **({"temperature": float(temperature)} if temperature is not None else {}),
            )
            if os.getenv("EGT_DEBUG_OPENAI"):
                try:
                    ot = getattr(resp, "output_text", None)
                    outputs = getattr(resp, "output", None)
                    usage = getattr(resp, "usage", None)
                    print(
                        "OPENAI RESP META:",
                        {
                            "model": getattr(resp, "model", None) or getattr(resp, "model_name", None),
                            "output_text_len": len(ot or "") if isinstance(ot, str) else 0,
                            "has_output_blocks": bool(outputs),
                            "num_blocks": len(outputs or []),
                            "usage": {
                                "input_tokens": int(getattr(usage, "input_tokens", 0) or 0) if usage else None,
                                "output_tokens": int(getattr(usage, "output_tokens", 0) or 0) if usage else None,
                            },
                        },
                    )
                except Exception:
                    pass
            return resp
        except BadRequestError as e:
            # Retry with simple string input if the model rejects structured input
            try:
                resp = client.responses.create(
                    model=resolved_model,
                    instructions=SYSTEM_PROMPT.strip(),
                    input=prompt,
                    max_output_tokens=max_output_tokens,
                    **({"temperature": float(temperature)} if temperature is not None else {}),
                )
                if os.getenv("EGT_DEBUG_OPENAI"):
                    try:
                        ot = getattr(resp, "output_text", None)
                        outputs = getattr(resp, "output", None)
                        usage = getattr(resp, "usage", None)
                        print(
                            "OPENAI RESP META (fallback):",
                            {
                                "model": getattr(resp, "model", None) or getattr(resp, "model_name", None),
                                "output_text_len": len(ot or "") if isinstance(ot, str) else 0,
                                "has_output_blocks": bool(outputs),
                                "num_blocks": len(outputs or []),
                                "usage": {
                                    "input_tokens": int(getattr(usage, "input_tokens", 0) or 0) if usage else None,
                                    "output_tokens": int(getattr(usage, "output_tokens", 0) or 0) if usage else None,
                                },
                            },
                        )
                    except Exception:
                        pass
                return resp
            except Exception:
                # Surface detailed info in logs to debug 4xx issues
                print("OPENAI 400 (both formats failed):", getattr(e, "status_code", None), getattr(e, "response", None))
                raise
        except Exception as e:
            print("OPENAI ERROR:", repr(e))
            raise
    else:
        # Chat Completions for legacy/search-preview models
        try:
            resp = client.chat.completions.create(
                model=resolved_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT.strip()},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_output_tokens,
                **({"temperature": float(temperature)} if temperature is not None else {}),
            )
            if os.getenv("EGT_DEBUG_OPENAI"):
                try:
                    print("OPENAI CHAT COMPLETIONS META:", {
                        "model": resolved_model,
                        "choices": len(getattr(resp, "choices", []) or []),
                    })
                except Exception:
                    pass
            return resp
        except BadRequestError as e:
            print("OPENAI CHAT 400:", getattr(e, "status_code", None), getattr(e, "response", None))
            raise
        except Exception as e:
            print("OPENAI CHAT ERROR:", repr(e))
            raise
