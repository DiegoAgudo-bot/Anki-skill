# -*- coding: utf-8 -*-
"""Insertar o quitar en las plantillas el snippet que carga Fuentes.

Es lo que hace funcionar el popup en AnkiDroid, AnkiMobile y AnkiWeb: la
plantilla carga _fuentes.js y _fuentes.css desde la carpeta de medios
(que se sincroniza con AnkiWeb).

El snippet va delimitado por comentarios para poder quitarlo limpiamente:
quitar(insertar(x)) == x. No se toca nada más de la plantilla.
"""
import re

INICIO = "<!-- FUENTES:INICIO (lo gestiona el add-on Fuentes; no edites entre estas marcas) -->"
FIN = "<!-- FUENTES:FIN -->"
SNIPPET = (
    INICIO + "\n"
    '<link rel="stylesheet" href="_fuentes.css">\n'
    '<script src="_fuentes.js"></script>\n'
    + FIN
)
# El bloque y el salto de línea que se añadió delante al insertarlo.
_BLOQUE = re.compile(r"\n?<!-- FUENTES:INICIO.*?<!-- FUENTES:FIN -->", re.S)


def tiene(plantilla):
    return "<!-- FUENTES:INICIO" in (plantilla or "")


def quitar(plantilla):
    return _BLOQUE.sub("", plantilla or "")


def insertar(plantilla):
    """Añade el snippet al final (si ya estaba, lo sustituye por la versión actual)."""
    return quitar(plantilla) + "\n" + SNIPPET


def _aplicar(nt, funcion):
    cambiado = False
    for t in nt["tmpls"]:
        for lado in ("qfmt", "afmt"):
            nuevo = funcion(t[lado])
            if nuevo != t[lado]:
                t[lado] = nuevo
                cambiado = True
    return cambiado


def estado(nt):
    """'activo' si todas las plantillas lo llevan, 'parcial' si algunas, '' si ninguna."""
    lados = [t[l] for t in nt["tmpls"] for l in ("qfmt", "afmt")]
    con = sum(1 for x in lados if tiene(x))
    return "activo" if lados and con == len(lados) else ("parcial" if con else "")


# --- Con colección de Anki (col.models) -------------------------------------

def activar(col, ids):
    """Inserta el snippet en los tipos de nota indicados. Devuelve cuántos cambiaron."""
    n = 0
    for nid in ids:
        nt = col.models.get(nid)
        if nt and _aplicar(nt, insertar):
            col.models.update_dict(nt)
            n += 1
    return n


def desactivar(col, ids):
    n = 0
    for nid in ids:
        nt = col.models.get(nid)
        if nt and _aplicar(nt, quitar):
            col.models.update_dict(nt)
            n += 1
    return n
