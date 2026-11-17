# -*- coding: utf-8 -*-
"""Ventana «Ajustes»: con qué se abre el PDF y la clave para «Explicar»."""
from aqt import mw
from aqt.qt import (QButtonGroup, QDesktopServices, QDialog, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                    QPushButton, QRadioButton, QUrl, QVBoxLayout)
from aqt.utils import tooltip

from .. import core, explicar
from ..i18n import idioma, tr

URL_CLAVES = "https://console.anthropic.com/settings/keys"


class DialogoAjustes(QDialog):
    def __init__(self, parent=None, foco=None):
        super().__init__(parent or mw)
        self.setWindowTitle(tr("Pagewise: ajustes"))
        self.setMinimumWidth(560)
        capa = QVBoxLayout(self)

        # --- Visor de PDF
        grupo = QGroupBox(tr("Al hacer clic en un fragmento, abrir el PDF con"))
        g = QVBoxLayout(grupo)
        self.r_pagewise = QRadioButton(tr("El visor de Pagewise: abre la página y resalta el término"))
        self.r_sistema = QRadioButton(tr("El visor de PDF del ordenador: abre el archivo y tú vas a la página"))
        self.grupo_visor = QButtonGroup(self)
        for r in (self.r_pagewise, self.r_sistema):
            self.grupo_visor.addButton(r)
            g.addWidget(r)
        nota = QLabel(tr("Con el visor del ordenador no se puede saltar a la página ni resaltar: "
                         "Pagewise te dice en qué página está."))
        nota.setWordWrap(True)
        nota.setStyleSheet("color: gray")
        g.addWidget(nota)
        capa.addWidget(grupo)
        self.visor_actual = core.config().get("visor_pdf") or "pdfjs"
        (self.r_sistema if self.visor_actual == "sistema" else self.r_pagewise).setChecked(True)

        # --- Explicar
        grupo = QGroupBox(tr("Botón «Explicar» (Pagewise Pro)"))
        g = QVBoxLayout(grupo)
        texto = QLabel(tr(
            "«Explicar» pide a Claude, la IA de Anthropic, que te explique el término a partir de los "
            "fragmentos de tus fuentes, citando la página. Usa tu propia clave de la API de Anthropic "
            "(cada explicación cuesta unos céntimos en tu cuenta de Anthropic).<br><br>"
            "<b>Privacidad:</b> es lo único de Pagewise que se conecta a internet, y solo cuando pulsas "
            "«Explicar». Se envían a Anthropic el término, el texto de la tarjeta y los fragmentos de tus "
            "fuentes sobre ese término. Nunca se envían los PDFs completos."))
        texto.setWordWrap(True)
        g.addWidget(texto)
        fila = QHBoxLayout()
        fila.addWidget(QLabel(tr("Clave de la API de Anthropic:")))
        self.clave = QLineEdit()
        self.clave.setEchoMode(QLineEdit.EchoMode.Password)
        self.clave.setPlaceholderText("sk-ant-…")
        self.clave.setText(core.clave_api_guardada())
        fila.addWidget(self.clave, 1)
        ver = QPushButton(tr("Mostrar"))
        ver.setCheckable(True)
        ver.toggled.connect(lambda si: self.clave.setEchoMode(
            QLineEdit.EchoMode.Normal if si else QLineEdit.EchoMode.Password))
        fila.addWidget(ver)
        g.addLayout(fila)
        fila = QHBoxLayout()
        self.b_comprobar = QPushButton(tr("Comprobar la clave"))
        self.b_comprobar.clicked.connect(self._comprobar)
        fila.addWidget(self.b_comprobar)
        conseguir = QPushButton(tr("Conseguir una clave"))
        conseguir.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(URL_CLAVES)))
        fila.addWidget(conseguir)
        fila.addStretch()
        g.addLayout(fila)
        self.estado_clave = QLabel()
        self.estado_clave.setWordWrap(True)
        g.addWidget(self.estado_clave)
        if not core.es_pro():
            aviso = QLabel(tr("Necesitas Pagewise Pro para usar «Explicar». Puedes guardar la clave igualmente."))
            aviso.setWordWrap(True)
            g.addWidget(aviso)
        capa.addWidget(grupo)

        # --- Botones
        fila = QHBoxLayout()
        fila.addStretch()
        cancelar = QPushButton(tr("Cancelar"))
        cancelar.clicked.connect(self.reject)
        fila.addWidget(cancelar)
        guardar = QPushButton(tr("Guardar"))
        guardar.setDefault(True)
        guardar.clicked.connect(self._guardar)
        fila.addWidget(guardar)
        capa.addLayout(fila)

        if foco == "clave":
            self.estado_clave.setText(tr("Para usar «Explicar», pega aquí tu clave de la API de Anthropic."))
            self.clave.setFocus()

    def _comprobar(self):
        clave = "".join(self.clave.text().split())
        if not clave:
            self.estado_clave.setText(tr("Escribe primero la clave."))
            return
        self.b_comprobar.setEnabled(False)
        self.estado_clave.setText(tr("Comprobando…"))
        lengua = idioma()

        def terminado(fut):
            self.b_comprobar.setEnabled(True)
            try:
                fut.result()
                self.estado_clave.setText(tr("✓ La clave funciona."))
            except explicar.ErrorExplicar as e:
                self.estado_clave.setText("✗ " + str(e))
            except Exception as e:
                self.estado_clave.setText("✗ " + str(e))

        mw.taskman.run_in_background(lambda: explicar.comprobar_clave(clave, lengua), terminado)

    def _guardar(self):
        c = core.config()
        if self.r_sistema.isChecked():
            c["visor_pdf"] = "sistema"
        elif self.visor_actual == "sistema":
            c["visor_pdf"] = "pdfjs"
        # (si estaba en "chromium", elegido a mano en la configuración, se respeta)
        core.guardar_config(c)
        core.guardar_clave_api(self.clave.text())
        tooltip(tr("Ajustes guardados."), parent=mw)
        self.accept()


def mostrar(parent=None, foco=None):
    DialogoAjustes(parent or mw, foco).exec()
