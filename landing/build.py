# -*- coding: utf-8 -*-
"""Genera landing/index.html (un único archivo, listo para publicar).

    python3 landing/build.py

Fuentes:  src/pagina.html (estilos y contenido) + src/demo.js (demo en vivo)
Ajustes:  config.json
  lista_endpoint  URL del servicio de formularios que guarda los correos
                  (p. ej. https://formspree.io/f/XXXXXXXX). Vacío = la página
                  avisa de que la lista aún no está abierta; nunca finge.
  descarga_url    adónde lleva "Descargar la versión gratuita"
  url_publica     dirección final de la página (para compartir en redes)
"""
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

TITULO = "Fuentes: tus PDFs dentro de tus tarjetas de Anki"
DESCRIPCION = ("Add-on para Anki que subraya los términos de tus tarjetas y te enseña qué dicen "
               "sobre ellos tus propios PDFs, con la página exacta. Local y sin conexión.")
FUENTES = ("https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400"
           "&family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,800&family=Caveat:wght@500;700&display=swap")
# Icono: una "F" sobre trazo de subrayador.
ICONO = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
         "%3Crect y='13' width='32' height='13' fill='%23ffe83d'/%3E"
         "%3Cpath d='M9 26V5h15v4.5H14.5v4.5H22v4.5h-7.5V26z' fill='%23121a3a'/%3E%3C/svg%3E")


def leer(*partes):
    with open(os.path.join(AQUI, *partes), encoding="utf-8") as f:
        return f.read()


def main(salida=None, lista=None):
    """salida y lista permiten generar una copia de prueba (ver prueba.js)."""
    cfg = json.loads(leer("config.json"))
    if lista is not None:
        cfg["lista_endpoint"] = lista
    cuerpo = leer("src", "pagina.html")
    cuerpo = cuerpo.replace("/*__DEMO_JS__*/", leer("src", "demo.js"))
    cuerpo = cuerpo.replace("{{LISTA}}", json.dumps(cfg.get("lista_endpoint", "")))
    cuerpo = cuerpo.replace("{{DESCARGA}}", cfg["descarga_url"])
    canonica = ('<link rel="canonical" href="%s">\n<meta property="og:url" content="%s">\n'
                % (cfg["url_publica"], cfg["url_publica"])) if cfg.get("url_publica") else ""
    html = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>%(t)s</title>
<meta name="description" content="%(d)s">
<meta property="og:type" content="website">
<meta property="og:title" content="%(t)s">
<meta property="og:description" content="%(d)s">
%(c)s<link rel="icon" href="%(i)s">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="%(f)s">
<style>body{margin:0}img{max-width:100%%}[hidden]{display:none!important}</style>
</head>
<body>
%(b)s
</body>
</html>
""" % {"t": TITULO, "d": DESCRIPCION, "c": canonica, "i": ICONO, "f": FUENTES, "b": cuerpo}
    with open(salida or os.path.join(AQUI, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("%s generado (%d KB). Lista de espera: %s"
          % (salida or "landing/index.html", len(html.encode("utf-8")) // 1024, cfg.get("lista_endpoint") or "SIN CONECTAR"))


if __name__ == "__main__":
    main(*sys.argv[1:3])
