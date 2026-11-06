import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

API_DIR = Path(__file__).resolve().parent.parent
DB_DIR = API_DIR / "db"


def _bool(nome: str, padrao: bool) -> bool:
    valor = os.getenv(nome)
    if valor is None:
        return padrao
    return valor.strip().lower() in ("1", "true", "yes", "sim")


def _caminho_banco() -> Path:
    caminho = Path(os.getenv("DB_PATH", DB_DIR / "chatbot.db"))
    return caminho if caminho.is_absolute() else (API_DIR / caminho).resolve()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")

    # ─── Banco: arquivo SQLite (chatbot.db) ───────────────────────────
    DB_PATH = str(_caminho_banco())
    DB_SCHEMA_PATH = str(DB_DIR / "sqlite_schema.sql")
    DB_MIGRATIONS_DIR = str(DB_DIR / "migrations")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"timeout": 15}}
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key-troque-em-producao")

    # ─── WhatsApp ──────────────────────────────────────────────────────
    WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
    WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "bbt_verify")
    WHATSAPP_APP_SECRET = os.getenv("WHATSAPP_APP_SECRET", "")
    # Em produção a assinatura da Meta é obrigatória. Só desligue em
    # desenvolvimento local (WHATSAPP_REQUIRE_SIGNATURE=false).
    WHATSAPP_REQUIRE_SIGNATURE = _bool("WHATSAPP_REQUIRE_SIGNATURE", True)

    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
