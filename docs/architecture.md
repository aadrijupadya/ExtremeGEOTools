# ExtremeGEOTools - System Architecture

## 🏗️ **High-Level Architecture**

ExtremeGEOTools follows a **microservices-inspired architecture** with clear separation of concerns:

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

## 🔄 **Data Flow Architecture**

### **1. Query Execution Flow**
```
User Input → QueryForm → FastAPI → Engine Adapter → AI Engine → Response Processing → Database Storage → Dashboard Display
```

### **2. Metrics Computation Flow**
```
Automated Queries → Data Collection → Post-Processing → Metrics Calculation → Daily Aggregation → Dashboard Metrics
```

### **3. Real-time Processing Flow**
```
Live Query → Streaming Response → Real-time Processing → Immediate Storage → Live Dashboard Update
```

## 🗄️ **Database Architecture**

### **Core Tables**
- **`automated_runs`** - Query execution records
- **`daily_metrics`** - Aggregated daily statistics
- **`queries`** - Stored query templates

### **Data Relationships**
```
AutomatedRun (1) ←→ (1) DailyMetrics
AutomatedRun (many) ←→ (1) Query
DailyMetrics (many) ←→ (1) Engine
```

### **Key Design Decisions**
- **Denormalized metrics** for fast dashboard queries
- **Soft deletes** for data retention
- **JSON fields** for flexible citation and entity storage
- **Time-series optimization** for historical analysis

## 🔌 **Service Layer Architecture**

### **Core Services**
```
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                           │
├─────────────────────────────────────────────────────────────┤
│  QueryService     │  MetricsService  │  PricingService    │
│  - Query exec    │  - Aggregation    │  - Cost calc       │
├─────────────────────────────────────────────────────────────┤
│  EngineService    │  ExtractService   │  SchedulerService  │
│  - AI engine mgmt│  - Data extraction│  - Automation      │
└─────────────────────────────────────────────────────────────┘
```

### **Service Responsibilities**
- **`QueryService`** - Orchestrates query execution
- **`MetricsService`** - Computes and aggregates metrics
- **`EngineService`** - Manages AI engine interactions
- **`ExtractService`** - Processes AI responses
- **`SchedulerService`** - Handles automated execution

## 🌐 **API Architecture**

### **REST Endpoints**
```
/api/v1/
├── /query          # Query execution
├── /runs           # Run history
├── /metrics        # Dashboard metrics
├── /scheduler      # Automation control
└── /stats          # System statistics
```

### **API Design Principles**
- **RESTful conventions** for CRUD operations
- **Query parameters** for filtering and pagination
- **Consistent response formats** across endpoints
- **Error handling** with proper HTTP status codes
- **Rate limiting** for external API calls

## 🔄 **Frontend Architecture**

### **Component Hierarchy**
```
App
├── Header
├── Router
│   ├── Home
│   ├── QueryPage
│   ├── MetricsDashboard
│   ├── CompetitorAnalysis
│   └── CostsPage
└── Footer
```

### **State Management**
- **React Hooks** for local component state
- **Context API** for shared application state
- **Local Storage** for user preferences
- **API Services** for data fetching

### **Data Flow**
```
API Response → Component State → UI Rendering → User Interaction → API Request
```

## 🚀 **Automation Architecture**

### **Scheduling System**
```
Cron Jobs → Query Scheduler → Engine Execution → Data Processing → Metrics Update → Dashboard Refresh
```

### **Background Processing**
- **Redis Queue** for job management (planned)
- **Worker processes** for parallel execution
- **Retry mechanisms** for failed queries
- **Monitoring** for system health

## 🔒 **Security Architecture**

### **Authentication & Authorization**
- **API Key management** for external services
- **Environment variables** for sensitive data
- **Input validation** for all user inputs
- **SQL injection protection** via SQLAlchemy ORM

### **Data Protection**
- **HTTPS encryption** for data in transit
- **Database access control** via connection pooling
- **Audit logging** for all operations
- **Data retention policies** for compliance

## 📊 **Monitoring & Observability**

### **Logging Strategy**
- **Structured logging** with consistent formats
- **Log levels** for different environments
- **Centralized logging** for debugging
- **Performance metrics** for optimization

### **Health Checks**
- **Database connectivity** monitoring
- **External API** availability checks
- **Service health** endpoints
- **Automated alerting** for failures

## 🚀 **Deployment Architecture**

### **Container Strategy**
```
Docker Compose
├── PostgreSQL Database
├── FastAPI Backend
├── React Frontend
└── Redis (planned)
```

### **Environment Management**
- **Development** - Local Docker setup
- **Staging** - Production-like environment
- **Production** - Managed cloud deployment

## 🔮 **Future Architecture Considerations**

### **Scalability Improvements**
- **Horizontal scaling** for backend services
- **Load balancing** for multiple instances
- **Database sharding** for large datasets
- **CDN integration** for static assets

### **Advanced Features**
- **Real-time notifications** via WebSockets
- **Advanced analytics** with data warehouses
- **Machine learning** for predictive insights
- **Multi-tenant support** for enterprise use
