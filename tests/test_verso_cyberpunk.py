import os
import sys
import unittest
from itertools import combinations
from types import SimpleNamespace
from unittest.mock import patch

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "An Average City"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

if not pygame.get_init():
    pygame.init()
pygame.display.set_mode((1000, 800))

from Sistemas.SaveSystem import save_global
from Telas.TelaVerso import GerenciadorVerso


CONQUISTAS_CHEFES = ("chefe_sukuna", "chefe_charlie", "chefe_estraga_prazeres")


class TestVersoCyberpunk(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.multiple(
            save_global,
            conquistas=[],
            progresso_versos={},
            habilidades_desabilitadas={},
            pontos=0,
            total_pontos_acumulados=0,
            maior_pontuacao=0,
            member_card_coletado=False,
        ))
        self.salvar = self.enterContext(patch.object(save_global, "salvar"))
        self.personagem = SimpleNamespace(talentos=set(), ultimates_desbloqueadas=set())
        self.enterContext(patch("Telas.TelaVerso.personagem", self.personagem))
        self.superficie = pygame.Surface((1000, 800))

    def clicar(self, tela, posicao):
        tela.atualizar_eventos(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1), posicao)
        return tela.atualizar_eventos(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1), posicao)

    def test_apenas_as_tres_conquistas_dos_chefes_revelam_cyberpunk(self):
        for quantidade in range(4):
            for conquistas in combinations(CONQUISTAS_CHEFES, quantidade):
                with self.subTest(conquistas=conquistas):
                    save_global.conquistas[:] = ["chefe_derrotado", "vitoria_cyberpunk", *conquistas]
                    tela = GerenciadorVerso(self.superficie)
                    esperado = ["Sobrevivente", "Agente", "Feiticeiro"]
                    if quantidade == 3:
                        esperado.append("Cyberpunk")
                    self.assertEqual(tela.versos, esperado)
                    self.assertEqual(set(tela.esferas_rects), set(esperado))

    def test_area_do_verso_oculto_nao_permite_selecao(self):
        tela = GerenciadorVerso(self.superficie)
        for modo in ("menu", "visualizacao"):
            with self.subTest(modo=modo):
                tela.modo = modo
                self.assertIsNone(self.clicar(tela, (230, 575)))
                self.assertEqual(tela.verso_atual, "Sobrevivente")
                self.assertIsNone(tela.habilidade_foco)
        self.salvar.assert_not_called()

    def test_terceira_conquista_revela_na_mesma_tela_e_recupera_talentos(self):
        save_global.conquistas[:] = CONQUISTAS_CHEFES[:2]
        save_global.progresso_versos["Cyberpunk"] = ["C1", "C2", "C4"]
        save_global.habilidades_desabilitadas["Cyberpunk"] = ["C2"]
        tela = GerenciadorVerso(self.superficie)
        self.assertNotIn("Cyberpunk", tela.versos)
        self.assertEqual(tela.progresso_por_verso["Cyberpunk"], ["C1", "C2", "C4"])
        self.assertTrue(tela.arvores_por_verso["Cyberpunk"])

        save_global.desbloquear_conquista(CONQUISTAS_CHEFES[2])
        tela.sincronizar_habilidades_ativas()
        self.assertIn("Cyberpunk", tela.versos)
        self.clicar(tela, tela.esferas_rects["Cyberpunk"].center)
        self.assertEqual(tela.verso_atual, "Cyberpunk")
        self.assertEqual(tela.habilidades_desbloqueadas, ["C1", "C2", "C4"])
        self.assertEqual(tela.habilidades_desabilitadas["Cyberpunk"], {"C2"})
        self.assertEqual(self.personagem.talentos, {"C1", "C4"})

    def test_perder_requisitos_oculta_selecao_sem_apagar_progresso(self):
        save_global.conquistas[:] = CONQUISTAS_CHEFES
        save_global.progresso_versos["Cyberpunk"] = ["C1"]
        tela = GerenciadorVerso(self.superficie)
        self.clicar(tela, tela.esferas_rects["Cyberpunk"].center)
        tela.verso_ativo = "Cyberpunk"
        tela.habilidade_foco = tela.arvores_por_verso["Cyberpunk"][0]
        tela.aviso = "Ultimate desbloqueada para Cyberpunk!"

        save_global.conquistas.remove("chefe_charlie")
        tela.sincronizar_habilidades_ativas()
        self.assertNotIn("Cyberpunk", tela.versos)
        self.assertNotIn("Cyberpunk", tela.esferas_rects)
        self.assertEqual(tela.verso_atual, "Sobrevivente")
        self.assertIsNone(tela.verso_ativo)
        self.assertIsNone(tela.habilidade_foco)
        self.assertEqual(tela.aviso, "")
        self.assertEqual(save_global.progresso_versos["Cyberpunk"], ["C1"])
        self.assertEqual(tela.progresso_por_verso["Cyberpunk"], ["C1"])
        self.assertEqual(self.personagem.talentos, set())

    def test_reset_do_save_oculta_novamente_o_verso(self):
        save_global.conquistas[:] = CONQUISTAS_CHEFES
        tela = GerenciadorVerso(self.superficie)
        self.clicar(tela, tela.esferas_rects["Cyberpunk"].center)
        save_global.resetar_tudo()
        tela.sincronizar_habilidades_ativas()
        self.assertNotIn("Cyberpunk", tela.versos)
        self.assertNotIn("Cyberpunk", tela.esferas_rects)
        self.assertEqual(tela.verso_atual, "Sobrevivente")

    def test_confirmacao_desbloqueada_aplica_talentos_solo_e_cooperativo(self):
        save_global.conquistas[:] = CONQUISTAS_CHEFES
        save_global.progresso_versos["Cyberpunk"] = ["C1", "C4"]
        segundo_jogador = SimpleNamespace(talentos=set(), ultimates_desbloqueadas=set())
        for alvo in (None, segundo_jogador):
            with self.subTest(cooperativo=alvo is not None):
                tela = GerenciadorVerso(self.superficie)
                tela.modo = "visualizacao"
                tela.alvo_personagem = alvo
                self.clicar(tela, tela.esferas_rects["Cyberpunk"].center)
                resultado = self.clicar(tela, tela.botao_selecionar.rect.center)
                self.assertEqual(resultado, "Cyberpunk")
                personagem_alvo = alvo if alvo is not None else self.personagem
                self.assertEqual(personagem_alvo.talentos, {"C1", "C4"})
                self.assertIn("Cyberpunk", personagem_alvo.ultimates_desbloqueadas)


if __name__ == "__main__":
    unittest.main()
