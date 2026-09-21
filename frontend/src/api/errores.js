// Mensaje para mostrar al usuario según el tipo de fallo: sin red / servidor caído / error de negocio.
export function mensajeError(err, porDefecto) {
  if (!err.response) return "No se pudo conectar con el servidor. Revisá tu conexión e intentá de nuevo en unos minutos.";
  if (err.response.status >= 500) return "El servidor no está disponible en este momento. Intentá de nuevo en unos minutos.";
  const detalle = err.response.data?.detail;
  return typeof detalle === "string" ? detalle : porDefecto;
}
