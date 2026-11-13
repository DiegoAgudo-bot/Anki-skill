# -*- coding: utf-8 -*-
"""Utilidades de texto puras (sin Anki): normalización y búsqueda de términos.

IMPORTANTE: el algoritmo de este módulo está duplicado en web/pagewise.js
(el JS es el que subraya en las tarjetas, también en móvil). Ambos se prueban
con los mismos casos: tests/casos_matching.json. Si cambias algo aquí,
cámbialo también allí.

Reglas de normalización:
  * minúsculas;
  * se quitan tildes y diéresis (á→a, ü→u), PERO la ñ se conserva
    (para no confundir "año" con "ano");
  * cualquier racha de espacios (incluido &nbsp; y saltos de línea) cuenta
    como un único espacio.
"""
import re
import unicodedata

# Rangos que nunca deben subrayarse: etiquetas de audio de Anki,
# sintaxis cloze sin renderizar y fórmulas MathJax.
_PROTEGIDO = re.compile(
    r"\[sound:[^\]]*\]|\{\{c\d+::.*?\}\}|\\\(.*?\\\)|\\\[.*?\\\]", re.S
)
_ESPACIOS = " \t\n\r\f\v     "


def _normalizar_caracter(c):
    """Devuelve la forma normalizada de un carácter (puede ser '' o varios)."""
    bajo = c.lower()
    if bajo == "ñ":
        return "ñ"
    descompuesto = unicodedata.normalize("NFD", bajo)
    return "".join(x for x in descompuesto if not ("̀" <= x <= "ͯ"))


def es_palabra(c):
    """¿El carácter (ya normalizado) forma parte de una palabra?

    Usamos la misma heurística que en JS (que no tiene \\p{L} en móviles
    antiguos): letra si tiene mayúscula/minúscula distinta, o dígito.
    """
    return c in "0123456789" or c.lower() != c.upper()


def normalizar(texto):
    """Normaliza un texto y devuelve (normalizado, mapa).

    mapa[k] es el índice en `texto` del carácter que produjo la posición k
    de `normalizado`. Sirve para traducir coincidencias al texto original.
    """
    salida = []
    mapa = []
    en_espacio = False
    for i, c in enumerate(texto):
        if c in _ESPACIOS:
            if not en_espacio:
                salida.append(" ")
                mapa.append(i)
            en_espacio = True
            continue
        en_espacio = False
        for x in _normalizar_caracter(c):
            salida.append(x)
            mapa.append(i)
    return "".join(salida), mapa


def clave(texto):
    """Forma normalizada y recortada de un término (para comparar y deduplicar)."""
    return normalizar(texto.strip())[0].strip()


class Matcher:
    """Busca términos del glosario en un texto: la frase más larga gana.

    `variantes` es una lista de (texto_variante, id_termino). Se construye un
    trie de caracteres normalizados; en cada inicio de palabra se recorre el
    trie y se queda con la coincidencia más larga que termine en límite de
    palabra.
    """

    def __init__(self, variantes):
        self.raiz = {}
        for texto, ident in variantes:
            k = clave(texto)
            if not k:
                continue
            nodo = self.raiz
            for c in k:
                nodo = nodo.setdefault(c, {})
            # Si dos términos comparten forma normalizada, gana el primero.
            nodo.setdefault("\0", ident)

    def buscar(self, texto):
        """Devuelve una lista de (inicio, fin, id) sobre el texto ORIGINAL."""
        norm, mapa = normalizar(texto)
        protegidos = [(m.start(), m.end()) for m in _PROTEGIDO.finditer(texto)]
        resultados = []
        n = len(norm)
        k = 0
        while k < n:
            if (k > 0 and es_palabra(norm[k - 1])) or not es_palabra(norm[k]):
                k += 1
                continue
            nodo = self.raiz
            j = k
            mejor = None
            while j < n and norm[j] in nodo:
                nodo = nodo[norm[j]]
                j += 1
                if "\0" in nodo and (j == n or not es_palabra(norm[j])):
                    mejor = (j, nodo["\0"])
            if mejor is None:
                k += 1
                continue
            fin_norm, ident = mejor
            inicio = mapa[k]
            fin = mapa[fin_norm - 1] + 1
            if not any(a < fin and inicio < b for a, b in protegidos):
                resultados.append((inicio, fin, ident))
            k = fin_norm
        return resultados


def recortar(texto, inicio, fin, largo=360):
    """Recorta `texto` a unos `largo` caracteres alrededor de [inicio, fin).

    Corta en espacios y añade "…" donde se ha recortado.
    """
    if len(texto) <= largo:
        return texto
    margen = max(0, (largo - (fin - inicio)) // 2)
    a = max(0, inicio - margen)
    b = min(len(texto), a + largo)
    a = max(0, b - largo)
    if a > 0:
        espacio = texto.find(" ", a)
        if espacio != -1 and espacio < inicio:
            a = espacio + 1
    if b < len(texto):
        espacio = texto.rfind(" ", fin, b)
        if espacio != -1:
            b = espacio
    return ("…" if a > 0 else "") + texto[a:b].strip() + ("…" if b < len(texto) else "")
