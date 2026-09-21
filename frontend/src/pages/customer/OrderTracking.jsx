import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { trackOrder } from "../../api/ms4";
import NavBar from "../../components/NavBar";

export default function OrderTracking() {
  const { id } = useParams();
  const [tracking, setTracking] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    trackOrder(id)
      .then(setTracking)
      .catch(() => setError("No se pudo cargar el tracking"));
  }, [id]);

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, [load]);

  if (error) return <p className="error">{error}</p>;
  if (!tracking) return <p className="loading">Cargando...</p>;

  return (
    <div>
      <NavBar />
      <main className="container">
        <h1>Pedido #{tracking.order_id}</h1>
        <p className={`status status-${tracking.status}`}>{tracking.status}</p>

        <h3>Restaurante</h3>
        <p>
          {tracking.restaurante?.nombre} — {tracking.restaurante?.direccion}
        </p>

        <h3>Repartidor</h3>
        <p>{tracking.repartidor ? [tracking.repartidor.nombre, tracking.repartidor.telefono].filter(Boolean).join(" — ") : "Todavía no asignado"}</p>

        <h3>Items</h3>
        <ul>
          {tracking.items.map((it, i) => (
            <li key={i}>
              {it.cantidad}x {it.nombre_plato}
            </li>
          ))}
        </ul>
        <p className="total">Total: S/ {tracking.total}</p>
      </main>
    </div>
  );
}
