# MS1 — Usuarios / Auth

**Stack:** Python (FastAPI) + MySQL 8.0
**Puerto sugerido:** `8081`
**Base path:** `/api/v1`
**Responsable:** Integrante 1
**Docs:** Swagger UI en `/docs`

## Roles

| Rol | Se registra vía app? | Notas |
|---|---|---|
| `customer` | Sí (`/auth/register`) | Compra en restaurantes |
| `delivery` | Sí (`/auth/register`) | Recoge y entrega pedidos |
| `admin` | **No** — se crea por seed/carga inicial | Asignado a **1 restaurante** (`restaurante_id`), gestiona ese restaurante |

`POST /auth/register` **rechaza** `rol=admin` (400). Los admins se insertan directo en BD (seed) ya vinculados a un `restaurante_id` de MS2.

## Modelo de datos (MySQL)

```
usuarios (1) ──< (N) direcciones
```

**usuarios**
| campo | tipo | notas |
|---|---|---|
| id | INT PK AI | |
| nombre | VARCHAR | |
| email | VARCHAR UNIQUE | login |
| password_hash | VARCHAR | bcrypt |
| telefono | VARCHAR | |
| rol | ENUM('customer','delivery','admin') | |
| restaurante_id | VARCHAR NULL | solo si `rol='admin'` — FK lógica a MS2 |
| fecha_registro | DATETIME | |

**direcciones**
| campo | tipo | notas |
|---|---|---|
| id | INT PK AI | |
| usuario_id | INT FK → usuarios.id | típicamente `customer` |
| calle | VARCHAR | |
| ciudad | VARCHAR | |
| referencia | VARCHAR | |
| lat / lng | DECIMAL | opcional |
| es_principal | BOOLEAN | |

Carga masiva: `seed.py` → ≥20,000 registros en `usuarios` (mayoría `customer`, algunos `delivery`, admins fijos uno por restaurante).

## Endpoints

### Auth
| Método | Ruta | Descripción | Body | Response |
|---|---|---|---|---|
| POST | `/api/v1/auth/register` | Crea usuario **customer o delivery** | `{nombre,email,password,telefono,rol}` | `201 {id,email,rol,token}` |
| POST | `/api/v1/auth/login` | Login, emite JWT (incluye `rol` y `restaurante_id` si admin) | `{email,password}` | `200 {access_token,rol,restaurante_id?}` — el **frontend usa `rol` para redirigir al dashboard correcto** |
| POST | `/api/v1/auth/refresh` | Renueva token | `{refresh_token}` | `200 {access_token}` |

### Usuarios
| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| GET | `/api/v1/users/{user_id}` | Perfil de usuario | JWT propio |
| PUT | `/api/v1/users/{user_id}` | Actualiza perfil | JWT propio |
| GET | `/api/v1/users?rol=delivery` | Lista repartidores (usado por MS4/admin) | JWT admin |
| GET | `/api/v1/users?rol=customer&ids=1,2,3` | Batch lookup de clientes (usado por MS3/MS4 para "clientes del restaurante") | interno |
| DELETE | `/api/v1/users/{user_id}` | Baja lógica | JWT admin |

### Direcciones
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/v1/users/{user_id}/addresses` | Lista direcciones del customer |
| POST | `/api/v1/users/{user_id}/addresses` | Crea dirección |
| PUT | `/api/v1/addresses/{address_id}` | Edita dirección |
| DELETE | `/api/v1/addresses/{address_id}` | Elimina dirección |

### Infra
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Healthcheck (LB) |
| GET | `/docs` | Swagger UI |

## Consumido por
- **MS3** → `GET /api/v1/users?rol=customer&ids=...` (lista clientes del restaurante para dashboard admin)
- **MS4** → `GET /api/v1/users/{user_id}` (datos cliente/delivery para tracking/dashboards)
- **Frontend** → login (redirect por rol) + perfil

## Este servicio consume
- Ninguno (raíz de la cadena)
