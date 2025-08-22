# ExtremeGEOTools Codebase Structure

## Root Directory Overview
The project follows a clear separation between backend (FastAPI), frontend (React), and supporting infrastructure.

## Backend (`/backend/`)
**Purpose**: FastAPI backend server handling all business logic, database operations, and API endpoints.

### `/backend/app/` - Main Application Code
- **`__init__.py`** - Python package initialization
- **`main.py`** - FastAPI application entry point and server configuration

#### `/backend/app/models/` - Database Models
- **`__init__.py`** - Models package initialization
- **`automated_run.py`** - Automated query execution records
- **`metrics.py`** - Daily metrics and aggregated data
- **`run.py`** - Individual query run records

#### `/backend/app/routes/` - API Endpoints
- **`__init__.py`** - Routes package initialization
- **`metrics.py`** - Main business logic endpoints (enhanced analysis, competitor insights)
- **`pricing.py`** - Cost calculation and pricing endpoints
- **`query.py`** - Query management endpoints
- **`runs.py`** - Query execution history endpoints
- **`scheduler.py`** - Automation scheduling endpoints
- **`stats.py`** - General statistics endpoints

#### `/backend/app/schemas/` - Data Validation
- **`__init__.py`** - Schemas package initialization
- **`query_schemas.py`** - Pydantic models for request/response validation

#### `/backend/app/services/` - Business Logic Layer
- **`__init__.py`** - Services package initialization
- **`database.py`** - Database connection and session management
- **`engines.py`** - Query execution engine orchestration
- **`extract.py`** - Data extraction and processing from AI responses
- **`metrics.py`** - Metrics calculation and aggregation
- **`pricing.py`** - Cost estimation and pricing calculations
- **`query_scheduler.py`** - Automated query scheduling logic
- **`run_query.py`** - Core query execution pipeline
- **`db_writer.py`** - Database persistence functionality

##### `/backend/app/services/adapters/` - External API Integrations
- **`__init__.py`** - Adapters package initialization
- **`chatgpt_api.py`** - OpenAI API integration
- **`perplexity.py`** - Perplexity API integration

#### `/backend/app/utils/` - Utility Functions
- **`__init__.py`** - Utils package initialization

### `/backend/alembic/` - Database Migrations
- **`env.py`** - Alembic environment configuration
- **`script.py.mako`** - Migration template
- **`README`** - Migration documentation
- **`versions/`** - Individual migration files
  - **`0001_initial_and_indexes.py`** - Initial database setup
  - **`0002_add_deleted_column.py`** - Soft delete functionality
  - **`0003_add_daily_metrics.py`** - Daily metrics table
  - **`0004_add_source_column.py`** - Source tracking
  - **`0005_create_automated_runs_table.py`** - Automated runs table

### `/backend/scripts/` - Backend Utility Scripts
- **`compute_metrics.py`** - Batch metrics computation
- **`automated_scheduler.py`** - Automated query execution
- **`run_automated_queries.py`** - Query runner script
- **`run_daily_queries.py`** - Daily query execution
- **`setup_cron.sh`** - Cron job setup
- **`test_automated_scheduler.py`** - Scheduler testing
- **`test_query_scheduler.py`** - Query scheduler testing

## Frontend (`/frontend/`)
**Purpose**: React-based user interface for interacting with the backend APIs.

### `/frontend/public/` - Static Assets
- **`index.html`** - Main HTML template
- **`icons/`** - Application icons
  - **`chatgpt.png`** - OpenAI logo
  - **`perplexity.png`** - Perplexity logo
  - **`README.md`** - Icons documentation

### `/frontend/src/` - React Source Code
- **`index.js`** - React application entry point
- **`App.js`** - Main application component and routing
- **`App.css`** - Global application styles

#### `/frontend/src/components/` - React Components
- **`Header.js`** - Application header/navigation
- **`Home.js`** - Landing page component
- **`Dashboard.js`** - Main dashboard wrapper
- **`QueryPage.js`** - Query creation and management
- **`QueryForm.js`** - Query input form
- **`ResultsPage.js`** - Query results display
- **`ResultsTable.js`** - Results data table
- **`RunDetailPage.js`** - Individual run details
- **`RunLivePage.js`** - Live query execution
- **`MetricsDashboard.js`** - Main metrics dashboard
- **`EnhancedMetricsDashboard.js`** - Advanced metrics view
- **`CompetitorAnalysisDetail.js`** - Competitor analysis details
- **`QueryOverviewDetail.js`** - Query overview details
- **`CostsPage.js`** - Cost tracking and analysis
- **`Scheduler.js`** - Query scheduling interface
- **`AutomatedQueryDashboard.js`** - Automated queries dashboard
- **`BrandIcon.js`** - Brand icon component
- **`EngineIcon.js`** - Engine icon component

#### `/frontend/src/hooks/` - Custom React Hooks
- **`usePersistentDraft.js`** - Persistent form data hook

#### `/frontend/src/services/` - API Integration
- **`api.js`** - HTTP client and API endpoint functions

#### `/frontend/src/styles/` - Component Styles
- **`App.css`** - Global application styles

### `/frontend/package.json` - Node.js dependencies and scripts
### `/frontend/package-lock.json` - Locked dependency versions

## Data (`/data/`)
**Purpose**: Application data storage and configuration.

### `/data/dashboard/` - Dashboard Data
- **`latest_summary.json`** - Latest dashboard summary data

### `/data/queries/` - Query Configuration
- **`system_queries.json`** - System-defined query templates

### `/data/storage/` - Data Storage
- Application data storage directory

## Documentation (`/docs/`)
**Purpose**: Project documentation and API specifications.

- **`api_contract.md`** - API endpoint specifications
- **`architecture.md`** - System architecture documentation
- **`repo.md`** - Repository overview and setup

## Infrastructure Files
- **`docker-compose.yml`** - Docker container orchestration
- **`requirements.txt`** - Python backend dependencies
- **`alembic.ini`** - Database migration configuration
- **`README.md`** - Project overview and setup instructions

## Scripts (`/scripts/`)
**Purpose**: Root-level utility scripts and automation.

- **`automated_scheduler.py`** - Main automation script
- **`debug_ranking_data.py`** - Data debugging utility
- **`post_process_metrics.py`** - Metrics post-processing
- **`run_automated_queries.py`** - Query execution script
- **`run_daily_queries.py`** - Daily query runner
- **`setup_cron.sh`** - Cron job configuration
- **`test_automated_scheduler.py`** - Scheduler testing
- **`test_query_scheduler.py`** - Query scheduler testing

## Other Files
- **`deep_dive.md`** - Codebase deep dive guide
- **`models.txt`** - Model documentation
- **`logs/`** - Application log files
- **`venv/`** - Python virtual environment

## Key Architectural Patterns

### Backend Architecture
- **FastAPI** for REST API endpoints
- **SQLAlchemy** for database ORM
- **Alembic** for database migrations
- **Service layer** for business logic separation
- **Adapter pattern** for external API integrations

### Frontend Architecture
- **React** for component-based UI
- **Functional components** with hooks
- **Service layer** for API communication
- **Component composition** for reusability

### Data Flow
1. **Frontend** sends requests via API service
2. **Backend routes** receive and validate requests
3. **Services** execute business logic
4. **Models** interact with database
5. **Response** flows back through the same path

### Automation
- **QueryScheduler** service manages automated execution
- **Cron jobs** trigger scheduled queries
- **Background workers** process queries asynchronously
- **Metrics computation** runs on schedule
