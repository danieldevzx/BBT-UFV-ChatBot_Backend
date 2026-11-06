import logging
import threading
from collections import OrderedDict

from app.bot import responder
from app.core.database.extensions import db
from app.core.models import Atendimento, Feedback, Mensagem, NoFluxo
from app.core.utils.wa_utils import normalize_wa_id
from app.whatsapp import whatsapp

logger = logging.getLogger(__name__)

# A Meta pode reenviar a mesma mensagem; guardamos os ids recentes para não
# responder duas vezes. Fica em memória: basta porque o backend roda em um
# único processo (o SQLite só aceita um escritor por vez).
_MAX_IDS = 5000
_ids_processados: "OrderedDict[str, None]" = OrderedDict()
_lock = threading.Lock()


def _ja_processada(msg_id: str) -> bool:
    with _lock:
        if msg_id in _ids_processados:
            return True
        _ids_processados[msg_id] = None
        if len(_ids_processados) > _MAX_IDS:
            _ids_processados.popitem(last=False)
        return False


def process(data: dict):
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for msg in value.get("messages", []):
                msg_id = msg.get("id")
                if msg_id and _ja_processada(msg_id):
                    continue
                try:
                    _processar_mensagem(msg)
                except Exception:
                    # Nunca devolver 500 à Meta: ela reenviaria a mensagem.
                    db.session.rollback()
                    logger.exception("Falha ao processar mensagem do webhook")


def _processar_mensagem(msg: dict):
    wa_id = normalize_wa_id(msg.get("from", ""))
    if not wa_id:
        return
    tipo = msg.get("type", "")
    if tipo == "interactive":
        _handle_interactive(wa_id, msg.get("interactive", {}))
    elif tipo == "text":
        texto = (msg.get("text", {}) or {}).get("body", "")
        if texto:
            _handle_text(wa_id, texto)


def _handle_interactive(wa_id: str, interactive: dict):
    reply = interactive.get("button_reply") or interactive.get("list_reply") or {}
    reply_id = reply.get("id", "")
    if not reply_id:
        return

    if reply_id.startswith(responder.FEEDBACK_PREFIX):
        _handle_feedback(wa_id, reply_id)
        return
    if reply_id == responder.NAV_INICIO:
        _send_menu_inicial(wa_id)
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
            Mensagem(atendimento_id=atendimento.id, remetente="USUARIO", texto=texto)
        )
        db.session.commit()
        return

    whatsapp.send_text(wa_id, responder.fallback())
    _send_menu_inicial(wa_id)


def _handle_feedback(wa_id: str, reply_id: str):
    try:
        _, util, no_id = reply_id.split(":")
        no_id = int(no_id)
    except ValueError:
        _send_menu_inicial(wa_id)
        return
    if db.session.get(NoFluxo, no_id) is None:
        _send_menu_inicial(wa_id)
        return
    db.session.add(Feedback(no_fluxo_id=no_id, util=util == "1"))
    db.session.commit()
    whatsapp.send_buttons(
        wa_id, responder.feedback_agradecimento(), [responder.botao_menu_inicial()]
    )


def _atendimento_aberto(wa_id: str):
    return (
        Atendimento.query.filter(
            Atendimento.telefone_solicitante == wa_id,
            Atendimento.status != "FECHADO",
        )
        .order_by(Atendimento.id.desc())
        .first()
    )


def _send_menu_inicial(wa_id: str):
    _send_menu(wa_id, responder.acao_inicial())


def _send_menu(wa_id: str, acao: dict):
    opcoes = [(no.id, no.titulo) for no in acao["opcoes"]]
    if acao.get("voltar"):
        # garante espaço para o "Voltar" dentro do limite de 10 linhas
        opcoes = opcoes[: whatsapp.MAX_ROWS - 1] + [responder.botao_voltar(acao["voltar"])]

    if not opcoes:
        whatsapp.send_text(wa_id, acao["body"])
        return

    # Botões só quando cabem: até 3 opções e todos os títulos com até 20
    # caracteres. Senão vai como lista (títulos até 24), sem cortar texto.
    cabe_em_botoes = len(opcoes) <= whatsapp.MAX_BUTTONS and all(
        len(titulo) <= whatsapp.MAX_BUTTON_TITLE for _, titulo in opcoes
    )
    if cabe_em_botoes:
        whatsapp.send_buttons(wa_id, acao["body"], opcoes)
    else:
        whatsapp.send_list(wa_id, acao["body"], responder.menu_botao(), opcoes)


def _send_resposta(wa_id: str, acao: dict):
    whatsapp.send_text(wa_id, acao["body"])
    whatsapp.send_buttons(
        wa_id,
        responder.feedback_pergunta(),
        responder.resposta_feedback(acao["no"].id) + [responder.botao_menu_inicial()],
    )


def _abrir_atendimento(wa_id: str, acao: dict):
    if _atendimento_aberto(wa_id):
        whatsapp.send_text(wa_id, responder.atendente_ja_aberto())
        return

    atendimento = Atendimento(telefone_solicitante=wa_id, status="ABERTO", canal="WHATSAPP")
    db.session.add(atendimento)
    db.session.flush()
    # Registra de qual opção o aluno veio, para a atendente saber o assunto.
    db.session.add(
        Mensagem(
            atendimento_id=atendimento.id,
            remetente="BOT",
            texto=f"Encaminhado pelo menu: {acao['no'].titulo}",
        )
    )
    db.session.commit()
    whatsapp.send_text(wa_id, acao["body"])
