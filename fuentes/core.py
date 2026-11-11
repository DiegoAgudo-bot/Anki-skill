# -*- coding: utf-8 -*-
"""Estado compartido del add-on dentro de Anki: rutas, configuración,
índice y exportación a la carpeta de medios.
"""
import json
import os

from aqt import mw
from aqt.utils import tooltip

from . import exporter, glossary
from .index import Indice

ADDON_DIR = os.path.dirname(os.path.abspath(__file__))
MODULO = __name__.split(".")[0]
WEB_DIR = os.path.join(ADDON_DIR, "web")
USER_FILES = os.path.join(ADDON_DIR, "user_files")
PDFS_DIR = os.path.join(USER_FILES, "pdfs")
INDEX_PATH = os.path.join(USER_FILES, "index.sqlite3")
GLOSARIO_PATH = os.path.join(USER_FILES, "glosario.json")
CACHE_PATH = os.path.join(USER_FILES, "export_cache.json")

DEFECTO = {
    "subrayado": True,
    "fragmentos_por_fuente": 3,
    "max_caracteres_fragmento": 300,
    "solo_primera_aparicion": True,
    "fuentes_inactivas": [],
    "aviso_tamano_mb": 50,
    "inyectar_en_escritorio": True,
}

_indice = None


def carpeta_addon_web():
    """Nombre de la carpeta del add-on tal y como la sirve Anki (/_addons/<x>/)."""
    return mw.addonManager.addonFromModule(MODULO)


def config():
    c = dict(DEFECTO)
    c.update(mw.addonManager.getConfig(MODULO) or {})
    return c


def guardar_config(c):
    mw.addonManager.writeConfig(MODULO, c)


def indice():
    """Conexión al índice para el hilo principal (las tareas en segundo plano abren la suya)."""
    global _indice
    if _indice is None:
        os.makedirs(USER_FILES, exist_ok=True)
        _indice = Indice(INDEX_PATH)
    return _indice


def cerrar_indice():
    global _indice
    if _indice is not None:
        _indice.cerrar()
        _indice = None


def terminos():
    return glossary.cargar(GLOSARIO_PATH)


def guardar_terminos(ts):
    os.makedirs(USER_FILES, exist_ok=True)
    return glossary.guardar(GLOSARIO_PATH, ts)


def carpeta_medios():
    return mw.col.media.dir() if mw.col else None


def fuentes_activas():
    inactivas = set(config()["fuentes_inactivas"])
    return [f["id"] for f in indice().fuentes() if f["estado"] == "lista" and f["id"] not in inactivas]


# ---------------------------------------------------------------- exportación

def _leer_cache():
    try:
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (IOError, OSError, ValueError):
        return {}


def _guardar_cache(todo):
    temporal = CACHE_PATH + ".tmp"
    with open(temporal, "w", encoding="utf-8") as f:
        json.dump(todo, f)
    os.replace(temporal, CACHE_PATH)


_exportando = False
_repetir = False


def exportar(silencioso=False, al_terminar=None):
    """Exporta los datos del móvil a los medios del perfil abierto, en segundo plano.

    Si ya hay una exportación en marcha, se encola otra al terminar.
    """
    global _exportando, _repetir
    medios = carpeta_medios()
    if not medios:
        return
    if _exportando:
        _repetir = True
        return
    _exportando = True
    ajustes = config()
    ts = terminos()

    def tarea():
        ind = Indice(INDEX_PATH)  # conexión propia para este hilo
        try:
            todo = _leer_cache()
            cache = todo.get(medios, {})
            inf = exporter.exportar(ind, ts, medios, WEB_DIR, ajustes, cache=cache)
            todo[medios] = cache
            _guardar_cache(todo)
            return inf
        finally:
            ind.cerrar()

    def terminado(fut):
        global _exportando, _repetir
        _exportando = False
        try:
            inf = fut.result()
        except Exception as e:  # no tumbar Anki por un fallo al exportar
            tooltip("Fuentes: error al exportar los datos para el móvil: %s" % e)
            inf = None
        if inf is not None and not silencioso:
            tooltip("Fuentes: %d términos exportados (%s)" % (inf.terminos, exporter.formato_tamano(inf.bytes)))
        if inf is not None and inf.bytes > ajustes["aviso_tamano_mb"] * 1024 * 1024:
            tooltip("Fuentes: los datos para el móvil ocupan %s. Considera reducir el glosario "
                    "o los fragmentos por fuente." % exporter.formato_tamano(inf.bytes), period=6000)
        if _repetir:
            _repetir = False
            exportar(silencioso, al_terminar)
        elif al_terminar:
            al_terminar(inf)

    mw.taskman.run_in_background(tarea, terminado)


def tamano_exportado():
    medios = carpeta_medios()
    return exporter.tamano_exportado(medios) if medios else 0


def al_abrir_perfil():
    """Al abrir un perfil: actualiza el JS/CSS en los medios y reexporta si hace falta.

    La exportación es incremental: si nada ha cambiado no escribe nada.
    """
    if os.path.exists(INDEX_PATH) or os.path.exists(GLOSARIO_PATH):
        exportar(silencioso=True)


def al_cambiar_config(_nueva):
    exportar(silencioso=True)


def al_cerrar_perfil():
    cerrar_indice()
