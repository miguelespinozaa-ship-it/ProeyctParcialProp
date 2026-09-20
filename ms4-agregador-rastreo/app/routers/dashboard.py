import asyncio
from typing import Literal, Optional

import httpx
from fastapi import APIRouter, Header, HTTPException, Query

from app.clients import ms1_client, ms2_client, ms3_client

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

# Todos los dashboards tienen dos modos:
#  - sin page/page_size (ni status en admin): respuesta completa, exactamente como antes.
#  - con ellos: respuesta paginada, que usa el resumen por estado de MS3 y trae solo la página pedida.
# En el modo paginado, {items, page, page_size, total, total_pages} viene tal cual de MS3.

Estado = Literal["PEDIDO", "ENVIADO", "ENTREGADO"]


async def _resolve_restaurantes(pedidos: list[dict]) -> dict:
    restaurantes = {}
    for rid in {p["restaurant_id"] for p in pedidos}:
        try:
            r = await ms2_client.get_restaurant(rid)
            restaurantes[rid] = {"nombre": r.get("nombre"), "direccion": r.get("direccion")}
        except httpx.HTTPError:
            restaurantes[rid] = None
    return restaurantes


async def _with_restaurante(pedidos: list[dict]) -> list[dict]:
    restaurantes = await _resolve_restaurantes(pedidos)
    return [{**p, "restaurante": restaurantes.get(p["restaurant_id"])} for p in pedidos]


def _ms3_unavailable() -> HTTPException:
    return HTTPException(status_code=502, detail="MS3 no disponible")


# ---------------------------------------------------------------- customer

@router.get("/customer/{user_id}/summary")
async def customer_summary(
    user_id: int,
    authorization: Optional[str] = Header(None),
    page: Optional[int] = Query(None, ge=1, description="Activa el modo paginado (historial)"),
    page_size: Optional[int] = Query(None, ge=1, description="Por defecto 20, máximo 100"),
):
    try:
        perfil = await ms1_client.get_user(user_id, auth_header=authorization)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        raise HTTPException(status_code=502, detail="MS1 no disponible")
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="MS1 no disponible")

    usuario = {"nombre": perfil.get("nombre"), "email": perfil.get("email")}

    if page is None and page_size is None:
        try:
            pedidos = await ms3_client.list_orders(customer_id=user_id)
        except httpx.HTTPError:
            raise _ms3_unavailable()

        restaurantes = await _resolve_restaurantes(pedidos)
        pedidos_activos = [p for p in pedidos if p["status"] != "ENTREGADO"]
        return {
            "usuario": usuario,
            "pedidos_activos": [{**p, "restaurante": restaurantes.get(p["restaurant_id"])} for p in pedidos_activos],
            "historial": [{**p, "restaurante": restaurantes.get(p["restaurant_id"])} for p in pedidos],
        }

    try:
        resumen, historial, en_pedido, en_camino = await asyncio.gather(
            ms3_client.orders_summary(customer_id=user_id),
            ms3_client.list_orders(customer_id=user_id, page=page, page_size=page_size),
            ms3_client.list_orders(customer_id=user_id, status="PEDIDO", page=1, page_size=50),
            ms3_client.list_orders(customer_id=user_id, status="ENVIADO", page=1, page_size=50),
        )
    except httpx.HTTPError:
        raise _ms3_unavailable()

    historial["items"] = await _with_restaurante(historial["items"])
    return {
        "usuario": usuario,
        "resumen": resumen,
        "pedidos_activos": await _with_restaurante(en_pedido["items"] + en_camino["items"]),
        "historial": historial,
    }


# ---------------------------------------------------------------- delivery

@router.get("/delivery/{delivery_id}/summary")
async def delivery_summary(
    delivery_id: int,
    authorization: Optional[str] = Header(None),
    page: Optional[int] = Query(None, ge=1, description="Activa el modo paginado (pool de disponibles)"),
    page_size: Optional[int] = Query(None, ge=1, description="Por defecto 20, máximo 100"),
    curso_page: int = Query(1, ge=1, description="Página de las entregas en curso (modo paginado)"),
):
    if page is None and page_size is None:
        try:
            disponibles, asignados = await asyncio.gather(
                ms3_client.list_available_orders(auth_header=authorization),
                ms3_client.list_orders(delivery_id=delivery_id),
            )
        except httpx.HTTPError:
            raise _ms3_unavailable()

        restaurantes = await _resolve_restaurantes(disponibles + asignados)
        return {
            "disponibles": [{**p, "restaurante": restaurantes.get(p["restaurant_id"])} for p in disponibles],
            "en_curso": [{**p, "restaurante": restaurantes.get(p["restaurant_id"])} for p in asignados],
        }

    try:
        resumen, disponibles, en_curso = await asyncio.gather(
            ms3_client.orders_summary(delivery_id=delivery_id),
            ms3_client.list_available_orders(auth_header=authorization, page=page, page_size=page_size),
            ms3_client.list_orders(delivery_id=delivery_id, status="ENVIADO", page=curso_page, page_size=page_size),
        )
    except httpx.HTTPError:
        raise _ms3_unavailable()

    disponibles["items"] = await _with_restaurante(disponibles["items"])
    en_curso["items"] = await _with_restaurante(en_curso["items"])
    return {"resumen": resumen, "disponibles": disponibles, "en_curso": en_curso}


# ---------------------------------------------------------------- admin

@router.get("/admin/{restaurant_id}/summary")
async def admin_summary(
    restaurant_id: str,
    page: Optional[int] = Query(None, ge=1, description="Activa el modo paginado (pedidos del estado elegido)"),
    page_size: Optional[int] = Query(None, ge=1, description="Por defecto 20, máximo 100"),
    status: Optional[Estado] = Query(None, description="Estado a listar en modo paginado (por defecto PEDIDO)"),
    customers_page: int = Query(1, ge=1, description="Página de clientes (modo paginado)"),
):
    try:
        restaurante = await ms2_client.get_restaurant(restaurant_id)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Restaurante no encontrado")
        raise HTTPException(status_code=502, detail="MS2 no disponible")
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="MS2 no disponible")

    datos_restaurante = {"nombre": restaurante.get("nombre"), "direccion": restaurante.get("direccion")}

    if page is None and page_size is None and status is None:
        try:
            pedidos = await ms3_client.list_orders(restaurant_id=restaurant_id)
        except httpx.HTTPError:
            raise _ms3_unavailable()

        try:
            clientes = await ms3_client.get_restaurant_customers(restaurant_id)
        except httpx.HTTPError:
            clientes = []

        por_estado: dict[str, list] = {"PEDIDO": [], "ENVIADO": [], "ENTREGADO": []}
        for p in pedidos:
            por_estado.setdefault(p["status"], []).append(p)

        return {"restaurante": datos_restaurante, "pedidos_por_estado": por_estado, "clientes": clientes}

    estado = status or "PEDIDO"
    resultados = await asyncio.gather(
        ms3_client.orders_summary(restaurant_id=restaurant_id),
        ms3_client.list_orders(restaurant_id=restaurant_id, status=estado, page=page, page_size=page_size, include_items="true"),
        ms3_client.get_restaurant_customers(restaurant_id, page=customers_page, page_size=page_size),
        return_exceptions=True,
    )
    resumen, pedidos, clientes = resultados
    # resumen y pedidos son esenciales; los clientes degradan a null si MS3/MS1 fallan.
    for esencial in (resumen, pedidos):
        if isinstance(esencial, Exception):
            raise _ms3_unavailable()
    if isinstance(clientes, Exception):
        clientes = None

    return {
        "restaurante": datos_restaurante,
        "resumen": resumen,
        "estado": estado,
        "pedidos": pedidos,
        "clientes": clientes,
    }
