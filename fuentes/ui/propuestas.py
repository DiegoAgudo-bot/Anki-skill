# -*- coding: utf-8 -*-
"""Revisión de los términos propuestos a partir de los marcadores del PDF."""
from aqt.qt import (QDialog, QDialogButtonBox, QLabel, QListWidget, QListWidgetItem,
                    QPushButton, Qt, QHBoxLayout, QVBoxLayout)


class DialogoPropuestas(QDialog):
    """Lista con casillas: el usuario elige qué términos añadir al glosario."""

    def __init__(self, propuestos, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fuentes: términos propuestos")
        self.resize(420, 480)
        capa = QVBoxLayout(self)
        capa.addWidget(QLabel(
            "Estos términos salen de los marcadores (índice) del PDF.\n"
            "Marca los que quieras añadir al glosario. Podrás editarlos después."))
        self.lista = QListWidget()
        for t in propuestos:
            item = QListWidgetItem(t)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.lista.addItem(item)
        capa.addWidget(self.lista)
        fila = QHBoxLayout()
        for texto, estado in (("Marcar todos", Qt.CheckState.Checked), ("Desmarcar todos", Qt.CheckState.Unchecked)):
            b = QPushButton(texto)
            b.clicked.connect(lambda _=False, e=estado: self._marcar(e))
            fila.addWidget(b)
        fila.addStretch()
        capa.addLayout(fila)
        botones = QDialogButtonBox()
        botones.addButton("Añadir los marcados", QDialogButtonBox.ButtonRole.AcceptRole)
        botones.addButton("No añadir ninguno", QDialogButtonBox.ButtonRole.RejectRole)
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        capa.addWidget(botones)

    def _marcar(self, estado):
        for i in range(self.lista.count()):
            self.lista.item(i).setCheckState(estado)

    def elegidos(self):
        return [self.lista.item(i).text() for i in range(self.lista.count())
                if self.lista.item(i).checkState() == Qt.CheckState.Checked]
