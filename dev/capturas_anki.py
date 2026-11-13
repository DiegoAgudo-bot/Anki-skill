# -*- coding: utf-8 -*-
"""Saca capturas REALES del add-on funcionando en Anki (sin pantalla).

Sirven para el vídeo y la landing. Arranca Anki con una carpeta temporal,
importa los PDFs de prueba (texto inventado), crea un glosario y una tarjeta,
y guarda en la carpeta de salida:

    0-asistente.png  1-gestor.png  2-glosario.png  3-tarjeta.png
    4-popup.png      5-respuesta.png  6-popup2.png  7-visor.png
    posiciones.json  (dónde están los términos, para animar un cursor)

Uso (necesita aqt instalado en ese Python):
    python dev/capturas_anki.py carpeta_de_salida
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PILOTO = r'''
import json, os, traceback
from aqt import mw, gui_hooks
from aqt.qt import QTimer, QPoint

SALIDA = os.environ["FUENTES_CAPTURAS"]
PDFS = json.loads(os.environ["FUENTES_PDFS"])
pos = {}

def guardar(widget, nombre):
    widget.grab().save(os.path.join(SALIDA, nombre))

def salir(error=None):
    pos["error"] = error
    with open(os.path.join(SALIDA, "posiciones.json"), "w") as f:
        json.dump(pos, f, indent=1)
    mw.unloadProfileAndExit()

def seguro(f):
    def g(*a):
        try:
            f(*a)
        except Exception:
            salir(traceback.format_exc())
    return g

def luego(ms, f):
    QTimer.singleShot(ms, seguro(f))

def js(codigo, cb):
    mw.reviewer.web.evalWithCallback(codigo, seguro(cb))

RECT = """(function(sel, n){ var e = document.querySelectorAll(sel)[n]; if (!e) return null;
  var r = e.getBoundingClientRect(); return JSON.stringify([r.left, r.top, r.width, r.height]); })"""

def a_ventana(rect):
    """Coordenadas de la página web -> coordenadas de la ventana principal."""
    r = json.loads(rect)
    o = mw.reviewer.web.mapTo(mw, QPoint(0, 0))
    z = mw.reviewer.web.zoomFactor()
    return [o.x() + r[0] * z, o.y() + r[1] * z, r[2] * z, r[3] * z]

@seguro
def empezar():
    from fuentes import core, importer
    from fuentes.ui import asistente
    mw.resize(1120, 720)
    for nombre, ruta in PDFS:
        importer.importar_pdf(core.indice(), ruta, core.PDFS_DIR, nombre=nombre)
    core.guardar_terminos([
        {"termino": "arteria femoral", "sinonimos": ["a. femoral"], "activo": True},
        {"termino": "nervio ciático", "sinonimos": ["ciático"], "activo": True},
        {"termino": "ligamento inguinal", "sinonimos": [], "activo": True},
        {"termino": "aorta", "sinonimos": [], "activo": True},
        {"termino": "ventrículo izquierdo", "sinonimos": [], "activo": True},
    ])
    core.exportar(silencioso=True, al_terminar=seguro(dialogos))

def dialogos(_inf):
    from fuentes.ui import asistente, gestor, editor_glosario
    a = asistente.mostrar()
    pos["dialogos"] = {}
    def uno():
        guardar(a, "0-asistente.png"); a.close()
        g = gestor.GestorFuentes(mw); g.show()
        def dos():
            guardar(g, "1-gestor.png"); g.close()
            e = editor_glosario.EditorGlosario(mw); e.show()
            def tres():
                guardar(e, "2-glosario.png"); e.modificado = False; e.close()
                repasar()
            luego(500, tres)
        luego(500, dos)
    luego(500, uno)

def repasar():
    col = mw.col
    basico = col.models.by_name("Básico") or col.models.by_name("Basic")
    n = col.new_note(basico)
    n.fields[0] = "¿Por dónde entra en el muslo la arteria femoral?"
    n.fields[1] = "Bajo el ligamento inguinal.<br><br>Ojo: el nervio ciatico va por detrás, no la acompaña."
    col.add_note(n, col.decks.id("Default"))
    mw.col.decks.select(col.decks.id("Default"))
    mw.moveToState("review")
    mw.reviewer.web.setZoomFactor(1.6)  # tarjeta grande: se lee bien en un vídeo
    luego(3500, lambda: js(RECT + "('.fuentes-term', 0)", anverso))

def anverso(rect):
    guardar(mw, "3-tarjeta.png")
    pos["termino1"] = a_ventana(rect)
    js("Fuentes.abrir(document.querySelector('.fuentes-term')); 1",
       lambda _: luego(700, lambda: js(RECT + "('.fuentes-abrible', 0)", popup1)))

def popup1(rect):
    guardar(mw, "4-popup.png")
    pos["fragmento1"] = a_ventana(rect)
    # Qué fuente y página abre ese fragmento (lo usamos luego para el visor).
    js("(function(){ var f = document.querySelector('.fuentes-abrible');"
       "return JSON.stringify([+f.getAttribute('data-s'), +f.getAttribute('data-p')]); })()", popup1b)

def popup1b(destino):
    pos["abre"] = json.loads(destino)
    js("Fuentes.cerrar(); 1", lambda _: (mw.reviewer._showAnswer(),
       luego(2500, lambda: js("(function(){ var ts = document.querySelectorAll('.fuentes-term');"
                              "var t = ts[ts.length - 1]; window.__t = t; var r = t.getBoundingClientRect();"
                              "return JSON.stringify([r.left, r.top, r.width, r.height]); })()", reverso))))

def reverso(rect):
    guardar(mw, "5-respuesta.png")
    pos["termino2"] = a_ventana(rect)
    js("Fuentes.abrir(window.__t); 1", lambda _: luego(700, popup2))

def popup2():
    guardar(mw, "6-popup2.png")
    from fuentes.ui import visor
    visor.abrir(*pos["abre"])  # lo mismo que hace el clic en el fragmento
    visor._dialogo.resize(1120, 720)
    luego(6000, visor_listo)

def visor_listo():
    from fuentes.ui import visor
    guardar(visor._dialogo, "7-visor.png")
    visor._dialogo.reject()
    pos["ventana"] = [mw.width(), mw.height()]
    salir()

gui_hooks.profile_did_open.append(lambda: QTimer.singleShot(2000, empezar))
QTimer.singleShot(120000, lambda: os._exit(1))
'''


def main():
    salida = os.path.abspath(sys.argv[1])
    os.makedirs(salida, exist_ok=True)
    base = tempfile.mkdtemp(prefix="anki-capturas-")
    addons = os.path.join(base, "addons21")
    os.makedirs(os.path.join(addons, "zz_piloto"))
    os.symlink(os.path.join(RAIZ, "fuentes"), os.path.join(addons, "fuentes"))
    with open(os.path.join(addons, "zz_piloto", "__init__.py"), "w") as f:
        f.write(PILOTO)
    sys.path.insert(0, os.path.join(RAIZ, "dev"))
    import generar_pdfs
    pdfs = [("Apuntes de Anatomía", generar_pdfs.generar_apuntes(os.path.join(base, "apuntes-anatomia.pdf"))),
            ("Resumen de repaso", generar_pdfs.generar_otra_fuente(os.path.join(base, "resumen-repaso.pdf")))]
    entorno = dict(os.environ, FUENTES_CAPTURAS=salida, FUENTES_PDFS=json.dumps(pdfs),
                   QTWEBENGINE_CHROMIUM_FLAGS="--no-sandbox", QTWEBENGINE_DISABLE_SANDBOX="1",
                   QT_QPA_PLATFORM="offscreen", QT_SCALE_FACTOR="2")
    subprocess.run([sys.executable, "-c", (
        "import sys; from pathlib import Path; from aqt.profiles import ProfileManager;"
        "pm = ProfileManager(Path(sys.argv[1])); pm.setupMeta(); pm.create('Demo'); pm.load('Demo');"
        "pm.meta['firstRun'] = False; pm.meta['defaultLang'] = 'es_ES'; pm.save()"), base],
        env=entorno, check=True)
    # Apartamos los datos reales del desarrollador mientras dura la sesión.
    uf = os.path.join(RAIZ, "fuentes", "user_files")
    respaldo = uf + ".respaldo-capturas"
    if os.path.exists(respaldo):
        sys.exit("Existe %s de una ejecución anterior: revísalo y restáuralo a mano." % respaldo)
    os.rename(uf, respaldo)
    os.makedirs(uf)
    try:
        subprocess.run([sys.executable, "-c", "import aqt; aqt.run()", "-b", base, "-p", "Demo"],
                       env=entorno, timeout=180, stdout=subprocess.DEVNULL)
    finally:
        shutil.rmtree(uf, ignore_errors=True)
        os.rename(respaldo, uf)
        meta = os.path.join(RAIZ, "fuentes", "meta.json")
        if os.path.exists(meta):
            os.remove(meta)
    with open(os.path.join(salida, "posiciones.json")) as f:
        pos = json.load(f)
    print(json.dumps(pos, indent=1))
    sys.exit(1 if pos.get("error") else 0)


if __name__ == "__main__":
    main()
