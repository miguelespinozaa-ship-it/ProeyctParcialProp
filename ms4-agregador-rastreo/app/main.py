from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import dashboard, tracking

app = FastAPI(title="MS4 - Agregador/Rastreo", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ForwardedPrefixMiddleware:
    """Detrás de NGINX/API Gateway el servicio vive bajo /msN: usa X-Forwarded-Prefix como root_path para que Swagger UI arme bien sus URLs."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            for name, value in scope["headers"]:
                if name == b"x-forwarded-prefix":
                    scope = {**scope, "root_path": value.decode().rstrip("/")}
                    break
        await self.app(scope, receive, send)


app.add_middleware(ForwardedPrefixMiddleware)


app.include_router(tracking.router)
app.include_router(dashboard.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "ms4-agregador-rastreo"}
