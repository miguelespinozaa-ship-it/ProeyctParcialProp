import os

import httpx

MS2_BASE_URL = os.getenv("MS2_BASE_URL", "http://localhost:8082")


async def get_restaurant(restaurant_id: str):
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"{MS2_BASE_URL}/api/v1/restaurants/{restaurant_id}")
        resp.raise_for_status()
        return resp.json()
