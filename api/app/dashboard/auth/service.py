from app.core.auth.guards import current_usuario
from app.core.auth.security import check_password, encode_token, hash_password
from app.core.database.extensions import db
from app.core.dtos import (
    AuthResponseDTO,
    LoginRequestDTO,
    RegisterRequestDTO,
    ResultDTO,
    UserResponseDTO,
)
from app.core.models import Perfil, Usuario


def serialize(usuario: Usuario) -> dict:
    return UserResponseDTO(
        id=usuario.id,
        email=usuario.email,
        name=usuario.nome,
        perfil=usuario.perfil.nome,
        ativo=usuario.ativo,
        created_at=usuario.created_at.isoformat(),
    ).__dict__


def _perfil_by_nome(nome: str) -> Perfil | None:
    return Perfil.query.filter_by(nome=nome).first()


def register(req: RegisterRequestDTO) -> ResultDTO:
    if not req.email or not req.password:
        return ResultDTO.bad_request("email and password are required")

    total = Usuario.query.count()
    if total > 0:
        atual = current_usuario()
        if not atual or atual.perfil.nome != "ADMIN":
            return ResultDTO.forbidden("Only ADMIN can create users")

    perfil_nome = req.perfil or ("ADMIN" if total == 0 else "ATENDENTE")
    perfil = _perfil_by_nome(perfil_nome)
    if not perfil:
        return ResultDTO.bad_request(f"Unknown perfil: {perfil_nome}")

    if Usuario.query.filter_by(email=req.email).first():
        return ResultDTO.conflict("email already registered")

    usuario = Usuario(
        nome=req.name or req.email,
        email=req.email,
        password_hash=hash_password(req.password),
        perfil_id=perfil.id,
    )
    db.session.add(usuario)
    db.session.commit()

    return ResultDTO.created(
        AuthResponseDTO(
            email=usuario.email,
            name=usuario.nome,
            perfil=perfil.nome,
            message="User created",
        ).__dict__
    )


def login(req: LoginRequestDTO) -> ResultDTO:
    if not req.email or not req.password:
        return ResultDTO.bad_request("email and password are required")

    usuario = Usuario.query.filter_by(email=req.email, ativo=True).first()
    if not usuario or not check_password(req.password, usuario.password_hash):
        return ResultDTO.unauthorized("Invalid credentials")

    token = encode_token(usuario.id)
    return ResultDTO.ok(
        AuthResponseDTO(
            email=usuario.email,
            name=usuario.nome,
            perfil=usuario.perfil.nome,
            token=token,
        ).__dict__
    )


def me(usuario: Usuario) -> ResultDTO:
    return ResultDTO.ok(serialize(usuario))
