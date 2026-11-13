# -*- coding: utf-8 -*-
import re

from pagewise import glossary


def test_limpiar_fusiona_y_quita_vacios():
    res = glossary.limpiar([
        {"termino": "  Arteria   femoral ", "sinonimos": ["a. femoral", "ARTERIA FEMORAL", ""]},
        {"termino": "arteria fémoral", "sinonimos": ["femoral artery", "A. Femoral"]},
        {"termino": "   ", "sinonimos": ["x"]},
    ])
    assert res == [{"termino": "Arteria femoral", "sinonimos": ["a. femoral", "femoral artery"], "activo": True}]


def test_guardar_y_cargar(tmp_path):
    ruta = str(tmp_path / "g.json")
    assert glossary.cargar(ruta) == []
    glossary.guardar(ruta, [{"termino": "Año", "sinonimos": [], "activo": False}])
    assert glossary.cargar(ruta) == [{"termino": "Año", "sinonimos": [], "activo": False}]


def test_anadir_no_duplica():
    ts = [{"termino": "nervio ciático", "sinonimos": ["ciático"], "activo": True}]
    assert glossary.anadir(ts, ["Nervio Ciatico", "ciatico", "Aorta", "aorta", ""]) == 1
    assert [t["termino"] for t in ts] == ["nervio ciático", "Aorta"]


def test_nombres_de_archivo_seguros():
    nombres = [glossary.nombre_archivo(t) for t in
               ["Nervio ciático", "nervio ciatico", "año", "ano", "../../etc/passwd", "C:\\x", "  ", "Ω" * 80, "a" * 300]]
    for n in nombres:
        assert re.match(r"^_pagewise_t_[a-z0-9-]+_[0-9a-f]{8}\.json$", n), n
        assert len(n) < 80
    assert nombres[0] == nombres[1]          # mismas claves -> mismo archivo
    assert nombres[2] != nombres[3]          # la ñ distingue


def test_leer_archivo_txt_y_json(tmp_path):
    txt = tmp_path / "g.txt"
    txt.write_text("# comentario\narteria femoral; a. femoral\nnervio ciático\tciático\n\n", encoding="utf-8")
    assert glossary.leer_archivo(str(txt)) == [
        {"termino": "arteria femoral", "sinonimos": ["a. femoral"], "activo": True},
        {"termino": "nervio ciático", "sinonimos": ["ciático"], "activo": True}]
    js = tmp_path / "g.json"
    js.write_text('["aorta", {"termino": "vena cava", "sinonimos": ["cava"]}]', encoding="utf-8")
    assert [t["termino"] for t in glossary.leer_archivo(str(js))] == ["aorta", "vena cava"]


def test_fusionar():
    ts = [{"termino": "aorta", "sinonimos": [], "activo": True}]
    n = glossary.fusionar(ts, [{"termino": "Aorta", "sinonimos": ["arteria aorta"], "activo": True},
                               {"termino": "vena cava", "sinonimos": [], "activo": True}])
    assert n == 1
    assert ts[0]["sinonimos"] == ["arteria aorta"]
