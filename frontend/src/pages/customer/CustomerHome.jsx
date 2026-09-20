import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listRestaurants } from "../../api/ms2";
import { listOrders } from "../../api/ms3";
import { useAuth } from "../../auth/AuthContext";
import NavBar from "../../components/NavBar";
import Pagination from "../../components/Pagination";

const ORDERS_PAGE_SIZE = 5;

export default function CustomerHome() {
  const { auth } = useAuth();
  const [restaurants, setRestaurants] = useState(null);
  const [orders, setOrders] = useState(null);
  const [ordersPage, setOrdersPage] = useState(1);

  useEffect(() => {
    listRestaurants().then(setRestaurants);
  }, []);

  useEffect(() => {
    listOrders({ customer_id: auth.userId, page: ordersPage, page_size: ORDERS_PAGE_SIZE }).then(setOrders);
  }, [auth.userId, ordersPage]);

  if (!restaurants || !orders) return <p className="loading">Cargando...</p>;

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
          {orders.items.map((o) => (
            <li key={o.id}>
              <Link to={`/customer/orders/${o.id}`}>
                Pedido #{o.id} — <span className={`status status-${o.status}`}>{o.status}</span> — S/ {o.total}
              </Link>
            </li>
          ))}
          {orders.total === 0 && <p>Todavía no hiciste ningún pedido.</p>}
        </ul>
        <Pagination page={orders.page} totalPages={orders.total_pages} total={orders.total} onChange={setOrdersPage} />
      </main>
    </div>
  );
}
