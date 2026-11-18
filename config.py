"""
Configurações centrais do projeto.

Tudo que pode mudar (modelo, pasta, tamanho do chunk) fica aqui,
em um só lugar. Os valores podem ser sobrescritos por um arquivo .env.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

RAIZ = Path(__file__).parent

# Onde ficam os PDFs que o assistente vai "ler"
PASTA_DOCUMENTOS = RAIZ / "documentos"

# Onde o banco vetorial (Chroma) é salvo no disco
PASTA_BANCO = RAIZ / "banco_vetorial"
NOME_COLECAO = "manual_vacinacao"

# Modelo que transforma texto em vetores (embeddings), rodando no Ollama
MODELO_EMBEDDING = os.getenv("MODELO_EMBEDDING", "bge-m3")

# Modelo que gera as respostas (usado na etapa 4)
MODELO_LLM = os.getenv("MODELO_LLM", "qwen3:8b")

# Chunking: tamanho de cada pedaço (em caracteres) e quanto um pedaço
# "repete" do anterior, para não cortar uma ideia no meio
TAMANHO_CHUNK = int(os.getenv("TAMANHO_CHUNK", "1000"))
SOBREPOSICAO_CHUNK = int(os.getenv("SOBREPOSICAO_CHUNK", "200"))
