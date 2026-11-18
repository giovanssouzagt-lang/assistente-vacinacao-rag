"""
ETAPA 4 — GERAÇÃO DE RESPOSTA (o "G" de RAG: Generation)
=========================================================
Junta tudo:  pergunta -> busca os trechos -> IA lê os trechos -> resposta com página.

O segredo contra "alucinação" (a IA inventar coisas) está no PROMPT DE
SISTEMA: instruções fixas que mandam a IA usar SOMENTE os trechos
entregues e admitir quando a resposta não está neles.

Rode com:  python resposta.py "sua pergunta"
"""
from dataclasses import dataclass

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

import config
from busca import Buscador

# Frase fixa para quando a resposta não está no manual. Ser uma frase
# exata permite que o teste automático detecte se a IA recusou certo.
SEM_RESPOSTA = "Não encontrei essa informação no Manual de Normas e Procedimentos para Vacinação."

PROMPT_SISTEMA = f"""Você é um assistente para profissionais de saúde em salas de vacinação.
Responda à pergunta usando SOMENTE os trechos do Manual de Normas e Procedimentos
para Vacinação (Ministério da Saúde, 2024) fornecidos abaixo.

Regras:
1. Use apenas informações presentes nos trechos. Nunca use conhecimento próprio.
2. Cite a página de cada informação no formato (pág. N), usando a página do
   trecho de onde a informação foi tirada.
3. Se os trechos não contiverem a resposta, responda exatamente:
   "{SEM_RESPOSTA}"
4. Só responda "Sim" se um trecho afirmar isso explicitamente. A ausência de
   uma proibição NÃO é uma permissão.
5. Atenção a exceções e negações ("exceto", "não está indicada", "deve ser
   adiada", "contraindicada"). Em uma lista de situações que NÃO impedem a
   vacinação, um item marcado como "exceto" significa que, nesse caso, a
   vacinação NÃO deve ser feita.
6. Em tabelas, as notas numeradas logo abaixo (1., 2., 3.) também contêm
   informações válidas.
7. Seja direto: comece pela resposta (Sim, Não ou o valor pedido) e depois
   explique em até 3 frases.
8. Responda em português do Brasil."""


@dataclass
class Resposta:
    texto: str
    trechos: list[Document]

    @property
    def paginas(self) -> list[int]:
        return sorted({d.metadata["pagina"] for d in self.trechos})


class Assistente:
    def __init__(self):
        self.buscador = Buscador()
        self.llm = ChatOllama(
            model=config.MODELO_LLM,
            temperature=0,     # respostas consistentes, sem "criatividade"
            reasoning=config.PENSAR,  # modo "pensar" do Qwen3 (ver config.py)
            num_ctx=8192,      # espaço para a pergunta + 5 trechos
        )

    @staticmethod
    def _montar_contexto(trechos: list[Document]) -> str:
        # O título da seção acompanha cada trecho: sem ele, um item solto de
        # uma lista (ex.: de "Falsas contraindicações") pode ser mal entendido.
        partes = []
        for i, d in enumerate(trechos, start=1):
            secao = d.metadata.get("secao")
            cabecalho = f"[Trecho {i} | pág. {d.metadata['pagina']}"
            cabecalho += f" | Seção: {secao}]" if secao else "]"
            partes.append(f"{cabecalho}\n{d.page_content}")
        return "\n\n".join(partes)

    def perguntar(self, pergunta: str) -> Resposta:
        trechos = self.buscador.vetorial(pergunta, k=config.TOP_K)
        mensagens = [
            SystemMessage(PROMPT_SISTEMA),
            HumanMessage(
                f"TRECHOS DO MANUAL:\n\n{self._montar_contexto(trechos)}\n\n"
                f"PERGUNTA: {pergunta}"
            ),
        ]
        texto = self.llm.invoke(mensagens).content.strip()
        return Resposta(texto=texto, trechos=trechos)


if __name__ == "__main__":
    import sys

    pergunta = " ".join(sys.argv[1:]) or "Recém-nascido com menos de 2 kg pode tomar BCG?"
    r = Assistente().perguntar(pergunta)
    print(f"PERGUNTA: {pergunta}\n\n{r.texto}\n\nTrechos consultados: págs. {r.paginas}")
