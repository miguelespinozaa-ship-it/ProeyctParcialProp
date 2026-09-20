import client from "./client";

export const topRestaurants = () => client.get("/ms5/api/v1/analytics/top-restaurants").then((r) => r.data);
// Con { page, page_size } devuelve solo esa página (data + page/total/total_pages).
export const userMetrics = (params) =>
  client.get("/ms5/api/v1/analytics/user-metrics", { params }).then((r) => r.data);
