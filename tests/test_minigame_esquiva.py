import os
import sys
import unittest
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"

RAIZ = Path(__file__).resolve().parent.parent / "An Average City"
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import pygame
pygame.init()
pygame.display.set_mode((1000, 800))

from Gameplay.MinigameEsquiva import MinigameEsquiva
from Telas.TelaCombate import GerenciadorJogo
from Entidades.Personagem import personagem
from Entidades.Inimigo import Inimigo


class TestMinigameEsquivaModerno(unittest.TestCase):

    def setUp(self):
        self.tela = pygame.Surface((1000, 800))
        self.esquiva = MinigameEsquiva(total_rodadas=3, tela=self.tela)

    def test_inicializacao_e_estado_ativo(self):
        """Verifica se o minigame inicia corretamente com atributos e trilho balanceados."""
        self.assertFalse(self.esquiva.esta_ativo())
        self.esquiva.iniciar(velocidade_base=4.8, dano_pendente=60, atacante_nome="Boss Teste")

        self.assertTrue(self.esquiva.esta_ativo())
        self.assertEqual(len(self.esquiva.barras), 3)
        self.assertEqual(self.esquiva.dano_pendente, 60)
        self.assertEqual(self.esquiva.atacante_nome, "Boss Teste")
        self.assertEqual(self.esquiva.ponto_centro, 200)

    def test_balanceamento_velocidade_e_agilidade(self):
        """Verifica se a velocidade base é justa (~4.8) e se a Agilidade e talento A3 desaceleram suavemente."""
        jogo = GerenciadorJogo(self.tela)
        # Velocidade base
        self.assertAlmostEqual(jogo.esquiva_vel, 4.8, places=1)

        # Personagem com agilidade padrão (ex: 2)
        personagem.atributos["Agi"] = 2
        personagem.talentos = set()
        vel_padrao = jogo.velocidade_esquiva(personagem)
        self.assertLess(vel_padrao, 5.0)
        self.assertGreater(vel_padrao, 4.0)

        # Personagem com alta agilidade (ex: 15)
        personagem.atributos["Agi"] = 15
        vel_agil = jogo.velocidade_esquiva(personagem)
        self.assertLess(vel_agil, vel_padrao)

        # Personagem com talento A3
        personagem.talentos.add("A3")
        vel_com_a3 = jogo.velocidade_esquiva(personagem)
        self.assertLess(vel_com_a3, vel_agil)
        self.assertGreaterEqual(vel_com_a3, 2.4)

    def test_parry_perfeito_no_centro(self):
        """Verifica se acerto no centro (distancia <= 22) registra PARRY PERFEITO e +10% de redução."""
        self.esquiva.iniciar(velocidade_base=4.5, dano_pendente=100)

        # Coloca a primeira barra exatamente no centro (x=200)
        self.esquiva.barras[0]["x"] = 200.0

        # Clica para acionar
        res = self.esquiva.atualizar(clicou=True)
        self.assertEqual(self.esquiva.acertos_centro, 1)
        self.assertAlmostEqual(self.esquiva.reducao, 0.10, places=2)
        self.assertIn("PARRY PERFEITO", self.esquiva.ultimo_feedback)
        self.assertEqual(self.esquiva.barras[0]["resultado"], "parry")
        self.assertGreater(len(self.esquiva.particulas), 0)

    def test_esquiva_lateral_sincronizada(self):
        """Verifica se acerto lateral (distancia <= 80) registra ESQUIVA e +5% de redução."""
        self.esquiva.iniciar(velocidade_base=4.5, dano_pendente=100)

        # Coloca a primeira barra na lateral da zona (x=150, distancia = 50)
        self.esquiva.barras[0]["x"] = 150.0

        self.esquiva.atualizar(clicou=True)
        self.assertEqual(self.esquiva.acertos, 1)
        self.assertAlmostEqual(self.esquiva.reducao, 0.05, places=2)
        self.assertIn("ESQUIVA SINCRONIZADA", self.esquiva.ultimo_feedback)
        self.assertEqual(self.esquiva.barras[0]["resultado"], "esquiva")

    def test_erro_tempo_fora_da_zona(self):
        """Verifica se clique muito distante (distancia > 80) registra erro sem redução."""
        self.esquiva.iniciar(velocidade_base=4.5, dano_pendente=100)

        # Coloca barra longe da zona (x=50, distancia = 150)
        self.esquiva.barras[0]["x"] = 50.0

        self.esquiva.atualizar(clicou=True)
        self.assertEqual(self.esquiva.acertos, 0)
        self.assertEqual(self.esquiva.acertos_centro, 0)
        self.assertEqual(self.esquiva.reducao, 0.0)
        self.assertIn("ERROU O TEMPO", self.esquiva.ultimo_feedback)
        self.assertEqual(self.esquiva.barras[0]["resultado"], "erro")

    def test_suporte_evento_tecla_espaco(self):
        """Verifica se a tecla [ESPAÇO] registra ação de esquiva via processar_evento."""
        self.esquiva.iniciar(velocidade_base=4.5, dano_pendente=100)
        self.esquiva.barras[0]["x"] = 200.0

        ev_space = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
        self.esquiva.processar_evento(ev_space, (0, 0))
        self.assertTrue(self.esquiva.acao_pendente)

        # Na atualização, a ação pendente deve ser consumida e acertar o Parry
        self.esquiva.atualizar(clicou=False)
        self.assertFalse(self.esquiva.acao_pendente)
        self.assertEqual(self.esquiva.acertos_centro, 1)

    def test_conclusao_completa_e_reducao_dano(self):
        """Verifica o encerramento do minigame com cálculo correto de redução e dano."""
        self.esquiva.iniciar(velocidade_base=5.0, dano_pendente=100)

        # Força acerto de 3 Parries consecutivos
        for i in range(3):
            self.esquiva.barras[i]["x"] = 200.0
            self.esquiva.atualizar(clicou=True)

        # Todas as barras ficaram inativas; avança o timer de encerramento
        resultado = None
        for _ in range(30):
            res = self.esquiva.atualizar(clicou=False)
            if res:
                resultado = res
                break

        self.assertIsNotNone(resultado)
        self.assertTrue(resultado["concluido"])
        self.assertTrue(resultado["evitou_tudo"])
        self.assertEqual(resultado["acertos_centro"], 3)
        self.assertAlmostEqual(resultado["reducao_total"], 0.30, places=2)
        self.assertEqual(resultado["dano_tomado"], 70)

    def test_renderizacao_grafica_sem_erros(self):
        """Verifica se o método desenhar renderiza todas as camadas e elementos sem exceções."""
        self.esquiva.iniciar(velocidade_base=4.8, dano_pendente=80, atacante_nome="Sukuna")
        self.esquiva.desenhar(self.tela)

        # Testa também a chamada legada com coordenadas diretas
        self.esquiva.desenhar(self.tela, bar_x=300, bar_y=250, bar_w=400, bar_h=24)

    def test_orbes_lados_diferentes_e_velocidades_diferentes(self):
        """Verifica se cada orbe sai de um lado alternado (esquerda/direita) e com velocidade diferente."""
        self.esquiva.iniciar(velocidade_base=4.8, dano_pendente=50)

        barras = self.esquiva.barras
        self.assertEqual(len(barras), 3)

        # Lados diferentes alternados
        self.assertNotEqual(barras[0]["lado"], barras[1]["lado"])
        self.assertNotEqual(barras[1]["lado"], barras[2]["lado"])

        # Direções opostas
        self.assertNotEqual(barras[0]["direcao"], barras[1]["direcao"])
        self.assertNotEqual(barras[1]["direcao"], barras[2]["direcao"])

        # Velocidades diferentes entre todas as orbes
        vels = [b["velocidade"] for b in barras]
        self.assertNotEqual(vels[0], vels[1])
        self.assertNotEqual(vels[1], vels[2])

    def test_parry_orbe_vindo_da_direita(self):
        """Verifica o movimento e parry de uma orbe vindo da direita (direção -1)."""
        self.esquiva.iniciar(velocidade_base=5.0, dano_pendente=80)
        # Força primeira barra vindo da direita
        self.esquiva.barras[0]["lado"] = "direita"
        self.esquiva.barras[0]["direcao"] = -1
        self.esquiva.barras[0]["x"] = 200.0

        res = self.esquiva.atualizar(clicou=True)
        self.assertEqual(self.esquiva.acertos_centro, 1)
        self.assertEqual(self.esquiva.barras[0]["resultado"], "parry")

    def test_orbe_direita_perdida_quando_ultrapassa_limite(self):
        """Verifica se orbe vindo da direita é marcada como perdida ao passar x <= 0."""
        self.esquiva.iniciar(velocidade_base=5.0, dano_pendente=80)
        self.esquiva.barras[0]["lado"] = "direita"
        self.esquiva.barras[0]["direcao"] = -1
        self.esquiva.barras[0]["x"] = 1.0

        # Atualiza sem clicar; a velocidade negativa deve mover x <= 0
        self.esquiva.atualizar(clicou=False)
        self.assertFalse(self.esquiva.barras[0]["ativa"])
        self.assertEqual(self.esquiva.barras[0]["resultado"], "perdida")
        self.assertIn("PROJÉTIL PERDIDO", self.esquiva.ultimo_feedback)


if __name__ == "__main__":
    unittest.main()
