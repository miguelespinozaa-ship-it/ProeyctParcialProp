

-- ============================================================
-- 1) Ventas totales por restaurante (orders + order_items + mongodb)
-- ============================================================
SELECT
    r.nombre AS restaurante,
    COUNT(DISTINCT o.id) AS num_pedidos,
    SUM(oi.cantidad * oi.precio_unitario) AS total_ventas
FROM orders o
JOIN order_items oi ON oi.order_id = o.id
JOIN mongodb r ON r._id."$oid" = o.restaurant_id
GROUP BY r.nombre
ORDER BY total_ventas DESC;

-- ============================================================
-- 2) Clientes con más gasto, con nombre real (orders + usuarios)
-- ============================================================
SELECT
    u.nombre AS cliente,
    u.email,
    COUNT(o.id) AS num_pedidos,
    SUM(o.total) AS gasto_total
FROM orders o
JOIN usuarios u ON u.id = o.customer_id
GROUP BY u.nombre, u.email
ORDER BY gasto_total DESC
LIMIT 50;

-- ============================================================
-- 3) Platos más vendidos por restaurante (order_items + orders + mongodb)
-- ============================================================
SELECT
    r.nombre AS restaurante,
    oi.nombre_plato,
    SUM(oi.cantidad) AS unidades_vendidas
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
JOIN mongodb r ON r._id."$oid" = o.restaurant_id
GROUP BY r.nombre, oi.nombre_plato
ORDER BY unidades_vendidas DESC
LIMIT 50;

-- ============================================================
-- 4) Ciudad registrada del cliente vs dirección real de entrega (orders + usuarios + direcciones)
-- ============================================================
SELECT
    u.nombre AS cliente,
    d.ciudad AS ciudad_registrada,
    o.direccion_entrega,
    COUNT(o.id) AS num_pedidos
FROM orders o
JOIN usuarios u ON u.id = o.customer_id
LEFT JOIN direcciones d ON d.usuario_id = u.id AND d.es_principal = 1
GROUP BY u.nombre, d.ciudad, o.direccion_entrega
ORDER BY num_pedidos DESC
LIMIT 50;

-- ============================================================
-- Vista 1: v_resumen_ventas_restaurante (consumida por MS5 GET /analytics/top-restaurants)
-- ============================================================
CREATE OR REPLACE VIEW v_resumen_ventas_restaurante AS
SELECT
    r._id."$oid" AS restaurante_id,
    r.nombre,
    COUNT(DISTINCT o.id) AS num_pedidos,
    SUM(oi.cantidad * oi.precio_unitario) AS total_ventas,
    r.calificacion_promedio
FROM orders o
JOIN order_items oi ON oi.order_id = o.id
JOIN mongodb r ON r._id."$oid" = o.restaurant_id
GROUP BY r._id."$oid", r.nombre, r.calificacion_promedio;

-- ============================================================
-- Vista 2: v_metricas_usuarios (consumida por MS5 GET /analytics/user-metrics)
-- ============================================================
CREATE OR REPLACE VIEW v_metricas_usuarios AS
SELECT
    u.id AS usuario_id,
    u.nombre,
    COUNT(o.id) AS num_pedidos,
    COALESCE(AVG(o.total), 0) AS gasto_promedio,
    CASE
        WHEN date_diff('day', date(substr(u.fecha_registro, 1, 10)), current_date) < 30 THEN '0-30 dias'
        WHEN date_diff('day', date(substr(u.fecha_registro, 1, 10)), current_date) < 90 THEN '31-90 dias'
        ELSE '90+ dias'
    END AS antiguedad_cuenta
FROM usuarios u
LEFT JOIN orders o ON o.customer_id = u.id
GROUP BY u.id, u.nombre, u.fecha_registro;
