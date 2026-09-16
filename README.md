# Proyecto Parcial Cloud — Plataforma de Delivery (Microservicios)

Monorepo con 5 microservicios + frontend SPA + pipeline de datos, desplegado en AWS (2 EC2 para backend + 1 EC2 de ingesta).

## Documentación

- [proyecto-parcial-requisitos.md](proyecto-parcial-requisitos.md) — checklist de requisitos del parcial
- [plan-desarrollo.md](plan-desarrollo.md) — plan paso a paso por fases
- [estructura-proyecto.md](estructura-proyecto.md) — estructura de repo y flujo de despliegue
- [microservicios/](microservicios/) — spec de endpoints por microservicio (`00-mapa-conexiones.md` + `MS1`-`MS5`)

## Quickstart (desarrollo local)

```bash
cp .env.example .env
docker compose -f docker-compose.dev.yml up -d --build
```

Con eso alcanza — el `.env.example` ya trae valores funcionales para desarrollo local (JWT compartido, credenciales de las 3 BD, `ATHENA_MOCK=true`). Probado clonando el repo desde cero en una carpeta limpia.

Servicios disponibles:

| Servicio | URL local | Vía NGINX | Docs |
|---|---|---|---|
| MS1 (Usuarios/Auth) | http://localhost:8081 | http://localhost/ms1 | `/docs` |
| MS2 (Catálogo) | http://localhost:8082 | http://localhost/ms2 | `/swagger-ui.html` |
| MS3 (Pedidos) | http://localhost:8083 | http://localhost/ms3 | `/api-docs` |
| MS4 (Agregador) | http://localhost:8084 | http://localhost/ms4 | `/docs` |
| MS5 (Analítico) | http://localhost:8085 | http://localhost/ms5 | `/docs` |

### Un paso manual único: `restaurante_id` del admin demo

El seed de MySQL crea 3 usuarios de prueba (`customer@demo.com`, `delivery@demo.com`, `admin@demo.com`, password `password123`), pero el `restaurante_id` del admin queda con un placeholder porque MongoDB genera un `_id` distinto en cada arranque. Para probar el flujo de admin (cambiar pedidos a `ENVIADO`, CRUD de menú):

```bash
# 1. sacar el _id real de un restaurante
curl http://localhost:8082/api/v1/restaurants

# 2. apuntar el admin demo a ese restaurante
docker exec mysql mysql -ums1_user -pms1_password ms1_usuarios \
  -e "UPDATE usuarios SET restaurante_id='<_id de arriba>' WHERE email='admin@demo.com';"
```

### Smoke test rápido (registro → pedido → tracking)

```bash
# registrar y loguear un customer
curl -X POST http://localhost/ms1/api/v1/auth/register -H "Content-Type: application/json" \
  -d '{"nombre":"Test","email":"test@demo.com","password":"pass123","telefono":"999000000","rol":"customer"}'

# ver restaurantes, crear pedido, etc. — ver microservicios/*.md para el detalle de cada endpoint
```

## Estado actual

Fases 0-8 del plan de desarrollo completas y probadas end-to-end (incluyendo carga masiva de 20k registros y el stack completo detrás de NGINX): los 5 microservicios tienen lógica de negocio real, no solo esqueletos. Fase 9 (pipeline de ingesta a S3/Glue/Athena) está preparada en [data-science/](data-science/) lista para correr contra una cuenta AWS real — ver su [README](data-science/README.md). Detalle completo de qué se probó en cada fase: [plan-desarrollo.md](plan-desarrollo.md).

## Estructura

```
ms1-usuarios-auth/         FastAPI + MySQL — auth, usuarios, direcciones
ms2-catalogo-restaurantes/ Spring Boot + MongoDB — restaurantes, menú, reseñas
ms3-pedidos/                Express + PostgreSQL — pedidos, order_items
ms4-agregador-rastreo/      FastAPI, sin BD — tracking + dashboards por rol
ms5-analitico/               FastAPI + boto3 — consultas a AWS Athena
nginx/                       reverse proxy / path routing
db/                          scripts de inicialización de esquema por BD
data-science/                pipeline ETL (Integrante 3, Fase 9)
frontend/                    SPA (Integrante 4, Fase 11)
infra/diagramas/             diagramas draw.io
```

## Próximos pasos

Ver el checklist completo en [plan-desarrollo.md](plan-desarrollo.md). Siguiente fase: **Fase 10 — Infra AWS real (2 EC2)**, desplegar `docker-compose.app.yml`/`docker-compose.db.yml` en instancias reales.
