#!/usr/bin/env python3
"""Genera los diagramas del proyecto a partir de una sola definición:
  - proyecto-delivery-cloud.drawio  (5 páginas, editable en draw.io / diagrams.net)
  - <nombre>.svg y <nombre>.png     (para el informe y la presentación)

Uso: python3 generar_diagramas.py [ruta/a/glue_tables.json]
Requiere inkscape para exportar el PNG. Si se pasa glue_tables.json (esquema real del catálogo
de Glue) el diagrama E/R de Glue usa esas columnas; si no, usa los tipos esperados.
"""
import html
import json
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
INK = "#232F3E"
GRIS = "#5F6B7A"
MONO = "DejaVu Sans Mono, Courier New, monospace"
SANS = "Liberation Sans, Arial, Helvetica, sans-serif"

# Paleta inspirada en las categorías de iconos de AWS
C = {
    "front": ("#FDECEF", "#DD344C"),
    "apigw": ("#FDE7F1", "#E7157B"),
    "red": ("#F1E9FF", "#8C4FFF"),
    "ec2": ("#FFF3E0", "#ED7100"),
    "db": ("#E6E9FB", "#3B48CC"),
    "s3": ("#E8F5E1", "#3F8624"),
    "analytics": ("#F1E9FF", "#8C4FFF"),
    "docker": ("#FFFFFF", "#6B7785"),
    "user": ("#F2F3F3", "#5F6B7A"),
    "nota": ("#FFFBE6", "#D6B656"),
}


def esc(s):
    return html.escape(str(s), quote=True)


class Diagrama:
    def __init__(self, nombre, titulo, w, h):
        self.nombre, self.titulo, self.w, self.h = nombre, titulo, w, h
        self.items = []
        self.oy = 0  # desplazamiento vertical de todo el contenido (deja libre la franja del título)

    def add(self, **kw):
        self.items.append(kw)
        return kw

    # --- primitivas -------------------------------------------------
    def caja(self, x, y, w, h, texto, color="docker", fs=13, negrita_primera=True, dash=False, r=8, sw=1.6, mono=False, align="middle"):
        self.add(t="caja", x=x, y=y + self.oy, w=w, h=h, texto=texto, color=color, fs=fs, np=negrita_primera, dash=dash, r=r, sw=sw, mono=mono, align=align)

    def grupo(self, x, y, w, h, titulo, stroke, fill="none", dash=False, fs=14):
        self.add(t="grupo", x=x, y=y + self.oy, w=w, h=h, titulo=titulo, stroke=stroke, fill=fill, dash=dash, fs=fs)

    def texto(self, x, y, texto, fs=13, negrita=False, color=INK, anchor="start", mono=False):
        self.add(t="texto", x=x, y=y + self.oy, texto=texto, fs=fs, negrita=negrita, color=color, anchor=anchor, mono=mono)

    def flecha(self, pts, label=None, lpos=None, dash=False, color=INK, ini=None, fin="flecha", fs=12):
        pts = [(px, py + self.oy) for px, py in pts]
        lpos = (lpos[0], lpos[1] + self.oy) if lpos else None
        self.add(t="flecha", pts=pts, label=label, lpos=lpos, dash=dash, color=color, ini=ini, fin=fin, fs=fs)

    def tabla(self, x, y, w, titulo, filas, head=("#3B48CC"), sub=None):
        """filas: (tag, nombre, tipo). Devuelve un objeto para calcular puntos de anclaje."""
        t = Tabla(x, y + self.oy, w, titulo, filas, head, sub)
        self.add(t="tabla", obj=t)
        return t


class Tabla:
    HEAD, ROW = 32, 26

    def __init__(self, x, y, w, titulo, filas, head, sub):
        self.x, self.y, self.w, self.titulo, self.filas, self.head, self.sub = x, y, w, titulo, filas, head, sub

    @property
    def h(self):
        return self.HEAD + self.ROW * len(self.filas)

    def fila_y(self, i):
        return self.y + self.HEAD + self.ROW * i + self.ROW / 2

    def idx(self, nombre):
        return [f[1] for f in self.filas].index(nombre)

    def izq(self, nombre=None):
        return (self.x, self.fila_y(self.idx(nombre)) if nombre else self.y + self.h / 2)

    def der(self, nombre=None):
        return (self.x + self.w, self.fila_y(self.idx(nombre)) if nombre else self.y + self.h / 2)

    def arriba(self, dx=0.5):
        return (self.x + self.w * dx, self.y)

    def abajo(self, dx=0.5):
        return (self.x + self.w * dx, self.y + self.h)


# ====================================================================
# Renderizado SVG
# ====================================================================
def ancho_txt(s, fs, mono=False):
    return len(s) * fs * (0.6 if mono else 0.55)


def svg_texto(x, y, s, fs, negrita=False, color=INK, anchor="start", mono=False):
    fam = MONO if mono else SANS
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{fs}" '
            f'font-weight="{"700" if negrita else "400"}" fill="{color}" text-anchor="{anchor}" xml:space="preserve">{esc(s)}</text>')


def svg_marca_er(p, d, tipo, color):
    """Marca de cardinalidad en el punto p; d = vector unitario que apunta HACIA la entidad."""
    x, y = p
    dx, dy = d
    px, py = -dy, dx
    out = []
    if tipo == "uno":
        for off in (10, 16):
            cx, cy = x - dx * off, y - dy * off
            out.append(f'<line x1="{cx + px * 7:.1f}" y1="{cy + py * 7:.1f}" x2="{cx - px * 7:.1f}" y2="{cy - py * 7:.1f}" stroke="{color}" stroke-width="2"/>')
    elif tipo == "muchos":
        bx, by = x - dx * 16, y - dy * 16
        for s in (-1, 0, 1):
            out.append(f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{x + px * 8 * s:.1f}" y2="{y + py * 8 * s:.1f}" stroke="{color}" stroke-width="2"/>')
    return "".join(out)


def unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = (dx * dx + dy * dy) ** 0.5 or 1
    return dx / n, dy / n


def a_svg(d):
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{d.w}" height="{d.h}" viewBox="0 0 {d.w} {d.h}">',
         '<defs><marker id="fl" markerWidth="12" markerHeight="10" refX="11" refY="5" orient="auto" markerUnits="userSpaceOnUse">'
         '<path d="M0,0 L12,5 L0,10 z" fill="context-stroke"/></marker></defs>',
         f'<rect width="{d.w}" height="{d.h}" fill="#FFFFFF"/>',
         svg_texto(24, 34, d.titulo, 21, True)]
    for it in d.items:
        t = it["t"]
        if t == "grupo":
            dash = ' stroke-dasharray="7 5"' if it["dash"] else ""
            o.append(f'<rect x="{it["x"]}" y="{it["y"]}" width="{it["w"]}" height="{it["h"]}" rx="10" fill="{it["fill"]}" stroke="{it["stroke"]}" stroke-width="1.6"{dash}/>')
            o.append(svg_texto(it["x"] + 12, it["y"] + 22, it["titulo"], it["fs"], True, it["stroke"]))
        elif t == "caja":
            fill, stroke = C[it["color"]]
            dash = ' stroke-dasharray="6 4"' if it["dash"] else ""
            o.append(f'<rect x="{it["x"]}" y="{it["y"]}" width="{it["w"]}" height="{it["h"]}" rx="{it["r"]}" fill="{fill}" stroke="{stroke}" stroke-width="{it["sw"]}"{dash}/>')
            lineas = it["texto"].split("\n")
            lh = it["fs"] * 1.3
            if it["align"] == "middle":
                y0 = it["y"] + it["h"] / 2 - lh * (len(lineas) - 1) / 2 + it["fs"] * 0.35
                for i, ln in enumerate(lineas):
                    o.append(svg_texto(it["x"] + it["w"] / 2, y0 + i * lh, ln, it["fs"], it["np"] and i == 0, INK, "middle", it["mono"]))
            else:
                y0 = it["y"] + 12 + it["fs"]
                for i, ln in enumerate(lineas):
                    o.append(svg_texto(it["x"] + 12, y0 + i * lh, ln, it["fs"], it["np"] and i == 0, INK, "start", it["mono"]))
        elif t == "texto":
            for i, ln in enumerate(it["texto"].split("\n")):
                o.append(svg_texto(it["x"], it["y"] + i * it["fs"] * 1.35, ln, it["fs"], it["negrita"], it["color"], it["anchor"], it["mono"]))
        elif t == "tabla":
            tb = it["obj"]
            o.append(f'<rect x="{tb.x}" y="{tb.y}" width="{tb.w}" height="{tb.h}" rx="6" fill="#FFFFFF" stroke="{tb.head}" stroke-width="1.8"/>')
            o.append(f'<path d="M{tb.x},{tb.y + tb.HEAD} L{tb.x},{tb.y + 6} Q{tb.x},{tb.y} {tb.x + 6},{tb.y} L{tb.x + tb.w - 6},{tb.y} Q{tb.x + tb.w},{tb.y} {tb.x + tb.w},{tb.y + 6} L{tb.x + tb.w},{tb.y + tb.HEAD} Z" fill="{tb.head}"/>')
            o.append(svg_texto(tb.x + 12, tb.y + 21, tb.titulo, 15, True, "#FFFFFF"))
            if tb.sub:
                o.append(svg_texto(tb.x + tb.w - 10, tb.y + 21, tb.sub, 11, False, "#FFFFFF", "end"))
            for i, (tag, nom, tipo) in enumerate(tb.filas):
                ry = tb.y + tb.HEAD + i * tb.ROW
                if i % 2 == 1:
                    o.append(f'<rect x="{tb.x + 1}" y="{ry}" width="{tb.w - 2}" height="{tb.ROW}" fill="#F6F7F9"/>')
                col = {"PK": "#B45F06", "FK": "#1155CC", "UQ": "#674EA7"}.get(tag, GRIS)
                o.append(svg_texto(tb.x + 10, ry + 18, tag, 11, True, col))
                o.append(svg_texto(tb.x + 46, ry + 18, nom, 13, tag == "PK"))
                o.append(svg_texto(tb.x + tb.w - 10, ry + 18, tipo, 12, False, GRIS, "end", True))
        elif t == "flecha":
            pts = it["pts"]
            dash = ' stroke-dasharray="7 5"' if it["dash"] else ""
            pathd = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
            mk = ' marker-end="url(#fl)"' if it["fin"] == "flecha" else ""
            o.append(f'<path d="{pathd}" fill="none" stroke="{it["color"]}" stroke-width="1.8"{dash}{mk}/>')
            if it["ini"] in ("uno", "muchos"):
                o.append(svg_marca_er(pts[0], unit(pts[1], pts[0]), it["ini"], it["color"]))
            if it["fin"] in ("uno", "muchos"):
                o.append(svg_marca_er(pts[-1], unit(pts[-2], pts[-1]), it["fin"], it["color"]))
            if it["label"]:
                lx, ly = it["lpos"]
                lineas = it["label"].split("\n")
                w = max(ancho_txt(s, it["fs"]) for s in lineas) + 10
                hh = len(lineas) * it["fs"] * 1.3 + 4
                o.append(f'<rect x="{lx - w / 2:.1f}" y="{ly - hh / 2:.1f}" width="{w:.1f}" height="{hh:.1f}" fill="#FFFFFF" fill-opacity="0.92"/>')
                for i, ln in enumerate(lineas):
                    o.append(svg_texto(lx, ly - hh / 2 + it["fs"] + i * it["fs"] * 1.3 - 1, ln, it["fs"], False, it["color"], "middle"))
    o.append("</svg>")
    return "\n".join(o)


# ====================================================================
# Renderizado draw.io (mxGraph)
# ====================================================================
def a_drawio(d):
    cells, n = [], [1]

    def nid():
        n[0] += 1
        return f"c{n[0]}"

    def vertice(x, y, w, h, valor, estilo):
        cells.append(f'<mxCell id="{nid()}" value="{esc(valor)}" style="{estilo}" vertex="1" parent="1">'
                     f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')

    def lineas_html(txt, primera_negrita):
        ls = txt.split("\n")
        if primera_negrita and ls:
            ls[0] = f"<b>{html.escape(ls[0])}</b>"
            ls[1:] = [html.escape(x) for x in ls[1:]]
        else:
            ls = [html.escape(x) for x in ls]
        ls = ["&nbsp;" * (len(x) - len(x.lstrip(" "))) + x.lstrip(" ") for x in ls]
        return "<br>".join(ls)

    vertice(24, 12, d.w - 48, 34, d.titulo, f"text;html=0;fontSize=20;fontStyle=1;fontColor={INK};align=left;verticalAlign=middle;strokeColor=none;fillColor=none;")
    ER = {"uno": "ERmandOne", "muchos": "ERmany"}
    for it in d.items:
        t = it["t"]
        if t == "grupo":
            dash = "dashed=1;" if it["dash"] else ""
            fill = it["fill"] if it["fill"] != "none" else "none"
            vertice(it["x"], it["y"], it["w"], it["h"], it["titulo"],
                    f"rounded=1;arcSize=3;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={it['stroke']};strokeWidth=1.6;{dash}"
                    f"verticalAlign=top;align=left;spacingLeft=10;spacingTop=2;fontStyle=1;fontSize={it['fs']};fontColor={it['stroke']};")
        elif t == "caja":
            fill, stroke = C[it["color"]]
            dash = "dashed=1;" if it["dash"] else ""
            fam = "fontFamily=Courier New;" if it["mono"] else ""
            al = "align=left;spacingLeft=10;verticalAlign=top;spacingTop=6;" if it["align"] != "middle" else "align=center;verticalAlign=middle;"
            vertice(it["x"], it["y"], it["w"], it["h"], lineas_html(it["texto"], it["np"]),
                    f"rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};strokeWidth={it['sw']};{dash}{fam}{al}fontSize={it['fs']};fontColor={INK};")
        elif t == "texto":
            fam = "fontFamily=Courier New;" if it["mono"] else ""
            al = {"start": "left", "middle": "center", "end": "right"}[it["anchor"]]
            nl = it["texto"].count("\n") + 1
            w = max(ancho_txt(s, it["fs"], it["mono"]) for s in it["texto"].split("\n")) + 16
            x = it["x"] if it["anchor"] == "start" else (it["x"] - w / 2 if it["anchor"] == "middle" else it["x"] - w)
            vertice(x, it["y"] - it["fs"], w, nl * it["fs"] * 1.4 + 6, lineas_html(it["texto"], it["negrita"]),
                    f"text;html=1;strokeColor=none;fillColor=none;{fam}align={al};verticalAlign=top;whiteSpace=nowrap;fontSize={it['fs']};fontColor={it['color']};")
        elif t == "tabla":
            tb = it["obj"]
            vertice(tb.x, tb.y, tb.w, tb.h, "", f"rounded=1;arcSize=3;html=1;fillColor=#FFFFFF;strokeColor={tb.head};strokeWidth=1.8;")
            vertice(tb.x, tb.y, tb.w, tb.HEAD, tb.titulo + (f"  ({tb.sub})" if tb.sub else ""),
                    f"rounded=1;arcSize=12;html=1;fillColor={tb.head};strokeColor={tb.head};fontColor=#FFFFFF;fontStyle=1;fontSize=15;align=left;spacingLeft=10;")
            for i, (tag, nom, tipo) in enumerate(tb.filas):
                ry = tb.y + tb.HEAD + i * tb.ROW
                if i % 2 == 1:
                    vertice(tb.x + 1, ry, tb.w - 2, tb.ROW, "", "html=1;fillColor=#F6F7F9;strokeColor=none;")
                col = {"PK": "#B45F06", "FK": "#1155CC", "UQ": "#674EA7"}.get(tag, GRIS)
                vertice(tb.x + 4, ry, 40, tb.ROW, tag, f"text;html=1;align=left;verticalAlign=middle;fontStyle=1;fontSize=11;fontColor={col};strokeColor=none;fillColor=none;")
                vertice(tb.x + 44, ry, tb.w * 0.5, tb.ROW, nom, f"text;html=1;align=left;verticalAlign=middle;fontSize=13;{'fontStyle=1;' if tag == 'PK' else ''}strokeColor=none;fillColor=none;")
                vertice(tb.x + tb.w * 0.45, ry, tb.w * 0.55 - 8, tb.ROW, html.escape(tipo), f"text;html=1;align=right;verticalAlign=middle;fontSize=12;fontFamily=Courier New;fontColor={GRIS};strokeColor=none;fillColor=none;")
        elif t == "flecha":
            pts = it["pts"]
            dash = "dashed=1;" if it["dash"] else ""
            ini = f"startArrow={ER[it['ini']]};startFill=0;" if it["ini"] in ER else "startArrow=none;"
            fin = f"endArrow={ER[it['fin']]};endFill=0;" if it["fin"] in ER else ("endArrow=block;endFill=1;" if it["fin"] == "flecha" else "endArrow=none;")
            mid = "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in pts[1:-1])
            arr = f'<Array as="points">{mid}</Array>' if mid else ""
            cells.append(f'<mxCell id="{nid()}" style="edgeStyle=none;html=1;rounded=0;strokeColor={it["color"]};strokeWidth=1.8;{dash}{ini}{fin}" edge="1" parent="1">'
                         f'<mxGeometry relative="1" as="geometry"><mxPoint x="{pts[0][0]}" y="{pts[0][1]}" as="sourcePoint"/>'
                         f'<mxPoint x="{pts[-1][0]}" y="{pts[-1][1]}" as="targetPoint"/>{arr}</mxGeometry></mxCell>')
            if it["label"]:
                lx, ly = it["lpos"]
                ls = it["label"].split("\n")
                w = max(ancho_txt(s, it["fs"]) for s in ls) + 12
                vertice(lx - w / 2, ly - len(ls) * it["fs"] * 0.75, w, len(ls) * it["fs"] * 1.4 + 4, "<br>".join(html.escape(s) for s in ls),
                        f"text;html=1;align=center;verticalAlign=middle;whiteSpace=nowrap;fontSize={it['fs']};fontColor={it['color']};fillColor=#FFFFFF;strokeColor=none;opacity=90;")
    return (f'<diagram name="{esc(d.nombre)}" id="{esc(d.nombre)}"><mxGraphModel dx="{d.w}" dy="{d.h}" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" '
            f'arrows="1" fold="1" page="1" pageScale="1" pageWidth="{d.w}" pageHeight="{d.h}" math="0" shadow="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/>'
            + "".join(cells) + "</root></mxGraphModel></diagram>")


# ====================================================================
# Definición de los diagramas
# ====================================================================
def er_mysql():
    d = Diagrama("ER MySQL (MS1)", "Diagrama Entidad-Relación — MS1 Usuarios/Auth · MySQL 8.0 · base ms1_usuarios", 1000, 520)
    us = d.tabla(40, 80, 380, "usuarios", [
        ("PK", "id", "INT AUTO_INCREMENT"), ("", "nombre", "VARCHAR(150) NOT NULL"), ("UQ", "email", "VARCHAR(150) NOT NULL"),
        ("", "password_hash", "VARCHAR(255) NOT NULL"), ("", "telefono", "VARCHAR(30) NULL"),
        ("", "rol", "ENUM(customer,delivery,admin)"), ("", "restaurante_id", "VARCHAR(50) NULL"),
        ("", "fecha_registro", "DATETIME DEFAULT NOW()")], "#3B48CC", "20,009 filas")
    di = d.tabla(580, 80, 380, "direcciones", [
        ("PK", "id", "INT AUTO_INCREMENT"), ("FK", "usuario_id", "INT NOT NULL"), ("", "calle", "VARCHAR(255) NOT NULL"),
        ("", "ciudad", "VARCHAR(100) NOT NULL"), ("", "referencia", "VARCHAR(255) NULL"),
        ("", "lat", "DECIMAL(10,7) NULL"), ("", "lng", "DECIMAL(10,7) NULL"), ("", "es_principal", "TINYINT(1) DEFAULT 0")], "#3B48CC", "17,025 filas")
    a, b = us.der("id"), di.izq("usuario_id")
    d.flecha([a, (500, a[1]), (500, b[1]), b], "1 : N", (500, (a[1] + b[1]) / 2 - 22), ini="uno", fin="muchos", fs=13)
    d.texto(500, b[1] + 30, "ON DELETE CASCADE", 11, False, GRIS, "middle")
    d.caja(40, 372, 920, 118,
           "Reglas del modelo\n"
           "• Un usuario tiene de 0 a N direcciones (usuarios 1 : N direcciones); la FK usuario_id elimina en cascada.\n"
           "• email es único; rol restringe a customer, delivery o admin. restaurante_id solo lo usa el admin y es una referencia\n"
           "  lógica al _id del restaurante en MongoDB (no hay FK entre motores).\n"
           "• Carga masiva única con seed.py (Faker): 20,000+ usuarios. Índices: idx_usuarios_rol, idx_direcciones_usuario.",
           "nota", 13, True, align="izq")
    return d


def er_postgres():
    d = Diagrama("ER PostgreSQL (MS3)", "Diagrama Entidad-Relación — MS3 Pedidos · PostgreSQL 16 · base ms3_pedidos", 1000, 540)
    o = d.tabla(40, 80, 400, "orders", [
        ("PK", "id", "SERIAL"), ("", "customer_id", "INTEGER NOT NULL"), ("", "restaurant_id", "VARCHAR(50) NOT NULL"),
        ("", "delivery_id", "INTEGER NULL"), ("", "direccion_entrega", "TEXT NOT NULL"),
        ("", "status", "VARCHAR(20) CHECK(3 estados)"), ("", "total", "NUMERIC(10,2) DEFAULT 0"),
        ("", "created_at", "TIMESTAMP DEFAULT NOW()")], "#3B48CC", "20,012 filas")
    it = d.tabla(600, 80, 360, "order_items", [
        ("PK", "id", "SERIAL"), ("FK", "order_id", "INTEGER NOT NULL"), ("", "dish_id", "VARCHAR(50) NOT NULL"),
        ("", "nombre_plato", "VARCHAR(255) NOT NULL"), ("", "cantidad", "INTEGER CHECK (> 0)"),
        ("", "precio_unitario", "NUMERIC(10,2)")], "#3B48CC", "26,566 filas")
    a, b = o.der("id"), it.izq("order_id")
    d.flecha([a, (520, a[1]), (520, b[1]), b], "1 : N", (520, (a[1] + b[1]) / 2 - 22), ini="uno", fin="muchos", fs=13)
    d.texto(520, b[1] + 30, "ON DELETE CASCADE", 11, False, GRIS, "middle")
    d.caja(40, 336, 920, 168,
           "Reglas del modelo\n"
           "• Un pedido tiene de 1 a N ítems (orders 1 : N order_items). Al crearse, MS3 valida cada plato contra MS2 y guarda\n"
           "  nombre y precio unitario como fotografía del momento de la compra.\n"
           "• status ∈ {PEDIDO, ENVIADO, ENTREGADO}: PEDIDO → ENVIADO (admin del restaurante) → ENTREGADO (repartidor asignado).\n"
           "• customer_id / delivery_id (MySQL) y restaurant_id (MongoDB) son referencias lógicas entre microservicios, sin FK.\n"
           "• Índices: idx_orders_customer, idx_orders_restaurant(restaurant_id, status), idx_orders_delivery, idx_order_items_order.\n"
           "• Carga masiva única con seed.js: 20,000+ pedidos con sus ítems.",
           "nota", 13, True, align="izq")
    return d


def json_mongo():
    d = Diagrama("JSON MongoDB (MS2)", "Estructura JSON — MS2 Catálogo de Restaurantes · MongoDB 7 · colección ms2_catalogo.restaurantes", 1260, 720)
    r = d.tabla(40, 80, 400, "restaurantes  (documento)", [
        ("PK", "_id", "ObjectId"), ("", "nombre", "string"), ("", "categoria", "string"), ("", "ciudad", "string"),
        ("", "direccion", "string"), ("", "admin_id", "int | null"), ("", "calificacion_promedio", "double"),
        ("", "platos", "array<Plato>"), ("", "resenas", "array<Resena>")], "#3F8624", "20,000 docs")
    p = d.tabla(40, 420, 400, "Plato  (embebido)", [
        ("", "id", "string  (p1, p2…)"), ("", "nombre", "string"), ("", "descripcion", "string"),
        ("", "precio", "double"), ("", "categoria", "string"), ("", "disponible", "bool")], "#6B8E23")
    rs = d.tabla(520, 420, 300, "Resena  (embebido)", [
        ("", "usuario_id", "int  (ref. MySQL)"), ("", "comentario", "string"), ("", "puntuacion", "int  (1–5)"),
        ("", "fecha", "date")], "#6B8E23")
    fin = r.y + r.h
    d.flecha([(140, fin), (140, p.y)], "platos[]  ·  1 : N", (250, fin + 34), ini="uno", fin="muchos", fs=12)
    d.flecha([(380, fin), (380, fin + 24), (670, fin + 24), (670, rs.y)], "resenas[]  ·  1 : N", (525, fin + 8), ini="uno", fin="muchos", fs=12)
    ejemplo = (
        '{\n'
        '  "_id": ObjectId("6ab06fe698e3490c73a1e3e9"),\n'
        '  "nombre": "Casa Fresco #3",\n'
        '  "categoria": "Postres y Cafe",\n'
        '  "ciudad": "Huancayo",\n'
        '  "direccion": "Jr. Cusco 764",\n'
        '  "admin_id": null,\n'
        '  "calificacion_promedio": 4.5,\n'
        '  "platos": [\n'
        '    { "id": "p1", "nombre": "Cheesecake",\n'
        '      "descripcion": "Cheesecake de la casa",\n'
        '      "precio": 16.2, "categoria": "Fondos",\n'
        '      "disponible": true },\n'
        '    { "id": "p2", "nombre": "Brownie", ... }\n'
        '  ],\n'
        '  "resenas": [\n'
        '    { "usuario_id": 10374,\n'
        '      "comentario": "Excelente sabor",\n'
        '      "puntuacion": 4,\n'
        '      "fecha": ISODate("2026-07-12T23:44:38Z") }\n'
        '  ]\n'
        '}')
    d.caja(860, 80, 370, 420, "Documento de ejemplo (real)\n" + ejemplo, "nota", 11, True, mono=True, align="izq")
    d.caja(40, 622, 1190, 66,
           "Los platos y las reseñas van embebidos porque siempre se leen junto al restaurante (menú y ficha) y su volumen por restaurante es chico.\n"
           "Se cargaron 20,000 restaurantes con seed.js (mongosh); hay índices en categoria y ciudad.",
           "docker", 12, False, align="izq")
    return d


def er_glue(glue):
    d = Diagrama("ER Catalogo Glue", "Diagrama Entidad-Relación del Catálogo de Datos — AWS Glue · base ubereats_datalake", 1480, 760)

    def cols(nombre, defecto):
        if glue and nombre in glue:
            cs = glue[nombre]["columns"] + glue[nombre]["partitions"]
            def corto(t):
                return "array<struct<…>>" if t.startswith("array<struct") else (t if len(t) < 30 else t[:27] + "…")
            return [("", n, corto(t)) for n, t in cs]
        return defecto

    S = "string"
    usu = cols("usuarios", [("", "id", "bigint"), ("", "nombre", S), ("", "email", S), ("", "password_hash", S), ("", "telefono", S),
                            ("", "rol", S), ("", "restaurante_id", S), ("", "fecha_registro", S), ("", "dt", S)])
    dirs = cols("direcciones", [("", "id", "bigint"), ("", "usuario_id", "bigint"), ("", "calle", S), ("", "ciudad", S), ("", "referencia", S),
                                ("", "lat", "double"), ("", "lng", "double"), ("", "es_principal", "bigint"), ("", "dt", S)])
    ords = cols("orders", [("", "id", "bigint"), ("", "customer_id", "bigint"), ("", "restaurant_id", S), ("", "delivery_id", "bigint"),
                           ("", "direccion_entrega", S), ("", "status", S), ("", "total", "double"), ("", "created_at", S), ("", "dt", S)])
    itm = cols("order_items", [("", "id", "bigint"), ("", "order_id", "bigint"), ("", "dish_id", S), ("", "nombre_plato", S),
                               ("", "cantidad", "bigint"), ("", "precio_unitario", "double"), ("", "dt", S)])
    mon = cols("mongodb", [("", "_id", "struct<$oid:string>"), ("", "nombre", S), ("", "categoria", S), ("", "ciudad", S), ("", "direccion", S),
                           ("", "admin_id", "bigint"), ("", "calificacion_promedio", "double"), ("", "platos", "array<struct>"),
                           ("", "resenas", "array<struct>"), ("", "dt", S)])

    def marca(fs, pk=None, fk=None):
        return [("PK" if n == pk else "FK" if n == fk else t0, n, t) for t0, n, t in fs]

    tu = d.tabla(40, 90, 360, "usuarios", marca(usu, "id"), "#8C4FFF", "raw/mysql")
    td = d.tabla(40, 90 + tu.h + 70, 360, "direcciones", marca(dirs, "id", "usuario_id"), "#8C4FFF", "raw/mysql")
    to = d.tabla(560, 90, 360, "orders", marca(ords, "id", "customer_id"), "#8C4FFF", "raw/postgres")
    ti = d.tabla(560, 90 + to.h + 70, 360, "order_items", marca(itm, "id", "order_id"), "#8C4FFF", "raw/postgres")
    tm = d.tabla(1080, 90, 380, "mongodb  (restaurantes)", marca(mon, "_id"), "#8C4FFF", "raw/mongodb")

    a, b = tu.der("id"), to.izq("customer_id")
    d.flecha([a, (480, a[1]), (480, b[1]), b], "1 : N", (480, (a[1] + b[1]) / 2 - 20), ini="uno", fin="muchos", fs=13)
    d.flecha([tu.abajo(0.3), td.arriba(0.3)], "1 : N", (tu.x + tu.w * 0.3 + 40, (tu.y + tu.h + td.y) / 2), ini="uno", fin="muchos", fs=13)
    d.flecha([to.abajo(0.3), ti.arriba(0.3)], "1 : N", (to.x + to.w * 0.3 + 40, (to.y + to.h + ti.y) / 2), ini="uno", fin="muchos", fs=13)
    a, b = tm.izq("_id"), to.der("restaurant_id")
    d.flecha([a, (1000, a[1]), (1000, b[1]), b], "1 : N", (1000, (a[1] + b[1]) / 2 - 20), ini="uno", fin="muchos", fs=13)
    d.texto(1000, b[1] + 26, 'mongodb._id."$oid"\n= orders.restaurant_id', 11, False, GRIS, "middle")
    d.caja(1080, 90 + tm.h + 30, 380, 190,
           "Notas del catálogo\n"
           "• 5 tablas (una por archivo cargado a S3); dt es la\n"
           "  partición por fecha de ingesta.\n"
           "• Las relaciones son lógicas: los CSV/JSONL no tienen\n"
           "  claves foráneas; Athena las resuelve con JOIN.\n"
           "• El crawler nombró mongodb a la colección de\n"
           "  restaurantes y su _id quedó como struct {\"$oid\"}.\n"
           "• _class lo añade Spring Data al guardar; partition_0\n"
           "  la crea el crawler por la carpeta restaurantes/.",
           "nota", 12, True, align="izq")
    return d


def arquitectura():
    d = Diagrama("Arquitectura de solucion", "Diagrama de Arquitectura de Solución — Delivery Cloud (AWS · us-east-1)", 1900, 1200)
    d.oy = 40
    # Cliente y frontend
    d.caja(20, 430, 120, 90, "Usuario\nNavegador web\ncustomer · admin\ndelivery", "user", 12)
    d.grupo(170, 20, 1710, 1110, "AWS Cloud — región us-east-1", "#232F3E", dash=True, fs=15)
    d.grupo(190, 50, 260, 130, "FRONTEND", "#DD344C", "#FFFFFF", fs=12)
    d.caja(205, 82, 230, 82, "AWS Amplify\nSPA React + Vite\nmain.duqtfdxa5tvcw.amplifyapp.com", "front", 12)
    d.caja(250, 430, 200, 90, "Amazon API Gateway\nHTTP API · HTTPS\n/ms1 … /ms5 → VPC Link", "apigw", 13)
    d.flecha([(80, 430), (80, 123), (205, 123)], "1. carga la SPA", (128, 140), fs=11)
    d.flecha([(140, 475), (250, 475)], "2. REST/HTTPS", (195, 455), fs=11)
    # VPC
    d.grupo(470, 200, 1390, 590, "VPC por defecto  ·  subredes us-east-1a / us-east-1b", "#248814", "#FBFDFB", fs=14)
    d.caja(490, 440, 110, 70, "VPC Link\n(API Gateway)", "red", 12)
    d.caja(650, 440, 150, 70, "ALB interno\nsin IP pública\nhealth check /health", "red", 12)
    d.flecha([(450, 475), (490, 475)])
    d.flecha([(600, 475), (650, 475)])
    # App tier (2 VMs balanceadas)
    d.texto(930, 232, "App Tier · 2 VMs balanceadas", 12, True, "#ED7100")
    for y, az, nm in [(240, "us-east-1a", "PP-App-Tier"), (520, "us-east-1b", "PP-App-Tier-2")]:
        d.grupo(890, y, 420, 240, f"EC2 {nm} · t2.micro · {az}", "#ED7100", "#FFFDF9", fs=12)
        d.caja(905, y + 60, 100, 80, "NGINX\n:80\nX-Served-By", "ec2", 12)
        d.grupo(1024, y + 34, 278, 152, "", "#9AA5B1", "none", dash=True)
        for i, (a, b) in enumerate([("MS1", "FastAPI"), ("MS2", "Spring Boot"), ("MS3", "Express"), ("MS4", "FastAPI"), ("MS5", "FastAPI")]):
            d.caja(1032 + (i % 3) * 90, y + 42 + (i // 3) * 74, 82, 60, f"{a}\n{b}", "docker", 11)
        d.flecha([(1005, y + 100), (1024, y + 100)])
        d.texto(1032, y + 210, "docker compose · restart: unless-stopped", 11, False, GRIS)
    d.flecha([(800, 475), (860, 475), (860, 340), (905, 340)])
    d.flecha([(860, 475), (860, 620), (905, 620)], "reparte", (830, 458), fs=11)
    # DB tier
    d.grupo(1400, 240, 400, 290, "EC2 PP-DB-Tier · privada (SG solo App e Ingesta)", "#3B48CC", "#FAFBFF", fs=12)
    for i, (t, sub) in enumerate([("MySQL 8.0", "ms1_usuarios · usuarios, direcciones"), ("PostgreSQL 16", "ms3_pedidos · orders, order_items"),
                                  ("MongoDB 7", "ms2_catalogo · restaurantes")]):
        d.caja(1420, 282 + i * 78, 360, 64, f"{t}\n{sub}", "db", 12)
    d.flecha([(1310, 370), (1355, 370), (1355, 340), (1420, 340)], "SQL / Mongo\n(IP privada)", (1355, 305), fs=11)
    d.flecha([(1310, 640), (1355, 640), (1355, 470), (1420, 470)])
    # Ingesta
    d.grupo(1400, 560, 400, 200, "EC2 PP-Ingest-VM · MV de ingesta (privada)", "#ED7100", "#FFFDF9", fs=12)
    for i, nm in enumerate(["ingest-\nmysql", "ingest-\npostgres", "ingest-\nmongodb"]):
        d.caja(1415 + i * 125, 605, 112, 70, f"{nm}\nPython", "ec2", 11, False)
    d.texto(1415, 725, "3 contenedores · pull del 100 % de las tablas", 11, False, GRIS)
    d.flecha([(1600, 560), (1600, 530)], "pull 100 %", (1660, 546), fs=11)
    # Data science
    d.grupo(470, 810, 1390, 300, "DATA SCIENCE  ·  Data Lake y analítica", "#8C4FFF", "#FCFAFF", fs=14)
    d.caja(1510, 850, 270, 120, "Amazon S3 · Data Lake\nraw/mysql · raw/postgres\nraw/mongodb\nCSV / JSONL · snapshot completo", "s3", 12)
    d.caja(1180, 850, 270, 120, "AWS Glue\nCrawler + Data Catalog\nubereats_datalake\n5 tablas", "analytics", 12)
    d.caja(850, 850, 270, 120, "Amazon Athena\nSQL sobre S3 (pp-workgroup)\n4 consultas JOIN · 2 vistas", "analytics", 12)
    d.caja(540, 850, 240, 120, "Amazon S3\nathena-results\n(resultados de consultas)", "s3", 12)
    d.flecha([(1600, 760), (1600, 850)], "escribe", (1645, 805), fs=11)
    d.flecha([(1510, 910), (1450, 910)], "cataloga", (1480, 893), fs=11)
    d.flecha([(1180, 910), (1120, 910)], "esquema", (1150, 893), fs=11)
    d.flecha([(850, 910), (780, 910)])
    d.flecha([(985, 970), (985, 1060), (1645, 1060), (1645, 970)], "lee los archivos", (1315, 1045), dash=True, fs=11)
    d.flecha([(985, 760), (985, 850)], "MS5 · boto3", (1045, 805), fs=11)
    # Seguridad
    d.grupo(20, 560, 430, 300, "Seguridad y operación", "#5F6B7A", "#F8F9FA", fs=13)
    d.texto(36, 610,
            "• ALB: solo acepta tráfico del VPC Link (SG propio).\n"
            "• App Tier: puerto 80 desde el ALB; sin SSH público\n"
            "  (administración con AWS Systems Manager).\n"
            "• DB Tier: 3306 / 5432 / 27017 solo desde el SG de\n"
            "  App e Ingesta; sin puertos abiertos a internet.\n"
            "• Roles IAM: LabInstanceProfile en las EC2\n"
            "  (S3, Athena, Glue, SSM); sin claves en el código.\n"
            "• JWT HS256 compartido entre MS1, MS2 y MS3;\n"
            "  MS4 reenvía el token del usuario.\n"
            "• Health check del ALB cada 15 s: si una VM cae,\n"
            "  la otra atiende todo el tráfico.", 12.5)
    return d


def main():
    glue = None
    ruta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, "glue_tables.json")
    if os.path.exists(ruta):
        glue = json.load(open(ruta))
        print("Usando esquema real de Glue:", ruta)
    else:
        print("glue_tables.json no encontrado: el diagrama de Glue usa los tipos esperados")
    diagramas = [er_mysql(), er_postgres(), json_mongo(), er_glue(glue), arquitectura()]
    archivos = ["er-mysql-ms1", "er-postgresql-ms3", "json-mongodb-ms2", "er-catalogo-glue", "arquitectura-solucion"]
    for d, nom in zip(diagramas, archivos):
        svg = os.path.join(AQUI, nom + ".svg")
        png = os.path.join(AQUI, nom + ".png")
        open(svg, "w").write(a_svg(d))
        subprocess.run(["inkscape", svg, "--export-type=png", f"--export-filename={png}", "--export-width", str(int(d.w * 1.6))],
                       check=True, capture_output=True)
        print("OK", nom)
    xml = '<mxfile host="app.diagrams.net" agent="generar_diagramas.py">' + "".join(a_drawio(d) for d in diagramas) + "</mxfile>"
    open(os.path.join(AQUI, "proyecto-delivery-cloud.drawio"), "w").write(xml)
    print("OK proyecto-delivery-cloud.drawio (5 páginas)")


if __name__ == "__main__":
    main()
