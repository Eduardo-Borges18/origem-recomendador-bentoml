"""Mockup determinístico do módulo de recomendação do Origem."""

import json
import logging
import re
import time
from pathlib import Path
from uuid import UUID

import bentoml
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

CATALOGO = json.loads(Path(__file__).with_name("catalogo.json").read_text(encoding="utf-8"))
CAMPOS_PUBLICOS = ("id", "nome", "preco", "categoria", "imagemPrincipal", "notaMedia")
logger = logging.getLogger("origem.recomendacoes")
logger.setLevel(logging.INFO)
app = FastAPI(title="Origem — Recomendador", version="1.0.0")


def registrar(estrategia: str, quantidade: int, inicio: float, status: int) -> None:
    """Registra apenas dados operacionais, sem IDs ou dados pessoais."""
    logger.info(
        "estrategia=%s quantidade=%d duracao_ms=%.2f status=%d",
        estrategia, quantidade, (time.perf_counter() - inicio) * 1000, status,
    )


def erro(codigo: str, mensagem: str, inicio: float) -> JSONResponse:
    registrar("erro_validacao", 0, inicio, 400)
    return JSONResponse(
        status_code=400,
        content={"error": {"code": codigo, "message": mensagem, "details": {}}},
    )


def uuid_valido(valor: str) -> str | None:
    try:
        return str(UUID(valor))
    except (ValueError, AttributeError, TypeError):
        return None


def elegiveis(excluir_id: str | None) -> list[dict]:
    vistos = set()
    resultado = []
    for produto in CATALOGO:
        identificador = produto["id"]
        if (
            produto["ativo"] and produto["estoque"] > 0
            and identificador != excluir_id and identificador not in vistos
        ):
            vistos.add(identificador)
            resultado.append(produto)
    return resultado


def publico(produto: dict) -> dict:
    return {campo: produto[campo] for campo in CAMPOS_PUBLICOS}


@app.get("/recomendacoes")
def recomendacoes(request: Request):
    inicio = time.perf_counter()
    parametros = request.query_params
    produtos = parametros.getlist("produtoId")
    usuarios = parametros.getlist("usuarioId")
    if len(produtos) + len(usuarios) != 1:
        return erro("CONTEXTO_INVALIDO", "Informe exatamente um contexto de recomendação.", inicio)

    contexto = produtos[0] if produtos else usuarios[0]
    contexto_id = uuid_valido(contexto)
    if contexto_id is None:
        return erro("CONTEXTO_INVALIDO", "O contexto deve ser um UUID válido.", inicio)

    limites = parametros.getlist("limite")
    if len(limites) > 1 or (limites and not re.fullmatch(r"[0-9]+", limites[0])):
        return erro("LIMITE_INVALIDO", "O limite deve ser inteiro entre 1 e 8.", inicio)
    try:
        limite = int(limites[0]) if limites else 8
    except ValueError:
        return erro("LIMITE_INVALIDO", "O limite deve ser inteiro entre 1 e 8.", inicio)
    if not 1 <= limite <= 8:
        return erro("LIMITE_INVALIDO", "O limite deve ser inteiro entre 1 e 8.", inicio)

    produto_id = contexto_id if produtos else None
    candidatos = elegiveis(produto_id)
    referencia = next((p for p in CATALOGO if p["id"] == produto_id), None)
    relacionados = (
        [p for p in candidatos if p["categoria"] == referencia["categoria"]]
        if referencia is not None else []
    )

    if relacionados:
        estrategia = "categoria_regiao_vendas_avaliacao_v1"
        ordenados = sorted(
            relacionados,
            key=lambda p: (p["regiao"] != referencia["regiao"], -p["vendas"], -p["notaMedia"], p["id"]),
        )
    elif candidatos:
        estrategia = "popularidade_geral_v1"
        ordenados = sorted(candidatos, key=lambda p: (-p["vendas"], -p["notaMedia"], p["id"]))
    else:
        estrategia = "sem_resultados"
        ordenados = []

    itens = [publico(p) for p in ordenados[:limite]]
    registrar(estrategia, len(itens), inicio, 200)
    return {"estrategia": estrategia, "itens": itens}


@bentoml.service
@bentoml.asgi_app(app, path="/")
class RecomendadorOrigem:
    """Hospeda o contrato GET do Origem via BentoML."""
    pass
