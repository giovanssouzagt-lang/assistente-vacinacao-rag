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
- **FastAPI**: API REST com validação (Pydantic) e documentação automática
- **HTML + JavaScript**: tela de chat sem dependências, com tema claro/escuro

## Como rodar

Pré-requisitos: Python 3.12+ e [Ollama](https://ollama.com) instalados.

```bash
ollama pull bge-m3
ollama pull qwen3:8b

python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

python ingestao.py              # lê o PDF e monta o banco vetorial
uvicorn api:app                 # sobe a API e a tela de chat
```

Abra **http://localhost:8000** para usar o chat, ou **http://localhost:8000/docs**
para a documentação interativa da API.

### API

| Rota | O que faz |
|---|---|
| `GET /` | Tela de chat |
| `GET /saude` | Verifica se o Ollama está no ar e se os modelos estão baixados |
| `POST /perguntar` | Recebe `{"pergunta": "..."}` e devolve a resposta e as fontes |
| `GET /docs` | Documentação interativa (Swagger), gerada pelo FastAPI |

Exemplo de resposta de `POST /perguntar`:

```json
{
  "resposta": "Não. A administração da vacina BCG deve ser adiada quando a criança apresentar peso inferior a 2 kg (pág. 179).",
  "encontrou": true,
  "fontes": [
    { "pagina": 179, "secao": "12.2.1 Vacina BCG – BCG", "trecho": "..." }
  ]
}
```

Quando a resposta não está no manual, `encontrou` é `false` e `fontes` vem vazia.
Perguntas vazias ou com mais de 500 caracteres são recusadas com erro 422.

Também dá para testar pelo terminal, sem API:
`python resposta.py "Recém-nascido com menos de 2 kg pode tomar BCG?"`

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

## Avaliação das respostas

Rodando `python avaliacao_respostas.py`, cada resposta do gabarito é classificada como
**certa**, **recusa** ("não encontrei no manual") ou **errada**. Também há 4 perguntas
armadilha, cujos assuntos não estão no manual (ex.: dose de dipirona), que precisam ser recusadas.

Em saúde, uma resposta errada dita com confiança é pior que um "não sei". Por isso
recusa e erro são contados separadamente.

| Versão | Certas | Recusas | **Erradas** | Armadilhas | Tempo |
|---|---|---|---|---|---|
| qwen3:8b, prompt inicial | 8/12 | 0 | **4** | 4/4 | 1,7s |
| qwen3:8b, prompt com regras | 9/12 | — | **3** | 4/4 | 2,2s |
| qwen3:8b, modo "pensar" | 10/12 | — | **2** | 4/4 | 74s |
| qwen3:14b | 11/12 | 0 | **1** | 4/4 | 12,3s |
| **qwen3:8b + seção no contexto** ✅ | **10/12** | 2 | **0** | **4/4** | **1,3s** |

**Decisão: qwen3:8b com o título da seção no contexto.** O 14b acerta uma pergunta a mais,
mas dá **uma resposta perigosa** (diz que lactante com bebê de 4 meses pode tomar a vacina da
febre amarela, o que o manual proíbe) e é 10x mais lento. O 8b tem zero respostas erradas.

O que mais ajudou:
- **Regras no prompt contra suposições**: "a ausência de proibição não é permissão" e atenção
  a exceções ("exceto", "deve ser adiada").
- **Título da seção junto de cada trecho**: o item "Internação hospitalar, exceto para pólio
  oral" está numa lista de *falsas* contraindicações cujo título fica na página anterior.
  Sem o título, a IA entendia o contrário. O título vai só para a IA, não para o embedding:
  testei incluir e a busca vetorial piorou (11/12 → 10/12).

Limitações conhecidas (as 2 recusas):
- **Febre amarela e amamentação**: a busca não traz as páginas 200/203. Melhorar a busca é o próximo passo.
- **Validade da VOPb descongelada**: a informação está numa nota de rodapé de tabela, e a extração
  de tabelas do PDF ainda é frágil.

## Progresso

- [x] Ingestão: leitura do PDF, limpeza de texto, chunking e embeddings
- [x] Busca: comparação vetorial × BM25 × híbrida, com avaliação automática
- [x] Geração de respostas com citação de página e recusa quando não há resposta
- [x] API (FastAPI) e interface de chat
