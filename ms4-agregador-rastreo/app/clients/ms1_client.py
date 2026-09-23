import os
from typing import Optional

import httpx

MS1_BASE_URL = os.getenv("MS1_BASE_URL", "http://localhost:8081")


async def get_user(user_id: int, auth_header: Optional[str] = None):
    # Reenvía el Authorization del caller: MS1 exige JWT propio o admin, y MS4 no tiene identidad propia.
    headers = {"Authorization": auth_header} if auth_header else {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"{MS1_BASE_URL}/api/v1/users/{user_id}", headers=headers)
        resp.raise_for_status()
        return resp.json()


async def get_user_public(user_id: int):
    """Solo el nombre, vía el listado interno de MS1 (sin JWT). Sirve para mostrar quién reparte un pedido
    sin exponer el teléfono ni permitir leer perfiles ajenos."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"{MS1_BASE_URL}/api/v1/users", params={"ids": str(user_id)})
        resp.raise_for_status()
        usuarios = resp.json()
        return {"nombre": usuarios[0].get("nombre"), "telefono": None} if usuarios else None
