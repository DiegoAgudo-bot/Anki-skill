# -*- coding: utf-8 -*-
"""Proveedores de fragmentos para un término.

Hoy solo existe ProveedorFTS (búsqueda léxica en el índice SQLite). La idea
es que en el futuro se pueda añadir, sin tocar el resto, un proveedor de
búsqueda semántica o un LLM ("Explicar") con la misma interfaz:

    proveedor.fragmentos(variantes, source_ids, por_fuente)
        -> [{"id": 1, "nombre": "Libro", "fragmentos": [{"p": 12, "e": "x", "x": "texto"}]}]

El exportador (para móvil) y los comandos de pycmd (escritorio) solo
conocen esta interfaz.
"""
from .textutil import Matcher, recortar


def agrupar(filas, nombres, matcher, por_fuente, max_caracteres):
    """Agrupa filas del índice por fuente, recortando cada fragmento alrededor
    de la primera coincidencia del matcher (y descartando las que no casan)."""
    por_fuente_dict = {}
    orden = []
    for fila in filas:
        sid = fila["source_id"]
        lista = por_fuente_dict.setdefault(sid, [])
        if sid not in orden:
            orden.append(sid)
        if len(lista) >= por_fuente:
            continue
        # FTS ignora la ñ y la puntuación; confirmamos con nuestro matcher
        # (el mismo criterio que el subrayado de la tarjeta).
        coincidencias = matcher.buscar(fila["texto"])
        if not coincidencias:
            continue
        a, b, _ = coincidencias[0]
        texto = recortar(fila["texto"], a, b, max_caracteres)
        if any(f["x"] == texto for f in lista):
            continue
        frag = {"p": fila["pagina"], "x": texto}
        if fila.get("etiqueta"):
            frag["e"] = fila["etiqueta"]
        lista.append(frag)
    return [
        {"id": sid, "nombre": nombres.get(sid, "?"), "fragmentos": por_fuente_dict[sid]}
        for sid in orden
        if por_fuente_dict[sid]
    ]


class ProveedorFTS:
    nombre = "fts"

    def __init__(self, indice, max_caracteres=360):
        self.indice = indice
        self.max_caracteres = max_caracteres

    def _nombres(self):
        return {f["id"]: f["nombre"] for f in self.indice.fuentes()}

    def fragmentos(self, variantes, source_ids=None, por_fuente=3):
        variantes = [v for v in variantes if v and v.strip()]
        if not variantes:
            return []
        # Pedimos de más: algunos resultados de FTS se descartan al agrupar.
        filas = self.indice.buscar(variantes, source_ids, limite=2000, por_fuente=por_fuente * 3)
        matcher = Matcher([(v, 0) for v in variantes])
        return agrupar(filas, self._nombres(), matcher, por_fuente, self.max_caracteres)

    def buscar_libre(self, texto, source_ids=None, por_fuente=5):
        """Texto libre: fragmentos con todas las palabras. Devuelve (fuentes, palabras)."""
        palabras = [p for p in texto.split() if len(p) > 1]
        filas = self.indice.buscar_libre(texto, source_ids, limite=200)
        matcher = Matcher([(p, 0) for p in palabras])
        return agrupar(filas, self._nombres(), matcher, por_fuente, self.max_caracteres), palabras
