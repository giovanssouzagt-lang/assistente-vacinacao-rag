"""
ETAPA 5 — API (FastAPI)
=======================
Expõe o assistente como um serviço web, para que qualquer sistema
(um app, um site, um chatbot de WhatsApp) possa fazer perguntas a ele.

Rotas:
    GET  /            -> tela de chat (static/index.html)
    GET  /saude       -> verifica se a API e o Ollama estão funcionando
    POST /perguntar   -> recebe {"pergunta": "..."} e devolve a resposta com as fontes
    GET  /docs        -> documentação interativa gerada automaticamente pelo FastAPI

Rode com:  uvicorn api:app --reload
Depois abra:  http://localhost:8000
"""
import re
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import config
from resposta import SEM_RESPOSTA, Assistente

PASTA_STATIC = Path(__file__).parent / "static"
assistente: Assistente | None = None

# Marcadores de lista do PDF vêm como caracteres de controle invisíveis
# (ex.: \x83), que aparecem como quadradinhos na tela.
MARCADORES_PDF = re.compile(r"[\x80-\x9f\ue000-\uf8ff]")


def texto_para_exibir(trecho: str) -> str:
    """
    Troca os marcadores do PDF por "•", APENAS para exibição.

    A limpeza não é feita na ingestão de propósito: testei, e trocar esse
    caractere no texto indexado virou duas respostas de "certas" para
    "erradas" na avaliação. O modelo de 8b é sensível a pequenas mudanças
    no contexto, então uma melhoria só visual não pode mexer no que a IA lê.
    """
    return MARCADORES_PDF.sub("•", trecho)


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    # Carrega o banco vetorial e o modelo UMA vez, quando a API sobe,
    # e não a cada pergunta (seria lento).
    global assistente
    assistente = Assistente()
    yield


app = FastAPI(
    title="Assistente de Vacinação (RAG)",
    description="Responde perguntas com base no Manual de Normas e Procedimentos "
                "para Vacinação (Ministério da Saúde, 2024), citando as páginas.",
    version="1.0.0",
    lifespan=ciclo_de_vida,
)


# ---------- Formatos de entrada e saída (validados automaticamente) ----------

class Pergunta(BaseModel):
    pergunta: str = Field(
        min_length=3, max_length=500,
        examples=["Recém-nascido com menos de 2 kg pode tomar BCG?"],
    )


class Fonte(BaseModel):
    pagina: int
    secao: str | None
    trecho: str


class RespostaAPI(BaseModel):
    resposta: str
    encontrou: bool  # False quando o assistente não achou a resposta no manual
    fontes: list[Fonte]


# ---------- Rotas ----------

@app.get("/", include_in_schema=False)
def tela_de_chat():
    return FileResponse(PASTA_STATIC / "index.html")


@app.get("/saude")
def saude():
    """Confere se o Ollama está no ar e se os modelos necessários estão baixados."""
    try:
        modelos = httpx.get("http://localhost:11434/api/tags", timeout=3).json()["models"]
    except httpx.HTTPError:
        raise HTTPException(503, "Ollama não está rodando.")
    nomes = {m["name"] for m in modelos}
    faltando = [m for m in (config.MODELO_LLM, f"{config.MODELO_EMBEDDING}:latest") if m not in nomes]
    if faltando:
        raise HTTPException(503, f"Modelos não encontrados no Ollama: {faltando}")
    return {"status": "ok", "modelo": config.MODELO_LLM, "embedding": config.MODELO_EMBEDDING}


@app.post("/perguntar", response_model=RespostaAPI)
def perguntar(entrada: Pergunta):
    # Função síncrona de propósito: o FastAPI a roda em uma thread separada,
    # então uma pergunta demorada não trava as outras requisições.
    try:
        r = assistente.perguntar(entrada.pergunta.strip())
    except (httpx.HTTPError, ConnectionError):
        raise HTTPException(503, "Não foi possível falar com o Ollama. Ele está rodando?")

    encontrou = SEM_RESPOSTA.lower() not in r.texto.lower()
    return RespostaAPI(
        resposta=r.texto,
        encontrou=encontrou,
        # Sem resposta, não faz sentido mostrar "fontes"
        fontes=[
            Fonte(
                pagina=d.metadata["pagina"],
                secao=d.metadata.get("secao"),
                trecho=texto_para_exibir(d.page_content),
            )
            for d in r.trechos
        ] if encontrou else [],
    )
