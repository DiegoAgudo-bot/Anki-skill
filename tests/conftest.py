# -*- coding: utf-8 -*-
"""Configuración de pytest: los tests corren FUERA de Anki."""
import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "dev"))
# Probamos con el pypdf que va dentro del add-on, no con el del sistema.
sys.path.insert(0, os.path.join(RAIZ, "fuentes", "vendor"))

import generar_pdfs  # noqa: E402


@pytest.fixture(scope="session")
def pdfs(tmp_path_factory):
    d = tmp_path_factory.mktemp("pdfs")
    return {
        "apuntes": generar_pdfs.generar_apuntes(str(d / "apuntes.pdf")),
        "resumen": generar_pdfs.generar_otra_fuente(str(d / "resumen.pdf")),
        "escaneado": generar_pdfs.generar_escaneado(str(d / "escaneado.pdf")),
    }


@pytest.fixture
def indice(tmp_path):
    from fuentes.index import Indice

    ind = Indice(str(tmp_path / "index.sqlite3"))
    yield ind
    ind.cerrar()


def pytest_addoption(parser):
    parser.addoption("--lentos", action="store_true", help="incluye tests lentos (PDF de 1200 páginas)")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--lentos"):
        return
    saltar = pytest.mark.skip(reason="test lento: usa --lentos")
    for item in items:
        if "lento" in item.keywords:
            item.add_marker(saltar)
