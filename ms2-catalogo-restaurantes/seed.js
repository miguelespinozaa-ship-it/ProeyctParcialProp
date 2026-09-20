// Carga masiva de restaurantes (>= 20,000 documentos) - MS2 / MongoDB.
// Ejecutar UNA sola vez contra la base real:
//   docker cp ms2-catalogo-restaurantes/seed.js mongo:/tmp/seed.js && docker exec mongo mongosh --quiet --file /tmp/seed.js
// Conserva los 2 restaurantes del seed inicial (los usan el admin demo y los pedidos) y completa hasta TOTAL.
const TOTAL = 20000;
const BATCH = 1000;
const database = db.getSiblingDB("ms2_catalogo");
const col = database.restaurantes;

const existentes = col.countDocuments();
if (existentes >= TOTAL) {
  print(`Ya hay ${existentes} restaurantes (>= ${TOTAL}). No se inserta nada.`);
  quit(0);
}

const CIUDADES = ["Lima", "Arequipa", "Cusco", "Trujillo", "Chiclayo", "Piura", "Huancayo", "Iquitos", "Tacna", "Ica"];
const NOMBRES = ["Sabor", "Rincon", "Casa", "Fogon", "Mesa", "Sazon", "Antojo", "Patio", "Huerta", "Cocina"];
const ADJ = ["Criollo", "del Norte", "Andino", "Dorado", "Real", "Marino", "Fresco", "Tradicional", "Gourmet", "Familiar"];
const CALLES = ["Av. Grau", "Jr. Union", "Av. Arequipa", "Calle Los Pinos", "Av. Bolivar", "Jr. Cusco", "Av. Sol", "Calle Lima"];

const MENUS = {
  "Comida Peruana": [["Lomo Saltado", 25.9], ["Aji de Gallina", 22.5], ["Ceviche", 28.0], ["Arroz con Pollo", 19.5], ["Seco de Res", 24.0], ["Causa Limena", 16.0]],
  "Italiana": [["Pizza Margarita", 32.0], ["Lasagna", 29.5], ["Fettuccine Alfredo", 27.0], ["Ravioles", 30.0], ["Tiramisu", 14.0], ["Bruschetta", 12.5]],
  "Pollos y Parrillas": [["Pollo a la Brasa", 36.0], ["Anticuchos", 21.0], ["Parrillada", 55.0], ["Choripan", 11.0], ["Ensalada Fresca", 13.0], ["Papas Fritas", 9.0]],
  "Chifa": [["Arroz Chaufa", 20.0], ["Tallarin Saltado", 23.0], ["Wantan Frito", 15.0], ["Kam Lu Wantan", 26.0], ["Sopa Wantan", 17.0], ["Pollo Tipakay", 24.5]],
  "Hamburguesas": [["Hamburguesa Clasica", 18.0], ["Hamburguesa Doble", 26.0], ["Alitas BBQ", 22.0], ["Nuggets", 14.0], ["Papas Cheddar", 12.0], ["Malteada", 10.0]],
  "Sushi": [["Maki California", 28.0], ["Nigiri Salmon", 32.0], ["Sashimi Mixto", 45.0], ["Ramen", 30.0], ["Gyozas", 18.0], ["Roll Acevichado", 34.0]],
  "Vegetariana": [["Bowl de Quinoa", 21.0], ["Hamburguesa de Lentejas", 19.0], ["Ensalada Mediterranea", 17.0], ["Wrap Vegano", 16.0], ["Sopa de Verduras", 12.0], ["Jugo Verde", 9.0]],
  "Mexicana": [["Tacos al Pastor", 20.0], ["Burrito", 22.0], ["Quesadilla", 16.0], ["Nachos", 15.0], ["Enchiladas", 24.0], ["Guacamole", 12.0]],
  "Postres y Cafe": [["Cheesecake", 14.0], ["Brownie", 10.0], ["Cafe Americano", 7.0], ["Capuchino", 9.0], ["Torta de Chocolate", 13.0], ["Helado Artesanal", 11.0]],
  "Mariscos": [["Ceviche Mixto", 34.0], ["Chicharron de Pescado", 29.0], ["Arroz con Mariscos", 33.0], ["Jalea", 38.0], ["Sudado de Pescado", 31.0], ["Parihuela", 36.0]],
};
const CATEGORIAS = Object.keys(MENUS);
const COMENTARIOS = ["Excelente sabor", "Muy buena atencion", "Llego rapido", "Porciones generosas", "Podria mejorar", "Volveria a pedir", "Todo perfecto", "Un poco frio", "Buena relacion precio-calidad"];

const rnd = (n) => Math.floor(Math.random() * n);
const pick = (arr) => arr[rnd(arr.length)];
const round1 = (x) => Math.round(x * 10) / 10;

function crearRestaurante(i) {
  const categoria = pick(CATEGORIAS);
  const menu = MENUS[categoria];
  const cantidadPlatos = 4 + rnd(menu.length - 3);
  const platos = menu.slice(0, cantidadPlatos).map(([nombre, precio], idx) => ({
    id: `p${idx + 1}`,
    nombre,
    descripcion: `${nombre} de la casa`,
    precio: round1(precio * (0.9 + Math.random() * 0.3)),
    categoria: idx < 4 ? "Fondos" : "Extras",
    disponible: Math.random() > 0.05,
  }));
  const resenas = [];
  for (let r = rnd(5); r > 0; r--) {
    resenas.push({
      usuario_id: 1 + rnd(20000),
      comentario: pick(COMENTARIOS),
      puntuacion: 1 + rnd(5),
      fecha: new Date(Date.now() - rnd(365) * 86400000),
    });
  }
  const promedio = resenas.length
    ? round1(resenas.reduce((acc, x) => acc + x.puntuacion, 0) / resenas.length)
    : round1(3 + Math.random() * 2);
  return {
    nombre: `${pick(NOMBRES)} ${pick(ADJ)} #${i}`,
    categoria,
    ciudad: pick(CIUDADES),
    direccion: `${pick(CALLES)} ${100 + rnd(900)}`,
    admin_id: null,
    calificacion_promedio: promedio,
    platos,
    resenas,
  };
}

print(`Restaurantes existentes: ${existentes}. Insertando hasta ${TOTAL}...`);
let insertados = 0;
for (let i = existentes; i < TOTAL; i += BATCH) {
  const docs = [];
  for (let j = i; j < Math.min(i + BATCH, TOTAL); j++) docs.push(crearRestaurante(j + 1));
  col.insertMany(docs, { ordered: false });
  insertados += docs.length;
}
col.createIndex({ categoria: 1 });
col.createIndex({ ciudad: 1 });
print(`Insertados ${insertados}. Total en la coleccion: ${col.countDocuments()}`);
