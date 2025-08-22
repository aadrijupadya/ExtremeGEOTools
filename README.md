# ExtremeGEOTools

> **Competitive Intelligence Dashboard** for Extreme Networks

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)](https://postgresql.org)

## 🎯 **What is ExtremeGEOTools?**

ExtremeGEOTools is a **Competitive Intelligence Dashboard** that runs automated queries across multiple AI engines (OpenAI, Perplexity) to track brand visibility, competitor mentions, and market positioning for Extreme Networks.

## ✨ **Key Features**

- 🔍 **Multi-Engine AI Queries** - OpenAI GPT-4o and Perplexity Sonar
- 📊 **Real-time Metrics Dashboard** - Brand visibility and competitor analysis
- 🤖 **Automated Execution** - Scheduled queries and backfill capabilities
- 💰 **Cost Tracking** - Token usage and pricing optimization
- 📈 **Citation Analysis** - Source quality assessment and ranking
- 🏢 **Competitor Intelligence** - Market share and positioning metrics

## 🚀 **Quick Start**

### **Prerequisites**
- Docker and Docker Compose
- Python 3.9+
- Node.js 16+

### **1. Clone and Setup**
```bash
git clone <repository-url>
cd ExtremeGEOTools
```

### **2. Environment Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
OPENAI_API_KEY=your_openai_key_here
PERPLEXITY_API_KEY=your_perplexity_key_here
```

### **3. Start Services**
```bash
# Start backend and database
docker-compose up -d

# Start frontend
cd frontend
npm install
npm start
```

### **4. Access Dashboard**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📚 **Documentation**

📖 **Complete documentation is available in the [`/docs/`](docs/) folder:**

- **[Project Overview](docs/project-overview.md)** - What is ExtremeGEOTools and current status
- **[System Architecture](docs/architecture.md)** - High-level system design
- **[Codebase Structure](docs/codebase-structure.md)** - File and folder organization
- **[API Contract](docs/api_contract.md)** - Complete API documentation
- **[Documentation Index](docs/README.md)** - Navigate all available docs

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   External      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   APIs          │
│                 │    │                 │    │                 │
│   - Dashboard   │    │   - Routes      │    │   - OpenAI      │
│   - Metrics     │    │   - Services    │    │   - Perplexity  │
│   - Query UI    │    │   - Models      │    │   - Database    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 **Tech Stack**

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: React, CSS3
- **AI Engines**: OpenAI GPT-4o, Perplexity Sonar
- **Automation**: Cron jobs, background workers
- **Deployment**: Docker, Docker Compose

## 📊 **Current Status**

**MVP Progress: 57% Complete**

### ✅ **What's Working**
- Query execution pipeline
- Multi-engine AI integration
- Metrics dashboard
- Automation and scheduling
- Cost tracking

### 🚧 **What's Next**
- Monthly/trend views
- Keyword analysis
- Query management UI
- Enhanced reporting

## 🎯 **Use Cases**

- **Competitive Intelligence** - Track competitor mentions and positioning
- **Brand Monitoring** - Monitor Extreme Networks visibility
- **Market Research** - Analyze industry trends and sentiment
- **Content Strategy** - Identify high-impact topics and sources
- **Cost Optimization** - Monitor AI query costs and efficiency

## 🤝 **Contributing**

This is an internal tool for Extreme Networks competitive intelligence. For questions or contributions, contact the development team.

## 📄 **License**

Internal use only - Extreme Networks

---

**Need Help?** Check the [documentation](docs/) or contact the development team.
