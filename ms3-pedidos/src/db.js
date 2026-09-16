const { Pool } = require("pg");

const pool = new Pool({
  host: process.env.PG_HOST || "localhost",
  port: process.env.PG_PORT || 5432,
  user: process.env.PG_USER || "ms3_user",
  password: process.env.PG_PASSWORD || "ms3_password",
  database: process.env.PG_DATABASE || "ms3_pedidos",
});

module.exports = pool;
