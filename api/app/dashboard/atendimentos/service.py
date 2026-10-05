from datetime import datetime, timezone

from app.core.database.extensions import db
from app.core.dtos import ResultDTO
from app.core.models import Atendimento, Mensagem
from app.core.serializers import atendimento_dict, mensagem_dict
from app.whatsapp import whatsapp

STATUS = ("ABERTO", "EM_ATENDIMENTO", "FECHADO")


def _pode_acessar(usuario, atendimento: Atendimento) -> bool:
    if usuario.perfil.nome == "ADMIN":
        return True
    return atendimento.usuario_atendente_id in (None, usuario.id)


def listar(usuario) -> ResultDTO:
    query = Atendimento.query
    if usuario.perfil.nome != "ADMIN":
        query = query.filter(
            (Atendimento.usuario_atendente_id == usuario.id)
            | (Atendimento.usuario_atendente_id.is_(None))
        )
    return ResultDTO.ok(
        [atendimento_dict(a) for a in query.order_by(Atendimento.created_at.desc()).all()]
    )


def obter(atendimento_id: int, usuario) -> ResultDTO:
    atendimento = db.session.get(Atendimento, atendimento_id)
    if not atendimento:
        return ResultDTO.not_found("Atendimento not found")
    if not _pode_acessar(usuario, atendimento):
        return ResultDTO.forbidden("Forbidden")
    return ResultDTO.ok(atendimento_dict(atendimento))


def atualizar(atendimento_id: int, dados: dict, usuario) -> ResultDTO:
    atendimento = db.session.get(Atendimento, atendimento_id)
    if not atendimento:
        return ResultDTO.not_found("Atendimento not found")
    if not _pode_acessar(usuario, atendimento):
        return ResultDTO.forbidden("Forbidden")

    status = dados.get("status")
    if status is not None:
        if status not in STATUS:
            return ResultDTO.bad_request("Invalid status")
        atendimento.status = status
        if status == "EM_ATENDIMENTO" and not atendimento.usuario_atendente_id:
            atendimento.usuario_atendente_id = usuario.id
        if status == "FECHADO":
            atendimento.closed_at = datetime.now(timezone.utc)

    if dados.get("assumir") and not atendimento.usuario_atendente_id:
        atendimento.usuario_atendente_id = usuario.id
        atendimento.status = "EM_ATENDIMENTO"

    db.session.commit()
    return ResultDTO.ok(atendimento_dict(atendimento))


def listar_mensagens(atendimento_id: int, usuario) -> ResultDTO:
    atendimento = db.session.get(Atendimento, atendimento_id)
    if not atendimento:
        return ResultDTO.not_found("Atendimento not found")
    if not _pode_acessar(usuario, atendimento):
        return ResultDTO.forbidden("Forbidden")
    mensagens = (
        Mensagem.query.filter_by(atendimento_id=atendimento_id)
        .order_by(Mensagem.enviado_em)
        .all()
    )
    return ResultDTO.ok([mensagem_dict(m) for m in mensagens])


def criar_mensagem(atendimento_id: int, dados: dict, usuario) -> ResultDTO:
    atendimento = db.session.get(Atendimento, atendimento_id)
    if not atendimento:
        return ResultDTO.not_found("Atendimento not found")
    if not _pode_acessar(usuario, atendimento):
        return ResultDTO.forbidden("Forbidden")

    texto = (dados.get("texto") or "").strip()
    if not texto:
        return ResultDTO.bad_request("texto is required")

    mensagem = Mensagem(atendimento_id=atendimento_id, remetente="ATENDENTE", texto=texto)
    db.session.add(mensagem)
    db.session.commit()

    enviado = whatsapp.send_text(atendimento.telefone_solicitante, texto)
    return ResultDTO.created({**mensagem_dict(mensagem), "enviado": enviado})
