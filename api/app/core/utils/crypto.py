from cryptography.fernet import Fernet
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator


def _get_key() -> bytes:
    from flask import current_app
    key = current_app.config.get("ENCRYPTION_KEY", "")
    return key.encode() if key else b""


def encrypt(plain: str) -> str:
    return Fernet(_get_key()).encrypt(plain.encode()).decode()


def decrypt(cipher: str) -> str:
    return Fernet(_get_key()).decrypt(cipher.encode()).decode()


class EncryptedText(TypeDecorator):
    impl = Text

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return encrypt(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return decrypt(value)