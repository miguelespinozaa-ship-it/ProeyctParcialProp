import { mensajeError } from "../api/errores";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { login as loginApi } from "../api/ms1";
import { useAuth } from "../auth/AuthContext";
import { decodeJwt } from "../utils/jwt";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const data = await loginApi({ email, password });
      const payload = decodeJwt(data.access_token);
      login({
        token: data.access_token,
        rol: data.rol,
        restauranteId: data.restaurante_id,
        userId: Number(payload?.sub),
      });
      if (data.rol === "admin") navigate("/admin");
      else if (data.rol === "delivery") navigate("/delivery");
      else navigate("/customer");
    } catch (err) {
      setError(mensajeError(err, "Credenciales inválidas"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <form onSubmit={handleSubmit} className="auth-form">
        <h1>Iniciar sesión</h1>
        {error && <p className="error">{error}</p>}
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Contraseña"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button type="submit" disabled={submitting}>
          {submitting ? "Entrando..." : "Entrar"}
        </button>
        <p>
          ¿No tenés cuenta? <Link to="/register">Registrate</Link>
        </p>
      </form>
    </div>
  );
}
