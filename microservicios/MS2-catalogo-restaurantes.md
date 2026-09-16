# MS2 — Catálogo de Restaurantes

**Stack:** Java (Spring Boot) + MongoDB
**Puerto:** `8082`
**Base path:** `/api/v1`
**Responsable:** Integrante 2
**Docs:** Swagger UI en `/swagger-ui.html`

## Reglas de rol

- **customer**: solo lectura (browse restaurantes, ver menú).
- **admin**: CRUD de **platillos** limitado a **su propio restaurante** (`restaurante_id` viene del JWT emitido por MS1; el backend debe validar `restaurante_id == restaurant_id` de la ruta antes de escribir — si no coincide → `403`).

## Modelo de datos (MongoDB — documentos embebidos)

```json
// colección: restaurantes
{
  "_id": "ObjectId",
  "nombre": "string",
  "categoria": "string",
  "ciudad": "string",
  "direccion": "string",
  "admin_id": 1,
  "calificacion_promedio": 4.5,
  "platos": [
    { "id": "string", "nombre": "string", "descripcion": "string", "precio": 0.0, "categoria": "string", "disponible": true }
  ],
  "resenas": [
    { "usuario_id": 1, "comentario": "string", "puntuacion": 5, "fecha": "ISODate" }
  ]
}
```

## Endpoints

### Restaurantes (público / customer)
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/v1/restaurants` | Lista restaurantes (filtros `?categoria=&ciudad=`) |
| GET | `/api/v1/restaurants/{restaurant_id}` | Detalle (incluye platos y reseñas embebidos) |

### Restaurante — administración (solo admin dueño)
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/v1/restaurants/{restaurant_id}/admin` | Datos del restaurante para el panel admin |
| PUT | `/api/v1/restaurants/{restaurant_id}` | Actualiza datos del restaurante (nombre, dirección, categoría) |

### Menú — CRUD platillos disponibles (solo admin dueño del restaurante)
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/v1/restaurants/{restaurant_id}/menu` | Lista platillos (customer y admin) |
| GET | `/api/v1/restaurants/{restaurant_id}/menu/{dish_id}` | Detalle de un plato (valida existencia/precio, usado por MS3) |
| POST | `/api/v1/restaurants/{restaurant_id}/menu` | Crea platillo — **admin dueño** |
| PUT | `/api/v1/restaurants/{restaurant_id}/menu/{dish_id}` | Edita platillo (precio, descripción) — **admin dueño** |
| PATCH | `/api/v1/restaurants/{restaurant_id}/menu/{dish_id}/disponibilidad` | Toggle rápido `disponible: true/false` — **admin dueño** |
| DELETE | `/api/v1/restaurants/{restaurant_id}/menu/{dish_id}` | Elimina platillo — **admin dueño** |

### Reseñas (embebidas, customer)
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/v1/restaurants/{restaurant_id}/reviews` | Lista reseñas |
| POST | `/api/v1/restaurants/{restaurant_id}/reviews` | Agrega reseña (customer) |

### Infra
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/actuator/health` | Healthcheck |
| GET | `/swagger-ui.html` | Swagger UI |

## Consumido por
- **MS3** → `GET /api/v1/restaurants/{restaurant_id}/menu/{dish_id}` (valida precio/disponibilidad al agregar al carrito y al crear pedido)
- **MS4** → `GET /api/v1/restaurants/{restaurant_id}` (info restaurante para dashboards/tracking)
- **Frontend** → browse restaurantes + ver menú (customer) / CRUD platillos (admin)

## Este servicio consume
- Ninguno
