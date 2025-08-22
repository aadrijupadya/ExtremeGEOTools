from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routes.query import router as query_router
from backend.app.routes.pricing import router as pricing_router
from backend.app.routes.stats import router as stats_router
from backend.app.routes.runs import router as runs_router
from backend.app.routes.metrics import router as metrics_router
from backend.app.routes.scheduler import router as scheduler_router
from backend.app.services.database import init_db

#app configuration and endpoint registration
app = FastAPI()

# CORS for local React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#adding routers/endpoints to backend
app.include_router(query_router)
app.include_router(pricing_router)
app.include_router(stats_router)
app.include_router(runs_router)
app.include_router(metrics_router)
app.include_router(scheduler_router)

#simple health check endpoint
@app.get("/health")
def health():
    return {"ok": True}

# Alias for frontend health check
@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.on_event("startup")
def on_startup():
    # Ensure tables exist (simple create_all; for bigger projects use Alembic migrations)
    init_db()
