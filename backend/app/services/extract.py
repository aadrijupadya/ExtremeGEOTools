from __future__ import annotations
import re
from typing import List

from ..schemas.query_schemas import VendorItem
from urllib.parse import urlparse

COMPETITORS = [
    "Cisco", "Juniper", "Huawei", "Arista", "HPE", "Aruba",
    "Dell", "Fortinet", "Ubiquiti", "Nokia", "Extreme Networks",
]

# Common alias → canonical vendor name map
ALIASES = {
    "cisco systems": "Cisco",
    "cisco system": "Cisco",
    "juniper networks": "Juniper",
    "hewlett packard enterprise": "HPE",
    "hp enterprise": "HPE",
    "hpe aruba": "Aruba",
    "aruba networks": "Aruba",
    "ubiquiti networks": "Ubiquiti",
    "extreme networks": "Extreme Networks",
    "extremenetworks": "Extreme Networks",
}

#extracts competitors using array of competitors
def extract_competitors(text: str) -> List[VendorItem]:
    txt = (text or "")
    found: List[VendorItem] = []
    # 1) Canonical names
    for v in COMPETITORS:
        pattern = re.compile(rf"\b{re.escape(v)}\b", re.IGNORECASE)
        m = pattern.search(txt)
        if m:
            found.append(VendorItem(name=v, first_pos=m.start()))
    # 2) Aliases → canonical
    for alias, canonical in ALIASES.items():
        pattern = re.compile(rf"\b{re.escape(alias)}\b", re.IGNORECASE)
        m = pattern.search(txt)
        if m:
            found.append(VendorItem(name=canonical, first_pos=m.start()))
    # dedupe by canonical name, keep earliest match
    seen = set()
    out: List[VendorItem] = []
    for item in sorted(found, key=lambda x: x.first_pos or 10**9):
        key = item.name.lower()
        if key not in seen:
            out.append(item)
            seen.add(key)
    return out

#using regex to extract links
def extract_links(text: str) -> List[str]:
    """Extract URLs from text including markdown [title](url), strip trailing punctuation, dedupe preserving order."""
    s = text or ""
    links: List[str] = []

    # 1) Markdown links: [title](url)
    for m in re.finditer(r"\[[^\]]+\]\((https?://[^)\s]+)\)", s):
        links.append(m.group(1))

    # 2) Raw URLs
    for m in re.finditer(r"https?://[^\s<>\]\)\"]+", s):
        links.append(m.group(0))

    # Cleanup trailing punctuation and brackets
    cleaned: List[str] = []
    for u in links:
        u2 = u.rstrip('.,);:]')
        # basic validation
        try:
            p = urlparse(u2)
            if p.scheme in ("http", "https") and p.netloc:
                cleaned.append(u2)
        except Exception:
            continue

    # Dedupe preserving order
    seen = set()
    out: List[str] = []
    for u in cleaned:
        if u not in seen:
            out.append(u)
            seen.add(u)
    return out

#convert links to valid domains
def to_domains(links: List[str]) -> List[str]:
    out: List[str] = []
    for u in links:
        try:
            p = urlparse(u)
            dom = (p.netloc or "").lower()
            if dom.startswith("www."):
                dom = dom[4:]
            if dom:
                out.append(dom)
        except Exception:
            pass
    return out

#placeholder stub for extracting sources using llm
def extract_sources_llm(answer_text: str) -> List[str]:
    """Placeholder stub. If needed, wire to OpenAI like the original implementation."""
    return []