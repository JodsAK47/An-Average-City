# -*- coding: utf-8 -*-
import os
import sys
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

from Sistemas.Inventario import SistemaInventario, Equipamento


class TestInventarioTrocaPosicao(unittest.TestCase):
    def setUp(self):
        self.inv = SistemaInventario()

    def test_equipar_arma_sobre_outra_troca_de_posicao_sem_deletar(self):
        """Equipar arma da mochila por cima de outra arma deve trocar ambas de posição."""
        arma_equipada = Equipamento("Katana", {"For": 2}, categoria="arma")
        item_antes = Equipamento("Capacete A", {"Con": 1}, categoria="capacete")
        arma_mochila = Equipamento("Machado", {"For": 3}, categoria="arma")
        item_depois = Equipamento("Bota A", {"Agi": 1}, categoria="bota")

        self.inv.equipar(arma_equipada)
        self.inv.equipamentos_inventario = [item_antes, arma_mochila, item_depois]

        self.assertTrue(self.inv.equipar(arma_mochila))
        self.assertIs(self.inv.equipamento_slot, arma_mochila)
        # A arma antiga deve ocupar exatamente o índice 1 onde a nova estava
        self.assertEqual(self.inv.equipamentos_inventario, [item_antes, arma_equipada, item_depois])

    def test_equipar_armaduras_troca_exata_de_posicao(self):
        """Equipar capacete/peitoral/calca/bota da mochila troca exatamente de posição com o equipado."""
        casos = [
            ("capacete", "capacete_slot"),
            ("peitoral", "peitoral_slot"),
            ("calca", "calca_slot"),
            ("bota", "bota_slot"),
        ]
        for categoria, attr_slot in casos:
            with self.subTest(categoria=categoria):
                inv = SistemaInventario()
                antigo = Equipamento(f"{categoria} antigo", {"Con": 1}, categoria=categoria)
                pre_0 = Equipamento("Filler 0", {"For": 1}, categoria="arma")
                novo = Equipamento(f"{categoria} novo", {"Con": 3}, categoria=categoria)
                pos_2 = Equipamento("Filler 2", {"Agi": 1}, categoria="arma")

                inv.equipar(antigo)
                inv.equipamentos_inventario = [pre_0, novo, pos_2]

                self.assertTrue(inv.equipar(novo))
                self.assertIs(getattr(inv, attr_slot), novo)
                self.assertEqual(inv.equipamentos_inventario, [pre_0, antigo, pos_2])

    def test_equipar_arma_direta_preserva_arma_anterior_na_mochila(self):
        """Equipar um novo item diretamente (fora da mochila) sobre um slot ocupado guarda o antigo na mochila."""
        arma1 = Equipamento("Espada 1", {"For": 2}, categoria="arma")
        arma2 = Equipamento("Espada 2", {"For": 4}, categoria="arma")

        self.inv.equipar(arma1)
        self.inv.equipar(arma2)

        self.assertIs(self.inv.equipamento_slot, arma2)
        self.assertIn(arma1, self.inv.equipamentos_inventario)


if __name__ == "__main__":
    unittest.main()
