import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register as registerApi } from "../api/ms1";
import { useAuth } from "../auth/AuthContext";

export default function Register() {
  const [form, setForm] = useState({ nombre: "", email: "", password: "", telefono: "", rol: "customer" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const data = await registerApi(form);
      login({ token: data.token, rol: data.rol, userId: data.id });
      navigate(data.rol === "delivery" ? "/delivery" : "/customer");
    } catch (err) {
      setError(err.response?.data?.detail || "No se pudo crear la cuenta");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <form onSubmit={handleSubmit} className="auth-form">
        <h1>Crear cuenta</h1>
        {error && <p className="error">{error}</p>}
        <input name="nombre" placeholder="Nombre" value={form.nombre} onChange={handleChange} required />
        <input name="email" type="email" placeholder="Email" value={form.email} onChange={handleChange} required />
        <input
          name="password"
          type="password"
          placeholder="Contraseña"
          value={form.password}
          onChange={handleChange}
          required
        />
        <input name="telefono" placeholder="Teléfono" value={form.telefono} onChange={handleChange} />
        <select name="rol" value={form.rol} onChange={handleChange}>
          <option value="customer">Customer</option>
          <option value="delivery">Delivery</option>
        </select>
        <button type="submit" disabled={submitting}>
          {submitting ? "Creando..." : "Registrarme"}
        </button>
        <p>
          ¿Ya tenés cuenta? <Link to="/login">Iniciar sesión</Link>
        </p>
      </form>
    </div>
  );
}
