# -*- coding: utf-8 -*-
import os
import sys
import random
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
DIRETORIO_RAIZ = os.path.abspath(os.path.join(DIRETORIO_ATUAL, ".."))
if DIRETORIO_RAIZ not in sys.path:
    sys.path.insert(0, DIRETORIO_RAIZ)
DIRETORIO_PROJETO = os.path.join(DIRETORIO_RAIZ, "An Average City")
if DIRETORIO_PROJETO not in sys.path:
    sys.path.insert(0, DIRETORIO_PROJETO)

import pygame
if not pygame.get_init():
    pygame.init()
pygame.display.set_mode((1000, 768))

from Entidades.Personagem import personagem
from Gameplay.GeracaoFases import GeradorFase, obter_regras_fase
from Telas.TelaCombate import TelaCombate


class TestBalanceamento2Jogadores(unittest.TestCase):
    def setUp(self):
        self.tela = pygame.display.get_surface()
        self.gerador = GeradorFase(1)

    def test_regras_quantidade_2p(self):
        """Modo 2P deve exigir no mínimo 2 inimigos nas fases 1-3 e 3 nas fases 4-9."""
        for fase in (1, 2, 3):
            min_q, max_q, _ = obter_regras_fase(fase, duas_pessoas=True)
            self.assertEqual((min_q, max_q), (2, 4))
        for fase in (4, 5, 6, 7, 8, 9):
            min_q, max_q, _ = obter_regras_fase(fase, duas_pessoas=True)
            self.assertEqual((min_q, max_q), (3, 4))

    def test_inimigos_e_chefe_2p_escalam_acima_do_solo(self):
        """Inimigos e chefe gerados com duas_pessoas=True têm HP e atributos superiores ao modo solo."""
        rng_state = random.getstate()
        try:
            random.seed(101)
            inimigos_1p = self.gerador.gerar_inimigos_aleatorios(fase_num=5, quantidade=3, verso="Feiticeiro", duas_pessoas=False)
            random.seed(101)
            inimigos_2p = self.gerador.gerar_inimigos_aleatorios(fase_num=5, quantidade=3, verso="Feiticeiro", duas_pessoas=True)

            soma_hp_1p = sum(i.max_hp for i in inimigos_1p)
            soma_hp_2p = sum(i.max_hp for i in inimigos_2p)
            self.assertGreater(soma_hp_2p, soma_hp_1p)

            random.seed(202)
            chefe_1p = self.gerador.gerar_chefe_verso("Feiticeiro", duas_pessoas=False)
            random.seed(202)
            chefe_2p = self.gerador.gerar_chefe_verso("Feiticeiro", duas_pessoas=True)

            self.assertGreater(chefe_2p.max_hp, chefe_1p.max_hp)
            self.assertGreater(chefe_2p.max_mp, chefe_1p.max_mp)
            self.assertGreater(sum(chefe_2p.atributos.values()), sum(chefe_1p.atributos.values()))
        finally:
            random.setstate(rng_state)

    def test_recuperacao_pos_batalha_reduzida_em_2p_sem_dormir(self):
        """Sem dormir, a cura gratuita pós-batalha é menor no modo 2P (20% HP, 2 MP) que no solo (30% HP, 3 MP)."""
        combate = TelaCombate(self.tela)
        personagem.max_hp = 100
        personagem.hp = 50
        personagem.max_mp = 20
        personagem.mp = 5

        combate.duas_pessoas = False
        info_1p = combate.recuperar_apos_batalha(dormir=False)
        self.assertEqual(info_1p["percentual_hp"], 30)
        self.assertEqual(info_1p["pontos_mp"], 3)

        personagem.hp = 50
        personagem.mp = 5
        combate.duas_pessoas = True
        info_2p = combate.recuperar_apos_batalha(dormir=False)
        self.assertEqual(info_2p["percentual_hp"], 20)
        self.assertEqual(info_2p["pontos_mp"], 2)


if __name__ == "__main__":
    unittest.main()
