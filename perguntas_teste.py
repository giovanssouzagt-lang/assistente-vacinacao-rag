"""
GABARITO DE AVALIAÇÃO
=====================
Perguntas que um profissional de saúde faria, com:

- "paginas": onde a resposta realmente está no manual (numeração do leitor
  de PDF). Usado para avaliar a BUSCA e a CITAÇÃO.
- "deve_conter": expressão regular que a resposta da IA PRECISA conter para
  estar correta. Usado para avaliar o CONTEÚDO. Ex.: se o manual diz "não",
  a resposta tem que começar com "Não".

Tudo conferido manualmente no texto do manual. As perguntas usam de propósito
palavras DIFERENTES das do manual ("geladeira" em vez de "câmara refrigerada"),
porque é assim que as pessoas perguntam de verdade.
"""

PERGUNTAS = [
    {
        "pergunta": "Em qual temperatura devo manter as vacinas na geladeira da sala de vacinação?",
        "paginas": [123, 129],
        "deve_conter": r"\+?2\s*°?\s*C?.{0,15}\+?8\s*°?C",
    },
    {
        "pergunta": "Em quantos graus o alarme da câmara de vacinas deve disparar?",
        "paginas": [129],
        "deve_conter": r"\+?\s?7\s*°?C",
    },
    {
        "pergunta": "Depois que eu abro um frasco multidose, posso usar até a data de validade do rótulo?",
        "paginas": [127],
        "deve_conter": r"^\W*N[ãa]o\b",
    },
    {
        "pergunta": "Quem não pode tomar a vacina BCG?",
        "paginas": [179],
        "deve_conter": r"2\s?kg",
    },
    {
        "pergunta": "Recém-nascido com menos de 2 kg pode tomar BCG?",
        "paginas": [179],
        "deve_conter": r"^\W*N[ãa]o\b",
    },
    {
        "pergunta": "Até quando o bebê deve receber a primeira dose da vacina de hepatite B?",
        "paginas": [183, 184],
        "deve_conter": r"24 horas",
    },
    {
        "pergunta": "Quem tomou a tríplice viral pode doar sangue logo depois?",
        "paginas": [205],
        "deve_conter": r"^\W*N[ãa]o\b.*(quatro|4) semanas",
    },
    {
        "pergunta": "Quanto tempo a mulher deve esperar para engravidar depois da vacina contra sarampo, caxumba e rubéola?",
        "paginas": [205],
        "deve_conter": r"(um|1) m[êe]s",
    },
    {
        "pergunta": "Mãe que amamenta bebê de 4 meses pode tomar a vacina da febre amarela?",
        "paginas": [148, 200, 203],
        "deve_conter": r"^\W*N[ãa]o\b",
    },
    {
        "pergunta": "Criança internada no hospital pode receber a vacina oral de pólio?",
        "paginas": [148],
        "deve_conter": r"^\W*N[ãa]o\b",
    },
    {
        "pergunta": "Qual o prazo de validade da vacina oral de pólio depois de descongelada?",
        "paginas": [122],
        "deve_conter": r"(seis|6) meses",
    },
    {
        "pergunta": "Quanto tempo esperar depois de montar a caixa térmica antes de colocar as vacinas?",
        "paginas": [46],
        "deve_conter": r"(duas|2) horas",
    },
]
