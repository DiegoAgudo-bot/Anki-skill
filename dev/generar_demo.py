# -*- coding: utf-8 -*-
"""Regenera dev/demo-data/ con el exportador REAL a partir de los PDFs de prueba.

    python dev/generar_demo.py

dev/demo-data/ imita la carpeta de medios de Anki tras exportar: glosario,
un JSON por término, _pagewise.js y _pagewise.css. Todo el texto es inventado.
"""
import os
import shutil
import sys
import tempfile

DEV = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(DEV)
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "pagewise", "vendor"))
sys.path.insert(0, DEV)

import generar_pdfs  # noqa: E402
from pagewise import exporter, importer  # noqa: E402
from pagewise.index import Indice  # noqa: E402

# Glosario de ejemplo escrito para las pruebas (no sale de ningún libro).
GLOSARIO = [
    {"termino": "arteria femoral", "sinonimos": ["a. femoral"], "activo": True},
    {"termino": "nervio ciático", "sinonimos": [], "activo": True},
    {"termino": "aorta", "sinonimos": ["aorta torácica"], "activo": True},
    {"termino": "ventrículo izquierdo", "sinonimos": [], "activo": True},
    {"termino": "nervio femoral", "sinonimos": [], "activo": True},
    {"termino": "vena safena mayor", "sinonimos": ["safena mayor"], "activo": True},
    {"termino": "cuádriceps femoral", "sinonimos": ["cuádriceps"], "activo": True},
    {"termino": "bíceps braquial", "sinonimos": [], "activo": True},
    {"termino": "médula espinal", "sinonimos": [], "activo": True},
]


def main(destino=os.path.join(DEV, "demo-data"), con_web=False):
    """con_web=False quita _pagewise.js/.css (la demo carga los de pagewise/web)."""
    tmp = tempfile.mkdtemp()
    try:
        ind = Indice(os.path.join(tmp, "index.sqlite3"))
        for nombre, f in (("Apuntes de Anatomía (ejemplo)", generar_pdfs.generar_apuntes),
                          ("Resumen de repaso (ejemplo)", generar_pdfs.generar_otra_fuente)):
            ruta = f(os.path.join(tmp, nombre + ".pdf"))
            importer.importar_pdf(ind, ruta, os.path.join(tmp, "pdfs"), nombre=nombre)
        if os.path.isdir(destino):
            shutil.rmtree(destino)
        os.makedirs(destino)
        inf = exporter.exportar(ind, GLOSARIO, destino, os.path.join(RAIZ, "pagewise", "web"))
        ind.cerrar()
        if not con_web:
            for n in ("_pagewise.js", "_pagewise.css"):
                os.remove(os.path.join(destino, n))
        print("%s: %d términos, %s" % (destino, inf.terminos, exporter.formato_tamano(inf.bytes)))
    finally:
        shutil.rmtree(tmp)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1], con_web=True)
    else:
        main()
