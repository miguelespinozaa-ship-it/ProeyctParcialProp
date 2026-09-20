export default function Pagination({ page, totalPages, total, onChange, disabled = false }) {
  if (!total) return null;
  const pages = Math.max(totalPages || 1, 1);

  return (
    <div className="pagination">
      <button onClick={() => onChange(page - 1)} disabled={disabled || page <= 1}>
        Anterior
      </button>
      <span>
        Página {page} de {pages} · {total.toLocaleString("es-PE")} en total
      </span>
      <button onClick={() => onChange(page + 1)} disabled={disabled || page >= pages}>
        Siguiente
      </button>
    </div>
  );
}
