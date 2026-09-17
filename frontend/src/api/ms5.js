import client from "./client";

export const topRestaurants = () => client.get("/ms5/api/v1/analytics/top-restaurants").then((r) => r.data);
export const userMetrics = () => client.get("/ms5/api/v1/analytics/user-metrics").then((r) => r.data);
