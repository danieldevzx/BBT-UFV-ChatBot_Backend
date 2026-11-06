"""Navegação na árvore real do chatbot.db (18 nós do seed)."""
from app.bot import responder
from app.core.database.extensions import db
from app.core.models import Conteudo
from tests.base import BaseTestCase


class FlowTestCase(BaseTestCase):
    def test_menu_inicial_do_banco(self):
        acao = responder.acao_inicial()
        self.assertEqual(acao["tipo"], "MENU")
        self.assertTrue(acao["body"].startswith("Olá! Sou o assistente virtual da Biblioteca"))
        self.assertEqual(
            [n.titulo for n in acao["opcoes"]],
            [
                "Multas", "Renovação de livros", "Login e senha Sapiens",
                "Pesquisar no acervo", "Horários e contatos", "Biblioteca das Coisas",
                "Minha Biblioteca", "Nada Consta", "Falar com atendente",
            ],
        )
        self.assertIsNone(acao["voltar"])

    def test_submenu_tem_voltar(self):
        acao = responder.acao_no(1)  # Multas
        self.assertEqual(acao["tipo"], "MENU")
        self.assertEqual(len(acao["opcoes"]), 3)
        self.assertEqual(acao["voltar"], responder.NAV_INICIO)

    def test_resposta(self):
        acao = responder.acao_no(10)  # Valores das multas
        self.assertEqual(acao["tipo"], "RESPOSTA")
        self.assertTrue(acao["body"].startswith("Veja como funcionam as multas"))

    def test_atendente(self):
        acao = responder.acao_no(9)
        self.assertEqual(acao["tipo"], "ATENDENTE")
        self.assertTrue(acao["body"].startswith("Certo! Vou encaminhar você"))

    def test_no_inexistente(self):
        self.assertIsNone(responder.acao_no(999))

    def test_conteudo_desativado_esconde_a_opcao(self):
        db.session.get(Conteudo, 3).ativo = False  # Como renovar livros (nó 2)
        db.session.commit()
        titulos = [n.titulo for n in responder.acao_inicial()["opcoes"]]
        self.assertNotIn("Renovação de livros", titulos)
        self.assertIsNone(responder.acao_no(2))

    def test_textos_do_config_bot(self):
        self.assertTrue(responder.fallback().startswith("Não entendi sua mensagem"))
        self.assertEqual(responder.menu_botao(), "Ver opções")
        self.assertEqual(responder.feedback_pergunta(), "Essa resposta te ajudou?")
        self.assertEqual(
            responder.resposta_feedback(7),
            [("feedback:1:7", "Ajudou"), ("feedback:0:7", "Não ajudou")],
        )
        self.assertEqual(responder.botao_menu_inicial(), ("inicio", "Menu inicial"))
