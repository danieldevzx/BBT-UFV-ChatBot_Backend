from app.bot import fluxo

FEEDBACK_PREFIX = "feedback:"


def acao_inicial() -> dict:
    return {
        "tipo": "MENU",
        "body": fluxo.obter_config("boas_vindas", "Escolha uma opção:"),
        "opcoes": fluxo.listar_filhos(None),
    }


def acao_no(no_id) -> dict | None:
    no = fluxo.obter_no(no_id)
    if not no:
        return None
    if no.tipo == "MENU":
        return {"tipo": "MENU", "body": no.titulo, "opcoes": fluxo.listar_filhos(no.id)}
    if no.tipo == "RESPOSTA":
        return {"tipo": "RESPOSTA", "body": no.conteudo.texto, "no": no}
    return {"tipo": "ATENDENTE", "body": fluxo.obter_config("atendente_msg", "Aguarde, você será atendido."), "no": no}


def resposta_feedback(no_id: int):
    return [
        (f"{FEEDBACK_PREFIX}1:{no_id}", fluxo.obter_config("feedback_sim", "Ajudou")),
        (f"{FEEDBACK_PREFIX}0:{no_id}", fluxo.obter_config("feedback_nao", "Não ajudou")),
    ]


def menu_botao() -> str:
    return fluxo.obter_config("menu_botao", "Ver opções")


def feedback_pergunta() -> str:
    return fluxo.obter_config("feedback_pergunta", "Essa resposta te ajudou?")


def feedback_agradecimento() -> str:
    return fluxo.obter_config("feedback_obrigado", "Obrigado pelo seu feedback!")


def fallback() -> str:
    return fluxo.obter_config(
        "fallback", "Não entendi. Vou te mostrar o menu novamente."
    )
