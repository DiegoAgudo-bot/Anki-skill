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

Plurales: un término en singular también casa con su plural ("arteria" →
"arterias", "nervio ciático" → "nervios ciáticos", "nariz" → "narices").
Ver plurales().
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


# Palabras que cortan la concordancia: en "agujero de conjunción" el plural
# es "agujeros de conjunción", así que solo se pluraliza lo que va antes.
_SIN_PLURAL = frozenset(
    "de del la las el los lo un una y e o u ni en a al con por para sin sobre entre tras"
    " desde hasta segun of the and or in on to for with from by at an as".split()
)
_VOCALES = "aeiou"
# Si salen más combinaciones que esto (términos largos), solo la más probable.
_MAX_COMBINACIONES = 16


def plurales_palabra(p):
    """Plurales candidatos de una palabra YA normalizada (sin tildes).

    Reglas del español con algún extra del inglés. Generar alguna forma que no
    existe no hace daño: simplemente no aparecerá en ningún texto.
    """
    if len(p) < 3 or p in _SIN_PLURAL or not all(es_palabra(c) for c in p) or p[-1] in "0123456789":
        return []
    u = p[-1]
    if u in "sx":                      # mes → meses; crisis, bíceps, tórax no cambian
        return [p + "es"]
    if u == "z":                       # nariz → narices
        return [p[:-1] + "ces", p + "es"]
    if u == "y":                       # rey → reyes; artery → arteries; day → days
        return [p + "s", p + "es", p[:-1] + "ies"]
    if u in "iu":                      # bisturí → bisturíes / bisturís
        return [p + "s", p + "es"]
    if u in _VOCALES:                  # arteria → arterias
        return [p + "s"]
    return [p + "es", p + "s"]         # común → comunes; tendon → tendons


def plurales(texto):
    """Formas en plural (normalizadas) de un término; no incluye el singular.

    Se pluralizan a la vez todas las palabras hasta la primera preposición o
    artículo: "vena safena mayor" → "venas safenas mayores".
    """
    palabras = clave(texto).split(" ")
    if not palabras or not palabras[0]:
        return []
    corte = len(palabras)
    for i, w in enumerate(palabras):
        if w in _SIN_PLURAL:
            corte = i
            break
    opciones = [plurales_palabra(w) or [w] for w in palabras[:corte]]
    if not any(plurales_palabra(w) for w in palabras[:corte]):
        return []
    total = 1
    for o in opciones:
        total *= len(o)
    if total > _MAX_COMBINACIONES:
        opciones = [o[:1] for o in opciones]
    formas = [""]
    for o in opciones:
        formas = [(f + " " + x) if f else x for f in formas for x in o]
    resto = " ".join(palabras[corte:])
    return [(f + " " + resto) if resto else f for f in formas]


def con_plurales(variantes, maximo=None):
    """Lista de textos con sus plurales añadidos detrás, sin repetir."""
    vistos = set()
    salida = []
    for v in list(variantes) + [x for v in variantes for x in plurales(v)]:
        k = clave(v)
        if k and k not in vistos:
            vistos.add(k)
            salida.append(v)
    return salida[:maximo] if maximo else salida


class Matcher:
    """Busca términos del glosario en un texto: la frase más larga gana.

    `variantes` es una lista de (texto_variante, id_termino). Se construye un
    trie de caracteres normalizados; en cada inicio de palabra se recorre el
    trie y se queda con la coincidencia más larga que termine en límite de
    palabra.
    """

    def __init__(self, variantes, con_plurales=True):
        self.raiz = {}
        variantes = list(variantes)
        for texto, ident in variantes:
            self._insertar(clave(texto), ident)
        if con_plurales:
            # Después de los originales: si el plural de un término coincide
            # con otro término del glosario, gana el que escribió el usuario.
            for texto, ident in variantes:
                for forma in plurales(texto):
                    self._insertar(forma, ident)

    def _insertar(self, k, ident):
        if not k:
            return
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
