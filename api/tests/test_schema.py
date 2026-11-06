"""Garante que o código e o chatbot.db não voltem a divergir."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import inspect

from app.config import DB_DIR
from app.core.database.cli import criar_banco
from app.core.database.extensions import SCHEMA_VERSION, db
from tests.base import BANCO_REAL, BaseTestCase


def _schema(caminho):
    conn = sqlite3.connect(caminho)
    linhas = conn.execute(
        "select type, name, sql from sqlite_master "
        "where name not like 'sqlite_%' order by type, name"
    ).fetchall()
    versao = conn.execute("pragma user_version").fetchone()[0]
    conn.close()
    return linhas, versao


class SchemaTestCase(BaseTestCase):
    def test_versao_do_banco_bate_com_o_codigo(self):
        _, versao = _schema(BANCO_REAL)
        self.assertEqual(versao, SCHEMA_VERSION)

    def test_schema_sql_mais_migracoes_recria_o_chatbot_db(self):
        with tempfile.TemporaryDirectory() as tmp:
            novo = str(Path(tmp) / "novo.db")
            criar_banco(novo, str(DB_DIR / "sqlite_schema.sql"), str(DB_DIR / "migrations"))
            self.assertEqual(_schema(novo), _schema(BANCO_REAL))

    def test_models_batem_com_as_tabelas(self):
        insp = inspect(db.engine)
        for tabela in db.metadata.sorted_tables:
            colunas_banco = {c["name"]: c for c in insp.get_columns(tabela.name)}
            for coluna in tabela.columns:
                self.assertIn(coluna.name, colunas_banco, f"{tabela.name}.{coluna.name}")
                if coluna.primary_key:
                    continue
                self.assertEqual(
                    coluna.nullable,
                    colunas_banco[coluna.name]["nullable"],
                    f"nullable diferente em {tabela.name}.{coluna.name}",
                )
            for fk in tabela.foreign_keys:
                alvo = fk.column
                self.assertEqual(
                    str(fk.parent.type.python_type),
                    str(alvo.type.python_type),
                    f"tipo da FK {tabela.name}.{fk.parent.name} difere de {alvo.table.name}.{alvo.name}",
                )

    def test_pragmas_em_toda_conexao(self):
        self.assertEqual(self.sql("pragma foreign_keys")[0][0], 1)
        self.assertEqual(self.sql("pragma journal_mode")[0][0], "wal")

    def test_health(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["schema_version"], SCHEMA_VERSION)
