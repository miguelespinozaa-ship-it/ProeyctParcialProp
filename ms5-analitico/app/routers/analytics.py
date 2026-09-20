import math
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app import mock_data
from app.athena_client import ATHENA_MOCK, run_query

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/top-restaurants")
def top_restaurants():
    if ATHENA_MOCK:
        return {"source": "mock", "data": mock_data.mock_top_restaurants()}
    rows = run_query("SELECT * FROM v_resumen_ventas_restaurante ORDER BY total_ventas DESC")
    return {"source": "athena", "data": rows}


DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
_COUNT_TTL_SECONDS = 60
_count_cache: dict = {}


def _cached_count(key: str, sql: str) -> int:
    """El total cambia poco y cada consulta a Athena tarda segundos: se cachea un minuto."""
    hit = _count_cache.get(key)
    if hit and time.time() - hit[0] < _COUNT_TTL_SECONDS:
        return hit[1]
    total = int(run_query(sql)[0]["total"])
    _count_cache[key] = (time.time(), total)
    return total


@router.get("/user-metrics")
def user_metrics(
    page: Optional[int] = Query(None, ge=1, description="Activa el paginado (desde 1). Sin page/page_size devuelve todo."),
    page_size: Optional[int] = Query(None, ge=1, description=f"Por defecto {DEFAULT_PAGE_SIZE}, máximo {MAX_PAGE_SIZE}"),
):
    paginated = page is not None or page_size is not None

    if not paginated:
        if ATHENA_MOCK:
            return {"source": "mock", "data": mock_data.mock_user_metrics()}
        rows = run_query("SELECT * FROM v_metricas_usuarios ORDER BY usuario_id")
        return {"source": "athena", "data": rows}

    page = page or 1
    size = min(page_size or DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE)
    offset = (page - 1) * size  # enteros validados por FastAPI: seguro interpolarlos en el SQL

    if ATHENA_MOCK:
        all_rows = mock_data.mock_user_metrics()
        total, rows, source = len(all_rows), all_rows[offset : offset + size], "mock"
    else:
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                f_rows = pool.submit(
                    run_query,
                    f"SELECT * FROM v_metricas_usuarios ORDER BY usuario_id OFFSET {offset} LIMIT {size}",
                )
                f_total = pool.submit(
                    _cached_count, "user_metrics", "SELECT COUNT(*) AS total FROM v_metricas_usuarios"
                )
                rows, total = f_rows.result(), f_total.result()
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=f"Athena no disponible: {exc}")
        source = "athena"

    return {
        "source": source,
        "data": rows,
        "page": page,
        "page_size": size,
        "total": total,
        "total_pages": math.ceil(total / size),
    }


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
