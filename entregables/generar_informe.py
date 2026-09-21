#!/usr/bin/env python3
"""Genera el informe técnico en PDF.

Uso:  AUTORES="Nombre Apellido; Otro Integrante" python3 generar_informe.py
Lee la evidencia de Athena de athena_evidence.json (generado por recolectar_evidencia.py).
"""
import json
import os
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, NextPageTemplate, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle, Preformatted)

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
DIAG = os.path.join(RAIZ, "infra", "diagramas")
SALIDA = os.path.join(AQUI, "Informe-Tecnico-Delivery-Cloud.pdf")

pdfmetrics.registerFont(TTFont("F", "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("F-B", "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("F-I", "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Oblique.ttf"))
pdfmetrics.registerFontFamily("F", normal="F", bold="F-B", italic="F-I", boldItalic="F-B")

AZUL = colors.HexColor("#232F3E")
NARANJA = colors.HexColor("#ED7100")
GRIS = colors.HexColor("#5F6B7A")
CLARO = colors.HexColor("#F2F4F7")
LINEA = colors.HexColor("#D0D5DD")

REPO = "https://github.com/miguelespinozaa-ship-it/ProeyctParcialProp"
AMPLIFY = "https://main.d2wzxjgeu63fi4.amplifyapp.com"
GATEWAY = "https://jt3z0elcud.execute-api.us-east-1.amazonaws.com"

S = {
    "titulo": ParagraphStyle("titulo", fontName="F-B", fontSize=30, leading=36, textColor=AZUL),
    "subtitulo": ParagraphStyle("subtitulo", fontName="F", fontSize=14, leading=20, textColor=GRIS),
    "h1": ParagraphStyle("h1", fontName="F-B", fontSize=16, leading=21, textColor=AZUL, spaceBefore=6, spaceAfter=8, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="F-B", fontSize=12, leading=16, textColor=NARANJA, spaceBefore=10, spaceAfter=5, keepWithNext=1),
    "h2n": ParagraphStyle("h2n", fontName="F-B", fontSize=12, leading=16, textColor=NARANJA, spaceBefore=10, spaceAfter=5),
    "p": ParagraphStyle("p", fontName="F", fontSize=9.3, leading=13.6, alignment=TA_JUSTIFY, spaceAfter=6),
    "b": ParagraphStyle("b", fontName="F", fontSize=9.3, leading=13.4, leftIndent=12, bulletIndent=2, spaceAfter=2.5, alignment=TA_LEFT),
    "peq": ParagraphStyle("peq", fontName="F", fontSize=8, leading=11, textColor=GRIS),
    "cel": ParagraphStyle("cel", fontName="F", fontSize=8.3, leading=11),
    "celb": ParagraphStyle("celb", fontName="F-B", fontSize=8.3, leading=11),
    "celh": ParagraphStyle("celh", fontName="F-B", fontSize=8.3, leading=11, textColor=colors.white),
    "leyenda": ParagraphStyle("leyenda", fontName="F-I", fontSize=8, leading=11, textColor=GRIS, alignment=1, spaceAfter=8),
    "codigo": ParagraphStyle("codigo", fontName="Courier", fontSize=7, leading=8.6, backColor=CLARO, borderPadding=5, leftIndent=4),
}


def P(t, e="p"):
    return Paragraph(t, S[e])


def B(items):
    return [Paragraph(t, S["b"], bulletText="•") for t in items]


def tabla(filas, anchos, cabecera=True, zebra=True, extra=None):
    data = []
    for i, f in enumerate(filas):
        est = "celh" if (cabecera and i == 0) else "cel"
        data.append([c if not isinstance(c, str) else Paragraph(c, S[est]) for c in f])
    t = Table(data, colWidths=anchos, repeatRows=1 if cabecera else 0)
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), 0.4, LINEA),
          ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
          ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5)]
    if cabecera:
        st.append(("BACKGROUND", (0, 0), (-1, 0), AZUL))
    if zebra:
        for i in range(1 if cabecera else 0, len(filas)):
            if i % 2 == 0:
                st.append(("BACKGROUND", (0, i), (-1, i), CLARO))
    if extra:
        st += extra
    t.setStyle(TableStyle(st))
    return t


def img(nombre, ancho, leyenda=None, alto_max=None):
    ruta = os.path.join(DIAG, nombre)
    from PIL import Image as PI
    w, h = PI.open(ruta).size
    alto = ancho * h / w
    if alto_max and alto > alto_max:
        ancho, alto = ancho * alto_max / alto, alto_max
    out = [Image(ruta, width=ancho, height=alto)]
    if leyenda:
        out.append(Paragraph(leyenda, S["leyenda"]))
    return out


def galeria(items, ancho_total):
    """Cuadrícula de 2 columnas con capturas y su leyenda."""
    from PIL import Image as PI
    cw = ancho_total / 2 - 6
    filas = []
    for i in range(0, len(items), 2):
        fila_i, fila_l = [], []
        for nombre, leyenda in items[i:i + 2]:
            ruta = os.path.join(AQUI, "capturas", nombre)
            w, h = PI.open(ruta).size
            fila_i.append(Image(ruta, width=cw, height=cw * h / w))
            fila_l.append(Paragraph(leyenda, S["leyenda"]))
        filas += [fila_i, fila_l]
    t = Table(filas, colWidths=[ancho_total / 2] * 2)
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                           ("BOX", (0, 0), (-1, -1), 0, colors.white)]))
    return t


def pie(canvas, doc):
    canvas.saveState()
    w, h = canvas._pagesize
    canvas.setFont("F", 7.5)
    canvas.setFillColor(GRIS)
    canvas.drawString(1.8 * cm, 1.0 * cm, "Delivery Cloud — Informe técnico")
    canvas.drawRightString(w - 1.8 * cm, 1.0 * cm, f"Página {doc.page}")
    canvas.setStrokeColor(LINEA)
    canvas.line(1.8 * cm, 1.4 * cm, w - 1.8 * cm, 1.4 * cm)
    canvas.restoreState()


def ejecuciones():
    ruta = os.path.join(AQUI, "athena_evidence.json")
    return json.load(open(ruta)) if os.path.exists(ruta) else None


def cuenta_llamadas_front():
    res = {}
    for n in range(1, 6):
        txt = open(os.path.join(RAIZ, "frontend", "src", "api", f"ms{n}.js")).read()
        res[n] = len(re.findall(r"client\.(get|post|put|patch|delete)", txt))
    return res


def fmt_num(x):
    try:
        v = float(x)
        return f"{v:,.2f}" if v != int(v) or "." in str(x) else f"{int(v):,}"
    except (ValueError, TypeError):
        return str(x)


def captura_athena(nombre, ancho):
    """Captura de la consola de Athena (si existe en entregables/capturas-athena)."""
    ruta = os.path.join(AQUI, "capturas-athena", nombre)
    if not os.path.exists(ruta):
        return []
    from PIL import Image as PI
    w, h = PI.open(ruta).size
    return [Spacer(1, 4), Image(ruta, width=ancho, height=ancho * h / w),
            Paragraph("Captura de la consola de Amazon Athena (workgroup pp-workgroup).", S["leyenda"])]


def bloque_consulta(num, titulo, desc, q):
    out = [P(f"Consulta {num} — {titulo}", "h2"), P(desc)]
    sql = q["sql"].strip()
    out.append(Preformatted(sql, S["codigo"]))
    out.append(Spacer(1, 4))
    hdr = [c for c in q["header"]]
    filas = [hdr] + [[fmt_num(c) if re.fullmatch(r"-?\d+(\.\d+)?(E\d+)?", c or "") else c for c in r] for r in q["rows"][:6]]
    n = len(hdr)
    ancho = 17.4 * cm / n
    out.append(tabla(filas, [ancho] * n))
    out.append(P(f"Athena: {q['id']} · {q['ms'] / 1000:.1f} s · {q['bytes'] / 1024:.0f} KB escaneados · primeras 6 filas de {len(q['rows'])} devueltas.", "peq"))
    out += captura_athena(f"consulta-{num}.png", 17.4 * cm)
    return out


def construir(autores):
    ev = ejecuciones()
    api = cuenta_llamadas_front()
    doc = BaseDocTemplate(SALIDA, pagesize=A4, title="Informe técnico — Delivery Cloud",
                          author=autores or "Equipo del proyecto", subject="Proyecto Parcial — microservicios en AWS")
    m = 1.8 * cm
    fr_v = Frame(m, 1.8 * cm, A4[0] - 2 * m, A4[1] - 3.4 * cm, id="v")
    ap = landscape(A4)
    fr_h = Frame(1.2 * cm, 1.8 * cm, ap[0] - 2.4 * cm, ap[1] - 3.0 * cm, id="h")
    doc.addPageTemplates([PageTemplate("vertical", frames=[fr_v], onPage=pie, pagesize=A4),
                          PageTemplate("horizontal", frames=[fr_h], onPage=pie, pagesize=ap)])
    W = A4[0] - 2 * m
    E = []

    # ---------------- Portada
    E += [Spacer(1, 4.2 * cm), P("Delivery Cloud", "titulo"), Spacer(1, 6),
          P("Plataforma de delivery basada en microservicios, con analítica sobre un data lake, desplegada en AWS", "subtitulo"),
          Spacer(1, 1.2 * cm), P("Informe técnico · Proyecto Parcial (Semanas 3 a 6)", "subtitulo"), Spacer(1, 1.6 * cm)]
    filas = [["Repositorio público (GitHub)", f'<link href="{REPO}" color="#1155CC">{REPO}</link>'],
             ["Aplicación web (AWS Amplify)", f'<link href="{AMPLIFY}" color="#1155CC">{AMPLIFY}</link>'],
             ["API pública (API Gateway, HTTPS)", f'<link href="{GATEWAY}" color="#1155CC">{GATEWAY}</link>'],
             ["Fecha", "21 de septiembre de 2026"]]
    if autores:
        filas.insert(0, ["Autores", autores])
    filas = [[f"<b>{a}</b>", b] for a, b in filas]
    E.append(tabla(filas, [5.6 * cm, W - 5.6 * cm], cabecera=False, zebra=False))
    E += [PageBreak()]

    # ---------------- 1. Resumen
    E += [P("1. Resumen", "h1"),
          P("Delivery Cloud es una plataforma de pedidos de comida con tres roles: <b>customer</b> (explora restaurantes, arma su carrito, "
            "hace pedidos, los sigue y deja reseñas), <b>admin</b> de restaurante (gestiona su menú, ve los platos de cada pedido y lo despacha) y "
            "<b>delivery</b> (toma pedidos disponibles y los entrega). El backend se compone de <b>cinco microservicios en Docker</b>, escritos en tres "
            "lenguajes y con tres motores de base de datos distintos. Un sexto flujo, de <b>Data Science</b>, extrae el 100 % de las tablas hacia un "
            "data lake en S3, las cataloga con AWS Glue y las consulta con Amazon Athena; el microservicio analítico (MS5) expone esas consultas a la aplicación web."),
          P("Todo está desplegado en AWS: dos máquinas virtuales de aplicación detrás de un <b>balanceador interno</b>, una máquina virtual de base de datos "
            "privada, una máquina de ingesta, <b>API Gateway</b> como puerta de entrada HTTPS (con VPC Link hacia el balanceador) y la SPA en <b>AWS Amplify</b>.")]
    cifras = [["Microservicios", "Lenguajes / motores", "Registros cargados", "Máquinas virtuales", "Consultas Athena"],
              ["5 en Docker", "Python, Java, Node.js · MySQL, PostgreSQL, MongoDB", "más de 20,000 por base de datos", "4 EC2 (2 de App balanceadas)", "4 con JOIN y 2 vistas"]]
    E += [tabla(cifras, [W / 5] * 5), Spacer(1, 8)]
    E.append(P("Cumplimiento de los requisitos", "h2n"))
    req = [["Requisito", "Cómo se cumple", "Sección"],
           ["5 microservicios en Docker; 3 con su propia BD, 3 lenguajes, 3 BD (2 SQL y 1 NoSQL)", "MS1 FastAPI + MySQL, MS2 Spring Boot + MongoDB, MS3 Express + PostgreSQL", "3"],
           ["Diagrama E/R por BD SQL y JSON de la BD NoSQL; mínimo 2 tablas relacionadas", "E/R de MySQL (usuarios 1:N direcciones) y PostgreSQL (orders 1:N order_items); estructura JSON de restaurantes", "4"],
           ["Un microservicio consume a otro", "MS3 consulta a MS2 (validar plato y precio) y a MS1 (nombres de clientes)", "3.2"],
           ["Un microservicio sin BD que solo consume a otros", "MS4 Agregador/Rastreo: tracking y 3 dashboards con datos de MS1, MS2 y MS3", "3"],
           ["Un microservicio analítico con queries en Athena", "MS5 ejecuta consultas con boto3 sobre las vistas del data lake", "7"],
           ["Carga masiva única, mínimo 20,000 registros por BD", "seed.py (usuarios), seed.js (pedidos) y seed.js en mongosh (restaurantes)", "4.4"],
           ["2 VMs de producción con balanceador privado, BD en una tercera VM privada, APIs públicas con HTTPS en API Gateway",
            "2 EC2 de App detrás de un ALB interno; API Gateway → VPC Link → ALB; BD en EC2 sin puertos abiertos a internet", "6"],
           ["Documentar las 5 APIs en Swagger UI", "Swagger UI accesible en los 5 servicios, incluso a través del API Gateway", "6.5"],
           ["Aplicación web que consuma los 5 servicios (≥ 2 métodos REST por servicio) desplegada en Amplify",
            f"SPA React: {api[1]}, {api[2]}, {api[3]}, {api[4]} y {api[5]} llamadas REST a MS1 … MS5; desplegada en AWS Amplify con CI/CD desde GitHub", "5"],
           ["MV de ingesta, bucket S3 y 3 contenedores Python de ingesta (pull del 100 %)", "PP-Ingest-VM con 3 contenedores; S3 con snapshot completo por tabla", "7.1"],
           ["Catálogo en Glue y diagrama E/R que relacione las tablas del catálogo", "Crawler sobre S3, 5 tablas; diagrama E/R del catálogo", "7.2"],
           ["4 consultas SQL con JOIN en Athena y 2 vistas", "Ejecutadas en Athena con evidencia (ID de ejecución y resultados)", "7.3"],
           ["Diagrama de arquitectura en draw.io con todos los servicios de AWS", "infra/diagramas/proyecto-delivery-cloud.drawio (5 páginas)", "2"],
           ["Repositorios públicos en GitHub", f"Un monorepo público con todo el código fuente", "Anexo A"]]
    E.append(tabla(req, [6.6 * cm, W - 6.6 * cm - 1.9 * cm, 1.9 * cm]))

    # ---------------- 2. Arquitectura (página horizontal)
    E += [NextPageTemplate("horizontal"), PageBreak(), P("2. Arquitectura de la solución", "h1")]
    E += img("arquitectura-solucion.png", 26.4 * cm, "Figura 1. Arquitectura de solución en AWS (editable en infra/diagramas/proyecto-delivery-cloud.drawio).", alto_max=15.2 * cm)
    E += [NextPageTemplate("vertical"), PageBreak()]
    E += [P("Flujo de una petición", "h2")]
    E += B(["<b>1. Carga de la aplicación.</b> El navegador descarga la SPA React desde AWS Amplify por HTTPS.",
            "<b>2. Llamada a la API.</b> La SPA llama al API Gateway (HTTP API, HTTPS) con rutas /ms1 … /ms5 y el token JWT del usuario.",
            "<b>3. Entrada a la red privada.</b> API Gateway entra a la VPC por un <b>VPC Link</b> hacia el <b>ALB interno</b>, que no tiene IP pública y solo acepta tráfico del VPC Link.",
            "<b>4. Balanceo.</b> El ALB reparte entre las dos VMs de App (zonas us-east-1a y 1b) y las saca de rotación si su health check /health falla.",
            "<b>5. Enrutamiento.</b> NGINX de cada VM enruta por prefijo de ruta al microservicio correspondiente y añade la cabecera <i>X-Served-By</i> con el nombre de la VM.",
            "<b>6. Datos.</b> Cada microservicio se conecta por IP privada a su base de datos en la VM de BD; MS5 consulta Athena con boto3 usando el rol de la instancia."])
    E += [P("Decisiones de diseño", "h2")]
    E += B(["<b>Base de datos por servicio.</b> Cada microservicio es dueño de su esquema; las relaciones entre servicios (customer_id, restaurant_id) son referencias lógicas y se resuelven por API, no por claves foráneas.",
            "<b>JWT compartido.</b> MS1 emite tokens HS256; MS2 y MS3 los validan con el mismo secreto. MS4 reenvía el token del usuario a los servicios que consulta.",
            "<b>Servicios sin estado.</b> Toda la persistencia está en la VM de BD, por eso las dos VMs de App son idénticas y pueden balancearse sin coordinación.",
            "<b>Paginado opcional.</b> Los listados grandes aceptan ?page= y ?page_size=; sin esos parámetros devuelven todo, como antes (sección 8)."])

    # ---------------- 3. Microservicios
    E += [P("3. Microservicios", "h1"),
          tabla([["Servicio", "Tecnología", "Base de datos", "Responsabilidad", "Operaciones (Swagger)"],
                 ["<b>MS1</b> Usuarios / Auth", "Python · FastAPI", "MySQL 8.0 (usuarios, direcciones)", "Registro, login (JWT), perfil, direcciones y consulta de usuarios", "12"],
                 ["<b>MS2</b> Catálogo", "Java 17 · Spring Boot", "MongoDB 7 (restaurantes con platos y reseñas embebidos)", "Restaurantes, menú (CRUD del admin) y reseñas", "13"],
                 ["<b>MS3</b> Pedidos", "Node.js · Express", "PostgreSQL 16 (orders, order_items)", "Crear pedido, cambiar de estado, tomar y entregar, resumen por estado", "9"],
                 ["<b>MS4</b> Agregador / Rastreo", "Python · FastAPI", "Sin base de datos", "Tracking de un pedido y dashboards por rol combinando MS1, MS2 y MS3", "5"],
                 ["<b>MS5</b> Analítico", "Python · FastAPI + boto3", "Amazon Athena (data lake)", "Top de restaurantes, métricas de usuarios y resumen de ventas", "5"]],
                [3.0 * cm, 2.9 * cm, 3.8 * cm, 5.6 * cm, W - 15.3 * cm]),
          Spacer(1, 6), P("3.1 Estados y reglas de negocio", "h2")]
    E += B(["<b>Pedido:</b> PEDIDO → ENVIADO (solo el admin dueño del restaurante) → ENTREGADO (solo el repartidor que lo tomó). Un pedido ENVIADO sin repartidor está disponible para que un delivery lo tome (<i>claim</i>); si dos lo intentan a la vez, solo uno lo obtiene.",
            "<b>Roles:</b> el registro público no permite crear admins. Cada admin está asociado a un restaurante (restaurante_id en el token) y solo puede tocar su propio menú y sus pedidos.",
            "<b>Reseñas:</b> puntuación de 1 a 5 y comentario obligatorio; al guardar una reseña se recalcula la calificación promedio del restaurante."])
    E += [P("3.2 Comunicación entre microservicios", "h2"),
          tabla([["Origen", "Destino", "Para qué"],
                 ["MS3 Pedidos", "MS2 Catálogo", "Validar que el plato existe y obtener su precio antes de guardar el pedido"],
                 ["MS3 Pedidos", "MS1 Usuarios", "Resolver nombres de los clientes de un restaurante (en bloques de 200 ids)"],
                 ["MS4 Agregador", "MS1, MS2 y MS3", "Componer el tracking del pedido y los dashboards de customer, delivery y admin; si un servicio falla responde con datos parciales o 502 controlado"],
                 ["MS5 Analítico", "Amazon Athena", "Consultas SQL sobre las vistas v_resumen_ventas_restaurante y v_metricas_usuarios"]],
                [3.0 * cm, 3.4 * cm, W - 6.4 * cm])]

    # ---------------- 4. Datos
    E += [P("4. Modelo de datos", "h1"),
          P("Cada base de datos SQL tiene dos tablas relacionadas y se documenta con su diagrama Entidad-Relación; la base NoSQL se documenta con la estructura JSON de su documento.")]
    E += [P("4.1 MySQL — MS1 (usuarios 1 : N direcciones)", "h2")] + img("er-mysql-ms1.png", W, "Figura 2. Diagrama E/R de MS1.")
    E += [P("4.2 PostgreSQL — MS3 (orders 1 : N order_items)", "h2")] + img("er-postgresql-ms3.png", W, "Figura 3. Diagrama E/R de MS3.")
    E += [PageBreak(), P("4.3 MongoDB — MS2 (restaurantes con platos y reseñas embebidos)", "h2")] + img("json-mongodb-ms2.png", W, "Figura 4. Estructura JSON de la colección restaurantes.")
    cnt = (ev or {}).get("counts", {})
    E += [P("4.4 Carga masiva de datos", "h2"),
          P("Los datos ficticios se insertaron una sola vez en cada base, con scripts incluidos en el repositorio. Los conteos son los del último snapshot cargado al data lake:"),
          tabla([["Base de datos", "Tabla / colección", "Script", "Registros"],
                 ["MySQL (MS1)", "usuarios", "seed.py (Faker)", fmt_num(cnt.get("usuarios", "20,000+"))],
                 ["MySQL (MS1)", "direcciones", "seed.py", fmt_num(cnt.get("direcciones", "—"))],
                 ["PostgreSQL (MS3)", "orders", "seed.js", fmt_num(cnt.get("orders", "20,000+"))],
                 ["PostgreSQL (MS3)", "order_items", "seed.js", fmt_num(cnt.get("order_items", "—"))],
                 ["MongoDB (MS2)", "restaurantes", "seed.js (mongosh)", fmt_num(cnt.get("mongodb", "20,000"))]],
                [4.0 * cm, 4.0 * cm, 4.6 * cm, W - 12.6 * cm])]

    # ---------------- 5. Frontend
    E += [P("5. Aplicación web (frontend)", "h1"),
          P(f"La aplicación es una SPA en <b>React con Vite</b>, con login y rutas protegidas por rol. Está desplegada en <b>AWS Amplify</b> "
            f'(<link href="{AMPLIFY}" color="#1155CC">{AMPLIFY}</link>) y consume la API únicamente por el API Gateway con HTTPS.'),
          tabla([["Rol", "Pantallas", "Servicios que consume"],
                 ["Customer", "Restaurantes (grilla paginada), menú con carrito y reseñas, mis pedidos y seguimiento del pedido", "MS1, MS2, MS3, MS4"],
                 ["Admin", "Panel de pedidos por estado (con los platos y cantidades de cada pedido), clientes, gestión del menú y analítica", "MS2, MS3, MS4, MS5"],
                 ["Delivery", "Pedidos disponibles, entregas en curso, marcar como entregado", "MS3, MS4"]],
                [2.4 * cm, W - 7.6 * cm, 5.2 * cm]), Spacer(1, 6),
          P("Pantallas de la aplicación", "h2"),
          galeria([("01-customer-restaurantes.png", "Customer: grilla de restaurantes paginada (20,000)"),
                   ("02-customer-menu-resenas.png", "Customer: menú, reseñas y carrito"),
                   ("03-admin-pedidos.png", "Admin: pedidos por estado con sus platos y cantidades"),
                   ("04-admin-analitica-athena.png", "Admin: analítica con datos de Athena")], W),
          P("Llamadas REST por microservicio", "h2"),
          tabla([["Servicio", "Llamadas en el frontend", "Ejemplos"],
                 ["MS1", str(api[1]), "login, registro, perfil, direcciones"],
                 ["MS2", str(api[2]), "listar restaurantes, ver menú, CRUD de platos, listar y crear reseñas"],
                 ["MS3", str(api[3]), "crear pedido, listar pedidos, cambiar de estado, tomar y entregar"],
                 ["MS4", str(api[4]), "tracking del pedido, dashboards de customer, delivery y admin"],
                 ["MS5", str(api[5]), "top de restaurantes, métricas de usuarios (consulta a Athena)"]],
                [2.4 * cm, 4.0 * cm, W - 6.4 * cm])]

    # ---------------- 6. Despliegue
    E += [P("6. Despliegue en AWS", "h1"), P("6.1 Recursos", "h2"),
          tabla([["Recurso", "Detalle"],
                 ["PP-App-Tier", "EC2 t2.micro, us-east-1a · NGINX + MS1…MS5 con docker compose · Elastic IP"],
                 ["PP-App-Tier-2", "EC2 t2.micro, us-east-1b · idéntica a la anterior"],
                 ["PP-DB-Tier", "EC2 t2.micro, us-east-1a · MySQL, PostgreSQL y MongoDB en contenedores con volúmenes persistentes"],
                 ["PP-Ingest-VM", "EC2 t2.micro, us-east-1a · 3 contenedores de ingesta en Python"],
                 ["pp-alb-interno", "Application Load Balancer interno, target group pp-app-tg (las dos VMs de App), health check GET /health cada 15 s"],
                 ["VPC Link + API Gateway", "HTTP API con integración privada (VPC Link) hacia el listener del ALB; protocolo HTTPS hacia el cliente"],
                 ["AWS Amplify", "Conectado al repositorio de GitHub (rama main): cada push compila y despliega la SPA con amplify.yml (Node 22)"],
                 ["S3 · Glue · Athena", "Bucket pp-ubereats-datalake-…; base ubereats_datalake y crawler pp-crawler; workgroup pp-workgroup"]],
                [4.0 * cm, W - 4.0 * cm]),
          P("6.2 Red y seguridad", "h2"),
          tabla([["Security group", "Entrada permitida"],
                 ["pp-alb-sg (ALB)", "TCP 80 solo desde pp-vpclink-sg"],
                 ["pp-app-tier-sg (VMs de App)", "TCP 80 desde el ALB (también desde internet, ver sección 11); SSH restringido a una IP de administración"],
                 ["pp-db-tier-sg (VM de BD)", "TCP 3306, 5432 y 27017 solo desde los SG de App e Ingesta; sin ningún puerto abierto a internet"],
                 ["pp-ingest-sg (Ingesta)", "Ninguna entrada"]],
                [5.0 * cm, W - 5.0 * cm]), Spacer(1, 4)]
    E += B(["La administración de las VMs se hace con AWS Systems Manager (SSH sobre SSM), sin exponer el puerto 22 de la VM de BD.",
            "Las instancias usan el rol IAM del laboratorio (LabInstanceProfile): no hay claves de AWS en el código ni en los contenedores.",
            "El acceso a las bases de datos se comprobó desde internet: 22, 3306, 5432 y 27017 no responden."])
    E += [P("6.3 Balanceo de carga", "h2"),
          P("El ALB interno reparte las peticiones entre las dos VMs de App. Se comprobó con la cabecera <i>X-Served-By</i>: en 30 peticiones consecutivas al mismo endpoint, "
            "14 las atendió app-1 y 13 app-2. Para verificar la tolerancia a fallos se detuvo NGINX en la segunda VM: el ALB la marcó como <i>unhealthy</i> en unos 30 s y "
            "las 30 peticiones siguientes las atendió app-1, todas con código 200. Al reiniciar NGINX, la VM volvió a rotación.")]
    E += [P("6.4 Cómo se actualiza", "h2"),
          P("El código se despliega con git pull y docker compose up --build en cada VM (en segundo plano, con swap de 2.5 GB porque las VMs t2.micro tienen 1 GB de RAM), "
            "y después se reinicia NGINX, que resuelve las IPs de los contenedores al arrancar. El frontend se despliega solo: cada push a la rama main de GitHub dispara en Amplify la compilación y el despliegue.")]
    E += [P("6.5 Documentación Swagger", "h2"),
          tabla([["Servicio", "URL de Swagger UI (a través del API Gateway)"],
                 ["MS1", GATEWAY + "/ms1/docs"], ["MS2", GATEWAY + "/ms2/swagger-ui.html"], ["MS3", GATEWAY + "/ms3/api-docs/"],
                 ["MS4", GATEWAY + "/ms4/docs"], ["MS5", GATEWAY + "/ms5/docs"]], [2.2 * cm, W - 2.2 * cm]),
          P("Detrás de NGINX y del API Gateway los servicios FastAPI viven bajo un prefijo (/ms1, /ms4, /ms5). NGINX envía la cabecera X-Forwarded-Prefix y un middleware "
            "la usa como root_path, de modo que Swagger UI carga el esquema y el botón «Try it out» arma bien las URLs.", "peq")]

    # ---------------- 7. Data Science
    E += [P("7. Data Science: ingesta, catálogo y analítica", "h1"), P("7.1 Ingesta y data lake", "h2"),
          P("La <b>MV de ingesta</b> (PP-Ingest-VM) ejecuta <b>tres contenedores Docker en Python</b>, uno por microservicio, con estrategia <i>pull</i> del 100 % de las tablas. "
            "Cada uno genera archivos CSV (MySQL y PostgreSQL) o JSONL (MongoDB) y los sube al bucket de S3 en una carpeta por tabla y fecha "
            "(raw/mysql/usuarios/dt=AAAA-MM-DD/…). Antes de subir, cada contenedor elimina el snapshot anterior de esa tabla (<i>full refresh</i>), para que Athena no sume dos particiones."),
          tabla([["Contenedor", "Origen", "Destino en S3", "Formato"],
                 ["ingest-mysql", "usuarios, direcciones (MS1)", "raw/mysql/usuarios/ · raw/mysql/direcciones/", "CSV"],
                 ["ingest-postgres", "orders, order_items (MS3)", "raw/postgres/orders/ · raw/postgres/order_items/", "CSV"],
                 ["ingest-mongodb", "restaurantes (MS2)", "raw/mongodb/restaurantes/", "JSONL"]],
                [3.2 * cm, 4.3 * cm, 7.0 * cm, W - 14.5 * cm]),
          P("7.2 Catálogo de datos en AWS Glue", "h2"),
          P("Un crawler (pp-crawler) recorre el bucket y crea una tabla por cada carpeta: <b>usuarios, direcciones, orders, order_items y mongodb</b> (el crawler nombró así a la colección de restaurantes). "
            "Los archivos no tienen claves foráneas; las relaciones del diagrama son lógicas y se resuelven con JOIN en Athena.")]
    E += img("er-catalogo-glue.png", W, "Figura 5. Diagrama E/R de las tablas del catálogo de Glue.", alto_max=9.6 * cm)
    E += [P("Hallazgos al catalogar: (1) el _id de MongoDB llegó como struct {\"$oid\"} y se accede con r._id.\"$oid\"; (2) es_principal (booleano en MySQL) llegó como bigint 0/1; "
           "(3) Spring Data agrega el campo _class a los documentos de MongoDB y el crawler agrega la partición partition_0; (4) el modelo de usuarios no tiene fecha de nacimiento, por lo que la vista de métricas usa la antigüedad de la cuenta en lugar de una edad inventada.", "peq")]
    E += [PageBreak(), P("7.3 Consultas y vistas en Amazon Athena", "h2")]
    if ev:
        E.append(P(f"Las consultas se ejecutaron en el workgroup pp-workgroup sobre la base ubereats_datalake. Cada resultado indica el <b>ID de ejecución de Athena</b>, "
                   f"que puede verificarse en el historial de consultas de la consola. Conteos del catálogo: " +
                   ", ".join(f"{k} = {fmt_num(v)}" for k, v in ev["counts"].items() if k in ("usuarios", "orders", "order_items", "mongodb")) + "."))
        tit = [("Ventas por restaurante", "Une orders, order_items y mongodb (3 tablas) para calcular pedidos y ventas totales por restaurante."),
               ("Clientes con mayor gasto", "Une orders y usuarios para obtener el nombre real de los clientes que más gastan."),
               ("Platos más vendidos", "Une order_items, orders y mongodb (3 tablas) para obtener las unidades vendidas por plato y restaurante."),
               ("Ciudad registrada vs. dirección de entrega", "Une orders, usuarios y direcciones (LEFT JOIN) para comparar la ciudad del cliente con el destino del pedido.")]
        for i, q in enumerate(ev["queries"]):
            E.append(KeepTogether(bloque_consulta(i + 1, tit[i][0], tit[i][1], q)))
        E.append(PageBreak())
        E.append(P("Vistas creadas", "h2"))
        E.append(P("Se crearon dos vistas, consumidas por el microservicio MS5. Su resultado se muestra con un SELECT sobre cada vista."))
        for v in ev["views"]:
            bl = [P(v["view"], "h2"), Preformatted(v["create_sql"].strip(), S["codigo"]), Spacer(1, 4)]
            filas = [v["header"]] + [[fmt_num(c) if re.fullmatch(r"-?\d+(\.\d+)?(E\d+)?", c or "") else c for c in r] for r in v["rows"][:6]]
            bl.append(tabla(filas, [W / len(v["header"])] * len(v["header"])))
            bl.append(P(f"CREATE VIEW: {v['create_id']} · SELECT: {v['id']} · {v['ms'] / 1000:.1f} s.", "peq"))
            bl += captura_athena(f"vista-{1 if v['view'] == 'v_resumen_ventas_restaurante' else 2}.png", 17.4 * cm)
            E.append(KeepTogether(bl))
    else:
        E.append(P("Evidencia de Athena pendiente de ejecución (falta athena_evidence.json)."))

    # ---------------- 8. Paginado
    E += [P("8. Paginado y rendimiento", "h1"),
          P("Con más de 20,000 registros por base, devolver listados completos era inviable (cientos de KB o MB por petición y miles de elementos en el DOM). "
            "Se añadió un <b>paginado opcional en la misma ruta</b>, que no rompe a los consumidores existentes:"),
          ] + B(["Sin <i>page</i> ni <i>page_size</i> la respuesta es la de siempre (un arreglo con todo).",
                 "Con ellos la respuesta es {items, page, page_size, total, total_pages}. page_size vale 20 por defecto y se limita a 100; valores inválidos dan 400 (Express y Spring) o 422 (FastAPI).",
                 "El total también viaja en la cabecera X-Total-Count (expuesta por CORS). Los dashboards de MS4 y la analítica de MS5 tienen su propio modo paginado; MS3 agrega /orders/summary para contar pedidos por estado sin traer las filas."]) + [
          Spacer(1, 4),
          tabla([["Petición", "Sin paginar", "Paginada"],
                 ["Dashboard admin (MS4)", "4.2 MB · 0.84 s", "4 KB · 60 ms"],
                 ["Usuarios (MS1)", "6.6 MB · 2.3 s", "página de 20: 14 ms"],
                 ["Restaurantes (MS2, 20,000)", "21 MB · 1.0 s", "página de 12: 12 KB · 14 ms"],
                 ["Pedidos de un restaurante (MS3)", "miles de filas", "página de 10: ≈ 10 ms"],
                 ["Métricas de usuarios (MS5)", "consulta completa a Athena", "página de 10: ≈ 3 a 4 s (latencia de Athena)"]],
                [6.0 * cm, 5.4 * cm, W - 11.4 * cm]),
          P("Mediciones tomadas en el entorno local con unos 40 mil pedidos (MS2 con sus 20,000 restaurantes); en AWS las respuestas son de un orden similar.", "peq")]

    # ---------------- 9. Pruebas
    E += [P("9. Pruebas y validación", "h1"),
          tabla([["Prueba", "Alcance", "Resultado"],
                 ["Colección Postman / Newman", "72 requests sobre los 5 servicios: flujo completo, casos de error (400, 401, 422) y modos con y sin paginado", "72 ejecutadas · 66 aserciones · 0 fallos, en local y a través del API Gateway"],
                 ["Navegador (Playwright)", "Flujos por rol en Chromium contra la URL de Amplify: pestañas y paginado del admin, pool del delivery, grilla de restaurantes, pedido, tracking y reseñas", "Todas las comprobaciones correctas y sin errores de consola"],
                 ["Balanceo y failover", "30 peticiones repartidas; NGINX detenido en una VM", "14 / 13 entre las dos VMs; con una caída, 30 de 30 respuestas 200"],
                 ["Aislamiento de la BD", "Sondeo de puertos 22, 3306, 5432 y 27017 desde internet", "Todos cerrados"]],
                [3.6 * cm, 8.0 * cm, W - 11.6 * cm])]

    # ---------------- 10. Seguridad
    E += [P("10. Seguridad", "h1")] + B([
        "Autenticación con JWT (HS256, secreto de al menos 32 bytes) y contraseñas con bcrypt; autorización por rol en cada endpoint sensible.",
        "Red: BD sin puertos abiertos a internet, ALB interno, ingesta sin entradas y administración sin SSH público.",
        "Sin secretos en el repositorio: los archivos .env están en .gitignore y en AWS se usa el rol de la instancia.",
        "Observación: como la ingesta extrae el 100 % de las tablas, password_hash llega al data lake. En producción se excluiría o enmascararía esa columna antes de subirla."])

    # ---------------- 11. Limitaciones
    E += [P("11. Limitaciones y trabajo futuro", "h1")] + B([
        "<b>Puerto 80 de las VMs de App.</b> El tráfico de producción entra por API Gateway → ALB, pero las VMs aún aceptan el puerto 80 desde internet (por ejemplo por la IP elástica). Cerrarlo es una regla de red.",
        "<b>Recursos limitados.</b> Las VMs t2.micro (1 GB de RAM) funcionan con swap; en producción convendría t3.small o superior.",
        "<b>Reseñas.</b> MS2 toma el usuario_id del cuerpo de la petición y no del token; debería derivarse del JWT.",
        "<b>Data lake.</b> La ingesta es manual (bajo demanda); se podría programar con EventBridge y automatizar el crawler."])

    # ---------------- 12. Lecciones
    E += [P("12. Lecciones aprendidas", "h1")] + B([
        "En AWS Academy Learner Lab las credenciales y las sesiones vencen, y al terminar la sesión las instancias quedan detenidas; los servicios se diseñaron para reiniciar solos (restart: unless-stopped).",
        "La plataforma limita a 9 el número de instancias de la cuenta y cuenta también las detenidas: las instancias nuevas se terminan a los segundos si se supera el límite.",
        "La AMI de Cloud9 trae Apache (puerto 80) y MySQL (3306) instalados: hay que deshabilitarlos antes de levantar NGINX y la base de datos.",
        "NGINX resuelve las IPs de los contenedores al arrancar: tras recrear un contenedor hay que reiniciarlo.",
        "Un crawler de Glue nombra las tablas según la estructura de S3 y puede convertir tipos (booleano a bigint, ObjectId a struct): conviene revisar el catálogo antes de escribir consultas."])

    # ---------------- Anexos
    E += [PageBreak(), P("Anexo A. Enlaces", "h1"),
          tabla([["Elemento", "Enlace"],
                 ["Repositorio público (código fuente de los 5 microservicios, frontend, ingesta y diagramas)", f'<link href="{REPO}" color="#1155CC">{REPO}</link>'],
                 ["Aplicación web (AWS Amplify)", f'<link href="{AMPLIFY}" color="#1155CC">{AMPLIFY}</link>'],
                 ["API pública (API Gateway, HTTPS)", f'<link href="{GATEWAY}" color="#1155CC">{GATEWAY}</link>'],
                 ["Colección Postman", "postman/delivery-cloud.postman_collection.json (en el repositorio)"],
                 ["Diagramas editables (draw.io)", "infra/diagramas/proyecto-delivery-cloud.drawio (en el repositorio)"]],
                [7.4 * cm, W - 7.4 * cm]),
          P("Anexo B. Cómo reproducir el proyecto", "h1"),
          P("En local (cualquier persona que clone el repositorio):"),
          Preformatted("git clone " + REPO + ".git\ncd ProeyctParcialProp\ncp .env.example .env\ndocker compose -f docker-compose.dev.yml up -d --build\n"
                       "# servicios en http://localhost/ms1 ... /ms5\n"
                       "# Swagger: /ms1/docs  /ms2/swagger-ui.html  /ms3/api-docs  /ms4/docs  /ms5/docs\n"
                       "# frontend:  cd frontend && npm install && npm run dev\n"
                       "# pruebas:   npx newman run postman/delivery-cloud.postman_collection.json --env-var \"base_url=http://localhost\"", S["codigo"]),
          Spacer(1, 6),
          P("En AWS: las VMs de App usan docker-compose.app.yml, la VM de BD docker-compose.db.yml y la de ingesta data-science/docker-compose.ingest.yml. "
            "Los pasos de red (security groups, ALB, VPC Link y API Gateway) y los comandos de despliegue están descritos en el README del repositorio.")]
    doc.build(E)
    print("OK", SALIDA)


if __name__ == "__main__":
    construir(os.environ.get("AUTORES"))
