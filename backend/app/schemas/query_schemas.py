from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field

#defining pydantic models for request and response schemas

#this is the request schema for the query endpoint, used to validate incoming requests
class QueryRequest(BaseModel):
    query: str = Field(min_length=3, max_length=300) #actual content of query
    intent: str = Field(default="unlabeled") #SEO Intent (commercial, informational, etc.)
    engines: List[str] = Field(default_factory=lambda: ["openai"])  # "openai" | "perplexity", currently
    prompt_version: str = Field(default="v1") #version of prompt used
    force: bool = Field(default=False) #force re-run even if cached
    temperature: float = Field(default=0.2, ge=0.0, le=1.0) #temperature for openai, controls randomness of responses

#object ot help with competitive analysis
class VendorItem(BaseModel):
    name: str #name of company
    relevance: Optional[float] = None #relevance score (need to find heuristic)
    first_pos: Optional[int] = None #position of company in search results

#this class is used to understand the response from the query endpoint
class RunResponse(BaseModel):
    id: str #unique identifier for the run
    ts: str #timestamp of run
    query: str #actual query
    intent: str #SEO Intent (commercial, informational, etc.)
    engine: str #engine used (openai, perplexity)
    model: str #model used (gpt-4o, sonar, etc.)
    prompt_version: str #version of prompt used
    status: str #status of run (ok, error, etc.)
    latency_ms: int #latency of run
    input_tokens: int #number of tokens input
    output_tokens: int #number of tokens output
    cost_usd: float #cost of run
    raw_excerpt: str #raw excerpt from run
    extreme_mentioned: bool #whether extreme was mentioned
    extreme_rank: Optional[int] #position of extreme in search results
    vendors: List[VendorItem] #list of vendors mentioned
    links: List[str] #list of links mentioned
    domains: List[str] #list of domains mentioned

#this class is used to understand the response from the query endpoint
class QueryResponse(BaseModel):
    status: str #status of response (ex: ok, error)
    runs: List[RunResponse] #list of runs