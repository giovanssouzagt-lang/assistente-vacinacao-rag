"""
ETAPA 3 — BUSCA (o "R" de RAG: Retrieval)
=========================================
Três estratégias para encontrar os trechos do manual que respondem
a uma pergunta:

1. VETORIAL (semântica): compara o SIGNIFICADO da pergunta com o de cada
   chunk, usando embeddings. Entende sinônimos ("geladeira" ~ "câmara
   refrigerada"), mas pode se confundir com textos parecidos sobre outro
   assunto (ex.: temperatura da caixa térmica).

2. BM25 (palavra-chave): o algoritmo clássico dos buscadores. Dá pontos
   para chunks que contêm as palavras da pergunta, valorizando palavras
   raras ("BCG", "multidose") mais que palavras comuns. Ótimo para termos
   exatos, mas não entende sinônimos.

3. HÍBRIDA: roda as duas e junta os rankings com Reciprocal Rank Fusion
   (RRF). Cada chunk ganha 1/(60 + posição) em cada lista; quem aparece
   bem nas duas sobe. Pega o melhor dos dois mundos.
"""
import re
import unicodedata

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from rank_bm25 import BM25Okapi

import config

# Palavras muito comuns que não ajudam a diferenciar um chunk de outro
STOPWORDS = set("""
a o as os um uma uns umas de do da dos das em no na nos nas por para pra
com sem e ou que se ao aos à às é ser foi são pode posso devo deve qual
quais quem quando quanto quantos como onde até depois antes mais menos
muito já não sim eu ele ela isso este esta esse essa seu sua meu minha
""".split())


def tokenizar(texto: str) -> list[str]:
    """Minúsculas, sem acentos, sem pontuação e sem stopwords."""
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return [t for t in re.findall(r"\w+", texto) if t not in STOPWORDS]


class Buscador:
    def __init__(self):
        self.banco = Chroma(
            collection_name=config.NOME_COLECAO,
            embedding_function=OllamaEmbeddings(model=config.MODELO_EMBEDDING),
            persist_directory=str(config.PASTA_BANCO),
        )
        # O índice BM25 é montado a partir dos MESMOS chunks do Chroma,
        # assim as duas buscas olham exatamente para o mesmo conteúdo.
        dados = self.banco.get(include=["documents", "metadatas"])
        self.chunks = [
            Document(page_content=texto, metadata=meta)
            for texto, meta in zip(dados["documents"], dados["metadatas"])
        ]
        self.bm25 = BM25Okapi([tokenizar(c.page_content) for c in self.chunks])

    def vetorial(self, pergunta: str, k: int = 5) -> list[Document]:
        return self.banco.similarity_search(pergunta, k=k)

    def palavra_chave(self, pergunta: str, k: int = 5) -> list[Document]:
        notas = self.bm25.get_scores(tokenizar(pergunta))
        melhores = sorted(range(len(notas)), key=lambda i: notas[i], reverse=True)
        return [self.chunks[i] for i in melhores[:k]]

    def hibrida(self, pergunta: str, k: int = 5, candidatos: int = 20) -> list[Document]:
        listas = [
            self.vetorial(pergunta, k=candidatos),
            self.palavra_chave(pergunta, k=candidatos),
        ]
        pontos: dict[str, float] = {}
        por_id: dict[str, Document] = {}
        for lista in listas:
            for posicao, doc in enumerate(lista):
                chave = doc.page_content  # o texto identifica o chunk
                pontos[chave] = pontos.get(chave, 0) + 1 / (60 + posicao + 1)
                por_id[chave] = doc
        ranking = sorted(pontos, key=pontos.get, reverse=True)
        return [por_id[c] for c in ranking[:k]]


if __name__ == "__main__":
    # Teste rápido:  python busca.py "sua pergunta"
    import sys

    pergunta = " ".join(sys.argv[1:]) or "Qual a temperatura da geladeira de vacinas?"
    for doc in Buscador().hibrida(pergunta):
        print(f"[pág. {doc.metadata['pagina']}] {doc.page_content[:200]}...\n")
