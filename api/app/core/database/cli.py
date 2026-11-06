"""Comandos de banco:  flask db init | upgrade | version | backup <destino>

Substituem o Flask-Migrate. A fonte da verdade é db/sqlite_schema.sql
(versão 0) mais os arquivos db/migrations/NNN_*.sql, aplicados em ordem
conforme o PRAGMA user_version do arquivo.
"""
import re
import sqlite3
from pathlib import Path

import click
from flask import current_app
from flask.cli import AppGroup

from .extensions import SCHEMA_VERSION

db_cli = AppGroup("db", help="Banco SQLite (chatbot.db).")


def _conectar(caminho: str) -> sqlite3.Connection:
    conn = sqlite3.connect(caminho)
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def versao(conn: sqlite3.Connection) -> int:
    return conn.execute("PRAGMA user_version").fetchone()[0]


def migracoes(pasta: str) -> list[tuple[int, Path]]:
    itens = []
    for arq in sorted(Path(pasta).glob("*.sql")):
        m = re.match(r"^(\d+)_", arq.name)
        if m:
            itens.append((int(m.group(1)), arq))
    return itens


def aplicar_migracoes(conn: sqlite3.Connection, pasta: str) -> list[str]:
    aplicadas = []
    atual = versao(conn)
    for numero, arq in migracoes(pasta):
        if numero <= atual:
            continue
        conn.executescript(arq.read_text(encoding="utf-8"))
        nova = versao(conn)
        if nova != numero:
            raise click.ClickException(
                f"{arq.name} deveria deixar user_version = {numero}, mas deixou {nova}"
            )
        problemas = conn.execute("PRAGMA foreign_key_check").fetchall()
        if problemas:
            raise click.ClickException(f"Violação de chave estrangeira após {arq.name}: {problemas}")
        aplicadas.append(arq.name)
        atual = nova
    return aplicadas


def criar_banco(caminho: str, schema: str, pasta_migracoes: str) -> None:
    conn = _conectar(caminho)
    try:
        conn.executescript(Path(schema).read_text(encoding="utf-8"))
        aplicar_migracoes(conn, pasta_migracoes)
    finally:
        conn.close()


@db_cli.command("init")
@click.option("--force", is_flag=True, help="Apaga o arquivo existente antes de criar.")
def init_cmd(force):
    """Cria o chatbot.db a partir do sqlite_schema.sql + migrações."""
    caminho = Path(current_app.config["DB_PATH"])
    if caminho.exists():
        if not force:
            raise click.ClickException(f"{caminho} já existe. Use 'flask db upgrade' ou --force.")
        for sufixo in ("", "-wal", "-shm"):
            Path(f"{caminho}{sufixo}").unlink(missing_ok=True)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    criar_banco(str(caminho), current_app.config["DB_SCHEMA_PATH"], current_app.config["DB_MIGRATIONS_DIR"])
    click.echo(f"Banco criado em {caminho} (schema v{SCHEMA_VERSION}).")


@db_cli.command("upgrade")
def upgrade_cmd():
    """Aplica as migrações pendentes no chatbot.db."""
    conn = _conectar(current_app.config["DB_PATH"])
    try:
        antes = versao(conn)
        aplicadas = aplicar_migracoes(conn, current_app.config["DB_MIGRATIONS_DIR"])
        if aplicadas:
            click.echo(f"v{antes} -> v{versao(conn)}: " + ", ".join(aplicadas))
        else:
            click.echo(f"Nada a aplicar (schema v{antes}).")
    finally:
        conn.close()


@db_cli.command("version")
def version_cmd():
    """Mostra a versão do schema no arquivo e a esperada pelo código."""
    conn = _conectar(current_app.config["DB_PATH"])
    try:
        click.echo(f"arquivo: v{versao(conn)} | código espera: v{SCHEMA_VERSION}")
    finally:
        conn.close()


@db_cli.command("backup")
@click.argument("destino")
def backup_cmd(destino):
    """Cópia consistente com a API de backup do SQLite (segura com o app rodando)."""
    origem = _conectar(current_app.config["DB_PATH"])
    alvo = sqlite3.connect(destino)
    try:
        with alvo:
            origem.backup(alvo)
    finally:
        alvo.close()
        origem.close()
    click.echo(f"Backup gravado em {destino}")
