# -*- coding: utf-8 -*-
"""Exportación de datos precalculados a la carpeta de medios de Anki.

Así el popup funciona sin conexión en AnkiDroid, AnkiMobile y AnkiWeb: los
archivos viajan con la sincronización de medios del propio usuario.

IMPORTANTE: la carpeta de medios de Anki es PLANA (no se sincronizan
subcarpetas), así que todo va en la raíz con el prefijo "_pagewise_".
Anki no borra los medios que empiezan por "_" al "Comprobar medios".

Archivos generados:
    _pagewise_glosario.json          términos, sinónimos, archivo de cada uno y ajustes
    _pagewise_t_<slug>_<hash>.json   mejores fragmentos de cada término
    _pagewise.js / _pagewise.css      el script y el estilo del popup

No depende de Anki (se prueba con pytest).
"""
import hashlib
import json
import os

from . import glossary
from .providers import ProveedorFTS

PREFIJO = "_pagewise"
PREFIJO_TERMINO = "_pagewise_t_"
GLOSARIO = "_pagewise_glosario.json"
VERSION_FORMATO = 1

AJUSTES_POR_DEFECTO = {
    "subrayado": True,
    "fragmentos_por_fuente": 3,
    "max_caracteres_fragmento": 300,
    "solo_primera_aparicion": True,
    "fuentes_inactivas": [],
    "idioma": "es",
}


class Informe:
    def __init__(self):
        self.terminos = 0           # términos exportados (con fragmentos)
        self.sin_resultados = []    # términos del glosario sin ningún fragmento
        self.escritos = 0           # archivos escritos o actualizados
        self.borrados = 0           # archivos viejos eliminados
        self.bytes = 0              # tamaño total de lo exportado

    def __repr__(self):
        return "<Informe %d términos, %d escritos, %d borrados, %d bytes>" % (
            self.terminos, self.escritos, self.borrados, self.bytes)


def _json(datos):
    return json.dumps(datos, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _escribir_si_cambia(ruta, contenido):
    """Escribe solo si el contenido es distinto: evita resincronizar medios iguales."""
    try:
        with open(ruta, "rb") as f:
            if f.read() == contenido:
                return False
    except (IOError, OSError):
        pass
    temporal = ruta + ".tmp"
    with open(temporal, "wb") as f:
        f.write(contenido)
    os.replace(temporal, ruta)
    return True


def tamano_exportado(carpeta_medios):
    """Bytes que ocupan los archivos del add-on en la carpeta de medios."""
    total = 0
    try:
        nombres = os.listdir(carpeta_medios)
    except OSError:
        return 0
    for n in nombres:
        if n.startswith(PREFIJO):
            try:
                total += os.path.getsize(os.path.join(carpeta_medios, n))
            except OSError:
                pass
    return total


def formato_tamano(n):
    for unidad in ("B", "KB", "MB", "GB"):
        if n < 1024 or unidad == "GB":
            return ("%d %s" % (n, unidad)) if unidad == "B" else ("%.1f %s" % (n, unidad))
        n /= 1024.0


def copiar_web(carpeta_web, carpeta_medios):
    """Copia pagewise.js y pagewise.css como _pagewise.js y _pagewise.css. Devuelve nº escritos."""
    escritos = 0
    for origen, destino in (("pagewise.js", "_pagewise.js"), ("pagewise.css", "_pagewise.css")):
        with open(os.path.join(carpeta_web, origen), "rb") as f:
            escritos += _escribir_si_cambia(os.path.join(carpeta_medios, destino), f.read())
    return escritos


def _ajustes(ajustes):
    a = dict(AJUSTES_POR_DEFECTO)
    a.update(ajustes or {})
    return a


def _firma(*partes):
    return hashlib.sha1(json.dumps(partes, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def exportar(indice, terminos, carpeta_medios, carpeta_web, ajustes=None,
             cache=None, proveedor=None, progreso=None):
    """Genera todos los archivos para el móvil.

    `cache` es un dict (persistido por quien llama) que permite NO recalcular
    los términos que no han cambiado desde la última exportación a esta
    carpeta de medios: editar el glosario solo recalcula lo editado.
    Devuelve un Informe.
    """
    a = _ajustes(ajustes)
    cache = cache if cache is not None else {}
    proveedor = proveedor or ProveedorFTS(indice, a["max_caracteres_fragmento"])
    informe = Informe()
    os.makedirs(carpeta_medios, exist_ok=True)

    inactivas = set(a["fuentes_inactivas"])
    activas = [f["id"] for f in indice.fuentes() if f["estado"] == "lista" and f["id"] not in inactivas]
    # Si cambia el índice o los ajustes que afectan a los fragmentos, se recalcula todo.
    firma_global = _firma(indice.version(), activas, a["fragmentos_por_fuente"],
                          a["max_caracteres_fragmento"], proveedor.nombre, VERSION_FORMATO)
    anteriores = cache.get("terminos", {}) if cache.get("firma") == firma_global else {}
    nuevos = {}

    entradas = []
    vivos = set()
    activos = [t for t in terminos if t.get("activo", True)]
    for n, t in enumerate(activos):
        variantes = [t["termino"]] + list(t["sinonimos"])
        archivo = glossary.nombre_archivo(t["termino"])
        clave_cache = _firma(variantes)
        previo = anteriores.get(clave_cache)
        if previo is not None and (previo == "" or os.path.exists(os.path.join(carpeta_medios, archivo))):
            hay_datos = previo != ""
        else:
            fuentes = proveedor.fragmentos(variantes, activas, a["fragmentos_por_fuente"]) if activas else []
            hay_datos = bool(fuentes)
            if hay_datos:
                datos = {"t": t["termino"], "fuentes": fuentes}
                informe.escritos += _escribir_si_cambia(os.path.join(carpeta_medios, archivo), _json(datos))
        nuevos[clave_cache] = archivo if hay_datos else ""
        if hay_datos:
            vivos.add(archivo)
            entradas.append({"t": t["termino"], "s": list(t["sinonimos"]), "f": archivo})
        else:
            informe.sin_resultados.append(t["termino"])
        if progreso and (n % 25 == 0 or n == len(activos) - 1):
            progreso(n + 1, len(activos))

    glosario_json = {
        "version": VERSION_FORMATO,
        "ajustes": {
            "subrayado": bool(a["subrayado"]),
            "fragmentos": int(a["fragmentos_por_fuente"]),
            "soloPrimera": bool(a["solo_primera_aparicion"]),
            "idioma": str(a["idioma"]),
        },
        "terminos": entradas,
    }
    informe.escritos += _escribir_si_cambia(os.path.join(carpeta_medios, GLOSARIO), _json(glosario_json))
    informe.escritos += copiar_web(carpeta_web, carpeta_medios)

    # Borrar archivos de términos que ya no existen o ya no tienen fragmentos.
    for nombre in os.listdir(carpeta_medios):
        if nombre.startswith(PREFIJO_TERMINO) and nombre not in vivos:
            try:
                os.remove(os.path.join(carpeta_medios, nombre))
                informe.borrados += 1
            except OSError:
                pass

    cache.clear()
    cache.update({"firma": firma_global, "terminos": nuevos})
    informe.terminos = len(entradas)
    informe.bytes = tamano_exportado(carpeta_medios)
    return informe


def borrar_todo(carpeta_medios):
    """Elimina todos los archivos del add-on de la carpeta de medios."""
    n = 0
    for nombre in os.listdir(carpeta_medios):
        if nombre.startswith(PREFIJO):
            os.remove(os.path.join(carpeta_medios, nombre))
            n += 1
    return n
