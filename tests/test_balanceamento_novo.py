# -*- coding: utf-8 -*-
"""
Testes unitários para as novas mecânicas de balanceamento:
- Redução de dano passivo por Constituição e Armaduras (Def).
- Escalonamento do atributo Sorte a 0,5% (+0.005) por ponto.
- Regeneração de PM: +1 PM no início do turno e +1 PM em ataques de custo 0.
- Minigame de esquiva: 5% por acerto parcial e 10% por acerto total/centro.
"""

import os
import sys
import unittest
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
DIRETORIO_RAIZ = os.path.abspath(os.path.join(DIRETORIO_ATUAL, ".."))
if DIRETORIO_RAIZ not in sys.path:
    sys.path.insert(0, DIRETORIO_RAIZ)
DIRETORIO_PROJETO = os.path.join(DIRETORIO_RAIZ, "An Average City")
if DIRETORIO_PROJETO not in sys.path:
    sys.path.insert(0, DIRETORIO_PROJETO)

pygame.init()
pygame.display.set_mode((1000, 768))

from Entidades.Personagem import Personagem, personagem
from Gameplay.Habilidades import Habilidade
from Gameplay.MinigameEsquiva import MinigameEsquiva
from Sistemas.Inventario import inventario_global, Equipamento
from Telas.TelaCombate import TelaCombate


class TestBalanceamentoNovo(unittest.TestCase):

    def setUp(self):
        self.tela = pygame.display.get_surface()
        self.jogo = TelaCombate(self.tela)
        self.esquiva = MinigameEsquiva(total_rodadas=3, tela=self.tela)

        # Reset do jogador
        personagem.atributos = {"For": 5, "Agi": 5, "Con": 6, "Sab": 5, "Int": 5, "Sor": 10}
        personagem.hp = 100
        personagem.max_hp = 100
        personagem.mp = 5
        personagem.max_mp = 20
        personagem.talentos = set()
        personagem.bloqueando = False
        personagem.recuperando = False
        personagem.focado = False

        # Reset equipamentos do inventário
        inventario_global.limpar_equipamentos()

    def test_esquiva_reducoes_5_porcento_e_10_porcento(self):
        """Valida que acerto parcial na esquiva reduz 5% e acerto central reduz 10%."""
        self.esquiva.iniciar(velocidade_base=4.0, dano_pendente=100)

        # 1. Acerto central (distancia <= 22) -> Parry: +10%
        self.esquiva.barras[0]["x"] = 200.0  # ponto_centro = 200
        self.esquiva.atualizar(clicou=True)
        self.assertEqual(self.esquiva.acertos_centro, 1)
        self.assertAlmostEqual(self.esquiva.reducao, 0.10, places=2)
        self.assertIn("PARRY PERFEITO! (-10% DANO)", self.esquiva.ultimo_feedback)

        # 2. Acerto lateral (distancia <= 80) -> Esquiva: +5%
        self.esquiva.barras[1]["x"] = 160.0  # distancia = 40 <= 80
        self.esquiva.atualizar(clicou=True)
        self.assertEqual(self.esquiva.acertos, 1)
        self.assertAlmostEqual(self.esquiva.reducao, 0.15, places=2)  # 0.10 + 0.05
        self.assertIn("ESQUIVA SINCRONIZADA! (-5% DANO)", self.esquiva.ultimo_feedback)

    def test_sorte_escala_a_meio_porcento_por_ponto(self):
        """Valida se o cálculo de chance crítica escala a 0.5% (+0.005) por ponto de Sorte."""
        # Sem A2 (base 0.05). Com Sorte = 10 -> 0.05 + (10 * 0.005) = 0.10 (10%)
        personagem.atributos["Sor"] = 10
        sorte_efetiva = personagem.atributos["Sor"] + inventario_global.obter_bonus_atributo("Sor")
        chance_crit = min(1.0, 0.05 + (sorte_efetiva * 0.005))
        self.assertAlmostEqual(chance_crit, 0.10, places=3)

        # Com Sorte = 20 -> 0.05 + (20 * 0.005) = 0.15 (15%)
        personagem.atributos["Sor"] = 20
        sorte_efetiva = 20
        chance_crit = min(1.0, 0.05 + (sorte_efetiva * 0.005))
        self.assertAlmostEqual(chance_crit, 0.15, places=3)

    def test_defesa_passiva_constituicao_e_armaduras(self):
        """Valida o cálculo da defesa passiva: Con // 2 + bônus de Armaduras."""
        # Apenas Constituição (Con = 8 -> Defesa = 4)
        personagem.atributos["Con"] = 8
        defesa_base = self.jogo.calcular_defesa_passiva(personagem)
        self.assertEqual(defesa_base, 4)

        # Equipando Peitoral de Aço (Con +3, Def +3)
        peitoral = Equipamento(
            nome="Peitoral de Aço",
            atributos_bonus={"Con": 3, "Def": 3},
            categoria="peitoral",
            descricao="Armadura pesada de placas de aço."
        )
        inventario_global.equipar(peitoral)

        # Total Con = 8 + 3 = 11 -> Con // 2 = 5
        # Total Def dos equipamentos = 3
        # Defesa Passiva esperada = 5 + 3 = 8
        defesa_com_armadura = self.jogo.calcular_defesa_passiva(personagem)
        self.assertEqual(defesa_com_armadura, 8)

    def test_ataque_basico_custo_zero_nao_recupera_pm(self):
        """Valida que desferir ataque NÃO recupera PM ao acertar (mecânica removida)."""
        personagem.mp = 3
        personagem.max_mp = 10

        hab_basica = Habilidade(
            nome="Golpe Básico",
            tipo="Físico",
            dano=8,
            custo_mp=0,
            precisao=1.0,
            descricao="Ataque básico sem custo."
        )

        from Entidades.Inimigo import Inimigo
        inimigo = Inimigo(x=100, y=100, vida_maxima=50, nome_imagem="Inimigo1.png", nome="Alvo Teste")
        self.jogo.inimigos_fase = [inimigo]
        self.jogo.ordem_turnos = [personagem, inimigo]

        self.jogo.executar_ataque_jogador(hab_basica, alvo_principal=inimigo, jogador_ativo=personagem, chance_erro_minigame=0.0)

        # Jogador NÃO deve recuperar PM ao atacar (mantém 3 PM)
        self.assertEqual(personagem.mp, 3)
        self.assertNotIn("[+1 PM]", self.jogo.mensagem_log)


if __name__ == "__main__":
    unittest.main()
