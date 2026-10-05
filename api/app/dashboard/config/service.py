from app.core.audit import registrar
from app.core.database.extensions import db
from app.core.dtos import ResultDTO
from app.core.models import ConfigBot
from app.core.serializers import config_bot_dict


def listar() -> ResultDTO:
    itens = ConfigBot.query.order_by(ConfigBot.chave).all()
    return ResultDTO.ok([config_bot_dict(i) for i in itens])


def obter(chave: str) -> ResultDTO:
    item = db.session.get(ConfigBot, chave)
    if not item:
        return ResultDTO.not_found("Config not found")
    return ResultDTO.ok(config_bot_dict(item))


def upsert(chave: str, dados: dict, autor_id: str) -> ResultDTO:
    valor = dados.get("valor")
    if valor is None:
        return ResultDTO.bad_request("valor is required")

    item = db.session.get(ConfigBot, chave)
    acao = "ATUALIZOU_CONFIG" if item else "CRIOU_CONFIG"
    if item:
        item.valor = valor
    else:
        item = ConfigBot(chave=chave, valor=valor)
        db.session.add(item)
    registrar(autor_id, acao, "config_bot", None)
    db.session.commit()
    return ResultDTO.ok(config_bot_dict(item))


def remover(chave: str, autor_id: str) -> ResultDTO:
    item = db.session.get(ConfigBot, chave)
    if not item:
        return ResultDTO.not_found("Config not found")
    db.session.delete(item)
    registrar(autor_id, "REMOVEU_CONFIG", "config_bot", None)
    db.session.commit()
    return ResultDTO.ok({"chave": chave})
