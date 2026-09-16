from fastapi import FastAPI

from app.routers import analytics

app = FastAPI(title="MS5 - Analítico", version="1.0.0")

app.include_router(analytics.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "ms5-analitico"}
