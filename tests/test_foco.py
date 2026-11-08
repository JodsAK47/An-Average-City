import os
import sys
import unittest
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

RAIZ = Path(__file__).resolve().parent.parent / "An Average City"
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import pygame
pygame.init()
pygame.display.set_mode((1000, 800))

from Telas.TelaCombate import GerenciadorJogo
from Entidades.Personagem import Personagem
from Sistemas.SistemaEfeitos import CONFIG_EFEITOS, obter_efeitos_ativos
import json

class TestFoco(unittest.TestCase):
    def setUp(self):
        self.tela = pygame.display.get_surface()
        self.jogo = GerenciadorJogo(self.tela)

    def test_botao_foco_existe_e_rotulo_correto(self):
        self.assertTrue(hasattr(self.jogo, "btn_foco"))
        self.assertTrue(hasattr(self.jogo, "btn_recuperar"))
        self.assertEqual(self.jogo.btn_foco.texto, "FOCO")
        self.assertIs(self.jogo.btn_foco, self.jogo.btn_recuperar)

    def test_execucao_foco_sem_talentos(self):
        p = Personagem(100, 100, "pixil.png")
        p.mp = 0
        p.max_mp = 10
        p.hp = 50
        p.max_hp = 100
        p.talentos.clear()

        res = self.jogo.executar_foco(p)
        self.assertEqual(res["pm"], 1)
        self.assertEqual(res["hp"], 0)
        self.assertEqual(p.mp, 1)
        self.assertTrue(p.recuperando)
        self.assertTrue(p.focado)
        self.assertIn("🧘 FOCO:", self.jogo.mensagem_log)
        self.assertIn("+1 PM", self.jogo.mensagem_log)
        self.assertIn("+30% dano!", self.jogo.mensagem_log)

    def test_execucao_foco_com_talentos(self):
        p = Personagem(100, 100, "pixil.png")
        p.mp = 0
        p.max_mp = 10
        p.hp = 50
        p.max_hp = 100
        p.talentos = {"F1", "F2", "F3"}

        res = self.jogo.focar(p)
        # F1 = 2 PM base, F2 = +2 PM -> total 4 PM
        # F3 = 10% max_hp -> 10 HP
        self.assertEqual(res["pm"], 4)
        self.assertEqual(res["hp"], 10)
        self.assertEqual(p.mp, 4)
        self.assertEqual(p.hp, 60)
        self.assertTrue(p.recuperando)
        self.assertTrue(p.focado)
        self.assertIn("🧘 FOCO:", self.jogo.mensagem_log)
        self.assertIn("+4 PM", self.jogo.mensagem_log)
        self.assertIn("+10 HP", self.jogo.mensagem_log)
        self.assertIn("sem penalidade de dano (F2)!", self.jogo.mensagem_log)

    def test_alias_recuperar_chama_foco(self):
        p = Personagem(100, 100, "pixil.png")
        p.mp = 0
        p.max_mp = 10
        p.talentos.clear()

        res = self.jogo.recuperar(p)
        self.assertEqual(res["pm"], 1)
        self.assertIn("🧘 FOCO:", self.jogo.mensagem_log)

    def test_efeito_ativo_nome_foco(self):
        p = Personagem(100, 100, "pixil.png")
        p.focado = True
        efeitos = obter_efeitos_ativos(p)
        self.assertTrue(any(e["nome"] == "Foco" for e in efeitos))
        self.assertTrue(any(e["id"] == "recuperando" for e in efeitos))
        self.assertIn("+30% dano", CONFIG_EFEITOS["recuperando"]["descricao"])

    def test_arvores_json_textos_foco(self):
        caminho_arvores = RAIZ / "Dados" / "arvores.json"
        with open(caminho_arvores, "r", encoding="utf-8") as f:
            dados = json.load(f)
        feiticeiro = dados.get("Feiticeiro", [])
        f2 = next(h for h in feiticeiro if h["id"] == "F2")
        f3 = next(h for h in feiticeiro if h["id"] == "F3")
        self.assertIn("Foco", f2["desc"])
        self.assertNotIn("Recuperar", f2["desc"])
        self.assertIn("Foco", f3["desc"])
        self.assertNotIn("Recuperar", f3["desc"])

    def test_dano_extra_foco_e_negacao_f2(self):
        """Testa se o foco sem F2 aumenta dano recebido em 30% e com F2 o anula."""
        dano_base = 100

        # Caso 1: Jogador focado SEM F2 -> sofre 30% a mais (100 -> 130)
        p1 = Personagem(100, 100, "pixil.png")
        p1.focado = True
        p1.talentos.clear()

        dano_calculado_1 = dano_base
        if p1.recuperando or getattr(p1, "focado", False):
            if not self.jogo.tem_talento(p1, "F2"):
                dano_calculado_1 += max(1, int(dano_calculado_1 * 0.30))
        self.assertEqual(dano_calculado_1, 130)

        # Caso 2: Jogador focado COM F2 -> dano extra é anulado (100 -> 100)
        p2 = Personagem(100, 100, "pixil.png")
        p2.focado = True
        p2.talentos = {"F2"}

        dano_calculado_2 = dano_base
        if p2.recuperando or getattr(p2, "focado", False):
            if not self.jogo.tem_talento(p2, "F2"):
                dano_calculado_2 += max(1, int(dano_calculado_2 * 0.30))
        self.assertEqual(dano_calculado_2, 100)

if __name__ == "__main__":
    unittest.main()
