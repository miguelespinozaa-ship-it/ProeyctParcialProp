import { useCallback, useEffect, useState } from "react";
import { adminSummary } from "../../api/ms4";
import { sendOrder } from "../../api/ms3";
import { useAuth } from "../../auth/AuthContext";
import NavBar from "../../components/NavBar";

export default function AdminDashboard() {
  const { auth } = useAuth();
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    adminSummary(auth.restauranteId)
      .then(setSummary)
      .catch(() => setError("No se pudo cargar el dashboard"));
  }, [auth.restauranteId]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSend = async (orderId) => {
    await sendOrder(orderId);
    load();
  };

  if (error) return <p className="error">{error}</p>;
  if (!summary) return <p className="loading">Cargando...</p>;

  return (
    <div>
      <NavBar />
      <main className="container">
        <h1>{summary.restaurante.nombre}</h1>
        <p>{summary.restaurante.direccion}</p>

        {["PEDIDO", "ENVIADO", "ENTREGADO"].map((status) => (
          <section key={status}>
            <h2>
              {status} ({summary.pedidos_por_estado[status]?.length || 0})
            </h2>
            <ul className="order-list">
              {(summary.pedidos_por_estado[status] || []).map((o) => (
                <li key={o.id}>
                  #{o.id} — S/ {o.total} — {o.direccion_entrega}
                  {status === "PEDIDO" && <button onClick={() => handleSend(o.id)}>Enviar</button>}
                </li>
              ))}
              {(summary.pedidos_por_estado[status] || []).length === 0 && <p>Sin pedidos en este estado.</p>}
            </ul>
          </section>
        ))}

        <h2>Clientes</h2>
        <ul>
          {summary.clientes.map((c) => (
            <li key={c.id}>
              {c.nombre} — {c.email}
            </li>
          ))}
        </ul>
      </main>
    </div>
  );
}
