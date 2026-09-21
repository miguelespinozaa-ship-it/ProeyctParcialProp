import client from "./client";

export const listRestaurants = (params) => client.get("/ms2/api/v1/restaurants", { params }).then((r) => r.data);
export const getRestaurant = (id) => client.get(`/ms2/api/v1/restaurants/${id}`).then((r) => r.data);
export const getMenu = (restaurantId) => client.get(`/ms2/api/v1/restaurants/${restaurantId}/menu`).then((r) => r.data);
export const createDish = (restaurantId, data) =>
  client.post(`/ms2/api/v1/restaurants/${restaurantId}/menu`, data).then((r) => r.data);
export const updateDish = (restaurantId, dishId, data) =>
  client.put(`/ms2/api/v1/restaurants/${restaurantId}/menu/${dishId}`, data).then((r) => r.data);
export const toggleDish = (restaurantId, dishId) =>
  client.patch(`/ms2/api/v1/restaurants/${restaurantId}/menu/${dishId}/disponibilidad`).then((r) => r.data);
export const deleteDish = (restaurantId, dishId) =>
  client.delete(`/ms2/api/v1/restaurants/${restaurantId}/menu/${dishId}`).then((r) => r.data);
export const listReviews = (restaurantId) =>
  client.get(`/ms2/api/v1/restaurants/${restaurantId}/reviews`).then((r) => r.data);
export const createReview = (restaurantId, data) =>
  client.post(`/ms2/api/v1/restaurants/${restaurantId}/reviews`, data).then((r) => r.data);
