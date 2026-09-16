import asyncio
from typing import Optional

import httpx
from fastapi import APIRouter, Header, HTTPException

from app.clients import ms1_client, ms2_client, ms3_client

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


async def _resolve_restaurantes(pedidos: list[dict]) -> dict:
    restaurantes = {}
    for rid in {p["restaurant_id"] for p in pedidos}:
        try:
            r = await ms2_client.get_restaurant(rid)
            restaurantes[rid] = {"nombre": r.get("nombre"), "direccion": r.get("direccion")}
        except httpx.HTTPError:
            restaurantes[rid] = None
    return restaurantes


@router.get("/customer/{user_id}/summary")
async def customer_summary(user_id: int, authorization: Optional[str] = Header(None)):
    try:
        perfil = await ms1_client.get_user(user_id, auth_header=authorization)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        raise HTTPException(status_code=502, detail="MS1 no disponible")
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="MS1 no disponible")

    try:
        pedidos = await ms3_client.list_orders(customer_id=user_id)
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="MS3 no disponible")

    restaurantes = await _resolve_restaurantes(pedidos)
    pedidos_activos = [p for p in pedidos if p["status"] != "ENTREGADO"]

    return {
        "usuario": {"nombre": perfil.get("nombre"), "email": perfil.get("email")},
        "pedidos_activos": [{**p, "restaurante": restaurantes.get(p["restaurant_id"])} for p in pedidos_activos],
        "historial": [{**p, "restaurante": restaurantes.get(p["restaurant_id"])} for p in pedidos],
    }


@router.get("/delivery/{delivery_id}/summary")
async def delivery_summary(delivery_id: int, authorization: Optional[str] = Header(None)):
    try:
        disponibles, asignados = await asyncio.gather(
            ms3_client.list_available_orders(auth_header=authorization),
            ms3_client.list_orders(delivery_id=delivery_id),
        )
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="MS3 no disponible")

    restaurantes = await _resolve_restaurantes(disponibles + asignados)

    return {
        "disponibles": [{**p, "restaurante": restaurantes.get(p["restaurant_id"])} for p in disponibles],
        "en_curso": [{**p, "restaurante": restaurantes.get(p["restaurant_id"])} for p in asignados],
    }


@router.get("/admin/{restaurant_id}/summary")
async def admin_summary(restaurant_id: str):
    try:
        restaurante = await ms2_client.get_restaurant(restaurant_id)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Restaurante no encontrado")
        raise HTTPException(status_code=502, detail="MS2 no disponible")
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="MS2 no disponible")

    try:
        pedidos = await ms3_client.list_orders(restaurant_id=restaurant_id)
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="MS3 no disponible")

    try:
        clientes = await ms3_client.get_restaurant_customers(restaurant_id)
    except httpx.HTTPError:
        clientes = []

    por_estado: dict[str, list] = {"PEDIDO": [], "ENVIADO": [], "ENTREGADO": []}
    for p in pedidos:
        por_estado.setdefault(p["status"], []).append(p)

    return {
        "restaurante": {"nombre": restaurante.get("nombre"), "direccion": restaurante.get("direccion")},
        "pedidos_por_estado": por_estado,
        "clientes": clientes,
    }
