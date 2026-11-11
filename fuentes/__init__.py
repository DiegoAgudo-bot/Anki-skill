# -*- coding: utf-8 -*-
"""Add-on «Fuentes» para Anki: subraya los términos de tus tarjetas y muestra
fragmentos de TUS propias fuentes (PDFs que importas tú), con su página.

Este archivo solo registra hooks y menús. La lógica está en:
  importer.py, index.py, exporter.py, templates.py, reviewer.py, ui/ y web/.
"""
try:
    from aqt import gui_hooks, mw
except ImportError:  # fuera de Anki (tests con pytest)
    mw = None

if mw is not None:
    from aqt.qt import QAction, QMenu

    from . import core, reviewer
    from .ui import importar

    def _accion(menu, texto, funcion):
        a = QAction(texto, mw)
        a.triggered.connect(lambda _=False: funcion())
        menu.addAction(a)
        return a

    def _crear_menu():
        menu = QMenu("Fuentes", mw)
        _accion(menu, "Añadir PDF…", importar.elegir_e_importar)
        _accion(menu, "Importar glosario…", importar.importar_glosario)
        menu.addSeparator()
        _accion(menu, "Exportar datos para el móvil ahora", core.exportar)
        mw.form.menuTools.addMenu(menu)

    # El JS y el CSS se sirven desde la carpeta del add-on en escritorio.
    mw.addonManager.setWebExports(__name__, r"web/.*\.(js|css)")
    gui_hooks.card_will_show.append(reviewer.al_mostrar_tarjeta)
    gui_hooks.webview_did_receive_js_message.append(reviewer.al_recibir_mensaje)
    gui_hooks.profile_did_open.append(core.al_abrir_perfil)
    gui_hooks.profile_will_close.append(core.al_cerrar_perfil)
    mw.addonManager.setConfigUpdatedAction(__name__, core.al_cambiar_config)
    _crear_menu()
