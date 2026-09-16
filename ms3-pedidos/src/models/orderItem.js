const pool = require("../db");

async function createMany(orderId, items, client = pool) {
  const inserted = [];
  for (const item of items) {
    const { rows } = await client.query(
      `INSERT INTO order_items (order_id, dish_id, nombre_plato, cantidad, precio_unitario)
       VALUES ($1, $2, $3, $4, $5) RETURNING *`,
      [orderId, item.dishId, item.nombrePlato, item.cantidad, item.precioUnitario]
    );
    inserted.push(rows[0]);
  }
  return inserted;
}

async function findByOrderId(orderId) {
  const { rows } = await pool.query("SELECT * FROM order_items WHERE order_id = $1", [orderId]);
  return rows;
}

module.exports = { createMany, findByOrderId };
