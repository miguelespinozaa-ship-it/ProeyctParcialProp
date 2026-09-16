from fastapi import FastAPI

from app.routers import addresses, auth, users

app = FastAPI(title="MS1 - Usuarios/Auth", version="1.0.0")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(addresses.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "ms1-usuarios-auth"}
