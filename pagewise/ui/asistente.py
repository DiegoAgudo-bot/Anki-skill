# -*- coding: utf-8 -*-
"""Asistente de primeros pasos: guía al usuario por los tres pasos básicos
(importar un PDF, crear el glosario y activar el móvil) y muestra cuáles
están ya hechos. Se abre solo la primera vez y desde el menú."""
from aqt import mw
from aqt.qt import (QDialog, QFrame, QGridLayout, QLabel, QPushButton, QVBoxLayout)

from .. import core, templates
from ..i18n import tr
from . import editor_glosario, importar, tipos_nota

_abierto = None


def estado():
    """Qué pasos están hechos: (hay_fuentes, hay_glosario, movil_activo)."""
    hay_fuentes = any(f["estado"] == "lista" for f in core.indice().fuentes())
    hay_glosario = any(t["activo"] for t in core.terminos())
    movil = False
    if mw.col:
        for item in mw.col.models.all_names_and_ids():
            if templates.estado(mw.col.models.get(item.id)):
                movil = True
                break
    return hay_fuentes, hay_glosario, movil


class Asistente(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle(tr("Pagewise: primeros pasos"))
        self.setMinimumWidth(560)
        capa = QVBoxLayout(self)
        intro = QLabel(tr(
            "<b>Pagewise</b> subraya los términos de tus tarjetas y te muestra qué dicen sobre ellos "
            "<b>tus propios PDFs</b>, con su página. Todo se procesa en este ordenador.<br><br>"
            "Importa solo material que tengas derecho a usar."))
        intro.setWordWrap(True)
        capa.addWidget(intro)
        linea = QFrame()
        linea.setFrameShape(QFrame.Shape.HLine)
        capa.addWidget(linea)

        rejilla = QGridLayout()
        rejilla.setColumnStretch(1, 1)
        rejilla.setVerticalSpacing(14)
        pasos = [
            (tr("<b>1. Añade un PDF</b><br>Un libro o tus apuntes, con texto (no escaneado)."),
             tr("Añadir PDF…"), self._paso_pdf),
            (tr("<b>2. Crea tu glosario</b><br>Los términos que quieres ver subrayados, con sus sinónimos."),
             tr("Editar glosario…"), self._paso_glosario),
            (tr("<b>3. Actívalo en el móvil</b> (opcional)<br>Elige los tipos de nota y sincroniza."),
             tr("Activar en tipos de nota…"), self._paso_movil),
        ]
        self.marcas = []
        for fila, (texto, boton, funcion) in enumerate(pasos):
            marca = QLabel()
            marca.setMinimumWidth(24)
            self.marcas.append(marca)
            rejilla.addWidget(marca, fila, 0)
            etiqueta = QLabel(texto)
            etiqueta.setWordWrap(True)
            rejilla.addWidget(etiqueta, fila, 1)
            b = QPushButton(boton)
            b.clicked.connect(lambda _=False, f=funcion: f())
            rejilla.addWidget(b, fila, 2)
        capa.addLayout(rejilla)

        self.resumen = QLabel()
        self.resumen.setWordWrap(True)
        capa.addWidget(self.resumen)
        cerrar = QPushButton(tr("Cerrar"))
        cerrar.clicked.connect(self.close)
        capa.addWidget(cerrar)
        self.refrescar()

    def refrescar(self):
        hechos = estado()
        for marca, hecho in zip(self.marcas, hechos):
            marca.setText("✅" if hecho else "⬜")
        if hechos[0] and hechos[1]:
            self.resumen.setText(tr(
                "¡Listo! Repasa una tarjeta que contenga alguno de tus términos y pasa el ratón por encima. "
                "Encontrarás todo en Herramientas → Pagewise."))
        elif hechos[0]:
            self.resumen.setText(tr("Ya tienes fuentes. Ahora añade los términos que quieres subrayar."))
        else:
            self.resumen.setText(tr("Empieza por el paso 1."))

    def _paso_pdf(self):
        importar.elegir_e_importar(self, al_terminar=self.refrescar)

    def _paso_glosario(self):
        editor_glosario.EditorGlosario(self).exec()
        self.refrescar()

    def _paso_movil(self):
        tipos_nota.DialogoTiposNota(self).exec()
        self.refrescar()


def mostrar():
    """Abre el asistente sin bloquear Anki (ventana no modal)."""
    global _abierto
    if _abierto is not None:
        _abierto.close()
    _abierto = Asistente(mw)
    _abierto.show()
    _abierto.raise_()
    return _abierto


def mostrar_si_es_la_primera_vez():
    c = core.config()
    if c.get("asistente_visto"):
        return
    c["asistente_visto"] = True
    core.guardar_config(c)
    if not core.indice().fuentes():  # quien ya usa el add-on no lo necesita
        mostrar()
