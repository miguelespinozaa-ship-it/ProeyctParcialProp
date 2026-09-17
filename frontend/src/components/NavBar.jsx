import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function NavBar() {
  const { auth, logout } = useAuth();
  const home = auth?.rol === "admin" ? "/admin" : auth?.rol === "delivery" ? "/delivery" : "/customer";

  return (
    <nav className="navbar">
      <Link to={home} className="brand">
        Delivery Cloud
      </Link>
      <div className="navbar-right">
        {auth?.rol === "admin" && (
          <>
            <Link to="/admin/menu">Menú</Link>
            <Link to="/admin/analytics">Analítica</Link>
          </>
        )}
        <span className="rol-badge">{auth?.rol}</span>
        <button onClick={logout}>Salir</button>
      </div>
    </nav>
  );
}
