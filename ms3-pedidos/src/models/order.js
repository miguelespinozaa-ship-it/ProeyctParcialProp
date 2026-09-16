const pool = require("../db");

async function create({ customerId, restaurantId, direccionEntrega, total }, client = pool) {
  const { rows } = await client.query(
    `INSERT INTO orders (customer_id, restaurant_id, direccion_entrega, status, total)
     VALUES ($1, $2, $3, 'PEDIDO', $4) RETURNING *`,
    [customerId, restaurantId, direccionEntrega, total]
  );
  return rows[0];
}

async function findById(orderId) {
  const { rows } = await pool.query("SELECT * FROM orders WHERE id = $1", [orderId]);
  return rows[0] || null;
}

async function findByFilters({ customerId, restaurantId, deliveryId, status }) {
  const clauses = [];
  const values = [];
  if (customerId) {
    values.push(customerId);
    clauses.push(`customer_id = $${values.length}`);
  }
  if (restaurantId) {
    values.push(restaurantId);
    clauses.push(`restaurant_id = $${values.length}`);
  }
  if (deliveryId) {
    values.push(deliveryId);
    clauses.push(`delivery_id = $${values.length}`);
  }
  if (status) {
    values.push(status);
    clauses.push(`status = $${values.length}`);
  }
  const where = clauses.length ? `WHERE ${clauses.join(" AND ")}` : "";
  const { rows } = await pool.query(`SELECT * FROM orders ${where} ORDER BY created_at DESC`, values);
  return rows;
}

async function findAvailable() {
  const { rows } = await pool.query(
    "SELECT * FROM orders WHERE status = 'ENVIADO' AND delivery_id IS NULL ORDER BY created_at ASC"
  );
  return rows;
}

async function updateStatus(orderId, status) {
  const { rows } = await pool.query("UPDATE orders SET status = $1 WHERE id = $2 RETURNING *", [status, orderId]);
  return rows[0] || null;
}

async function claim(orderId, deliveryId) {
  const { rows } = await pool.query(
    `UPDATE orders SET delivery_id = $1
     WHERE id = $2 AND status = 'ENVIADO' AND delivery_id IS NULL
     RETURNING *`,
    [deliveryId, orderId]
  );
  return rows[0] || null;
}

async function deliver(orderId, deliveryId) {
  const { rows } = await pool.query(
    `UPDATE orders SET status = 'ENTREGADO'
     WHERE id = $1 AND delivery_id = $2 AND status = 'ENVIADO'
     RETURNING *`,
    [orderId, deliveryId]
  );
  return rows[0] || null;
}

async function distinctCustomerIds(restaurantId) {
  const { rows } = await pool.query("SELECT DISTINCT customer_id FROM orders WHERE restaurant_id = $1", [
    restaurantId,
  ]);
  return rows.map((r) => r.customer_id);
}

module.exports = {
  create,
  findById,
  findByFilters,
  findAvailable,
  updateStatus,
  claim,
  deliver,
  distinctCustomerIds,
};
