# -*- coding: utf-8 -*-
"""Botón «Explicar»: Claude explica un término a partir de TUS fuentes.

Es la única parte de Pagewise que se conecta a internet, y solo cuando el
usuario pulsa «Explicar». Se envían a la API de Anthropic (api.anthropic.com):
el término, el texto de la tarjeta y los fragmentos de tus fuentes que hablan
de él (con el nombre de la fuente y la página). Nada más.

Usa la clave de API del propio usuario (la paga él) y no depende de Anki, así
que se prueba con pytest.

¿Por qué HTTP directo y no el SDK oficial `anthropic`? El add-on es un único
.ankiaddon para Windows, macOS y Linux, y el SDK necesita librerías compiladas
(pydantic-core, jiter) que habría que empaquetar para cada sistema. La
petición es una sola y sin streaming, así que urllib basta.
"""
import json
import socket
import urllib.error
import urllib.request

URL_API = "https://api.anthropic.com/v1/messages"
URL_MODELOS = "https://api.anthropic.com/v1/models?limit=1"
VERSION_API = "2026-10-21"
# Si el modelo declina responder por seguridad, la API reintenta en otro
# modelo dentro de la misma llamada (fallbacks "default").
BETA_FALLBACK = "server-side-fallback-2026-07-01"

MODELO = "claude-opus-5-5"
ESFUERZO = "low"           # explicación breve durante el repaso: prima la rapidez
MAX_TOKENS = 16000
TIEMPO_MAX = 120           # segundos
MAX_FRAGMENTOS = 12
MAX_TEXTO_TARJETA = 1500

_SISTEMA = {
    "es": (
        "Ayudas a un estudiante que repasa tarjetas de Anki. Explica el término que te pide "
        "basándote en los fragmentos de SUS fuentes (sus libros y apuntes) que van en el mensaje.\n"
        "- Apóyate en los fragmentos y cita de dónde sale cada idea así: (Fuente, p. N).\n"
        "- Si los fragmentos no bastan, dilo en una frase y completa con conocimiento general, "
        "dejando claro qué parte no viene de sus fuentes.\n"
        "- Si los fragmentos dicen algo distinto de lo que sabes, señálalo sin corregirlos por tu cuenta.\n"
        "- Ten en cuenta el texto de la tarjeta para enfocar la explicación en lo que está estudiando.\n"
        "- Entre 80 y 180 palabras, en español, en párrafos cortos de texto plano: sin títulos, "
        "sin listas largas y sin formato Markdown."
    ),
    "en": (
        "You help a student who is reviewing Anki flashcards. Explain the term they ask about "
        "based on the excerpts from THEIR sources (their books and notes) included in the message.\n"
        "- Rely on the excerpts and cite where each idea comes from like this: (Source, p. N).\n"
        "- If the excerpts are not enough, say so in one sentence and fill in with general "
        "knowledge, making clear which part does not come from their sources.\n"
        "- If the excerpts say something different from what you know, point it out without "
        "correcting them on your own.\n"
        "- Use the card text to focus the explanation on what they are studying.\n"
        "- Between 80 and 180 words, in English, in short plain-text paragraphs: no headings, "
        "no long lists and no Markdown formatting."
    ),
}

_MENSAJES = {
    "es": {
        "clave": "La clave de API no es válida. Revísala en Herramientas → Pagewise → Ajustes.",
        "permiso": "Esta clave de API no tiene permiso para usar el modelo.",
        "saldo": "La API de Anthropic ha rechazado la petición: %s",
        "limite": "Demasiadas peticiones seguidas. Espera un momento y vuelve a probar.",
        "saturado": "Claude está saturado ahora mismo. Vuelve a probar en un momento.",
        "red": "No se ha podido conectar con la API de Anthropic. ¿Hay conexión a internet?",
        "tiempo": "Claude ha tardado demasiado en responder. Vuelve a probar.",
        "error": "Error de la API de Anthropic (%s): %s",
        "rechazo": "Claude no ha querido responder a esta petición.",
        "vacio": "Claude no ha devuelto ninguna explicación.",
        "sin_fragmentos": "(No hay fragmentos de tus fuentes sobre este término.)",
        "tarjeta": "Texto de la tarjeta",
        "fragmentos": "Fragmentos de mis fuentes",
        "pide": "Explícame «%s».",
    },
    "en": {
        "clave": "The API key is not valid. Check it in Tools → Pagewise → Settings.",
        "permiso": "This API key is not allowed to use the model.",
        "saldo": "The Anthropic API rejected the request: %s",
        "limite": "Too many requests in a row. Wait a moment and try again.",
        "saturado": "Claude is overloaded right now. Try again in a moment.",
        "red": "Could not connect to the Anthropic API. Are you online?",
        "tiempo": "Claude took too long to answer. Try again.",
        "error": "Anthropic API error (%s): %s",
        "rechazo": "Claude declined to answer this request.",
        "vacio": "Claude returned no explanation.",
        "sin_fragmentos": "(There are no excerpts from your sources about this term.)",
        "tarjeta": "Card text",
        "fragmentos": "Excerpts from my sources",
        "pide": "Explain \"%s\" to me.",
    },
}


class ErrorExplicar(Exception):
    """Error que se puede enseñar tal cual al usuario."""


def _m(idioma, clave):
    return _MENSAJES.get(idioma, _MENSAJES["en"])[clave]


def mensaje_usuario(termino, fuentes, texto_tarjeta="", idioma="es"):
    """Texto del mensaje: término, tarjeta y fragmentos numerados con su fuente y página.

    `fuentes` tiene el formato de ProveedorFTS.fragmentos():
    [{"nombre": "Libro", "fragmentos": [{"p": 12, "e": "xii", "x": "texto"}]}]
    """
    partes = [_m(idioma, "pide") % termino]
    tarjeta = " ".join(str(texto_tarjeta or "").split())[:MAX_TEXTO_TARJETA]
    if tarjeta:
        partes.append("<%s>\n%s\n</%s>" % ("tarjeta" if idioma == "es" else "card", tarjeta,
                                          "tarjeta" if idioma == "es" else "card"))
    lineas = []
    n = 0
    for f in fuentes or []:
        for fr in f.get("fragmentos", []):
            if n >= MAX_FRAGMENTOS:
                break
            n += 1
            pagina = fr.get("e") or fr.get("p")
            lineas.append("[%d] (%s, p. %s) %s" % (n, f.get("nombre", "?"), pagina, fr.get("x", "")))
    cuerpo = "\n\n".join(lineas) if lineas else _m(idioma, "sin_fragmentos")
    etiqueta = "fragmentos" if idioma == "es" else "excerpts"
    partes.append("<%s>\n%s\n</%s>" % (etiqueta, cuerpo, etiqueta))
    return "\n\n".join(partes)


def peticion(termino, fuentes, texto_tarjeta="", idioma="es", modelo=None, esfuerzo=None):
    """Cuerpo JSON de la petición a la API de Mensajes."""
    return {
        "model": modelo or MODELO,
        "max_tokens": MAX_TOKENS,
        "output_config": {"effort": esfuerzo or ESFUERZO},
        "fallbacks": "default",
        "system": _SISTEMA.get(idioma, _SISTEMA["en"]),
        "messages": [{"role": "user", "content": mensaje_usuario(termino, fuentes, texto_tarjeta, idioma)}],
    }


def _cabeceras(clave_api):
    return {
        "content-type": "application/json",
        "x-api-key": clave_api,
        "anthropic-version": VERSION_API,
        "anthropic-beta": BETA_FALLBACK,
    }


def _error_http(e, idioma):
    """Traduce un error HTTP de la API a un mensaje para el usuario."""
    try:
        detalle = json.loads(e.read().decode("utf-8")).get("error", {}).get("message", "")
    except Exception:
        detalle = ""
    codigo = e.code
    if codigo == 401:
        return ErrorExplicar(_m(idioma, "clave"))
    if codigo == 403:
        return ErrorExplicar(_m(idioma, "permiso"))
    if codigo == 400 and "credit" in detalle.lower():
        return ErrorExplicar(_m(idioma, "saldo") % detalle)
    if codigo == 429:
        return ErrorExplicar(_m(idioma, "limite"))
    if codigo in (500, 502, 503, 504, 529):
        return ErrorExplicar(_m(idioma, "saturado"))
    return ErrorExplicar(_m(idioma, "error") % (codigo, detalle or e.reason))


def _enviar(req, idioma, abrir):
    try:
        with abrir(req, timeout=TIEMPO_MAX) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise _error_http(e, idioma)
    except (socket.timeout, TimeoutError):
        raise ErrorExplicar(_m(idioma, "tiempo"))
    except urllib.error.URLError as e:
        if isinstance(getattr(e, "reason", None), (socket.timeout, TimeoutError)):
            raise ErrorExplicar(_m(idioma, "tiempo"))
        raise ErrorExplicar(_m(idioma, "red"))


def texto_respuesta(respuesta, idioma="es"):
    """Texto de la explicación a partir de la respuesta JSON de la API."""
    if respuesta.get("stop_reason") == "refusal":
        raise ErrorExplicar(_m(idioma, "rechazo"))
    # El contenido puede traer bloques "thinking" (vacíos) y "fallback": solo
    # nos interesan los de texto.
    texto = "".join(b.get("text", "") for b in respuesta.get("content", []) if b.get("type") == "text").strip()
    if not texto:
        raise ErrorExplicar(_m(idioma, "vacio"))
    return texto


def explicar(clave_api, termino, fuentes, texto_tarjeta="", idioma="es", modelo=None, esfuerzo=None,
             abrir=urllib.request.urlopen):
    """Pide la explicación a Claude. Devuelve el texto o lanza ErrorExplicar.

    Bloquea mientras espera: llámalo en segundo plano.
    """
    cuerpo = json.dumps(peticion(termino, fuentes, texto_tarjeta, idioma, modelo, esfuerzo)).encode("utf-8")
    req = urllib.request.Request(URL_API, data=cuerpo, headers=_cabeceras(clave_api), method="POST")
    return texto_respuesta(_enviar(req, idioma, abrir), idioma)


def comprobar_clave(clave_api, idioma="es", abrir=urllib.request.urlopen):
    """Comprueba la clave listando los modelos (no gasta tokens). Lanza ErrorExplicar."""
    cab = _cabeceras(clave_api)
    cab.pop("content-type")
    cab.pop("anthropic-beta")
    _enviar(urllib.request.Request(URL_MODELOS, headers=cab, method="GET"), idioma, abrir)
    return True
