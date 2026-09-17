import { useEffect, useState } from "react";
import { topRestaurants, userMetrics } from "../../api/ms5";
import NavBar from "../../components/NavBar";

export default function AdminAnalytics() {
  const [restaurants, setRestaurants] = useState([]);
  const [users, setUsers] = useState([]);

  useEffect(() => {
    topRestaurants().then((r) => setRestaurants(r.data));
    userMetrics().then((r) => setUsers(r.data));
  }, []);

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
                <td>S/ {r.total_ventas}</td>
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
            {users.map((u) => (
              <tr key={u.usuario_id}>
                <td>{u.nombre}</td>
                <td>{u.num_pedidos}</td>
                <td>S/ {u.gasto_promedio}</td>
                <td>{u.antiguedad_cuenta}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </main>
    </div>
  );
}
