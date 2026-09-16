// MS2 — Catálogo de Restaurantes (MongoDB). Seed manual mínimo (Fase 3): 2 restaurantes con platos.
db = db.getSiblingDB("ms2_catalogo");

db.restaurantes.insertMany([
  {
    nombre: "Sabor Criollo",
    categoria: "Comida Peruana",
    ciudad: "Lima",
    direccion: "Av. Siempre Viva 123",
    admin_id: 1,
    calificacion_promedio: 4.5,
    platos: [
      { id: "p1", nombre: "Lomo Saltado", descripcion: "Clásico plato peruano", precio: 25.9, categoria: "Fondos", disponible: true },
      { id: "p2", nombre: "Ají de Gallina", descripcion: "Cremoso y picante", precio: 22.5, categoria: "Fondos", disponible: true },
    ],
    resenas: [],
  },
  {
    nombre: "Pizza Bella",
    categoria: "Italiana",
    ciudad: "Lima",
    direccion: "Jr. Las Flores 456",
    admin_id: 2,
    calificacion_promedio: 4.2,
    platos: [
      { id: "p3", nombre: "Pizza Margarita", descripcion: "Tomate, mozzarella y albahaca", precio: 32.0, categoria: "Pizzas", disponible: true },
    ],
    resenas: [],
  },
]);
