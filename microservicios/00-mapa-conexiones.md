# Mapa de Conexiones entre Microservicios

## Flujo por rol (frontend)

```
DIDI-frontend.vercel.app/login
        │
        ▼ (según `rol` devuelto por MS1)
   ┌────┴────┬──────────┐
   ▼         ▼          ▼
 admin    delivery   customer
   │         │          │
   ▼         ▼          ▼
CRUD menú  jalar      carrito →
+ clientes pedidos    hacer pedido
+ estados  + entregar
pedidos
```

- **register/login**: solo `customer` y `delivery`. `admin` va seedeado (1 admin por restaurante, `restaurante_id` fijo en MySQL).
- **Estados de pedido**: `PEDIDO → ENVIADO → ENTREGADO` (admin mueve a `ENVIADO`, delivery jala y mueve a `ENTREGADO`).
- **Carrito**: 100% frontend (estado local), se materializa recién en `POST /api/v1/orders`.

## Grafo de dependencias (backend)

```
MS1 (Auth/Usuarios) ◄────────────┬──────────────┐
   MySQL                         │              │
                                  │              │
MS2 (Catálogo) ◄───┐             │              │
   MongoDB          │            │              │
                    │            │              │
MS3 (Pedidos) ──────┘            │              │  (valida dish_id/precio)
   PostgreSQL                    │              │  (resuelve nombres clientes)
   │                             │              │
   ▼                             │              │
MS4 (Agregador) ──────────────────┴──────────────┘
   sin BD          (GET users, GET restaurants, GET orders — por rol)

MS5 (Analítico) ──> AWS Athena (independiente, no llama a MS1-4 en runtime)
   sin BD
```

## Tabla resumen: quién llama a quién

| Origen | Destino | Endpoint consumido | Motivo |
|---|---|---|---|
| MS3 | MS2 | `GET /api/v1/restaurants/{id}/menu/{dish_id}` | Validar plato/precio al crear pedido |
| MS3 | MS1 | `GET /api/v1/users?rol=customer&ids=` | Resolver nombres para "clientes del restaurante" |
| MS4 | MS1 | `GET /api/v1/users/{user_id}` | Datos cliente/delivery |
| MS4 | MS2 | `GET /api/v1/restaurants/{restaurant_id}` | Datos del restaurante |
| MS4 | MS3 | `GET /api/v1/orders/{order_id}`, `?customer_id=`, `?delivery_id=`, `?restaurant_id=`, `/orders/available` | Tracking + 3 dashboards por rol |
| MS5 | AWS Athena | vistas `v_resumen_ventas_restaurante`, `v_metricas_usuarios` | Analítica (no HTTP a otros MS) |
| Frontend | MS1-MS5 | mín. 2 endpoints c/u, filtrado por rol | Consumo directo desde SPA |

## Infraestructura real (indicación del profesor)

Solo **2 EC2** (no 3):

| EC2 | Contenido |
|---|---|
| **EC2 #1 — App Tier** | Los **5 microservicios** dockerizados (MS1-MS5) en un mismo `docker-compose.yml`, todos en la misma instancia. NGINX corre acá también (reverse proxy / path routing, no balanceo entre VMs ya que hay una sola). |
| **EC2 #2 — DB Tier (privada)** | Contenedores MySQL, PostgreSQL y MongoDB. Sin IP pública — Security Group solo acepta tráfico desde el SG de EC2 #1. |

Los MS dentro de EC2 #1 se llaman entre sí por **nombre de contenedor** (misma docker network), y llegan a las BD de EC2 #2 por **IP privada** de esa instancia.

## Puertos y base URLs internas

| Servicio | Puerto | URL interna (docker network, dentro de EC2 #1) |
|---|---|---|
| MS1 | 8081 | `http://ms1:8081` |
| MS2 | 8082 | `http://ms2:8082` |
| MS3 | 8083 | `http://ms3:8083` |
| MS4 | 8084 | `http://ms4:8084` |
| MS5 | 8085 | `http://ms5:8085` |

| Base de datos | Puerto | Host (desde EC2 #1, hacia IP privada de EC2 #2) |
|---|---|---|
| MySQL (MS1) | 3306 | `<ip-privada-ec2-db>:3306` |
| PostgreSQL (MS3) | 5432 | `<ip-privada-ec2-db>:5432` |
| MongoDB (MS2) | 27017 | `<ip-privada-ec2-db>:27017` |

Todo el tráfico externo entra por **AWS API Gateway (HTTPS) → NGINX en EC2 #1** y se enruta por path prefix (`/ms1/*`, `/ms2/*`, etc.) al contenedor correspondiente.

## Orden de arranque recomendado
1. **EC2 #2**: `docker-compose up` de MySQL, PostgreSQL, MongoDB (deben estar arriba antes que los MS)
2. **EC2 #1**: MS1, MS2 (no dependen de otros MS, sí de sus BD en EC2 #2)
3. MS3 (depende de MS1 y MS2 para validar, y de su Postgres en EC2 #2)
4. MS4 (depende de MS1, MS2, MS3 — sirve los 3 dashboards por rol)
5. MS5 (independiente, requiere credenciales AWS + Athena ya poblado)
6. NGINX al final, ya con los 5 MS levantados

## Checklist de integración
- [ ] JWT de MS1 incluye `rol` y `restaurante_id` (si admin) — MS2/MS3 lo usan para autorizar escritura
- [ ] MS2 valida `restaurante_id` del JWT contra el `restaurant_id` de la ruta antes de CRUD de menú
- [ ] MS3 valida transición de estado (`PEDIDO→ENVIADO` solo admin dueño, `ENVIADO→ENTREGADO` solo delivery asignado)
- [ ] Cada MS expone `/health` para el LB
- [ ] Variables `*_BASE_URL` inyectadas por servicio en `docker-compose.yml`
- [ ] Timeouts + manejo de error en cascada (MS4 es el más expuesto)
- [ ] CORS habilitado en los 5 MS para el dominio de Amplify/Vercel
- [ ] Swagger UI accesible en los 5 (`/docs`, `/swagger-ui.html`, `/api-docs`)

## Convención de paginado (todos los listados grandes)

Los endpoints de listado tienen **dos modos**, en la misma ruta:

| Modo | Cómo se pide | Respuesta |
|---|---|---|
| Completo (original) | sin `page` ni `page_size` | array con todo, igual que siempre. Header `X-Total-Count` con el total |
| Paginado | `?page=1&page_size=20` | `{items, page, page_size, total, total_pages}` |

- `page` desde 1. `page_size` por defecto 20, **máximo 100** (si se pide más se limita y la respuesta informa el tamaño aplicado).
- Página fuera de rango → `items` vacío (no es error). `page`/`page_size` inválidos → **400** en MS3 y **422** en los servicios FastAPI (MS1, MS4, MS5).
- El modo completo se mantiene por compatibilidad (seeds, llamadas internas). Las pantallas usan el paginado.
- Endpoints con paginado: MS1 `GET /users`; MS3 `GET /orders`, `GET /orders/available`, `GET /restaurants/{id}/customers`; MS4 los 3 dashboards; MS5 `GET /analytics/user-metrics` (aquí `data` sigue siendo un array y se agregan `page/page_size/total/total_pages`).
- Extras para no traer miles de filas: MS3 `GET /orders/summary` (conteo por estado). MS4 modo paginado del dashboard admin: `?status=PEDIDO|ENVIADO|ENTREGADO&page=&page_size=&customers_page=`; delivery: `?page=&page_size=&curso_page=`.
