# -*- coding: utf-8 -*-
"""Importación de PDFs desde la interfaz: en segundo plano y con progreso."""
import os
import time

from aqt import mw
from aqt.qt import QFileDialog
from aqt.utils import showInfo, showWarning

from .. import core, glossary, importer, licencia
from ..index import Indice
from .propuestas import DialogoPropuestas
from ..i18n import tr

FASES = {"extraer": tr("leyendo texto"), "indexar": tr("indexando texto")}


def elegir_e_importar(parent=None, al_terminar=None):
    # Versión gratuita: hasta 2 fuentes. Con Pro no hay límite.
    huecos = core.huecos_para_fuentes()
    if huecos == 0:
        from . import pro
        pro.mostrar(parent, por_limite=True)
        if al_terminar:
            al_terminar()
        return
    rutas, _ = QFileDialog.getOpenFileNames(parent or mw, tr("Añadir PDFs a Pagewise"), "", tr("PDF (*.pdf)"))
    rutas = list(rutas)
    if huecos is not None and len(rutas) > huecos:
        showInfo(tr("La versión gratuita admite %d fuentes: se importarán solo los primeros %d PDF de los %d elegidos.")
                 % (licencia.LIMITE_FUENTES_GRATIS, huecos, len(rutas)), parent=parent or mw, title="Pagewise")
        rutas = rutas[:huecos]
    if rutas:
        importar(rutas, parent, al_terminar)


def _en_segundo_plano(trabajo, titulo, parent, al_terminar):
    """Ejecuta trabajo(progreso, cancelado) en segundo plano con barra de progreso.

    progreso(etiqueta, hechas, total) se puede llamar desde el hilo de fondo:
    se reenvía al hilo principal como mucho cada 0,2 s.
    """
    mw.progress.start(label=titulo, immediate=True, parent=parent or mw)
    ultimo = [0.0]

    def progreso(etiqueta, hechas, total):
        ahora = time.time()
        if ahora - ultimo[0] < 0.2 and hechas < total:
            return
        ultimo[0] = ahora
        mw.taskman.run_on_main(lambda: mw.progress.update(label=etiqueta, value=hechas, max=total))

    def tarea():
        return trabajo(progreso, mw.progress.want_cancel)

    def terminado(fut):
        mw.progress.finish()
        al_terminar(fut)

    mw.taskman.run_in_background(tarea, terminado)


def importar(rutas, parent=None, al_terminar=None):
    def trabajo(progreso, cancelado):
        ind = Indice(core.INDEX_PATH)  # conexión propia del hilo de fondo
        resultados = []
        try:
            for n, ruta in enumerate(rutas):
                nombre = os.path.basename(ruta)
                pre = tr("Importando %d de %d: %s\n") % (n + 1, len(rutas), nombre) if len(rutas) > 1 else "%s\n" % nombre

                def prog(fase, hechas, total, pre=pre):
                    progreso(tr("%s%s página %d de %d") % (pre, FASES[fase], hechas, total), hechas, total)

                try:
                    r = importer.importar_pdf(ind, ruta, core.PDFS_DIR, progreso=prog, cancelado=cancelado)
                    propuestos = importer.proponer_terminos(ruta) if r.source_id else []
                    resultados.append((ruta, r, propuestos, None))
                except importer.ImportacionCancelada:
                    resultados.append((ruta, None, [], tr("Cancelado.")))
                    break
                except Exception as e:
                    resultados.append((ruta, None, [], str(e)))
        finally:
            ind.cerrar()
        return resultados

    def terminado(fut):
        try:
            resultados = fut.result()
        except Exception as e:
            showWarning(tr("Pagewise: error al importar: %s") % e)
            return
        _resumen(resultados, parent)
        if al_terminar:
            al_terminar()

    _en_segundo_plano(trabajo, tr("Importando PDF…"), parent, terminado)


def _resumen(resultados, parent):
    lineas = []
    propuestos = []
    alguno = False
    for ruta, r, prop, error in resultados:
        nombre = os.path.basename(ruta)
        if error:
            lineas.append("✗ %s: %s" % (nombre, error))
        elif r.escaneado:
            lineas.append(
                tr("✗ %s: parece un PDF escaneado (sin texto que se pueda extraer). "
                "Necesitaría OCR, que esta versión todavía no incluye. Si tienes una versión "
                "del PDF con texto, impórtala en su lugar.") % nombre)
        else:
            alguno = True
            linea = tr("✓ %s: %d páginas, %d fragmentos.") % (nombre, r.paginas, r.fragmentos)
            if r.paginas_sin_texto:
                linea += tr(" Aviso: %d páginas sin texto (¿imágenes o escaneadas?).") % r.paginas_sin_texto
            lineas.append(linea)
            propuestos.extend(prop)
    showInfo("\n\n".join(lineas), parent=parent or mw, title="Pagewise")

    if propuestos:
        actuales = core.terminos()
        existentes = {glossary.clave(t["termino"]) for t in actuales}
        nuevos = [p for p in propuestos if glossary.clave(p) not in existentes]
        if nuevos:
            d = DialogoPropuestas(nuevos, parent or mw)
            if d.exec():
                glossary.anadir(actuales, d.elegidos())
                core.guardar_terminos(actuales)
    if alguno:
        core.exportar()


def reindexar(source_id, parent=None, al_terminar=None):
    def trabajo(progreso, cancelado):
        ind = Indice(core.INDEX_PATH)
        try:
            def prog(fase, hechas, total):
                progreso(tr("Reindexando: %s página %d de %d") % (FASES[fase], hechas, total), hechas, total)
            return importer.reindexar(ind, source_id, core.PDFS_DIR, progreso=prog, cancelado=cancelado)
        finally:
            ind.cerrar()

    def terminado(fut):
        try:
            r = fut.result()
            showInfo(tr("Reindexado: %d páginas, %d fragmentos.") % (r.paginas, r.fragmentos),
                     parent=parent or mw, title="Pagewise")
        except importer.ImportacionCancelada:
            showWarning(tr("Reindexado cancelado. La fuente queda incompleta: vuelve a reindexarla."),
                        parent=parent or mw)
        except Exception as e:
            showWarning(tr("Pagewise: error al reindexar: %s") % e, parent=parent or mw)
        core.exportar()
        if al_terminar:
            al_terminar()

    _en_segundo_plano(trabajo, tr("Reindexando…"), parent, terminado)

