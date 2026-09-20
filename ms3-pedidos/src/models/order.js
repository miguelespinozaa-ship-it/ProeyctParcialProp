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

function buildWhere({ customerId, restaurantId, deliveryId, status }) {
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
  return { where: clauses.length ? `WHERE ${clauses.join(" AND ")}` : "", values };
}

// Sin limit/offset devuelve todo (comportamiento original). Orden estable para poder paginar.
async function findByFilters({ limit, offset, ...filters }) {
  const { where, values } = buildWhere(filters);
  let sql = `SELECT * FROM orders ${where} ORDER BY created_at DESC, id DESC`;
  if (limit !== undefined) {
    values.push(limit, offset);
    sql += ` LIMIT $${values.length - 1} OFFSET $${values.length}`;
  }
  const { rows } = await pool.query(sql, values);
  return rows;
}

async function countByFilters(filters) {
  const { where, values } = buildWhere(filters);
  const { rows } = await pool.query(`SELECT COUNT(*)::int AS total FROM orders ${where}`, values);
  return rows[0].total;
}

// Cantidad de pedidos por estado (para dashboards, sin traer las filas).
async function countByStatus(filters) {
  const { where, values } = buildWhere({ ...filters, status: undefined });
  const { rows } = await pool.query(
    `SELECT status, COUNT(*)::int AS total FROM orders ${where} GROUP BY status`,
    values
  );
  const result = { PEDIDO: 0, ENVIADO: 0, ENTREGADO: 0 };
  for (const r of rows) result[r.status] = r.total;
  result.total = result.PEDIDO + result.ENVIADO + result.ENTREGADO;
  return result;
}

async function findAvailable({ limit, offset } = {}) {
  const values = [];
  let sql = "SELECT * FROM orders WHERE status = 'ENVIADO' AND delivery_id IS NULL ORDER BY created_at ASC, id ASC";
  if (limit !== undefined) {
    values.push(limit, offset);
    sql += " LIMIT $1 OFFSET $2";
  }
  const { rows } = await pool.query(sql, values);
  return rows;
}

async function countAvailable() {
  const { rows } = await pool.query(
    "SELECT COUNT(*)::int AS total FROM orders WHERE status = 'ENVIADO' AND delivery_id IS NULL"
  );
  return rows[0].total;
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

async function distinctCustomerIds(restaurantId, { limit, offset } = {}) {
  const values = [restaurantId];
  let sql = "SELECT DISTINCT customer_id FROM orders WHERE restaurant_id = $1 ORDER BY customer_id";
  if (limit !== undefined) {
    values.push(limit, offset);
    sql += " LIMIT $2 OFFSET $3";
  }
  const { rows } = await pool.query(sql, values);
  return rows.map((r) => r.customer_id);
}

async function countDistinctCustomers(restaurantId) {
  const { rows } = await pool.query(
    "SELECT COUNT(DISTINCT customer_id)::int AS total FROM orders WHERE restaurant_id = $1",
    [restaurantId]
  );
  return rows[0].total;
}

module.exports = {
  create,
  findById,
  findByFilters,
  countByFilters,
  countByStatus,
  findAvailable,
  countAvailable,
  updateStatus,
  claim,
  deliver,
  distinctCustomerIds,
  countDistinctCustomers,
};
