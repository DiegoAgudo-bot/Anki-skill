# -*- coding: utf-8 -*-
"""Ventana «Pagewise Pro»: estado de la licencia y activación (sin conexión)."""
from aqt import mw
from aqt.qt import (QDesktopServices, QDialog, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QUrl,
                    QVBoxLayout)
from aqt.utils import tooltip

from .. import core, licencia
from ..i18n import tr


def _fecha(d):
    return d.strftime("%d/%m/%Y")


def texto_estado():
    """Una línea con el estado actual (también la usa el gestor de fuentes)."""
    if licencia.edicion_pro():
        return tr("Pagewise Pro (edición completa): fuentes ilimitadas, sin licencia que activar.")
    lic = core.licencia_actual()
    if lic is None:
        return tr("Versión gratuita: hasta %d fuentes.") % licencia.LIMITE_FUENTES_GRATIS
    if lic.caduca:
        return tr("Pagewise Pro activo. Licencia de %s, válida hasta el %s.") % (lic.email, _fecha(lic.caduca))
    return tr("Pagewise Pro activo. Licencia de %s, sin caducidad.") % lic.email


class DialogoPro(QDialog):
    def __init__(self, parent=None, por_limite=False):
        super().__init__(parent or mw)
        self.setWindowTitle(tr("Pagewise Pro"))
        self.setMinimumWidth(520)
        capa = QVBoxLayout(self)

        if por_limite:
            aviso = QLabel(tr("<b>Has llegado al límite de la versión gratuita: %d fuentes.</b><br>"
                              "Para añadir más, activa Pagewise Pro o elimina una fuente.")
                           % licencia.LIMITE_FUENTES_GRATIS)
            aviso.setWordWrap(True)
            capa.addWidget(aviso)

        self.estado = QLabel()
        self.estado.setWordWrap(True)
        capa.addWidget(self.estado)

        incluye = QLabel(tr("Pagewise Pro incluye:<ul><li>Fuentes ilimitadas</li>"
                            "<li>PDFs escaneados con OCR <i>(en desarrollo)</i></li>"
                            "<li>Botón «Explicar»: Claude te explica el término a partir de tus fuentes "
                            "(con tu clave de la API de Anthropic)</li></ul>"))
        incluye.setWordWrap(True)
        capa.addWidget(incluye)

        if licencia.edicion_pro():
            # Edición Pro empaquetada: no hay licencia que pegar ni quitar.
            cerrar = QPushButton(tr("Cerrar"))
            cerrar.clicked.connect(self.reject)
            fila = QHBoxLayout()
            fila.addStretch()
            fila.addWidget(cerrar)
            capa.addLayout(fila)
            self.estado.setText(texto_estado())
            return

        capa.addWidget(QLabel(tr("Pega aquí tu licencia:")))
        self.campo = QPlainTextEdit()
        self.campo.setPlaceholderText("PW1.…")
        self.campo.setFixedHeight(84)
        capa.addWidget(self.campo)
        self.mensaje = QLabel()
        self.mensaje.setWordWrap(True)
        capa.addWidget(self.mensaje)

        fila = QHBoxLayout()
        self.b_activar = QPushButton(tr("Activar licencia"))
        self.b_activar.setDefault(True)
        self.b_activar.clicked.connect(self._activar)
        fila.addWidget(self.b_activar)
        if core.URL_PRO:
            conseguir = QPushButton(tr("Conseguir Pagewise Pro"))
            conseguir.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(core.URL_PRO)))
            fila.addWidget(conseguir)
        self.b_quitar = QPushButton(tr("Quitar la licencia de este ordenador"))
        self.b_quitar.clicked.connect(self._quitar)
        fila.addWidget(self.b_quitar)
        fila.addStretch()
        cerrar = QPushButton(tr("Cerrar"))
        cerrar.clicked.connect(self.reject)
        fila.addWidget(cerrar)
        capa.addLayout(fila)

        nota = QLabel(tr("La licencia se comprueba en tu ordenador: Pagewise no se conecta a ningún servidor."))
        nota.setWordWrap(True)
        capa.addWidget(nota)
        self.refrescar()

    def refrescar(self):
        self.estado.setText(texto_estado())
        self.b_quitar.setVisible(core.hay_licencia_guardada())
        if core.licencia_actual() is None and core.hay_licencia_guardada():
            # Hay una licencia guardada pero ya no vale: decimos por qué.
            self.mensaje.setText(self._motivo(core.motivo_licencia_guardada()))

    def _motivo(self, motivo):
        return {
            "formato": tr("Ese texto no parece una licencia de Pagewise. Cópiala entera, desde «PW1.» hasta el final."),
            "firma": tr("La licencia no es válida. Comprueba que la has copiado entera y sin cambios."),
            "caducada": tr("Esta licencia ha caducado. Tus fuentes siguen funcionando; renuévala para añadir más."),
        }.get(motivo, "")

    def _activar(self):
        try:
            lic = licencia.guardar(core.LICENCIA_PATH, self.campo.toPlainText())
        except licencia.LicenciaInvalida as e:
            self.mensaje.setText(self._motivo(e.motivo))
            return
        self.campo.clear()
        self.mensaje.setText("")
        self.refrescar()
        tooltip(tr("Pagewise Pro activado. Gracias, %s.") % lic.email, parent=self)

    def _quitar(self):
        licencia.quitar(core.LICENCIA_PATH)
        self.mensaje.setText(tr("Licencia quitada de este ordenador."))
        self.refrescar()


def mostrar(parent=None, por_limite=False):
    DialogoPro(parent or mw, por_limite).exec()
