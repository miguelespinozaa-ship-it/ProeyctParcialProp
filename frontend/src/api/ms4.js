import client from "./client";

export const trackOrder = (orderId) => client.get(`/ms4/api/v1/tracking/order/${orderId}`).then((r) => r.data);
export const customerSummary = (userId) =>
  client.get(`/ms4/api/v1/dashboard/customer/${userId}/summary`).then((r) => r.data);
export const deliverySummary = (deliveryId) =>
  client.get(`/ms4/api/v1/dashboard/delivery/${deliveryId}/summary`).then((r) => r.data);
export const adminSummary = (restaurantId) =>
  client.get(`/ms4/api/v1/dashboard/admin/${restaurantId}/summary`).then((r) => r.data);
