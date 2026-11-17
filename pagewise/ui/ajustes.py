# -*- coding: utf-8 -*-
"""Ventana «Ajustes»: con qué se abre el PDF, y la IA y su clave para «Explicar»."""
from aqt import mw
from aqt.qt import (QButtonGroup, QDesktopServices, QDialog, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                    QPushButton, QRadioButton, QUrl, QVBoxLayout)
from aqt.utils import tooltip

from .. import core, explicar
from ..i18n import idioma, tr

URL_CLAVES = {
    "anthropic": "https://console.anthropic.com/settings/keys",
    "openai": "https://platform.openai.com/api-keys",
}


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
            "«Explicar» pide a una IA que te explique el término a partir de los fragmentos de tus "
            "fuentes, citando la página. Elige Claude (Anthropic) o ChatGPT (OpenAI) y pon tu propia "
            "clave de su API: cada explicación cuesta unos céntimos en tu cuenta.<br><br>"
            "<b>Privacidad:</b> es lo único de Pagewise que se conecta a internet, y solo cuando pulsas "
            "«Explicar». Se envían a la empresa que elijas el término, el texto de la tarjeta y los "
            "fragmentos de tus fuentes sobre ese término. Nunca se envían los PDFs completos."))
        texto.setWordWrap(True)
        g.addWidget(texto)
        fila = QHBoxLayout()
        fila.addWidget(QLabel(tr("Usar:")))
        self.r_claude = QRadioButton(tr("Claude (Anthropic)"))
        self.r_openai = QRadioButton(tr("ChatGPT (OpenAI)"))
        self.grupo_ia = QButtonGroup(self)
        for r in (self.r_claude, self.r_openai):
            self.grupo_ia.addButton(r)
            fila.addWidget(r)
        fila.addStretch()
        g.addLayout(fila)
        (self.r_openai if core.proveedor_explicar() == "openai" else self.r_claude).setChecked(True)

        self.claves = {}
        for proveedor, etiqueta, ejemplo in (("anthropic", tr("Clave de la API de Anthropic:"), "sk-ant-…"),
                                             ("openai", tr("Clave de la API de OpenAI:"), "sk-…")):
            fila = QHBoxLayout()
            fila.addWidget(QLabel(etiqueta))
            campo = QLineEdit()
            campo.setEchoMode(QLineEdit.EchoMode.Password)
            campo.setPlaceholderText(ejemplo)
            campo.setText(core.clave_api_guardada(proveedor))
            fila.addWidget(campo, 1)
            ver = QPushButton(tr("Mostrar"))
            ver.setCheckable(True)
            ver.toggled.connect(lambda si, c=campo: c.setEchoMode(
                QLineEdit.EchoMode.Normal if si else QLineEdit.EchoMode.Password))
            fila.addWidget(ver)
            g.addLayout(fila)
            self.claves[proveedor] = campo
        self.clave = self.claves["anthropic"]  # compatibilidad con pruebas antiguas
        fila = QHBoxLayout()
        self.b_comprobar = QPushButton(tr("Comprobar la clave"))
        self.b_comprobar.clicked.connect(self._comprobar)
        fila.addWidget(self.b_comprobar)
        conseguir = QPushButton(tr("Conseguir una clave"))
        conseguir.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(URL_CLAVES[self._proveedor()])))
        fila.addWidget(conseguir)
        fila.addStretch()
        g.addLayout(fila)
        self.estado_clave = QLabel()
        self.estado_clave.setWordWrap(True)
        g.addWidget(self.estado_clave)
        self.grupo_ia.buttonToggled.connect(lambda *_: self.estado_clave.setText(""))
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
            self.estado_clave.setText(tr("Para usar «Explicar», pega aquí la clave de la API que hayas elegido."))
            self.claves[self._proveedor()].setFocus()

    def _proveedor(self):
        return "openai" if self.r_openai.isChecked() else "anthropic"

    def _comprobar(self):
        proveedor = self._proveedor()
        clave = "".join(self.claves[proveedor].text().split())
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

        mw.taskman.run_in_background(lambda: explicar.comprobar_clave(clave, lengua, proveedor=proveedor),
                                     terminado)

    def _guardar(self):
        c = core.config()
        if self.r_sistema.isChecked():
            c["visor_pdf"] = "sistema"
        elif self.visor_actual == "sistema":
            c["visor_pdf"] = "pdfjs"
        # (si estaba en "chromium", elegido a mano en la configuración, se respeta)
        c["explicar_proveedor"] = self._proveedor()
        core.guardar_config(c)
        for proveedor, campo in self.claves.items():
            core.guardar_clave_api(campo.text(), proveedor)
        tooltip(tr("Ajustes guardados."), parent=mw)
        self.accept()


def mostrar(parent=None, foco=None):
    DialogoAjustes(parent or mw, foco).exec()
