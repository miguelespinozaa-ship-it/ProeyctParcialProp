# Plan de Desarrollo — Paso a Paso (con pruebas en cada fase)

Orden pensado para probar cada pieza **antes** de construir la siguiente (nada se integra sin haber sido probado suelto primero). Referencias de endpoints: ver [microservicios/](microservicios/).

> ⚠️ **Regla de oro:** Fases 0-7 son **100% local** (tu máquina, `docker-compose.dev.yml`). Nada se sube a AWS hasta que el flujo completo (los 5 MS + BD) funcione local. Fase 10 recién ahí despliega en las 2 EC2 (ver [estructura-proyecto.md](estructura-proyecto.md)).

---

## Fase 0 — Prerrequisitos

- [ ] Instalar: Docker Desktop, Node.js 20+, Python 3.11+, Java 17+ / Maven, AWS CLI, Postman o Insomnia.
- [ ] Crear cuenta/organización AWS (o usar la del curso) y credenciales IAM de prueba.
- [ ] Crear los 5 repos (o 1 monorepo con carpetas `ms1/` `ms2/` `ms3/` `ms4/` `ms5/`) en GitHub, públicos.

**✅ Prueba:** `docker --version`, `node -v`, `python --version`, `mvn -v`, `aws --version` corren sin error.

---

## Fase 1 — Bases de datos en local (simulando EC2 #2)

- [ ] `docker-compose.db.yml` con MySQL 8.0, PostgreSQL 16, MongoDB (solo para desarrollo local).
- [ ] Crear las tablas de MS1 (`usuarios`, `direcciones`) y MS3 (`orders`, `order_items`) vía script/migración.
- [ ] Crear colección `restaurantes` en Mongo con 1 documento de prueba (platos + reseñas embebidos).

**✅ Prueba:** conectarse con un cliente (MySQL Workbench / `psql` / `mongosh`) a cada BD y hacer un `SELECT`/`find()` manual.

---

## Fase 2 — MS1 (Usuarios/Auth)

- [ ] Proyecto FastAPI, conexión a MySQL (SQLAlchemy), modelos `Usuario`/`Direccion`.
- [ ] Endpoints de `/auth/register` y `/auth/login` (rechazando `rol=admin`).
- [ ] Endpoints de perfil y direcciones.
- [ ] Seed manual: 1 customer, 1 delivery, 1 admin (con `restaurante_id` de prueba) — a mano, no el masivo todavía.
- [ ] Swagger en `/docs`.

**✅ Prueba (Swagger o curl):**
1. Registrar customer → login → recibir JWT.
2. `GET /users/{id}` con el token devuelve el perfil correcto.
3. Intentar registrar `rol=admin` → debe rechazar (400).

---

## Fase 3 — MS2 (Catálogo Restaurantes)

- [ ] Proyecto Spring Boot, conexión a MongoDB (Spring Data Mongo).
- [ ] Endpoints públicos de restaurantes/menú.
- [ ] Endpoints admin de CRUD platillos, validando `restaurante_id` del JWT (puede simularse con un header temporal mientras no hay integración real con MS1 todavía).
- [ ] Seed manual: 2-3 restaurantes con platos.
- [ ] Swagger en `/swagger-ui.html`.

**✅ Prueba:**
1. `GET /restaurants` lista los seedeados.
2. Como admin del restaurante A, crear un platillo en A → OK. Intentar crear en restaurante B → 403.
3. `GET /restaurants/{id}/menu/{dish_id}` devuelve precio correcto (este endpoint lo va a llamar MS3 después).

---

## Fase 4 — MS3 (Pedidos) — primera integración real

- [ ] Proyecto Express, conexión a PostgreSQL (Prisma/Sequelize/pg).
- [ ] `POST /orders`: por cada item, llama a **MS2** (`GET /restaurants/{id}/menu/{dish_id}`) para validar precio/disponibilidad antes de insertar.
- [ ] Endpoints de listado por `customer_id`, `restaurant_id`, `delivery_id`.
- [ ] `PUT /orders/{id}/status` (admin), `/claim` y `/deliver` (delivery), con las validaciones de rol/estado.
- [ ] `GET /restaurants/{id}/customers` llamando a **MS1** (`GET /users?rol=customer&ids=`).
- [ ] Swagger en `/api-docs`.

**✅ Prueba (integración MS3 ↔ MS2 ↔ MS1, todos corriendo en local con `docker-compose` de dev):**
1. Crear pedido con un `dish_id` real de MS2 → se crea en estado `PEDIDO` con precio correcto.
2. Crear pedido con `dish_id` inexistente → error controlado (no crashea).
3. Admin cambia a `ENVIADO`. Delivery lista `/orders/available`, hace `claim`, luego `deliver` → estado final `ENTREGADO`.
4. `GET /restaurants/{id}/customers` devuelve nombres reales (via MS1).

---

## Fase 5 — MS4 (Agregador/Rastreo)

- [ ] Proyecto FastAPI/Express sin BD, cliente HTTP (httpx/axios) hacia MS1/MS2/MS3 por variables de entorno `*_BASE_URL`.
- [ ] `GET /tracking/order/{order_id}`.
- [ ] Los 3 dashboards por rol (`/dashboard/customer/...`, `/dashboard/delivery/...`, `/dashboard/admin/...`).
- [ ] Manejo de error/timeout si un MS dependiente no responde (no debe tumbar el request completo, devolver parcial o 502 controlado).
- [ ] Swagger en `/docs`.

**✅ Prueba:**
1. Con datos de la Fase 4 ya creados, pegarle a `/tracking/order/{id}` y verificar que junta cliente+restaurante+estado correctamente.
2. Apagar MS2 a propósito y verificar que MS4 responde error controlado, no un 500 crudo.

---

## Fase 6 — Carga masiva (20,000 registros)

- [ ] `seed.py` (MS1) → ≥20,000 `usuarios` (faker/Python).
- [ ] `seed.js` (MS3) → ≥20,000 `orders` (con `order_items` coherentes, referenciando usuarios y restaurantes ya existentes).
- [ ] Ejecutar **una sola vez** contra las BD reales (no en cada arranque).

**✅ Prueba:** `SELECT COUNT(*)` en `usuarios` y `orders` ≥ 20,000. Endpoints de listado siguen respondiendo rápido (revisar índices si se ponen lentos).

---

## Fase 7 — Dockerización completa + integración local end-to-end

- [ ] `Dockerfile` para cada uno de los 5 MS.
- [ ] `docker-compose.yml` único (o dos: uno por EC2) levantando **los 5 MS + las 3 BD** juntos, con la red interna y las URLs de la Fase 5.
- [ ] NGINX como reverse proxy local, enrutando por path prefix a cada MS.

**✅ Prueba:** con un solo `docker-compose up`, repetir manualmente los checks de las Fases 2-5 pero pegándole a NGINX en vez de a cada puerto directo. Flujo completo: registrar customer → ver restaurantes → hacer pedido → admin lo envía → delivery lo jala y entrega → tracking muestra `ENTREGADO`.

---

## Fase 8 — MS5 (Analítico) — puede ir en paralelo desde Fase 1

> Depende del pipeline de Data Science (Fase 9), así que en la práctica se termina de probar al final, pero el esqueleto FastAPI + boto3 se puede armar desde ya.

- [ ] Proyecto FastAPI + boto3, endpoints `/analytics/top-restaurants`, `/analytics/user-metrics`, `/analytics/sales-summary`.
- [ ] Swagger en `/docs`.

**✅ Prueba (parcial, sin Athena real):** mockear la respuesta de Athena y verificar que el endpoint arma el JSON esperado. Prueba real se hace en Fase 9.

---

## Fase 9 — Pipeline Data Science (en paralelo, Integrante 3)

- [ ] EC2 de Ingesta + bucket S3.
- [ ] 3 contenedores `ingest-mysql`, `ingest-mongodb`, `ingest-postgres` (pull 100%, CSV/JSONL a S3).
- [ ] Glue Crawlers sobre el bucket → Data Catalog.
- [ ] `queries_and_views.sql`: 4 JOINs multi-tabla + 2 vistas (`v_resumen_ventas_restaurante`, `v_metricas_usuarios`).

**✅ Prueba:**
1. Cada contenedor de ingesta corre y deja archivos en S3 (`aws s3 ls`).
2. Glue Catalog muestra las tablas con el schema correcto.
3. Las 4 queries y las 2 vistas corren en la consola de Athena sin error.

**→ Vuelve a Fase 8:** conectar MS5 a las vistas reales y volver a probar `/analytics/*` con datos reales.

---

## Fase 10 — Infra AWS real (2 EC2)

- [ ] **EC2 #2 (privada)**: levantar `docker-compose` solo de BD (Mongo/Postgres/MySQL), Security Group sin acceso público.
- [ ] **EC2 #1**: levantar `docker-compose` de los 5 MS + NGINX, apuntando por IP privada a EC2 #2.
- [ ] Security Groups: EC2 #2 solo acepta tráfico del SG de EC2 #1.
- [ ] AWS API Gateway (HTTPS) apuntando a EC2 #1 (NGINX).

**✅ Prueba:** repetir el flujo end-to-end de la Fase 7 pero contra la URL pública de API Gateway (no localhost). Verificar que la BD **no** es alcanzable desde internet (intento de conexión externo debe fallar/timeout).

---

## Fase 11 — Frontend SPA (Integrante 4)

- [ ] Armar login con redirect por `rol` (como en el diagrama: admin/delivery/customer).
- [ ] Pantallas: browse restaurantes + carrito (customer), CRUD menú + pedidos (admin), pool de pedidos + entrega (delivery), dashboard analítico (MS5).
- [ ] Consumir mínimo 2 endpoints por MS (10 en total).
- [ ] Deploy en AWS Amplify (o Vercel si así lo decidieron) con CI/CD desde GitHub.

**✅ Prueba:** flujo completo desde el navegador contra la API pública (Fase 10), los 3 roles funcionando.

---

## Fase 12 — Entregables finales

- [ ] Diagrama de Arquitectura en draw.io (Amplify, API Gateway, 2 EC2, S3, Glue, Athena, NGINX).
- [ ] Diagrama ER del Data Catalog (Glue).
- [ ] Informe técnico (Word/PDF) + PPT resumen.
- [ ] Verificar checklist completo contra [proyecto-parcial-requisitos.md](proyecto-parcial-requisitos.md).

---

## Orden resumido (quién puede empezar en paralelo)

| Cuándo | Integrante 1 | Integrante 2 | Integrante 3 | Integrante 4 |
|---|---|---|---|---|
| Semana 3-4 | Fase 1-2 (MS1) | Fase 3 (MS2) esqueleto | Fase 9 arranca (EC2 ingesta, S3) | Boceto SPA + Amplify vacío |
| Semana 4-5 | Fase 4 (MS3) | Fase 5 (MS4) + Fase 8 esqueleto MS5 | Fase 9 ETL + Glue | Login/roles frontend |
| Semana 5-6 | Fase 6 (seed 20k) + Fase 7 | Fase 8 real (Athena) + Swagger en los 5 | Fase 9 Athena queries/vistas | Fase 11 integración completa |
| Semana 6 | Fase 10 (EC2 #1/#2) | Apoyo integración | Apoyo diagrama ER | Fase 12 diagramas/informe |
