import { createContext, useContext, useState } from "react";

const AuthContext = createContext(null);

function loadStoredAuth() {
  const raw = localStorage.getItem("auth");
  return raw ? JSON.parse(raw) : null;
}

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState(loadStoredAuth);

  const login = (authData) => {
    localStorage.setItem("auth", JSON.stringify(authData));
    setAuth(authData);
  };

  const logout = () => {
    localStorage.removeItem("auth");
    setAuth(null);
  };

  return <AuthContext.Provider value={{ auth, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
