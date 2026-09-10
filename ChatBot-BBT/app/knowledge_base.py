from pathlib import Path


def load_knowledge_base():
    path = Path("data/biblioteca.txt")

    with open(path, "r", encoding="utf-8") as file:
        return file.read()