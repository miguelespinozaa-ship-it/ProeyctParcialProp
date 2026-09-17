from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import analytics

app = FastAPI(title="MS5 - Analítico", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analytics.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "ms5-analitico"}
