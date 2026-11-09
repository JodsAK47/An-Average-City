import os
import sys
import json
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "An Average City"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
if not pygame.get_init():
    pygame.init()
pygame.display.set_mode((100, 100))

from Sistemas.Recursos import caminho_dados, caminho_imagem
from Entidades.Minion import (
    BANCO_MINIONS,
    BANCO_MINIONS_PERSONAGEM,
    BANCO_MINIONS_INIMIGOS,
    criar_minion,
    Minion
)
from Entidades.Personagem import Personagem
from Entidades.Inimigo import Inimigo


class TestJsonMinionsPersonagemEInimigos(unittest.TestCase):
    def test_arquivo_minions_personagem_valido(self):
        """Verifica se minions_personagem.json existe e contém todos os minions do jogador com dados válidos."""
        p_path = caminho_dados("minions_personagem.json")
        self.assertTrue(os.path.exists(p_path), f"Arquivo não encontrado: {p_path}")

        with open(p_path, "r", encoding="utf-8") as f:
            minions_p = json.load(f)

        esperados = [
            "Abelha Soldado",
            "Pássaro Olhudo",
            "Torreta Sentinela",
            "Drone Caçador",
            "Cão Divino",
            "Nue",
            "Mahoraga"
        ]
        for nome in esperados:
            self.assertIn(nome, minions_p, f"Minion de personagem '{nome}' ausente em minions_personagem.json")
            dados = minions_p[nome]
            self.assertEqual(dados.get("nome"), nome)
            self.assertIn("max_hp", dados)
            self.assertIn("max_mp", dados)
            self.assertIn("atributos", dados)
            self.assertIn("ataques", dados)
            self.assertGreater(len(dados["ataques"]), 0)

            # Verifica existência do sprite
            img = dados.get("arquivo_imagem")
            self.assertTrue(bool(img))
            caminho_res = caminho_imagem(img)
            self.assertTrue(os.path.exists(caminho_res), f"Sprite '{img}' não encontrado em {caminho_res}")

    def test_arquivo_minions_inimigos_valido(self):
        """Verifica se minions_inimigos.json existe e contém minions de inimigos com dados válidos."""
        i_path = caminho_dados("minions_inimigos.json")
        self.assertTrue(os.path.exists(i_path), f"Arquivo não encontrado: {i_path}")

        with open(i_path, "r", encoding="utf-8") as f:
            minions_i = json.load(f)

        esperados = [
            "Pequeno Santuário",
            "Fera do Breu",
            "Mãos das Sombras",
            "Tentáculos das Trevas",
            "Enxame Noturno",
            "Torreta Inimiga",
            "Pássaro Sombrio"
        ]
        for nome in esperados:
            self.assertIn(nome, minions_i, f"Minion inimigo '{nome}' ausente em minions_inimigos.json")
            dados = minions_i[nome]
            self.assertEqual(dados.get("nome"), nome)
            self.assertIn("max_hp", dados)
            self.assertIn("max_mp", dados)
            self.assertIn("atributos", dados)
            self.assertIn("ataques", dados)
            self.assertGreater(len(dados["ataques"]), 0)

            # Verifica existência do sprite
            img = dados.get("arquivo_imagem")
            self.assertTrue(bool(img))
            caminho_res = caminho_imagem(img)
            self.assertTrue(os.path.exists(caminho_res), f"Sprite '{img}' não encontrado em {caminho_res}")

    def test_bancos_carregados_no_minion(self):
        """Verifica se Minion.py carrega e expõe BANCO_MINIONS_PERSONAGEM e BANCO_MINIONS_INIMIGOS separadamente."""
        self.assertGreaterEqual(len(BANCO_MINIONS_PERSONAGEM), 7)
        self.assertGreaterEqual(len(BANCO_MINIONS_INIMIGOS), 7)

        # Cão Divino é do jogador
        self.assertIn("Cão Divino", BANCO_MINIONS_PERSONAGEM)
        # Pequeno Santuário e Fera do Breu são de inimigos
        self.assertIn("Pequeno Santuário", BANCO_MINIONS_INIMIGOS)
        self.assertIn("Fera do Breu", BANCO_MINIONS_INIMIGOS)

        # BANCO_MINIONS geral unifica ambos
        self.assertIn("Cão Divino", BANCO_MINIONS)
        self.assertIn("Pequeno Santuário", BANCO_MINIONS)
        self.assertIn("Fera do Breu", BANCO_MINIONS)

    def test_criar_minion_com_dono_jogador_e_inimigo(self):
        """Verifica se criar_minion associa corretamente o lado do dono ao minion."""
        from Entidades.Personagem import personagem
        inimigo = Inimigo(700, 300, 100, "Inimigo1.png", nome="Boss")

        minion_p = criar_minion("Cão Divino", dono=personagem)
        self.assertEqual(minion_p.lado, "jogador")
        self.assertTrue(minion_p.eh_do_jogador)
        self.assertFalse(minion_p.eh_do_inimigo)

        minion_i = criar_minion("Fera do Breu", dono=inimigo)
        self.assertEqual(minion_i.lado, "inimigo")
        self.assertFalse(minion_i.eh_do_jogador)
        self.assertTrue(minion_i.eh_do_inimigo)


if __name__ == "__main__":
    unittest.main()
