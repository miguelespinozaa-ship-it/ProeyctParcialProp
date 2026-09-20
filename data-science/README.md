# Data Science — Ingesta y Analytics (Fase 9)

Pipeline: 3 contenedores de ingesta (Pull 100%) → S3 (data lake) → Glue Crawler (Data Catalog) → Athena (queries + vistas) → consumido por MS5.

Todo el código de acá está probado y ya se ejecutó de verdad en AWS: la ingesta corre desde la MV dedicada `PP-Ingest-VM`, que usa el rol de instancia (sin claves en el `.env`). Esta guía sirve para repetir el proceso.

## 0. Prerrequisitos

- AWS CLI instalado y configurado (`aws configure`) con un usuario IAM (no la cuenta root) con permisos para S3, EC2, IAM, Glue y Athena.
- Una instancia EC2 para la "MV de Ingesta" (puede ser `t2.micro`/`t3.micro`, con Docker instalado — mismo setup que las otras EC2 del proyecto).
- Las 2 EC2 del backend (App Tier + DB Tier) ya desplegadas (Fase 10), con datos reales cargados (Fases 2-6).

## 1. Bucket S3

```bash
aws s3 mb s3://<tu-bucket-unico> --region us-east-1
```

El nombre debe ser único a nivel global de AWS — `ubereats-datalake-utec` (el que aparece en la documentación) probablemente ya esté tomado por otro alumno/curso. Usá algo como `<tu-usuario>-ubereats-datalake`.

## 2. Security Group de la MV de BD

La MV de Ingesta es una instancia *distinta* a las 2 EC2 del backend, así que el Security Group de la MV de BD (que hoy solo acepta tráfico del SG de la MV de App) necesita una regla nueva: puertos 3306/5432 desde el Security Group de la MV de Ingesta.

## 3. Rol IAM para Glue

Un rol con:
- Managed policy `AWSGlueServiceRole`
- Una policy inline que dé `s3:GetObject`/`s3:ListBucket` sobre tu bucket

Lo vas a necesitar al crear el Crawler en el paso 5.

## 4. Correr la ingesta

En la MV de Ingesta (o desde cualquier máquina con red hacia la MV de BD y credenciales AWS):

```bash
cd data-science
cp .env.example .env
# completar DB_HOST (IP privada de la MV de BD) y S3_BUCKET. En EC2 no hacen falta claves AWS: se usa el rol de la instancia
docker compose -f docker-compose.ingest.yml up --build
```

**✅ Prueba:**
```bash
aws s3 ls s3://<tu-bucket>/raw/ --recursive
```
Deberías ver `raw/mysql/usuarios/...`, `raw/mysql/direcciones/...`, `raw/mongodb/restaurantes/...`, `raw/postgres/orders/...`, `raw/postgres/order_items/...`.

## 5. Glue Crawler

En la consola de Glue → Crawlers → Create crawler:
- Data source: `s3://<tu-bucket>/raw/` (recursivo — un crawler para toda la carpeta detecta cada subcarpeta como una tabla distinta)
- IAM role: el del paso 3
- Target database: `ubereats_datalake` (mismo nombre que `ATHENA_DATABASE` en `.env.example` de la raíz del proyecto)
- Run on demand

**✅ Prueba:** correlo y confirmá en el Data Catalog que aparecen 5 tablas: `usuarios`, `direcciones`, `restaurantes`, `orders`, `order_items`, con el schema correcto (`restaurantes` con `platos` y `resenas` como arrays anidados).

## 6. Athena — queries y vistas

En la consola de Athena:
1. Settings → Query result location → `s3://<tu-bucket>/athena-results/` (debe coincidir con `ATHENA_OUTPUT_S3` del `.env` raíz)
2. Database: `ubereats_datalake`
3. Correr cada bloque de [`athena/queries_and_views.sql`](athena/queries_and_views.sql) — las 4 queries con JOIN y las 2 `CREATE VIEW`

**✅ Prueba:** las 4 queries devuelven filas con datos reales, y `SELECT * FROM v_resumen_ventas_restaurante` / `v_metricas_usuarios` funcionan.

## 7. Diagrama ER del Data Catalog

Documentar las tablas de Glue y cómo se relacionan (mismas relaciones lógicas que ya existen entre microservicios: `orders.customer_id` → `usuarios.id`, `orders.restaurant_id` → `restaurantes._id`, `order_items.order_id` → `orders.id`, `direcciones.usuario_id` → `usuarios.id`). Va en `infra/diagramas/` junto con el diagrama de arquitectura general (Fase 12).

## 8. Conectar MS5 a Athena real

Una vez las vistas existen de verdad:

```bash
# en .env (raíz del proyecto)
ATHENA_MOCK=false
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
ATHENA_DATABASE=ubereats_datalake
ATHENA_OUTPUT_S3=s3://<tu-bucket>/athena-results/
```

```bash
docker compose -f docker-compose.dev.yml up -d --build ms5
curl http://localhost:8085/api/v1/analytics/top-restaurants
```

La respuesta debería traer `"source": "athena"` en vez de `"source": "mock"`, con datos reales.

## Nota: "rango de edad" → "antigüedad de cuenta"

El modelo de `usuarios` (MS1) no tiene fecha de nacimiento, solo `fecha_registro`. `v_metricas_usuarios` agrupa por antigüedad de cuenta (días desde el registro) en vez de edad. Si preferís tener edad real, hay que agregar una columna `fecha_nacimiento` a MS1 (`db/mysql/init/01-schema.sql` + `app/models.py` + `seed.py`) y volver a correr el seed masivo.
