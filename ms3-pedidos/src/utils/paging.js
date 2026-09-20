const DEFAULT_PAGE_SIZE = 20;
const MAX_PAGE_SIZE = 100;

// Paginado opcional: sin `page` ni `page_size` devuelve null y el endpoint responde como siempre (todo).
// Con cualquiera de los dos devuelve { page, pageSize, limit, offset } o { error } si son inválidos.
// page_size se limita a MAX_PAGE_SIZE (la respuesta informa el tamaño realmente aplicado).
function parsePaging(query) {
  if (query.page === undefined && query.page_size === undefined) return null;

  const page = query.page === undefined ? 1 : Number(query.page);
  const requested = query.page_size === undefined ? DEFAULT_PAGE_SIZE : Number(query.page_size);

  if (!Number.isInteger(page) || page < 1) return { error: "page debe ser un entero >= 1" };
  if (!Number.isInteger(requested) || requested < 1) return { error: "page_size debe ser un entero >= 1" };

  const pageSize = Math.min(requested, MAX_PAGE_SIZE);
  return { page, pageSize, limit: pageSize, offset: (page - 1) * pageSize };
}

function envelope(items, total, paging) {
  return {
    items,
    page: paging.page,
    page_size: paging.pageSize,
    total,
    total_pages: Math.ceil(total / paging.pageSize),
  };
}

module.exports = { parsePaging, envelope, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE };
