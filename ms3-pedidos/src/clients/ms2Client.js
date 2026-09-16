const axios = require("axios");

const MS2_BASE_URL = process.env.MS2_BASE_URL || "http://localhost:8082";

async function getDish(restaurantId, dishId) {
  const { data } = await axios.get(
    `${MS2_BASE_URL}/api/v1/restaurants/${restaurantId}/menu/${dishId}`,
    { timeout: 5000 }
  );
  return data;
}

module.exports = { getDish };
