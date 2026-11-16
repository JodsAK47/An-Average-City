import unittest
import os
import sys
import pygame

# Garante que os módulos do jogo possam ser importados
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "An Average City"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

if not pygame.get_init():
    pygame.init()
pygame.display.set_mode((1000, 700))

from Entidades.Minion import Minion, criar_minion
from Entidades.Inimigo import Inimigo
from Telas.TelaCombate import TelaCombate, personagem
from Telas.CombateHUD import desenhar_barras_status


class TestSeparacaoSummons(unittest.TestCase):
    def setUp(self):
        self.superficie = pygame.Surface((1000, 700))
        self.combate = TelaCombate(self.superficie)
        self.jogador = personagem
        self.jogador.hp = 100
        self.jogador.max_hp = 100
        self.jogador.mp = 50
        self.jogador.max_mp = 50
        self.inimigo = Inimigo(700, 300, 80, "Inimigo1.png", nome="Monstro Teste")
        self.inimigo.hp = 80
        self.inimigo.max_hp = 80
        self.combate.ordem_turnos = [self.jogador, self.inimigo]

    def test_minion_lado_e_propriedades(self):
        minion_jogador = criar_minion("Lobo Espiritual", dono=self.jogador)
        minion_inimigo = criar_minion("Torreta Sentinela", dono=self.inimigo)
        minion_sem_dono = criar_minion("Abelha Operária")

        self.assertEqual(minion_jogador.lado, "jogador")
        self.assertTrue(minion_jogador.eh_do_jogador)
        self.assertFalse(minion_jogador.eh_do_inimigo)

        self.assertEqual(minion_inimigo.lado, "inimigo")
        self.assertFalse(minion_inimigo.eh_do_jogador)
        self.assertTrue(minion_inimigo.eh_do_inimigo)

        self.assertEqual(minion_sem_dono.lado, "inimigo")
        self.assertFalse(minion_sem_dono.eh_do_jogador)
        self.assertTrue(minion_sem_dono.eh_do_inimigo)

    def test_classificacao_tela_combate(self):
        minion_p = self.combate.invocar_minion("Lobo Espiritual", dono=self.jogador)
        minion_e = self.combate.invocar_minion("Torreta Sentinela", dono=self.inimigo)

        self.assertIsNotNone(minion_p)
        self.assertIsNotNone(minion_e)

        # Helpers de identificação de tipo
        self.assertTrue(self.combate.eh_minion(minion_p))
        self.assertTrue(self.combate.eh_minion(minion_e))
        self.assertFalse(self.combate.eh_minion(self.jogador))
        self.assertFalse(self.combate.eh_minion(self.inimigo))

        # Diferenciação jogador vs inimigo
        self.assertTrue(self.combate.eh_minion_jogador(minion_p))
        self.assertFalse(self.combate.eh_minion_jogador(minion_e))

        self.assertFalse(self.combate.eh_minion_inimigo(minion_p))
        self.assertTrue(self.combate.eh_minion_inimigo(minion_e))

        # Aliados vs Inimigos para o jogador
        self.assertTrue(self.combate.eh_aliado(self.jogador))
        self.assertTrue(self.combate.eh_aliado(minion_p))
        self.assertFalse(self.combate.eh_aliado(self.inimigo))
        self.assertFalse(self.combate.eh_aliado(minion_e))

        self.assertFalse(self.combate.eh_inimigo(self.jogador))
        self.assertFalse(self.combate.eh_inimigo(minion_p))
        self.assertTrue(self.combate.eh_inimigo(self.inimigo))
        self.assertTrue(self.combate.eh_inimigo(minion_e))

        # Listas filtradas por lado
        minions_j = self.combate.obter_minions_jogador()
        minions_i = self.combate.obter_minions_inimigos()
        self.assertIn(minion_p, minions_j)
        self.assertNotIn(minion_e, minions_j)
        self.assertIn(minion_e, minions_i)
        self.assertNotIn(minion_p, minions_i)

    def test_posicionamento_e_orientacao(self):
        minion_p = self.combate.invocar_minion("Lobo Espiritual", dono=self.jogador)
        minion_e = self.combate.invocar_minion("Torreta Sentinela", dono=self.inimigo)

        self.combate.atualizar_posicoes_inimigos()

        # Minion do jogador deve estar no lado esquerdo (x = 395) e virado para leste
        self.assertEqual(minion_p.rect.centerx, 395)
        self.assertEqual(getattr(minion_p, "direcao_olhar", None), "leste")

        # Minion inimigo deve estar no lado direito (x = 540) e virado para oeste
        self.assertEqual(minion_e.rect.centerx, 540)
        self.assertEqual(getattr(minion_e, "direcao_olhar", None), "oeste")

    def test_turno_minion_alvos(self):
        minion_p = self.combate.invocar_minion("Cão Divino", dono=self.jogador)
        minion_e = self.combate.invocar_minion("Torreta Sentinela", dono=self.inimigo)

        # Garante 100% de precisão nos ataques para o teste
        for a in minion_p.ataques:
            minion_p.obter_habilidade(a).precisao = 1.0
        for a in minion_e.ataques:
            minion_e.obter_habilidade(a).precisao = 1.0

        # Minion do jogador deve focar e atacar inimigos
        self.inimigo.hp = 80
        self.combate.executar_turno_minion(minion_p, alvo_forcado=self.inimigo)
        self.assertLess(self.inimigo.hp, 80)

        # Minion do inimigo deve atacar o jogador ou os minions do jogador
        hp_jogador_inicial = self.jogador.hp
        hp_minion_p_inicial = minion_p.hp
        self.combate.executar_turno_minion(minion_e, alvo_forcado=self.jogador)
        dano_sofrido = (hp_jogador_inicial - self.jogador.hp) + (hp_minion_p_inicial - minion_p.hp)
        self.assertGreater(dano_sofrido, 0)

    def test_colapso_summons_ao_derrotar_invocador(self):
        minion_e = self.combate.invocar_minion("Torreta Sentinela", dono=self.inimigo)
        self.assertGreater(minion_e.hp, 0)

        # Ao derrotar o inimigo summoner com golpe do jogador, seu minion deve colapsar
        self.inimigo.hp = 5
        from Gameplay.Habilidades import Habilidade
        hab = Habilidade("Golpe Fatal", "Físico", 50, 0, 1.0, "Ataque teste")
        self.combate.executar_ataque_jogador(hab, alvo_principal=self.inimigo, jogador_ativo=self.jogador)

        self.assertEqual(self.inimigo.hp, 0)
        self.assertEqual(minion_e.hp, 0)

    def test_hud_placa_diferenciada(self):
        fonte = pygame.font.Font(None, 18)
        minion_p = criar_minion("Cão Divino", dono=self.jogador)
        minion_e = criar_minion("Torreta Sentinela", dono=self.inimigo)

        # Ambas as chamadas de desenho devem ocorrer com sucesso sem erros
        res_p = desenhar_barras_status(
            self.superficie, minion_p, fonte, lambda e: getattr(e, "is_minion", False)
        )
        res_e = desenhar_barras_status(
            self.superficie, minion_e, fonte, lambda e: getattr(e, "is_minion", False)
        )

        self.assertIsNone(res_p)
        self.assertIsNone(res_e)

    def test_ia_inimigo_nao_ataca_minion_aliado(self):
        # Inimigo e minion do inimigo em campo
        minion_e = self.combate.invocar_minion("Torreta Sentinela", dono=self.inimigo)
        minion_p = self.combate.invocar_minion("Cão Divino", dono=self.jogador)

        # Os minions alvos para o inimigo devem ser apenas os do jogador
        alvos_minions_para_inimigo = self.combate.obter_minions_jogador()
        self.assertIn(minion_p, alvos_minions_para_inimigo)
        self.assertNotIn(minion_e, alvos_minions_para_inimigo)


if __name__ == "__main__":
    unittest.main()
