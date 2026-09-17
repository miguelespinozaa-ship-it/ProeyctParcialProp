import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { createOrder } from "../../api/ms3";
import { getRestaurant } from "../../api/ms2";
import NavBar from "../../components/NavBar";

export default function RestaurantMenu() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [restaurant, setRestaurant] = useState(null);
  const [cart, setCart] = useState({});
  const [direccion, setDireccion] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    getRestaurant(id).then(setRestaurant);
  }, [id]);

  const addToCart = (dishId) => setCart((c) => ({ ...c, [dishId]: (c[dishId] || 0) + 1 }));
  const removeFromCart = (dishId) =>
    setCart((c) => {
      const next = { ...c };
      if (next[dishId] > 1) next[dishId] -= 1;
      else delete next[dishId];
      return next;
    });

  const items = restaurant
    ? Object.entries(cart).map(([dishId, cantidad]) => ({
        dish: restaurant.platos.find((p) => p.id === dishId),
        cantidad,
      }))
    : [];
  const total = items.reduce((sum, it) => sum + it.dish.precio * it.cantidad, 0);

  const handleOrder = async () => {
    setError("");
    if (items.length === 0) return setError("El carrito está vacío");
    if (!direccion) return setError("Ingresá una dirección de entrega");
    setSubmitting(true);
    try {
      const order = await createOrder({
        restaurant_id: id,
        direccion_entrega: direccion,
        items: items.map((it) => ({ dish_id: it.dish.id, cantidad: it.cantidad })),
      });
      navigate(`/customer/orders/${order.id}`);
    } catch (err) {
      setError(err.response?.data?.error || "No se pudo crear el pedido");
    } finally {
      setSubmitting(false);
    }
  };

  if (!restaurant) return <p className="loading">Cargando...</p>;

  return (
    <div>
      <NavBar />
      <main className="container menu-layout">
        <div>
          <h1>{restaurant.nombre}</h1>
          <p>{restaurant.direccion}</p>

          <div className="menu-grid">
            {restaurant.platos.map((p) => (
              <div key={p.id} className="dish-card">
                <h3>{p.nombre}</h3>
                <p>{p.descripcion}</p>
                <p className="price">S/ {p.precio.toFixed(2)}</p>
                {!p.disponible && <p className="badge">No disponible</p>}
                <div className="qty-control">
                  <button onClick={() => removeFromCart(p.id)} disabled={!cart[p.id]}>
                    -
                  </button>
                  <span>{cart[p.id] || 0}</span>
                  <button onClick={() => addToCart(p.id)} disabled={!p.disponible}>
                    +
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <aside className="cart">
          <h2>Carrito</h2>
          {items.length === 0 && <p>Vacío</p>}
          {items.map((it) => (
            <p key={it.dish.id}>
              {it.cantidad}x {it.dish.nombre} — S/ {(it.dish.precio * it.cantidad).toFixed(2)}
            </p>
          ))}
          <p className="total">Total: S/ {total.toFixed(2)}</p>
          <input
            placeholder="Dirección de entrega"
            value={direccion}
            onChange={(e) => setDireccion(e.target.value)}
          />
          {error && <p className="error">{error}</p>}
          <button onClick={handleOrder} disabled={submitting}>
            {submitting ? "Enviando..." : "Hacer pedido"}
          </button>
        </aside>
      </main>
    </div>
  );
}
