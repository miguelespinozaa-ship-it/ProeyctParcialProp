import { useCallback, useEffect, useState } from "react";
import { claimOrder, deliverOrder } from "../../api/ms3";
import { deliverySummary } from "../../api/ms4";
import { useAuth } from "../../auth/AuthContext";
import NavBar from "../../components/NavBar";
import Pagination from "../../components/Pagination";

const PAGE_SIZE = 10;

export default function DeliveryDashboard() {
  const { auth } = useAuth();
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [cursoPage, setCursoPage] = useState(1);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(() => {
    setRefreshing(true);
    deliverySummary(auth.userId, { page, page_size: PAGE_SIZE, curso_page: cursoPage })
      .then((data) => {
        setSummary(data);
        setError("");
      })
      .catch(() => setError("No se pudo cargar el dashboard"))
      .finally(() => setRefreshing(false));
  }, [auth.userId, page, cursoPage]);

  useEffect(() => {
    load();
  }, [load]);

  const handleClaim = async (orderId) => {
    setError("");
    try {
      await claimOrder(orderId);
      load();
    } catch {
      setError("No se pudo jalar el pedido (puede que ya lo haya tomado otro repartidor)");
    }
  };

  const handleDeliver = async (orderId) => {
    await deliverOrder(orderId);
    load();
  };

  if (!summary) return error ? <p className="error">{error}</p> : <p className="loading">Cargando...</p>;

  const { disponibles, en_curso: enCurso } = summary;

  return (
    <div>
      <NavBar />
      <main className="container">
        <h1>Panel de repartidor</h1>
        {error && <p className="error">{error}</p>}

        <h2>Disponibles para jalar ({disponibles.total.toLocaleString("es-PE")})</h2>
        <ul className="order-list">
          {disponibles.items.map((o) => (
            <li key={o.id}>
              #{o.id} — {o.restaurante?.nombre} — {o.direccion_entrega} — S/ {o.total}
              <button onClick={() => handleClaim(o.id)}>Jalar</button>
            </li>
          ))}
          {disponibles.total === 0 && <p>No hay pedidos disponibles ahora.</p>}
        </ul>
        <Pagination
          page={disponibles.page}
          totalPages={disponibles.total_pages}
          total={disponibles.total}
          onChange={setPage}
          disabled={refreshing}
        />

        <h2>Mis entregas en curso ({enCurso.total})</h2>
        <ul className="order-list">
          {enCurso.items.map((o) => (
            <li key={o.id}>
              #{o.id} — {o.restaurante?.nombre} — {o.direccion_entrega}
              <button onClick={() => handleDeliver(o.id)}>Marcar entregado</button>
            </li>
          ))}
          {enCurso.total === 0 && <p>No tenés entregas en curso.</p>}
        </ul>
        <Pagination
          page={enCurso.page}
          totalPages={enCurso.total_pages}
          total={enCurso.total}
          onChange={setCursoPage}
          disabled={refreshing}
        />
      </main>
    </div>
  );
}
