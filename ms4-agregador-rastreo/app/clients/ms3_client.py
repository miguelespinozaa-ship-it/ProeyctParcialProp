import os
from typing import Optional

import httpx

MS3_BASE_URL = os.getenv("MS3_BASE_URL", "http://localhost:8083")


def _clean(params: dict) -> dict:
    return {k: v for k, v in params.items() if v is not None}


async def get_order(order_id: int):
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"{MS3_BASE_URL}/api/v1/orders/{order_id}")
        resp.raise_for_status()
        return resp.json()


async def list_orders(**params):
    """Sin page/page_size devuelve un array (todo); con ellos, un objeto paginado {items, total, ...}."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{MS3_BASE_URL}/api/v1/orders", params=_clean(params))
        resp.raise_for_status()
        return resp.json()


async def orders_summary(**params):
    """Cantidad de pedidos por estado, sin traer las filas (?restaurant_id= / ?customer_id= / ?delivery_id=)."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"{MS3_BASE_URL}/api/v1/orders/summary", params=_clean(params))
        resp.raise_for_status()
        return resp.json()


async def list_available_orders(auth_header: Optional[str] = None, **params):
    # GET /orders/available exige rol delivery en MS3 — reenviar el Authorization del caller.
    headers = {"Authorization": auth_header} if auth_header else {}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{MS3_BASE_URL}/api/v1/orders/available", headers=headers, params=_clean(params)
        )
        resp.raise_for_status()
        return resp.json()


async def get_restaurant_customers(restaurant_id: str, **params):
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{MS3_BASE_URL}/api/v1/restaurants/{restaurant_id}/customers", params=_clean(params)
        )
        resp.raise_for_status()
        return resp.json()
