# Frontend — Delivery Cloud (React + Vite)

SPA que consume los 5 microservicios, con login/registro y 3 flujos por rol (`customer`, `admin`, `delivery`).

## Stack

- React 19 + Vite
- React Router (rutas protegidas por rol)
- Axios (interceptor inyecta el JWT en cada request)
- Sin librería de estilos — CSS plano en `src/index.css`

## Quickstart

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Por defecto pega a `http://localhost` (NGINX del `docker-compose.dev.yml` en la raíz del repo — levantalo primero). Para apuntar a otro backend (por ejemplo el API Gateway real), cambiar `VITE_API_BASE_URL` en `.env`.

## Estructura

```
src/
├── api/              # un módulo por microservicio (ms1.js..ms5.js) + client.js (axios + JWT)
├── auth/             # AuthContext (localStorage) + ProtectedRoute (redirect por rol)
├── components/       # NavBar
├── pages/
│   ├── Login.jsx / Register.jsx
│   ├── customer/      # browse restaurantes, carrito, pedido, tracking
│   ├── admin/          # dashboard por estado, CRUD de menú, analítica (MS5)
│   └── delivery/       # pool de pedidos, jalar, entregar
└── utils/jwt.js       # decode client-side del JWT (para sacar el user id tras login)
```

## Flujo por rol

- **customer**: `/register` (o `/login`) → `/customer` (browse) → `/customer/restaurants/:id` (menú + carrito) → `POST /orders` → `/customer/orders/:id` (tracking, polling cada 5s vía MS4).
- **admin**: se loguea con la cuenta seedeada (`admin@demo.com` / `password123`) → `/admin` (pedidos por estado vía MS4, botón "Enviar" → `PUT /orders/:id/status`) → `/admin/menu` (CRUD de platos vía MS2) → `/admin/analytics` (MS5).
- **delivery**: `/delivery` — pool de disponibles (`GET /orders/available`) con botón "Jalar" (`PUT /claim`), y entregas en curso con "Marcar entregado" (`PUT /deliver`).

## Endpoints consumidos (mínimo 2 por MS, hay más)

| MS | Endpoints |
|---|---|
| MS1 | `POST /auth/register`, `POST /auth/login` |
| MS2 | `GET /restaurants`, `GET /restaurants/{id}`, `POST/PUT/PATCH/DELETE /restaurants/{id}/menu/*` (admin) |
| MS3 | `POST /orders`, `GET /orders`, `PUT /orders/{id}/status`, `PUT /orders/{id}/claim`, `PUT /orders/{id}/deliver` |
| MS4 | `GET /tracking/order/{id}`, `GET /dashboard/admin/{id}/summary`, `GET /dashboard/delivery/{id}/summary` |
| MS5 | `GET /analytics/top-restaurants`, `GET /analytics/user-metrics` |

## Probado

Flujo completo verificado con Playwright en un Chromium real (no solo build): registro → redirect por rol → browse → carrito → pedido → tracking → login admin → enviar pedido → login delivery → jalar → entregar. Cero errores de consola/JS en las 3 vistas de rol.

## Pendiente (Fase 11 del plan)

Deploy en AWS Amplify con CI/CD desde GitHub — no hecho todavía.
