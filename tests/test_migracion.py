# -*- coding: utf-8 -*-
"""Migración de los datos del nombre anterior del add-on (Fuentes -> Pagewise)."""
import os

from pagewise import migracion


def _antiguo(tmp_path):
    uf = tmp_path / "fuentes" / "user_files"
    (uf / "pdfs").mkdir(parents=True)
    (uf / "index.sqlite3").write_bytes(b"indice")
    (uf / "glosario.json").write_text('{"terminos": []}', encoding="utf-8")
    (uf / "pdfs" / "libro.pdf").write_bytes(b"%PDF")
    return str(uf)


def test_copia_indice_glosario_y_pdfs(tmp_path):
    viejo = _antiguo(tmp_path)
    nuevo = str(tmp_path / "pagewise" / "user_files")
    assert migracion.copiar_datos(viejo, nuevo) is True
    assert sorted(os.listdir(nuevo)) == ["glosario.json", "index.sqlite3", "pdfs"]
    assert os.listdir(os.path.join(nuevo, "pdfs")) == ["libro.pdf"]
    assert os.path.exists(os.path.join(viejo, "index.sqlite3"))      # no borra lo antiguo
    assert migracion.copiar_datos(viejo, nuevo) is False             # y no repite


def test_no_pisa_datos_existentes(tmp_path):
    viejo = _antiguo(tmp_path)
    nuevo = tmp_path / "pagewise" / "user_files"
    nuevo.mkdir(parents=True)
    (nuevo / "index.sqlite3").write_bytes(b"mis datos nuevos")
    assert migracion.copiar_datos(viejo, str(nuevo)) is False
    assert (nuevo / "index.sqlite3").read_bytes() == b"mis datos nuevos"


def test_sin_addon_antiguo(tmp_path):
    assert migracion.copiar_datos(str(tmp_path / "no-existe"), str(tmp_path / "nuevo")) is False
    assert not os.path.exists(str(tmp_path / "nuevo"))


def test_borra_solo_los_medios_antiguos(tmp_path):
    for n in ("_fuentes.js", "_fuentes_glosario.json", "_fuentes_t_aorta_1.json",
              "_pagewise.js", "foto.jpg", "_otra_cosa.png"):
        (tmp_path / n).write_bytes(b"x")
    assert migracion.borrar_medios_antiguos(str(tmp_path)) == 3
    assert sorted(os.listdir(str(tmp_path))) == ["_otra_cosa.png", "_pagewise.js", "foto.jpg"]
