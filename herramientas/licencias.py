#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Herramienta del VENDEDOR para emitir licencias de Pagewise Pro.

No forma parte del add-on. Necesita la clave privada, que debes guardar tú
en un lugar seguro y con copia: quien la tenga puede emitir licencias, y si
la pierdes no podrás emitir más para las versiones ya distribuidas.

    python herramientas/licencias.py generar-claves mi.clave-privada
        Crea una clave privada nueva y escribe la pública en
        pagewise/licencia.py. Hazlo una vez, antes de vender; las licencias
        emitidas con la clave anterior dejan de valer.

    python herramientas/licencias.py emitir mi.clave-privada ana@correo.es
    python herramientas/licencias.py emitir mi.clave-privada ana@correo.es --caduca 2027-12-31
        Imprime la licencia que le envías al comprador.

    python herramientas/licencias.py comprobar "PW1.xxxx.yyyy"
        Dice si una licencia es válida para el add-on actual.
"""
import argparse
import datetime
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from pagewise import ed25519, licencia  # noqa: E402

ARCHIVO_PUBLICA = os.path.join(RAIZ, "pagewise", "licencia.py")


def _leer_privada(ruta):
    with open(ruta, encoding="ascii") as f:
        clave = bytes.fromhex(f.read().strip())
    if len(clave) != 32:
        sys.exit("La clave privada no tiene el formato esperado (64 caracteres hexadecimales).")
    return clave


def generar_claves(args):
    if os.path.exists(args.archivo):
        sys.exit("Ya existe %s. No lo sobrescribo: bórralo tú si de verdad quieres otra clave." % args.archivo)
    privada = os.urandom(32)
    publica = ed25519.clave_publica(privada).hex()
    descriptor = os.open(args.archivo, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as f:
        f.write(privada.hex() + "\n")
    with open(ARCHIVO_PUBLICA, encoding="utf-8") as f:
        codigo = f.read()
    nuevo, n = re.subn(r'CLAVE_PUBLICA = bytes\.fromhex\("[0-9a-f_A-Z]*"\)',
                       'CLAVE_PUBLICA = bytes.fromhex("%s")' % publica, codigo)
    if n != 1:
        sys.exit("No encuentro CLAVE_PUBLICA en pagewise/licencia.py.")
    with open(ARCHIVO_PUBLICA, "w", encoding="utf-8") as f:
        f.write(nuevo)
    # Python guarda una copia compilada del módulo: la quitamos para que la
    # clave nueva se use desde ya (si no, podría seguir cargando la antigua).
    cache = os.path.join(os.path.dirname(ARCHIVO_PUBLICA), "__pycache__")
    if os.path.isdir(cache):
        for nombre in os.listdir(cache):
            if nombre.startswith("licencia."):
                os.remove(os.path.join(cache, nombre))
    print("Clave privada guardada en %s (NO la subas a ningún repositorio; haz una copia segura)." % args.archivo)
    print("Clave pública escrita en pagewise/licencia.py: %s" % publica)
    print("Vuelve a generar el paquete (./build.sh) para distribuir el add-on con la clave nueva.")


def emitir(args):
    privada = _leer_privada(args.clave)
    if ed25519.clave_publica(privada) != licencia.CLAVE_PUBLICA:
        sys.exit("Esa clave privada no corresponde a la clave pública del add-on: las licencias no valdrían.")
    if args.caduca:
        datetime.date.fromisoformat(args.caduca)  # valida el formato AAAA-MM-DD
    texto = licencia.emitir(privada, args.email.strip().lower(), args.caduca, ident=args.id or "")
    licencia.leer(texto, hoy=datetime.date(2000, 1, 1))  # comprobación: se verifica con el add-on actual
    print(texto)


def comprobar(args):
    try:
        lic = licencia.leer(args.licencia)
    except licencia.LicenciaInvalida as e:
        sys.exit("NO válida: %s" % e.motivo)
    print("Válida. Correo: %s. %s" % (lic.email, "Caduca el %s." % lic.caduca if lic.caduca else "No caduca."))


def main():
    p = argparse.ArgumentParser(description="Licencias de Pagewise Pro")
    sub = p.add_subparsers(dest="orden", required=True)
    g = sub.add_parser("generar-claves"); g.add_argument("archivo"); g.set_defaults(f=generar_claves)
    e = sub.add_parser("emitir"); e.add_argument("clave"); e.add_argument("email")
    e.add_argument("--caduca", help="AAAA-MM-DD; sin esto, la licencia no caduca")
    e.add_argument("--id", help="referencia tuya (nº de pedido…)"); e.set_defaults(f=emitir)
    c = sub.add_parser("comprobar"); c.add_argument("licencia"); c.set_defaults(f=comprobar)
    args = p.parse_args()
    args.f(args)


if __name__ == "__main__":
    main()
