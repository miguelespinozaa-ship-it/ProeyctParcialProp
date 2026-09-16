import os
from typing import Optional

import httpx

MS1_BASE_URL = os.getenv("MS1_BASE_URL", "http://localhost:8081")


async def get_user(user_id: int, auth_header: Optional[str] = None):
    # GET /users/{id} exige JWT propio o admin en MS1 — hay que reenviar el Authorization
    # del caller original (frontend), MS4 no tiene identidad propia.
    headers = {"Authorization": auth_header} if auth_header else {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"{MS1_BASE_URL}/api/v1/users/{user_id}", headers=headers)
        resp.raise_for_status()
        return resp.json()
