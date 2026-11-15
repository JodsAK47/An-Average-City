"""Criação do chefe exclusivo do desafio nos esgotos."""

from Entidades.Inimigo import Inimigo
from Gameplay.GeracaoFases import BANCO_INIMIGOS


def criar_david(x=740, y=400):
    dados = next(template for template in BANCO_INIMIGOS if template.get("nome") == "David Martins")
    david = Inimigo(
        x=x,
        y=y,
        vida_maxima=dados["max_hp"],
        nome_imagem=dados["arquivo_imagem"],
        nome=dados["nome"],
        ataques=list(dados["ataques"]),
        xp=dados["xp"],
        atributos=dict(dados["atributos"]),
        max_mp=dados["max_mp"],
        tipo=dados["tipo"],
        classe=dados["classe"],
    )
    david.verso = dados["verso"]
    david.especial = True
    david.mp = david.max_mp
    return david
