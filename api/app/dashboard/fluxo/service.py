from app.core.audit import registrar
from app.core.database.extensions import db
from app.core.dtos import ResultDTO
from app.core.models import Conteudo, NoFluxo
from app.core.serializers import no_fluxo_dict

TIPOS = ("MENU", "RESPOSTA", "ATENDENTE")
MAX_TITULO = 24


def listar(parent_id=None, raiz=False, ativo=None) -> ResultDTO:
    query = NoFluxo.query
    if raiz:
        query = query.filter(NoFluxo.parent_id.is_(None))
    elif parent_id is not None:
        query = query.filter_by(parent_id=parent_id)
    if ativo is not None:
        query = query.filter_by(ativo=ativo)
    return ResultDTO.ok(
        [no_fluxo_dict(n) for n in query.order_by(NoFluxo.ordem, NoFluxo.id).all()]
    )


def obter(no_id: int) -> ResultDTO:
    no = db.session.get(NoFluxo, no_id)
    if not no:
        return ResultDTO.not_found("NoFluxo not found")
    return ResultDTO.ok(no_fluxo_dict(no))


def _validar(dados: dict, no_id: int | None = None) -> str | None:
    tipo = dados.get("tipo")
    if tipo is not None and tipo not in TIPOS:
        return "tipo must be MENU, RESPOSTA or ATENDENTE"
    titulo = dados.get("titulo")
    if titulo is not None and len(titulo) > MAX_TITULO:
        return f"titulo must be at most {MAX_TITULO} characters"
    if dados.get("parent_id") is not None:
        parent = db.session.get(NoFluxo, dados["parent_id"])
        if not parent:
            return "Unknown parent_id"
        if no_id is not None and parent.id == no_id:
            return "parent_id cannot reference itself"
    if tipo == "RESPOSTA":
        if not dados.get("conteudo_id"):
            return "conteudo_id is required when tipo=RESPOSTA"
        if not db.session.get(Conteudo, dados["conteudo_id"]):
            return "Unknown conteudo_id"
    if tipo in ("MENU", "ATENDENTE") and dados.get("conteudo_id"):
        return "conteudo_id must be empty unless tipo=RESPOSTA"
    return None


def criar(dados: dict, autor_id: str) -> ResultDTO:
    if not dados.get("titulo") or not dados.get("tipo"):
        return ResultDTO.bad_request("titulo and tipo are required")
    erro = _validar(dados)
    if erro:
        return ResultDTO.bad_request(erro)

    no = NoFluxo(
        titulo=dados["titulo"],
        tipo=dados["tipo"],
        parent_id=dados.get("parent_id"),
        conteudo_id=dados.get("conteudo_id"),
        ordem=dados.get("ordem", 0),
    )
    db.session.add(no)
    db.session.flush()
    registrar(autor_id, "CRIOU_NO_FLUXO", "no_fluxo", no.id)
    db.session.commit()
    return ResultDTO.created(no_fluxo_dict(no))


def atualizar(no_id: int, dados: dict, autor_id: str) -> ResultDTO:
    no = db.session.get(NoFluxo, no_id)
    if not no:
        return ResultDTO.not_found("NoFluxo not found")

    erro = _validar(dados, no_id=no_id)
    if erro:
        return ResultDTO.bad_request(erro)

    for campo in ("titulo", "tipo", "parent_id", "conteudo_id", "ordem", "ativo"):
        if campo in dados:
            setattr(no, campo, dados[campo])

    registrar(autor_id, "ATUALIZOU_NO_FLUXO", "no_fluxo", no.id)
    db.session.commit()
    return ResultDTO.ok(no_fluxo_dict(no))


def desativar(no_id: int, autor_id: str) -> ResultDTO:
    no = db.session.get(NoFluxo, no_id)
    if not no:
        return ResultDTO.not_found("NoFluxo not found")
    no.ativo = False
    registrar(autor_id, "DESATIVOU_NO_FLUXO", "no_fluxo", no.id)
    db.session.commit()
    return ResultDTO.ok(no_fluxo_dict(no))
