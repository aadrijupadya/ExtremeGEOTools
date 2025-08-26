# ExtremeGEOTools - Project Overview

## What is ExtremeGEOTools?

ExtremeGEOTools is a **Competitive Intelligence Dashboard** that runs automated queries across multiple AI engines (OpenAI, Perplexity) to track brand visibility, competitor mentions, and market positioning for Extreme Networks.

## 🎯 **Current Status: MVP (57% Complete)**

### **✅ What's Working:**
- **Query Execution Pipeline** - Automated queries across OpenAI and Perplexity
- **Database Backend** - PostgreSQL with FastAPI
- **Metrics Dashboard** - Brand visibility, competitor analysis, citation tracking
- **Automation** - Scheduled queries, backfill capabilities
- **Cost Tracking** - Token usage and pricing calculations

### **🚧 What's Next:**
- **Monthly/Trend Views** - Time-series analysis and charts
- **Keyword Analysis** - Search term performance tracking
- **Query Management** - Bulk import and management UI
- **Enhanced Reporting** - Export capabilities and alerts

## 🏗️ **Architecture Overview**

```
ExtremeGEOTools/
├── backend/           # FastAPI + PostgreSQL backend
│   ├── app/          # Main application code
│   ├── alembic/      # Database migrations
│   └── scripts/      # Utility scripts
├── frontend/          # React-based dashboard
├── scripts/           # Automation and post-processing
├── data/              # Data storage and configuration
└── docs/              # Project documentation
```

## 🔧 **Tech Stack**

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: React, CSS3
- **AI Engines**: OpenAI GPT-4o, Perplexity Sonar
- **Automation**: Cron jobs, background workers
- **Deployment**: Docker, Docker Compose

## 📊 **Core Features**

1. **Automated Query Execution** - Scheduled competitive intelligence queries
2. **Multi-Engine Support** - OpenAI and Perplexity integration
3. **Brand Visibility Tracking** - Extreme Networks mention detection
4. **Competitor Analysis** - Market share and positioning metrics
5. **Citation Quality Assessment** - Source credibility scoring
6. **Cost Management** - Token usage and pricing tracking
7. **Branded Query Flag** - `is_branded` boolean on runs to distinguish brand/comparison queries from generic intent
8. **Real-time Dashboard** - Live metrics and insights

## 🎯 **Use Cases**

- **Competitive Intelligence** - Track competitor mentions and positioning
- **Brand Monitoring** - Monitor Extreme Networks visibility
- **Market Research** - Analyze industry trends and sentiment
- **Content Strategy** - Identify high-impact topics and sources
- **Cost Optimization** - Monitor AI query costs and efficiency

## 🚀 **Getting Started**

1. **Setup**: `docker-compose up -d`
2. **Frontend**: `cd frontend && npm start`
3. **Backend**: `cd backend && python main.py`
4. **Dashboard**: Navigate to `http://localhost:3000/metrics`

## 📈 **Development Roadmap**

- **Phase 1**: Core MVP (Current) ✅
- **Phase 2**: Enhanced Analytics (Next 2 weeks)
- **Phase 3**: Advanced Reporting (Next month)
- **Phase 4**: Enterprise Features (Future)

## 🤝 **Contributing**

This is an internal tool for Extreme Networks competitive intelligence. For questions or contributions, contact the development team.
