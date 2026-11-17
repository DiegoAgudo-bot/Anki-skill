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
    python dev/e2e_anki.py [--plantillas] [--ingles] [--migracion] [--paquete=build/pagewise-1.7.0.ankiaddon] [-q]
        [--pdf-grande=RUTA]   además abre ese PDF (p. ej. de 2 GB) y mide tiempo y memoria
                              (PAGEWISE_E2E_GRANDE_PAGINA y PAGEWISE_E2E_GRANDE_BUSCAR eligen dónde)
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

SALIDA = os.environ["PAGEWISE_E2E_SALIDA"]
PDF = os.environ["PAGEWISE_E2E_PDF"]
PLANTILLAS = os.environ.get("PAGEWISE_E2E_PLANTILLAS") == "1"
MIGRACION = os.environ.get("PAGEWISE_E2E_MIGRACION") == "1"
GRANDE = os.environ.get("PAGEWISE_E2E_GRANDE") or ""
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

def cerrar_aviso():
    """Cierra el aviso modal de la migración y guarda su texto."""
    w = mw.app.activeModalWidget()
    if w is not None:
        res["aviso_migracion"] = w.text() if hasattr(w, "text") else w.windowTitle()
        w.accept()

def probar_migracion():
    """Venimos del add-on antiguo «fuentes» con datos, medios y plantillas."""
    try:
        from pagewise import core, migracion, templates
        medios = mw.col.media.dir()
        paso("migracion", {
            "fuentes": [f["nombre"] for f in core.indice().fuentes()],
            "terminos": [t["termino"] for t in core.terminos()],
            "pdfs": len(os.listdir(core.PDFS_DIR)),
            "antiguo_activo": mw.addonManager.isEnabled("fuentes"),
            "asistente_visto": core.config()["asistente_visto"],
            "medios_antiguos": sorted(n for n in os.listdir(medios) if n.startswith("_fuentes")),
            "medios_nuevos": len([n for n in os.listdir(medios) if n.startswith("_pagewise")]),
            "aviso": res.get("aviso_migracion", "")[:60],
        })
        # Plantilla con el bloque antiguo: se renueva al nombre nuevo.
        col = mw.col
        basico = col.models.by_name("Basic") or col.models.by_name("Básico")
        basico["tmpls"][0]["qfmt"] += ('\n<!-- FUENTES:INICIO (antiguo) -->\n<link rel="stylesheet" href="_fuentes.css">'
                                      '\n<script src="_fuentes.js"></script>\n<!-- FUENTES:FIN -->')
        col.models.update_dict(basico)
        n = migracion.actualizar_plantillas(col)
        q = col.models.get(basico["id"])["tmpls"][0]["qfmt"]
        paso("plantilla_migrada", {"cambiados": n, "nuevo": "_pagewise.js" in q, "antiguo": "_fuentes" in q,
                                   "reverso_intacto": not templates.tiene(col.models.get(basico["id"])["tmpls"][0]["afmt"])})
        res["ok"] = True
        guardar()
    except Exception as e:
        fallo(e)
        return
    mw.unloadProfileAndExit()

def empezar():
    if MIGRACION:
        return probar_migracion()
    try:
        from pagewise import core, importer, i18n
        from pagewise.ui import asistente
        # Primer arranque: el asistente se abre solo (sin bloquear) y nada está hecho.
        a = asistente._abierto
        paso("asistente_inicial", {"visible": bool(a and a.isVisible()), "marcas": [m.text() for m in a.marcas],
                                   "titulo": a.windowTitle()})
        menu = [x for x in mw.form.menuTools.actions() if x.menu() and x.text() == "Pagewise"][0].menu()
        paso("idioma", {"idioma": i18n.idioma(), "menu": [x.text() for x in menu.actions() if x.text()]})
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
        paso("exportado", sorted(n for n in os.listdir(medios) if n.startswith("_pagewise")))
        with open(os.path.join(medios, "_pagewise_glosario.json"), encoding="utf-8") as f:
            paso("ajustes_exportados", json.load(f)["ajustes"])
        from pagewise.ui import asistente
        asistente._abierto.refrescar()
        paso("asistente_despues", [m.text() for m in asistente._abierto.marcas])
        asistente._abierto.grab().save(SALIDA + ".asistente.png")
        asistente._abierto.close()
        col = mw.col
        basico = col.models.by_name("Basic") or col.models.by_name("Básico")
        n = col.new_note(basico)
        n.fields[0] = "¿Qué <b>arteria femoral</b> se palpa? Cerca del nervio ciatico. Las aortas."
        n.fields[1] = "La aorta da ramas; <img src='x.png'> [sound:aorta.mp3]"
        col.add_note(n, col.decks.id("Default"))
        if PLANTILLAS:
            from pagewise import templates
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
        cargado: !!(window.Pagewise && Pagewise.__cargado),
        terminos: Array.prototype.map.call(document.querySelectorAll('.pagewise-term'), function(e){return e.textContent;}),
        scripts: Array.prototype.map.call(document.querySelectorAll('#qa script'), function(e){return e.getAttribute('src');}),
        html: document.getElementById('qa').innerHTML
    })""", anverso)

def anverso(r):
    try:
        paso("anverso", json.loads(r))
        js("""(function(){ var t = document.querySelector('.pagewise-term');
            Pagewise.forceTouch(true); t.click();
            var p = document.querySelector('.pagewise-popup');
            return JSON.stringify({visible: p && p.style.display, texto: p && p.textContent,
                abribles: document.querySelectorAll('.pagewise-abrible').length});
        })()""", popup)
    except Exception as e:
        fallo(e)

def popup(r):
    try:
        paso("popup", json.loads(r))
        js("""Pagewise.py({cmd:'mas', variantes:['arteria femoral']}, function(r){ window.__mas = r; });
              Pagewise.py({cmd:'buscar', q:'ligamento inguinal'}, function(r){ window.__buscar = r; });
              Pagewise.py({cmd:'archivo', nombre:'_pagewise_glosario.json'}, function(r){ window.__arch = r; }); 1""",
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
    js("""JSON.stringify({terminos: Array.prototype.map.call(document.querySelectorAll('.pagewise-term'),
        function(e){return e.textContent;}), scripts: document.querySelectorAll('script[src*="pagewise"]').length})""", reverso)

def reverso(r):
    try:
        paso("reverso", json.loads(r))
        # Diálogos de la fase d.
        from pagewise.ui import gestor, editor_glosario, visor
        g = gestor.GestorFuentes(mw)
        paso("gestor", {"filas": g.tabla.rowCount(), "estado": g.estado.text(),
                        "nombre": g.tabla.item(0, 1).text()})
        g.close()
        e = editor_glosario.EditorGlosario(mw)
        paso("editor", [e.tabla.item(i, 1).text() for i in range(e.tabla.rowCount())])
        e.modificado = False
        e.close()
        # Pagewise Pro: versión gratuita, licencia inválida, activación y retirada.
        from pagewise import core, ed25519, licencia
        from pagewise.ui import pro
        if licencia.edicion_pro():
            # Paquete de la edición Pro (./build.sh --pro): sin licencia ni límite.
            d = pro.DialogoPro(mw)
            paso("pro", {"edicion_pro": True, "estado": d.estado.text(), "es_pro": core.es_pro(),
                         "huecos": core.huecos_para_fuentes(), "campo_licencia": hasattr(d, "campo")})
            d.close()
            return seguir_tras_pro()
        privada = bytes(range(32))                      # clave SOLO de esta prueba
        real = licencia.CLAVE_PUBLICA
        d = pro.DialogoPro(mw, por_limite=True)
        r = {"gratis": d.estado.text(), "huecos_gratis": core.huecos_para_fuentes(), "es_pro_antes": core.es_pro()}
        d.campo.setPlainText(licencia.emitir(privada, "ana@correo.es"))   # firmada con una clave que no es la del add-on
        d._activar()
        r["rechaza_clave_ajena"] = d.mensaje.text()[:40]
        licencia.CLAVE_PUBLICA = ed25519.clave_publica(privada)
        try:
            d.campo.setPlainText("  " + licencia.emitir(privada, "ana@correo.es", caduca="2099-12-31") + "\n")
            d._activar()
            r.update({"pro": d.estado.text(), "es_pro": core.es_pro(), "huecos_pro": core.huecos_para_fuentes()})
            g2 = gestor.GestorFuentes(mw)
            r["gestor"] = g2.estado.text().split("\n")[-1]
            g2.close()
            d._quitar()
            r.update({"tras_quitar": core.es_pro(), "archivo": os.path.exists(core.LICENCIA_PATH)})
        finally:
            licencia.CLAVE_PUBLICA = real
        d.close()
        paso("pro", r)
        seguir_tras_pro()
    except Exception as e:
        fallo(e)

def seguir_tras_pro():
    try:
        from pagewise.ui import tipos_nota
        tn = tipos_nota.DialogoTiposNota(mw)
        paso("tipos_nota", [tn.lista.item(i).text() + ":" + str(tn.lista.item(i).checkState() == 2 or
              tn.lista.item(i).checkState().value == 2) for i in range(tn.lista.count())])
        tn.close()
        js("Pagewise.py({cmd:'abrir', fuente:1, pagina:2, q:'nervio ciático', frase:true}); 1",
           lambda _: QTimer.singleShot(8000, leer_visor))
    except Exception as e:
        fallo(e)

def leer_visor():
    """El visor (pdf.js) debe estar en la página pedida y con el texto resaltado."""
    try:
        from pagewise.ui import visor
        d = visor._dialogo
        paso("visor", {"abierto": d is not None and d.isVisible(), "cargado_ok": d and d.cargado_ok,
                       "alternativa": d and d.alternativa_usada, "url": d and d.web.url().toString(),
                       "titulo": d and d.titulo.text(), "modo": d and d.modo, "pdfjs_listo": d and d.pdfjs_listo})
        d.web.page().runJavaScript("window.pagewiseEstado ? JSON.stringify(pagewiseEstado()) : ''", visor_estado)
    except Exception as e:
        fallo(e)

def visor_estado(texto):
    try:
        from pagewise.ui import visor
        d = visor._dialogo
        paso("visor_pdfjs", json.loads(texto) if texto else None)
        d.grab().save(os.environ["PAGEWISE_E2E_SALIDA"] + ".visor.png")
        # Mismo libro, otra página y otro texto: salta sin recargar.
        visor.abrir(1, 3, "bíceps braquial")
        QTimer.singleShot(3000, lambda: d.web.page().runJavaScript(
            "JSON.stringify(pagewiseEstado())", visor_segundo))
    except Exception as e:
        fallo(e)

def visor_segundo(texto):
    try:
        from pagewise.ui import visor
        d = visor._dialogo
        paso("visor_pdfjs_2", json.loads(texto) if texto else None)
        d.reject()
        probar_ajustes_y_explicar()
    except Exception as e:
        fallo(e)

def probar_ajustes_y_explicar():
    """Ajustes (visor del sistema) y botón «Explicar», con Claude simulado (sin red)."""
    try:
        from pagewise import core, explicar
        from pagewise.ui import ajustes, visor
        r = {}
        # 1) Ajustes: elegir el visor del sistema y guardar.
        d = ajustes.DialogoAjustes(mw)
        d.show()
        d.grab().save(SALIDA + ".ajustes.png")
        r["visor_inicial"] = "sistema" if d.r_sistema.isChecked() else "pagewise"
        d.r_sistema.setChecked(True)
        d._guardar()
        r["visor_guardado"] = core.config()["visor_pdf"]
        abiertos = []
        original = visor.abrir_con_sistema
        visor.abrir_con_sistema = lambda ruta: abiertos.append(os.path.basename(ruta))
        try:
            visor.abrir(1, 2, "aorta")
        finally:
            visor.abrir_con_sistema = original
        r["abierto_con_sistema"] = abiertos
        d = ajustes.DialogoAjustes(mw)
        d.r_pagewise.setChecked(True)
        d._guardar()
        r["visor_restaurado"] = core.config()["visor_pdf"]
        paso("ajustes", r)
        # 2) Explicar: en la gratuita pide Pro; con Pro y clave, explica.
        estado["explicar"] = {}
        pedido = []

        def falso(clave, termino, fuentes, tarjeta, idioma, modelo, esfuerzo, proveedor="anthropic"):
            pedido.append({"proveedor": proveedor, "clave": clave, "termino": termino, "n_fuentes": len(fuentes),
                           "fragmentos": sum(len(f["fragmentos"]) for f in fuentes),
                           "tarjeta": tarjeta[:40], "modelo": modelo, "esfuerzo": esfuerzo})
            return "Explicación simulada de %s (Apuntes de prueba, p. 1).\n\nSegundo párrafo." % termino

        estado["pedido"] = pedido
        estado["restaurar"] = (explicar.explicar, core.es_pro, core.clave_api)
        explicar.explicar = falso
        ABRIR_EXPLICAR = """(function(){ Pagewise.cerrar(); var t = document.querySelector('.pagewise-term');
            Pagewise.forceTouch(true); t.click();
            var b = Array.prototype.filter.call(document.querySelectorAll('.pagewise-accion'),
                function(x){ return x.textContent === 'Explicar' || x.textContent === 'Explain'; })[0];
            if (!b) return 'sin boton'; b.click(); return 'ok'; })()"""
        es_pro_real = core.es_pro()
        estado["es_pro_real"] = es_pro_real
        if not es_pro_real:
            js(ABRIR_EXPLICAR, lambda _: QTimer.singleShot(800, lambda: leer_explicar("gratis", ABRIR_EXPLICAR)))
        else:
            leer_explicar("gratis", ABRIR_EXPLICAR, saltar=True)
    except Exception as e:
        fallo(e)

estado = {}

def cerrar_dialogos():
    for w in mw.app.topLevelWidgets():
        if w.isVisible() and w.__class__.__name__ in ("DialogoPro", "DialogoAjustes"):
            estado.setdefault("dialogos", []).append(w.__class__.__name__)
            w.reject()

def leer_explicar(fase, abrir_js, saltar=False):
    from pagewise import core
    def leido(texto):
        try:
            if not saltar:
                estado["explicar"][fase] = texto
            if fase == "pro":
                mw.reviewer.web.grab().save(SALIDA + ".explicar.png")
            cerrar_dialogos()
            if fase == "gratis":
                core.es_pro = lambda: True
                core.clave_api = lambda: "sk-ant-prueba"
                js(abrir_js, lambda _: QTimer.singleShot(1500, lambda: leer_explicar("pro", abrir_js)))
            elif fase == "pro":
                # Misma tarjeta con ChatGPT elegido en Ajustes.
                c = core.config()
                c["explicar_proveedor"] = "openai"
                core.guardar_config(c)
                js(abrir_js, lambda _: QTimer.singleShot(1500, lambda: leer_explicar("openai", abrir_js)))
            else:
                c = core.config()
                c["explicar_proveedor"] = "anthropic"
                core.guardar_config(c)
                acabar_explicar()
        except Exception as e:
            fallo(e)
    js("""JSON.stringify({texto: (document.querySelector('.pagewise-popup .pagewise-cuerpo')||{}).textContent || '',
        parrafos: document.querySelectorAll('.pagewise-explicacion p').length})""", leido)

def acabar_explicar():
    try:
        from pagewise import core, explicar
        explicar.explicar, core.es_pro, core.clave_api = estado["restaurar"]
        paso("explicar", {"popup": {k: json.loads(v) for k, v in estado["explicar"].items()},
                          "pedido": estado["pedido"], "es_pro_real": estado["es_pro_real"],
                          "dialogos": estado.get("dialogos", [])})
        if GRANDE:
            visor_grande()
            return
        terminar()
    except Exception as e:
        fallo(e)

def memoria_mb():
    """Memoria (PSS) de Anki y sus procesos hijos (los de Chromium). Solo Linux."""
    try:
        padres = {}
        for pid in os.listdir("/proc"):
            if pid.isdigit():
                try:
                    with open("/proc/%s/stat" % pid) as f:
                        padres[int(pid)] = int(f.read().rsplit(")", 1)[1].split()[1])
                except (OSError, ValueError, IndexError):
                    pass
        mios = {os.getpid()}
        cambio = True
        while cambio:
            cambio = False
            for pid, padre in padres.items():
                if padre in mios and pid not in mios:
                    mios.add(pid)
                    cambio = True
        kb = 0
        for pid in mios:
            try:
                with open("/proc/%d/smaps_rollup" % pid) as f:
                    kb += sum(int(l.split()[1]) for l in f if l.startswith("Pss:"))
            except (OSError, ValueError):
                pass
        return kb // 1024
    except Exception:
        return None

def visor_grande():
    """Opcional (--pdf-grande=RUTA): abre un PDF enorme por la mitad, con
    resaltado, y apunta cuánto tarda y cuánta memoria gasta."""
    import time
    try:
        from pagewise import core
        from pagewise.ui import visor
        nombre = "grande-e2e.pdf"
        destino = os.path.join(core.PDFS_DIR, nombre)
        os.makedirs(core.PDFS_DIR, exist_ok=True)
        try:
            os.link(GRANDE, destino)
        except OSError:
            os.symlink(GRANDE, destino)
        sid = core.indice().agregar_fuente("Grande", nombre, GRANDE, 0, "e2e-grande")
        core.indice().marcar_lista(sid)
        pagina = int(os.environ.get("PAGEWISE_E2E_GRANDE_PAGINA") or 2)
        buscar = os.environ.get("PAGEWISE_E2E_GRANDE_BUSCAR") or ""
        antes = memoria_mb()
        t0 = time.time()
        visor.abrir(sid, pagina, buscar)
        d = visor._dialogo
        pico = [antes or 0]

        def mirar():
            d.web.page().runJavaScript("window.pagewiseEstado ? JSON.stringify(pagewiseEstado()) : ''", leido)

        def leido(texto):
            try:
                estado = json.loads(texto) if texto else {}
                pico[0] = max(pico[0], memoria_mb() or 0)
                seg = time.time() - t0
                hecho = estado.get("listo") and estado.get("pagina") == pagina and (
                    not buscar or estado.get("paginaCoincidencia") == pagina)
                if hecho or seg > 240 or d.modo != "pdfjs":
                    paso("visor_grande", {"mb_archivo": os.path.getsize(GRANDE) >> 20, "segundos": round(seg, 1),
                                          "mb_antes": antes, "mb_pico": pico[0], "modo": d.modo, "estado": estado})
                    d.grab().save(os.environ["PAGEWISE_E2E_SALIDA"] + ".grande.png")
                    d.reject()
                    terminar()
                else:
                    QTimer.singleShot(1000, mirar)
            except Exception as e:
                fallo(e)

        QTimer.singleShot(1000, mirar)
    except Exception as e:
        fallo(e)

def terminar():
    try:
        if PLANTILLAS:
            from pagewise import templates
            basico = mw.col.models.by_name("Basic") or mw.col.models.by_name("Básico")
            paso("desactivado", templates.desactivar(mw.col, [basico["id"]]))
            paso("qfmt_final", mw.col.models.get(basico["id"])["tmpls"][0]["qfmt"])
        res["ok"] = True
        guardar()
    except Exception as e:
        fallo(e)
        return
    mw.unloadProfileAndExit()

if MIGRACION:
    gui_hooks.profile_did_open.append(lambda: QTimer.singleShot(1800, cerrar_aviso))
gui_hooks.profile_did_open.append(lambda: QTimer.singleShot(3000 if MIGRACION else 1500, empezar))
QTimer.singleShot(90000, lambda: (res.update({"error": res.get("error") or "tiempo agotado"}), guardar(), os._exit(1)))
'''


def main():
    plantillas = "--plantillas" in sys.argv
    base = tempfile.mkdtemp(prefix="anki-e2e-")
    addons = os.path.join(base, "addons21")
    os.makedirs(addons)
    paquete = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--paquete=")), None)
    if paquete:
        # Instala el .ankiaddon tal y como lo haría el usuario.
        import zipfile
        zipfile.ZipFile(paquete).extractall(os.path.join(addons, "pagewise"))
    else:
        os.symlink(os.path.join(RAIZ, "pagewise"), os.path.join(addons, "pagewise"))
    os.makedirs(os.path.join(addons, "zz_piloto"))
    with open(os.path.join(addons, "zz_piloto", "__init__.py"), "w") as f:
        f.write(PILOTO)
    sys.path.insert(0, os.path.join(RAIZ, "dev"))
    import generar_pdfs
    pdf = generar_pdfs.generar_apuntes(os.path.join(base, "apuntes.pdf"))
    salida = os.path.join(base, "resultado.json")
    migracion = "--migracion" in sys.argv
    if migracion:
        # Simula el add-on antiguo instalado, con sus datos, y medios antiguos en la colección.
        viejo = os.path.join(addons, "fuentes")
        os.makedirs(os.path.join(viejo, "user_files"))
        open(os.path.join(viejo, "__init__.py"), "w").close()
        sys.path.insert(0, RAIZ)
        from pagewise import glossary, importer
        from pagewise.index import Indice
        ind = Indice(os.path.join(viejo, "user_files", "index.sqlite3"))
        importer.importar_pdf(ind, pdf, os.path.join(viejo, "user_files", "pdfs"), nombre="Libro antiguo")
        ind.cerrar()
        glossary.guardar(os.path.join(viejo, "user_files", "glosario.json"),
                         [{"termino": "aorta", "sinonimos": [], "activo": True}])
        medios = os.path.join(base, "Prueba", "collection.media")
        os.makedirs(medios)
        for n in ("_fuentes.js", "_fuentes_glosario.json", "_fuentes_t_aorta_0.json"):
            open(os.path.join(medios, n), "w").close()
    grande = next((os.path.abspath(a.split("=", 1)[1]) for a in sys.argv if a.startswith("--pdf-grande=")), "")
    entorno = dict(os.environ, PAGEWISE_E2E_SALIDA=salida, PAGEWISE_E2E_PDF=pdf, PAGEWISE_E2E_GRANDE=grande,
                   PAGEWISE_E2E_MIGRACION="1" if migracion else "0",
                   PAGEWISE_E2E_PLANTILLAS="1" if plantillas else "0",
                   QTWEBENGINE_CHROMIUM_FLAGS="--no-sandbox", QTWEBENGINE_DISABLE_SANDBOX="1",
                   QT_QPA_PLATFORM=os.environ.get("QT_QPA_PLATFORM", "offscreen"))
    # Los datos del add-on (user_files) se crean en la carpeta del repositorio:
    # los apartamos para no mezclarlos con los del desarrollador.
    uf = os.path.join(RAIZ, "pagewise", "user_files")
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
        "pm.meta['firstRun'] = False; pm.meta['defaultLang'] = sys.argv[2]; pm.save()"), base,
        "en_US" if "--ingles" in sys.argv else "es_ES"],
        env=entorno, check=True)
    try:
        subprocess.run([sys.executable, "-c", "import aqt; aqt.run()", "-b", base, "-p", "Prueba"], env=entorno, timeout=420 if grande else 150,
                       stdout=subprocess.DEVNULL if "-q" in sys.argv else None)
    finally:
        shutil.rmtree(uf, ignore_errors=True)
        os.rename(respaldo, uf)  # rename (no move) para no anidar carpetas
        for p in ("meta.json",):
            ruta = os.path.join(RAIZ, "pagewise", p)
            if os.path.exists(ruta):
                os.remove(ruta)
    with open(salida) as f:
        res = json.load(f)
    for captura in ("visor", "asistente", "grande", "ajustes", "explicar"):  # capturas para revisar a ojo
        if os.path.exists("%s.%s.png" % (salida, captura)):
            shutil.copy("%s.%s.png" % (salida, captura),
                        os.path.join(tempfile.gettempdir(), "pagewise-e2e-%s.png" % captura))
    print(json.dumps(res, ensure_ascii=False, indent=1))
    fallos = []
    if res.get("ok") and not migracion:
        # El visor abre la página pedida con el texto resaltado, y al pedir
        # otra página del mismo libro salta y resalta sin recargar.
        v1, v2 = res.get("visor_pdfjs") or {}, res.get("visor_pdfjs_2") or {}
        if (res.get("visor") or {}).get("modo") != "pdfjs":
            fallos.append("el visor no ha usado pdf.js")
        if not (v1.get("pagina") == 2 and v1.get("paginaCoincidencia") == 2 and v1.get("resaltadas", 0) >= 1):
            fallos.append("no resalta el término en la página 2: %s" % v1)
        if not (v2.get("pagina") == 3 and v2.get("paginaCoincidencia") == 3 and v2.get("resaltadas", 0) >= 1):
            fallos.append("no salta/resalta en la página 3: %s" % v2)
        if "aortas" not in (res.get("anverso") or {}).get("terminos", []):
            fallos.append("no subraya el plural «aortas»: %s" % (res.get("anverso") or {}).get("terminos"))
        p = res.get("pro") or {}
        if p.get("edicion_pro") and not (p.get("es_pro") and p.get("huecos") is None and not p.get("campo_licencia")):
            fallos.append("la edición Pro no quita el límite: %s" % p)
        aj = res.get("ajustes") or {}
        if not (aj.get("visor_guardado") == "sistema" and aj.get("abierto_con_sistema")
                and aj.get("visor_restaurado") == "pdfjs"):
            fallos.append("el ajuste del visor no funciona: %s" % aj)
        ex = res.get("explicar") or {}
        pro_popup = (ex.get("popup") or {}).get("pro") or {}
        if not (pro_popup.get("parrafos") == 2 and "Explicación simulada" in pro_popup.get("texto", "")
                and ex.get("pedido") and ex["pedido"][0]["fragmentos"] > 0):
            fallos.append("«Explicar» no muestra la explicación: %s" % ex)
        oa = (ex.get("popup") or {}).get("openai") or {}
        if not (("Explicación de ChatGPT" in oa.get("texto", "") or "Explanation by ChatGPT" in oa.get("texto", "")) and len(ex.get("pedido") or []) == 2
                and ex["pedido"][1]["proveedor"] == "openai" and ex["pedido"][1]["modelo"] == "gpt-5"):
            fallos.append("«Explicar» con ChatGPT no funciona: %s" % ex)
        if not ex.get("es_pro_real") and "Pro" not in ((ex.get("popup") or {}).get("gratis") or {}).get("texto", ""):
            fallos.append("en la gratuita «Explicar» no pide Pro: %s" % ex)
        g = res.get("visor_grande")
        if grande and not (g and g["modo"] == "pdfjs" and g["estado"].get("listo")):
            fallos.append("el PDF grande no se ha abierto con pdf.js: %s" % g)
    for f in fallos:
        print("FALLO:", f)
    sys.exit(0 if res.get("ok") and not fallos else 1)


if __name__ == "__main__":
    main()
