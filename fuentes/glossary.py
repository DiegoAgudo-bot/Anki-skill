# -*- coding: utf-8 -*-
"""Glosario editable: términos + sinónimos (user_files/glosario.json).

Formato del archivo:
    {"version": 1, "terminos": [
        {"termino": "arteria femoral", "sinonimos": ["a. femoral"], "activo": true}
    ]}

El add-on se distribuye con el glosario VACÍO: lo rellena el usuario (a mano
o aceptando propuestas sacadas de los marcadores de sus PDFs).
"""
import hashlib
import json
import os
import re

from .textutil import clave

VERSION = 1


def _entrada(termino, sinonimos=(), activo=True):
    return {"termino": termino, "sinonimos": list(sinonimos), "activo": bool(activo)}


def limpiar(terminos):
    """Recorta espacios, quita vacíos y fusiona duplicados (sin tildes ni mayúsculas)."""
    salida = []
    por_clave = {}
    for t in terminos:
        termino = " ".join(str(t.get("termino", "")).split())
        k = clave(termino)
        if not k:
            continue
        sinonimos = []
        for s in t.get("sinonimos", []) or []:
            s = " ".join(str(s).split())
            if s and clave(s) != k and clave(s) not in [clave(x) for x in sinonimos]:
                sinonimos.append(s)
        if k in por_clave:
            previo = por_clave[k]
            for s in sinonimos:
                if clave(s) not in [clave(x) for x in previo["sinonimos"]]:
                    previo["sinonimos"].append(s)
            continue
        entrada = _entrada(termino, sinonimos, t.get("activo", True))
        por_clave[k] = entrada
        salida.append(entrada)
    return salida


def cargar(ruta):
    if not os.path.exists(ruta):
        return []
    with open(ruta, encoding="utf-8") as f:
        datos = json.load(f)
    return limpiar(datos.get("terminos", []))


def guardar(ruta, terminos):
    """Guarda de forma atómica (no deja el archivo a medias si Anki se cierra)."""
    terminos = limpiar(terminos)
    temporal = ruta + ".tmp"
    with open(temporal, "w", encoding="utf-8") as f:
        json.dump({"version": VERSION, "terminos": terminos}, f, ensure_ascii=False, indent=1)
    os.replace(temporal, ruta)
    return terminos


def anadir(terminos, nuevos):
    """Añade términos nuevos (lista de str) que no existan ya. Devuelve cuántos."""
    existentes = {clave(t["termino"]) for t in terminos}
    for t in terminos:
        existentes.update(clave(s) for s in t["sinonimos"])
    n = 0
    for nuevo in nuevos:
        k = clave(nuevo)
        if k and k not in existentes:
            terminos.append(_entrada(" ".join(nuevo.split())))
            existentes.add(k)
            n += 1
    return n


def nombre_archivo(termino):
    """Nombre de archivo seguro y estable para el JSON de un término.

    Solo a-z, 0-9 y guiones (válido en Windows, macOS, Android e iOS, y sin
    problemas de mayúsculas), con un hash corto para evitar colisiones:
        "Nervio ciático" -> "_fuentes_t_nervio-ciatico_3f2a9c1b.json"
    """
    k = clave(termino)
    legible = re.sub(r"[^a-z0-9]+", "-", k.replace("ñ", "n")).strip("-")[:40].strip("-")
    resumen = hashlib.sha1(k.encode("utf-8")).hexdigest()[:8]
    return "_fuentes_t_%s_%s.json" % (legible or "t", resumen)


def leer_archivo(ruta):
    """Lee un glosario para importarlo. Formatos admitidos:

    * .json: el formato del add-on, o una lista de cadenas;
    * .txt / .csv / .tsv: una línea por término; los sinónimos van detrás
      separados por ";" (o tabulador). Las líneas que empiezan por # se ignoran.
    """
    with open(ruta, encoding="utf-8-sig") as f:
        contenido = f.read()
    if ruta.lower().endswith(".json"):
        datos = json.loads(contenido)
        if isinstance(datos, dict):
            datos = datos.get("terminos", [])
        salida = []
        for d in datos:
            if isinstance(d, str):
                salida.append(_entrada(d))
            elif isinstance(d, dict):
                salida.append(_entrada(d.get("termino", ""), d.get("sinonimos", []), d.get("activo", True)))
        return limpiar(salida)
    salida = []
    for linea in contenido.splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        partes = [p.strip() for p in re.split(r"[;\t]", linea)]
        salida.append(_entrada(partes[0], [p for p in partes[1:] if p]))
    return limpiar(salida)


def fusionar(terminos, nuevos):
    """Añade `nuevos` (entradas completas) a `terminos`, fusionando sinónimos. Devuelve cuántos son nuevos."""
    antes = len(limpiar(terminos))
    resultado = limpiar(list(terminos) + list(nuevos))
    terminos[:] = resultado
    return len(resultado) - antes
