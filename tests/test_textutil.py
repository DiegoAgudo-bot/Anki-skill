# -*- coding: utf-8 -*-
"""Matching en Python con los MISMOS casos que el JS (tests/casos_matching.json)."""
import json
import os

import pytest

from pagewise.textutil import Matcher, clave, normalizar, recortar

with open(os.path.join(os.path.dirname(__file__), "casos_matching.json"), encoding="utf-8") as f:
    DATOS = json.load(f)


def _matcher():
    variantes = []
    for i, t in enumerate(DATOS["glosario"]):
        for v in [t["term"]] + t["synonyms"]:
            variantes.append((v, i))
    return Matcher(variantes)


@pytest.mark.parametrize("caso", DATOS["casos"], ids=[c["nombre"] for c in DATOS["casos"]])
def test_casos_compartidos(caso):
    texto = caso["texto"]
    obtenido = [
        {"termino": DATOS["glosario"][i]["term"], "texto": texto[a:b]}
        for a, b, i in _matcher().buscar(texto)
    ]
    assert obtenido == caso["esperado"]


def test_normalizar_conserva_mapa():
    norm, mapa = normalizar("Á  b")
    assert norm == "a b"
    assert mapa == [0, 1, 3]


def test_clave():
    assert clave("  Nervio  CIÁTICO ") == "nervio ciatico"
    assert clave("Año") == "año"


def test_recortar_centra_en_el_termino():
    texto = ("palabra " * 100) + "AORTA " + ("otra " * 100)
    i = texto.index("AORTA")
    r = recortar(texto, i, i + 5, largo=100)
    assert "AORTA" in r and r.startswith("…") and r.endswith("…")
    assert len(r) <= 102
    assert recortar("corto", 0, 5) == "corto"
