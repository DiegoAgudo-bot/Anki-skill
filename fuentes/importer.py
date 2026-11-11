# -*- coding: utf-8 -*-
"""Importación de PDFs: extracción de texto, limpieza y troceado.

No depende de Anki: se puede probar con pytest. La interfaz (ui/) lo llama
en segundo plano y le pasa funciones de progreso y cancelación.
"""
import hashlib
import os
import re
import shutil
import sys
from collections import Counter

_VENDOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor")
if _VENDOR not in sys.path:
    # Al final de sys.path: si Anki u otro add-on ya trae estas librerías,
    # no las pisamos.
    sys.path.append(_VENDOR)

from pypdf import PdfReader  # noqa: E402

# Una página con menos caracteres útiles que esto se considera "sin texto".
MIN_CARACTERES_PAGINA = 25
# Si más de este porcentaje de páginas no tiene texto, el PDF es escaneado.
UMBRAL_ESCANEADO = 0.9
# Tamaño objetivo de cada fragmento indexado (en caracteres).
TAM_FRAGMENTO = 700
TAM_MAX_FRAGMENTO = 1100


class ImportacionCancelada(Exception):
    pass


class PdfNoLegible(Exception):
    """El PDF no se puede abrir (dañado, protegido con contraseña…)."""


class Resultado:
    def __init__(self, source_id, paginas, fragmentos, paginas_sin_texto, escaneado):
        self.source_id = source_id
        self.paginas = paginas
        self.fragmentos = fragmentos
        self.paginas_sin_texto = paginas_sin_texto
        self.escaneado = escaneado


# --------------------------------------------------------------------------
# Lectura del PDF
# --------------------------------------------------------------------------

def abrir_pdf(ruta):
    try:
        lector = PdfReader(ruta, strict=False)
        if lector.is_encrypted:
            # Muchos PDFs "protegidos" solo tienen contraseña de propietario.
            try:
                if not lector.decrypt(""):
                    raise PdfNoLegible("El PDF está protegido con contraseña.")
            except PdfNoLegible:
                raise
            except Exception:
                raise PdfNoLegible(
                    "El PDF está cifrado y no se puede leer sin librerías extra."
                )
        len(lector.pages)  # fuerza la lectura de la estructura de páginas
        return lector
    except PdfNoLegible:
        raise
    except Exception as e:
        raise PdfNoLegible("No se puede leer el PDF: %s" % e)


def _etiqueta(lector, i):
    """Número de página impreso (p. ej. 'xii' o '45'); None si coincide con el físico."""
    try:
        etiqueta = lector.page_labels[i]
    except Exception:
        return None
    return None if etiqueta == str(i + 1) else etiqueta


def extraer_paginas(lector, progreso=None, cancelado=None):
    """Extrae el texto bruto de cada página. Devuelve [(etiqueta, texto)].

    Se procesa página a página; `progreso(hechas, total)` se llama a menudo y
    `cancelado()` permite abortar a mitad (lanza ImportacionCancelada).
    """
    total = len(lector.pages)
    paginas = []
    for i in range(total):
        if cancelado and cancelado():
            raise ImportacionCancelada()
        try:
            texto = lector.pages[i].extract_text() or ""
        except Exception:
            texto = ""  # una página rota no debe tumbar la importación
        paginas.append((_etiqueta(lector, i), texto))
        if progreso and (i % 5 == 0 or i == total - 1):
            progreso(i + 1, total)
    return paginas


# --------------------------------------------------------------------------
# Limpieza del texto
# --------------------------------------------------------------------------

_NUMERO_PAGINA = re.compile(
    r"^(p[aá]g(ina)?\.?\s*)?[-–—\s]*\d{1,4}([\s/]+(de\s+)?\d{1,4})?[-–—\s]*$", re.I
)


def _clave_linea(linea):
    """Clave para detectar cabeceras/pies: sin números ni espacios extra."""
    return re.sub(r"\s+", " ", re.sub(r"\d+", "#", linea.lower())).strip()


def _lineas(texto):
    return [l.strip() for l in texto.replace("­", "").splitlines() if l.strip()]


def detectar_repetidas(textos, bordes=2):
    """Devuelve las claves de líneas que se repiten arriba o abajo en muchas páginas."""
    cuenta = Counter()
    con_texto = 0
    for texto in textos:
        lineas = _lineas(texto)
        if not lineas:
            continue
        con_texto += 1
        # En páginas con pocas líneas miramos menos, para no tomar el
        # contenido por cabecera.
        k = max(1, min(bordes, len(lineas) // 2))
        candidatas = set(lineas[:k] + lineas[-k:])
        cuenta.update({_clave_linea(l) for l in candidatas})
    if con_texto < 3:
        return set()
    umbral = max(3, int(con_texto * 0.3))
    return {k for k, n in cuenta.items() if n >= umbral and k and k != "#"}


def limpiar_pagina(texto, repetidas=frozenset(), bordes=2):
    """Limpia el texto de una página y lo devuelve en una sola línea."""
    lineas = _lineas(texto)

    def es_ruido(linea):
        return _clave_linea(linea) in repetidas or bool(_NUMERO_PAGINA.match(linea))

    # Quitar cabeceras y pies (solo en los bordes de la página).
    for _ in range(bordes):
        if lineas and es_ruido(lineas[0]):
            lineas.pop(0)
        if lineas and es_ruido(lineas[-1]):
            lineas.pop()

    # Unir líneas, reparando palabras cortadas con guion a final de línea:
    # "arte-" + "ria" -> "arteria" (solo si sigue minúscula, para no romper
    # compuestos como "Guyton-Hall").
    salida = ""
    for linea in lineas:
        if (
            salida.endswith("-")
            and len(salida) > 1
            and salida[-2].isalpha()
            and linea[:1].islower()
        ):
            salida = salida[:-1] + linea
        elif salida:
            salida += " " + linea
        else:
            salida = linea
    return re.sub(r"\s+", " ", salida).strip()


def trocear(texto, tam=TAM_FRAGMENTO, tam_max=TAM_MAX_FRAGMENTO):
    """Divide el texto de una página en fragmentos por frases."""
    if not texto:
        return []
    frases = re.split(r"(?<=[.!?;:])\s+", texto)
    fragmentos = []
    actual = ""
    for frase in frases:
        # Frases larguísimas (tablas, listas sin puntos): cortar por espacios.
        while len(frase) > tam_max:
            corte = frase.rfind(" ", 0, tam)
            corte = corte if corte > 0 else tam
            if actual:
                fragmentos.append(actual)
                actual = ""
            fragmentos.append(frase[:corte].strip())
            frase = frase[corte:].strip()
        if actual and len(actual) + 1 + len(frase) > tam:
            fragmentos.append(actual)
            actual = frase
        else:
            actual = (actual + " " + frase).strip()
    if actual:
        fragmentos.append(actual)
    return fragmentos


# --------------------------------------------------------------------------
# Importación completa
# --------------------------------------------------------------------------

def sha1_archivo(ruta):
    h = hashlib.sha1()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def _slug(nombre):
    base = re.sub(r"[^a-z0-9]+", "-", nombre.lower()).strip("-")
    return base[:40] or "fuente"


def copiar_pdf(ruta_original, carpeta_pdfs, sha1):
    """Copia el PDF a la carpeta del add-on (user_files/pdfs).

    Así la fuente sigue funcionando aunque el usuario mueva o borre el original.
    Devuelve el nombre del archivo copiado (relativo a carpeta_pdfs).
    """
    os.makedirs(carpeta_pdfs, exist_ok=True)
    nombre = os.path.splitext(os.path.basename(ruta_original))[0]
    destino = "%s-%s.pdf" % (_slug(nombre), sha1[:10])
    ruta_destino = os.path.join(carpeta_pdfs, destino)
    if not os.path.exists(ruta_destino):
        temporal = ruta_destino + ".tmp"
        shutil.copyfile(ruta_original, temporal)
        os.replace(temporal, ruta_destino)
    return destino


def indexar_paginas(indice, source_id, paginas, progreso=None, cancelado=None):
    """Limpia, trocea y guarda en el índice. Devuelve (nº fragmentos, páginas sin texto)."""
    repetidas = detectar_repetidas([t for _, t in paginas])
    n_fragmentos = 0
    sin_texto = 0
    lote = []
    for i, (etiqueta, bruto) in enumerate(paginas):
        if cancelado and cancelado():
            raise ImportacionCancelada()
        limpio = limpiar_pagina(bruto, repetidas)
        if len(limpio) < MIN_CARACTERES_PAGINA:
            sin_texto += 1
        for trozo in trocear(limpio):
            lote.append((i + 1, etiqueta, trozo))
        # Guardar por lotes: no acumulamos todo el libro en una transacción.
        if len(lote) >= 300:
            indice.agregar_fragmentos(source_id, lote)
            n_fragmentos += len(lote)
            lote = []
        if progreso and (i % 20 == 0 or i == len(paginas) - 1):
            progreso(i + 1, len(paginas))
    if lote:
        indice.agregar_fragmentos(source_id, lote)
        n_fragmentos += len(lote)
    return n_fragmentos, sin_texto


def es_escaneado(paginas_sin_texto, total):
    return total > 0 and paginas_sin_texto / float(total) >= UMBRAL_ESCANEADO


def importar_pdf(indice, ruta, carpeta_pdfs, nombre=None, progreso=None, cancelado=None):
    """Importa un PDF: lo copia, extrae, limpia e indexa.

    `progreso(fase, hechas, total)` con fase "extraer" o "indexar".
    Si el PDF es escaneado (casi sin texto) NO se guarda y se devuelve
    Resultado con escaneado=True y source_id=None.
    """
    def prog(fase):
        return (lambda h, t: progreso(fase, h, t)) if progreso else None

    lector = abrir_pdf(ruta)
    sha1 = sha1_archivo(ruta)
    existente = indice.fuente_por_sha1(sha1)
    if existente:
        raise ValueError('Este PDF ya está importado como "%s".' % existente["nombre"])

    paginas = extraer_paginas(lector, prog("extraer"), cancelado)
    total = len(paginas)
    vacias = sum(1 for _, t in paginas if len(t.strip()) < MIN_CARACTERES_PAGINA)
    if es_escaneado(vacias, total):
        return Resultado(None, total, 0, vacias, True)

    archivo = copiar_pdf(ruta, carpeta_pdfs, sha1)
    nombre = nombre or os.path.splitext(os.path.basename(ruta))[0]
    source_id = indice.agregar_fuente(nombre, archivo, ruta, total, sha1)
    try:
        n, sin_texto = indexar_paginas(indice, source_id, paginas, prog("indexar"), cancelado)
    except BaseException:
        # Cancelación o error: no dejamos fuentes a medias.
        indice.eliminar_fuente(source_id)
        try:
            os.remove(os.path.join(carpeta_pdfs, archivo))
        except OSError:
            pass
        raise
    indice.marcar_lista(source_id)
    return Resultado(source_id, total, n, sin_texto, False)


def reindexar(indice, source_id, carpeta_pdfs, progreso=None, cancelado=None):
    """Vuelve a extraer e indexar una fuente a partir de su copia del PDF."""
    def prog(fase):
        return (lambda h, t: progreso(fase, h, t)) if progreso else None

    fuente = indice.fuente(source_id)
    lector = abrir_pdf(os.path.join(carpeta_pdfs, fuente["archivo"]))
    paginas = extraer_paginas(lector, prog("extraer"), cancelado)
    indice.borrar_fragmentos(source_id)
    n, sin_texto = indexar_paginas(indice, source_id, paginas, prog("indexar"), cancelado)
    indice.marcar_lista(source_id, len(paginas))
    return Resultado(source_id, len(paginas), n, sin_texto, False)


# --------------------------------------------------------------------------
# Propuesta de términos a partir de los marcadores (outline)
# --------------------------------------------------------------------------

_GENERICOS = {
    "indice", "introduccion", "bibliografia", "referencias", "contenido",
    "contenidos", "prologo", "prefacio", "resumen", "anexo", "apendice",
    "glosario", "agradecimientos", "portada", "creditos", "conclusiones",
    "ejercicios", "preguntas", "autoevaluacion", "sumario",
}
_NUMERACION = re.compile(
    r"^((cap[ií]tulo|tema|secci[oó]n|parte|unidad|lecci[oó]n)\s+[\divxlc]+\s*[:.\-–—]?\s*"
    r"|[\divxlc]+(\.\d+)*[.)]?\s+)",
    re.I,
)


def _titulos_outline(nodos):
    for nodo in nodos:
        if isinstance(nodo, list):
            for t in _titulos_outline(nodo):
                yield t
        else:
            titulo = getattr(nodo, "title", None)
            if titulo:
                yield titulo


def proponer_terminos(ruta):
    """Lista de términos candidatos sacados de los marcadores del PDF.

    El usuario los revisa antes de añadirlos al glosario.
    """
    from .textutil import clave

    try:
        outline = abrir_pdf(ruta).outline
    except Exception:
        return []
    vistos = set()
    propuestos = []
    for titulo in _titulos_outline(outline):
        t = re.sub(r"\s+", " ", titulo).strip(" .:-–—")
        t = _NUMERACION.sub("", t).strip(" .:-–—")
        k = clave(t)
        if not (3 <= len(t) <= 60) or k in vistos or k in _GENERICOS:
            continue
        if not re.search(r"[^\W\d_]", t):  # sin letras
            continue
        vistos.add(k)
        propuestos.append(t)
    return propuestos
