import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listRestaurants } from "../../api/ms2";
import { listOrders } from "../../api/ms3";
import { useAuth } from "../../auth/AuthContext";
import NavBar from "../../components/NavBar";

export default function CustomerHome() {
  const { auth } = useAuth();
  const [restaurants, setRestaurants] = useState([]);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([listRestaurants(), listOrders({ customer_id: auth.userId })])
      .then(([r, o]) => {
        setRestaurants(r);
        setOrders(o);
      })
      .finally(() => setLoading(false));
  }, [auth.userId]);

  if (loading) return <p className="loading">Cargando...</p>;

  return (
    <div>
      <NavBar />
      <main className="container">
        <h1>Restaurantes</h1>
        <div className="grid">
          {restaurants.map((r) => (
            <Link key={r.id} to={`/customer/restaurants/${r.id}`} className="card">
              <h3>{r.nombre}</h3>
              <p>
                {r.categoria} · {r.ciudad}
              </p>
              <p>⭐ {r.calificacion_promedio}</p>
            </Link>
          ))}
        </div>

        <h2>Mis pedidos</h2>
        <ul className="order-list">
          {orders.map((o) => (
            <li key={o.id}>
              <Link to={`/customer/orders/${o.id}`}>
                Pedido #{o.id} — <span className={`status status-${o.status}`}>{o.status}</span> — S/ {o.total}
              </Link>
            </li>
          ))}
          {orders.length === 0 && <p>Todavía no hiciste ningún pedido.</p>}
        </ul>
      </main>
    </div>
  );
}
