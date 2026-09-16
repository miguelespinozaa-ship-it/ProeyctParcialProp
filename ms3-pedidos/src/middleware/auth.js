const jwt = require("jsonwebtoken");

const JWT_SECRET = process.env.JWT_SECRET || "change-me-in-prod-use-a-long-random-secret-32-bytes-min";

// Igual que en MS1/MS2: valida el Bearer token si viene, pero no rechaza requests sin token.
// Cada ruta decide si exige autenticación (requireAuth / requireRole).
function authenticate(req, res, next) {
  const header = req.headers.authorization;
  if (header && header.startsWith("Bearer ")) {
    try {
      const decoded = jwt.verify(header.slice(7), JWT_SECRET, { algorithms: ["HS256"] });
      req.user = {
        id: parseInt(decoded.sub, 10),
        rol: decoded.rol,
        restauranteId: decoded.restaurante_id || null,
      };
    } catch (err) {
      // token inválido/expirado: sigue sin autenticar
    }
  }
  next();
}

function requireAuth(req, res, next) {
  if (!req.user) {
    return res.status(401).json({ error: "Falta token de autenticación" });
  }
  next();
}

function requireRole(...roles) {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({ error: "Falta token de autenticación" });
    }
    if (!roles.includes(req.user.rol)) {
      return res.status(403).json({ error: "No autorizado" });
    }
    next();
  };
}

module.exports = { authenticate, requireAuth, requireRole };
