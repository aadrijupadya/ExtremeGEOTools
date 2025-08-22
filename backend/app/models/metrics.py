from __future__ import annotations
from sqlalchemy import Column, Integer, String, Date, Numeric, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from ..services.database import Base

#daily metrics are metrics that are computed daily for the dashboard
class DailyMetrics(Base):
    __tablename__ = "daily_metrics"

    # Composite primary key: date + engine + brand_context
    date = Column(Date, primary_key=True, nullable=False)
    engine = Column(String, primary_key=True, nullable=False)
    brand_context = Column(String, primary_key=True, nullable=False)  # "extreme_networks", "competitors", "overall"
    
    # Run counts and costs
    total_runs = Column(Integer, nullable=False, default=0)
    total_cost_usd = Column(Numeric(18, 6), nullable=False, default=0)
    
    # Citation metrics
    total_citations = Column(Integer, nullable=False, default=0)
    unique_domains = Column(Integer, nullable=False, default=0)
    top_domains = Column(JSONB, nullable=False, default=list)  # [{"domain": "example.com", "count": 5, "quality_score": 0.8}]
    
    # Entity visibility metrics
    brand_mentions = Column(Integer, nullable=False, default=0)
    competitor_mentions = Column(Integer, nullable=False, default=0)
    share_of_voice_pct = Column(Numeric(5, 2), nullable=False, default=0)  # 0.00 to 100.00
    
    # Quality metrics
    avg_visibility_score = Column(Numeric(5, 2), nullable=False, default=0)  # 0.00 to 100.00
    high_quality_citations = Column(Integer, nullable=False, default=0)  # citations with quality_score > 0.7
    
    # Metadata
    last_updated = Column(String, nullable=False)  # ISO timestamp
    data_version = Column(String, nullable=False, default="1.0")  # for schema evolution
