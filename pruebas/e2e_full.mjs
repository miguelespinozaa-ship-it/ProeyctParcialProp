// Prueba E2E en navegador: registro, pedido, reseña, despacho, entrega, tracking, analítica y rutas protegidas.
// Uso: npm i playwright && npx playwright install chromium && node pruebas/e2e_full.mjs
// El 409 en consola es esperado: un pedido solo lo puede tomar un repartidor.
import { chromium } from "playwright";
const U = "https://main.d2wzxjgeu63fi4.amplifyapp.com";
const API = "https://jt3z0elcud.execute-api.us-east-1.amazonaws.com";
const b = await chromium.launch(); const ctx = await b.newContext({ viewport: { width: 1200, height: 900 } });
const page = await ctx.newPage();
const errs = []; page.on("console", (m) => m.type() === "error" && errs.push(m.text())); page.on("pageerror", (e) => errs.push(String(e)));
const res4xx = []; page.on("response", (r) => { if (r.status() >= 400 && !/\/register|\/auth/.test(r.url())) res4xx.push(r.status() + " " + r.url()); });
let bad = 0, n = 0; const check = (nom, ok, x = "") => { n++; console.log((ok ? "OK   " : "FALLA") + " " + nom + (x ? `  (${x})` : "")); if (!ok) bad++; };
const stamp = Date.now();
const salir = async () => { await page.evaluate(() => localStorage.clear()); };
const login = async (email, url) => { await page.goto(`${U}/login`); await salir(); await page.goto(`${U}/login`);
  await page.fill('input[type="email"]', email); await page.fill('input[type="password"]', "password123"); await page.click('button[type="submit"]'); await page.waitForURL(`**${url}`); };
const token = async () => JSON.parse(await page.evaluate(() => localStorage.getItem("auth"))).token;

console.log("== 1. CUSTOMER: registro, catálogo, pedido y tracking ==");
const emailC = `e2e.customer.${stamp}@demo.com`;
await page.goto(`${U}/register`); await salir(); await page.goto(`${U}/register`);
await page.fill('input[name="nombre"]', "Cliente E2E"); await page.fill('input[name="email"]', emailC); await page.fill('input[name="password"]', "password123");
await page.click('button[type="submit"]'); await page.waitForURL("**/customer");
check("registro de customer y redirección a /customer", true, emailC);
await page.waitForSelector(".grid .card");
check("grilla paginada de 12 restaurantes", (await page.locator(".grid .card").count()) === 12);
check("paginador: 20,000 restaurantes", /20[.,]000/.test(await page.locator(".pagination").first().innerText()));
await page.locator(".grid .card h3", { hasText: /^Sabor Criollo$/ }).first().click(); await page.waitForSelector(".dish-card");
const plato = await page.locator(".dish-card h3").first().innerText();
const add = page.locator(".dish-card").first().getByRole("button", { name: "+" }); await add.click(); await add.click();
await page.fill('input[placeholder="Dirección de entrega"]', `Calle E2E ${stamp}`);
await page.getByRole("button", { name: "Hacer pedido" }).click(); await page.waitForURL("**/customer/orders/*", { timeout: 30000 });
const orderId = page.url().split("/").pop(); await page.waitForSelector("h1:has-text('Pedido #')");
let body = await page.locator("main").innerText();
check("pedido creado y tracking en estado PEDIDO", /PEDIDO/.test(body) && body.includes(`2x ${plato}`), `#${orderId}, 2x ${plato}`);
check("tracking sin repartidor asignado", /Todavía no asignado/.test(body));

console.log("== 2. CUSTOMER: reseña ==");
await page.goto(`${U}/customer`); await page.waitForSelector(".grid .card");
await page.locator(".grid .card h3", { hasText: /^Sabor Criollo$/ }).first().click(); await page.waitForSelector(".reviews");
const txt = `Muy buen servicio E2E ${stamp}`;
await page.selectOption(".review-form select", "4"); await page.fill(".review-form textarea", txt); await page.getByRole("button", { name: "Publicar reseña" }).click();
await page.waitForSelector(`.review-list li:has-text("${txt}")`, { timeout: 20000 });
check("la reseña aparece con 4 estrellas y 'Tú'", (await page.locator(".review-list li", { hasText: txt }).innerText()).includes("Tú"));

console.log("== 3. ADMIN: ve los platos del pedido y lo despacha ==");
await login("admin@demo.com", "/admin"); await page.waitForSelector(".order-items");
const cnt = async (t) => Number((await page.locator(".tabs button", { hasText: t }).innerText()).match(/\(([\d,]+)\)/)[1].replace(/,/g, ""));
const pedidos0 = await cnt("PEDIDO"), env0 = await cnt("ENVIADO");
const fila = page.locator(".order-list > li", { hasText: `#${orderId} ` }).first();
check("el pedido está en la pestaña PEDIDO", await fila.count() === 1);
const ft = await fila.innerText();
check("muestra '2 platos' y la lista de platos", /2 platos/.test(ft) && ft.includes(`2 × ${plato}`), ft.replace(/\n/g, " / ").slice(0, 90));
await fila.getByRole("button", { name: "Enviar" }).click();
await page.waitForFunction((n) => /PEDIDO \(([\d,]+)\)/.test(document.querySelector(".tabs").innerText) && Number(document.querySelector(".tabs button").innerText.match(/\(([\d,]+)\)/)[1].replace(/,/g, "")) < n, pedidos0, { timeout: 20000 });
check("PEDIDO baja en 1 y ENVIADO sube en 1", (await cnt("PEDIDO")) === pedidos0 - 1 && (await cnt("ENVIADO")) === env0 + 1, `${pedidos0}->${await cnt("PEDIDO")}, ${env0}->${await cnt("ENVIADO")}`);
await page.locator(".tabs button", { hasText: "ENVIADO" }).click(); await page.waitForTimeout(800);
check("el pedido aparece en la pestaña ENVIADO sin botón 'Enviar'", (await page.locator(".order-list > li", { hasText: `#${orderId} ` }).count()) === 1
  && (await page.locator(".order-list > li", { hasText: `#${orderId} ` }).getByRole("button", { name: "Enviar" }).count()) === 0);
check("clientes paginados en el panel", /Página 1 de/.test(await page.locator(".pagination").last().innerText()));

console.log("== 4. DELIVERY: registro, toma el pedido y lo entrega ==");
const emailD = `e2e.delivery.${stamp}@demo.com`;
await page.goto(`${U}/register`); await salir(); await page.goto(`${U}/register`);
await page.fill('input[name="nombre"]', "Repartidor E2E"); await page.fill('input[name="email"]', emailD); await page.fill('input[name="password"]', "password123");
await page.selectOption('select[name="rol"]', "delivery"); await page.click('button[type="submit"]'); await page.waitForURL("**/delivery");
await page.waitForSelector(".pagination");
check("delivery ve el pool de pedidos disponibles paginado", /Disponibles para jalar \(([\d,]+)\)/.test(await page.locator("h2").first().innerText()));
const tk = await token();
const r = await page.evaluate(async ([api, id, t]) => { const x = await fetch(`${api}/ms3/api/v1/orders/${id}/claim`, { method: "PUT", headers: { Authorization: `Bearer ${t}` } }); return x.status; }, [API, orderId, tk]);
check("claim del pedido (el pedido más viejo del pool: se toma por API)", r === 200, `HTTP ${r}`);
const r2 = await page.evaluate(async ([api, id, t]) => (await fetch(`${api}/ms3/api/v1/orders/${id}/claim`, { method: "PUT", headers: { Authorization: `Bearer ${t}` } })).status, [API, orderId, tk]);
check("un segundo claim del mismo pedido es rechazado (409)", r2 === 409, `HTTP ${r2}`);
await page.reload(); await page.waitForSelector(".pagination");
const li = page.locator(".order-list li", { hasText: `#${orderId} ` }).first(); await li.waitFor({ timeout: 20000 });
check("el pedido aparece en 'Mis entregas en curso'", (await page.locator("h2", { hasText: "Mis entregas en curso (1)" }).count()) === 1);
await li.getByRole("button", { name: "Marcar entregado" }).click();
await page.waitForFunction(() => /Mis entregas en curso \(0\)/.test(document.body.innerText), null, { timeout: 20000 });
check("marcar entregado vacía las entregas en curso", true);

console.log("== 5. CUSTOMER: ve el pedido ENTREGADO con su repartidor ==");
await login(emailC, "/customer");
await page.goto(`${U}/customer/orders/${orderId}`); await page.waitForSelector("h1:has-text('Pedido #')");
body = await page.locator("main").innerText();
check("tracking ENTREGADO con el nombre del repartidor", /ENTREGADO/.test(body) && body.includes("Repartidor E2E"));
await page.goto(`${U}/customer`); await page.waitForSelector(".order-list");
check("'Mis pedidos' lista el pedido como ENTREGADO", (await page.locator(".order-list li", { hasText: `Pedido #${orderId}` }).innerText()).includes("ENTREGADO"));

console.log("== 6. ADMIN: analítica (Athena) ==");
await login("admin@demo.com", "/admin"); await page.goto(`${U}/admin/analytics`); await page.waitForSelector(".pagination", { timeout: 90000 });
const t = await page.locator("main").innerText();
check("top de restaurantes y métricas de usuarios cargan desde Athena", /Top restaurantes/.test(t) && /Métricas de usuarios/.test(t));
check("montos con formato S/ 0,000.00 (sin ruido decimal)", /S\/ [\d,]+\.\d{2}\b/.test(t) && !/\d\.\d{6,}/.test(t));
check("20,000+ usuarios paginados", /20[.,]\d{3}/.test(await page.locator(".pagination").last().innerText()));

console.log("== 7. Seguridad de rutas ==");
await salir(); await page.goto(`${U}/admin`); await page.waitForURL("**/login");
check("sin sesión, /admin redirige a /login", true);
await login("customer@demo.com", "/customer"); await page.goto(`${U}/admin`); await page.waitForTimeout(1500);
check("un customer no ve el panel de admin", !(await page.locator(".tabs").count()));

console.log("\nerrores de consola:", errs.length ? errs : "ninguno");
console.log("respuestas 4xx inesperadas:", res4xx.length ? res4xx : "ninguna");
console.log(`\n${n - bad}/${n} comprobaciones OK`, bad ? `· FALLARON ${bad}` : "· TODO OK");
await b.close(); process.exit(bad ? 1 : 0);
