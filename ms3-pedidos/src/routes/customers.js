const express = require("express");

const ms1Client = require("../clients/ms1Client");
const orderModel = require("../models/order");

const router = express.Router();

// GET /api/v1/restaurants/:restaurantId/customers
router.get("/restaurants/:restaurantId/customers", async (req, res) => {
  const customerIds = await orderModel.distinctCustomerIds(req.params.restaurantId);
  if (customerIds.length === 0) return res.json([]);
  try {
    const customers = await ms1Client.getUsersByIds(customerIds);
    res.json(customers);
  } catch (err) {
    res.status(502).json({ error: "MS1 no disponible al resolver clientes" });
  }
});

module.exports = router;
