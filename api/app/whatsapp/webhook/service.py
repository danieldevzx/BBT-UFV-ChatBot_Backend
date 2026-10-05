import logging

from app.bot import responder
from app.core.database.extensions import db
from app.core.models import Atendimento, Feedback, Mensagem
from app.core.utils.wa_utils import normalize_wa_id
from app.whatsapp import whatsapp

logger = logging.getLogger(__name__)


def process(data: dict):
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for msg in value.get("messages", []):
                wa_id = normalize_wa_id(msg.get("from", ""))
                if not wa_id:
                    continue

                tipo = msg.get("type", "")
                if tipo == "interactive":
                    _handle_interactive(wa_id, msg.get("interactive", {}))
                elif tipo == "text":
                    texto = (msg.get("text", {}) or {}).get("body", "")
                    if texto:
                        _handle_text(wa_id, texto)


def _handle_interactive(wa_id: str, interactive: dict):
    reply = (
        interactive.get("button_reply") or interactive.get("list_reply") or {}
    )
    reply_id = reply.get("id", "")
    if not reply_id:
        return

    if reply_id.startswith(responder.FEEDBACK_PREFIX):
        _handle_feedback(wa_id, reply_id)
        return

    try:
        no_id = int(reply_id)
    except ValueError:
        _send_menu_inicial(wa_id)
        return

    acao = responder.acao_no(no_id)
    if not acao:
        _send_menu_inicial(wa_id)
        return

    if acao["tipo"] == "MENU":
        _send_menu(wa_id, acao)
    elif acao["tipo"] == "RESPOSTA":
        _send_resposta(wa_id, acao)
    else:
        _abrir_atendimento(wa_id, acao)


def _handle_text(wa_id: str, texto: str):
    atendimento = _atendimento_aberto(wa_id)
    if atendimento:
        db.session.add(
            Mensagem(
                atendimento_id=atendimento.id, remetente="USUARIO", texto=texto
            )
        )
        db.session.commit()
        return

    whatsapp.send_text(wa_id, responder.fallback())
    _send_menu_inicial(wa_id)


def _handle_feedback(wa_id: str, reply_id: str):
    _, util, no_id = reply_id.split(":")
    db.session.add(Feedback(no_fluxo_id=int(no_id), util=util == "1"))
    db.session.commit()
    whatsapp.send_text(wa_id, responder.feedback_agradecimento())


def _atendimento_aberto(wa_id: str):
    return Atendimento.query.filter(
        Atendimento.telefone_solicitante == wa_id,
        Atendimento.status != "FECHADO",
    ).first()


def _send_menu_inicial(wa_id: str):
    _send_menu(wa_id, responder.acao_inicial())


def _send_menu(wa_id: str, acao: dict):
    opcoes = [(no.id, no.titulo) for no in acao["opcoes"]]
    if not opcoes:
        whatsapp.send_text(wa_id, acao["body"])
    elif len(opcoes) <= whatsapp.MAX_BUTTONS:
        whatsapp.send_buttons(wa_id, acao["body"], opcoes)
    else:
        whatsapp.send_list(wa_id, acao["body"], responder.menu_botao(), opcoes)


def _send_resposta(wa_id: str, acao: dict):
    whatsapp.send_text(wa_id, acao["body"])
    whatsapp.send_buttons(
        wa_id,
        responder.feedback_pergunta(),
        responder.resposta_feedback(acao["no"].id),
    )


def _abrir_atendimento(wa_id: str, acao: dict):
    db.session.add(
        Atendimento(
            telefone_solicitante=wa_id, status="ABERTO", canal="WHATSAPP"
        )
    )
    db.session.commit()
    whatsapp.send_text(wa_id, acao["body"])
