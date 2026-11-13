# -*- coding: utf-8 -*-
"""Insertar o quitar en las plantillas el snippet que carga Pagewise.

Es lo que hace funcionar el popup en AnkiDroid, AnkiMobile y AnkiWeb: la
plantilla carga _pagewise.js y _pagewise.css desde la carpeta de medios
(que se sincroniza con AnkiWeb).

El snippet va delimitado por comentarios para poder quitarlo limpiamente:
quitar(insertar(x)) == x. No se toca nada más de la plantilla.
"""
import re

INICIO = "<!-- PAGEWISE:INICIO (lo gestiona el add-on Pagewise; no edites entre estas marcas) -->"
FIN = "<!-- PAGEWISE:FIN -->"
SNIPPET = (
    INICIO + "\n"
    '<link rel="stylesheet" href="_pagewise.css">\n'
    '<script src="_pagewise.js"></script>\n'
    + FIN
)
# El bloque y el salto de línea que se añadió delante al insertarlo. También
# reconoce el bloque del nombre anterior del add-on (FUENTES), para migrarlo.
_BLOQUE = re.compile(r"\n?<!-- (PAGEWISE|FUENTES):INICIO.*?<!-- \1:FIN -->", re.S)


def tiene(plantilla):
    return "<!-- PAGEWISE:INICIO" in (plantilla or "")


def tiene_antiguo(plantilla):
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
    con = sum(1 for x in lados if tiene(x) or tiene_antiguo(x))
    return "activo" if lados and con == len(lados) else ("parcial" if con else "")


# --- Con colección de Anki (col.models) -------------------------------------

def _renovar(plantilla):
    """Sustituye un bloque existente (también el antiguo) por el actual; si no hay, no toca nada."""
    return insertar(plantilla) if (tiene(plantilla) or tiene_antiguo(plantilla)) else plantilla


def activar(col, ids, solo_con_bloque=False):
    """Inserta el snippet en los tipos de nota indicados. Devuelve cuántos cambiaron.

    Con solo_con_bloque=True solo renueva las plantillas que ya lo llevaban.
    """
    n = 0
    for nid in ids:
        nt = col.models.get(nid)
        if nt and _aplicar(nt, _renovar if solo_con_bloque else insertar):
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
