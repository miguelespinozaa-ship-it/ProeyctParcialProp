import os
from typing import Optional

import httpx

MS3_BASE_URL = os.getenv("MS3_BASE_URL", "http://localhost:8083")


async def get_order(order_id: int):
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"{MS3_BASE_URL}/api/v1/orders/{order_id}")
        resp.raise_for_status()
        return resp.json()


async def list_orders(**params):
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"{MS3_BASE_URL}/api/v1/orders", params=params)
        resp.raise_for_status()
        return resp.json()


async def list_available_orders(auth_header: Optional[str] = None):
    # GET /orders/available exige rol delivery en MS3 — reenviar el Authorization del caller.
    headers = {"Authorization": auth_header} if auth_header else {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"{MS3_BASE_URL}/api/v1/orders/available", headers=headers)
        resp.raise_for_status()
        return resp.json()


async def get_restaurant_customers(restaurant_id: str):
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"{MS3_BASE_URL}/api/v1/restaurants/{restaurant_id}/customers")
        resp.raise_for_status()
        return resp.json()
