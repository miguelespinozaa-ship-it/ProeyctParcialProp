require("dotenv").config();
const cors = require("cors");
const express = require("express");
const swaggerUi = require("swagger-ui-express");

const customersRouter = require("./routes/customers");
const ordersRouter = require("./routes/orders");
const openapiSpec = require("./openapi.json");

const app = express();
app.use(cors());
app.use(express.json());

app.use("/api/v1", ordersRouter);
app.use("/api/v1", customersRouter);
app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(openapiSpec));

app.get("/health", (req, res) => res.json({ status: "ok", service: "ms3-pedidos" }));

const PORT = process.env.PORT || 8083;
app.listen(PORT, () => console.log(`MS3 pedidos escuchando en puerto ${PORT}`));
