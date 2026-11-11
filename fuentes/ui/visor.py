# -*- coding: utf-8 -*-
"""Visor de PDF dentro de Anki (solo escritorio).

Usa QWebEngineView con el visor de PDF integrado de Chromium y abre
"archivo.pdf#page=N". Si esta instalación de Qt no puede mostrar PDFs (el
PDF se intenta descargar, o la carga falla) se recurre al visor del sistema.
"""
import os

from aqt import mw
from aqt.qt import (QDesktopServices, QDialog, QHBoxLayout, QLabel, QPushButton, QUrl,
                    QVBoxLayout, QWebEngineSettings, QWebEngineView)
from aqt.utils import restoreGeom, saveGeom, showWarning, tooltip

from .. import core

_dialogo = None


def ruta_pdf(source_id):
    f = core.indice().fuente(source_id)
    return (os.path.join(core.PDFS_DIR, f["archivo"]), f["nombre"]) if f else (None, None)


def abrir_con_sistema(ruta):
    QDesktopServices.openUrl(QUrl.fromLocalFile(ruta))


class VisorPDF(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fuentes")
        self.ruta = None
        # Nota: el visor de PDF de Chromium no siempre emite loadFinished para
        # el PDF; solo lo usamos para detectar fallos explícitos.
        self.cargado_ok = None
        self.alternativa_usada = False
        capa = QVBoxLayout(self)
        capa.setContentsMargins(6, 6, 6, 6)
        barra = QHBoxLayout()
        self.titulo = QLabel()
        barra.addWidget(self.titulo, 1)
        externo = QPushButton("Abrir con el visor del sistema")
        externo.clicked.connect(lambda: self.ruta and abrir_con_sistema(self.ruta))
        barra.addWidget(externo)
        capa.addLayout(barra)

        self.web = QWebEngineView(self)
        ajustes = self.web.settings()
        ajustes.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        if hasattr(QWebEngineSettings.WebAttribute, "PdfViewerEnabled"):
            ajustes.setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)
        # Si Qt no sabe mostrar el PDF, lo "descarga": lo cancelamos y usamos el sistema.
        self.web.page().profile().downloadRequested.connect(self._descarga)
        self.web.loadFinished.connect(self._cargado)
        capa.addWidget(self.web)
        self.resize(900, 1000)
        restoreGeom(self, "fuentes_visor")

    def mostrar(self, ruta, pagina, nombre):
        self.ruta = ruta
        self.cargado_ok = None
        self.alternativa_usada = False
        self.titulo.setText("%s — página %d" % (nombre, pagina))
        self.setWindowTitle("Fuentes: %s" % nombre)
        url = QUrl.fromLocalFile(ruta)
        url.setFragment("page=%d" % pagina)
        # Pasar por about:blank fuerza la recarga aunque sea el mismo archivo
        # (si no, cambiar solo el #page no siempre mueve el visor).
        self.web.setUrl(QUrl("about:blank"))
        self.web.setUrl(url)
        self.show()
        self.raise_()
        self.activateWindow()

    def _cargado(self, ok):
        if self.web.url().scheme() != "file":
            return
        self.cargado_ok = ok
        if not ok:
            self._alternativa()

    def _descarga(self, descarga):
        # El perfil web es compartido con Anki: solo tocamos NUESTRO PDF.
        try:
            if not self.ruta or descarga.url().toLocalFile() != self.ruta:
                return
            descarga.cancel()
        except Exception:
            return
        self._alternativa()

    def _alternativa(self):
        if self.ruta and not self.alternativa_usada:
            self.alternativa_usada = True
            tooltip("Este Anki no puede mostrar el PDF dentro; se abre con el visor del sistema.")
            abrir_con_sistema(self.ruta)
            self.hide()

    def reject(self):
        saveGeom(self, "fuentes_visor")
        self.web.setUrl(QUrl("about:blank"))  # libera memoria del PDF
        super().reject()


def abrir(source_id, pagina=1):
    global _dialogo
    ruta, nombre = ruta_pdf(source_id)
    if not ruta or not os.path.exists(ruta):
        showWarning("No se encuentra el PDF de esta fuente. Elimínala y vuelve a importarla.")
        return
    try:
        if _dialogo is None:
            _dialogo = VisorPDF(mw)
        _dialogo.mostrar(ruta, max(1, pagina), nombre)
    except Exception as e:
        print("Fuentes: visor integrado no disponible (%s); uso el del sistema." % e)
        abrir_con_sistema(ruta)
