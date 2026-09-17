import { Navigate } from "react-router-dom";
import { useAuth } from "./AuthContext";

export default function ProtectedRoute({ rol, children }) {
  const { auth } = useAuth();
  if (!auth) return <Navigate to="/login" replace />;
  if (rol && auth.rol !== rol) return <Navigate to="/login" replace />;
  return children;
}
