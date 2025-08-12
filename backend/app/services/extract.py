from __future__ import annotations
import re
from typing import List

from ..schemas.query_schemas import VendorItem

COMPETITORS = [
    "Cisco", "Juniper", "Huawei", "Arista", "HPE", "Aruba",
    "Dell", "Fortinet", "Ubiquiti", "Nokia", "Extreme Networks",
]


def extract_competitors(text: str) -> List[VendorItem]:
    txt = (text or "").lower()
    found: List[VendorItem] = []
    for v in COMPETITORS:
        i = txt.find(v.lower())
        if i != -1:
            found.append(VendorItem(name=v, first_pos=i))
    # dedupe by name, keep first
    seen = set()
    out: List[VendorItem] = []
    for item in sorted(found, key=lambda x: x.first_pos or 10**9):
        if item.name not in seen:
            out.append(item)
            seen.add(item.name)
    return out


def extract_links(text: str) -> List[str]:
    return re.findall(r'https?://[^\s\]\)>,"]+', text or "")


def to_domains(links: List[str]) -> List[str]:
    out = []
    for u in links:
        try:
            dom = u.split("//", 1)[1].split("/", 1)[0]
            out.append(dom.lower())
        except Exception:
            pass
    return out


def extract_sources_llm(answer_text: str) -> List[str]:
    """Placeholder stub. If needed, wire to OpenAI like the original implementation."""
    return []