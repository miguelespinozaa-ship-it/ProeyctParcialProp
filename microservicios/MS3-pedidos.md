# MS3 — Pedidos (Orders)

**Stack:** Node.js (Express) + PostgreSQL 16
**Puerto:** `8083`
**Base path:** `/api/v1`
**Responsable:** Integrante 1
**Docs:** Swagger UI en `/api-docs`

## Flujo de estados

```
PEDIDO ──(admin prepara)──> ENVIADO ──(delivery entrega)──> ENTREGADO
```

- **customer**: arma carrito (client-side) → `POST /orders` crea pedido en estado `PEDIDO`.
- **admin** (dueño del restaurante del pedido): cambia `PEDIDO → ENVIADO` cuando el pedido está listo para recoger.
- **delivery**: "jala" (claim) un pedido en estado `ENVIADO` sin repartidor asignado → luego marca `ENVIADO → ENTREGADO` al llegar.

## Modelo de datos (PostgreSQL)

```
orders (1) ──< (N) order_items
```

**orders**
| campo | tipo | notas |
|---|---|---|
| id | SERIAL PK | |
| customer_id | INT | FK lógica → MS1.usuarios (rol customer) |
| restaurant_id | VARCHAR | FK lógica → MS2 (ObjectId) |
| delivery_id | INT NULL | FK lógica → MS1.usuarios (rol delivery), null hasta que se "jala" |
| direccion_entrega | TEXT | |
| status | VARCHAR | `PEDIDO` \| `ENVIADO` \| `ENTREGADO` |
| total | NUMERIC(10,2) | |
| created_at | TIMESTAMP | |

**order_items**
| campo | tipo | notas |
|---|---|---|
| id | SERIAL PK | |
| order_id | INT FK → orders.id | |
| dish_id | VARCHAR | FK lógica → MS2 |
| nombre_plato | VARCHAR | snapshot al momento del pedido |
| cantidad | INT | |
| precio_unitario | NUMERIC(10,2) | snapshot (validado contra MS2 al crear) |

Carga masiva: `seed.js` → ≥20,000 registros en `orders`.

> El **carrito** vive en el frontend (estado local, no persiste en backend). Al dar "hacer pedido" se llama `POST /api/v1/orders` con todos los items acumulados.

## Endpoints

### Customer
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/v1/orders` | Crea pedido desde el carrito — valida cada `dish_id`/precio contra **MS2**, status inicial `PEDIDO` |
| GET | `/api/v1/orders/{order_id}` | Detalle de pedido + items |
| GET | `/api/v1/orders?customer_id={id}` | Historial de pedidos del customer |

### Admin (restaurante)
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/v1/orders?restaurant_id={id}&status=` | Pedidos del restaurante del admin (filtrable por estado) |
| PUT | `/api/v1/orders/{order_id}/status` | Cambia `PEDIDO → ENVIADO` (solo admin dueño del restaurante del pedido) |
| GET | `/api/v1/restaurants/{restaurant_id}/customers` | Clientes distintos que han pedido en ese restaurante (join interno con MS1 vía `GET /users?rol=customer&ids=`) |

### Delivery
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/v1/orders/available` | Pedidos en estado `ENVIADO` con `delivery_id` nulo (para "jalar") |
| PUT | `/api/v1/orders/{order_id}/claim` | Delivery jala el pedido — asigna `delivery_id` (requiere `status=ENVIADO` y `delivery_id` null) |
| PUT | `/api/v1/orders/{order_id}/deliver` | Delivery marca `ENVIADO → ENTREGADO` (requiere `delivery_id == self`) |
| GET | `/api/v1/orders?delivery_id={id}` | Pedidos asignados/entregados por ese repartidor |

### Infra
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Healthcheck |
| GET | `/api-docs` | Swagger UI |

## Consumido por
- **MS4** → `GET /api/v1/orders/{order_id}` (tracking), `GET /api/v1/orders?customer_id=` / `?delivery_id=` / `?restaurant_id=` (dashboards)
- **Frontend** → crear pedido, listar pedidos, cambiar estado, claim/deliver (según rol)

## Este servicio consume
- **MS1** → `GET /api/v1/users?rol=customer&ids=...` (para endpoint "clientes del restaurante")
- **MS2** → `GET /api/v1/restaurants/{restaurant_id}/menu/{dish_id}` (valida plato/precio al crear pedido)
