import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { createOrder } from "../../api/ms3";
import { createReview, getRestaurant } from "../../api/ms2";
import { useAuth } from "../../auth/AuthContext";
import NavBar from "../../components/NavBar";

export default function RestaurantMenu() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { auth } = useAuth();
  const [restaurant, setRestaurant] = useState(null);
  const [cart, setCart] = useState({});
  const [direccion, setDireccion] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [puntuacion, setPuntuacion] = useState(5);
  const [comentario, setComentario] = useState("");
  const [reviewError, setReviewError] = useState("");
  const [sendingReview, setSendingReview] = useState(false);

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

  const handleReview = async (e) => {
    e.preventDefault();
    setReviewError("");
    if (!comentario.trim()) return setReviewError("Escribí un comentario");
    setSendingReview(true);
    try {
      await createReview(id, { usuario_id: auth.userId, puntuacion, comentario: comentario.trim() });
      setComentario("");
      setPuntuacion(5);
      setRestaurant(await getRestaurant(id));
    } catch (err) {
      setReviewError(err.response?.data?.message || "No se pudo guardar la reseña");
    } finally {
      setSendingReview(false);
    }
  };

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

          <section className="reviews">
            <h2>
              Reseñas — ⭐ {Number(restaurant.calificacion_promedio || 0).toFixed(1)} ({restaurant.resenas.length})
            </h2>
            {restaurant.resenas.length === 0 && <p>Todavía no hay reseñas. ¡Sé el primero!</p>}
            <ul className="review-list">
              {[...restaurant.resenas]
                .sort((a, b) => new Date(b.fecha) - new Date(a.fecha))
                .slice(0, 10)
                .map((r, i) => (
                  <li key={i}>
                    <div className="review-head">
                      <span className="stars">{"★".repeat(r.puntuacion)}{"☆".repeat(5 - r.puntuacion)}</span>
                      <span>
                        {r.usuario_id === auth.userId ? "Tú" : `Usuario #${r.usuario_id}`} ·{" "}
                        {r.fecha ? new Date(r.fecha).toLocaleDateString("es-PE") : ""}
                      </span>
                    </div>
                    <p>{r.comentario}</p>
                  </li>
                ))}
            </ul>

            <form className="review-form" onSubmit={handleReview}>
              <h3>Dejá tu reseña</h3>
              <label>
                Puntuación{" "}
                <select value={puntuacion} onChange={(e) => setPuntuacion(Number(e.target.value))}>
                  {[5, 4, 3, 2, 1].map((n) => (
                    <option key={n} value={n}>
                      {n} {n === 1 ? "estrella" : "estrellas"}
                    </option>
                  ))}
                </select>
              </label>
              <textarea
                placeholder="Contá tu experiencia"
                value={comentario}
                onChange={(e) => setComentario(e.target.value)}
                maxLength={300}
              />
              {reviewError && <p className="error">{reviewError}</p>}
              <button type="submit" disabled={sendingReview}>
                {sendingReview ? "Enviando..." : "Publicar reseña"}
              </button>
            </form>
          </section>
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
