# -*- coding: utf-8 -*-
"""Botón «Explicar»: una IA explica un término a partir de TUS fuentes.

Dos proveedores, a elegir en Ajustes, cada uno con la clave del usuario:
  * "anthropic": Claude, por la API de Mensajes (api.anthropic.com).
  * "openai": ChatGPT, por la API de Chat Completions (api.openai.com).

Es la única parte de Pagewise que se conecta a internet, y solo cuando el
usuario pulsa «Explicar». Se envían al proveedor elegido: el término, el texto
de la tarjeta y los fragmentos de tus fuentes que hablan de él (con el nombre
de la fuente y la página). Nada más.

No depende de Anki, así que se prueba con pytest.

¿Por qué HTTP directo y no los SDK oficiales (`anthropic`, `openai`)? El
add-on es un único .ankiaddon para Windows, macOS y Linux, y esos SDK
necesitan librerías compiladas (pydantic-core, jiter) que habría que
empaquetar para cada sistema. La petición es una sola y sin streaming, así
que urllib basta.
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

# OpenAI (ChatGPT). Modelo y esfuerzo se cambian en la configuración.
URL_OPENAI = "https://api.openai.com/v1/chat/completions"
URL_MODELOS_OPENAI = "https://api.openai.com/v1/models"
MODELO_OPENAI = "gpt-5"
ESFUERZO_OPENAI = "low"    # reasoning_effort; vacío = no se envía (modelos sin razonamiento)

PROVEEDORES = {
    "anthropic": {"nombre": "Claude", "empresa": "Anthropic"},
    "openai": {"nombre": "ChatGPT", "empresa": "OpenAI"},
}


def nombre(proveedor):
    return PROVEEDORES.get(proveedor, PROVEEDORES["anthropic"])["nombre"]
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
        "saldo": "La API de {empresa} ha rechazado la petición: %s",
        "cuota": "Tu cuenta de {empresa} no tiene saldo o ha superado su cuota. Revísala en su web.",
        "limite": "Demasiadas peticiones seguidas. Espera un momento y vuelve a probar.",
        "saturado": "{nombre} está saturado ahora mismo. Vuelve a probar en un momento.",
        "red": "No se ha podido conectar con la API de {empresa}. ¿Hay conexión a internet?",
        "tiempo": "{nombre} ha tardado demasiado en responder. Vuelve a probar.",
        "error": "Error de la API de {empresa} (%s): %s",
        "rechazo": "{nombre} no ha querido responder a esta petición.",
        "vacio": "{nombre} no ha devuelto ninguna explicación.",
        "sin_fragmentos": "(No hay fragmentos de tus fuentes sobre este término.)",
        "tarjeta": "Texto de la tarjeta",
        "fragmentos": "Fragmentos de mis fuentes",
        "pide": "Explícame «%s».",
    },
    "en": {
        "clave": "The API key is not valid. Check it in Tools → Pagewise → Settings.",
        "permiso": "This API key is not allowed to use the model.",
        "saldo": "The {empresa} API rejected the request: %s",
        "cuota": "Your {empresa} account has no credit or has exceeded its quota. Check it on their website.",
        "limite": "Too many requests in a row. Wait a moment and try again.",
        "saturado": "{nombre} is overloaded right now. Try again in a moment.",
        "red": "Could not connect to the {empresa} API. Are you online?",
        "tiempo": "{nombre} took too long to answer. Try again.",
        "error": "{empresa} API error (%s): %s",
        "rechazo": "{nombre} declined to answer this request.",
        "vacio": "{nombre} returned no explanation.",
        "sin_fragmentos": "(There are no excerpts from your sources about this term.)",
        "tarjeta": "Card text",
        "fragmentos": "Excerpts from my sources",
        "pide": "Explain \"%s\" to me.",
    },
}


class ErrorExplicar(Exception):
    """Error que se puede enseñar tal cual al usuario."""


def _m(idioma, clave, proveedor="anthropic"):
    datos = PROVEEDORES.get(proveedor, PROVEEDORES["anthropic"])
    return _MENSAJES.get(idioma, _MENSAJES["en"])[clave].replace(
        "{nombre}", datos["nombre"]).replace("{empresa}", datos["empresa"])


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


def peticion_openai(termino, fuentes, texto_tarjeta="", idioma="es", modelo=None, esfuerzo=None):
    """Cuerpo JSON de la petición a Chat Completions de OpenAI."""
    cuerpo = {
        "model": modelo or MODELO_OPENAI,
        "max_completion_tokens": MAX_TOKENS,
        "messages": [
            {"role": "system", "content": _SISTEMA.get(idioma, _SISTEMA["en"])},
            {"role": "user", "content": mensaje_usuario(termino, fuentes, texto_tarjeta, idioma)},
        ],
    }
    esfuerzo = ESFUERZO_OPENAI if esfuerzo is None else esfuerzo
    if esfuerzo:
        cuerpo["reasoning_effort"] = esfuerzo
    return cuerpo


def _cabeceras(clave_api, proveedor="anthropic"):
    if proveedor == "openai":
        return {"content-type": "application/json", "authorization": "Bearer " + clave_api}
    return {
        "content-type": "application/json",
        "x-api-key": clave_api,
        "anthropic-version": VERSION_API,
        "anthropic-beta": BETA_FALLBACK,
    }


class _ErrorHTTP(ErrorExplicar):
    def __init__(self, mensaje, codigo, detalle):
        ErrorExplicar.__init__(self, mensaje)
        self.codigo = codigo
        self.detalle = detalle


def _error_http(e, idioma, proveedor="anthropic"):
    """Traduce un error HTTP de la API a un mensaje para el usuario."""
    try:
        error = json.loads(e.read().decode("utf-8")).get("error", {}) or {}
    except Exception:
        error = {}
    detalle = str(error.get("message", "") or "")
    tipo = str(error.get("code", "") or error.get("type", "") or "")
    codigo = e.code

    def err(clave, *args):
        texto = _m(idioma, clave, proveedor)
        return _ErrorHTTP(texto % args if args else texto, codigo, detalle)

    if codigo == 401:
        return err("clave")
    if codigo == 403:
        return err("permiso")
    if codigo == 400 and "credit" in detalle.lower():
        return err("saldo", detalle)
    if codigo == 429 and ("quota" in tipo or "billing" in tipo or "quota" in detalle.lower()):
        return err("cuota")           # OpenAI: sin saldo también es un 429
    if codigo == 429:
        return err("limite")
    if codigo in (500, 502, 503, 504, 529):
        return err("saturado")
    return err("error", codigo, detalle or e.reason)


def _enviar(req, idioma, abrir, proveedor="anthropic"):
    try:
        with abrir(req, timeout=TIEMPO_MAX) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise _error_http(e, idioma, proveedor)
    except (socket.timeout, TimeoutError):
        raise ErrorExplicar(_m(idioma, "tiempo", proveedor))
    except urllib.error.URLError as e:
        if isinstance(getattr(e, "reason", None), (socket.timeout, TimeoutError)):
            raise ErrorExplicar(_m(idioma, "tiempo", proveedor))
        raise ErrorExplicar(_m(idioma, "red", proveedor))


def texto_respuesta(respuesta, idioma="es"):
    """Texto de la explicación a partir de la respuesta JSON de la API de Claude."""
    if respuesta.get("stop_reason") == "refusal":
        raise ErrorExplicar(_m(idioma, "rechazo"))
    # El contenido puede traer bloques "thinking" (vacíos) y "fallback": solo
    # nos interesan los de texto.
    texto = "".join(b.get("text", "") for b in respuesta.get("content", []) if b.get("type") == "text").strip()
    if not texto:
        raise ErrorExplicar(_m(idioma, "vacio"))
    return texto


def texto_respuesta_openai(respuesta, idioma="es"):
    """Texto de la explicación a partir de la respuesta JSON de Chat Completions."""
    opciones = respuesta.get("choices") or []
    if not opciones:
        raise ErrorExplicar(_m(idioma, "vacio", "openai"))
    mensaje = opciones[0].get("message") or {}
    if mensaje.get("refusal") or opciones[0].get("finish_reason") == "content_filter":
        raise ErrorExplicar(_m(idioma, "rechazo", "openai"))
    contenido = mensaje.get("content") or ""
    if isinstance(contenido, list):  # por si llega en partes
        contenido = "".join(p.get("text", "") for p in contenido if isinstance(p, dict))
    texto = str(contenido).strip()
    if not texto:
        raise ErrorExplicar(_m(idioma, "vacio", "openai"))
    return texto


def explicar(clave_api, termino, fuentes, texto_tarjeta="", idioma="es", modelo=None, esfuerzo=None,
             abrir=urllib.request.urlopen, proveedor="anthropic"):
    """Pide la explicación al proveedor elegido. Devuelve el texto o lanza ErrorExplicar.

    Bloquea mientras espera: llámalo en segundo plano.
    """
    if proveedor == "openai":
        cuerpo = peticion_openai(termino, fuentes, texto_tarjeta, idioma, modelo, esfuerzo)

        def enviar(c):
            req = urllib.request.Request(URL_OPENAI, data=json.dumps(c).encode("utf-8"),
                                         headers=_cabeceras(clave_api, "openai"), method="POST")
            return _enviar(req, idioma, abrir, "openai")

        try:
            respuesta = enviar(cuerpo)
        except _ErrorHTTP as e:
            # Modelos sin razonamiento (p. ej. si se cambia a uno antiguo) no
            # aceptan reasoning_effort: se reintenta una vez sin él.
            if e.codigo != 400 or "reasoning_effort" not in cuerpo or "reasoning" not in e.detalle.lower():
                raise
            cuerpo.pop("reasoning_effort")
            respuesta = enviar(cuerpo)
        return texto_respuesta_openai(respuesta, idioma)

    cuerpo = json.dumps(peticion(termino, fuentes, texto_tarjeta, idioma, modelo, esfuerzo)).encode("utf-8")
    req = urllib.request.Request(URL_API, data=cuerpo, headers=_cabeceras(clave_api), method="POST")
    return texto_respuesta(_enviar(req, idioma, abrir), idioma)


def comprobar_clave(clave_api, idioma="es", abrir=urllib.request.urlopen, proveedor="anthropic"):
    """Comprueba la clave listando los modelos (no gasta tokens). Lanza ErrorExplicar."""
    cab = _cabeceras(clave_api, proveedor)
    cab.pop("content-type")
    cab.pop("anthropic-beta", None)
    url = URL_MODELOS_OPENAI if proveedor == "openai" else URL_MODELOS
    _enviar(urllib.request.Request(url, headers=cab, method="GET"), idioma, abrir, proveedor)
    return True
