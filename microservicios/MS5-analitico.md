# MS5 — Servicio Analítico

**Stack:** Python (FastAPI) + `boto3` (AWS Athena)
**Puerto:** `8085`
**Base path:** `/api/v1`
**Responsable:** Integrante 2
**Docs:** Swagger UI en `/docs`

Sin base de datos propia: ejecuta queries contra las **Vistas de Athena** (`v_resumen_ventas_restaurante`, `v_metricas_usuarios`) creadas por Integrante 3 sobre el Data Catalog de Glue (alimentado por los 3 contenedores de ingesta desde S3).

## Endpoints

| Método | Ruta | Descripción | Vista/Query Athena |
|---|---|---|---|
| GET | `/api/v1/analytics/top-restaurants` | Ranking de restaurantes por ventas/calificación | `v_resumen_ventas_restaurante` |
| GET | `/api/v1/analytics/user-metrics` | Métricas de usuarios (pedidos, gasto promedio, rango de edad) | `v_metricas_usuarios` |
| GET | `/api/v1/analytics/sales-summary` | Resumen de ventas por periodo (JOIN orders+order_items+restaurantes) | query ad-hoc |
| GET | `/api/v1/analytics/views` | Lista vistas/queries disponibles (metadata) | — |

### Infra
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Healthcheck |
| GET | `/docs` | Swagger UI |

## Consumido por
- **Frontend** → dashboard de analítica y gráficos (mínimo 2 endpoints exigidos)

## Este servicio consume
- **AWS Athena** (vía `boto3.client('athena')`) — no llama a MS1/MS2/MS3/MS4 directamente; opera sobre datos ya replicados en S3/Glue por el pipeline ETL.

## Configuración necesaria
```
AWS_REGION=us-east-1
ATHENA_DATABASE=ubereats_datalake
ATHENA_OUTPUT_S3=s3://ubereats-datalake-utec/athena-results/
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```
