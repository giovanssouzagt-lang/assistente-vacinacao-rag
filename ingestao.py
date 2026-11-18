"""
ETAPA 2 — INGESTÃO
==================
Lê os PDFs da pasta `documentos/`, limpa o texto, divide em pedaços
(chunks), transforma cada pedaço em vetor (embedding) e salva tudo no
banco vetorial Chroma.

Rode com:  python ingestao.py

Fluxo:
    PDF  ->  páginas  ->  limpeza  ->  chunks  ->  embeddings  ->  Chroma
"""
import re
import shutil
import time

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

import config

# Cabeçalhos que se repetem em toda página do manual. Não carregam
# informação e "poluem" a busca, então removemos.
CABECALHOS = [
    r"SECRETARIA DE VIGIL[AÂ]NCIA EM SA[UÚ]DE E AMBIENTE\s*/\s*MS",
    r"MANUAL DE NORMAS E PROCEDIMENTOS PARA VACINA[CÇ][AÃ]O",
]


def limpar_texto(texto: str) -> str:
    """Corrige os defeitos típicos de texto extraído de PDF."""
    for cabecalho in CABECALHOS:
        texto = re.sub(cabecalho, " ", texto, flags=re.IGNORECASE)

    # Remove o número da página solto no começo (ex.: "30\n")
    texto = re.sub(r"^\s*\d{1,3}\s*\n", "", texto)

    # Junta palavras hifenizadas na quebra de linha: "ins-\ntâncias" -> "instâncias"
    texto = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", texto)

    # Quebra de linha simples vira espaço (no PDF ela é só fim da linha visual).
    # Quebra dupla (fim de parágrafo) é preservada.
    texto = re.sub(r"(?<!\n)\n(?!\n)", " ", texto)

    # Espaços repetidos viram um só
    texto = re.sub(r"[ \t]+", " ", texto)
    return texto.strip()


def carregar_pdfs() -> list[Document]:
    """Carrega cada página de cada PDF como um Document, já limpo."""
    paginas = []
    for pdf in sorted(config.PASTA_DOCUMENTOS.glob("*.pdf")):
        print(f"  Lendo {pdf.name}...")
        # enumerate começa em 1 porque o leitor de PDF que a pessoa abre
        # conta as páginas a partir de 1
        for numero, pagina in enumerate(PdfReader(pdf).pages, start=1):
            texto = limpar_texto(pagina.extract_text() or "")
            if len(texto) < 50:  # página praticamente vazia (capa, separador)
                continue
            paginas.append(
                Document(
                    page_content=texto,
                    metadata={"fonte": pdf.name, "pagina": numero},
                )
            )
    return paginas


def dividir_em_chunks(paginas: list[Document]) -> list[Document]:
    """
    Divide as páginas em pedaços menores.

    O RecursiveCharacterTextSplitter tenta cortar primeiro em parágrafos,
    depois em frases, depois em palavras, para não partir uma ideia ao meio.
    Cada chunk herda os metadados da página (fonte e número da página),
    o que permite citar a fonte na resposta.
    """
    divisor = RecursiveCharacterTextSplitter(
        chunk_size=config.TAMANHO_CHUNK,
        chunk_overlap=config.SOBREPOSICAO_CHUNK,
        separators=["\n\n", ". ", "; ", " ", ""],
    )
    return divisor.split_documents(paginas)


def main():
    inicio = time.time()

    print("1/3 Carregando PDFs...")
    paginas = carregar_pdfs()
    if not paginas:
        print(f"Nenhum PDF encontrado em {config.PASTA_DOCUMENTOS}")
        return
    print(f"  {len(paginas)} páginas com conteúdo.")

    print("2/3 Dividindo em chunks...")
    chunks = dividir_em_chunks(paginas)
    print(f"  {len(chunks)} chunks (tamanho {config.TAMANHO_CHUNK}, "
          f"sobreposição {config.SOBREPOSICAO_CHUNK}).")

    print(f"3/3 Gerando embeddings com '{config.MODELO_EMBEDDING}' e salvando no Chroma...")
    # Recria o banco do zero, para não duplicar chunks se rodar de novo
    if config.PASTA_BANCO.exists():
        shutil.rmtree(config.PASTA_BANCO)

    Chroma.from_documents(
        documents=chunks,
        embedding=OllamaEmbeddings(model=config.MODELO_EMBEDDING),
        collection_name=config.NOME_COLECAO,
        persist_directory=str(config.PASTA_BANCO),
    )

    print(f"\nPronto! {len(chunks)} chunks salvos em '{config.PASTA_BANCO.name}/' "
          f"em {time.time() - inicio:.0f}s.")


if __name__ == "__main__":
    main()
