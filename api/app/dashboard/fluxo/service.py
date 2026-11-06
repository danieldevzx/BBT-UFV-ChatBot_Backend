from app.core.audit import registrar
from app.core.database.extensions import db
from app.core.dtos import ResultDTO
from app.core.models import Conteudo, NoFluxo
from app.core.serializers import no_fluxo_dict

TIPOS = ("MENU", "RESPOSTA", "ATENDENTE")
MAX_TITULO = 24
# Lista do WhatsApp: até 10 linhas. Nos submenus o bot acrescenta "Voltar",
# então sobram 9 para as opções.
MAX_OPCOES_RAIZ = 10
MAX_OPCOES_SUBMENU = 9


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


class _Erro(Exception):
    pass


def _int_ou_none(dados: dict, campo: str):
    valor = dados.get(campo)
    if valor is None or valor == "":
        return None
    if isinstance(valor, bool):
        raise _Erro(f"{campo} must be an integer")
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise _Erro(f"{campo} must be an integer")


def _ancestral_de(candidato_pai: NoFluxo, no_id: int) -> bool:
    """True se no_id aparece na cadeia de pais de candidato_pai (ou é ele)."""
    vistos = set()
    atual = candidato_pai
    while atual is not None and atual.id not in vistos:
        if atual.id == no_id:
            return True
        vistos.add(atual.id)
        atual = db.session.get(NoFluxo, atual.parent_id) if atual.parent_id else None
    return False


def _resolver(dados: dict, no: NoFluxo | None = None) -> dict:
    """Junta o estado atual do nó com as mudanças pedidas e valida o resultado
    final, para nunca mandar ao banco algo que viole os CHECKs."""
    final = {}

    # título
    if "titulo" in dados or no is None:
        titulo = (dados.get("titulo") or "").strip()
        if not titulo:
            raise _Erro("titulo is required")
        if len(titulo) > MAX_TITULO:
            raise _Erro(f"titulo must be at most {MAX_TITULO} characters")
        final["titulo"] = titulo

    # tipo e conteúdo
    tipo = dados.get("tipo", no.tipo if no else None)
    if tipo not in TIPOS:
        raise _Erro("tipo must be MENU, RESPOSTA or ATENDENTE")
    if "conteudo_id" in dados:
        conteudo_id = _int_ou_none(dados, "conteudo_id")
    else:
        conteudo_id = no.conteudo_id if (no and tipo == "RESPOSTA") else None
    if tipo == "RESPOSTA":
        if conteudo_id is None:
            raise _Erro("conteudo_id is required when tipo=RESPOSTA")
        if not db.session.get(Conteudo, conteudo_id):
            raise _Erro("Unknown conteudo_id")
    elif conteudo_id is not None:
        raise _Erro("conteudo_id must be empty unless tipo=RESPOSTA")
    if no is not None and no.tipo == "MENU" and tipo != "MENU":
        if any(f.ativo for f in no.filhos):
            raise _Erro("MENU com opções ativas não pode mudar de tipo; desative ou mova as opções antes")
    final["tipo"] = tipo
    final["conteudo_id"] = conteudo_id

    # pai (sem ciclos, e só MENU pode ter filhos)
    if "parent_id" in dados:
        parent_id = _int_ou_none(dados, "parent_id")
    else:
        parent_id = no.parent_id if no else None
    if parent_id is not None:
        pai = db.session.get(NoFluxo, parent_id)
        if not pai:
            raise _Erro("Unknown parent_id")
        if pai.tipo != "MENU":
            raise _Erro("parent_id must reference a MENU node")
        if no is not None and _ancestral_de(pai, no.id):
            raise _Erro("parent_id cannot be the node itself or one of its descendants")
    final["parent_id"] = parent_id

    # ordem e ativo
    if "ordem" in dados or no is None:
        final["ordem"] = _int_ou_none(dados, "ordem") or 0
    ativo = bool(dados["ativo"]) if "ativo" in dados else (no.ativo if no else True)
    final["ativo"] = ativo

    # limite de opções por menu
    entrando = ativo and (no is None or not no.ativo or parent_id != no.parent_id)
    if entrando:
        irmaos = NoFluxo.query.filter(NoFluxo.ativo.is_(True))
        irmaos = (
            irmaos.filter(NoFluxo.parent_id.is_(None))
            if parent_id is None
            else irmaos.filter(NoFluxo.parent_id == parent_id)
        )
        if no is not None:
            irmaos = irmaos.filter(NoFluxo.id != no.id)
        limite = MAX_OPCOES_RAIZ if parent_id is None else MAX_OPCOES_SUBMENU
        if irmaos.count() >= limite:
            raise _Erro(f"este menu já tem o máximo de {limite} opções ativas")

    return final


def criar(dados: dict, autor_id: int) -> ResultDTO:
    try:
        valores = _resolver(dados)
    except _Erro as e:
        return ResultDTO.bad_request(str(e))

    no = NoFluxo(**valores)
    db.session.add(no)
    db.session.flush()
    registrar(autor_id, "CRIOU_NO_FLUXO", "no_fluxo", no.id)
    db.session.commit()
    return ResultDTO.created(no_fluxo_dict(no))


def atualizar(no_id: int, dados: dict, autor_id: int) -> ResultDTO:
    no = db.session.get(NoFluxo, no_id)
    if not no:
        return ResultDTO.not_found("NoFluxo not found")

    try:
        valores = _resolver(dados, no)
    except _Erro as e:
        return ResultDTO.bad_request(str(e))

    for campo, valor in valores.items():
        setattr(no, campo, valor)

    registrar(autor_id, "ATUALIZOU_NO_FLUXO", "no_fluxo", no.id)
    db.session.commit()
    return ResultDTO.ok(no_fluxo_dict(no))


def desativar(no_id: int, autor_id: int) -> ResultDTO:
    no = db.session.get(NoFluxo, no_id)
    if not no:
        return ResultDTO.not_found("NoFluxo not found")
    no.ativo = False
    registrar(autor_id, "DESATIVOU_NO_FLUXO", "no_fluxo", no.id)
    db.session.commit()
    return ResultDTO.ok(no_fluxo_dict(no))
