const axios = require("axios");

const MS1_BASE_URL = process.env.MS1_BASE_URL || "http://localhost:8081";

async function getUsersByIds(ids) {
  const { data } = await axios.get(`${MS1_BASE_URL}/api/v1/users`, {
    params: { rol: "customer", ids: ids.join(",") },
    timeout: 5000,
  });
  return data;
}

module.exports = { getUsersByIds };
