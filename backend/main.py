from fastapi import FastAPI
from backend.app.routes.query import router as query_router

app = FastAPI()
app.include_router(query_router)

@app.get("/health") 
def health(): return {"ok": True}
