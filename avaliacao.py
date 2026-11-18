"""
AVALIAÇÃO DA BUSCA
==================
Roda todas as perguntas do gabarito em cada estratégia de busca e mede:

- ACERTO@K (hit rate): em quantas perguntas pelo menos um dos K trechos
  trazidos é de uma página correta. Se a busca não traz a página certa,
  a IA não tem como responder certo.

- MRR (Mean Reciprocal Rank): QUÃO NO TOPO veio o primeiro acerto.
  1º lugar = 1.0, 2º = 0.5, 3º = 0.33... Média de todas as perguntas.

Rode com:  python avaliacao.py
"""
from busca import Buscador
from perguntas_teste import PERGUNTAS

K = 5


def avaliar(nome: str, funcao_busca) -> None:
    acertos, soma_rr = 0, 0.0
    erros = []
    for item in PERGUNTAS:
        paginas = [d.metadata["pagina"] for d in funcao_busca(item["pergunta"], k=K)]
        posicao = next((i for i, p in enumerate(paginas) if p in item["paginas"]), None)
        if posicao is None:
            erros.append(f"    x {item['pergunta']}  (esperado {item['paginas']}, veio {paginas})")
        else:
            acertos += 1
            soma_rr += 1 / (posicao + 1)

    total = len(PERGUNTAS)
    print(f"{nome:<16} acerto@{K}: {acertos}/{total} ({acertos / total:.0%})   "
          f"MRR: {soma_rr / total:.2f}")
    for e in erros:
        print(e)


if __name__ == "__main__":
    buscador = Buscador()
    print(f"Avaliando {len(PERGUNTAS)} perguntas, top {K} trechos por busca\n")
    avaliar("Vetorial", buscador.vetorial)
    avaliar("Palavra-chave", buscador.palavra_chave)
    avaliar("Híbrida (RRF)", buscador.hibrida)
