# -*- coding: utf-8 -*-
import os
import time

import pytest

from pagewise import importer


def test_limpieza_guiones_y_espacios():
    bruto = "La arte-\nria femoral   y el\nnervio Guyton-\nHall."
    assert importer.limpiar_pagina(bruto) == "La arteria femoral y el nervio Guyton- Hall."


def test_quita_cabeceras_pies_y_numeros():
    paginas = ["Mi libro — Tema %d\nTexto de la página %d con contenido.\nPágina %d de 9" % (i, i, i) for i in range(1, 10)]
    rep = importer.detectar_repetidas(paginas)
    limpio = importer.limpiar_pagina(paginas[3], rep)
    assert limpio == "Texto de la página 4 con contenido."


def test_no_quita_lineas_si_hay_pocas_paginas():
    assert importer.detectar_repetidas(["a\nb", "a\nb"]) == set()


def test_trocear_respeta_tamano():
    texto = " ".join("Frase número %d con algo de texto." % i for i in range(200))
    trozos = importer.trocear(texto, tam=300, tam_max=500)
    assert all(len(t) <= 500 for t in trozos)
    assert " ".join(trozos) == texto
    # Una "frase" enorme sin puntos también se corta.
    largo = "palabra " * 500
    assert all(len(t) <= 1100 for t in importer.trocear(largo))


def test_importar_pdf(indice, pdfs, tmp_path):
    carpeta = str(tmp_path / "pdfs")
    progreso = []
    r = importer.importar_pdf(indice, pdfs["apuntes"], carpeta, nombre="Apuntes",
                              progreso=lambda f, h, t: progreso.append((f, h, t)))
    assert not r.escaneado and r.paginas == 3 and r.fragmentos > 0
    assert {f for f, _, _ in progreso} == {"extraer", "indexar"}
    fuente = indice.fuente(r.source_id)
    assert fuente["estado"] == "lista" and fuente["nombre"] == "Apuntes"
    # El PDF se COPIA a la carpeta del add-on.
    assert os.path.exists(os.path.join(carpeta, fuente["archivo"]))
    # La palabra partida con guion se ha reparado.
    textos = " ".join(f["texto"] for f in indice.buscar(["cavidades"]))
    assert "cavidades" in textos
    # Las cabeceras repetidas no están en el índice.
    assert indice.buscar(["Material de prueba"]) == []


def test_pdf_duplicado(indice, pdfs, tmp_path):
    importer.importar_pdf(indice, pdfs["apuntes"], str(tmp_path))
    with pytest.raises(ValueError):
        importer.importar_pdf(indice, pdfs["apuntes"], str(tmp_path))


def test_escaneado_no_se_importa(indice, pdfs, tmp_path):
    r = importer.importar_pdf(indice, pdfs["escaneado"], str(tmp_path))
    assert r.escaneado and r.source_id is None
    assert indice.fuentes() == []


def test_cancelar_no_deja_restos(indice, pdfs, tmp_path):
    llamadas = []

    def cancelado():
        llamadas.append(1)
        return len(llamadas) > 4  # cancela durante la indexación

    carpeta = tmp_path / "pdfs"
    with pytest.raises(importer.ImportacionCancelada):
        importer.importar_pdf(indice, pdfs["apuntes"], str(carpeta), cancelado=cancelado)
    assert indice.fuentes() == []
    assert os.listdir(str(carpeta)) == []


def test_pdf_ilegible(indice, tmp_path):
    malo = tmp_path / "malo.pdf"
    malo.write_bytes(b"esto no es un pdf")
    with pytest.raises(importer.PdfNoLegible):
        importer.importar_pdf(indice, str(malo), str(tmp_path / "pdfs"))


def test_reindexar(indice, pdfs, tmp_path):
    carpeta = str(tmp_path)
    r = importer.importar_pdf(indice, pdfs["apuntes"], carpeta)
    antes = indice.fuentes()[0]["fragmentos"]
    r2 = importer.reindexar(indice, r.source_id, carpeta)
    assert indice.fuentes()[0]["fragmentos"] == antes == r2.fragmentos


def test_proponer_terminos(pdfs):
    assert importer.proponer_terminos(pdfs["apuntes"]) == [
        "Sistema cardiovascular", "Sistema nervioso periférico", "Aparato locomotor"]
    assert importer.proponer_terminos(pdfs["resumen"]) == []


@pytest.mark.lento
def test_pdf_de_1200_paginas(indice, tmp_path):
    import generar_pdfs
    ruta = generar_pdfs.generar_apuntes(str(tmp_path / "grande.pdf"), repeticiones=400)
    t0 = time.time()
    r = importer.importar_pdf(indice, ruta, str(tmp_path / "pdfs"))
    duracion = time.time() - t0
    print("\n1200 páginas importadas en %.1f s (%d fragmentos)" % (duracion, r.fragmentos))
    assert r.paginas == 1200
    t0 = time.time()
    for _ in range(100):
        indice.buscar(["arteria femoral", "a. femoral"])
    print("100 búsquedas en %.3f s" % (time.time() - t0))
