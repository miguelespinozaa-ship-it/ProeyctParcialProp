# MS4 — Agregador / Rastreo

**Stack:** Python 3.11 (FastAPI) + `httpx` — **sin base de datos propia**
**Puerto:** `8084` · **Base path:** `/api/v1` · **Docs:** `/docs`
**Código:** [`ms4-agregador-rastreo/`](../ms4-agregador-rastreo/)
**En AWS:** `https://<api-gateway>/ms4/...`

## Qué resuelve

No persiste nada: en cada request llama en paralelo a MS1, MS2 y MS3 y combina las respuestas. Existe para que el frontend no tenga que orquestar 3 llamadas por pantalla (tracking de un pedido, dashboard de cada rol).

**Resiliencia:** distingue entre lo que es esencial y lo que es complementario. Si MS3 (la fuente del pedido) falla, la respuesta completa falla con `502`. Si MS1 o MS2 fallan (nombre del cliente, datos del restaurante), esos campos se degradan a `null` en vez de tumbar todo el endpoint.

## Endpoints

### Tracking
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/v1/tracking/order/{order_id}` | `{order_id,status,cliente,repartidor,restaurante,items,total}`. `cliente` viene de MS1 (JWT del caller reenviado — si el caller es el dueño puede leer su propio perfil); `repartidor` se resuelve por el listado interno de MS1 (solo nombre, sin teléfono, porque el cliente no tiene permiso de leer el perfil ajeno del repartidor). |

### Dashboards (uno por rol, todos con modo completo y modo paginado)
| Método | Ruta | Modo completo | Modo paginado |
|---|---|---|---|
| GET | `/api/v1/dashboard/customer/{user_id}/summary` | `{usuario,pedidos_activos,historial}` | `?page=&page_size=` → agrega `resumen` (conteo por estado) y `historial` paginado; `pedidos_activos` sigue trayendo hasta 50 PEDIDO + 50 ENVIADO |
| GET | `/api/v1/dashboard/delivery/{delivery_id}/summary` | `{resumen,disponibles,en_curso}` | `?page=&page_size=&curso_page=` → `disponibles` (pool) y `en_curso` (asignados a este repartidor) paginados por separado |
| GET | `/api/v1/dashboard/admin/{restaurant_id}/summary` | `{restaurante,pedidos_por_estado,clientes}` | `?status=PEDIDO\|ENVIADO\|ENTREGADO&page=&page_size=&customers_page=` → `{restaurante,resumen,estado,pedidos,clientes}`; `pedidos` incluye `include_items=true` (cada pedido trae sus platos) |

En modo paginado, cada bloque paginado tiene la forma `{items,page,page_size,total,total_pages}` tal como la devuelve MS3, sin transformarla.

### Infra
| Método | Ruta |
|---|---|
| GET | `/health` |

## Seguridad
No emite ni valida tokens propios: reenvía el `Authorization` del caller a MS1/MS3 cuando corresponde (`get_user`, listar clientes). Sin ese reenvío, MS1 rechazaría la consulta del perfil.

## Quién lo consume
- **Frontend**: los 3 dashboards + tracking (4 llamadas REST) — es la fuente principal de datos de las pantallas de customer, admin y delivery.

## Correrlo solo
```bash
docker compose -f docker-compose.dev.yml up -d --build ms1 ms2 ms3 ms4
```
(depende de los 3 para responder algo útil, aunque arranca sin ellos y degrada).
