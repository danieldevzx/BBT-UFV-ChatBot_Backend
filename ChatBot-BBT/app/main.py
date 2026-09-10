from agent import ask_agent


print("===================================")
print("   Chatbot da Biblioteca - PoC")
print("===================================")
print("Digite 'sair' para encerrar.\n")


while True:

    question = input("Você: ")

    if question.lower() == "sair":
        break

    answer = ask_agent(question)

    print(f"\nBot: {answer}\n")
    