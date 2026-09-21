import { useEffect, useState } from "react";
import { topRestaurants, userMetrics } from "../../api/ms5";
import NavBar from "../../components/NavBar";
import Pagination from "../../components/Pagination";

const METRICS_PAGE_SIZE = 10;

const soles = (n) => `S/ ${Number(n).toLocaleString("es-PE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

export default function AdminAnalytics() {
  const [restaurants, setRestaurants] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [page, setPage] = useState(1);
  const [loadingPage, setLoadingPage] = useState(false);

  useEffect(() => {
    topRestaurants().then((r) => setRestaurants(r.data));
  }, []);

  useEffect(() => {
    setLoadingPage(true);
    userMetrics({ page, page_size: METRICS_PAGE_SIZE })
      .then(setMetrics)
      .finally(() => setLoadingPage(false));
  }, [page]);

  return (
    <div>
      <NavBar />
      <main className="container">
        <h1>Analítica</h1>

        <h2>Top restaurantes</h2>
        <table>
          <thead>
            <tr>
              <th>Restaurante</th>
              <th>Ventas</th>
              <th>Pedidos</th>
              <th>Calificación</th>
            </tr>
          </thead>
          <tbody>
            {restaurants.map((r) => (
              <tr key={r.restaurante_id}>
                <td>{r.nombre}</td>
                <td>{soles(r.total_ventas)}</td>
                <td>{r.num_pedidos}</td>
                <td>{r.calificacion_promedio}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <h2>Métricas de usuarios</h2>
        <table>
          <thead>
            <tr>
              <th>Usuario</th>
              <th>Pedidos</th>
              <th>Gasto promedio</th>
              <th>Antigüedad</th>
            </tr>
          </thead>
          <tbody>
            {(metrics?.data || []).map((u) => (
              <tr key={u.usuario_id}>
                <td>{u.nombre}</td>
                <td>{u.num_pedidos}</td>
                <td>{soles(u.gasto_promedio)}</td>
                <td>{u.antiguedad_cuenta}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!metrics && <p className="loading">Consultando Athena...</p>}
        {metrics && (
          <Pagination
            page={metrics.page}
            totalPages={metrics.total_pages}
            total={metrics.total}
            onChange={setPage}
            disabled={loadingPage}
          />
        )}
      </main>
    </div>
  );
}
