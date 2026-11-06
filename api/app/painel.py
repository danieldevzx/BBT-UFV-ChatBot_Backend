"""Serve o painel web (front) pelo próprio Flask.

A página e a API ficam no mesmo endereço, então o navegador não precisa de
CORS: abra http://<servidor>:5000/ e a página chama /api/dashboard/...
"""
from pathlib import Path

from flask import Blueprint, abort, send_from_directory

PASTA_FRONT = Path(__file__).resolve().parent.parent / "frontend"
PAGINA = "gestor-fluxos.html"
ARQUIVOS = {"logo.png", "capivara_UFV.png"}

painel_bp = Blueprint("painel", __name__)


@painel_bp.route("/")
def index():
    return send_from_directory(PASTA_FRONT, PAGINA)


@painel_bp.route("/<nome>")
def arquivo(nome):
    if nome not in ARQUIVOS:
        abort(404)
    return send_from_directory(PASTA_FRONT, nome)
