import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Garantir que o diretório base do jogo esteja no sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "An Average City"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import pygame
if not pygame.get_init():
    pygame.init()

from Entidades.Personagem import Personagem
from Entidades.Inimigo import Inimigo
from Telas.TelaCombate import TelaCombate, personagem
from Telas.TelaGameOver import GerenciadorGameOver
from Telas.TelaVitoria import GerenciadorVitoria


class TestCutsceneDerrotaEPontos(unittest.TestCase):
    def setUp(self):
        self.superficie = pygame.Surface((1000, 700))
        self.combate = TelaCombate(self.superficie)
        self.personagem = personagem
        self.combate.pontos_jogo = 350

    def test_derrota_para_inimigo_comum_nao_marca_perdeu_para_chefe(self):
        """Ao ser derrotado por inimigos comuns, perdeu_para_chefe deve ser False."""
        inimigo_comum = Inimigo(700, 300, 50, "Inimigo Sobrevivente 1.png", nome="Zumbi", tipo="fraco")
        inimigo_comum.hp = 50
        self.personagem.hp = 0

        self.combate.ordem_turnos = [self.personagem, inimigo_comum]
        self.combate.derrota_processada = False

        self.combate.atualizar((0, 0), (False, False, False))
        
        self.assertFalse(self.combate.perdeu_para_chefe)
        self.assertIsNone(self.combate.ultimo_chefe_combate)
        # Pontos devem ser preservados e NÃO zerados!
        self.assertEqual(self.combate.pontos_jogo, 350)

    def test_derrota_para_chefe_marca_perdeu_para_chefe(self):
        """Ao ser derrotado por um chefe vivo, perdeu_para_chefe deve ser True."""
        chefe = Inimigo(700, 300, 500, "Sukuna.png", nome="Sukuna", tipo="chefe")
        chefe.hp = 500
        self.personagem.hp = 0

        self.combate.ordem_turnos = [self.personagem, chefe]
        self.combate.derrota_processada = False

        self.combate.atualizar((0, 0), (False, False, False))

        self.assertTrue(self.combate.perdeu_para_chefe)
        self.assertEqual(self.combate.ultimo_chefe_combate, "Sukuna")
        self.assertEqual(self.combate.pontos_jogo, 350)

    def test_derrota_com_chefe_morto_mas_minion_vivo_nao_marca_chefe(self):
        """Se o chefe já estava morto (hp<=0) e restava apenas um minion que matou o player, não perdeu para o chefe."""
        chefe_morto = Inimigo(700, 300, 500, "Sukuna.png", nome="Sukuna", tipo="chefe")
        chefe_morto.hp = 0
        minion_vivo = Inimigo(750, 320, 30, "Inimigo Sobrevivente 1.png", nome="Lacaio", tipo="fraco")
        minion_vivo.hp = 30
        self.personagem.hp = 0

        self.combate.ordem_turnos = [self.personagem, chefe_morto, minion_vivo]
        self.combate.derrota_processada = False

        self.combate.atualizar((0, 0), (False, False, False))

        self.assertFalse(self.combate.perdeu_para_chefe)
        self.assertIsNone(self.combate.ultimo_chefe_combate)
        self.assertEqual(self.combate.pontos_jogo, 350)

    def test_tela_game_over_exibe_pontos(self):
        """TelaGameOver deve receber e desenhar os pontos corretamente."""
        game_over = GerenciadorGameOver(self.superficie)
        game_over.pontos = 1250
        
        # Testar chamada de desenho
        try:
            game_over.desenhar()
        except Exception as e:
            self.fail(f"desenhar() da TelaGameOver lançou exceção: {e}")

        self.assertEqual(game_over.pontos, 1250)

    def test_tela_vitoria_exibe_pontos(self):
        """TelaVitoria deve possuir atributo pontos e desenhar sem erro."""
        vitoria = GerenciadorVitoria(self.superficie)
        self.assertEqual(vitoria.pontos, 0)
        vitoria.pontos = 2500

        try:
            vitoria.desenhar()
        except Exception as e:
            self.fail(f"desenhar() da TelaVitoria lançou exceção: {e}")

        self.assertEqual(vitoria.pontos, 2500)


if __name__ == "__main__":
    unittest.main()
