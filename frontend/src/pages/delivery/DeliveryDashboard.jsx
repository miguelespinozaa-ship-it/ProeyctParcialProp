import { useCallback, useEffect, useState } from "react";
import { claimOrder, deliverOrder } from "../../api/ms3";
import { deliverySummary } from "../../api/ms4";
import { useAuth } from "../../auth/AuthContext";
import NavBar from "../../components/NavBar";

export default function DeliveryDashboard() {
  const { auth } = useAuth();
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    deliverySummary(auth.userId)
      .then(setSummary)
      .catch(() => setError("No se pudo cargar el dashboard"));
  }, [auth.userId]);

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

  if (!summary) return <p className="loading">Cargando...</p>;

  return (
    <div>
      <NavBar />
      <main className="container">
        <h1>Panel de repartidor</h1>
        {error && <p className="error">{error}</p>}

        <h2>Disponibles para jalar</h2>
        <ul className="order-list">
          {summary.disponibles.map((o) => (
            <li key={o.id}>
              #{o.id} — {o.restaurante?.nombre} — {o.direccion_entrega} — S/ {o.total}
              <button onClick={() => handleClaim(o.id)}>Jalar</button>
            </li>
          ))}
          {summary.disponibles.length === 0 && <p>No hay pedidos disponibles ahora.</p>}
        </ul>

        <h2>Mis entregas en curso</h2>
        <ul className="order-list">
          {summary.en_curso
            .filter((o) => o.status !== "ENTREGADO")
            .map((o) => (
              <li key={o.id}>
                #{o.id} — {o.restaurante?.nombre} — {o.direccion_entrega}
                <button onClick={() => handleDeliver(o.id)}>Marcar entregado</button>
              </li>
            ))}
        </ul>
      </main>
    </div>
  );
}
