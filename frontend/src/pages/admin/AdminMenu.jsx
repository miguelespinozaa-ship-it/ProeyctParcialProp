import { useCallback, useEffect, useState } from "react";
import { createDish, deleteDish, getRestaurant, toggleDish } from "../../api/ms2";
import { useAuth } from "../../auth/AuthContext";
import NavBar from "../../components/NavBar";

export default function AdminMenu() {
  const { auth } = useAuth();
  const [restaurant, setRestaurant] = useState(null);
  const [form, setForm] = useState({ nombre: "", descripcion: "", precio: "", categoria: "" });
  const [error, setError] = useState("");

  const load = useCallback(() => {
    getRestaurant(auth.restauranteId).then(setRestaurant);
  }, [auth.restauranteId]);

  useEffect(() => {
    load();
  }, [load]);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleCreate = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await createDish(auth.restauranteId, { ...form, precio: parseFloat(form.precio), disponible: true });
      setForm({ nombre: "", descripcion: "", precio: "", categoria: "" });
      load();
    } catch {
      setError("No se pudo crear el platillo");
    }
  };

  const handleToggle = async (dishId) => {
    await toggleDish(auth.restauranteId, dishId);
    load();
  };

  const handleDelete = async (dishId) => {
    await deleteDish(auth.restauranteId, dishId);
    load();
  };

  if (!restaurant) return <p className="loading">Cargando...</p>;

  return (
    <div>
      <NavBar />
      <main className="container">
        <h1>Menú — {restaurant.nombre}</h1>

        <form onSubmit={handleCreate} className="dish-form">
          <input name="nombre" placeholder="Nombre" value={form.nombre} onChange={handleChange} required />
          <input name="descripcion" placeholder="Descripción" value={form.descripcion} onChange={handleChange} />
          <input
            name="precio"
            type="number"
            step="0.01"
            placeholder="Precio"
            value={form.precio}
            onChange={handleChange}
            required
          />
          <input name="categoria" placeholder="Categoría" value={form.categoria} onChange={handleChange} />
          <button type="submit">Agregar plato</button>
        </form>
        {error && <p className="error">{error}</p>}

        <ul className="dish-list">
          {restaurant.platos.map((p) => (
            <li key={p.id}>
              <strong>{p.nombre}</strong> — S/ {p.precio} — {p.disponible ? "Disponible" : "No disponible"}
              <button onClick={() => handleToggle(p.id)}>Toggle</button>
              <button onClick={() => handleDelete(p.id)}>Eliminar</button>
            </li>
          ))}
        </ul>
      </main>
    </div>
  );
}
