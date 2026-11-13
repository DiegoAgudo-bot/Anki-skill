# -*- coding: utf-8 -*-
"""Activar Pagewise en los tipos de nota (necesario para el móvil)."""
from aqt import mw
from aqt.qt import (QDialog, QDialogButtonBox, QLabel, QListWidget, QListWidgetItem, Qt,
                    QVBoxLayout)
from aqt.utils import showInfo

from .. import core, templates
from ..i18n import tr


class DialogoTiposNota(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle(tr("Pagewise: activar en tipos de nota"))
        self.resize(460, 480)
        capa = QVBoxLayout(self)
        texto = QLabel(
            tr("Marca los tipos de nota en los que quieres el subrayado en el <b>móvil</b> "
            "(AnkiDroid, AnkiMobile, AnkiWeb). Se añade al final de sus plantillas un pequeño "
            "bloque que carga <code>_pagewise.js</code>; al desmarcar se quita sin tocar nada más.<br><br>"
            "En el escritorio no hace falta: allí el add-on lo carga solo."))
        texto.setWordWrap(True)
        capa.addWidget(texto)
        self.lista = QListWidget()
        self.inicial = {}
        for item in sorted(mw.col.models.all_names_and_ids(), key=lambda x: x.name.lower()):
            nt = mw.col.models.get(item.id)
            est = templates.estado(nt)
            w = QListWidgetItem(item.name + (tr("  (parcial)") if est == "parcial" else ""))
            w.setFlags(w.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            w.setCheckState(Qt.CheckState.Checked if est == "activo" else Qt.CheckState.Unchecked)
            w.setData(Qt.ItemDataRole.UserRole, item.id)
            self.inicial[item.id] = est
            self.lista.addItem(w)
        capa.addWidget(self.lista)
        botones = QDialogButtonBox()
        botones.addButton(tr("Aplicar"), QDialogButtonBox.ButtonRole.AcceptRole)
        botones.addButton(tr("Cancelar"), QDialogButtonBox.ButtonRole.RejectRole)
        botones.accepted.connect(self._aplicar)
        botones.rejected.connect(self.reject)
        capa.addWidget(botones)

    def _aplicar(self):
        activar, desactivar = [], []
        for i in range(self.lista.count()):
            w = self.lista.item(i)
            nid = w.data(Qt.ItemDataRole.UserRole)
            marcado = w.checkState() == Qt.CheckState.Checked
            if marcado and self.inicial[nid] != "activo":
                activar.append(nid)
            elif not marcado and self.inicial[nid]:
                desactivar.append(nid)
        n = templates.activar(mw.col, activar) + templates.desactivar(mw.col, desactivar)
        self.accept()
        if activar:
            # Asegura que los archivos _pagewise_* están en los medios.
            core.exportar(silencioso=True)
        if n:
            showInfo(tr("Plantillas actualizadas en %d tipos de nota.\n\nPara usarlo en el móvil: "
                     "sincroniza aquí y después en el móvil (los datos viajan como medios).") % n,
                     parent=mw, title="Pagewise")


def mostrar():
    DialogoTiposNota(mw).exec()
