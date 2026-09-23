# Data Science — Ingesta y Analytics

Pipeline: 3 contenedores de ingesta (pull 100%) → S3 (data lake) → Glue Crawler (Data Catalog) → Athena (queries + vistas) → consumido por MS5.

Ya está corriendo en AWS: la ingesta se ejecuta desde la MV `PP-Ingest-VM`, con el rol de la instancia (sin claves en `.env`). Esta guía sirve para repetirlo en otra cuenta — ver también [`DESPLIEGUE-AWS.md`](../DESPLIEGUE-AWS.md) en la raíz para el resto de la infraestructura.

## 0. Prerrequisitos

- AWS CLI configurado con permisos para S3, EC2, IAM, Glue y Athena.
- Una EC2 para la ingesta (`t2.micro`/`t3.micro`, con Docker).
- La EC2 de BD y las de App ya desplegadas, con datos cargados.

## 1. Bucket S3

```bash
aws s3 mb s3://<tu-bucket-unico> --region us-east-1
```

El nombre debe ser único a nivel global de S3.

## 2. Security Group de la BD

La MV de Ingesta es distinta a las de App y BD: el Security Group de la BD necesita una regla para
puertos 3306/5432/27017 desde el Security Group de la MV de Ingesta.

## 3. Rol IAM para Glue

Un rol con la managed policy `AWSGlueServiceRole` y una policy inline con `s3:GetObject`/`s3:ListBucket`
sobre el bucket. Se usa al crear el Crawler en el paso 5.

## 4. Correr la ingesta

En la MV de Ingesta:

```bash
cd data-science
cp .env.example .env
# completar DB_HOST (IP privada de la BD) y S3_BUCKET
docker compose -f docker-compose.ingest.yml up --build
```

Verificación:
```bash
aws s3 ls s3://<tu-bucket>/raw/ --recursive
```
Debe verse `raw/mysql/usuarios/...`, `raw/mysql/direcciones/...`, `raw/mongodb/restaurantes/...`,
`raw/postgres/orders/...`, `raw/postgres/order_items/...`.

## 5. Glue Crawler

En la consola de Glue → Crawlers → Create crawler:
- Data source: `s3://<tu-bucket>/raw/` (un crawler para toda la carpeta detecta cada subcarpeta como tabla)
- IAM role: el del paso 3
- Target database: `ubereats_datalake`
- Run on demand

Verificación: el Data Catalog debe mostrar 5 tablas (`usuarios`, `direcciones`, `restaurantes`, `orders`,
`order_items`), con `restaurantes` mostrando `platos` y `resenas` como arrays anidados.

## 6. Athena — queries y vistas

En la consola de Athena:
1. Settings → Query result location → `s3://<tu-bucket>/athena-results/`
2. Database: `ubereats_datalake`
3. Correr cada bloque de [`athena/queries_and_views.sql`](athena/queries_and_views.sql) — las 4 queries con JOIN y las 2 `CREATE VIEW`, sentencia por sentencia.

## 7. Diagrama E/R del Data Catalog

Las tablas de Glue y sus relaciones ya están documentadas en [`infra/diagramas/er-catalogo-glue.png`](../infra/diagramas/er-catalogo-glue.png) (mismas relaciones lógicas que entre microservicios: `orders.customer_id → usuarios.id`, `orders.restaurant_id → restaurantes._id`, `order_items.order_id → orders.id`, `direcciones.usuario_id → usuarios.id`).

## 8. Conectar MS5 a Athena real

```bash
# en .env de la App Tier
ATHENA_MOCK=false
ATHENA_DATABASE=ubereats_datalake
ATHENA_OUTPUT_S3=s3://<tu-bucket>/athena-results/
```
```bash
docker compose -f docker-compose.app.yml up -d --build ms5
curl localhost/ms5/api/v1/analytics/top-restaurants
```
La respuesta debe traer `"source": "athena"` con datos reales, en vez de `"source": "mock"`.

## Antigüedad de cuenta en vez de edad

El modelo de `usuarios` (MS1) no tiene fecha de nacimiento, solo `fecha_registro`. `v_metricas_usuarios`
agrupa por antigüedad de cuenta (días desde el registro) en vez de edad.
