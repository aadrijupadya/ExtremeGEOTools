from __future__ import annotations
from fastapi import APIRouter

from ..services.pricing import PRICING_EXACT, DEFAULT_COST_PER_1K_INPUT, DEFAULT_COST_PER_1K_OUTPUT


router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.get("/models")
def list_models_pricing():
    """Expose model pricing configured on the server.

    Returns a stable JSON shape for the frontend to render live estimates
    without making per-keystroke API calls.
    """
    models = [
        {
            "id": model_id,
            "input_per_1k": float(prices.get("in", DEFAULT_COST_PER_1K_INPUT)),
            "output_per_1k": float(prices.get("out", DEFAULT_COST_PER_1K_OUTPUT)),
        }
        for model_id, prices in PRICING_EXACT.items()
    ]

    return {
        "models": models,
        "defaults": {
            "input_per_1k": float(DEFAULT_COST_PER_1K_INPUT),
            "output_per_1k": float(DEFAULT_COST_PER_1K_OUTPUT),
        },
    }


