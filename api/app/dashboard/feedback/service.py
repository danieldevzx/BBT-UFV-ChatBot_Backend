from app.core.database.extensions import db
from app.core.dtos import ResultDTO
from app.core.models import Feedback, NoFluxo
from app.core.serializers import feedback_dict


def listar(no_fluxo_id=None) -> ResultDTO:
    query = Feedback.query
    if no_fluxo_id is not None:
        query = query.filter_by(no_fluxo_id=no_fluxo_id)
    return ResultDTO.ok(
        [feedback_dict(f) for f in query.order_by(Feedback.criado_em.desc()).all()]
    )


def criar(dados: dict) -> ResultDTO:
    no_fluxo_id = dados.get("no_fluxo_id")
    if no_fluxo_id is None:
        return ResultDTO.bad_request("no_fluxo_id is required")
    if not db.session.get(NoFluxo, no_fluxo_id):
        return ResultDTO.bad_request("Unknown no_fluxo_id")

    feedback = Feedback(
        no_fluxo_id=no_fluxo_id,
        util=dados.get("util"),
        comentario=dados.get("comentario"),
    )
    db.session.add(feedback)
    db.session.commit()
    return ResultDTO.created(feedback_dict(feedback))
