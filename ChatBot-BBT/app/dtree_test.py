from respostas import RESPOSTAS


def identificar_intencao(pergunta):

    pergunta = pergunta.lower()

    # Nó 1 - Multas
    if "multa" in pergunta or "multas" in pergunta:
        return "multa"

    # Nó 2 - Renovação
    elif "renovar" in pergunta or "renovação" in pergunta:
        return "renovacao"

    # Nó 3 - Acervo
    elif (
        "acervo" in pergunta
        or "livro" in pergunta
        or "pergamum" in pergunta
    ):
        return "acervo"

    # Nó 4 - Horários
    elif (
        "horário" in pergunta
        or "horarios" in pergunta
        or "abre" in pergunta
        or "fecha" in pergunta
    ):
        return "horarios"

    # Não identificou
    else:
        return "desconhecido"


def responder(pergunta):

    intencao = identificar_intencao(pergunta)

    return RESPOSTAS[intencao]


print("===================================")
print("      Chatbot da Biblioteca")
print("===================================")
print("Digite 'sair' para encerrar.\n")


while True:

    pergunta = input("Você: ")

    if pergunta.lower() == "sair":
        print("Bot: Até mais!")
        break

    resposta = responder(pergunta)

    print(f"\nBot: {resposta}")