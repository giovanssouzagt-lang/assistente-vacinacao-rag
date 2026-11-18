# Assistente de Vacinação (RAG)

Assistente que responde perguntas de profissionais de saúde com base no
**Manual de Normas e Procedimentos para Vacinação** (Ministério da Saúde, 2ª ed., 2024),
citando a página de onde tirou a informação.

Usa **RAG (Retrieval-Augmented Generation)**: em vez de confiar na "memória" da IA,
o sistema busca os trechos relevantes do manual e entrega à IA junto com a pergunta.

> 🚧 Projeto em desenvolvimento.

## Stack

- **Python** + **LangChain**: orquestração do pipeline
- **Chroma**: banco vetorial
- **Ollama**: modelos rodando 100% local, na GPU (nenhum dado sai da máquina)
  - `bge-m3`: embeddings multilíngues
  - `qwen3:8b`: geração de respostas
- **FastAPI**: API (em breve)

## Como rodar

Pré-requisitos: Python 3.12+ e [Ollama](https://ollama.com) instalados.

```bash
ollama pull bge-m3
ollama pull qwen3:8b

python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

python ingestao.py              # lê o PDF e monta o banco vetorial
```

## Progresso

- [x] Ingestão: leitura do PDF, limpeza de texto, chunking e embeddings
- [ ] Busca híbrida (vetorial + BM25) e avaliação de qualidade
- [ ] Geração de respostas com citação de fonte
- [ ] API (FastAPI) e interface de chat
