from __future__ import annotations
from sqlalchemy import Column, Integer, String, Text, Boolean, Numeric
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from ..services.database import Base


class Run(Base):
    __tablename__ = "runs"

    id = Column(String, primary_key=True)  # run_id
    ts = Column(TIMESTAMP(timezone=True), nullable=False)
    engine = Column(String, nullable=False)
    model = Column(String, nullable=True)
    prompt_version = Column(String, nullable=True)
    intent = Column(String, nullable=True)
    query = Column(Text, nullable=False)
    status = Column(String, nullable=False)

    latency_ms = Column(Integer, nullable=False, default=0)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    cost_usd = Column(Numeric(18, 6), nullable=False, default=0)

    raw_excerpt = Column(Text, nullable=True)
    vendors = Column(JSONB, nullable=False, default=list)
    links = Column(JSONB, nullable=False, default=list)
    domains = Column(JSONB, nullable=False, default=list)

    # Cached enrichment (persisted once, reused by API/UI)
    citations_enriched = Column(JSONB, nullable=False, default=list)
    entities_normalized = Column(JSONB, nullable=False, default=list)

    extreme_mentioned = Column(Boolean, nullable=False, default=False)
    extreme_rank = Column(Integer, nullable=True)

    # Soft delete flag (excluded from listings but included in cost rollups)
    deleted = Column(Boolean, nullable=False, default=False)


