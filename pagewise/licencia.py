# -*- coding: utf-8 -*-
"""Licencias de Pagewise Pro. Sin dependencias de Anki y SIN conexión.

Una licencia es un texto que el comprador pega en «Activar Pro»:

    PW1.<datos en base64>.<firma en base64>

Los datos (JSON) llevan el correo del comprador, el plan y, si es una
suscripción, la fecha de caducidad. La firma (Ed25519) se comprueba con la
CLAVE_PUBLICA de abajo: solo quien tiene la clave privada puede emitir
licencias, y esa clave no está en el add-on ni en el repositorio.

Honestidad técnica: el código del add-on es legible, así que quien quiera
saltarse esta comprobación puede hacerlo editándolo. La licencia no es un
candado; es la forma cómoda y legítima de activar Pro.
"""
import base64
import datetime
import json
import os

from . import ed25519

# Clave pública con la que se verifican las licencias. Para cambiarla:
#   python herramientas/licencias.py generar-claves
CLAVE_PUBLICA = bytes.fromhex("9bdd0fd710d81d067169df90397c1a54a23bef9b6dbbe59848a62af0656a676e")

VERSION = "PW1"
LIMITE_FUENTES_GRATIS = 2

# Edición Pro empaquetada (./build.sh --pro): lleva este archivo en la raíz del
# add-on y no necesita licencia. El repositorio no lo incluye.
MARCA_EDICION_PRO = "EDICION_PRO"


def edicion_pro(carpeta=None):
    """¿Es este add-on la edición Pro (sin límite de fuentes, sin licencia)?"""
    carpeta = carpeta or os.path.dirname(os.path.abspath(__file__))
    return os.path.exists(os.path.join(carpeta, MARCA_EDICION_PRO))


class LicenciaInvalida(Exception):
    """motivo: 'formato', 'firma' o 'caducada'."""

    def __init__(self, motivo):
        Exception.__init__(self, motivo)
        self.motivo = motivo


class Licencia:
    def __init__(self, datos):
        self.email = str(datos.get("e", ""))
        self.plan = str(datos.get("p", "pro"))
        self.id = str(datos.get("n", ""))
        self.caduca = datetime.date.fromisoformat(datos["x"]) if datos.get("x") else None  # None = para siempre

    def caducada(self, hoy=None):
        return self.caduca is not None and (hoy or datetime.date.today()) > self.caduca


def _b64(b):
    return base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")


def _de_b64(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def emitir(clave_privada, email, caduca=None, plan="pro", ident=""):
    """Crea el texto de una licencia. Solo lo usa herramientas/licencias.py."""
    datos = {"e": email, "p": plan}
    if caduca:
        datos["x"] = caduca if isinstance(caduca, str) else caduca.isoformat()
    if ident:
        datos["n"] = ident
    cuerpo = json.dumps(datos, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "%s.%s.%s" % (VERSION, _b64(cuerpo), _b64(ed25519.firmar(clave_privada, cuerpo)))


def leer(texto, clave_publica=None, hoy=None):
    """Valida el texto de una licencia y devuelve una Licencia.

    Lanza LicenciaInvalida('formato' | 'firma' | 'caducada').
    """
    limpio = "".join(str(texto or "").split())  # al copiar y pegar se cuelan espacios y saltos
    partes = limpio.split(".")
    if len(partes) != 3 or partes[0] != VERSION:
        raise LicenciaInvalida("formato")
    try:
        cuerpo, firma = _de_b64(partes[1]), _de_b64(partes[2])
    except Exception:
        raise LicenciaInvalida("formato")
    if not ed25519.verificar(clave_publica or CLAVE_PUBLICA, cuerpo, firma):
        raise LicenciaInvalida("firma")
    try:
        lic = Licencia(json.loads(cuerpo.decode("utf-8")))
    except Exception:
        raise LicenciaInvalida("formato")
    if lic.caducada(hoy):
        raise LicenciaInvalida("caducada")
    return lic


# --- Licencia guardada en el ordenador (user_files/licencia.txt) -------------

_cache = {}


def guardada(ruta, clave_publica=None, hoy=None):
    """Licencia válida guardada en `ruta`, o None (no hay, o ya no es válida)."""
    try:
        marca = os.path.getmtime(ruta)
    except OSError:
        return None
    clave = (ruta, marca, hoy or datetime.date.today())
    if clave not in _cache:
        _cache.clear()
        try:
            with open(ruta, encoding="utf-8") as f:
                _cache[clave] = leer(f.read(), clave_publica, hoy)
        except (LicenciaInvalida, OSError, ValueError):
            _cache[clave] = None
    return _cache[clave]


def guardar(ruta, texto, clave_publica=None, hoy=None):
    """Valida y guarda la licencia. Devuelve la Licencia o lanza LicenciaInvalida."""
    lic = leer(texto, clave_publica, hoy)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("".join(str(texto).split()) + "\n")
    _cache.clear()
    return lic


def quitar(ruta):
    _cache.clear()
    try:
        os.remove(ruta)
    except OSError:
        pass


def puede_anadir_fuente(n_fuentes, lic):
    """En la versión gratuita se pueden tener hasta LIMITE_FUENTES_GRATIS fuentes.

    Las que ya existan por encima del límite (por ejemplo, al caducar una
    licencia) siguen funcionando: solo se bloquea añadir más.
    """
    return lic is not None or n_fuentes < LIMITE_FUENTES_GRATIS
