from openai import OpenAI
from knowledge_base import load_knowledge_base

client = OpenAI()

knowledge_base = load_knowledge_base()


def ask_agent(question):

    prompt = f"""
Você é o assistente virtual da biblioteca.

Sua função é responder dúvidas dos alunos de maneira
natural, clara e amigável.

Use SOMENTE as informações presentes na base de conhecimento
abaixo.

Se a informação necessária não estiver na base, diga que não
possui essa informação e oriente o usuário a entrar em contato
com um atendente.

BASE DE CONHECIMENTO:

{knowledge_base}


PERGUNTA DO USUÁRIO:

{question}
"""

    response = client.responses.create(
        model="gpt-5",
        input=prompt
    )

    return response.output_text