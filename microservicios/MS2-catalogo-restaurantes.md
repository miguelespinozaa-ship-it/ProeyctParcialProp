# MS2 — Catálogo de Restaurantes

**Stack:** Java 17 (Spring Boot) + Spring Data MongoDB
**Puerto:** `8082` · **Base path:** `/api/v1` · **Docs:** `/swagger-ui.html`
**Código:** [`ms2-catalogo-restaurantes/`](../ms2-catalogo-restaurantes/)
**En AWS:** `https://<api-gateway>/ms2/...`

## Qué resuelve

El catálogo público de restaurantes: menú y reseñas van **embebidos** en el mismo documento del restaurante, porque siempre se leen juntos (ficha del restaurante + su menú). No consume a ningún otro microservicio; es MS3 el que lo consulta a él.

## Modelo de datos (MongoDB, colección `ms2_catalogo.restaurantes`)

Un documento por restaurante, sin colecciones separadas para platos ni reseñas:

```json
{
  "_id": ObjectId("6aaf439f1bd3c2380450f532"),
  "nombre": "Sabor Criollo", "categoria": "Comida Peruana", "ciudad": "Lima", "direccion": "Av. Siempre Viva 123",
  "admin_id": 1, "calificacion_promedio": 4.5,
  "platos": [{ "id": "p1", "nombre": "Lomo Saltado", "descripcion": "...", "precio": 25.9, "categoria": "Fondos", "disponible": true }],
  "resenas": [{ "usuario_id": 10374, "comentario": "Excelente sabor", "puntuacion": 4, "fecha": ISODate("2026-07-12T...") }]
}
```

`admin_id` referencia (lógicamente) el `id` del admin en MS1. Carga masiva única: `seed.js` (mongosh) → 20,000 restaurantes, conservando los 2 del seed original. Índices en `categoria` y `ciudad`.

## Endpoints

### Restaurantes
| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/api/v1/restaurants?categoria=&ciudad=&page=&page_size=` | no | Lista. Sin `page`/`page_size` devuelve el arreglo completo (20,000 items); con ellos, `{items,page,page_size,total,total_pages}` (máx. 100/página, `400` si son inválidos). |
| GET | `/api/v1/restaurants/{id}` | no | Detalle completo (con `platos` y `resenas`). |
| GET | `/api/v1/restaurants/{id}/admin` | JWT admin dueño | Vista de administración. |
| PUT | `/api/v1/restaurants/{id}` | JWT admin dueño | Edita nombre/dirección/categoría/ciudad. |

### Menú (sub-recurso de `platos`)
| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/api/v1/restaurants/{id}/menu` | no | Lista de platos. |
| GET | `/api/v1/restaurants/{id}/menu/{dishId}` | no | Un plato (lo usa MS3 para validar precio). |
| POST | `/api/v1/restaurants/{id}/menu` | JWT admin dueño | Crea plato. |
| PUT | `/api/v1/restaurants/{id}/menu/{dishId}` | JWT admin dueño | Edita plato. |
| PATCH | `/api/v1/restaurants/{id}/menu/{dishId}/disponibilidad` | JWT admin dueño | Alterna `disponible`. |
| DELETE | `/api/v1/restaurants/{id}/menu/{dishId}` | JWT admin dueño | Elimina plato. |

### Reseñas
| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/api/v1/restaurants/{id}/reviews` | no | Lista de reseñas. |
| POST | `/api/v1/restaurants/{id}/reviews` | no* | Crea una reseña `{usuario_id,puntuacion,comentario}`; recalcula `calificacion_promedio`. Valida `1 ≤ puntuacion ≤ 5` y comentario no vacío (`400` si no). |

*El `usuario_id` viaja en el body, no se deriva del JWT — limitación conocida (ver README, sección de limitaciones).

### Infra
| Método | Ruta |
|---|---|
| GET | `/health` |

## Seguridad
Filtro JWT que valida el HS256 compartido. Para escribir en un restaurante, exige `rol=admin` **y** que el `restaurante_id` del token coincida con el `{id}` de la ruta (`403` si no). CORS abierto (`*`).

## Quién lo consume
- **MS3**: `GET /restaurants/{id}/menu/{dishId}` para validar plato/precio al crear un pedido.
- **MS4**: `GET /restaurants/{id}` para anexar nombre/dirección del restaurante a pedidos y dashboards.
- **Frontend**: listar/ver restaurantes, menú, reseñas, CRUD de menú del admin (9 llamadas REST).

## Correrlo solo
```bash
docker compose -f docker-compose.dev.yml up -d --build mongo ms2
```
