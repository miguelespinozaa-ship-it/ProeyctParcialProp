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
# editar .env con tus valores

docker compose -f docker-compose.dev.yml up -d --build
```

Servicios disponibles:

| Servicio | URL local | Docs |
|---|---|---|
| MS1 (Usuarios/Auth) | http://localhost:8081 | `/docs` |
| MS2 (Catálogo) | http://localhost:8082 | `/swagger-ui.html` |
| MS3 (Pedidos) | http://localhost:8083 | `/api-docs` (pendiente Fase 4) |
| MS4 (Agregador) | http://localhost:8084 | `/docs` |
| MS5 (Analítico) | http://localhost:8085 | `/docs` |
| NGINX (gateway local) | http://localhost:80 | — |

## Estado actual

Scaffold inicial (Fase 0-1 del plan de desarrollo): estructura de carpetas, Dockerfiles, esquemas de BD (MySQL/PostgreSQL/MongoDB) y esqueletos de endpoints (routers/controllers con `TODO` marcados por fase). La lógica de negocio se implementa fase por fase — ver [plan-desarrollo.md](plan-desarrollo.md).

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

Ver el checklist completo en [plan-desarrollo.md](plan-desarrollo.md). Siguiente fase: **Fase 2 — MS1 (Usuarios/Auth)**, implementar la lógica real de `auth.py`/`users.py`/`addresses.py` sobre los modelos ya definidos.
