# -*- coding: utf-8 -*-
"""Integración con el repaso en Anki escritorio.

- card_will_show: si la plantilla NO trae ya el snippet de Fuentes, inyecta
  el JS y el CSS servidos desde la carpeta del add-on (setWebExports).
  Si la plantilla ya lo trae (activado para móvil), no se inyecta otra vez.
- webview_did_receive_js_message: atiende los mensajes "fuentes:{json}" que
  manda el JS con pycmd. Son solo EXTRAS de escritorio: abrir el PDF, buscar
  más fragmentos en el índice y búsqueda de texto libre.
"""
import json
import os

from . import core
from .providers import ProveedorFTS

MARCA_JS = "_fuentes.js"
PREFIJO_MSG = "fuentes:"


def al_mostrar_tarjeta(texto, card, kind):
    c = core.config()
    if not (c["inyectar_en_escritorio"] and c["subrayado"]) or MARCA_JS in texto or "/web/fuentes.js" in texto:
        return texto
    base = "/_addons/%s/web/" % core.carpeta_addon_web()
    return texto + (
        '\n<link rel="stylesheet" href="%sfuentes.css">'
        '\n<script src="%sfuentes.js"></script>' % (base, base)
    )


# ------------------------------------------------------------- mensajes pycmd

def _cmd_abrir(msg):
    from .ui import visor

    visor.abrir(int(msg["fuente"]), int(msg.get("pagina") or 1))
    return {"ok": True}


def _cmd_mas(msg):
    c = core.config()
    prov = ProveedorFTS(core.indice(), max_caracteres=max(600, c["max_caracteres_fragmento"]))
    fuentes = prov.fragmentos([str(v) for v in msg.get("variantes", [])][:20], core.fuentes_activas(), 10)
    return {"ok": True, "fuentes": fuentes}


def _cmd_buscar(msg):
    q = str(msg.get("q", ""))[:200]
    prov = ProveedorFTS(core.indice(), max_caracteres=500)
    fuentes, palabras = prov.buscar_libre(q, core.fuentes_activas(), 5)
    return {"ok": True, "fuentes": fuentes, "resaltar": palabras}


def _cmd_archivo(msg):
    """Plan B si fetch/XHR fallan en escritorio: leer un JSON de los medios."""
    nombre = str(msg.get("nombre", ""))
    if not nombre.startswith("_fuentes") or not nombre.endswith(".json") or os.path.basename(nombre) != nombre:
        return {"ok": False}
    ruta = os.path.join(core.carpeta_medios() or "", nombre)
    try:
        with open(ruta, encoding="utf-8") as f:
            return {"ok": True, "datos": json.load(f)}
    except (IOError, OSError, ValueError):
        return {"ok": False}


COMANDOS = {"abrir": _cmd_abrir, "mas": _cmd_mas, "buscar": _cmd_buscar, "archivo": _cmd_archivo}


def al_recibir_mensaje(handled, mensaje, contexto):
    if not isinstance(mensaje, str) or not mensaje.startswith(PREFIJO_MSG):
        return handled
    try:
        msg = json.loads(mensaje[len(PREFIJO_MSG):])
        funcion = COMANDOS.get(msg.get("cmd"))
        if funcion is None:
            return (True, {"ok": False, "error": "comando desconocido"})
        return (True, funcion(msg))
    except Exception as e:
        print("Fuentes: error en el mensaje %r: %s" % (mensaje[:200], e))
        return (True, {"ok": False, "error": str(e)})
