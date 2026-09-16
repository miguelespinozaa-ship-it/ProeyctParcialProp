const express = require("express");

const pool = require("../db");
const ms2Client = require("../clients/ms2Client");
const { authenticate, requireRole } = require("../middleware/auth");
const orderItemModel = require("../models/orderItem");
const orderModel = require("../models/order");

const router = express.Router();

router.use(authenticate);

// POST /api/v1/orders — crea pedido, valida cada dish_id/precio contra MS2
router.post("/orders", requireRole("customer"), async (req, res) => {
  const { restaurant_id: restaurantId, direccion_entrega: direccionEntrega, items } = req.body;

  if (!restaurantId || !direccionEntrega || !Array.isArray(items) || items.length === 0) {
    return res.status(400).json({ error: "restaurant_id, direccion_entrega e items son requeridos" });
  }

  const resolvedItems = [];
  for (const item of items) {
    let dish;
    try {
      dish = await ms2Client.getDish(restaurantId, item.dish_id);
    } catch (err) {
      if (err.response && err.response.status === 404) {
        return res.status(400).json({ error: `Plato ${item.dish_id} no existe en el restaurante ${restaurantId}` });
      }
      return res.status(502).json({ error: "MS2 no disponible al validar el pedido" });
    }
    if (!dish.disponible) {
      return res.status(400).json({ error: `Plato ${item.dish_id} no está disponible` });
    }
    resolvedItems.push({
      dishId: dish.id,
      nombrePlato: dish.nombre,
      cantidad: item.cantidad,
      precioUnitario: dish.precio,
    });
  }

  const total = resolvedItems.reduce((sum, it) => sum + it.precioUnitario * it.cantidad, 0);

  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    const order = await orderModel.create(
      { customerId: req.user.id, restaurantId, direccionEntrega, total },
      client
    );
    const orderItems = await orderItemModel.createMany(order.id, resolvedItems, client);
    await client.query("COMMIT");
    res.status(201).json({ ...order, items: orderItems });
  } catch (err) {
    await client.query("ROLLBACK");
    res.status(500).json({ error: "Error al crear el pedido" });
  } finally {
    client.release();
  }
});

// GET /api/v1/orders/available — pedidos ENVIADO con delivery_id null (para "jalar")
router.get("/orders/available", requireRole("delivery"), async (req, res) => {
  const orders = await orderModel.findAvailable();
  res.json(orders);
});

// GET /api/v1/orders/:orderId — detalle + items
router.get("/orders/:orderId", async (req, res) => {
  const order = await orderModel.findById(req.params.orderId);
  if (!order) return res.status(404).json({ error: "Pedido no encontrado" });
  const items = await orderItemModel.findByOrderId(order.id);
  res.json({ ...order, items });
});

// GET /api/v1/orders — filtros ?customer_id= / ?restaurant_id=&status= / ?delivery_id=
// Nota: sin auth obligatoria, igual que GET /users en MS1 — lo consume MS4 internamente.
router.get("/orders", async (req, res) => {
  const { customer_id: customerId, restaurant_id: restaurantId, delivery_id: deliveryId, status } = req.query;
  const orders = await orderModel.findByFilters({ customerId, restaurantId, deliveryId, status });
  res.json(orders);
});

// PUT /api/v1/orders/:orderId/status — PEDIDO -> ENVIADO, solo admin dueño del restaurante
router.put("/orders/:orderId/status", requireRole("admin"), async (req, res) => {
  const order = await orderModel.findById(req.params.orderId);
  if (!order) return res.status(404).json({ error: "Pedido no encontrado" });
  if (order.restaurant_id !== req.user.restauranteId) {
    return res.status(403).json({ error: "No autorizado para este restaurante" });
  }
  if (order.status !== "PEDIDO") {
    return res.status(400).json({ error: `No se puede pasar de ${order.status} a ENVIADO` });
  }
  const updated = await orderModel.updateStatus(order.id, "ENVIADO");
  res.json(updated);
});

// PUT /api/v1/orders/:orderId/claim — asigna delivery_id (requiere status=ENVIADO y delivery_id null)
router.put("/orders/:orderId/claim", requireRole("delivery"), async (req, res) => {
  const claimed = await orderModel.claim(req.params.orderId, req.user.id);
  if (!claimed) {
    return res.status(409).json({ error: "Pedido no disponible para jalar (ya asignado o no está ENVIADO)" });
  }
  res.json(claimed);
});

// PUT /api/v1/orders/:orderId/deliver — ENVIADO -> ENTREGADO (requiere delivery_id == self)
router.put("/orders/:orderId/deliver", requireRole("delivery"), async (req, res) => {
  const delivered = await orderModel.deliver(req.params.orderId, req.user.id);
  if (!delivered) {
    return res.status(409).json({ error: "No se puede marcar como entregado (no asignado a vos o no está ENVIADO)" });
  }
  res.json(delivered);
});

module.exports = router;
