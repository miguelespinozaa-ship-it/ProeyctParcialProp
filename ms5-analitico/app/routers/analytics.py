from fastapi import APIRouter

from app import mock_data
from app.athena_client import ATHENA_MOCK, run_query

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/top-restaurants")
def top_restaurants():
    if ATHENA_MOCK:
        return {"source": "mock", "data": mock_data.mock_top_restaurants()}
    rows = run_query("SELECT * FROM v_resumen_ventas_restaurante ORDER BY total_ventas DESC")
    return {"source": "athena", "data": rows}


@router.get("/user-metrics")
def user_metrics():
    if ATHENA_MOCK:
        return {"source": "mock", "data": mock_data.mock_user_metrics()}
    rows = run_query("SELECT * FROM v_metricas_usuarios")
    return {"source": "athena", "data": rows}


@router.get("/sales-summary")
def sales_summary():
    if ATHENA_MOCK:
        return {"source": "mock", "data": mock_data.mock_sales_summary()}
    rows = run_query(
        """
        SELECT date_format(o.created_at, '%Y-%m') AS periodo,
               SUM(o.total) AS total_ventas,
               COUNT(DISTINCT o.id) AS num_pedidos
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.id
        GROUP BY 1
        ORDER BY 1 DESC
        """
    )
    return {"source": "athena", "data": rows}


@router.get("/views")
def list_views():
    return {
        "mock_mode": ATHENA_MOCK,
        "views": [
            {"name": "v_resumen_ventas_restaurante", "endpoint": "/top-restaurants"},
            {"name": "v_metricas_usuarios", "endpoint": "/user-metrics"},
        ],
    }
