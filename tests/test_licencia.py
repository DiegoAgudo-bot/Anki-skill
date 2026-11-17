# -*- coding: utf-8 -*-
import datetime
import os

import pytest

from pagewise import ed25519, licencia

PRIVADA = bytes(range(32))                 # clave SOLO de pruebas
PUBLICA = ed25519.clave_publica(PRIVADA)
HOY = datetime.date(2026, 6, 1)


def test_ida_y_vuelta():
    texto = licencia.emitir(PRIVADA, "ana@correo.es", ident="pedido-7")
    assert texto.startswith("PW1.") and "\n" not in texto
    lic = licencia.leer(texto, PUBLICA, HOY)
    assert (lic.email, lic.plan, lic.id, lic.caduca) == ("ana@correo.es", "pro", "pedido-7", None)


def test_tolera_espacios_y_saltos_al_pegar():
    texto = licencia.emitir(PRIVADA, "ana@correo.es")
    sucio = "  " + texto[:40] + "\n" + texto[40:90] + " \r\n" + texto[90:] + "\n"
    assert licencia.leer(sucio, PUBLICA, HOY).email == "ana@correo.es"


def test_caducidad():
    texto = licencia.emitir(PRIVADA, "ana@correo.es", caduca="2026-12-31")
    assert licencia.leer(texto, PUBLICA, datetime.date(2026, 12, 31)).caduca == datetime.date(2026, 12, 31)
    with pytest.raises(licencia.LicenciaInvalida) as e:
        licencia.leer(texto, PUBLICA, datetime.date(2027, 1, 1))
    assert e.value.motivo == "caducada"


@pytest.mark.parametrize("texto, motivo", [
    ("", "formato"), ("hola", "formato"), ("PW2.a.b", "formato"), ("PW1.@@.@@", "firma"), ("PW1.a.b.c", "formato"),
])
def test_textos_que_no_son_licencias(texto, motivo):
    with pytest.raises(licencia.LicenciaInvalida) as e:
        licencia.leer(texto, PUBLICA, HOY)
    assert e.value.motivo == motivo


def test_no_se_puede_falsificar():
    texto = licencia.emitir(PRIVADA, "ana@correo.es", caduca="2026-01-01")
    v, cuerpo, firma = texto.split(".")
    # Cambiar los datos (quitar la caducidad) invalida la firma.
    otro = licencia._b64(b'{"e":"ana@correo.es","p":"pro"}')
    with pytest.raises(licencia.LicenciaInvalida) as e:
        licencia.leer(".".join([v, otro, firma]), PUBLICA, HOY)
    assert e.value.motivo == "firma"
    # Una licencia firmada con otra clave tampoco vale.
    ajena = licencia.emitir(bytes(range(1, 33)), "ana@correo.es")
    with pytest.raises(licencia.LicenciaInvalida):
        licencia.leer(ajena, PUBLICA, HOY)


def test_las_licencias_de_prueba_no_valen_en_el_addon_real():
    """La clave pública del add-on no es la de estos tests."""
    assert licencia.CLAVE_PUBLICA != PUBLICA and len(licencia.CLAVE_PUBLICA) == 32
    assert licencia.CLAVE_PUBLICA != bytes(32), "falta generar la clave (herramientas/licencias.py generar-claves)"
    with pytest.raises(licencia.LicenciaInvalida):
        licencia.leer(licencia.emitir(PRIVADA, "ana@correo.es"))


def test_guardar_leer_y_quitar(tmp_path):
    ruta = str(tmp_path / "user_files" / "licencia.txt")
    assert licencia.guardada(ruta, PUBLICA, HOY) is None
    with pytest.raises(licencia.LicenciaInvalida):
        licencia.guardar(ruta, "PW1.x.y", PUBLICA, HOY)
    assert not os.path.exists(ruta)                       # una licencia inválida no se guarda
    licencia.guardar(ruta, licencia.emitir(PRIVADA, "ana@correo.es", caduca="2026-12-31"), PUBLICA, HOY)
    assert licencia.guardada(ruta, PUBLICA, HOY).email == "ana@correo.es"
    assert licencia.guardada(ruta, PUBLICA, datetime.date(2027, 6, 1)) is None   # caducó
    licencia.quitar(ruta)
    assert licencia.guardada(ruta, PUBLICA, HOY) is None


def test_limite_de_la_version_gratuita():
    lic = licencia.leer(licencia.emitir(PRIVADA, "ana@correo.es"), PUBLICA, HOY)
    assert licencia.LIMITE_FUENTES_GRATIS == 2
    assert [licencia.puede_anadir_fuente(n, None) for n in (0, 1, 2, 5)] == [True, True, False, False]
    assert all(licencia.puede_anadir_fuente(n, lic) for n in (0, 2, 50))


def test_edicion_pro_por_marca(tmp_path):
    assert not licencia.edicion_pro(str(tmp_path))
    (tmp_path / licencia.MARCA_EDICION_PRO).write_text("")
    assert licencia.edicion_pro(str(tmp_path))


def test_el_repositorio_no_es_la_edicion_pro():
    # La marca solo la añade ./build.sh --pro dentro del paquete.
    assert not licencia.edicion_pro()
