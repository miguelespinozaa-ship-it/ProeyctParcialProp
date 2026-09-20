const axios = require("axios");

const MS1_BASE_URL = process.env.MS1_BASE_URL || "http://localhost:8081";

// Los ids viajan en la URL (?ids=1,2,3): con miles de ids supera el límite y MS1 responde 400/414.
// Se piden en lotes chicos, con un poco de paralelismo, y se concatenan los resultados.
const CHUNK_SIZE = 200;
const PARALLEL_CHUNKS = 5;

async function fetchChunk(ids) {
  const { data } = await axios.get(`${MS1_BASE_URL}/api/v1/users`, {
    params: { rol: "customer", ids: ids.join(",") },
    timeout: 5000,
  });
  return data;
}

async function getUsersByIds(ids) {
  const chunks = [];
  for (let i = 0; i < ids.length; i += CHUNK_SIZE) chunks.push(ids.slice(i, i + CHUNK_SIZE));

  const users = [];
  for (let i = 0; i < chunks.length; i += PARALLEL_CHUNKS) {
    const results = await Promise.all(chunks.slice(i, i + PARALLEL_CHUNKS).map(fetchChunk));
    for (const r of results) users.push(...r);
  }
  return users;
}

module.exports = { getUsersByIds };
