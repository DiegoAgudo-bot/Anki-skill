# -*- coding: utf-8 -*-
"""Editor del glosario: términos, sinónimos y activación."""
import json

from aqt import mw
from aqt.qt import (QAbstractItemView, QDialog, QFileDialog, QHBoxLayout, QHeaderView, QLabel,
                    QLineEdit, QPushButton, Qt, QTableWidget, QTableWidgetItem, QVBoxLayout)
from aqt.utils import askUser, restoreGeom, saveGeom, showInfo, showWarning, tooltip

from .. import core, glossary
from ..textutil import clave
from ..i18n import tr

SEPARADOR = "; "


class EditorGlosario(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle(tr("Fuentes: editar glosario"))
        self.resize(720, 560)
        self.modificado = False
        capa = QVBoxLayout(self)

        ayuda = QLabel(tr("Cada término se subraya en tus tarjetas (sin distinguir mayúsculas ni tildes). "
                       "Escribe los sinónimos separados por punto y coma."))
        ayuda.setWordWrap(True)
        capa.addWidget(ayuda)

        fila = QHBoxLayout()
        fila.addWidget(QLabel(tr("Filtrar:")))
        self.filtro = QLineEdit()
        self.filtro.setPlaceholderText(tr("p. ej. arteria"))
        self.filtro.textChanged.connect(self._filtrar)
        fila.addWidget(self.filtro, 1)
        capa.addLayout(fila)

        self.tabla = QTableWidget(0, 3)
        self.tabla.setHorizontalHeaderLabels([tr("Activo"), tr("Término"), tr("Sinónimos")])
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        cab = self.tabla.horizontalHeader()
        cab.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        cab.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        cab.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabla.itemChanged.connect(lambda _i: setattr(self, "modificado", True))
        capa.addWidget(self.tabla)

        botones = QHBoxLayout()
        for texto, funcion in ((tr("Añadir término"), self._anadir), (tr("Eliminar seleccionados"), self._eliminar),
                               (tr("Importar…"), self._importar), (tr("Exportar…"), self._exportar)):
            b = QPushButton(texto)
            b.clicked.connect(lambda _=False, f=funcion: f())
            botones.addWidget(b)
        botones.addStretch()
        capa.addLayout(botones)

        pie = QHBoxLayout()
        self.contador = QLabel()
        pie.addWidget(self.contador, 1)
        cancelar = QPushButton(tr("Cancelar"))
        cancelar.clicked.connect(self.reject)
        guardar = QPushButton(tr("Guardar"))
        guardar.setDefault(True)
        guardar.clicked.connect(self._guardar)
        pie.addWidget(cancelar)
        pie.addWidget(guardar)
        capa.addLayout(pie)

        restoreGeom(self, "fuentes_glosario")
        self._cargar(core.terminos())
        self.modificado = False

    # ------------------------------------------------------------ tabla

    def _fila(self, t):
        fila = self.tabla.rowCount()
        self.tabla.insertRow(fila)
        activo = QTableWidgetItem()
        activo.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        activo.setCheckState(Qt.CheckState.Checked if t.get("activo", True) else Qt.CheckState.Unchecked)
        self.tabla.setItem(fila, 0, activo)
        self.tabla.setItem(fila, 1, QTableWidgetItem(t["termino"]))
        self.tabla.setItem(fila, 2, QTableWidgetItem(SEPARADOR.join(t["sinonimos"])))
        return fila

    def _cargar(self, terminos):
        self.tabla.blockSignals(True)
        self.tabla.setRowCount(0)
        for t in terminos:
            self._fila(t)
        self.tabla.blockSignals(False)
        self._filtrar()

    def _leer(self):
        salida = []
        for fila in range(self.tabla.rowCount()):
            termino = (self.tabla.item(fila, 1).text() if self.tabla.item(fila, 1) else "").strip()
            sinonimos = self.tabla.item(fila, 2).text() if self.tabla.item(fila, 2) else ""
            salida.append({
                "termino": termino,
                "sinonimos": [s.strip() for s in sinonimos.split(";") if s.strip()],
                "activo": self.tabla.item(fila, 0).checkState() == Qt.CheckState.Checked,
            })
        return salida

    def _filtrar(self):
        k = clave(self.filtro.text())
        visibles = 0
        for fila in range(self.tabla.rowCount()):
            texto = " ".join(self.tabla.item(fila, c).text() for c in (1, 2) if self.tabla.item(fila, c))
            oculta = bool(k) and k not in clave(texto)
            self.tabla.setRowHidden(fila, oculta)
            visibles += not oculta
        self.contador.setText(tr("%d términos") % self.tabla.rowCount() +
                              (tr(" (%d visibles)") % visibles if k else ""))

    # ------------------------------------------------------------ acciones

    def _anadir(self):
        self.filtro.clear()
        fila = self._fila({"termino": "", "sinonimos": [], "activo": True})
        self.tabla.scrollToItem(self.tabla.item(fila, 1))
        self.tabla.setCurrentCell(fila, 1)
        self.tabla.editItem(self.tabla.item(fila, 1))
        self._filtrar()

    def _eliminar(self):
        filas = sorted({i.row() for i in self.tabla.selectedIndexes()}, reverse=True)
        if not filas:
            tooltip(tr("Selecciona primero los términos."), parent=self)
            return
        for fila in filas:
            self.tabla.removeRow(fila)
        self.modificado = True
        self._filtrar()

    def _importar(self):
        ruta, _ = QFileDialog.getOpenFileName(self, tr("Importar glosario"), "", tr("Glosario (*.json *.txt *.csv *.tsv)"))
        if not ruta:
            return
        try:
            nuevos = glossary.leer_archivo(ruta)
        except Exception as e:
            showWarning(tr("No se pudo leer el archivo: %s") % e, parent=self)
            return
        actuales = self._leer()
        n = glossary.fusionar(actuales, nuevos)
        self._cargar(actuales)
        self.modificado = True
        tooltip(tr("%d términos nuevos.") % n, parent=self)

    def _exportar(self):
        ruta, _ = QFileDialog.getSaveFileName(self, tr("Exportar glosario"), "glosario.json", tr("JSON (*.json)"))
        if ruta:
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump({"version": 1, "terminos": glossary.limpiar(self._leer())}, f,
                          ensure_ascii=False, indent=1)
            tooltip(tr("Glosario exportado."), parent=self)

    def _guardar(self):
        terminos = core.guardar_terminos(self._leer())
        saveGeom(self, "fuentes_glosario")
        self.accept()

        def informe(inf):
            if inf is None:
                return
            msg = tr("Glosario guardado: %d términos con fragmentos en tus fuentes.") % inf.terminos
            if inf.sin_resultados:
                muestra = ", ".join(inf.sin_resultados[:15]) + ("…" if len(inf.sin_resultados) > 15 else "")
                msg += (tr("\n\n%d términos no aparecen en ninguna fuente activa y no se subrayarán:\n%s")
                        % (len(inf.sin_resultados), muestra))
            showInfo(msg, parent=mw, title="Fuentes")

        if terminos is not None:
            core.exportar(silencioso=True, al_terminar=informe)

    def reject(self):
        if self.modificado and not askUser(tr("¿Salir sin guardar los cambios del glosario?"), parent=self):
            return
        saveGeom(self, "fuentes_glosario")
        super().reject()


def mostrar():
    EditorGlosario(mw).exec()
