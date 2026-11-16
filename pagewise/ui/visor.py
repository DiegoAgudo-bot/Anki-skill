# -*- coding: utf-8 -*-
"""Visor de PDF dentro de Anki (solo escritorio).

Tres niveles, del mejor al de reserva:

1. pdf.js (web/pdfjs), servido por el servidor local de Anki. Pide el PDF
   por trozos, así que un libro de 1-2 GB se abre sin cargarlo en memoria, y
   resalta en la página el texto del fragmento en el que se ha hecho clic.
2. El visor de PDF integrado de Chromium ("archivo.pdf#page=N"): abre la
   página, sin resaltado. Se usa si pdf.js no llega a arrancar.
3. El visor del sistema, si esta instalación de Qt no sabe mostrar PDFs.

`visor_pdf` en la configuración permite forzar "chromium" o "sistema".
"""
import json
import os
from urllib.parse import quote

from aqt import mw
from aqt.qt import (QDesktopServices, QDialog, QHBoxLayout, QLabel, QPushButton, QTimer, QUrl,
                    QVBoxLayout, QWebEngineSettings, QWebEngineView)
from aqt.utils import restoreGeom, saveGeom, showWarning, tooltip

from .. import core
from ..i18n import tr

_dialogo = None


def ruta_pdf(source_id):
    f = core.indice().fuente(source_id)
    return (os.path.join(core.PDFS_DIR, f["archivo"]), f["nombre"]) if f else (None, None)


def abrir_con_sistema(ruta):
    QDesktopServices.openUrl(QUrl.fromLocalFile(ruta))


# Segundos que se espera a que pdf.js abra el documento antes de pasar al
# visor de Chromium. Solo lee la estructura del PDF, no el archivo entero.
ESPERA_PDFJS = 20
_VISOR_HTML = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "web", "pdfjs", "web", "viewer.html")


def modo_visor():
    modo = str(core.config().get("visor_pdf") or "pdfjs").lower()
    return modo if modo in ("pdfjs", "chromium", "sistema") else "pdfjs"


def fragmento_url(pagina, buscar="", frase=True):
    """Parte de la URL tras '#': página y, si hay, texto que resaltar."""
    h = "page=%d" % pagina
    if buscar:
        h += "&search=%s&phrase=%s" % (quote(buscar, safe=""), "true" if frase else "false")
    return h


# A partir de este tamaño el visor no lee el texto del libro entero para
# resaltar: solo el de las páginas cercanas (ver web/pdfjs/web/pagewise-visor.js).
MB_PDF_GRANDE = 200


def es_grande(ruta):
    try:
        return os.path.getsize(ruta) >= MB_PDF_GRANDE << 20
    except OSError:
        return False


def url_pdfjs(puerto, addon, archivo, pagina, buscar="", frase=True, idioma="", grande=False):
    """URL del visor pdf.js en el servidor local de Anki."""
    base = "/_addons/%s/" % quote(addon, safe="")
    pdf = base + "user_files/pdfs/" + quote(archivo, safe="")
    url = "http://127.0.0.1:%d%sweb/pdfjs/web/viewer.html?file=%s" % (puerto, base, quote(pdf, safe=""))
    if idioma:
        url += "&lang=" + idioma
    if grande:
        url += "&grande=1"
    return url + "#" + fragmento_url(pagina, buscar, frase)


def _puerto():
    try:
        return int(mw.mediaServer.getPort())
    except Exception:
        return 0


class VisorPDF(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pagewise")
        self.ruta = None
        self.pagina = 1
        self.modo = None          # "pdfjs" | "chromium"
        self.pdfjs_listo = False
        self._intento = 0
        # Nota: el visor de PDF de Chromium no siempre emite loadFinished para
        # el PDF; solo lo usamos para detectar fallos explícitos.
        self.cargado_ok = None
        self.alternativa_usada = False
        capa = QVBoxLayout(self)
        capa.setContentsMargins(6, 6, 6, 6)
        barra = QHBoxLayout()
        self.titulo = QLabel()
        barra.addWidget(self.titulo, 1)
        externo = QPushButton(tr("Abrir con el visor del sistema"))
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
        restoreGeom(self, "pagewise_visor")

    def mostrar(self, ruta, pagina, nombre, buscar="", frase=True):
        cambia = ruta != self.ruta
        self.ruta = ruta
        self.pagina = pagina
        self.cargado_ok = None
        self.alternativa_usada = False
        self.titulo.setText(tr("%s — página %d") % (nombre, pagina))
        self.setWindowTitle(tr("Pagewise: %s") % nombre)
        self.show()
        self.raise_()
        self.activateWindow()
        puerto = _puerto()
        if modo_visor() != "pdfjs" or not puerto or not os.path.exists(_VISOR_HTML):
            self._mostrar_chromium()
            return
        if self.modo == "pdfjs" and not cambia and self.pdfjs_listo:
            # Mismo libro ya abierto: solo saltar y resaltar, sin recargar.
            self.web.page().runJavaScript(
                "window.pagewiseIr ? pagewiseIr(%d, %s, %s) : false"
                % (pagina, json.dumps(buscar), "true" if frase else "false"))
            return
        self.modo = "pdfjs"
        self.pdfjs_listo = False
        self._intento += 1
        from ..i18n import idioma
        url = url_pdfjs(puerto, core.carpeta_addon_web(), os.path.basename(ruta), pagina, buscar, frase,
                        "es-ES" if idioma() == "es" else "en-US", es_grande(ruta))
        self.web.setUrl(QUrl("about:blank"))
        self.web.setUrl(QUrl(url))
        self._vigilar_pdfjs(self._intento, ESPERA_PDFJS * 2)

    def _vigilar_pdfjs(self, intento, quedan):
        """Comprueba que pdf.js ha abierto el documento; si no, visor de Chromium."""
        def revisar():
            if intento != self._intento or self.modo != "pdfjs" or not self.isVisible():
                return
            self.web.page().runJavaScript(
                "window.pagewiseEstado ? JSON.stringify(pagewiseEstado()) : ''", respuesta)

        def respuesta(texto):
            if intento != self._intento or self.modo != "pdfjs":
                return
            try:
                listo = bool(texto) and json.loads(texto).get("listo")
            except Exception:
                listo = False
            if listo:
                self.pdfjs_listo = True
            elif quedan > 1:
                self._vigilar_pdfjs(intento, quedan - 1)
            else:
                print("Pagewise: pdf.js no ha abierto el PDF; uso el visor integrado.")
                self._mostrar_chromium()

        QTimer.singleShot(500, revisar)

    def _mostrar_chromium(self):
        self.modo = "chromium"
        self.pdfjs_listo = False
        self._intento += 1
        url = QUrl.fromLocalFile(self.ruta)
        url.setFragment("page=%d" % self.pagina)
        # Pasar por about:blank fuerza la recarga aunque sea el mismo archivo
        # (si no, cambiar solo el #page no siempre mueve el visor).
        self.web.setUrl(QUrl("about:blank"))
        self.web.setUrl(url)

    def _cargado(self, ok):
        if self.modo == "pdfjs" and not ok and self.web.url().scheme() == "http":
            self._mostrar_chromium()  # el servidor local no ha respondido
            return
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
            tooltip(tr("Este Anki no puede mostrar el PDF dentro; se abre con el visor del sistema."))
            abrir_con_sistema(self.ruta)
            self.hide()

    def reject(self):
        saveGeom(self, "pagewise_visor")
        self.ruta = None
        self.modo = None
        self.pdfjs_listo = False
        self._intento += 1
        self.web.setUrl(QUrl("about:blank"))  # libera memoria del PDF
        super().reject()


def abrir(source_id, pagina=1, buscar="", frase=True):
    """Abre el PDF en `pagina`; con `buscar`, resalta ese texto en la página."""
    global _dialogo
    ruta, nombre = ruta_pdf(source_id)
    if not ruta or not os.path.exists(ruta):
        showWarning(tr("No se encuentra el PDF de esta fuente. Elimínala y vuelve a importarla."))
        return
    if modo_visor() == "sistema":
        abrir_con_sistema(ruta)
        return
    try:
        if _dialogo is None:
            _dialogo = VisorPDF(mw)
        _dialogo.mostrar(ruta, max(1, pagina), nombre, buscar, frase)
    except Exception as e:
        print(tr("Pagewise: visor integrado no disponible (%s); uso el del sistema.") % e)
        abrir_con_sistema(ruta)
