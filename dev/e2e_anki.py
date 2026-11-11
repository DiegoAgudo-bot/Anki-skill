# -*- coding: utf-8 -*-
"""Prueba de extremo a extremo con un Anki REAL (sin pantalla).

Arranca Anki con una carpeta de datos temporal, instala el add-on (enlace
simbólico) y un add-on "piloto" que:
  1. importa un PDF de prueba (texto inventado) y crea un glosario,
  2. exporta los datos a la carpeta de medios,
  3. crea notas (básica y cloze), opcionalmente activa el snippet en las
     plantillas, y abre el repaso,
  4. lee el DOM del repaso: términos subrayados, popup, pycmd.
Escribe los resultados en un JSON y cierra Anki.

Uso (necesita aqt instalado, p. ej. pip install "aqt[qt6]==2.1.66"):
    QT_QPA_PLATFORM=offscreen python dev/e2e_anki.py [--plantillas]
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PILOTO = r'''
import json, os, sys, traceback
from aqt import mw, gui_hooks
from aqt.qt import QTimer

SALIDA = os.environ["FUENTES_E2E_SALIDA"]
PDF = os.environ["FUENTES_E2E_PDF"]
PLANTILLAS = os.environ.get("FUENTES_E2E_PLANTILLAS") == "1"
res = {"pasos": []}

def guardar():
    with open(SALIDA, "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)

def fallo(e):
    res["error"] = traceback.format_exc()
    guardar()
    mw.unloadProfileAndExit()

def paso(nombre, valor=True):
    res["pasos"].append(nombre)
    res[nombre] = valor
    guardar()

def js(codigo, cb):
    mw.reviewer.web.evalWithCallback(codigo, cb)

def empezar():
    try:
        fuentes = sys.modules["fuentes"]
        from fuentes import core, importer
        r = importer.importar_pdf(core.indice(), PDF, core.PDFS_DIR, nombre="Apuntes de prueba")
        paso("importado", {"paginas": r.paginas, "fragmentos": r.fragmentos})
        core.guardar_terminos([
            {"termino": "arteria femoral", "sinonimos": ["a. femoral"], "activo": True},
            {"termino": "nervio ciático", "sinonimos": [], "activo": True},
            {"termino": "aorta", "sinonimos": [], "activo": True},
        ])
        core.exportar(silencioso=True, al_terminar=exportado)
    except Exception as e:
        fallo(e)

def exportado(inf):
    try:
        medios = mw.col.media.dir()
        paso("exportado", sorted(n for n in os.listdir(medios) if n.startswith("_fuentes")))
        col = mw.col
        basico = col.models.by_name("Basic") or col.models.by_name("Básico")
        n = col.new_note(basico)
        n.fields[0] = "¿Qué <b>arteria femoral</b> se palpa? Cerca del nervio ciatico."
        n.fields[1] = "La aorta da ramas; <img src='x.png'> [sound:aorta.mp3]"
        col.add_note(n, col.decks.id("Default"))
        if PLANTILLAS:
            from fuentes import templates
            cambiados = templates.activar(col, [basico["id"]])
            paso("plantillas", cambiados)
            basico = col.models.get(basico["id"])
            paso("plantilla_qfmt", basico["tmpls"][0]["qfmt"])
        mw.col.decks.select(col.decks.id("Default"))
        mw.moveToState("review")
        QTimer.singleShot(4000, leer_anverso)
    except Exception as e:
        fallo(e)

def leer_anverso():
    js("""JSON.stringify({
        cargado: !!(window.Fuentes && Fuentes.__cargado),
        terminos: Array.prototype.map.call(document.querySelectorAll('.fuentes-term'), function(e){return e.textContent;}),
        scripts: Array.prototype.map.call(document.querySelectorAll('#qa script'), function(e){return e.getAttribute('src');}),
        html: document.getElementById('qa').innerHTML
    })""", anverso)

def anverso(r):
    try:
        paso("anverso", json.loads(r))
        js("""(function(){ var t = document.querySelector('.fuentes-term');
            Fuentes.forceTouch(true); t.click();
            var p = document.querySelector('.fuentes-popup');
            return JSON.stringify({visible: p && p.style.display, texto: p && p.textContent,
                abribles: document.querySelectorAll('.fuentes-abrible').length});
        })()""", popup)
    except Exception as e:
        fallo(e)

def popup(r):
    try:
        paso("popup", json.loads(r))
        js("""Fuentes.py({cmd:'mas', variantes:['arteria femoral']}, function(r){ window.__mas = r; });
              Fuentes.py({cmd:'buscar', q:'ligamento inguinal'}, function(r){ window.__buscar = r; });
              Fuentes.py({cmd:'archivo', nombre:'_fuentes_glosario.json'}, function(r){ window.__arch = r; }); 1""",
           lambda _: QTimer.singleShot(1500, leer_pycmd))
    except Exception as e:
        fallo(e)

def leer_pycmd():
    js("JSON.stringify({mas: window.__mas, buscar: window.__buscar, archivo: !!(window.__arch && window.__arch.ok)})", pycmd)

def pycmd(r):
    try:
        paso("pycmd", json.loads(r))
        mw.reviewer._showAnswer()
        QTimer.singleShot(2500, leer_reverso)
    except Exception as e:
        fallo(e)

def leer_reverso():
    js("""JSON.stringify({terminos: Array.prototype.map.call(document.querySelectorAll('.fuentes-term'),
        function(e){return e.textContent;}), scripts: document.querySelectorAll('script[src*="fuentes"]').length})""", reverso)

def reverso(r):
    try:
        paso("reverso", json.loads(r))
        # Diálogos de la fase d.
        from fuentes.ui import gestor, editor_glosario, visor
        g = gestor.GestorFuentes(mw)
        paso("gestor", {"filas": g.tabla.rowCount(), "estado": g.estado.text(),
                        "nombre": g.tabla.item(0, 1).text()})
        g.close()
        e = editor_glosario.EditorGlosario(mw)
        paso("editor", [e.tabla.item(i, 1).text() for i in range(e.tabla.rowCount())])
        e.modificado = False
        e.close()
        js("Fuentes.py({cmd:'abrir', fuente:1, pagina:2}); 1", lambda _: QTimer.singleShot(5000, leer_visor))
    except Exception as e:
        fallo(e)

def leer_visor():
    try:
        from fuentes.ui import visor
        d = visor._dialogo
        paso("visor", {"abierto": d is not None and d.isVisible(), "cargado_ok": d and d.cargado_ok,
                       "alternativa": d and d.alternativa_usada, "url": d and d.web.url().toString(),
                       "titulo": d and d.titulo.text()})
        d.grab().save(os.environ["FUENTES_E2E_SALIDA"] + ".visor.png")
        d.reject()
        terminar()
    except Exception as e:
        fallo(e)

def terminar():
    try:
        if PLANTILLAS:
            from fuentes import templates
            basico = mw.col.models.by_name("Basic") or mw.col.models.by_name("Básico")
            paso("desactivado", templates.desactivar(mw.col, [basico["id"]]))
            paso("qfmt_final", mw.col.models.get(basico["id"])["tmpls"][0]["qfmt"])
        res["ok"] = True
        guardar()
    except Exception as e:
        fallo(e)
        return
    mw.unloadProfileAndExit()

gui_hooks.profile_did_open.append(lambda: QTimer.singleShot(1500, empezar))
QTimer.singleShot(90000, lambda: (res.update({"error": res.get("error") or "tiempo agotado"}), guardar(), os._exit(1)))
'''


def main():
    plantillas = "--plantillas" in sys.argv
    base = tempfile.mkdtemp(prefix="anki-e2e-")
    addons = os.path.join(base, "addons21")
    os.makedirs(addons)
    os.symlink(os.path.join(RAIZ, "fuentes"), os.path.join(addons, "fuentes"))
    os.makedirs(os.path.join(addons, "zz_piloto"))
    with open(os.path.join(addons, "zz_piloto", "__init__.py"), "w") as f:
        f.write(PILOTO)
    sys.path.insert(0, os.path.join(RAIZ, "dev"))
    import generar_pdfs
    pdf = generar_pdfs.generar_apuntes(os.path.join(base, "apuntes.pdf"))
    salida = os.path.join(base, "resultado.json")
    entorno = dict(os.environ, FUENTES_E2E_SALIDA=salida, FUENTES_E2E_PDF=pdf,
                   FUENTES_E2E_PLANTILLAS="1" if plantillas else "0",
                   QTWEBENGINE_CHROMIUM_FLAGS="--no-sandbox", QTWEBENGINE_DISABLE_SANDBOX="1",
                   QT_QPA_PLATFORM=os.environ.get("QT_QPA_PLATFORM", "offscreen"))
    # Los datos del add-on (user_files) se crean en la carpeta del repositorio:
    # los apartamos para no mezclarlos con los del desarrollador.
    uf = os.path.join(RAIZ, "fuentes", "user_files")
    respaldo = uf + ".respaldo-e2e"
    if os.path.exists(respaldo):
        sys.exit("Existe %s de una ejecución anterior: revísalo y restáuralo a mano." % respaldo)
    os.rename(uf, respaldo)
    os.makedirs(uf)
    # Creamos antes las preferencias y el perfil para evitar el selector de
    # idioma del primer arranque (es modal y bloquea).
    subprocess.run([sys.executable, "-c", (
        "import sys; from pathlib import Path; from aqt.profiles import ProfileManager;"
        "pm = ProfileManager(Path(sys.argv[1])); pm.setupMeta(); pm.create('Prueba'); pm.load('Prueba');"
        "pm.meta['firstRun'] = False; pm.meta['defaultLang'] = 'es'; pm.save()"), base],
        env=entorno, check=True)
    try:
        subprocess.run([sys.executable, "-c", "import aqt; aqt.run()", "-b", base, "-p", "Prueba"], env=entorno, timeout=150,
                       stdout=subprocess.DEVNULL if "-q" in sys.argv else None)
    finally:
        shutil.rmtree(uf, ignore_errors=True)
        os.rename(respaldo, uf)  # rename (no move) para no anidar carpetas
        for p in ("meta.json",):
            ruta = os.path.join(RAIZ, "fuentes", p)
            if os.path.exists(ruta):
                os.remove(ruta)
    with open(salida) as f:
        res = json.load(f)
    if os.path.exists(salida + ".visor.png"):
        shutil.copy(salida + ".visor.png", os.path.join(tempfile.gettempdir(), "fuentes-e2e-visor.png"))
    print(json.dumps(res, ensure_ascii=False, indent=1))
    sys.exit(0 if res.get("ok") else 1)


if __name__ == "__main__":
    main()
