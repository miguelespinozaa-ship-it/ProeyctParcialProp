/**
 * Carga masiva de pedidos (>= 20,000 registros) - MS3.
 * Ejecutar UNA sola vez contra la base real (Fase 6): `node seed.js`
 * Requiere que MS1 (usuarios) y MS2 (restaurantes/platos) ya tengan datos reales —
 * este script los consulta vía HTTP (no asume ids fijos) en vez de hardcodear valores.
 */
require("dotenv").config();
const { Pool } = require("pg");
const axios = require("axios");
const { faker } = require("@faker-js/faker");

const MS1_BASE_URL = process.env.MS1_BASE_URL || "http://localhost:8081";
const MS2_BASE_URL = process.env.MS2_BASE_URL || "http://localhost:8082";
const TOTAL_ORDERS = 20000;
const BATCH_SIZE = 100;
const STATUSES = ["PEDIDO", "ENVIADO", "ENTREGADO"];

// Pool dedicado con más conexiones concurrentes que el pool de runtime (src/db.js),
// solo para acelerar esta carga masiva de una sola vez.
const pool = new Pool({
  host: process.env.PG_HOST || "localhost",
  port: process.env.PG_PORT || 5432,
  user: process.env.PG_USER || "ms3_user",
  password: process.env.PG_PASSWORD || "ms3_password",
  database: process.env.PG_DATABASE || "ms3_pedidos",
  max: 20,
});

async function fetchCustomerIds() {
  const { data } = await axios.get(`${MS1_BASE_URL}/api/v1/users`, {
    params: { rol: "customer" },
    timeout: 120000,
  });
  return data.map((u) => u.id);
}

async function fetchRestaurantsWithDishes() {
  const { data } = await axios.get(`${MS2_BASE_URL}/api/v1/restaurants`, { timeout: 30000 });
  return data
    .filter((r) => Array.isArray(r.platos) && r.platos.length > 0)
    .map((r) => ({ id: r.id, platos: r.platos }));
}

async function createOrder(customerId, restaurant) {
  const status = faker.helpers.arrayElement(STATUSES);
  const cantidadItems = Math.min(faker.number.int({ min: 1, max: 3 }), restaurant.platos.length);
  const platosElegidos = faker.helpers.arrayElements(restaurant.platos, cantidadItems);

  let total = 0;
  const items = platosElegidos.map((dish) => {
    const cantidad = faker.number.int({ min: 1, max: 4 });
    total += dish.precio * cantidad;
    return { dish, cantidad };
  });

  const { rows } = await pool.query(
    `INSERT INTO orders (customer_id, restaurant_id, direccion_entrega, status, total)
     VALUES ($1, $2, $3, $4, $5) RETURNING id`,
    [customerId, restaurant.id, faker.location.streetAddress(), status, total.toFixed(2)]
  );
  const orderId = rows[0].id;

  await Promise.all(
    items.map(({ dish, cantidad }) =>
      pool.query(
        `INSERT INTO order_items (order_id, dish_id, nombre_plato, cantidad, precio_unitario)
         VALUES ($1, $2, $3, $4, $5)`,
        [orderId, dish.id, dish.nombre, cantidad, dish.precio]
      )
    )
  );
}

async function seed() {
  console.log("Obteniendo customers de MS1...");
  const customerIds = await fetchCustomerIds();
  console.log(`${customerIds.length} customers encontrados.`);

  console.log("Obteniendo restaurantes/platos de MS2...");
  const restaurants = await fetchRestaurantsWithDishes();
  console.log(`${restaurants.length} restaurantes con platos encontrados.`);

  if (customerIds.length === 0 || restaurants.length === 0) {
    throw new Error("Se necesitan customers en MS1 y restaurantes con platos en MS2 antes de correr este seed.");
  }

  for (let start = 0; start < TOTAL_ORDERS; start += BATCH_SIZE) {
    const end = Math.min(start + BATCH_SIZE, TOTAL_ORDERS);
    const batch = [];
    for (let i = start; i < end; i++) {
      const customerId = faker.helpers.arrayElement(customerIds);
      const restaurant = faker.helpers.arrayElement(restaurants);
      batch.push(createOrder(customerId, restaurant));
    }
    await Promise.all(batch);
    console.log(`${end} / ${TOTAL_ORDERS} pedidos creados...`);
  }

  console.log(`Seed completo: ${TOTAL_ORDERS} pedidos.`);
}

seed()
  .catch((err) => {
    console.error("Error en seed:", err.message);
    process.exitCode = 1;
  })
  .finally(() => pool.end());
