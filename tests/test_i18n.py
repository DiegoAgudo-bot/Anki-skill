# -*- coding: utf-8 -*-
"""Todos los textos envueltos en tr("…") deben tener traducción al inglés."""
import ast
import glob
import os
import re

from fuentes import i18n
from fuentes.i18n_en import EN

ADDON = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fuentes")


def _textos():
    for ruta in glob.glob(os.path.join(ADDON, "*.py")) + glob.glob(os.path.join(ADDON, "ui", "*.py")):
        with open(ruta, encoding="utf-8") as f:
            arbol = ast.parse(f.read())
        for n in ast.walk(arbol):
            if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "tr":
                assert len(n.args) == 1 and isinstance(n.args[0], ast.Constant), \
                    "tr() debe recibir un texto literal (%s:%d)" % (ruta, n.lineno)
                yield os.path.basename(ruta), n.args[0].value


def test_todo_tiene_traduccion():
    faltan = sorted({t for _, t in _textos() if t not in EN})
    assert not faltan, "Faltan en i18n_en.py: %r" % faltan


def test_no_sobran_traducciones():
    usados = {t for _, t in _textos()}
    assert sorted(set(EN) - usados) == []


def test_mismos_marcadores_de_formato():
    for es, en in EN.items():
        assert re.findall(r"%[sd]", es) == re.findall(r"%[sd]", en), es


def test_tr_segun_idioma():
    try:
        i18n.fijar_idioma("es_ES")
        assert i18n.tr("Guardar") == "Guardar"
        i18n.fijar_idioma("de")
        assert i18n.tr("Guardar") == "Save" and i18n.idioma() == "en"
        assert i18n.tr("texto sin traducir") == "texto sin traducir"
    finally:
        i18n.fijar_idioma("es")
