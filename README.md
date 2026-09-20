# Proyecto Parcial Cloud — Plataforma de Delivery (Microservicios)

Monorepo con 5 microservicios + frontend SPA + pipeline de datos, desplegado en AWS (EC2 App Tier + EC2 DB Tier + EC2 de ingesta, API Gateway, Amplify, S3/Glue/Athena).

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

Todas las fases del plan de desarrollo (0-11) están implementadas, probadas y desplegadas en AWS. Queda la Fase 12 (entregables: diagramas, informe y PPT). Detalle de pruebas por fase: [plan-desarrollo.md](plan-desarrollo.md).

| Pieza | Estado |
|---|---|
| 5 microservicios (FastAPI, Spring Boot, Express) | Desplegados en la EC2 App Tier con NGINX (`docker-compose.app.yml`) |
| Bases de datos (MySQL, PostgreSQL, MongoDB) | EC2 DB Tier (`docker-compose.db.yml`); solo aceptan tráfico del Security Group de la App Tier, sin puertos abiertos a internet |
| Carga masiva | 20,003 `usuarios` (MS1) y 20,000 `orders` (MS3) |
| API Gateway (HTTPS) | Expone `/ms1` ... `/ms5` hacia NGINX |
| Frontend SPA (React + Vite) | AWS Amplify, consume el API Gateway por HTTPS |
| MV de ingesta | EC2 dedicada `PP-Ingest-VM` (SG propio sin entradas, rol `LabInstanceProfile`). Ejecuta los 3 contenedores ETL por IP privada hacia la BD |
| Data lake | 3 contenedores de ingesta -> S3 (snapshot completo, sin duplicados) -> Glue Crawler -> Athena (2 vistas). MS5 consulta Athena real (`ATHENA_MOCK=false`) |
| Paginado | Opt-in en los listados grandes (`?page=&page_size=`), ver [00-mapa-conexiones.md](microservicios/00-mapa-conexiones.md) |
| Swagger UI | Los 5 servicios, también a través de NGINX y API Gateway (`/ms1/docs`, `/ms2/swagger-ui.html`, `/ms3/api-docs`, `/ms4/docs`, `/ms5/docs`) |

### Decisiones de arquitectura respecto al enunciado

- **Una sola EC2 de App** (en vez de dos): NGINX enruta por path a cada microservicio, pero no balancea carga entre dos VMs.
- **Amplify por despliegue manual** (zip): no está conectado a GitHub para CI/CD.
- **Postman:** [postman/delivery-cloud.postman_collection.json](postman/delivery-cloud.postman_collection.json) cubre los 5 microservicios (66 requests, 54 assertions). Contra local: `--env-var "base_url=http://localhost"`.

## Estructura

```
ms1-usuarios-auth/         FastAPI + MySQL — auth, usuarios, direcciones
ms2-catalogo-restaurantes/ Spring Boot + MongoDB — restaurantes, menú, reseñas
ms3-pedidos/                Express + PostgreSQL — pedidos, order_items
ms4-agregador-rastreo/      FastAPI, sin BD — tracking + dashboards por rol
ms5-analitico/               FastAPI + boto3 — consultas a AWS Athena
nginx/                       reverse proxy / path routing
db/                          scripts de inicialización de esquema por BD
data-science/                pipeline ETL a S3 + SQL de Athena (queries_and_views.sql)
frontend/                    SPA React (Vite)
postman/                     colección de Postman
infra/diagramas/             diagramas draw.io (pendiente)
```

## Próximos pasos (Fase 12)

- Diagrama de arquitectura en draw.io (`infra/diagramas/`).
- Diagrama ER del catálogo de Glue.
- Evidencia de Athena (4 consultas con JOIN + 2 vistas) para el informe.
- Informe técnico (PDF) y presentación (PowerPoint).
