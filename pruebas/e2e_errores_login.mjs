// Prueba: mensajes de error del login segun el fallo (503, sin conexion, clave incorrecta) y login correcto. Uso: node pruebas/e2e_errores_login.mjs [URL_del_frontend]
import { chromium } from "playwright";
const U = process.argv[2] || "http://localhost:5173";
const b = await chromium.launch(); const page = await b.newPage();
let bad = 0; const check = (n, c, x = "") => { console.log((c ? "OK   " : "FALLA") + " " + n + (x ? ` (${x})` : "")); if (!c) bad++; };
async function intentar(ruta, modo) {
  await page.unroute("**/auth/login"); await page.unroute("**/auth/register");
  if (modo === "caido") await page.route("**/auth/login", (r) => r.fulfill({ status: 503, contentType: "application/json", body: '{"message":"Service Unavailable"}' }));
  if (modo === "red") await page.route("**/auth/login", (r) => r.abort("failed"));
  await page.goto(`${U}/login`); await page.fill('input[type="email"]', "customer@demo.com"); await page.fill('input[type="password"]', modo === "mala" ? "incorrecta" : "password123");
  await page.click('button[type="submit"]'); await page.waitForTimeout(1500);
  return modo === "ok" ? page.url() : await page.locator(".error").innerText();
}
check("servidor caído (503): mensaje de servidor no disponible", /no está disponible/.test(await intentar("login", "caido")));
check("sin conexión / CORS: mensaje de conexión", /No se pudo conectar/.test(await intentar("login", "red")));
check("clave incorrecta: 'Credenciales inválidas' (solo en este caso)", /Credenciales inválidas/.test(await intentar("login", "mala")));
check("login correcto entra a /customer", /\/customer/.test(await intentar("login", "ok")));
console.log(bad ? `FALLARON ${bad}` : "TODO OK"); await b.close(); process.exit(bad ? 1 : 0);
