# -*- coding: utf-8 -*-
"""Firmas Ed25519 en Python puro (algoritmo de referencia del RFC 8032).

El add-on solo necesita verificar(); firmar() lo usa la herramienta que
emite licencias (herramientas/licencias.py), con una clave privada que NUNCA
se incluye en el add-on ni en el repositorio.

Es lento comparado con una librería nativa (unos milisegundos por firma),
pero no añade dependencias y basta para comprobar una licencia al arrancar.
"""
import hashlib

_p = 2 ** 255 - 19
_q = 2 ** 252 + 27742317777372353535851937790883648493


def _inv(x):
    return pow(x, _p - 2, _p)


_d = -121665 * _inv(121666) % _p
_RAIZ_M1 = pow(2, (_p - 1) // 4, _p)


def _sha512(b):
    return hashlib.sha512(b).digest()


def _sha512_modq(b):
    return int.from_bytes(_sha512(b), "little") % _q


def _sumar(P, Q):
    A = (P[1] - P[0]) * (Q[1] - Q[0]) % _p
    B = (P[1] + P[0]) * (Q[1] + Q[0]) % _p
    C = 2 * P[3] * Q[3] * _d % _p
    D = 2 * P[2] * Q[2] % _p
    E, F, G, H = B - A, D - C, D + C, B + A
    return (E * F % _p, G * H % _p, F * G % _p, E * H % _p)


def _multiplicar(s, P):
    Q = (0, 1, 1, 0)  # punto neutro
    while s > 0:
        if s & 1:
            Q = _sumar(Q, P)
        P = _sumar(P, P)
        s >>= 1
    return Q


def _iguales(P, Q):
    return (P[0] * Q[2] - Q[0] * P[2]) % _p == 0 and (P[1] * Q[2] - Q[1] * P[2]) % _p == 0


def _recuperar_x(y, signo):
    if y >= _p:
        return None
    x2 = (y * y - 1) * _inv(_d * y * y + 1) % _p
    if x2 == 0:
        return None if signo else 0
    x = pow(x2, (_p + 3) // 8, _p)
    if (x * x - x2) % _p != 0:
        x = x * _RAIZ_M1 % _p
    if (x * x - x2) % _p != 0:
        return None
    if (x & 1) != signo:
        x = _p - x
    return x


_gy = 4 * _inv(5) % _p
_gx = _recuperar_x(_gy, 0)
_G = (_gx, _gy, 1, _gx * _gy % _p)


def _comprimir(P):
    zinv = _inv(P[2])
    x, y = P[0] * zinv % _p, P[1] * zinv % _p
    return (y | ((x & 1) << 255)).to_bytes(32, "little")


def _descomprimir(b):
    if len(b) != 32:
        return None
    y = int.from_bytes(b, "little")
    signo = y >> 255
    y &= (1 << 255) - 1
    x = _recuperar_x(y, signo)
    return None if x is None else (x, y, 1, x * y % _p)


def _expandir(secreta):
    h = _sha512(secreta)
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= 1 << 254
    return a, h[32:]


def clave_publica(secreta):
    """Clave pública (32 bytes) de una clave privada (32 bytes)."""
    a, _ = _expandir(secreta)
    return _comprimir(_multiplicar(a, _G))


def firmar(secreta, mensaje):
    """Firma (64 bytes) de `mensaje` con la clave privada."""
    a, prefijo = _expandir(secreta)
    A = _comprimir(_multiplicar(a, _G))
    r = _sha512_modq(prefijo + mensaje)
    Rs = _comprimir(_multiplicar(r, _G))
    h = _sha512_modq(Rs + A + mensaje)
    s = (r + h * a) % _q
    return Rs + s.to_bytes(32, "little")


def verificar(publica, mensaje, firma):
    """True si `firma` es una firma válida de `mensaje` para esa clave pública."""
    if len(publica) != 32 or len(firma) != 64:
        return False
    A = _descomprimir(publica)
    R = _descomprimir(firma[:32])
    if A is None or R is None:
        return False
    s = int.from_bytes(firma[32:], "little")
    if s >= _q:
        return False
    h = _sha512_modq(firma[:32] + publica + mensaje)
    return _iguales(_multiplicar(s, _G), _sumar(R, _multiplicar(h, A)))
