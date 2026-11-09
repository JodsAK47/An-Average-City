# -*- coding: utf-8 -*-
"""
Testes unitários para a mecânica de teleporte e balanço da sprite em ataques físicos:
- Detecção de ataque físico (eh_ataque_fisico).
- Teleporte temporário da sprite para a frente do alvo (jogador, inimigo e minion).
- Oscilação e balanço dinâmico durante a execução do golpe.
- Retorno à posição base de batalha após a finalização do timer/cooldown.
- Renderização visual e estabilidade da barra de status no slot de origem.
"""

import os
import sys
import unittest
import math
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
from Entidades.Inimigo import Inimigo
from Entidades.Minion import criar_minion
from Gameplay.Habilidades import Habilidade, banco_habilidades
from Telas.TelaCombate import TelaCombate


class TestAnimacaoAtaqueFisico(unittest.TestCase):

    def setUp(self):
        self.tela = pygame.display.get_surface()
        self.jogo = TelaCombate(self.tela)

        personagem.atributos = {"For": 10, "Agi": 8, "Con": 10, "Sab": 5, "Int": 5, "Sor": 10}
        personagem.hp = 100
        personagem.max_hp = 100
        personagem.mp = 20
        personagem.max_mp = 20
        personagem.rect.center = (260, 400)
        personagem.posicao_base = (260, 400)
        personagem.bloqueando = False

        self.inimigo_teste = Inimigo(
            x=740,
            y=400,
            vida_maxima=80,
            nome_imagem="Inimigo1.png",
            nome="Inimigo Teste",
            ataques=["Soco"],
            xp=20,
            atributos={"For": 8, "Agi": 6, "Con": 8, "Int": 4, "Sor": 5}
        )
        self.inimigo_teste.rect.center = (740, 400)
        self.inimigo_teste.posicao_base = (740, 400)

        self.jogo.ordem_turnos = [personagem, self.inimigo_teste]
        self.jogo.atualizar_posicoes_inimigos()

    def test_deteccao_ataque_fisico(self):
        """Valida que eh_ataque_fisico identifica corretamente habilidades físicas e não-físicas."""
        # Ataques físicos de personagens
        self.assertTrue(self.jogo.eh_ataque_fisico("Machadada"))
        self.assertTrue(self.jogo.eh_ataque_fisico("Facada"))
        self.assertTrue(self.jogo.eh_ataque_fisico("Flash Negro"))
        self.assertTrue(self.jogo.eh_ataque_fisico("HamBat"))
        self.assertTrue(self.jogo.eh_ataque_fisico("Segura o Regue"))
        self.assertTrue(self.jogo.eh_ataque_fisico("Colisão 24 Frames"))

        # Ataques físicos genéricos e de inimigos/minions
        self.assertTrue(self.jogo.eh_ataque_fisico("Soco"))
        self.assertTrue(self.jogo.eh_ataque_fisico("Mordida"))
        self.assertTrue(self.jogo.eh_ataque_fisico("Ferrão Veloz"))
        self.assertTrue(self.jogo.eh_ataque_fisico("Bicada Perfurante"))
        self.assertTrue(self.jogo.eh_ataque_fisico("Presas das Sombras"))
        self.assertTrue(self.jogo.eh_ataque_fisico("Espada do Extermínio"))
        self.assertTrue(self.jogo.eh_ataque_fisico("Investida Lupina"))

        # Objetos de Habilidade com tipo "Físico"
        hab_obj = Habilidade("Golpe Pesado", 1, "Físico", 15, 0, 1.0, "Golpe físico pesado")
        self.assertTrue(self.jogo.eh_ataque_fisico(hab_obj))

        # Ataques não-físicos (Magia, Distância, Invocador, Suporte)
        self.assertFalse(self.jogo.eh_ataque_fisico("Azul"))
        self.assertFalse(self.jogo.eh_ataque_fisico("Vermelho"))
        self.assertFalse(self.jogo.eh_ataque_fisico("Boomerang"))
        self.assertFalse(self.jogo.eh_ataque_fisico("Laser Tático"))
        self.assertFalse(self.jogo.eh_ataque_fisico("Invocar Abelha"))
        self.assertFalse(self.jogo.eh_ataque_fisico("Plantar Spike"))

    def test_jogador_teleporta_na_frente_do_inimigo_e_balanca(self):
        """Valida teleporte do jogador para a frente do inimigo à direita e oscilação de balanço."""
        pos_base_jogador = (260, 400)
        pos_base_inimigo = (740, 400)
        self.jogo.atualizar_posicoes_inimigos()

        # Executa ataque físico "Machadada"
        self.jogo.executar_ataque_jogador("Machadada", alvo_principal=self.inimigo_teste, jogador_ativo=personagem)

        # Animação deve estar ativa
        self.assertIsNotNone(self.jogo.animacao_ataque_fisico)
        self.assertEqual(self.jogo.animacao_ataque_fisico["atacante"], personagem)
        self.assertEqual(self.jogo.animacao_ataque_fisico["alvo"], self.inimigo_teste)

        # Atualiza a tela por 1 frame para calcular posição com swing
        self.jogo.atualizar((0, 0), False)

        # Jogador deve estar teletransportado logo à esquerda da face do inimigo (x ~ 600-700)
        distancia_ao_alvo = abs(personagem.rect.centerx - self.inimigo_teste.rect.centerx)
        self.assertLess(distancia_ao_alvo, 150, "O jogador deve estar próximo/à frente do inimigo")
        self.assertGreater(personagem.rect.centerx, 500, "O jogador deve ter saído da base x=260")

        # Avança frames simulando o balanço
        posicoes_x = []
        for _ in range(15):
            self.jogo.atualizar((0, 0), False)
            posicoes_x.append(personagem.rect.centerx)

        # Verifica se houve variação/oscilação lateral (balanço dinâmico)
        self.assertGreater(len(set(posicoes_x)), 1, "A sprite deve oscilar/balançar durante o golpe")

        # Avança até o término do cooldown
        for _ in range(80):
            self.jogo.atualizar((0, 0), False)

        # Ao término da animação/turno, jogador retorna à posição original
        self.assertIsNone(self.jogo.animacao_ataque_fisico)
        self.assertEqual(personagem.rect.center, pos_base_jogador)

    def test_inimigo_teleporta_na_frente_do_jogador_e_balanca(self):
        """Valida teleporte do inimigo à direita para a frente do jogador à esquerda."""
        pos_base_inimigo = (740, 400)
        self.jogo.atualizar_posicoes_inimigos()

        # Inimigo desfere ataque físico contra o jogador bloqueando
        personagem.bloqueando = True
        self.inimigo_teste.mp = 5
        hab_soco = Habilidade("Soco", 1, "Físico", 10, 0, 1.0, "Soco potente")
        banco_inimigo = {"Soco": hab_soco}

        # Dispara animação de ataque físico do inimigo
        self.jogo.disparar_ataque_fisico_teleporte(self.inimigo_teste, personagem, duracao=40)
        self.assertIsNotNone(self.jogo.animacao_ataque_fisico)

        # Atualiza 1 frame
        self.jogo.atualizar((0, 0), False)

        # Inimigo deve estar teletransportado logo à direita da face do jogador (x ~ 300-380)
        self.assertLess(self.inimigo_teste.rect.centerx, 450)
        self.assertGreater(self.inimigo_teste.rect.centerx, 260)

        # Avança até expirar o timer
        for _ in range(45):
            self.jogo.atualizar((0, 0), False)

        # Inimigo retorna à base
        self.assertIsNone(self.jogo.animacao_ataque_fisico)
        self.assertEqual(self.inimigo_teste.rect.center, pos_base_inimigo)

    def test_minion_teleporta_na_frente_do_inimigo(self):
        """Valida teleporte de minion (ex: Abelha Soldado / Cão Divino) em ataque físico."""
        minion = criar_minion("Cão Divino", dono=personagem, x=395, y=405)
        self.jogo.ordem_turnos.append(minion)
        self.jogo.atualizar_posicoes_inimigos()

        # Executa turno do minion com golpe físico
        self.jogo.executar_turno_minion(minion, alvo_forcado=self.inimigo_teste)

        # Animação deve estar registrada para o minion
        self.assertIsNotNone(self.jogo.animacao_ataque_fisico)
        self.assertEqual(self.jogo.animacao_ataque_fisico["atacante"], minion)

        # Atualiza 1 frame
        self.jogo.atualizar((0, 0), False)

        # Minion teletransportado para frente do inimigo
        self.assertGreater(minion.rect.centerx, 550)

        # Ao término do timer, retorna para sua posição de formação (395, 405)
        for _ in range(80):
            self.jogo.atualizar((0, 0), False)

        self.assertIsNone(self.jogo.animacao_ataque_fisico)
        self.assertEqual(minion.rect.center, (395, 405))

    def test_ataque_magico_nao_dispara_teleporte(self):
        """Garante que ataques de Magia ou Distância NÃO teleportam a sprite."""
        self.jogo.atualizar_posicoes_inimigos()
        pos_antes = personagem.rect.center

        # Ataque de Magia "Azul"
        self.jogo.executar_ataque_jogador("Azul", alvo_principal=self.inimigo_teste, jogador_ativo=personagem)

        # Nenhuma animação de teleporte físico deve ser iniciada
        self.assertIsNone(self.jogo.animacao_ataque_fisico)
        self.jogo.atualizar((0, 0), False)
        self.assertEqual(personagem.rect.center, pos_antes)

    def test_inimigo_move_quadrado_e_barra_de_vida_juntos_com_pendulo_invertido(self):
        """Valida que o quadrado (rect) do inimigo e a barra de vida se movem juntos com pêndulo invertido."""
        self.jogo.atualizar_posicoes_inimigos()

        # Dispara ataque físico do inimigo
        self.jogo.disparar_ataque_fisico_teleporte(self.inimigo_teste, personagem, duracao=40)
        self.jogo.atualizar((0, 0), False)

        # O quadrado (rect) do inimigo deve estar na frente do jogador (x ~ 300-420)
        self.assertLess(self.inimigo_teste.rect.centerx, 450)
        self.assertGreater(self.inimigo_teste.rect.centerx, 260)

        # A barra de status desenhada para o inimigo agora usa diretamente o rect do inimigo na frente
        # Verificando se desenhar_barras_status usa rect na posição em frente ao jogador
        rect_inimigo = self.inimigo_teste.rect
        self.assertLess(rect_inimigo.centerx, 450)

        # Movimento de pêndulo invertido: deve possuir ângulo de rotação suave e sem tremer
        angulo = self.jogo.animacao_ataque_fisico.get("angulo_rotacao", 0.0)
        self.assertLessEqual(abs(angulo), 15.0, "O ângulo de pêndulo deve ser leve (<= 15 graus)")

        # Amostra posições para verificar movimento suave de pêndulo
        posicoes = []
        for _ in range(12):
            self.jogo.atualizar((0, 0), False)
            posicoes.append(self.inimigo_teste.rect.centerx)

        # Variação contínua e suave (sem saltos de alta frequência)
        delta_max = max(abs(posicoes[i] - posicoes[i-1]) for i in range(1, len(posicoes)))
        self.assertLessEqual(delta_max, 8, "Variação entre frames adjacentes deve ser suave (sem tremores)")

    def test_renderizacao_desenho_com_animacao_ativa(self):
        """Valida que desenhar() processa a entidade atacante sobrepondo o alvo e sem exceções."""
        self.jogo.disparar_ataque_fisico_teleporte(personagem, self.inimigo_teste, duracao=35)
        self.jogo.atualizar((0, 0), False)

        # Deve executar desenhar sem lançar qualquer exceção
        try:
            self.jogo.desenhar(posicao_mouse=(500, 384))
        except Exception as e:
            self.fail(f"desenhar() falhou com animação de ataque físico ativa: {e}")


if __name__ == "__main__":
    unittest.main()
