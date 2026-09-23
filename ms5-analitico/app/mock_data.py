"""Datos de ejemplo (ATHENA_MOCK=true): misma forma que las vistas reales
(`v_resumen_ventas_restaurante`, `v_metricas_usuarios`), pero fijos.
"""


def mock_top_restaurants() -> list[dict]:
    return [
        {
            "restaurante_id": "6aa79949d3bbb088661c974f",
            "nombre": "Sabor Criollo",
            "total_ventas": 15420.50,
            "num_pedidos": 312,
            "calificacion_promedio": 4.5,
        },
        {
            "restaurante_id": "6aa79949d3bbb088661c9750",
            "nombre": "Pizza Bella",
            "total_ventas": 9876.30,
            "num_pedidos": 198,
            "calificacion_promedio": 4.2,
        },
    ]


def mock_user_metrics() -> list[dict]:
    # Misma forma que v_metricas_usuarios (data-science/athena/queries_and_views.sql).
    return [
        {"usuario_id": 1, "nombre": "Cliente Demo", "num_pedidos": 12, "gasto_promedio": 45.80, "antiguedad_cuenta": "90+ dias"},
        {"usuario_id": 4, "nombre": "Juan Perez", "num_pedidos": 5, "gasto_promedio": 32.10, "antiguedad_cuenta": "31-90 dias"},
        {"usuario_id": 15000, "nombre": "Usuario Demo", "num_pedidos": 1, "gasto_promedio": 28.50, "antiguedad_cuenta": "0-30 dias"},
    ]


def mock_sales_summary() -> list[dict]:
    return [
        {"periodo": "2026-08", "total_ventas": 48230.75, "num_pedidos": 987},
        {"periodo": "2026-09", "total_ventas": 31450.20, "num_pedidos": 642},
    ]
