# -*- coding: utf-8 -*-
"""Botón «Explicar»: petición a la API de Claude y lectura de la respuesta (sin red)."""
import io
import json
import socket
import urllib.error

import pytest

from pagewise import explicar

FUENTES = [{"id": 1, "nombre": "Anatomía", "fragmentos": [
    {"p": 12, "x": "La arteria femoral continúa a la ilíaca externa."},
    {"p": 30, "e": "xxx", "x": "Se palpa en el triángulo femoral."},
]}]


class Respuesta(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def abrir_que_responde(cuerpo, enviadas):
    def abrir(req, timeout=None):
        enviadas.append(req)
        return Respuesta(json.dumps(cuerpo).encode("utf-8"))
    return abrir


def abrir_que_falla(codigo, mensaje=""):
    def abrir(req, timeout=None):
        cuerpo = io.BytesIO(json.dumps({"error": {"message": mensaje}}).encode("utf-8"))
        raise urllib.error.HTTPError(req.full_url, codigo, "x", {}, cuerpo)
    return abrir


def test_mensaje_con_tarjeta_y_fragmentos_citables():
    m = explicar.mensaje_usuario("arteria femoral", FUENTES, "¿Dónde se palpa  la\n arteria?", "es")
    assert "Explícame «arteria femoral»." in m
    assert "¿Dónde se palpa la arteria?" in m
    assert "[1] (Anatomía, p. 12) La arteria femoral" in m
    assert "[2] (Anatomía, p. xxx)" in m          # número de página impreso si lo hay


def test_mensaje_sin_fragmentos_lo_dice():
    assert "No hay fragmentos" in explicar.mensaje_usuario("aorta", [], "", "es")
    assert "no excerpts" in explicar.mensaje_usuario("aorta", [], "", "en")


def test_peticion_y_cabeceras():
    enviadas = []
    texto = explicar.explicar("sk-prueba", "arteria femoral", FUENTES, "tarjeta", "es",
                              abrir=abrir_que_responde({
                                  "stop_reason": "end_turn",
                                  "content": [{"type": "thinking", "thinking": ""},
                                              {"type": "text", "text": "La arteria femoral (Anatomía, p. 12)…"}]},
                                  enviadas))
    assert texto == "La arteria femoral (Anatomía, p. 12)…"
    req = enviadas[0]
    assert req.full_url == explicar.URL_API and req.get_method() == "POST"
    cab = {k.lower(): v for k, v in req.header_items()}
    assert cab["x-api-key"] == "sk-prueba"
    assert cab["anthropic-version"] == "2026-10-21"
    assert cab["anthropic-beta"] == "server-side-fallback-2026-07-01"
    cuerpo = json.loads(req.data.decode("utf-8"))
    assert cuerpo["model"] == "claude-opus-5-5"
    assert cuerpo["output_config"] == {"effort": "low"}
    assert cuerpo["fallbacks"] == "default"
    assert "thinking" not in cuerpo and "temperature" not in cuerpo
    assert cuerpo["messages"][0]["role"] == "user"


def test_modelo_y_esfuerzo_configurables():
    c = explicar.peticion("x", [], modelo="claude-sonnet-5-5", esfuerzo="medium")
    assert c["model"] == "claude-sonnet-5-5" and c["output_config"]["effort"] == "medium"


def test_ignora_bloques_de_fallback():
    r = {"stop_reason": "end_turn", "content": [
        {"type": "fallback", "from": {"model": "a"}, "to": {"model": "b"}},
        {"type": "text", "text": "Hola"}]}
    assert explicar.texto_respuesta(r) == "Hola"


def test_rechazo_y_respuesta_vacia():
    with pytest.raises(explicar.ErrorExplicar, match="no ha querido"):
        explicar.texto_respuesta({"stop_reason": "refusal", "content": []})
    with pytest.raises(explicar.ErrorExplicar, match="ninguna explicación"):
        explicar.texto_respuesta({"stop_reason": "end_turn", "content": []})


@pytest.mark.parametrize("codigo, mensaje, esperado", [
    (401, "invalid x-api-key", "clave de API no es válida"),
    (403, "", "no tiene permiso"),
    (400, "Your credit balance is too low", "credit balance"),
    (429, "", "Demasiadas peticiones"),
    (529, "", "saturado"),
    (404, "model not found", "404"),
])
def test_errores_http_con_mensajes_claros(codigo, mensaje, esperado):
    with pytest.raises(explicar.ErrorExplicar, match=esperado):
        explicar.explicar("k", "x", [], abrir=abrir_que_falla(codigo, mensaje))


def test_sin_red_y_tiempo_agotado():
    def sin_red(req, timeout=None):
        raise urllib.error.URLError("no route")

    def lento(req, timeout=None):
        raise socket.timeout()

    with pytest.raises(explicar.ErrorExplicar, match="conexión"):
        explicar.explicar("k", "x", [], abrir=sin_red)
    with pytest.raises(explicar.ErrorExplicar, match="tardado"):
        explicar.explicar("k", "x", [], abrir=lento)


def test_comprobar_clave_no_gasta_tokens():
    enviadas = []
    assert explicar.comprobar_clave("sk", abrir=abrir_que_responde({"data": []}, enviadas))
    req = enviadas[0]
    assert req.get_method() == "GET" and "/v1/models" in req.full_url and req.data is None


# ------------------------------------------------------------------ OpenAI

def _ok_openai(texto="Explicación (Anatomía, p. 12)."):
    return {"choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": texto, "refusal": None}}]}


def test_openai_peticion_y_cabeceras():
    enviadas = []
    texto = explicar.explicar("sk-openai", "arteria femoral", FUENTES, "tarjeta", "es",
                              abrir=abrir_que_responde(_ok_openai(), enviadas), proveedor="openai")
    assert texto == "Explicación (Anatomía, p. 12)."
    req = enviadas[0]
    assert req.full_url == "https://api.openai.com/v1/chat/completions" and req.get_method() == "POST"
    cab = {k.lower(): v for k, v in req.header_items()}
    assert cab["authorization"] == "Bearer sk-openai" and "x-api-key" not in cab
    cuerpo = json.loads(req.data.decode("utf-8"))
    assert cuerpo["model"] == "gpt-5" and cuerpo["reasoning_effort"] == "low"
    assert cuerpo["max_completion_tokens"] == explicar.MAX_TOKENS
    assert [m["role"] for m in cuerpo["messages"]] == ["system", "user"]
    assert "[1] (Anatomía, p. 12)" in cuerpo["messages"][1]["content"]


def test_openai_sin_reasoning_effort_si_se_deja_vacio():
    c = explicar.peticion_openai("x", [], modelo="gpt-4o", esfuerzo="")
    assert c["model"] == "gpt-4o" and "reasoning_effort" not in c


def test_openai_reintenta_sin_reasoning_effort_si_el_modelo_no_lo_admite():
    enviadas = []

    def abrir(req, timeout=None):
        enviadas.append(json.loads(req.data.decode("utf-8")))
        if len(enviadas) == 1:
            cuerpo = io.BytesIO(json.dumps({"error": {"message": "Unsupported parameter: 'reasoning_effort'",
                                                      "code": "unsupported_parameter"}}).encode("utf-8"))
            raise urllib.error.HTTPError(req.full_url, 400, "x", {}, cuerpo)
        return Respuesta(json.dumps(_ok_openai("Hola")).encode("utf-8"))

    assert explicar.explicar("k", "x", [], abrir=abrir, proveedor="openai", modelo="gpt-4o") == "Hola"
    assert "reasoning_effort" in enviadas[0] and "reasoning_effort" not in enviadas[1]


def test_openai_rechazo_y_vacio():
    with pytest.raises(explicar.ErrorExplicar, match="ChatGPT no ha querido"):
        explicar.texto_respuesta_openai({"choices": [{"message": {"content": None, "refusal": "No."}}]})
    with pytest.raises(explicar.ErrorExplicar, match="ChatGPT no ha devuelto"):
        explicar.texto_respuesta_openai({"choices": []})


@pytest.mark.parametrize("codigo, error, esperado", [
    (401, {"message": "Incorrect API key", "code": "invalid_api_key"}, "clave de API no es válida"),
    (429, {"message": "You exceeded your current quota", "code": "insufficient_quota"}, "OpenAI no tiene saldo"),
    (429, {"message": "Rate limit reached", "code": "rate_limit_exceeded"}, "Demasiadas peticiones"),
    (503, {"message": "overloaded"}, "ChatGPT está saturado"),
])
def test_openai_errores(codigo, error, esperado):
    def abrir(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, codigo, "x", {},
                                     io.BytesIO(json.dumps({"error": error}).encode("utf-8")))
    with pytest.raises(explicar.ErrorExplicar, match=esperado):
        explicar.explicar("k", "x", [], abrir=abrir, proveedor="openai")


def test_openai_comprobar_clave():
    enviadas = []
    explicar.comprobar_clave("sk-o", abrir=abrir_que_responde({"data": []}, enviadas), proveedor="openai")
    req = enviadas[0]
    assert req.full_url == "https://api.openai.com/v1/models" and req.get_method() == "GET"
    assert {k.lower(): v for k, v in req.header_items()}["authorization"] == "Bearer sk-o"
