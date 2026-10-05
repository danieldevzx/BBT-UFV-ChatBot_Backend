from app.core.models import ConfigBot, NoFluxo


def listar_filhos(parent_id=None):
    return (
        NoFluxo.query.filter_by(ativo=True, parent_id=parent_id)
        .order_by(NoFluxo.ordem, NoFluxo.id)
        .all()
    )


def obter_no(no_id):
    return NoFluxo.query.filter_by(id=no_id, ativo=True).first()


def obter_config(chave, default=None):
    item = ConfigBot.query.filter_by(chave=chave).first()
    return item.valor if item else default
