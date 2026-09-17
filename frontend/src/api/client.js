import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost";

const client = axios.create({ baseURL: BASE_URL });

client.interceptors.request.use((config) => {
  const raw = localStorage.getItem("auth");
  if (raw) {
    const { token } = JSON.parse(raw);
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default client;
