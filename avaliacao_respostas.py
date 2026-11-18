"""
AVALIAÇÃO DAS RESPOSTAS
=======================
Dois testes:

1. PERGUNTAS DO GABARITO: a resposta cita pelo menos uma página correta?
   (Se cita a página certa, a informação veio do lugar certo.)

2. PERGUNTAS ARMADILHA: assuntos que NÃO estão no manual. O assistente
   passa só se recusar com a frase padrão, em vez de inventar uma resposta.
   Isso mede a resistência à "alucinação".

As respostas completas são impressas para revisão humana, porque citar a
página certa não garante, sozinho, que o conteúdo da resposta está correto.

Rode com:  python avaliacao_respostas.py
"""
import re
import time

from perguntas_teste import PERGUNTAS
from resposta import SEM_RESPOSTA, Assistente

# Conferido: nenhum destes assuntos aparece no texto do manual
ARMADILHAS = [
    "Qual a dose de dipirona para uma criança de 10 kg?",
    "Qual o tratamento para infecção urinária em gestante?",
    "Ivermectina previne covid-19?",
    "Quem ganhou a Copa do Mundo de 2022?",
]


def paginas_citadas(texto: str) -> set[int]:
    return {int(n) for n in re.findall(r"p[áa]g(?:ina)?s?\.?\s*(\d+)", texto, re.I)}


def recusou(texto: str) -> bool:
    return "não encontrei" in texto.lower()


def main():
    assistente = Assistente()
    inicio = time.time()

    print("=" * 70, "\n1) PERGUNTAS DO GABARITO\n", "=" * 70, sep="")
    ok_conteudo, ok_citacao, recusas = 0, 0, 0
    for item in PERGUNTAS:
        r = assistente.perguntar(item["pergunta"])
        citadas = paginas_citadas(r.texto)
        # Uma recusa ("Não encontrei...") nunca conta como acerto, mesmo
        # que comece com "Não". Recusar é seguro, mas não responde.
        if recusou(r.texto):
            status = "RECUSOU"
            recusas += 1
        elif re.search(item["deve_conter"], r.texto, re.I | re.S):
            status = "CERTO"
            ok_conteudo += 1
        else:
            status = "ERRADO"
        citacao = bool(citadas & set(item["paginas"]))
        ok_citacao += citacao
        print(f"\n[conteúdo {status} | citação {'OK' if citacao else 'ERRADA'}] "
              f"{item['pergunta']}")
        print(f"  esperado págs. {item['paginas']} | citou {sorted(citadas)}")
        print("  " + r.texto.replace("\n", "\n  "))

    print("\n" + "=" * 70, "\n2) PERGUNTAS ARMADILHA (devem ser recusadas)\n", "=" * 70, sep="")
    ok_armadilha = 0
    for pergunta in ARMADILHAS:
        r = assistente.perguntar(pergunta)
        acertou = recusou(r.texto)
        ok_armadilha += acertou
        print(f"\n[{'OK' if acertou else 'INVENTOU'}] {pergunta}")
        print("  " + r.texto.replace("\n", "\n  "))

    total = len(PERGUNTAS) + len(ARMADILHAS)
    print("\n" + "=" * 70)
    erradas = len(PERGUNTAS) - ok_conteudo - recusas
    print(f"Conteúdo:   {ok_conteudo}/{len(PERGUNTAS)} certas | "
          f"{recusas} recusas (seguro) | {erradas} erradas (perigoso)")
    print(f"Citação:    {ok_citacao}/{len(PERGUNTAS)} citaram página correta")
    print(f"Armadilhas: {ok_armadilha}/{len(ARMADILHAS)} recusadas corretamente")
    print(f"Tempo médio por pergunta: {(time.time() - inicio) / total:.1f}s")


if __name__ == "__main__":
    main()
