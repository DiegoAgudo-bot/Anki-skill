# -*- coding: utf-8 -*-
import pytest

from fuentes.index import Indice, consulta_fts


def _cargar(indice):
    a = indice.agregar_fuente("Libro A", "a.pdf", "/x/a.pdf", 2, "sha-a")
    indice.agregar_fragmentos(a, [
        (1, None, "La arteria femoral pasa bajo el ligamento inguinal."),
        (2, "xii", "El nervio ciático es muy grueso. La ARTERIA FEMORAL también se cita."),
    ])
    indice.marcar_lista(a)
    b = indice.agregar_fuente("Libro B", "b.pdf", "/x/b.pdf", 1, "sha-b")
    indice.agregar_fragmentos(b, [(1, None, "Resumen: arteria femoral profunda y aórtico.")])
    indice.marcar_lista(b)
    return a, b


@pytest.fixture(params=[True, False], ids=["fts5", "sin-fts5"])
def ind(request, tmp_path):
    i = Indice(str(tmp_path / "i.sqlite3"), usar_fts=request.param)
    yield i
    i.cerrar()


def test_fts5_disponible(indice):
    assert indice.fts, "el SQLite de este Python debería traer FTS5"


def test_buscar_sin_tildes_y_mayusculas(ind):
    a, b = _cargar(ind)
    res = ind.buscar(["nervio ciatico"])
    assert [(r["source_id"], r["pagina"], r["etiqueta"]) for r in res] == [(a, 2, "xii")]
    assert len(ind.buscar(["Arteria Femoral"])) == 3


def test_filtrar_por_fuente(ind):
    a, b = _cargar(ind)
    assert {r["source_id"] for r in ind.buscar(["arteria femoral"], [b])} == {b}
    assert ind.buscar(["arteria femoral"], []) == []


def test_ignora_fuentes_a_medias(ind):
    a, b = _cargar(ind)
    ind.borrar_fragmentos(a)  # vuelve a estado 'indexando'
    ind.agregar_fragmentos(a, [(1, None, "arteria femoral a medias")])
    assert {r["source_id"] for r in ind.buscar(["arteria femoral"])} == {b}


def test_eliminar_y_renombrar(ind):
    a, b = _cargar(ind)
    ind.renombrar(b, "Nuevo")
    v1 = ind.version()
    ind.eliminar_fuente(a)
    assert [f["nombre"] for f in ind.fuentes()] == ["Nuevo"]
    assert ind.version() != v1
    assert {r["source_id"] for r in ind.buscar(["arteria femoral"])} == {b}


def test_buscar_libre(ind):
    _cargar(ind)
    assert len(ind.buscar_libre("grueso ciático")) == 1
    assert ind.buscar_libre("  ") == []


def test_consulta_segura():
    assert consulta_fts(['a "b"', "", "c  d"]) == '"a b" OR "c d"'
    # Caracteres raros no rompen FTS5.
    assert consulta_fts(["AND OR NOT ( ) *"]) == '"AND OR NOT ( ) *"'


def test_comillas_y_operadores_no_rompen(indice):
    _cargar(indice)
    indice.buscar(['NOT (" * '])
    indice.buscar(["AND", "OR", "*"])
    indice.buscar_libre('"; DROP TABLE chunks; --')
    assert len(indice.fuentes()) == 2
