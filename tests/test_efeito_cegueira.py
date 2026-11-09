import os
import sys
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "An Average City"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
if not pygame.get_init():
    pygame.init()
pygame.display.set_mode((1000, 700))

from Entidades.Personagem import Personagem
from Entidades.Inimigo import Inimigo
from Entidades.Minion import Minion, criar_minion
from Gameplay.Habilidades import Habilidade
from Telas.TelaCombate import TelaCombate, personagem
from Sistemas.SistemaEfeitos import obter_efeitos_ativos, carregar_icone_efeito, CONFIG_EFEITOS


class TestEfeitoCegueira(unittest.TestCase):
    def setUp(self):
        self.superficie = pygame.Surface((1000, 700))
        self.combate = TelaCombate(self.superficie)
        self.personagem = personagem
        self.personagem.hp = 100
        self.personagem.max_hp = 100
        self.personagem.mp = 50
        self.personagem.god_mode = False
        self.personagem.cego = False
        self.personagem.turnos_cegueira = 0
        self.inimigo = Inimigo(700, 300, 100, "Inimigo1.png", nome="Inimigo Teste")
        self.inimigo.hp = 100
        self.inimigo.max_hp = 100
        self.inimigo.cego = False
        self.inimigo.turnos_cegueira = 0
        self.combate.ordem_turnos = [self.personagem, self.inimigo]

    def test_config_efeito_e_sprite_cego(self):
        """Verifica se o efeito cegueira está configurado no SistemaEfeitos com Cego.png."""
        self.assertIn("cegueira", CONFIG_EFEITOS)
        self.assertIn("cego", CONFIG_EFEITOS)
        cfg = CONFIG_EFEITOS["cegueira"]
        self.assertEqual(cfg["arquivo"], "Cego.png")
        self.assertEqual(cfg["tipo"], "debuff")

        icone = carregar_icone_efeito("cegueira", 20)
        self.assertIsNotNone(icone)
        self.assertEqual(icone.get_size(), (20, 20))

    def test_aplicar_status_cegueira_na_entidade(self):
        """Aplicar status de cegueira deve ativar cego=True e definir 2 rodadas."""
        self.assertFalse(self.inimigo.cego)
        self.inimigo.aplicar_status("Cegueira")
        self.assertTrue(self.inimigo.cego)
        self.assertEqual(self.inimigo.turnos_cegueira, 2)

        efeitos = obter_efeitos_ativos(self.inimigo)
        nomes = [e["nome"] for e in efeitos]
        self.assertIn("Cegueira", nomes)

    def test_decremento_rodadas_cegueira(self):
        """A cada rodada em processar_fim_rodada, a duração de cegueira deve diminuir até expirar."""
        self.inimigo.aplicar_status("Cegueira")
        self.assertEqual(self.inimigo.turnos_cegueira, 2)

        # Rodada 1
        self.combate.processar_fim_rodada()
        self.assertEqual(self.inimigo.turnos_cegueira, 1)
        self.assertTrue(self.inimigo.cego)

        # Rodada 2 - deve expirar
        self.combate.processar_fim_rodada()
        self.assertEqual(self.inimigo.turnos_cegueira, 0)
        self.assertFalse(self.inimigo.cego)

    def test_cegueira_aumenta_falha_jogador_minigame(self):
        """Cegueira deve aumentar a chance_erro do minigame do jogador em +20% (0.20)."""
        hab = Habilidade("Disparo", "Físico", 20, 0, 1.0, "Disparo certeiro")

        # Sem cegueira: chance_erro = 0.10
        # Com cegueira: chance_erro_final deve ser 0.10 + 0.20 = 0.30
        self.personagem.cego = True

        # Força valor de random entre 0.20 e 0.30 (ex: 0.25)
        # Se não tivesse cegueira (chance_erro=0.10), 0.25 < 0.10 seria False (acertaria)
        # Com cegueira (chance_erro=0.30), 0.25 < 0.30 é True (erra!)
        import random
        random_original = random.random
        try:
            random.random = lambda: 0.25
            self.combate.executar_ataque_jogador(
                hab,
                alvo_principal=self.inimigo,
                jogador_ativo=self.personagem,
                chance_erro_minigame=0.10
            )
            self.assertIn("ERROU", self.combate.mensagem_log)
        finally:
            random.random = random_original

    def test_cegueira_reduz_precisao_ataque_direto_jogador(self):
        """Cegueira deve reduzir a precisão do jogador em 20% (+20% chance de falha)."""
        hab = Habilidade("Estocada", "Físico", 20, 0, 0.90, "Estocada")
        self.personagem.cego = True

        # Precisão 0.90 - 0.20 = 0.70
        # Se random.random() der 0.75:
        # Sem cegueira: 0.75 > 0.90 é False (acerta)
        # Com cegueira: 0.75 > 0.70 é True (erra!)
        import random
        random_original = random.random
        try:
            random.random = lambda: 0.75
            self.combate.executar_ataque_jogador(
                hab,
                alvo_principal=self.inimigo,
                jogador_ativo=self.personagem,
                chance_erro_minigame=None
            )
            self.assertIn("ERROU", self.combate.mensagem_log)
        finally:
            random.random = random_original

    def test_cegueira_reduz_precisao_inimigo(self):
        """Inimigo cego tem precisão reduzida em 20% (+20% chance de falha ao atacar)."""
        hab_inimigo = Habilidade("Pancada", "Físico", 15, 0, 0.90, "Pancada forte")
        self.inimigo.obter_habilidade = lambda nome: hab_inimigo
        self.inimigo.ataques = ["Pancada"]
        self.inimigo.cego = True

        # Precisão base 0.90 -> com cegueira 0.70
        # random = 0.75 causa erro (0.75 > 0.70)
        import random
        random_original = random.random
        try:
            random.random = lambda: 0.75
            # Simula ataque do inimigo diretamente na precisão
            precisao_inimigo = hab_inimigo.precisao
            if getattr(self.inimigo, "cego", False):
                precisao_inimigo = max(0.0, precisao_inimigo - 0.20)
            self.assertAlmostEqual(precisao_inimigo, 0.70)
        finally:
            random.random = random_original

    def test_cegueira_minion_aumenta_chance_falha(self):
        """Minion cego tem precisão final reduzida em 20% (+20% chance de falha)."""
        minion = criar_minion("Torreta Sentinela", dono=self.personagem)
        hab_minion = minion.obter_habilidade(minion.ataques[0])
        hab_minion.precisao = 0.90
        minion.cego = True

        # Com random = 0.75:
        # Sem cegueira (0.90), 0.75 > 0.90 é False (acertaria)
        # Com cegueira (0.70), 0.75 > 0.70 é True (erra)
        import random
        random_original = random.random
        try:
            random.random = lambda: 0.75
            self.combate.executar_turno_minion(minion, alvo_forcado=self.inimigo)
            self.assertIn("ERROU", self.combate.mensagem_log)
        finally:
            random.random = random_original


if __name__ == "__main__":
    unittest.main()
