import client from "./client";

export const register = (data) => client.post("/ms1/api/v1/auth/register", data).then((r) => r.data);
export const login = (data) => client.post("/ms1/api/v1/auth/login", data).then((r) => r.data);
export const getUser = (id) => client.get(`/ms1/api/v1/users/${id}`).then((r) => r.data);
export const listAddresses = (userId) => client.get(`/ms1/api/v1/users/${userId}/addresses`).then((r) => r.data);
export const createAddress = (userId, data) =>
  client.post(`/ms1/api/v1/users/${userId}/addresses`, data).then((r) => r.data);
