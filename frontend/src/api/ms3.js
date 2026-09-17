import client from "./client";

export const createOrder = (data) => client.post("/ms3/api/v1/orders", data).then((r) => r.data);
export const listOrders = (params) => client.get("/ms3/api/v1/orders", { params }).then((r) => r.data);
export const getOrder = (id) => client.get(`/ms3/api/v1/orders/${id}`).then((r) => r.data);
export const listAvailableOrders = () => client.get("/ms3/api/v1/orders/available").then((r) => r.data);
export const sendOrder = (id) => client.put(`/ms3/api/v1/orders/${id}/status`).then((r) => r.data);
export const claimOrder = (id) => client.put(`/ms3/api/v1/orders/${id}/claim`).then((r) => r.data);
export const deliverOrder = (id) => client.put(`/ms3/api/v1/orders/${id}/deliver`).then((r) => r.data);
export const restaurantCustomers = (restaurantId) =>
  client.get(`/ms3/api/v1/restaurants/${restaurantId}/customers`).then((r) => r.data);
