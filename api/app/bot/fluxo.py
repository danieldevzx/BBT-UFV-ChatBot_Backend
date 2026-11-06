from sqlalchemy import or_

from app.core.models import ConfigBot, Conteudo, NoFluxo


def _visiveis():
    """Nós ativos; RESPOSTA só aparece se o conteúdo dela também estiver ativo."""
    return (
        NoFluxo.query.outerjoin(Conteudo, NoFluxo.conteudo_id == Conteudo.id)
        .filter(NoFluxo.ativo.is_(True))
        .filter(or_(NoFluxo.tipo != "RESPOSTA", Conteudo.ativo.is_(True)))
    )


def listar_filhos(parent_id=None):
    query = _visiveis()
    query = (
        query.filter(NoFluxo.parent_id.is_(None))
        if parent_id is None
        else query.filter(NoFluxo.parent_id == parent_id)
    )
    return query.order_by(NoFluxo.ordem, NoFluxo.id).all()


def obter_no(no_id):
    return _visiveis().filter(NoFluxo.id == no_id).first()


def obter_config(chave, default=None):
    item = ConfigBot.query.filter_by(chave=chave).first()
    return item.valor if item else default
