from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON, Float, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class AutomatedRun(Base):
    """Model for storing automated competitive intelligence runs."""
    
    __tablename__ = "automated_runs"
    
    # Primary identifier
    id = Column(String, primary_key=True, index=True)
    
    # Run metadata
    ts = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    query = Column(Text, nullable=False)
    engine = Column(String, nullable=False, index=True)
    model = Column(String, nullable=False)
    
    # Run results
    status = Column(String, default="pending")  # pending, running, completed, failed
    answer_text = Column(Text)
    entities_normalized = Column(JSON)  # Extracted competitors and entities
    links = Column(JSON)  # URLs found in the response
    domains = Column(JSON)  # Extracted domains from links
    
    # Competitive intelligence data
    extreme_mentioned = Column(Boolean, default=False)
    competitor_mentions = Column(JSON)  # Which competitors were mentioned
    citation_count = Column(Integer, default=0)
    domain_count = Column(Integer, default=0)
    
    # Cost and performance
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    latency_ms = Column(Integer, default=0)
    
    # Query classification
    intent_category = Column(String, index=True)  # generic_intent, brand_focused, comparison
    competitor_set = Column(JSON)  # Which competitors this query targets
    
    # Processing metadata
    processed_at = Column(DateTime)
    metrics_computed = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<AutomatedRun(id={self.id}, query='{self.query[:50]}...', engine={self.engine})>"
