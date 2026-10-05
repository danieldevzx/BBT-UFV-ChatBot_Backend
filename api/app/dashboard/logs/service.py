from app.core.dtos import ResultDTO
from app.core.models import Log
from app.core.serializers import log_dict


def listar() -> ResultDTO:
    logs = Log.query.order_by(Log.criado_em.desc()).limit(500).all()
    return ResultDTO.ok([log_dict(l) for l in logs])
