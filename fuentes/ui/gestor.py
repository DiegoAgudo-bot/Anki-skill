# -*- coding: utf-8 -*-
"""Gestor de fuentes: añadir, renombrar, activar, reindexar y eliminar PDFs."""
import os

from aqt import mw
from aqt.qt import (QAbstractItemView, QDialog, QHBoxLayout, QHeaderView, QInputDialog, QLabel,
                    QPushButton, Qt, QTableWidget, QTableWidgetItem, QVBoxLayout)
from aqt.utils import askUser, restoreGeom, saveGeom, tooltip

from .. import core, exporter
from . import importar, visor
from ..i18n import tr

COLUMNAS = [tr("Activa"), tr("Nombre"), tr("Páginas"), tr("Fragmentos"), tr("Importada"), tr("Estado")]


class GestorFuentes(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle(tr("Fuentes: gestionar fuentes"))
        self.resize(760, 420)
        capa = QVBoxLayout(self)

        aviso = QLabel(
            tr("Importa solo material que tengas derecho a usar. Todo se procesa y se guarda en "
            "este ordenador; al móvil solo llega a través de tu propia sincronización con AnkiWeb."))
        aviso.setWordWrap(True)
        capa.addWidget(aviso)

        self.tabla = QTableWidget(0, len(COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(COLUMNAS)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.itemChanged.connect(self._activa_cambiada)
        self.tabla.itemDoubleClicked.connect(lambda _i: self._abrir())
        capa.addWidget(self.tabla)

        botones = QHBoxLayout()
        for texto, funcion in ((tr("Añadir PDF…"), self._anadir), (tr("Renombrar…"), self._renombrar),
                               (tr("Abrir PDF"), self._abrir), (tr("Reindexar"), self._reindexar),
                               (tr("Eliminar…"), self._eliminar)):
            b = QPushButton(texto)
            b.clicked.connect(lambda _=False, f=funcion: f())
            botones.addWidget(b)
        botones.addStretch()
        capa.addLayout(botones)

        pie = QHBoxLayout()
        self.estado = QLabel()
        self.estado.setWordWrap(True)
        pie.addWidget(self.estado, 1)
        exportar = QPushButton(tr("Exportar para el móvil"))
        exportar.clicked.connect(lambda: core.exportar(al_terminar=lambda _i: self.refrescar()))
        pie.addWidget(exportar)
        cerrar = QPushButton(tr("Cerrar"))
        cerrar.clicked.connect(self.reject)
        pie.addWidget(cerrar)
        capa.addLayout(pie)

        restoreGeom(self, "fuentes_gestor")
        self.refrescar()

    # ------------------------------------------------------------ datos

    def refrescar(self):
        inactivas = set(core.config()["fuentes_inactivas"])
        fuentes = core.indice().fuentes()
        self.tabla.blockSignals(True)
        self.tabla.setRowCount(len(fuentes))
        for fila, f in enumerate(fuentes):
            activa = QTableWidgetItem()
            activa.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            activa.setCheckState(Qt.CheckState.Unchecked if f["id"] in inactivas else Qt.CheckState.Checked)
            activa.setData(Qt.ItemDataRole.UserRole, f["id"])
            self.tabla.setItem(fila, 0, activa)
            estado = tr("Lista") if f["estado"] == "lista" else tr("Incompleta: reindexa")
            for col, valor in enumerate([f["nombre"], f["paginas"], f["fragmentos"], f["fecha"], estado], 1):
                self.tabla.setItem(fila, col, QTableWidgetItem(str(valor)))
        self.tabla.resizeColumnsToContents()
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.blockSignals(False)

        c = core.config()
        n_terminos = len([t for t in core.terminos() if t["activo"]])
        tam = core.tamano_exportado()
        texto = tr("%d fuentes · %d términos en el glosario · Datos para el móvil: %s") % (
            len(fuentes), n_terminos, exporter.formato_tamano(tam))
        if tam > c["aviso_tamano_mb"] * 1024 * 1024:
            texto += tr("  ⚠ más de %d MB: la sincronización con el móvil será lenta") % c["aviso_tamano_mb"]
        if not fuentes:
            texto = tr("Aún no hay fuentes. Pulsa «Añadir PDF…» para importar la primera.")
        self.estado.setText(texto)

    def _seleccionada(self):
        filas = self.tabla.selectionModel().selectedRows()
        if not filas:
            tooltip(tr("Selecciona primero una fuente."), parent=self)
            return None
        item = self.tabla.item(filas[0].row(), 0)
        return core.indice().fuente(item.data(Qt.ItemDataRole.UserRole))

    # ------------------------------------------------------------ acciones

    def _activa_cambiada(self, item):
        if item.column() != 0:
            return
        c = core.config()
        sid = item.data(Qt.ItemDataRole.UserRole)
        inactivas = [x for x in c["fuentes_inactivas"] if x != sid]
        if item.checkState() != Qt.CheckState.Checked:
            inactivas.append(sid)
        c["fuentes_inactivas"] = sorted(inactivas)
        core.guardar_config(c)
        core.exportar(silencioso=True, al_terminar=lambda _i: self.refrescar())

    def _anadir(self):
        importar.elegir_e_importar(self, al_terminar=self.refrescar)

    def _renombrar(self):
        f = self._seleccionada()
        if not f:
            return
        nombre, ok = QInputDialog.getText(self, tr("Renombrar fuente"), tr("Nombre que verás en el popup:"), text=f["nombre"])
        nombre = " ".join(nombre.split())
        if ok and nombre and nombre != f["nombre"]:
            core.indice().renombrar(f["id"], nombre)
            self.refrescar()
            core.exportar(silencioso=True, al_terminar=lambda _i: self.refrescar())

    def _abrir(self):
        f = self._seleccionada()
        if f:
            visor.abrir(f["id"], 1)

    def _reindexar(self):
        f = self._seleccionada()
        if f:
            importar.reindexar(f["id"], self, al_terminar=self.refrescar)

    def _eliminar(self):
        f = self._seleccionada()
        if not f:
            return
        if not askUser(tr("¿Eliminar la fuente «%s»?\n\nSe borrarán su índice y la copia del PDF guardada "
                       "por el add-on (tu archivo original no se toca).") % f["nombre"], parent=self,
                       defaultno=True, title=tr("Eliminar fuente")):
            return
        core.indice().eliminar_fuente(f["id"])
        try:
            os.remove(os.path.join(core.PDFS_DIR, f["archivo"]))
        except OSError:
            pass
        c = core.config()
        c["fuentes_inactivas"] = [x for x in c["fuentes_inactivas"] if x != f["id"]]
        core.guardar_config(c)
        self.refrescar()
        core.exportar(silencioso=True, al_terminar=lambda _i: self.refrescar())
        tooltip(tr("Fuente eliminada."), parent=self)

    def reject(self):
        saveGeom(self, "fuentes_gestor")
        super().reject()


def mostrar():
    GestorFuentes(mw).exec()
