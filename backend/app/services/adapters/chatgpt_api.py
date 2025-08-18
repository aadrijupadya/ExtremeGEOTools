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

def run_query(prompt: str, model: str | None = None, max_output_tokens: int = 500):
    # Responses API migration: https://platform.openai.com/docs/guides/migrate-to-responses
    # Build an input that includes system + user content
    input_blocks = [
        {"role": "system", "content": SYSTEM_PROMPT.strip()},
        {"role": "user", "content": prompt},
    ]

    # Preferred default model via env, fallback to nano ID, with alias support
    env_default = os.getenv("OPENAI_MODEL_ID", "gpt-5-nano-2025-08-07")
    requested = model or env_default
    model_alias = {
        "gpt-5-mini": "gpt-5-mini-2025-08-07",
        "gpt-5-mini-2025-08-07": "gpt-5-mini-2025-08-07",
        "gpt-5-nano": "gpt-5-nano-2025-08-07",
        "gpt-5-nano-2025-08-07": "gpt-5-nano-2025-08-07",
    }
    resolved_model = model_alias.get(requested, requested)

    client = _get_openai_client()
    try:
        # Some models do not support sampling params; omit them and set max_output_tokens to cap latency.
        resp = client.responses.create(
            model=resolved_model,
            instructions=SYSTEM_PROMPT.strip(),
            input=prompt,
            max_output_tokens=max_output_tokens,
        )
        return resp
    except BadRequestError as e:
        # Surface detailed info in logs to debug 4xx issues
        print("OPENAI 400:", getattr(e, "status_code", None), getattr(e, "response", None))
        raise
    except Exception as e:
        print("OPENAI ERROR:", repr(e))
        raise
