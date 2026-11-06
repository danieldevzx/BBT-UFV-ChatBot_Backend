import sqlite3

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()

# Versão de schema que este código espera (PRAGMA user_version do chatbot.db).
SCHEMA_VERSION = 1


@event.listens_for(Engine, "connect")
def _configurar_sqlite(dbapi_conn, _):
    """Roda em TODA conexão nova: o SQLite não guarda estas opções no arquivo
    (exceto journal_mode) e não aplica chaves estrangeiras por padrão."""
    if not isinstance(dbapi_conn, sqlite3.Connection):
        return
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON")
    cur.execute("PRAGMA busy_timeout = 5000")
    cur.execute("PRAGMA journal_mode = WAL")
    cur.execute("PRAGMA synchronous = NORMAL")
    cur.close()
