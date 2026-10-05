from app.core.database.extensions import db
from app.core.models import Log


def registrar(usuario_id, acao, tabela_afetada=None, registro_id=None):
    db.session.add(
        Log(
            usuario_id=usuario_id,
            acao=acao,
            tabela_afetada=tabela_afetada,
            registro_id=registro_id,
        )
    )
