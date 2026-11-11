# -*- coding: utf-8 -*-
"""Abrir el PDF de una fuente en una página (provisional: visor del sistema)."""
import os

from aqt.qt import QDesktopServices, QUrl
from aqt.utils import showWarning

from .. import core


def ruta_pdf(source_id):
    f = core.indice().fuente(source_id)
    return os.path.join(core.PDFS_DIR, f["archivo"]) if f else None


def abrir(source_id, pagina=1):
    ruta = ruta_pdf(source_id)
    if not ruta or not os.path.exists(ruta):
        showWarning("No se encuentra el PDF de esta fuente. Vuelve a importarlo.")
        return
    QDesktopServices.openUrl(QUrl.fromLocalFile(ruta))
