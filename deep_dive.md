# Deep Dive Guide: ExtremeGEOTools Codebase

## **Timeline Estimate: 2-3 days (8-12 hours)**

This guide will help you understand how the entire system works, from database models to frontend components.

## **Recommended Order:**

### **Day 1: Backend Foundation (3-4 hours)**

#### 1. **Start with `backend/main.py`** (30 min)
- This is the entry point - see how FastAPI is set up
- Understand the router registration and middleware
- See how CORS is configured for frontend communication
- Check the startup/shutdown event handlers

#### 2. **Database models in `backend/app/models/`** (1 hour)
- **`run.py`** - understand the core data structure
  - What fields are stored for each query execution
  - How entities, citations, and costs are tracked
  - Understanding the JSONB fields for flexible data storage
- **`metrics.py`** - see how aggregated data is stored
  - Daily metrics aggregation
  - Brand context and competitor analysis
- **`automated_run.py`** - understand automated query structure
  - How scheduled queries are managed
  - Difference between manual and automated runs

#### 3. **Database service in `backend/app/services/database.py`** (30 min)
- See how database connections are managed
- Understand session handling and connection pooling
- Check the initialization and cleanup processes

#### 4. **Core services in `backend/app/services/`** (1-1.5 hours)
- **`extract.py`** - understand how entities/citations are extracted
  - Competitor name extraction logic
  - URL and domain parsing
  - Ranking system implementation
- **`pricing.py`** - see how costs are calculated
  - Token-based pricing for different models
  - Cost optimization recommendations
- **`metrics.py`** - understand how data is aggregated
  - Daily metrics computation
  - Competitive intelligence analysis

### **Day 2: API Layer & Business Logic (3-4 hours)**

#### 1. **API routes in `backend/app/routes/`** (1.5 hours)
- **`query.py`** - see how queries are executed
  - Query submission and validation
  - Engine selection and model configuration
  - Real-time streaming responses
- **`runs.py`** - understand run management
  - Run history and filtering
  - Run details and metadata
  - Soft delete functionality
- **`metrics.py`** - see how analytics are served
  - Enhanced analysis endpoints
  - Daily metrics aggregation
  - Competitor insights

#### 2. **Query execution in `backend/app/services/`** (1 hour)
- **`run_query.py`** - understand the main query pipeline
  - How queries are routed to different engines
  - Response processing and extraction
  - Error handling and retry logic
- **`engines.py`** - see how different AI engines are handled
  - OpenAI integration
  - Perplexity integration
  - Engine-specific response parsing

#### 3. **Scripts in `scripts/`** (1 hour)
- **`post_process_metrics.py`** - understand the data processing pipeline
  - How raw responses are processed into insights
  - Competitor analysis and ranking
  - Citation quality assessment
- **`run_automated_queries.py`** - see how automated queries work
  - Scheduled query execution
  - Template-based query generation
  - Results aggregation

### **Day 3: Frontend & Integration (2-3 hours)**

#### 1. **Frontend structure in `frontend/src/`** (1 hour)
- **`App.js`** - understand routing and main structure
  - React Router setup
  - Component composition
  - Global state management
- **`components/`** - see how different pages are built
  - Page structure and navigation
  - Component hierarchy

#### 2. **API integration in `frontend/src/services/api.js`** (30 min)
- Understand how frontend talks to backend
- API endpoint management
- Error handling and response processing
- Request/response data flow

#### 3. **Key components** (1 hour)
- **`AutomatedQueryDashboard.js`** - see how metrics are displayed
  - Data visualization and charts
  - Filter controls and user interaction
  - Real-time data updates
- **`QueryForm.js`** - understand query submission
  - Form validation and submission
  - Engine and model selection
  - Parameter configuration

## **Key Concepts to Focus On:**

### 1. **Data Flow Architecture**
```
User Query → Frontend Form → Backend API → AI Engine → 
Response Processing → Entity Extraction → Database Storage → 
Metrics Aggregation → Dashboard Display
```

### 2. **Database Schema Understanding**
- **Runs Table**: Stores individual query executions with full metadata
- **Daily Metrics Table**: Aggregated daily statistics for analysis
- **JSONB Fields**: Flexible storage for entities, citations, and enriched data

### 3. **API Structure**
- RESTful endpoints with consistent response formats
- Query parameters for filtering and pagination
- Error handling and status codes
- Data transformation between database and API responses

### 4. **Frontend State Management**
- React hooks for local state
- API service layer for backend communication
- Component props and data flow
- User interaction and form handling

## **Quick Wins (1 hour total):**

- **Start with `backend/main.py`** - this gives you the big picture
- **Look at `backend/app/models/run.py`** - this shows you what data looks like
- **Check `frontend/src/App.js`** - this shows you the user flow

## **What to Skip Initially:**

- CSS/styling details
- Complex business logic in metrics calculations
- Docker/deployment configuration
- Alembic migration details
- Advanced error handling edge cases

## **Pro Tips for Understanding:**

### 1. **Use the Browser Dev Tools**
- Open Network tab to see what API calls the frontend is making
- Check Console for any error messages or debugging output
- Use React DevTools to inspect component state

### 2. **Check the Database Directly**
- Connect to PostgreSQL to see what data actually exists
- Run simple queries to understand the data structure
- Check if the data matches what you expect

### 3. **Follow One Query Through the System**
- Submit a test query from the frontend
- Watch the backend logs to see the processing
- Check the database to see what was stored
- Verify the frontend displays the results correctly

### 4. **Look at Console Logs**
- The frontend has debugging output for API calls
- Backend has logging for request processing
- Check for any error messages or warnings

## **Common Gotchas to Watch For:**

1. **Import Paths**: The backend expects to be run from the root directory
2. **Database Connections**: Check if PostgreSQL is running and accessible
3. **API Endpoints**: Verify the frontend is calling the correct backend URLs
4. **Data Format**: JSONB fields can have different structures
5. **Async Operations**: Many operations are asynchronous, check for proper await usage

## **When You're Ready to Dive Deeper:**

- **Performance Optimization**: Database query optimization, caching strategies
- **Error Handling**: Comprehensive error handling and user feedback
- **Testing**: Unit tests, integration tests, and end-to-end testing
- **Deployment**: Docker configuration, environment variables, production setup
- **Monitoring**: Logging, metrics collection, and alerting

## **Questions to Ask Yourself While Reading:**

1. **What happens when a user submits a query?**
2. **How is the response processed and stored?**
3. **What data is aggregated for the dashboard?**
4. **How does the frontend get and display the data?**
5. **What happens when something goes wrong?**

## **Resources for Further Learning:**

- **FastAPI Documentation**: For understanding the backend framework
- **React Documentation**: For frontend component patterns
- **SQLAlchemy Documentation**: For database ORM understanding
- **PostgreSQL JSONB**: For understanding the flexible data storage

---

**Remember**: Start with the high-level flow, then dive into specific components. Don't try to understand everything at once - focus on one piece at a time and build your mental model gradually.

Good luck with the deep dive! 🚀
