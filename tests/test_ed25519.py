# -*- coding: utf-8 -*-
"""Vectores de prueba oficiales del RFC 8032 (sección 7.1)."""
import time

from pagewise import ed25519

VECTORES = [
    ("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60",
     "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a",
     "",
     "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155"
     "5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"),
    ("4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb",
     "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c",
     "72",
     "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da"
     "085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00"),
]


def test_vectores_del_rfc():
    for secreta, publica, mensaje, firma in VECTORES:
        s, m = bytes.fromhex(secreta), bytes.fromhex(mensaje)
        assert ed25519.clave_publica(s).hex() == publica
        assert ed25519.firmar(s, m).hex() == firma
        assert ed25519.verificar(bytes.fromhex(publica), m, bytes.fromhex(firma))


def test_rechaza_lo_alterado():
    secreta, publica, _, _ = VECTORES[0]
    s, p = bytes.fromhex(secreta), bytes.fromhex(publica)
    firma = ed25519.firmar(s, b"licencia de ana")
    assert ed25519.verificar(p, b"licencia de ana", firma)
    assert not ed25519.verificar(p, b"licencia de eva", firma)                   # otro mensaje
    assert not ed25519.verificar(p, b"licencia de ana", firma[:-1] + b"\x00")    # firma tocada
    assert not ed25519.verificar(bytes.fromhex(VECTORES[1][1]), b"licencia de ana", firma)  # otra clave
    assert not ed25519.verificar(p, b"x", b"corta")
    assert not ed25519.verificar(b"\xff" * 32, b"x", b"\xff" * 64)


def test_es_rapido_de_sobra():
    secreta, publica, _, firma = VECTORES[0]
    t0 = time.time()
    ed25519.verificar(bytes.fromhex(publica), b"", bytes.fromhex(firma))
    assert time.time() - t0 < 1.0
