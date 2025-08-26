#!/usr/bin/env python3
"""
Backfill script to set is_branded on runs and automated_runs based on query text.

Heuristic: if the query contains any known company name keywords, mark as branded.
Companies include Extreme Networks and common competitors; also treat comparison
phrases (vs/versus/compare/comparison) as branded.
"""

from __future__ import annotations
import re
from typing import List
from datetime import datetime
import sys
from pathlib import Path

# Add backend to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.database import get_db
from app.models.run import Run
from app.models.automated_run import AutomatedRun


BRAND_TERMS = [
    "extreme", "extreme networks",
    "cisco", "juniper", "aruba", "hpe", "hewlett packard", "meraki",
    "fortinet", "palo alto", "panw", "mist", "ruckus", "ubiquiti",
    "netgear", "d-link", "tp-link", "huawei", "arista", "brocade",
    "nokia", "dell", "vmware", "broadcom", "versus", "vs", "compare",
    "comparison"
]


def is_branded_query(text: str | None) -> bool:
    if not text:
        return False
    s = text.lower()
    return any(term in s for term in BRAND_TERMS)


def backfill() -> dict:
    db = next(get_db())
    updated_runs = 0
    updated_auto = 0

    # Process runs
    runs: List[Run] = db.query(Run).all()
    for r in runs:
        desired = is_branded_query(r.query)
        if bool(getattr(r, "is_branded", False)) != desired:
            r.is_branded = desired
            db.add(r)
            updated_runs += 1

    # Process automated_runs
    autos: List[AutomatedRun] = db.query(AutomatedRun).all()
    for a in autos:
        desired = is_branded_query(a.query)
        # Some automated runs already set is_branded; align with heuristic
        if getattr(a, "is_branded", None) != desired:
            a.is_branded = desired
            db.add(a)
            updated_auto += 1

    db.commit()
    return {"runs_updated": updated_runs, "automated_runs_updated": updated_auto}


if __name__ == "__main__":
    res = backfill()
    print(f"Backfill complete: {res}")


