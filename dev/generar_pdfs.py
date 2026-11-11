# -*- coding: utf-8 -*-
"""Genera PDFs de prueba con texto INVENTADO (escrito para este proyecto).

No contiene material de ningún libro real. Se usa en los tests y en la demo.

    python dev/generar_pdfs.py [carpeta]      # crea los PDFs de ejemplo
"""
import os
import sys

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# Texto original, redactado para las pruebas. Es divulgativo y simplificado.
TEMAS = [
    (
        "Tema 1. Sistema cardiovascular",
        [
            "El corazón impulsa la sangre gracias a la contracción coordinada de sus cuatro cavidades. "
            "El ventrículo izquierdo tiene la pared más gruesa porque debe vencer la resistencia de toda "
            "la circulación sistémica.",
            "La aorta nace del ventrículo izquierdo y describe un arco antes de descender por el tórax. "
            "De sus ramas depende el riego de la cabeza, los miembros superiores y las vísceras.",
            "La arteria femoral continúa a la arteria ilíaca externa por debajo del ligamento inguinal. "
            "En el triángulo femoral se palpa el pulso con facilidad, lo que la hace útil para accesos "
            "vasculares en la práctica clínica.",
            "Las venas devuelven la sangre al corazón con ayuda de válvulas que impiden el reflujo. "
            "La vena safena mayor es la vena más larga del cuerpo y asciende por la cara medial del miembro "
            "inferior.",
        ],
    ),
    (
        "Tema 2. Sistema nervioso periférico",
        [
            "El nervio ciático es el nervio más grueso del organismo. Sale de la pelvis por el agujero "
            "ciático mayor y desciende por la región posterior del muslo.",
            "Por encima de la fosa poplítea, el nervio ciático suele dividirse en el nervio tibial y el "
            "nervio peroneo común. La lesión del peroneo común produce el llamado pie caído.",
            "La médula espinal transmite información entre el encéfalo y el resto del cuerpo. Los nervios "
            "raquídeos salen por los agujeros intervertebrales a cada lado.",
        ],
    ),
    (
        "Tema 3. Aparato locomotor",
        [
            "El músculo cuádriceps femoral extiende la rodilla y está formado por cuatro cabezas. Lo inerva "
            "el nervio femoral, que acompaña de cerca a la arteria femoral en la raíz del muslo.",
            "El bíceps braquial flexiona el codo y supina el antebrazo. Su tendón largo recorre el surco "
            "intertubercular del húmero.",
            "El año pasado se describió en estas notas inventadas un caso de fractura del cuello del fémur; "
            "el ejemplo sirve para comprobar que la eñe no se confunde con otras letras.",
        ],
    ),
]


def _escribir_parrafo(c, texto, x, y, ancho_chars=82, partir=True):
    """Escribe un párrafo a mano, cortando algunas palabras con guion."""
    palabras = texto.split()
    linea = ""
    for palabra in palabras:
        if len(linea) + len(palabra) + 1 > ancho_chars:
            resto = ancho_chars - len(linea) - 2
            if partir and resto >= 2 and len(palabra) >= 6:
                # Forzamos un corte con guion para probar la limpieza.
                corte = max(2, min(resto, len(palabra) - 3))
                c.drawString(x, y, (linea + " " + palabra[:corte] + "-").strip())
                y -= 14
                linea = palabra[corte:]
                continue
            c.drawString(x, y, linea.strip())
            y -= 14
            linea = palabra
        else:
            linea = (linea + " " + palabra).strip()
    if linea:
        c.drawString(x, y, linea)
        y -= 14
    return y - 8


def generar_apuntes(ruta, titulo="Apuntes de Anatomía (ejemplo)", repeticiones=1):
    """PDF con cabecera y pie repetidos, palabras partidas y marcadores (outline).

    `repeticiones` permite generar libros grandes (p. ej. 400 → 1200 páginas).
    """
    c = canvas.Canvas(ruta, pagesize=A4)
    c.setTitle(titulo)
    ancho, alto = A4
    pagina = 0
    for r in range(repeticiones):
        for n_tema, (tema, parrafos) in enumerate(TEMAS):
            pagina += 1
            clave = "t%d_%d" % (r, n_tema)
            c.bookmarkPage(clave)
            if r == 0:
                c.addOutlineEntry(tema, clave, level=0)
            c.setFont("Helvetica", 8)
            c.drawString(50, alto - 30, titulo + " — Material de prueba")
            c.drawString(ancho / 2, 30, str(pagina))
            c.setFont("Helvetica-Bold", 13)
            c.drawString(50, alto - 70, tema)
            c.setFont("Helvetica", 11)
            y = alto - 100
            for p in parrafos:
                y = _escribir_parrafo(c, p, 50, y)
            c.showPage()
    c.save()
    return ruta


def generar_otra_fuente(ruta):
    """Segunda fuente, más breve, para probar el popup con varias fuentes."""
    c = canvas.Canvas(ruta, pagesize=A4)
    _, alto = A4
    textos = [
        "Resumen de repaso. La arteria femoral profunda irriga los músculos del muslo. "
        "Recuerda que el nervio ciático no acompaña a la arteria femoral, sino que va por detrás.",
        "Esquema rápido: la aorta torácica da arterias intercostales; la aorta abdominal da el tronco "
        "celíaco y las arterias renales.",
    ]
    for i, t in enumerate(textos):
        c.setFont("Helvetica", 11)
        _escribir_parrafo(c, t, 50, alto - 80, partir=False)
        c.showPage()
    c.save()
    return ruta


def generar_escaneado(ruta, paginas=3):
    """Simula un PDF escaneado: solo dibujos, sin texto extraíble."""
    c = canvas.Canvas(ruta, pagesize=A4)
    for _ in range(paginas):
        for i in range(20):
            c.rect(50, 100 + i * 30, 400, 10, fill=1)
        c.showPage()
    c.save()
    return ruta


if __name__ == "__main__":
    carpeta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "pdfs")
    os.makedirs(carpeta, exist_ok=True)
    print(generar_apuntes(os.path.join(carpeta, "apuntes-anatomia.pdf")))
    print(generar_otra_fuente(os.path.join(carpeta, "resumen-repaso.pdf")))
    print(generar_escaneado(os.path.join(carpeta, "escaneado.pdf")))
