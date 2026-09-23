# MS3 — Pedidos

**Stack:** Node.js 20 (Express) + `pg`
**Puerto:** `8083` · **Base path:** `/api/v1` · **Docs:** `/api-docs` (Swagger, spec manual en `src/openapi.json`)
**Código:** [`ms3-pedidos/`](../ms3-pedidos/)
**En AWS:** `https://<api-gateway>/ms3/...`

## Qué resuelve

El corazón transaccional: crea pedidos, valida cada plato contra MS2, resuelve nombres contra MS1, y controla la máquina de estados `PEDIDO → ENVIADO → ENTREGADO`. Es el único microservicio con dos tablas relacionadas por FK real (dentro de su propia base).

## Modelo de datos (PostgreSQL 16, base `ms3_pedidos`)

```
orders (1) ──< (N) order_items      ON DELETE CASCADE
```

**`orders`**
| Campo | Tipo | Notas |
|---|---|---|
| `id` | SERIAL PK | |
| `customer_id` | INTEGER | referencia lógica a `usuarios.id` (MS1) |
| `restaurant_id` | VARCHAR(50) | referencia lógica al `_id` de MongoDB (MS2) |
| `delivery_id` | INTEGER NULL | se llena al hacer `claim` |
| `direccion_entrega` | TEXT | |
| `status` | VARCHAR(20) | `CHECK IN ('PEDIDO','ENVIADO','ENTREGADO')` |
| `total` | NUMERIC(10,2) | suma de `cantidad × precio_unitario` |
| `created_at` | TIMESTAMP | `DEFAULT NOW()` |

**`order_items`**
| Campo | Tipo | Notas |
|---|---|---|
| `id` | SERIAL PK | |
| `order_id` | INTEGER FK → `orders.id` | `ON DELETE CASCADE` |
| `dish_id`, `nombre_plato` | VARCHAR | fotografía del plato al momento de comprar (no se recalcula si el admin cambia el precio después) |
| `cantidad` | INTEGER | `CHECK (> 0)` |
| `precio_unitario` | NUMERIC(10,2) | |

Índices: `idx_orders_customer`, `idx_orders_restaurant(restaurant_id,status)`, `idx_orders_delivery`, `idx_order_items_order`. Carga masiva única: `seed.js` → 20,009 pedidos, 26,566 ítems.

## Máquina de estados

```
PEDIDO ──(admin dueño del restaurante)──> ENVIADO ──(delivery hace claim, luego deliver)──> ENTREGADO
```

- `claim` solo funciona sobre un pedido `ENVIADO` con `delivery_id IS NULL`, en una operación atómica en SQL: si dos repartidores lo intentan a la vez, solo uno gana (el otro recibe `409`).
- `deliver` solo lo puede ejecutar el mismo repartidor que hizo el `claim`.

## Endpoints

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| POST | `/api/v1/orders` | JWT customer | Crea pedido. Por cada ítem llama a MS2 (`GET .../menu/{dishId}`) para validar precio/disponibilidad; `400` si un plato no existe. |
| GET | `/api/v1/orders?customer_id=&restaurant_id=&delivery_id=&status=&include_items=&page=&page_size=` | no* | Listado con filtros. Paginado opcional (ver abajo). `include_items=true` trae los platos de cada pedido de la página en una sola query extra. |
| GET | `/api/v1/orders/summary?restaurant_id=&customer_id=&delivery_id=` | no* | Conteo `{PEDIDO,ENVIADO,ENTREGADO,total}` sin traer filas — lo usan los tabs del admin. |
| GET | `/api/v1/orders/{orderId}` | no* | Detalle + ítems. |
| PUT | `/api/v1/orders/{orderId}/status` | JWT admin dueño | `PEDIDO → ENVIADO`. `403` si el restaurante no es del admin del token. |
| PUT | `/api/v1/orders/{orderId}/claim` | JWT delivery | Asigna el pedido al repartidor. `409` si ya no está disponible. |
| PUT | `/api/v1/orders/{orderId}/deliver` | JWT delivery (mismo que hizo claim) | `ENVIADO → ENTREGADO`. |
| GET | `/api/v1/orders/available?page=&page_size=` | JWT delivery | Pool de pedidos `ENVIADO` sin asignar, orden FIFO. |
| GET | `/api/v1/restaurants/{restaurantId}/customers?page=&page_size=` | no | Clientes distintos de un restaurante, con nombre resuelto vía MS1 (lookup en lote de hasta 200 ids, 5 en paralelo). |

*Sin JWT obligatorio porque los consume MS4 internamente (red privada); la autorización de escritura sí es estricta.

**Paginado:** sin `page`/`page_size`, arreglo completo (`X-Total-Count` en la cabecera); con ellos, `{items,page,page_size,total,total_pages}` (máx. 100, `400` si son inválidos, página fuera de rango → `items` vacío).

## Seguridad
Mismo JWT HS256 que MS1/MS2. Middleware `requireRole` por endpoint de escritura; el `admin` solo puede tocar pedidos de su propio `restaurante_id` (viene en el token).

## Quién lo consume
- **MS4**: casi todos los endpoints, para armar tracking y los 3 dashboards.
- **Frontend**: crear pedido, listar, cambiar de estado, tomar/entregar (8 llamadas REST).

## Correrlo solo
```bash
docker compose -f docker-compose.dev.yml up -d --build postgres ms1 ms2 ms3
```
(necesita MS1 y MS2 arriba para validar plato y resolver nombres).
