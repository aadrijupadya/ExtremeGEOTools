from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import pandas as pd

# Resolve repo root by finding the nearest parent containing a `data` directory
HERE = Path(__file__).resolve()
REPO_ROOT = next(p for p in HERE.parents if (p / "data").exists())
DATA_DIR = REPO_ROOT / "data"
CSV_PATH = DATA_DIR / "storage" / "responses.csv"
CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

CSV_COLUMNS = [
    "ts", "run_id", "engine", "model", "prompt_version",
    "intent", "query", "status", "latency_ms",
    "input_tokens", "output_tokens", "cost_usd",
    "raw_excerpt", "vendors", "links", "domains",
    "extreme_mentioned", "extreme_rank",
]

def append_run_to_csv(row: Dict[str, Any]) -> None:
    """Append a single normalized run row to the CSV, creating the file if needed."""
    data = {k: row.get(k, None) for k in CSV_COLUMNS}
    df_new = pd.DataFrame([data])
    if CSV_PATH.exists():
        df = pd.read_csv(CSV_PATH)
        df = pd.concat([df, df_new], ignore_index=True)
    else:
        df = df_new
    df.to_csv(CSV_PATH, index=False)