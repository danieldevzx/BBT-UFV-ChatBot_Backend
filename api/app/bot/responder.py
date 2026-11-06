from app.bot import fluxo

FEEDBACK_PREFIX = "feedback:"
# id de botão que leva ao menu inicial (os demais ids são ids de nó)
NAV_INICIO = "inicio"


def acao_inicial() -> dict:
    return {
        "tipo": "MENU",
        "body": fluxo.obter_config("boas_vindas", "Escolha uma opção:"),
        "opcoes": fluxo.listar_filhos(None),
        "voltar": None,
    }


def acao_no(no_id) -> dict | None:
    no = fluxo.obter_no(no_id)
    if not no:
        return None
    if no.tipo == "MENU":
        return {
            "tipo": "MENU",
            "body": no.titulo,
            "opcoes": fluxo.listar_filhos(no.id),
            # submenu volta para o menu pai (ou para o inicial, se for de 1º nível)
            "voltar": str(no.parent_id) if no.parent_id else NAV_INICIO,
        }
    if no.tipo == "RESPOSTA":
        return {"tipo": "RESPOSTA", "body": no.conteudo.texto, "no": no}
    return {
        "tipo": "ATENDENTE",
        "body": fluxo.obter_config("atendente_msg", "Aguarde, você será atendido."),
        "no": no,
    }


def resposta_feedback(no_id: int):
    return [
        (f"{FEEDBACK_PREFIX}1:{no_id}", fluxo.obter_config("feedback_sim", "Ajudou")),
        (f"{FEEDBACK_PREFIX}0:{no_id}", fluxo.obter_config("feedback_nao", "Não ajudou")),
    ]


def botao_voltar(destino: str):
    return (destino, fluxo.obter_config("voltar", "Voltar"))


def botao_menu_inicial():
    return (NAV_INICIO, fluxo.obter_config("menu_inicial", "Menu inicial"))


def menu_botao() -> str:
    return fluxo.obter_config("menu_botao", "Ver opções")


def feedback_pergunta() -> str:
    return fluxo.obter_config("feedback_pergunta", "Essa resposta te ajudou?")


def feedback_agradecimento() -> str:
    return fluxo.obter_config("feedback_obrigado", "Obrigado pelo seu feedback!")


def atendente_ja_aberto() -> str:
    return fluxo.obter_config(
        "atendente_ja_aberto",
        "Seu atendimento já está aberto. É só escrever por aqui que a atendente responde.",
    )


def fallback() -> str:
    return fluxo.obter_config(
        "fallback", "Não entendi. Vou te mostrar o menu novamente."
    )
