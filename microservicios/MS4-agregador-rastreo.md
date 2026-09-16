# MS4 — Agregador / Rastreo

**Stack:** Python (FastAPI) o Node (Express) — **sin base de datos**
**Puerto:** `8084`
**Base path:** `/api/v1`
**Responsable:** Integrante 2
**Docs:** Swagger UI en `/docs`

Servicio 100% orquestador. Cada endpoint dispara llamadas REST síncronas a MS1/MS2/MS3 y devuelve un payload combinado por rol (`customer`, `delivery`, `admin`). No persiste nada.

## Endpoints

### `GET /api/v1/tracking/order/{order_id}`
Rastreo en tiempo real de un pedido (cualquier rol involucrado).

Llamadas internas:
1. `MS3 GET /api/v1/orders/{order_id}` → status (`PEDIDO`/`ENVIADO`/`ENTREGADO`), items, total
2. `MS2 GET /api/v1/restaurants/{restaurant_id}` → nombre/dirección restaurante
3. `MS1 GET /api/v1/users/{customer_id}` → datos cliente
4. `MS1 GET /api/v1/users/{delivery_id}` → datos repartidor (si ya fue asignado)

```json
{
  "order_id": 123,
  "status": "ENVIADO",
  "cliente": { "nombre": "...", "telefono": "..." },
  "repartidor": { "nombre": "...", "telefono": "..." },
  "restaurante": { "nombre": "...", "direccion": "..." },
  "items": [ {"nombre_plato": "...", "cantidad": 2} ],
  "total": 45.90
}
```

### `GET /api/v1/dashboard/customer/{user_id}/summary`
Dashboard del **customer**: historial + estado de pedidos activos.

Llamadas internas: `MS1 GET /users/{user_id}` → `MS3 GET /orders?customer_id=` → `MS2 GET /restaurants/{id}` por cada restaurante distinto.

### `GET /api/v1/dashboard/delivery/{delivery_id}/summary`
Dashboard del **delivery**: pedidos disponibles para jalar + pedidos propios en curso.

Llamadas internas: `MS3 GET /orders/available` (pool general) + `MS3 GET /orders?delivery_id=` (asignados) → `MS2 GET /restaurants/{id}` para direcciones de recojo.

### `GET /api/v1/dashboard/admin/{restaurant_id}/summary`
Dashboard del **admin** de restaurante: pedidos por estado + clientes del restaurante.

Llamadas internas: `MS2 GET /restaurants/{restaurant_id}` → `MS3 GET /orders?restaurant_id=&status=` → `MS3 GET /restaurants/{restaurant_id}/customers` (que a su vez resuelve nombres vía MS1).

### Infra
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Healthcheck |
| GET | `/docs` | Swagger UI |

## Consumido por
- **Frontend** → tras login, cada rol pega a su dashboard (`/dashboard/{rol}/...`) + tracking de pedido puntual

## Este servicio consume
- **MS1** → `GET /api/v1/users/{user_id}`
- **MS2** → `GET /api/v1/restaurants/{restaurant_id}`
- **MS3** → `GET /api/v1/orders/{order_id}`, `GET /api/v1/orders?customer_id=|delivery_id=|restaurant_id=`, `GET /api/v1/orders/available`, `GET /api/v1/restaurants/{restaurant_id}/customers`

## Variables de entorno
```
MS1_BASE_URL=http://ms1:8081
MS2_BASE_URL=http://ms2:8082
MS3_BASE_URL=http://ms3:8083
```
