const express = require("express");

const ms1Client = require("../clients/ms1Client");
const orderModel = require("../models/order");
const { envelope, parsePaging } = require("../utils/paging");

const router = express.Router();

// GET /api/v1/restaurants/:restaurantId/customers
// Sin page/page_size devuelve todos los clientes (array); con ellos, respuesta paginada
// (se pagina en SQL y solo se le piden a MS1 los clientes de esa página).
router.get("/restaurants/:restaurantId/customers", async (req, res) => {
  const { restaurantId } = req.params;
  const paging = parsePaging(req.query);
  if (paging && paging.error) return res.status(400).json({ error: paging.error });

  if (!paging) {
    const customerIds = await orderModel.distinctCustomerIds(restaurantId);
    res.set("X-Total-Count", String(customerIds.length));
    if (customerIds.length === 0) return res.json([]);
    try {
      return res.json(await ms1Client.getUsersByIds(customerIds));
    } catch (err) {
      return res.status(502).json({ error: "MS1 no disponible al resolver clientes" });
    }
  }

  const [customerIds, total] = await Promise.all([
    orderModel.distinctCustomerIds(restaurantId, paging),
    orderModel.countDistinctCustomers(restaurantId),
  ]);
  res.set("X-Total-Count", String(total));
  try {
    const customers = customerIds.length ? await ms1Client.getUsersByIds(customerIds) : [];
    res.json(envelope(customers, total, paging));
  } catch (err) {
    res.status(502).json({ error: "MS1 no disponible al resolver clientes" });
  }
});

module.exports = router;
