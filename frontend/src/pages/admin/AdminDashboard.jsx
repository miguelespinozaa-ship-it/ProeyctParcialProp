import { useCallback, useEffect, useState } from "react";
import { adminSummary } from "../../api/ms4";
import { sendOrder } from "../../api/ms3";
import { useAuth } from "../../auth/AuthContext";
import NavBar from "../../components/NavBar";
import Pagination from "../../components/Pagination";

const ESTADOS = ["PEDIDO", "ENVIADO", "ENTREGADO"];
const PAGE_SIZE = 10;

export default function AdminDashboard() {
  const { auth } = useAuth();
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");
  const [estado, setEstado] = useState("PEDIDO");
  const [page, setPage] = useState(1);
  const [customersPage, setCustomersPage] = useState(1);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(() => {
    setRefreshing(true);
    adminSummary(auth.restauranteId, {
      status: estado,
      page,
      page_size: PAGE_SIZE,
      customers_page: customersPage,
    })
      .then((data) => {
        setSummary(data);
        setError("");
      })
      .catch(() => setError("No se pudo cargar el dashboard"))
      .finally(() => setRefreshing(false));
  }, [auth.restauranteId, estado, page, customersPage]);

  useEffect(() => {
    load();
  }, [load]);

  const changeEstado = (nuevo) => {
    setEstado(nuevo);
    setPage(1);
  };

  const handleSend = async (orderId) => {
    setError("");
    try {
      await sendOrder(orderId);
      load();
    } catch (err) {
      setError(err.response?.data?.error || "No se pudo enviar el pedido");
    }
  };

  if (error && !summary) return <p className="error">{error}</p>;
  if (!summary) return <p className="loading">Cargando...</p>;

  const { pedidos, clientes, resumen } = summary;

  return (
    <div>
      <NavBar />
      <main className="container">
        <h1>{summary.restaurante.nombre}</h1>
        <p>{summary.restaurante.direccion}</p>
        {error && <p className="error">{error}</p>}

        <div className="tabs">
          {ESTADOS.map((e) => (
            <button key={e} className={e === estado ? "active" : ""} onClick={() => changeEstado(e)}>
              {e} ({resumen[e].toLocaleString("es-PE")})
            </button>
          ))}
        </div>

        <ul className="order-list">
          {pedidos.items.map((o) => (
            <li key={o.id}>
              #{o.id} — S/ {o.total} — {o.direccion_entrega}
              {summary.estado === "PEDIDO" && <button onClick={() => handleSend(o.id)}>Enviar</button>}
            </li>
          ))}
          {pedidos.items.length === 0 && <p>Sin pedidos en este estado.</p>}
        </ul>
        <Pagination
          page={pedidos.page}
          totalPages={pedidos.total_pages}
          total={pedidos.total}
          onChange={setPage}
          disabled={refreshing}
        />

        <h2>Clientes</h2>
        {clientes ? (
          <>
            <ul>
              {clientes.items.map((c) => (
                <li key={c.id}>
                  {c.nombre} — {c.email}
                </li>
              ))}
            </ul>
            <Pagination
              page={clientes.page}
              totalPages={clientes.total_pages}
              total={clientes.total}
              onChange={setCustomersPage}
              disabled={refreshing}
            />
          </>
        ) : (
          <p>No se pudieron cargar los clientes.</p>
        )}
      </main>
    </div>
  );
}
