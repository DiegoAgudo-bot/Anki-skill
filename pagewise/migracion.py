# -*- coding: utf-8 -*-
"""Migración desde el nombre anterior del add-on («Fuentes»).

Quien instaló la versión antigua tiene sus datos en la carpeta del add-on
«fuentes» y archivos «_fuentes*» en sus medios y plantillas. Aquí:

  1. migrar_datos(): copia el índice, el glosario, los PDFs y la
     configuración a Pagewise y desactiva el add-on antiguo.
  2. migrar_perfil(): borra los medios antiguos y actualiza el bloque de las
     plantillas al nombre nuevo.

Si no hay nada antiguo, no hace nada.
"""
import os
import shutil

from . import templates

MODULO_ANTIGUO = "fuentes"
PREFIJO_ANTIGUO = "_fuentes"
ARCHIVOS = ("index.sqlite3", "index.sqlite3-wal", "index.sqlite3-shm", "glosario.json")


def copiar_datos(uf_antiguo, uf_nuevo):
    """Copia los datos de usuario si existen y Pagewise aún no tiene los suyos.

    Devuelve True si copió algo. No borra nada del add-on antiguo.
    """
    hay_antiguos = any(os.path.exists(os.path.join(uf_antiguo, n)) for n in ("index.sqlite3", "glosario.json"))
    hay_nuevos = any(os.path.exists(os.path.join(uf_nuevo, n)) for n in ("index.sqlite3", "glosario.json"))
    if not hay_antiguos or hay_nuevos:
        return False
    os.makedirs(uf_nuevo, exist_ok=True)
    for nombre in ARCHIVOS:
        origen = os.path.join(uf_antiguo, nombre)
        if os.path.exists(origen):
            shutil.copy2(origen, os.path.join(uf_nuevo, nombre))
    pdfs = os.path.join(uf_antiguo, "pdfs")
    if os.path.isdir(pdfs) and not os.path.exists(os.path.join(uf_nuevo, "pdfs")):
        shutil.copytree(pdfs, os.path.join(uf_nuevo, "pdfs"))
    return True


def borrar_medios_antiguos(carpeta_medios):
    """Elimina los archivos «_fuentes*» de la carpeta de medios. Devuelve cuántos."""
    n = 0
    for nombre in os.listdir(carpeta_medios):
        if nombre.startswith(PREFIJO_ANTIGUO):
            try:
                os.remove(os.path.join(carpeta_medios, nombre))
                n += 1
            except OSError:
                pass
    return n


def actualizar_plantillas(col):
    """Cambia el bloque antiguo de las plantillas por el de Pagewise. Devuelve cuántos tipos de nota."""
    ids = []
    for item in col.models.all_names_and_ids():
        nt = col.models.get(item.id)
        if any(templates.tiene_antiguo(t[lado]) for t in nt["tmpls"] for lado in ("qfmt", "afmt")):
            ids.append(item.id)
    return templates.activar(col, ids, solo_con_bloque=True)


# --- Con Anki ---------------------------------------------------------------

_migrado_ahora = False


def migrar_datos():
    """Al cargar el add-on, antes de abrir el índice."""
    global _migrado_ahora
    from aqt import mw

    from . import core

    antiguo = os.path.join(os.path.dirname(core.ADDON_DIR), MODULO_ANTIGUO)
    try:
        if not copiar_datos(os.path.join(antiguo, "user_files"), core.USER_FILES):
            return
        conf = mw.addonManager.getConfig(MODULO_ANTIGUO)
        if conf:
            conf = dict(conf, asistente_visto=True)
            core.guardar_config(conf)
        # Dos add-ons a la vez subrayarían doble: el antiguo queda desactivado.
        mw.addonManager.toggleEnabled(MODULO_ANTIGUO, enable=False)
        _migrado_ahora = True
    except Exception as e:  # una migración fallida no debe impedir arrancar
        print("Pagewise: no se pudieron migrar los datos de Fuentes: %s" % e)


def migrar_perfil():
    """Al abrir un perfil (ya hay colección)."""
    global _migrado_ahora
    from aqt import mw
    from aqt.utils import showInfo

    from . import core
    from .i18n import tr

    try:
        medios = core.carpeta_medios()
        if medios and borrar_medios_antiguos(medios):
            core.exportar(silencioso=True)
        if mw.col:
            actualizar_plantillas(mw.col)
    except Exception as e:
        print("Pagewise: no se pudo completar la migración del perfil: %s" % e)
    if _migrado_ahora:
        _migrado_ahora = False
        # Con un pequeño retraso: un aviso modal aquí mismo detendría el
        # arranque del perfil (y a los demás complementos) hasta cerrarlo.
        from aqt.qt import QTimer

        QTimer.singleShot(600, lambda: showInfo(tr("Fuentes ahora se llama Pagewise.\n\nTus PDFs, tu índice y tu glosario se han copiado a "
                    "Pagewise y el complemento antiguo ha quedado desactivado.\n\nReinicia Anki. Después puedes "
                    "eliminar «Fuentes» en Herramientas → Complementos."), parent=mw, title="Pagewise"))
