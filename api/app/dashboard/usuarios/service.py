from app.core.audit import registrar
from app.core.auth.security import hash_password
from app.core.database.extensions import db
from app.core.dtos import ResultDTO
from app.core.models import Perfil, Usuario
from app.dashboard.auth.service import serialize


def listar() -> ResultDTO:
    usuarios = Usuario.query.order_by(Usuario.created_at).all()
    return ResultDTO.ok([serialize(u) for u in usuarios])


def obter(usuario_id: str) -> ResultDTO:
    usuario = db.session.get(Usuario, usuario_id)
    if not usuario:
        return ResultDTO.not_found("Usuario not found")
    return ResultDTO.ok(serialize(usuario))


def criar(dados: dict, autor_id: str) -> ResultDTO:
    email = (dados.get("email") or "").strip().lower()
    senha = (dados.get("password") or "").strip()
    if not email or not senha:
        return ResultDTO.bad_request("email and password are required")

    if Usuario.query.filter_by(email=email).first():
        return ResultDTO.conflict("email already registered")

    perfil = Perfil.query.filter_by(
        nome=(dados.get("perfil") or "ATENDENTE").upper()
    ).first()
    if not perfil:
        return ResultDTO.bad_request("Unknown perfil")

    usuario = Usuario(
        nome=(dados.get("name") or email),
        email=email,
        password_hash=hash_password(senha),
        perfil_id=perfil.id,
    )
    db.session.add(usuario)
    db.session.flush()
    registrar(autor_id, "CRIOU_USUARIO", "usuario", usuario.id)
    db.session.commit()
    return ResultDTO.created(serialize(usuario))


def atualizar(usuario_id: str, dados: dict, autor_id: str) -> ResultDTO:
    usuario = db.session.get(Usuario, usuario_id)
    if not usuario:
        return ResultDTO.not_found("Usuario not found")

    if "name" in dados:
        usuario.nome = (dados.get("name") or "").strip() or usuario.nome
    if "ativo" in dados:
        usuario.ativo = bool(dados.get("ativo"))
    if "password" in dados and dados.get("password"):
        usuario.password_hash = hash_password(dados["password"])
    if "perfil" in dados and dados.get("perfil"):
        perfil = Perfil.query.filter_by(nome=dados["perfil"].upper()).first()
        if not perfil:
            return ResultDTO.bad_request("Unknown perfil")
        usuario.perfil_id = perfil.id

    registrar(autor_id, "ATUALIZOU_USUARIO", "usuario", usuario.id)
    db.session.commit()
    return ResultDTO.ok(serialize(usuario))


def desativar(usuario_id: str, autor_id: str) -> ResultDTO:
    usuario = db.session.get(Usuario, usuario_id)
    if not usuario:
        return ResultDTO.not_found("Usuario not found")
    usuario.ativo = False
    registrar(autor_id, "DESATIVOU_USUARIO", "usuario", usuario.id)
    db.session.commit()
    return ResultDTO.ok(serialize(usuario))
