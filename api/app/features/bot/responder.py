_RESPOSTAS = {
    "multa": "Para informações sobre multas, consulte as regras da biblioteca e verifique o procedimento de pagamento.",
    "renovacao": "Para renovar um livro, é necessário realizar o procedimento de renovação pelo sistema da biblioteca.",
    "acervo": "Para pesquisar um livro no acervo, utilize o catálogo Pergamum da biblioteca.",
    "horarios": "Você pode consultar os horários de funcionamento e os canais de contato da biblioteca na documentação oficial.",
    "desconhecido": (
        "Não consegui identificar sua dúvida.\n\n"
        "Posso ajudar com:\n"
        "- multas\n"
        "- renovação de livros\n"
        "- pesquisa no acervo\n"
        "- horários e contatos\n\n"
        "Se sua dúvida for sobre outro assunto, posso encaminhar você para um atendente."
    ),
}


def identify_intent(question: str) -> str:
    q = question.lower()
    if "multa" in q:
        return "multa"
    if "renovar" in q or "renovação" in q:
        return "renovacao"
    if "acervo" in q or "livro" in q or "pergamum" in q:
        return "acervo"
    if "horário" in q or "horario" in q or "abre" in q or "fecha" in q:
        return "horarios"
    return "desconhecido"


def get_reply(question: str) -> str:
    return _RESPOSTAS[identify_intent(question)]