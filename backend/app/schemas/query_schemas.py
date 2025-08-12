from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    query: str = Field(min_length=3, max_length=300)
    intent: str = Field(default="unlabeled")
    engines: List[str] = Field(default_factory=lambda: ["openai"])  # "openai" | "perplexity"
    prompt_version: str = Field(default="v1")
    force: bool = Field(default=False)
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)

class VendorItem(BaseModel):
    name: str
    relevance: Optional[float] = None
    first_pos: Optional[int] = None

class RunResponse(BaseModel):
    id: str
    ts: str
    query: str
    intent: str
    engine: str
    model: str
    prompt_version: str
    status: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    cost_usd: float
    raw_excerpt: str
    extreme_mentioned: bool
    extreme_rank: Optional[int]
    vendors: List[VendorItem]
    links: List[str]
    domains: List[str]

class QueryResponse(BaseModel):
    status: str
    runs: List[RunResponse]