# Proyecto Parcial Cloud — Plataforma de Delivery (Microservicios)

Monorepo con 5 microservicios + frontend SPA + pipeline de datos, desplegado en AWS (2 EC2 App Tier con balanceador interno, EC2 DB Tier privada, EC2 de ingesta, API Gateway HTTPS, Amplify, S3/Glue/Athena).

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
| 5 microservicios (FastAPI, Spring Boot, Express) | Desplegados en **2 EC2 de App** (`PP-App-Tier` en us-east-1a y `PP-App-Tier-2` en us-east-1b), cada una con `docker-compose.app.yml` y NGINX |
| Balanceador de carga | **ALB interno** (`pp-alb-interno`, sin IP pública) reparte entre las 2 VMs con health check a `/health`. NGINX de cada VM enruta por path a los 5 servicios y devuelve `X-Served-By` con la VM que atendió |
| Bases de datos (MySQL, PostgreSQL, MongoDB) | EC2 DB Tier (`docker-compose.db.yml`); solo aceptan tráfico del Security Group de la App Tier, sin puertos abiertos a internet |
| Carga masiva | 20,007 `usuarios` (MS1, `seed.py`), 20,009 `orders` (MS3, `seed.js`) y 20,000 `restaurantes` (MS2, `seed.js` en mongosh) |
| API Gateway (HTTPS) | Expone `/ms1` ... `/ms5` y llega al ALB interno por un **VPC Link** |
| Frontend SPA (React + Vite) | AWS Amplify, consume el API Gateway por HTTPS |
| MV de ingesta | EC2 dedicada `PP-Ingest-VM` (SG propio sin entradas, rol `LabInstanceProfile`). Ejecuta los 3 contenedores ETL por IP privada hacia la BD |
| Data lake | 3 contenedores de ingesta -> S3 (snapshot completo, sin duplicados) -> Glue Crawler -> Athena (2 vistas). MS5 consulta Athena real (`ATHENA_MOCK=false`) |
| Paginado | Opt-in en los listados grandes (`?page=&page_size=`), ver [00-mapa-conexiones.md](microservicios/00-mapa-conexiones.md) |
| Swagger UI | Los 5 servicios, también a través de NGINX y API Gateway (`/ms1/docs`, `/ms2/swagger-ui.html`, `/ms3/api-docs`, `/ms4/docs`, `/ms5/docs`) |

### Balanceo y decisiones de arquitectura

Flujo: `Amplify (HTTPS) -> API Gateway -> VPC Link -> ALB interno -> NGINX (VM 1 o VM 2) -> microservicios -> DB Tier`. El ALB solo acepta tráfico del security group del VPC Link.
Para comprobar el reparto: `for i in $(seq 1 20); do curl -sI https://<gateway>/ms1/health | grep -i x-served-by; done`. Si una VM cae, el ALB la saca de rotación en ~30 s y la otra atiende todo.

- **Amplify por despliegue manual** (zip): no está conectado a GitHub para CI/CD.
- **Postman:** [postman/delivery-cloud.postman_collection.json](postman/delivery-cloud.postman_collection.json) cubre los 5 microservicios (71 requests, 65 assertions) y apunta por defecto al API Gateway HTTPS. Contra local: `--env-var "base_url=http://localhost"`.

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
infra/diagramas/             diagramas (draw.io editable + PNG/SVG) y su generador
entregables/                 informe técnico (PDF), presentación (PPTX), capturas y evidencia de Athena
amplify.yml                  build de AWS Amplify para el frontend (CI/CD desde GitHub)
```

## Entregables

- **Diagramas:** [infra/diagramas/](infra/diagramas/) — `proyecto-delivery-cloud.drawio` (5 páginas: arquitectura, E/R de MySQL, E/R de PostgreSQL, JSON de MongoDB, E/R del catálogo de Glue) y sus PNG/SVG. Se regeneran con `python3 infra/diagramas/generar_diagramas.py`.
- **Informe técnico (PDF) y presentación (PowerPoint):** [entregables/](entregables/), con `generar_informe.py` y `generar_presentacion.js`.
- **Evidencia de Athena:** `entregables/athena_evidence.json` (4 consultas con JOIN y 2 vistas, con el ID de ejecución de cada una).

## CI/CD del frontend (AWS Amplify)

[amplify.yml](amplify.yml) compila la SPA de `frontend/` (`npm ci` + `npm run build`) y usa por defecto el API Gateway del proyecto (`VITE_API_BASE_URL` puede sobreescribirse en Amplify). Para desplegar en cada `git push` a `main`: Amplify → *Create new app* → *GitHub* → autorizar → repositorio `ProeyctParcialProp`, rama `main` (marcar *monorepo* con carpeta `frontend`) → agregar la regla de reescritura `/<*>` → `/index.html` (200).
