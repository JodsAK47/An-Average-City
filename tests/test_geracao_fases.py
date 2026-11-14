# -*- coding: utf-8 -*-
import os
import sys
import random
import unittest
from collections import Counter

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

from Gameplay.GeracaoFases import (
    GeradorFase,
    TOTAL_FASES_NORMAIS,
    TOTAL_PARTIDAS_JOGO,
    listar_inimigos_disponiveis,
    normalizar_categoria_inimigo,
    obter_regras_fase,
)
from Telas.TelaCombate import TelaCombate
from Telas.TelaGameOver import GerenciadorGameOver


class TestGeracaoFases(unittest.TestCase):
    def setUp(self):
        self.tela = pygame.display.get_surface()
        self.gerador = GeradorFase(1)

    def test_total_de_nove_fases_mais_chefe(self):
        """O jogo deve possuir 9 fases normais e a 10ª partida sendo o chefe."""
        self.assertEqual(TOTAL_FASES_NORMAIS, 9)
        self.assertEqual(TOTAL_PARTIDAS_JOGO, 10)
        combate = TelaCombate(self.tela)
        self.assertEqual(combate.total_partidas, 10)
        self.assertEqual(combate.partida_atual, 1)

        combate.configurar_classe("Feiticeiro", "Magia")
        for partida in range(1, 10):
            combate.partida_atual = partida
            combate.fase_numero = partida - 1
            combate.configurar_cenario("ignorar_evento")
            inimigos = [e for e in combate.ordem_turnos if combate.eh_inimigo(e)]
            self.assertGreaterEqual(len(inimigos), 1)
            self.assertTrue(all(normalizar_categoria_inimigo(e.tipo) != "chefe" for e in inimigos))

        # 10ª partida deve gerar o chefe
        combate.partida_atual = 10
        combate.fase_numero = 9
        combate.configurar_cenario("ignorar_evento")
        inimigos_boss = [e for e in combate.ordem_turnos if combate.eh_inimigo(e)]
        self.assertEqual(len(inimigos_boss), 1)
        self.assertEqual(normalizar_categoria_inimigo(inimigos_boss[0].tipo), "chefe")

    def _verificar_distribuicao_fase(self, fase, min_esperado, max_esperado, permitidas, ordem_preferencia):
        min_q, max_q, pesos = obter_regras_fase(fase)
        self.assertEqual((min_q, max_q), (min_esperado, max_esperado))
        self.assertEqual(set(pesos.keys()), permitidas)
        for maior, menor in zip(ordem_preferencia, ordem_preferencia[1:]):
            self.assertGreater(pesos[maior], pesos[menor])

        contagem_cats = Counter()
        quantidades_vistas = set()
        for verso in ("Feiticeiro", "Sobrevivente", "Agente"):
            templates = listar_inimigos_disponiveis(verso=verso)
            for _ in range(120):
                tmpl = self.gerador._sortear_template_por_fase(templates, pesos)
                cat = normalizar_categoria_inimigo(tmpl)
                self.assertIn(cat, permitidas)
                contagem_cats[cat] += 1
            for _ in range(25):
                inimigos = self.gerador.gerar_inimigos_aleatorios(fase_num=fase, verso=verso)
                quantidades_vistas.add(len(inimigos))
                self.assertGreaterEqual(len(inimigos), min_esperado)
                self.assertLessEqual(len(inimigos), max_esperado)
                for ini in inimigos:
                    self.assertIn(normalizar_categoria_inimigo(ini.tipo), permitidas)

        self.assertEqual(quantidades_vistas, set(range(min_esperado, max_esperado + 1)))
        for maior, menor in zip(ordem_preferencia, ordem_preferencia[1:]):
            self.assertGreater(contagem_cats[maior], contagem_cats[menor])
        for cat in permitidas:
            self.assertGreater(contagem_cats[cat], 0)

    def test_fases_1_a_3_pequenos_e_medios_entre_1_e_4_com_preferencia_menores(self):
        """Fases 1 a 3: 1 a 4 inimigos pequenos/médios, sem grandes, preferência aos pequenos."""
        rng_state = random.getstate()
        random.seed(12345)
        try:
            for fase in (1, 2, 3):
                self._verificar_distribuicao_fase(fase, 1, 4, {"pequeno", "medio"}, ["pequeno", "medio"])
        finally:
            random.setstate(rng_state)

    def test_fases_4_a_6_medios_pequenos_grandes_entre_2_e_4(self):
        """Fases 4 a 6: 2 a 4 inimigos médios/pequenos/grandes, preferência médios e menor chance grandes."""
        rng_state = random.getstate()
        random.seed(54321)
        try:
            for fase in (4, 5, 6):
                self._verificar_distribuicao_fase(fase, 2, 4, {"pequeno", "medio", "grande"}, ["medio", "pequeno", "grande"])
        finally:
            random.setstate(rng_state)

    def test_fases_7_a_9_medios_e_grandes_entre_2_e_4(self):
        """Fases 7 a 9: 2 a 4 inimigos médios/grandes, sem pequenos, preferência médios."""
        rng_state = random.getstate()
        random.seed(99999)
        try:
            for fase in (7, 8, 9):
                self._verificar_distribuicao_fase(fase, 2, 4, {"medio", "grande"}, ["medio", "grande"])
        finally:
            random.setstate(rng_state)

    def test_novos_jogos_geram_quantidades_e_composicoes_diferentes(self):
        """Cada início de jogo deve sortear novamente quantidade e seleção de inimigos."""
        combate = TelaCombate(self.tela)
        combate.configurar_classe("Sobrevivente", "Físico")

        assinaturas = set()
        quantidades = set()
        for _ in range(30):
            combate.reiniciar(forcar_novos_inimigos=True)
            inimigos = [e for e in combate.ordem_turnos if combate.eh_inimigo(e)]
            quantidades.add(len(inimigos))
            assinaturas.add(tuple(e.nome for e in inimigos))

        self.assertGreater(len(quantidades), 1, "A quantidade de inimigos no início do jogo deve variar.")
        self.assertGreater(len(assinaturas), 2, "Os inimigos selecionados no início do jogo devem variar.")

    def test_gameover_fundo_procedural_nao_trava_random_global(self):
        """Gerar fundo procedural de game over não deve resetar a semente global do random."""
        go = GerenciadorGameOver(self.tela)
        go._gerar_fundo_procedural("sobrevivente")
        seq1 = [random.randint(1, 10000) for _ in range(10)]
        go._gerar_fundo_procedural("sobrevivente")
        seq2 = [random.randint(1, 10000) for _ in range(10)]
        self.assertNotEqual(seq1, seq2)


if __name__ == "__main__":
    unittest.main()
