from app.core.audit import registrar
from app.core.database.extensions import db
from app.core.dtos import ResultDTO
from app.core.models import Categoria, Conteudo
from app.core.serializers import conteudo_dict


def listar(categoria_id=None, ativo=None) -> ResultDTO:
    query = Conteudo.query
    if categoria_id is not None:
        query = query.filter_by(categoria_id=categoria_id)
    if ativo is not None:
        query = query.filter_by(ativo=ativo)
    return ResultDTO.ok([conteudo_dict(c) for c in query.order_by(Conteudo.titulo).all()])


def obter(conteudo_id: int) -> ResultDTO:
    conteudo = db.session.get(Conteudo, conteudo_id)
    if not conteudo:
        return ResultDTO.not_found("Conteudo not found")
    return ResultDTO.ok(conteudo_dict(conteudo))


def criar(dados: dict, autor_id: str) -> ResultDTO:
    titulo = (dados.get("titulo") or "").strip()
    texto = (dados.get("texto") or "").strip()
    categoria_id = dados.get("categoria_id")
    if not titulo or not texto or categoria_id is None:
        return ResultDTO.bad_request("titulo, texto and categoria_id are required")
    if not db.session.get(Categoria, categoria_id):
        return ResultDTO.bad_request("Unknown categoria")
    if Conteudo.query.filter_by(titulo=titulo).first():
        return ResultDTO.conflict("titulo already exists")

    conteudo = Conteudo(
        titulo=titulo,
        texto=texto,
        categoria_id=categoria_id,
        fonte=dados.get("fonte"),
        created_by=autor_id,
    )
    db.session.add(conteudo)
    db.session.flush()
    registrar(autor_id, "CRIOU_CONTEUDO", "conteudo", conteudo.id)
    db.session.commit()
    return ResultDTO.created(conteudo_dict(conteudo))


def atualizar(conteudo_id: int, dados: dict, autor_id: str) -> ResultDTO:
    conteudo = db.session.get(Conteudo, conteudo_id)
    if not conteudo:
        return ResultDTO.not_found("Conteudo not found")

    if "titulo" in dados:
        titulo = (dados.get("titulo") or "").strip()
        if titulo and titulo != conteudo.titulo:
            if Conteudo.query.filter_by(titulo=titulo).first():
                return ResultDTO.conflict("titulo already exists")
            conteudo.titulo = titulo
    if "texto" in dados:
        conteudo.texto = dados.get("texto") or conteudo.texto
    if "fonte" in dados:
        conteudo.fonte = dados.get("fonte")
    if "categoria_id" in dados:
        if not db.session.get(Categoria, dados["categoria_id"]):
            return ResultDTO.bad_request("Unknown categoria")
        conteudo.categoria_id = dados["categoria_id"]
    if "ativo" in dados:
        conteudo.ativo = bool(dados.get("ativo"))

    registrar(autor_id, "ATUALIZOU_CONTEUDO", "conteudo", conteudo.id)
    db.session.commit()
    return ResultDTO.ok(conteudo_dict(conteudo))


def desativar(conteudo_id: int, autor_id: str) -> ResultDTO:
    conteudo = db.session.get(Conteudo, conteudo_id)
    if not conteudo:
        return ResultDTO.not_found("Conteudo not found")
    conteudo.ativo = False
    registrar(autor_id, "DESATIVOU_CONTEUDO", "conteudo", conteudo.id)
    db.session.commit()
    return ResultDTO.ok(conteudo_dict(conteudo))
