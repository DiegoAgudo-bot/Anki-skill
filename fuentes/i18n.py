# -*- coding: utf-8 -*-
"""Traducción de la interfaz (español / inglés). Sin dependencias de Anki.

Los textos se escriben en español en el código, envueltos en tr("…").
Si Anki está en español se muestran tal cual; en cualquier otro idioma se
muestra la traducción inglesa de i18n_en.py. Un test comprueba que todos
los textos tienen traducción.

    tr("Hola %s") % nombre      # el formato se aplica DESPUÉS de traducir
"""
from .i18n_en import EN

_idioma = "es"


def fijar_idioma(codigo):
    """codigo: el idioma de Anki ('es', 'es-ES', 'en', 'de'…)."""
    global _idioma
    _idioma = "es" if str(codigo or "").lower().startswith("es") else "en"


def idioma():
    return _idioma


def tr(texto):
    if _idioma == "es":
        return texto
    return EN.get(texto, texto)
