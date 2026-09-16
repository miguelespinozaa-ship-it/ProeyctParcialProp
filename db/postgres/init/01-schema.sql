-- MS3 — Pedidos (PostgreSQL 16)
-- orders (1) ──< (N) order_items

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    restaurant_id VARCHAR(50) NOT NULL,
    delivery_id INTEGER NULL,
    direccion_entrega TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PEDIDO' CHECK (status IN ('PEDIDO', 'ENVIADO', 'ENTREGADO')),
    total NUMERIC(10, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    dish_id VARCHAR(50) NOT NULL,
    nombre_plato VARCHAR(255) NOT NULL,
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(10, 2) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_restaurant ON orders(restaurant_id, status);
CREATE INDEX IF NOT EXISTS idx_orders_delivery ON orders(delivery_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
