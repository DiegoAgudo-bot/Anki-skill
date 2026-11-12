# -*- coding: utf-8 -*-
import json
import os

import pytest

from fuentes import exporter, importer

WEB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fuentes", "web")

GLOSARIO = [
    {"termino": "arteria femoral", "sinonimos": ["a. femoral"], "activo": True},
    {"termino": "nervio ciático", "sinonimos": [], "activo": True},
    {"termino": "aorta", "sinonimos": [], "activo": True},
    {"termino": "término inexistente", "sinonimos": [], "activo": True},
    {"termino": "vena safena mayor", "sinonimos": [], "activo": False},
    {"termino": "año", "sinonimos": [], "activo": True},
]


@pytest.fixture
def cargado(indice, pdfs, tmp_path):
    carpeta = str(tmp_path / "pdfs")
    a = importer.importar_pdf(indice, pdfs["apuntes"], carpeta, nombre="Apuntes").source_id
    b = importer.importar_pdf(indice, pdfs["resumen"], carpeta, nombre="Resumen").source_id
    medios = tmp_path / "collection.media"
    medios.mkdir()
    (medios / "foto.jpg").write_bytes(b"x")
    return indice, str(medios), a, b


def _leer(medios, nombre):
    with open(os.path.join(medios, nombre), encoding="utf-8") as f:
        return json.load(f)


def test_exporta_glosario_terminos_y_web(cargado):
    indice, medios, a, b = cargado
    inf = exporter.exportar(indice, GLOSARIO, medios, WEB)
    g = _leer(medios, "_fuentes_glosario.json")
    assert [t["t"] for t in g["terminos"]] == ["arteria femoral", "nervio ciático", "aorta", "año"]
    assert g["ajustes"] == {"subrayado": True, "fragmentos": 3, "soloPrimera": True, "idioma": "es"}
    assert inf.sin_resultados == ["término inexistente"]
    assert os.path.exists(os.path.join(medios, "_fuentes.js"))
    assert os.path.exists(os.path.join(medios, "_fuentes.css"))

    datos = _leer(medios, g["terminos"][0]["f"])
    assert datos["t"] == "arteria femoral"
    assert {f["nombre"] for f in datos["fuentes"]} == {"Apuntes", "Resumen"}
    for fuente in datos["fuentes"]:
        assert 1 <= len(fuente["fragmentos"]) <= 3
        for fr in fuente["fragmentos"]:
            assert "femoral" in fr["x"].lower() and fr["p"] >= 1 and len(fr["x"]) <= 362
    # "año" NO trae fragmentos de "ano" (FTS los confunde; el matcher no).
    for f in _leer(medios, g["terminos"][3]["f"])["fuentes"]:
        for fr in f["fragmentos"]:
            assert "año" in fr["x"].lower()
    # No toca otros medios del usuario.
    assert os.path.exists(os.path.join(medios, "foto.jpg"))
    assert inf.bytes == exporter.tamano_exportado(medios) > 0


def test_fragmentos_por_fuente_y_fuentes_inactivas(cargado):
    indice, medios, a, b = cargado
    exporter.exportar(indice, GLOSARIO, medios, WEB,
                      {"fragmentos_por_fuente": 1, "fuentes_inactivas": [b]})
    g = _leer(medios, "_fuentes_glosario.json")
    datos = _leer(medios, g["terminos"][0]["f"])
    assert [f["id"] for f in datos["fuentes"]] == [a]
    assert len(datos["fuentes"][0]["fragmentos"]) == 1


def test_incremental_y_limpieza(cargado):
    indice, medios, a, b = cargado
    cache = {}
    primera = exporter.exportar(indice, GLOSARIO, medios, WEB, cache=cache)
    assert primera.escritos > 0
    # Sin cambios: no se reescribe nada (no se resincroniza nada).
    segunda = exporter.exportar(indice, GLOSARIO, medios, WEB, cache=cache)
    assert segunda.escritos == 0 and segunda.borrados == 0
    # Quitamos un término: se borra su archivo.
    tercera = exporter.exportar(indice, GLOSARIO[1:], medios, WEB, cache=cache)
    assert tercera.borrados == 1
    # Renombrar una fuente cambia el índice: se recalcula.
    indice.renombrar(a, "Apuntes v2")
    cuarta = exporter.exportar(indice, GLOSARIO[1:], medios, WEB, cache=cache)
    assert cuarta.escritos > 1


def test_sin_fuentes(indice, tmp_path):
    medios = str(tmp_path)
    inf = exporter.exportar(indice, GLOSARIO, medios, WEB)
    assert inf.terminos == 0
    assert _leer(medios, "_fuentes_glosario.json")["terminos"] == []


def test_borrar_todo(cargado):
    indice, medios, a, b = cargado
    exporter.exportar(indice, GLOSARIO, medios, WEB)
    assert exporter.borrar_todo(medios) >= 4
    assert os.listdir(medios) == ["foto.jpg"]


def test_formato_tamano():
    assert exporter.formato_tamano(10) == "10 B"
    assert exporter.formato_tamano(2048) == "2.0 KB"
    assert exporter.formato_tamano(5 * 1024 * 1024) == "5.0 MB"
