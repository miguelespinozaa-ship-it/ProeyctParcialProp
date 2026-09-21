// Genera Presentacion-Delivery-Cloud.pptx
// Uso: NODE_PATH=<carpeta con node_modules de pptxgenjs> node generar_presentacion.js
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const AQUI = __dirname;
const DIAG = path.join(AQUI, "..", "infra", "diagramas");
const CAP = path.join(AQUI, "capturas");
const REPO = "github.com/miguelespinozaa-ship-it/ProeyctParcialProp";
const AMPLIFY = "main.d2wzxjgeu63fi4.amplifyapp.com";
const GATEWAY = "jt3z0elcud.execute-api.us-east-1.amazonaws.com";

const NAVY = "232F3E", NARANJA = "ED7100", CLARO = "F2F4F7", GRIS = "5F6B7A", BLANCO = "FFFFFF", TEXTO = "1F2933";
const F = "Calibri";

const evPath = path.join(AQUI, "athena_evidence.json");
const ev = fs.existsSync(evPath) ? JSON.parse(fs.readFileSync(evPath, "utf8")) : null;
const nfmt = (n) => Number(n).toLocaleString("en-US");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 pulgadas
pres.title = "Delivery Cloud";

const sombra = () => ({ type: "outer", color: "000000", blur: 8, offset: 2, angle: 90, opacity: 0.15 });

function titulo(s, texto, sub) {
  s.addText(texto, { x: 0.5, y: 0.28, w: 9, h: 0.6, fontFace: F, fontSize: 28, bold: true, color: NAVY, margin: 0, isTextBox: true });
  if (sub) s.addText(sub, { x: 0.5, y: 0.86, w: 9, h: 0.35, fontFace: F, fontSize: 14, color: GRIS, margin: 0, isTextBox: true });
}
function claro() { const s = pres.addSlide(); s.background = { color: BLANCO }; return s; }
function oscuro() { const s = pres.addSlide(); s.background = { color: NAVY }; return s; }
function tarjeta(s, x, y, w, h, fill) {
  s.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, fill: { color: fill || CLARO }, line: { color: "E1E5EA", width: 0.75 } });
}
function cifra(s, x, y, w, valor, etiqueta, color) {
  s.addText(valor, { x, y, w, h: 0.75, fontFace: F, fontSize: 38, bold: true, color: color || NARANJA, margin: 0, isTextBox: true });
  s.addText(etiqueta, { x, y: y + 0.75, w, h: 0.5, fontFace: F, fontSize: 12, color: GRIS, margin: 0, valign: "top", isTextBox: true });
}
function imgAjustada(s, ruta, x, y, wMax, hMax) {
  const dim = require("child_process").execSync(`python3 -c "from PIL import Image; import sys; w,h=Image.open(sys.argv[1]).size; print(w,h)" "${ruta}"`).toString().trim().split(" ").map(Number);
  const r = dim[0] / dim[1];
  let w = wMax, h = w / r;
  if (h > hMax) { h = hMax; w = h * r; }
  s.addImage({ path: ruta, x: x + (wMax - w) / 2, y, w, h });
  return { w, h };
}

// 1 ─ Portada
{
  const s = oscuro();
  s.addText("Delivery Cloud", { x: 0.6, y: 1.25, w: 5.2, h: 0.9, fontFace: F, fontSize: 46, bold: true, color: BLANCO, margin: 0, isTextBox: true });
  s.addText("Plataforma de delivery con microservicios, data lake y analítica en AWS", { x: 0.6, y: 2.2, w: 4.9, h: 0.9, fontFace: F, fontSize: 18, color: "C9D1DB", margin: 0, valign: "top", isTextBox: true });
  s.addText("Proyecto Parcial · Semanas 3 a 6", { x: 0.6, y: 3.3, w: 4.9, h: 0.35, fontFace: F, fontSize: 14, color: NARANJA, bold: true, margin: 0, isTextBox: true });
  s.addText([{ text: "Código: " + REPO, options: { breakLine: true } }, { text: "Aplicación: " + AMPLIFY }],
    { x: 0.6, y: 4.5, w: 5.0, h: 0.6, fontFace: F, fontSize: 10.5, color: "9AA7B5", margin: 0, isTextBox: true });
  s.addImage({ path: path.join(CAP, "01-customer-restaurantes.png"), x: 5.75, y: 1.15, w: 3.85, h: 3.85 * 780 / 1280, shadow: sombra() });
  s.addImage({ path: path.join(CAP, "03-admin-pedidos.png"), x: 6.6, y: 3.05, w: 3.0, h: 3.0 * 780 / 1280, shadow: sombra() });
  s.addNotes("Presentación del proyecto Delivery Cloud: cinco microservicios en Docker, una aplicación web y un pipeline de datos, todo desplegado en AWS.");
}

// 2 ─ Qué resuelve
{
  const s = claro();
  titulo(s, "Una plataforma de delivery con tres roles", "Cada rol tiene su propio flujo de punta a punta");
  const roles = [
    ["Customer", ["Explora restaurantes (20,000)", "Arma su carrito y hace pedidos", "Sigue el pedido y deja reseñas"]],
    ["Admin de restaurante", ["Gestiona su menú (CRUD)", "Ve qué platos pidió cada cliente", "Despacha el pedido"]],
    ["Delivery", ["Ve los pedidos disponibles", "Toma un pedido (solo uno gana)", "Lo marca como entregado"]],
  ];
  roles.forEach(([n, b], i) => {
    const x = 0.5 + i * 3.05;
    tarjeta(s, x, 1.55, 2.85, 2.6, CLARO);
    s.addShape(pres.ShapeType.ellipse, { x: x + 0.2, y: 1.75, w: 0.55, h: 0.55, fill: { color: NARANJA }, line: { color: NARANJA } });
    s.addText(String(i + 1), { x: x + 0.2, y: 1.75, w: 0.55, h: 0.55, fontFace: F, fontSize: 20, bold: true, color: BLANCO, align: "center", valign: "middle", margin: 0, isTextBox: true });
    s.addText(n, { x: x + 0.9, y: 1.75, w: 1.85, h: 0.55, fontFace: F, fontSize: 16, bold: true, color: NAVY, valign: "middle", margin: 0, isTextBox: true });
    s.addText(b.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < b.length - 1 } })),
      { x: x + 0.2, y: 2.5, w: 2.5, h: 1.5, fontFace: F, fontSize: 13, color: TEXTO, margin: 0, valign: "top", paraSpaceAfter: 6, isTextBox: true });
  });
  s.addText("Detrás: 5 microservicios en Docker, un data lake en S3 con analítica en Athena y una SPA en AWS Amplify.",
    { x: 0.5, y: 4.55, w: 9, h: 0.5, fontFace: F, fontSize: 14, italic: true, color: GRIS, margin: 0, isTextBox: true });
  s.addNotes("Tres roles: customer, admin de restaurante y delivery. El pedido pasa por tres estados: PEDIDO, ENVIADO y ENTREGADO.");
}

// 3 ─ Cifras
{
  const s = claro();
  titulo(s, "El proyecto en cifras");
  const datos = [
    ["5", "microservicios en Docker"], ["3", "lenguajes y 3 bases de datos (2 SQL, 1 NoSQL)"], ["20,000+", "registros en cada base de datos"],
    ["4", "máquinas virtuales (2 de App balanceadas)"], ["72", "requests de Postman · 66 aserciones · 0 fallos"], ["4 + 2", "consultas con JOIN y vistas en Athena"],
  ];
  datos.forEach(([v, t], i) => cifra(s, 0.6 + (i % 3) * 3.05, 1.5 + Math.floor(i / 3) * 1.85, 2.8, v, t));
  s.addNotes("Cifras clave. Cada base de datos tiene más de 20,000 registros cargados de una sola vez con scripts incluidos en el repositorio.");
}

// 4 ─ Arquitectura
{
  const s = claro();
  titulo(s, "Arquitectura de la solución");
  imgAjustada(s, path.join(DIAG, "arquitectura-solucion.png"), 0.3, 0.9, 7.6, 4.55);
  const puntos = [["HTTPS de punta a punta", "Amplify → API Gateway → VPC Link"], ["Balanceador interno", "ALB sin IP pública reparte entre 2 VMs"], ["BD privada", "Sin puertos abiertos a internet"]];
  puntos.forEach(([a, b], i) => {
    const y = 1.1 + i * 1.4;
    tarjeta(s, 8.0, y, 1.75, 1.25, CLARO);
    s.addText(a, { x: 8.1, y: y + 0.08, w: 1.55, h: 0.5, fontFace: F, fontSize: 12, bold: true, color: NAVY, margin: 0, valign: "top", isTextBox: true });
    s.addText(b, { x: 8.1, y: y + 0.6, w: 1.55, h: 0.6, fontFace: F, fontSize: 10.5, color: GRIS, margin: 0, valign: "top", isTextBox: true });
  });
  s.addNotes("La petición entra por API Gateway y un VPC Link hacia un ALB interno. Las bases de datos y la ingesta viven en instancias sin acceso desde internet.");
}

// 5 ─ Microservicios
{
  const s = claro();
  titulo(s, "Cinco microservicios, tres lenguajes", "Cada uno con su responsabilidad y su propia documentación Swagger");
  const ms = [
    ["MS1", "Usuarios / Auth", "Python · FastAPI", "MySQL", "Registro, login JWT, perfil y direcciones"],
    ["MS2", "Catálogo", "Java · Spring Boot", "MongoDB", "Restaurantes, menú y reseñas"],
    ["MS3", "Pedidos", "Node.js · Express", "PostgreSQL", "Pedidos y sus estados; consulta a MS1 y MS2"],
    ["MS4", "Agregador", "Python · FastAPI", "Sin base de datos", "Tracking y dashboards con MS1, MS2 y MS3"],
    ["MS5", "Analítico", "Python · FastAPI", "Amazon Athena", "Consultas SQL al data lake con boto3"],
  ];
  ms.forEach(([id, n, tec, bd, r], i) => {
    const x = 0.4 + i * 1.86;
    tarjeta(s, x, 1.5, 1.74, 2.85, CLARO);
    s.addText(id, { x: x + 0.12, y: 1.6, w: 1.5, h: 0.5, fontFace: F, fontSize: 24, bold: true, color: NARANJA, margin: 0, isTextBox: true });
    s.addText(n, { x: x + 0.12, y: 2.1, w: 1.5, h: 0.35, fontFace: F, fontSize: 14, bold: true, color: NAVY, margin: 0, isTextBox: true });
    s.addText(tec, { x: x + 0.12, y: 2.5, w: 1.5, h: 0.3, fontFace: F, fontSize: 11, color: TEXTO, margin: 0, isTextBox: true });
    s.addText(bd, { x: x + 0.12, y: 2.8, w: 1.5, h: 0.3, fontFace: F, fontSize: 11, bold: true, color: "3B48CC", margin: 0, isTextBox: true });
    s.addText(r, { x: x + 0.12, y: 3.25, w: 1.5, h: 1.3, fontFace: F, fontSize: 11, color: GRIS, margin: 0, valign: "top", isTextBox: true });
  });
  s.addText("MS3 consume a MS1 y MS2 · MS4 no tiene base de datos y solo consume a otros · MS5 ejecuta queries en Athena",
    { x: 0.5, y: 4.6, w: 9, h: 0.4, fontFace: F, fontSize: 12, italic: true, color: GRIS, margin: 0, isTextBox: true });
  s.addNotes("MS3 valida cada plato contra MS2 antes de guardar el pedido. MS4 combina tres servicios sin base de datos propia. MS5 usa boto3 para consultar Athena.");
}

// 6 ─ SQL
{
  const s = claro();
  titulo(s, "Modelo de datos relacional", "Dos tablas relacionadas por cada base SQL");
  const a = imgAjustada(s, path.join(DIAG, "er-mysql-ms1.png"), 0.4, 1.45, 4.5, 2.6);
  const b = imgAjustada(s, path.join(DIAG, "er-postgresql-ms3.png"), 5.1, 1.45, 4.5, 2.6);
  s.addText("MS1 · MySQL 8.0 — usuarios 1:N direcciones", { x: 0.4, y: 1.45 + a.h + 0.08, w: 4.5, h: 0.3, fontFace: F, fontSize: 12, bold: true, color: NAVY, margin: 0, isTextBox: true });
  s.addText("MS3 · PostgreSQL 16 — orders 1:N order_items", { x: 5.1, y: 1.45 + b.h + 0.08, w: 4.5, h: 0.3, fontFace: F, fontSize: 12, bold: true, color: NAVY, margin: 0, isTextBox: true });
  const c = (ev && ev.counts) || {};
  s.addText(`Carga masiva única: ${c.usuarios ? nfmt(c.usuarios) : "20,000+"} usuarios (seed.py) y ${c.orders ? nfmt(c.orders) : "20,000+"} pedidos con ${c.order_items ? nfmt(c.order_items) : "sus"} ítems (seed.js)`,
    { x: 0.4, y: 4.7, w: 9.2, h: 0.4, fontFace: F, fontSize: 13, color: GRIS, italic: true, margin: 0, isTextBox: true });
  s.addNotes("Diagramas entidad-relación de las dos bases SQL. Las referencias entre servicios (customer_id, restaurant_id) son lógicas y se resuelven por API.");
}

// 7 ─ Mongo
{
  const s = claro();
  titulo(s, "MongoDB: platos y reseñas embebidos");
  const im = imgAjustada(s, path.join(DIAG, "json-mongodb-ms2.png"), 0.4, 1.1, 6.0, 3.8);
  const pts = ["20,000 restaurantes cargados con seed.js (mongosh)", "Platos y reseñas van embebidos: se leen siempre junto al restaurante",
    "Índices en categoría y ciudad", "Listado paginado: 12 restaurantes por página en la web"];
  s.addText(pts.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < pts.length - 1 } })),
    { x: 6.7, y: 1.3, w: 2.9, h: 3.2, fontFace: F, fontSize: 13, color: TEXTO, margin: 0, valign: "top", paraSpaceAfter: 8, isTextBox: true });
  s.addNotes("Estructura JSON del documento de restaurante. Al ser 20,000 documentos, el listado se paginó.");
}

// 8 ─ Despliegue y balanceo
{
  const s = claro();
  titulo(s, "Despliegue en AWS con balanceo de carga", "Amplify → API Gateway → VPC Link → ALB interno → 2 VMs de App → BD privada");
  const cajas = [["AWS Amplify", "SPA React", "FDECEF", "DD344C"], ["API Gateway", "HTTPS", "FDE7F1", "E7157B"], ["VPC Link", "→ red privada", "F1E9FF", "8C4FFF"],
    ["ALB interno", "sin IP pública", "F1E9FF", "8C4FFF"], ["2 × EC2 App", "NGINX + 5 MS", "FFF3E0", "ED7100"], ["EC2 BD", "MySQL · PG · Mongo", "E6E9FB", "3B48CC"]];
  cajas.forEach(([a, b, f, l], i) => {
    const x = 0.35 + i * 1.6;
    s.addShape(pres.ShapeType.roundRect, { x, y: 1.5, w: 1.35, h: 1.0, rectRadius: 0.08, fill: { color: f }, line: { color: l, width: 1.5 } });
    s.addText([{ text: a, options: { bold: true, breakLine: true, fontSize: 12 } }, { text: b, options: { fontSize: 10, color: GRIS } }],
      { x, y: 1.5, w: 1.35, h: 1.0, fontFace: F, color: NAVY, align: "center", valign: "middle", margin: 0, isTextBox: true });
    if (i < cajas.length - 1) s.addShape(pres.ShapeType.line, { x: x + 1.35, y: 2.0, w: 0.25, h: 0, line: { color: NAVY, width: 1.5, endArrowType: "triangle" } });
  });
  cifra(s, 0.6, 3.0, 2.8, "14 / 13", "peticiones atendidas por app-1 y app-2 (cabecera X-Served-By)");
  cifra(s, 3.6, 3.0, 2.8, "30 de 30", "respuestas 200 con una VM caída: el ALB la saca de rotación");
  cifra(s, 6.6, 3.0, 3.0, "0", "puertos de la BD abiertos a internet (solo el SG de App e Ingesta)");
  s.addNotes("Se probó el balanceo con 30 peticiones y la tolerancia a fallos deteniendo NGINX en la segunda VM: la otra atendió todo el tráfico.");
}

// 9 ─ Frontend
{
  const s = claro();
  titulo(s, "Aplicación web en React, desplegada en AWS Amplify", "Capturas de la aplicación en producción");
  const caps = [["01-customer-restaurantes.png", "Customer · 20,000 restaurantes paginados"], ["02-customer-menu-resenas.png", "Reseñas: promedio, lista y formulario"], ["03-admin-pedidos.png", "Admin · platos y cantidades de cada pedido"]];
  caps.forEach(([f, t], i) => {
    const x = 0.4 + i * 3.1;
    s.addImage({ path: path.join(CAP, f), x, y: 1.4, w: 2.95, h: 2.95 * 780 / 1280, shadow: sombra() });
    s.addText(t, { x, y: 1.4 + 2.95 * 780 / 1280 + 0.1, w: 2.95, h: 0.5, fontFace: F, fontSize: 12, bold: true, color: NAVY, margin: 0, valign: "top", isTextBox: true });
  });
  s.addText("CI/CD desde GitHub: cada push a main se despliega solo. Consume los 5 microservicios por el API Gateway: 5 · 9 · 8 · 4 · 2 llamadas REST hacia MS1 … MS5 (el mínimo pedido era 2 por servicio).",
    { x: 0.4, y: 4.55, w: 9.2, h: 0.6, fontFace: F, fontSize: 13, color: GRIS, italic: true, margin: 0, valign: "top", isTextBox: true });
  s.addNotes("La SPA tiene login y rutas por rol. Se despliega en AWS Amplify y habla con el API Gateway por HTTPS.");
}

// 10 ─ Pipeline de datos
{
  const s = claro();
  titulo(s, "Pipeline de Data Science", "De las bases de datos a una consulta SQL en Athena");
  const pasos = [["3 bases de datos", "MySQL · PG · Mongo", "E6E9FB", "3B48CC"], ["MV de ingesta", "3 contenedores Python", "FFF3E0", "ED7100"], ["S3 · Data Lake", "CSV / JSONL", "E8F5E1", "3F8624"],
    ["AWS Glue", "Crawler + catálogo", "F1E9FF", "8C4FFF"], ["Amazon Athena", "SQL · 2 vistas", "F1E9FF", "8C4FFF"], ["MS5 → Web", "Analítica en la SPA", "FDECEF", "DD344C"]];
  pasos.forEach(([a, b, f, l], i) => {
    const x = 0.35 + i * 1.6;
    s.addShape(pres.ShapeType.roundRect, { x, y: 1.55, w: 1.35, h: 1.05, rectRadius: 0.08, fill: { color: f }, line: { color: l, width: 1.5 } });
    s.addText([{ text: a, options: { bold: true, breakLine: true, fontSize: 12 } }, { text: b, options: { fontSize: 10, color: GRIS } }],
      { x, y: 1.55, w: 1.35, h: 1.05, fontFace: F, color: NAVY, align: "center", valign: "middle", margin: 0, isTextBox: true });
    if (i < pasos.length - 1) s.addShape(pres.ShapeType.line, { x: x + 1.35, y: 2.075, w: 0.25, h: 0, line: { color: NAVY, width: 1.5, endArrowType: "triangle" } });
  });
  const hechos = [["Pull del 100 %", "Cada contenedor extrae todas las tablas de un microservicio"], ["Full refresh", "Se reemplaza el snapshot anterior: sin duplicados en Athena"], ["5 tablas en Glue", "usuarios, direcciones, orders, order_items y mongodb"]];
  hechos.forEach(([a, b], i) => {
    const x = 0.5 + i * 3.05;
    tarjeta(s, x, 3.15, 2.85, 1.55, CLARO);
    s.addText(a, { x: x + 0.15, y: 3.25, w: 2.55, h: 0.4, fontFace: F, fontSize: 15, bold: true, color: NARANJA, margin: 0, isTextBox: true });
    s.addText(b, { x: x + 0.15, y: 3.7, w: 2.55, h: 0.9, fontFace: F, fontSize: 12, color: TEXTO, margin: 0, valign: "top", isTextBox: true });
  });
  s.addNotes("La MV de ingesta ejecuta tres contenedores Python que hacen pull del 100% de las tablas y las suben a S3. Glue las cataloga y Athena las consulta.");
}

// 11 ─ Glue ER
{
  const s = claro();
  titulo(s, "Catálogo de datos en AWS Glue");
  imgAjustada(s, path.join(DIAG, "er-catalogo-glue.png"), 0.6, 0.85, 8.8, 4.6);
  s.addNotes("Diagrama entidad-relación de las cinco tablas del catálogo. Las relaciones son lógicas y se resuelven con JOIN en Athena.");
}

// 12 ─ Athena
{
  const s = claro();
  titulo(s, "Consultas y vistas en Amazon Athena", "4 consultas con JOIN sobre varias tablas y 2 vistas · con el ID de cada ejecución");
  if (ev) {
    const nom = ["Ventas por restaurante", "Clientes con mayor gasto", "Platos más vendidos", "Ciudad del cliente vs. entrega"];
    const tablas = ["orders + order_items + mongodb", "orders + usuarios", "order_items + orders + mongodb", "orders + usuarios + direcciones"];
    const hdr = (t) => ({ text: t, options: { bold: true, color: BLANCO, fill: { color: NAVY }, fontFace: F, fontSize: 11 } });
    const cel = (t, o) => ({ text: String(t), options: Object.assign({ fontFace: F, fontSize: 10.5, color: TEXTO }, o || {}) });
    const filas = [[hdr("Consulta"), hdr("Tablas unidas"), hdr("Tiempo"), hdr("ID de ejecución (Athena)")]];
    ev.queries.forEach((q, i) => filas.push([cel(`${i + 1}. ${nom[i]}`, { bold: true }), cel(tablas[i]), cel((q.ms / 1000).toFixed(1) + " s"), cel(q.id.slice(0, 13) + "…", { fontFace: "Courier New", fontSize: 9.5 })]));
    ev.views.forEach((v) => filas.push([cel("Vista " + v.view, { bold: true }), cel("con JOIN"), cel((v.ms / 1000).toFixed(1) + " s"), cel(v.create_id.slice(0, 13) + "…", { fontFace: "Courier New", fontSize: 9.5 })]));
    s.addTable(filas, { x: 0.5, y: 1.4, w: 9.0, colW: [3.0, 3.0, 0.9, 2.1], rowH: 0.34, border: { type: "solid", pt: 0.5, color: "D0D5DD" }, valign: "middle" });
    const q3 = ev.queries[2];
    const filasG = q3.rows.slice(0, 3);
    s.addChart(pres.charts.BAR, [{ name: "Unidades vendidas", labels: filasG.map((r) => r[1] + " (" + r[0] + ")").map((t) => (t.length > 34 ? t.slice(0, 33) + "…" : t)), values: filasG.map((r) => Number(r[2])) }],
      { x: 0.5, y: 4.0, w: 9.0, h: 1.5, barDir: "bar", chartColors: [NARANJA], showTitle: false, showValue: true, dataLabelFontSize: 9, dataLabelColor: TEXTO,
        catAxisLabelFontSize: 9, catAxisLabelColor: GRIS, valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false, catAxisOrientation: "maxMin" });
  } else {
    s.addText("Evidencia de Athena pendiente de ejecución.", { x: 0.5, y: 2.5, w: 9, h: 0.5, fontFace: F, fontSize: 16, color: GRIS, margin: 0, isTextBox: true });
  }
  s.addNotes("Cada ejecución tiene un ID que se puede verificar en el historial de consultas de la consola de Athena. El gráfico muestra las unidades vendidas de la consulta 3.");
}

// 12b ─ Capturas de la consola de Athena
{
  const dirC = path.join(AQUI, "capturas-athena");
  const orden = ["consulta-1.png", "consulta-2.png", "consulta-3.png", "consulta-4.png", "vista-1.png", "vista-2.png"];
  const rot = { "consulta-1.png": "Consulta 1 · ventas por restaurante", "consulta-2.png": "Consulta 2 · clientes con mayor gasto", "consulta-3.png": "Consulta 3 · platos más vendidos",
    "consulta-4.png": "Consulta 4 · ciudad vs. dirección de entrega", "vista-1.png": "Vista v_resumen_ventas_restaurante", "vista-2.png": "Vista v_metricas_usuarios" };
  const hay = orden.filter((f) => fs.existsSync(path.join(dirC, f)));
  if (hay.length) {
    const s = claro();
    titulo(s, "Evidencia en la consola de Athena", "Capturas de las consultas y vistas ejecutadas sobre el data lake");
    const cols = hay.length <= 4 ? 2 : 3, w = cols === 2 ? 3.0 : 2.95, h = w * 1080 / 1920, gap = cols === 2 ? 0.3 : 0.12;
    const x0 = (10 - (cols * w + (cols - 1) * gap)) / 2;
    hay.forEach((f, i) => {
      const x = x0 + (i % cols) * (w + gap), y = 1.4 + Math.floor(i / cols) * (h + 0.42);
      s.addImage({ path: path.join(dirC, f), x, y, w, h, shadow: sombra() });
      s.addText(rot[f], { x, y: y + h + 0.05, w, h: 0.28, fontFace: F, fontSize: 11, bold: true, color: NAVY, margin: 0, isTextBox: true });
    });
    s.addNotes("Capturas reales de la consola de Amazon Athena con el workgroup pp-workgroup.");
  }
}

// 13 ─ Paginado
{
  const s = claro();
  titulo(s, "Paginado opcional: de megabytes a kilobytes", "Misma ruta, dos modos: sin parámetros devuelve todo; con ?page= y ?page_size= devuelve una página");
  const filas = [["Dashboard admin", "4.2 MB · 0.84 s", "4 KB · 60 ms"], ["Usuarios (MS1)", "6.6 MB · 2.3 s", "página: 14 ms"], ["Restaurantes (20,000)", "21 MB · 1.0 s", "página de 12: 14 ms"]];
  s.addText("Sin paginar", { x: 3.6, y: 1.55, w: 2.7, h: 0.35, fontFace: F, fontSize: 13, bold: true, color: GRIS, margin: 0, isTextBox: true });
  s.addText("Paginado", { x: 6.6, y: 1.55, w: 2.9, h: 0.35, fontFace: F, fontSize: 13, bold: true, color: NARANJA, margin: 0, isTextBox: true });
  filas.forEach(([n, a, b], i) => {
    const y = 2.0 + i * 0.95;
    tarjeta(s, 0.5, y, 9.0, 0.8, CLARO);
    s.addText(n, { x: 0.7, y, w: 2.8, h: 0.8, fontFace: F, fontSize: 15, bold: true, color: NAVY, valign: "middle", margin: 0, isTextBox: true });
    s.addText(a, { x: 3.6, y, w: 2.7, h: 0.8, fontFace: F, fontSize: 18, color: GRIS, valign: "middle", margin: 0, isTextBox: true });
    s.addText(b, { x: 6.6, y, w: 2.9, h: 0.8, fontFace: F, fontSize: 20, bold: true, color: NARANJA, valign: "middle", margin: 0, isTextBox: true });
  });
  s.addText("page_size vale 20 por defecto y se limita a 100 · total en la cabecera X-Total-Count · mediciones locales con unos 40 mil pedidos",
    { x: 0.5, y: 4.95, w: 9, h: 0.35, fontFace: F, fontSize: 11, italic: true, color: GRIS, margin: 0, isTextBox: true });
  s.addNotes("El paginado se agregó sin romper a los consumidores: sin parámetros el comportamiento es el de siempre.");
}

// 14 ─ Pruebas
{
  const s = claro();
  titulo(s, "Pruebas y validación");
  cifra(s, 0.6, 1.3, 2.8, "72", "requests de Postman/Newman · 66 aserciones · 0 fallos");
  cifra(s, 3.6, 1.3, 2.8, "3 roles", "recorridos completos con Playwright sobre la URL de Amplify");
  cifra(s, 6.6, 1.3, 3.0, "30 / 30", "respuestas 200 con una de las 2 VMs caída");
  const pts = ["Casos de error incluidos: 400, 401 y 422; con y sin paginado", "Conteos de Athena coinciden con las bases de datos", "Puertos 22, 3306, 5432 y 27017 cerrados a internet",
    "Swagger UI verificado en los 5 servicios a través del API Gateway"];
  tarjeta(s, 0.5, 3.0, 9.0, 1.9, CLARO);
  s.addText(pts.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < pts.length - 1 } })),
    { x: 0.75, y: 3.1, w: 8.5, h: 1.7, fontFace: F, fontSize: 14, color: TEXTO, margin: 0, valign: "middle", paraSpaceAfter: 6, isTextBox: true });
  s.addNotes("Las pruebas se ejecutaron en local y contra AWS a través del API Gateway.");
}

// 15 ─ Limitaciones
{
  const s = claro();
  titulo(s, "Limitaciones y próximos pasos");
  const izq = ["Las VMs aún aceptan el puerto 80 desde internet: cerrar y dejar solo el ALB", "VMs t2.micro (1 GB) con swap: subir a t3.small"];
  const der = ["Derivar el usuario de las reseñas del token JWT", "Programar la ingesta y el crawler (EventBridge)", "Ejecutar pruebas automáticas en el pipeline de CI", "Excluir password_hash del data lake"];
  [["Limitaciones actuales", izq, 0.5], ["Próximos pasos", der, 5.1]].forEach(([t, b, x]) => {
    tarjeta(s, x, 1.3, 4.4, 3.4, CLARO);
    s.addText(t, { x: x + 0.2, y: 1.42, w: 4.0, h: 0.4, fontFace: F, fontSize: 16, bold: true, color: NARANJA, margin: 0, isTextBox: true });
    s.addText(b.map((tt, i) => ({ text: tt, options: { bullet: true, breakLine: i < b.length - 1 } })),
      { x: x + 0.2, y: 1.95, w: 4.0, h: 2.6, fontFace: F, fontSize: 13, color: TEXTO, margin: 0, valign: "top", paraSpaceAfter: 8, isTextBox: true });
  });
  s.addNotes("Limitaciones conocidas y mejoras planeadas.");
}

// 16 ─ Cierre
{
  const s = oscuro();
  s.addText("Gracias", { x: 0.6, y: 1.3, w: 8.8, h: 0.9, fontFace: F, fontSize: 46, bold: true, color: BLANCO, margin: 0, isTextBox: true });
  s.addText("Delivery Cloud · microservicios, data lake y analítica en AWS", { x: 0.6, y: 2.25, w: 8.8, h: 0.5, fontFace: F, fontSize: 18, color: "C9D1DB", margin: 0, isTextBox: true });
  s.addText([{ text: "Código fuente (repositorio público)  ", options: { color: "9AA7B5", breakLine: true } }, { text: REPO, options: { color: BLANCO, breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 8 } },
    { text: "Aplicación web (AWS Amplify)  ", options: { color: "9AA7B5", breakLine: true } }, { text: AMPLIFY, options: { color: BLANCO, breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 8 } },
    { text: "API pública (API Gateway, HTTPS)  ", options: { color: "9AA7B5", breakLine: true } }, { text: GATEWAY, options: { color: BLANCO } }],
    { x: 0.6, y: 3.05, w: 8.8, h: 2.1, fontFace: F, fontSize: 14, margin: 0, valign: "top", isTextBox: true });
}

pres.writeFile({ fileName: path.join(AQUI, "Presentacion-Delivery-Cloud.pptx") }).then((f) => console.log("OK", f));
