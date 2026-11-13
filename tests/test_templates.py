# -*- coding: utf-8 -*-
import pytest

from pagewise import templates

PLANTILLAS = [
    "",
    "{{Front}}",
    "{{FrontSide}}\n\n<hr id=answer>\n\n{{Back}}\n",
    "<div class=x>{{cloze:Text}}</div>\n<script>var a = 1;</script>\n\n\n",
    "{{#Extra}}<br>{{Extra}}{{/Extra}}<!-- comentario del usuario -->",
]


@pytest.mark.parametrize("p", PLANTILLAS)
def test_ida_y_vuelta_exacta(p):
    con = templates.insertar(p)
    assert templates.tiene(con)
    assert con.startswith(p)                    # no toca lo que había
    assert '<script src="_pagewise.js"></script>' in con
    assert templates.quitar(con) == p           # se quita sin dejar rastro


def test_insertar_dos_veces_no_duplica():
    p = templates.insertar(templates.insertar("{{Front}}"))
    assert p.count("PAGEWISE:INICIO") == 1
    assert templates.quitar(p) == "{{Front}}"


def test_quitar_respeta_lo_que_el_usuario_puso_despues():
    p = templates.insertar("{{Front}}") + "\n<b>mío</b>"
    assert templates.quitar(p) == "{{Front}}\n<b>mío</b>"


class ColeccionFalsa:
    """Imita col.models lo justo para probar activar/desactivar."""
    def __init__(self, tipos):
        self.tipos = tipos
        self.actualizados = []
        self.models = self

    def get(self, nid):
        return self.tipos.get(nid)

    def update_dict(self, nt):
        self.actualizados.append(nt["id"])


def test_activar_y_desactivar():
    col = ColeccionFalsa({
        1: {"id": 1, "tmpls": [{"qfmt": "{{Front}}", "afmt": "{{FrontSide}}<hr id=answer>{{Back}}"}]},
        2: {"id": 2, "tmpls": [{"qfmt": "{{cloze:Text}}", "afmt": "{{cloze:Text}}"}]},
    })
    assert templates.activar(col, [1]) == 1
    assert templates.estado(col.tipos[1]) == "activo" and templates.estado(col.tipos[2]) == ""
    assert templates.activar(col, [1]) == 0            # ya estaba igual: no se reescribe
    col.tipos[2]["tmpls"][0]["qfmt"] = templates.insertar("{{cloze:Text}}")
    assert templates.estado(col.tipos[2]) == "parcial"
    assert templates.desactivar(col, [1, 2]) == 2
    assert col.tipos[1]["tmpls"][0] == {"qfmt": "{{Front}}", "afmt": "{{FrontSide}}<hr id=answer>{{Back}}"}
    assert col.actualizados == [1, 1, 2]


BLOQUE_ANTIGUO = ('\n<!-- FUENTES:INICIO (lo gestiona el add-on Fuentes; no edites entre estas marcas) -->\n'
                  '<link rel="stylesheet" href="_fuentes.css">\n<script src="_fuentes.js"></script>\n<!-- FUENTES:FIN -->')


def test_bloque_del_nombre_anterior():
    vieja = "{{Front}}" + BLOQUE_ANTIGUO
    assert templates.tiene_antiguo(vieja) and not templates.tiene(vieja)
    assert templates.quitar(vieja) == "{{Front}}"
    nueva = templates.insertar(vieja)                 # se sustituye, no se duplica
    assert "_fuentes" not in nueva and nueva.count("_pagewise.js") == 1
    assert templates.quitar(nueva) == "{{Front}}"


def test_renovar_solo_las_que_ya_lo_llevaban():
    col = ColeccionFalsa({
        1: {"id": 1, "tmpls": [{"qfmt": "{{Front}}" + BLOQUE_ANTIGUO, "afmt": "{{Back}}"}]},
        2: {"id": 2, "tmpls": [{"qfmt": "{{Front}}", "afmt": "{{Back}}"}]},
    })
    assert templates.estado(col.tipos[1]) == "parcial"
    assert templates.activar(col, [1, 2], solo_con_bloque=True) == 1
    assert "_pagewise.js" in col.tipos[1]["tmpls"][0]["qfmt"]
    assert col.tipos[1]["tmpls"][0]["afmt"] == "{{Back}}"       # la que no lo tenía sigue igual
    assert col.tipos[2]["tmpls"][0] == {"qfmt": "{{Front}}", "afmt": "{{Back}}"}
