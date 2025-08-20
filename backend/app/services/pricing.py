from __future__ import annotations
from typing import Dict, Tuple, Optional

# Default fallbacks if a model isn't found in pricing tables (USD per 1K tokens)
DEFAULT_COST_PER_1K_INPUT = 0.0025
DEFAULT_COST_PER_1K_OUTPUT = 0.010

# Pricing hash tables (exact first, then prefix). Values are USD per 1K tokens.
PRICING_EXACT: Dict[str, Dict[str, float]] = {
    # --- OpenAI (GPT-4o family) ---
    "gpt-4o-mini-search-preview": {"in": 0.00015, "out": 0.0006},
    "gpt-4o-search-preview": {"in": 0.00015, "out": 0.0006},
    
    # --- OpenAI (GPT-5 family placeholders) ---
    "gpt-5-mini-2025-08-07": {"in": 0.0006, "out": 0.0024},

    # --- Perplexity (sonar family) ---
    "sonar": {"in": 0.0010, "out": 0.0010},
    "sonar-pro": {"in": 0.0030, "out": 0.0150},
    "sonar-reasoning": {"in": 0.0010, "out": 0.0050},
    "sonar-reasoning-pro": {"in": 0.0020, "out": 0.0080},
    "sonar-deep-research": {"in": 0.0020, "out": 0.0080},
}

PRICING_PREFIX: Dict[str, Dict[str, float]] = {
    # --- OpenAI prefixes ---
    "gpt-4o-mini-search-preview": {"in": 0.00015, "out": 0.0006},
    "gpt-4o-search-preview": {"in": 0.00015, "out": 0.0006},
    "gpt-5-mini-2025-": {"in": 0.0006, "out": 0.0024},
    
    # --- Perplexity prefixes ---
    "sonar-": {"in": 0.0030, "out": 0.0150},
    "perplexity-": {"in": DEFAULT_COST_PER_1K_INPUT, "out": DEFAULT_COST_PER_1K_OUTPUT},
}


def prices_for_model(model: str) -> Tuple[float, float]:
    """Return (input_price, output_price) for a model ID, using exact→prefix→default."""
    m = (model or "").strip()
    if not m:
        return DEFAULT_COST_PER_1K_INPUT, DEFAULT_COST_PER_1K_OUTPUT

    if m in PRICING_EXACT:
        p = PRICING_EXACT[m]
        return float(p["in"]), float(p["out"])

    for prefix, p in PRICING_PREFIX.items():
        if m.startswith(prefix):
            return float(p["in"]), float(p["out"])

    return DEFAULT_COST_PER_1K_INPUT, DEFAULT_COST_PER_1K_OUTPUT


def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    fallback_cost: Optional[float],
    model: Optional[str],
) -> float:
    """Estimate cost using per-model pricing unless the adapter supplied cost.
    NOTE: External surcharges (e.g., deep-research browsing fees) are not modeled here.
    """
    if fallback_cost is not None:
        try:
            return float(fallback_cost)
        except Exception:
            pass

    in_price, out_price = prices_for_model(model or "")
    cost = (max(input_tokens, 0) / 1000.0 * in_price) + (max(output_tokens, 0) / 1000.0 * out_price)
    return round(cost, 6)