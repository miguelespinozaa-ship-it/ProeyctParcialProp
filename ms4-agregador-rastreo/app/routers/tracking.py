from typing import Optional

import httpx
from fastapi import APIRouter, Header, HTTPException

from app.clients import ms1_client, ms2_client, ms3_client

router = APIRouter(prefix="/api/v1/tracking", tags=["tracking"])


@router.get("/order/{order_id}")
async def track_order(order_id: int, authorization: Optional[str] = Header(None)):
    """Combina MS3 (status/items/total) + MS2 (restaurante) + MS1 (cliente/repartidor).

    MS3 es la fuente del pedido en sí: si no responde, la request completa falla con 502/404.
    MS1/MS2 son datos complementarios: si fallan, se degrada a null en vez de tumbar todo el tracking.
    """
    try:
        order = await ms3_client.get_order(order_id)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        raise HTTPException(status_code=502, detail="MS3 no disponible")
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="MS3 no disponible")

    restaurante = None
    try:
        r = await ms2_client.get_restaurant(order["restaurant_id"])
        restaurante = {"nombre": r.get("nombre"), "direccion": r.get("direccion")}
    except httpx.HTTPError:
        pass

    cliente = None
    try:
        u = await ms1_client.get_user(order["customer_id"], auth_header=authorization)
        cliente = {"nombre": u.get("nombre"), "telefono": u.get("telefono")}
    except httpx.HTTPError:
        pass

    repartidor = None
    if order.get("delivery_id"):
        try:
            d = await ms1_client.get_user(order["delivery_id"], auth_header=authorization)
            repartidor = {"nombre": d.get("nombre"), "telefono": d.get("telefono")}
        except httpx.HTTPError:
            pass

    items = [
        {"nombre_plato": it["nombre_plato"], "cantidad": it["cantidad"]}
        for it in order.get("items", [])
    ]

    return {
        "order_id": order["id"],
        "status": order["status"],
        "cliente": cliente,
        "repartidor": repartidor,
        "restaurante": restaurante,
        "items": items,
        "total": order["total"],
    }
