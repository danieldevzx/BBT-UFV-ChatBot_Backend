from app.core.audit import registrar
from app.core.database.extensions import db
from app.core.dtos import ResultDTO
from app.core.models import Categoria
from app.core.serializers import categoria_dict


def listar() -> ResultDTO:
    categorias = Categoria.query.order_by(Categoria.nome).all()
    return ResultDTO.ok([categoria_dict(c) for c in categorias])


def obter(categoria_id: int) -> ResultDTO:
    categoria = db.session.get(Categoria, categoria_id)
    if not categoria:
        return ResultDTO.not_found("Categoria not found")
    return ResultDTO.ok(categoria_dict(categoria))


def criar(dados: dict, autor_id: str) -> ResultDTO:
    nome = (dados.get("nome") or "").strip()
    if not nome:
        return ResultDTO.bad_request("nome is required")

    categoria = Categoria(nome=nome, descricao=dados.get("descricao"))
    db.session.add(categoria)
    db.session.flush()
    registrar(autor_id, "CRIOU_CATEGORIA", "categoria", categoria.id)
    db.session.commit()
    return ResultDTO.created(categoria_dict(categoria))


def atualizar(categoria_id: int, dados: dict, autor_id: str) -> ResultDTO:
    categoria = db.session.get(Categoria, categoria_id)
    if not categoria:
        return ResultDTO.not_found("Categoria not found")

    if "nome" in dados:
        categoria.nome = (dados.get("nome") or "").strip() or categoria.nome
    if "descricao" in dados:
        categoria.descricao = dados.get("descricao")

    registrar(autor_id, "ATUALIZOU_CATEGORIA", "categoria", categoria.id)
    db.session.commit()
    return ResultDTO.ok(categoria_dict(categoria))


def remover(categoria_id: int, autor_id: str) -> ResultDTO:
    categoria = db.session.get(Categoria, categoria_id)
    if not categoria:
        return ResultDTO.not_found("Categoria not found")

    db.session.delete(categoria)
    registrar(autor_id, "REMOVEU_CATEGORIA", "categoria", categoria_id)
    db.session.commit()
    return ResultDTO.ok({"id": categoria_id})
