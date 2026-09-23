# MS1 — Usuarios / Auth

**Stack:** Python 3.11 (FastAPI) + SQLAlchemy + MySQL 8.0
**Puerto:** `8081` · **Base path:** `/api/v1` · **Docs:** `/docs` (Swagger UI)
**Código:** [`ms1-usuarios-auth/`](../ms1-usuarios-auth/)
**En AWS:** `https://<api-gateway>/ms1/...`

## Qué resuelve

Es la raíz de identidad del sistema: emite y valida los JWT que usan MS2 y MS3, guarda los 3 roles (`customer`, `delivery`, `admin`) y las direcciones de entrega de cada cliente. No consume a ningún otro microservicio.

## Roles

| Rol | Se registra vía app | Notas |
|---|---|---|
| `customer` | Sí, `POST /auth/register` | Compra en restaurantes, tiene direcciones guardadas |
| `delivery` | Sí, `POST /auth/register` | Toma y entrega pedidos |
| `admin` | **No** | Se inserta por SQL (seed), ya vinculado a un `restaurante_id` de MS2. `register` devuelve **400** si `rol=admin`. |

## Modelo de datos (MySQL, base `ms1_usuarios`)

```
usuarios (1) ──< (N) direcciones      ON DELETE CASCADE
```

**`usuarios`**
| Campo | Tipo | Notas |
|---|---|---|
| `id` | INT PK AUTO_INCREMENT | |
| `nombre` | VARCHAR(150) | |
| `email` | VARCHAR(150) UNIQUE | login |
| `password_hash` | VARCHAR(255) | bcrypt |
| `telefono` | VARCHAR(30) NULL | |
| `rol` | ENUM(customer, delivery, admin) | |
| `restaurante_id` | VARCHAR(50) NULL | solo si `rol=admin`; referencia lógica al `_id` de MongoDB en MS2 (no hay FK entre motores) |
| `fecha_registro` | DATETIME | `DEFAULT NOW()` |

Índice: `idx_usuarios_rol`.

**`direcciones`**
| Campo | Tipo | Notas |
|---|---|---|
| `id` | INT PK AUTO_INCREMENT | |
| `usuario_id` | INT FK → `usuarios.id` | `ON DELETE CASCADE` |
| `calle`, `ciudad`, `referencia` | VARCHAR | |
| `lat`, `lng` | DECIMAL(10,7) NULL | opcional |
| `es_principal` | TINYINT(1) | |

Índice: `idx_direcciones_usuario`. Carga masiva única: `seed.py` (Faker) → 20,007 usuarios, 17,025 direcciones.

## Endpoints

### Auth (sin JWT)
| Método | Ruta | Body | Respuesta |
|---|---|---|---|
| POST | `/api/v1/auth/register` | `{nombre,email,password,telefono,rol}` (rol ∈ customer\|delivery) | `201 {id,email,rol,token}` |
| POST | `/api/v1/auth/login` | `{email,password}` | `200 {access_token,rol,restaurante_id?}` |
| POST | `/api/v1/auth/refresh` | `{refresh_token}` | `200 {access_token}` |

El frontend usa el `rol` del login para redirigir al dashboard correcto (`/customer`, `/admin`, `/delivery`).

### Usuarios (JWT)
| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/api/v1/users/{user_id}` | JWT propio o admin | Perfil. 403 si pedís uno ajeno sin ser admin. |
| PUT | `/api/v1/users/{user_id}` | JWT propio | Actualiza `nombre`/`telefono`. |
| GET | `/api/v1/users?rol=&ids=&page=&page_size=` | **sin JWT** (consumido internamente por MS3/MS4) | Lista/filtra usuarios. Ver paginado más abajo. |
| DELETE | `/api/v1/users/{user_id}` | JWT admin | Baja. |

**Paginado de `GET /users`:** sin `page`/`page_size` devuelve el arreglo completo (con `X-Total-Count`); con ellos, `{items,page,page_size,total,total_pages}` (`page_size` por defecto 20, máximo 100; valores inválidos → `422`). `ids=1,2,3` hace lookup en lote (lo usa MS3 para resolver nombres de clientes sin N llamadas).

### Direcciones (JWT propio)
| Método | Ruta |
|---|---|
| GET | `/api/v1/users/{user_id}/addresses` |
| POST | `/api/v1/users/{user_id}/addresses` |
| PUT | `/api/v1/addresses/{address_id}` |
| DELETE | `/api/v1/addresses/{address_id}` |

### Infra
| Método | Ruta |
|---|---|
| GET | `/health` |
| GET | `/docs` |

## Seguridad
JWT HS256, secreto compartido con MS2 y MS3 (`JWT_SECRET`, ≥32 bytes). Contraseñas con bcrypt. Solo el dueño del recurso (o un admin) puede leer/editar un perfil ajeno.

## Quién lo consume
- **MS3**: `GET /users?rol=customer&ids=` para resolver nombres.
- **MS4**: `GET /users/{id}` (perfil) y `GET /users?ids=` (nombre del repartidor en el tracking, sin exponer teléfono a un cliente que no es admin).
- **Frontend**: login/registro, perfil, direcciones (5 llamadas REST).

## Correrlo solo
```bash
cd ms1-usuarios-auth
docker build -t ms1 . && docker run -p 8081:8081 --env-file ../.env \
  -e DB_HOST=host.docker.internal -e DB_USER=ms1_user -e DB_PASSWORD=ms1_password -e DB_NAME=ms1_usuarios ms1
```
(o, más simple, `docker compose -f ../docker-compose.dev.yml up -d --build ms1` con las 3 BD ya arriba).
