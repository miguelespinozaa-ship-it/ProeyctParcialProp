from fastapi import FastAPI

from app.routers import dashboard, tracking

app = FastAPI(title="MS4 - Agregador/Rastreo", version="1.0.0")

app.include_router(tracking.router)
app.include_router(dashboard.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "ms4-agregador-rastreo"}
