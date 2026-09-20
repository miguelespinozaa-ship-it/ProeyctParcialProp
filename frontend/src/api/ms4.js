import client from "./client";

export const trackOrder = (orderId) => client.get(`/ms4/api/v1/tracking/order/${orderId}`).then((r) => r.data);

// Sin `params` devuelven el resumen completo (modo original). Con page/page_size (y status en admin)
// devuelven la versión paginada: solo la página pedida más los totales por estado.
export const customerSummary = (userId, params) =>
  client.get(`/ms4/api/v1/dashboard/customer/${userId}/summary`, { params }).then((r) => r.data);
export const deliverySummary = (deliveryId, params) =>
  client.get(`/ms4/api/v1/dashboard/delivery/${deliveryId}/summary`, { params }).then((r) => r.data);
export const adminSummary = (restaurantId, params) =>
  client.get(`/ms4/api/v1/dashboard/admin/${restaurantId}/summary`, { params }).then((r) => r.data);
