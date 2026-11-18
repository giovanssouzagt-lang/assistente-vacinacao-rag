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

## Avaliação da busca

Montei um gabarito com 12 perguntas no jeito que um profissional de saúde
perguntaria (ex.: "geladeira" em vez de "câmara refrigerada"), com as páginas
corretas conferidas no manual. Comparei três estratégias (`python avaliacao.py`):

| Estratégia | Acerto@3 | Acerto@5 | Acerto@8 | MRR@5 |
|---|---|---|---|---|
| **Vetorial (bge-m3)** | 9/12 | **11/12** | 11/12 | **0.71** |
| Palavra-chave (BM25) | — | 7/12 | — | 0.37 |
| Híbrida (RRF) | 7/12 | 9/12 | 11/12 | 0.43 |

**Decisão: busca vetorial com k=5.**

A busca híbrida é uma recomendação comum, mas aqui piorou o resultado.
O motivo: as perguntas usam linguagem do dia a dia ("geladeira", "vacina oral
de pólio"), e o manual usa termos técnicos ("câmara refrigerada", "VOPb").
O BM25 depende de palavras iguais, então trouxe trechos errados que
"puxaram" o ranking da híbrida para baixo. O modelo de embeddings entende
os sinônimos.

Lições do processo:
- **Medir antes de otimizar**: sem o gabarito, eu teria adotado a híbrida achando que melhorou.
- **O gabarito também erra**: uma "falha" da busca era, na verdade, uma resposta que também
  estava nas páginas 200 e 203. Corrigi o gabarito, não a busca.

## Progresso

- [x] Ingestão: leitura do PDF, limpeza de texto, chunking e embeddings
- [x] Busca: comparação vetorial × BM25 × híbrida, com avaliação automática
- [ ] Geração de respostas com citação de fonte
- [ ] API (FastAPI) e interface de chat
