# MS5 — Analítico

**Stack:** Python 3.11 (FastAPI) + `boto3` — **sin base de datos propia, consulta Amazon Athena**
**Puerto:** `8085` · **Base path:** `/api/v1` · **Docs:** `/docs`
**Código:** [`ms5-analitico/`](../ms5-analitico/)
**En AWS:** `https://<api-gateway>/ms5/...`

## Qué resuelve

Es la puerta REST hacia el data lake: traduce peticiones HTTP en consultas SQL sobre Athena (`SELECT` sobre las vistas `v_resumen_ventas_restaurante` y `v_metricas_usuarios`, ver [`data-science/athena/queries_and_views.sql`](../data-science/athena/queries_and_views.sql)) y devuelve el resultado como JSON. No llama a MS1-MS4 en tiempo de ejecución.

## Cómo se conecta a Athena

Con `boto3.client("athena")`: `start_query_execution` → sondea `get_query_execution` hasta `SUCCEEDED`/`FAILED` → `get_query_results` (paginado internamente con `NextToken`). Sin usuario/contraseña: en AWS usa el rol de la instancia EC2 (`LabInstanceProfile`); en local usa `~/.aws/credentials`.

`ATHENA_MOCK=true` (default en `.env.example`) hace que los 3 endpoints devuelvan datos de ejemplo con la misma forma que Athena, sin llamar a AWS — así se puede desarrollar y probar sin credenciales. En AWS está en `false`.

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/v1/analytics/top-restaurants` | `{source,data}` — `SELECT * FROM v_resumen_ventas_restaurante ORDER BY total_ventas DESC`. Sin paginar (son pocos restaurantes con ventas). |
| GET | `/api/v1/analytics/user-metrics?page=&page_size=` | Sin parámetros: `{source,data}` con todo. Con ellos: agrega `page,page_size,total,total_pages`; usa `OFFSET/LIMIT` en el `SELECT` y un `ThreadPoolExecutor` para pedir filas y conteo en paralelo. El `COUNT(*)` se cachea 60 s (cambia poco y tarda segundos en Athena). `422` si `page`/`page_size` son inválidos; `502` si Athena falla. |
| GET | `/api/v1/analytics/sales-summary` | `{source,data}` — ventas y pedidos por mes (JOIN `orders`+`order_items`, agrupado por `date_format(created_at,'%Y-%m')`). |
| GET | `/api/v1/analytics/views` | Metadata: qué vistas existen y qué endpoint las sirve, más si está en modo mock. |
| GET | `/health` | |

`source` en cada respuesta vale `"mock"` o `"athena"`, para que el frontend (o quien pruebe la API) sepa si los datos son reales.

## Por qué tarda más que los otros

Cada consulta paginada a Athena mide de 2 a 8 segundos, porque es un motor de consulta batch sobre archivos en S3, no una base de datos transaccional con índices. Es la razón por la que `user-metrics` cachea el conteo total y por la que el frontend muestra "Consultando Athena..." mientras espera.

## Quién lo consume
- **Frontend**: pantalla de Analítica del admin — top de restaurantes y métricas de usuarios (2 llamadas REST).

## Correrlo solo
```bash
# modo mock (sin AWS):
docker compose -f docker-compose.dev.yml up -d --build ms5

# contra Athena real: ATHENA_MOCK=false en .env + credenciales AWS válidas con permiso athena:*, glue:GetTable, s3:GetObject
```
