from datetime import datetime, timezone

from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator


def utcnow():
    return datetime.now(timezone.utc)


class IsoDateTime(TypeDecorator):
    """Data/hora gravada como TEXT no formato do chatbot.db:
    2026-11-05T14:03:22.517Z (UTC, milissegundos, sufixo Z).

    É o mesmo formato dos defaults do sqlite_schema.sql, então as linhas
    criadas pelo banco e pelo backend ordenam corretamente como texto.
    Na leitura, aceita também o formato antigo do SQLAlchemy
    ("2026-11-05 14:03:22.517000") e devolve sempre datetime com fuso UTC.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, str):
            value = self._parse(value)
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        value = value.astimezone(timezone.utc)
        return value.strftime("%Y-%m-%dT%H:%M:%S.") + f"{value.microsecond // 1000:03d}Z"

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return self._parse(value)

    @staticmethod
    def _parse(texto: str) -> datetime:
        texto = texto.strip().replace(" ", "T", 1)
        if texto.endswith("Z"):
            texto = texto[:-1] + "+00:00"
        dt = datetime.fromisoformat(texto)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
