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
pygame.mixer.init()

from Telas.TelaIntro import GerenciadorIntro, carregar_linhas_intro_json
from Sistemas.Fontes import obter_fonte_manga
from Sistemas.Recursos import caminho_dados


class TestTelaIntro(unittest.TestCase):
    def setUp(self):
        self.superficie = pygame.Surface((1000, 800))
        self.intro = GerenciadorIntro(self.superficie)

    def test_carregamento_linhas_json(self):
        """Verifica se as linhas foram carregadas corretamente de Dados/intro.json."""
        linhas = carregar_linhas_intro_json()
        self.assertGreater(len(linhas), 0)
        self.assertEqual(self.intro.linhas, linhas)

    def test_inicializacao_tela_intro(self):
        """Verifica se a tela de introdução inicia com fundo preto, na fase de digitação da primeira linha."""
        self.assertEqual(self.intro.cor_fundo, (0, 0, 0))
        self.assertEqual(self.intro.indice_linha, 0)
        self.assertEqual(self.intro.fase_atual, GerenciadorIntro.FASE_DIGITANDO)
        self.assertEqual(self.intro.caractere_atual, 0)
        self.assertFalse(self.intro.concluido)
        self.assertIsNotNone(self.intro.botao_pular)
        self.assertEqual(self.intro.botao_pular.texto, "PULAR >>")

    def test_fonte_manga_carregada(self):
        """Verifica se a fonte manga é carregada e funcional."""
        fonte = obter_fonte_manga(22)
        self.assertIsNotNone(fonte)
        surf = fonte.render("An Average City", True, (255, 255, 255))
        self.assertGreater(surf.get_width(), 0)

    def test_ciclo_linha_digitando_espera_fadeout(self):
        """Verifica se uma linha passa por FASE_DIGITANDO -> FASE_ESPERA -> FASE_FADEOUT -> Próxima Linha."""
        self.intro.iniciar(tocar_trilha=False)
        self.assertEqual(self.intro.indice_linha, 0)
        self.assertEqual(self.intro.fase_atual, GerenciadorIntro.FASE_DIGITANDO)

        # Simula avanço de caracteres até completar a primeira linha
        linha_len = len(self.intro.linhas[0])
        for _ in range(linha_len * 6 + 100):
            self.intro.atualizar((0, 0), (False, False, False))
            if self.intro.fase_atual != GerenciadorIntro.FASE_DIGITANDO:
                break

        self.assertEqual(self.intro.fase_atual, GerenciadorIntro.FASE_ESPERA)

        # Simula o tempo de espera antes do fade-out
        for _ in range(self.intro.duracao_espera_linha + 2):
            self.intro.atualizar((0, 0), (False, False, False))

        self.assertEqual(self.intro.fase_atual, GerenciadorIntro.FASE_FADEOUT)

        # Simula o tempo de fade-out até transicionar para a próxima linha
        for _ in range(self.intro.duracao_fadeout_linha + 2):
            self.intro.atualizar((0, 0), (False, False, False))

        self.assertEqual(self.intro.indice_linha, 1)
        self.assertEqual(self.intro.fase_atual, GerenciadorIntro.FASE_DIGITANDO)

    def test_exibicao_completa_ao_final(self):
        """Garante que após todas as linhas, a tela transiciona para FASE_COMPLETO."""
        self.intro.iniciar(tocar_trilha=False)

        # Força o avanço de todas as linhas
        while self.intro.indice_linha < len(self.intro.linhas):
            self.intro.avancar_proxima_linha()

        self.assertEqual(self.intro.fase_atual, GerenciadorIntro.FASE_COMPLETO)
        self.assertTrue(self.intro.concluido)

    def test_pular_ou_concluir(self):
        """Verifica se pular salta primeiro para o diálogo completo e depois para o menu."""
        self.intro.iniciar(tocar_trilha=False)
        self.assertFalse(self.intro.concluido)

        # Primeiro pulo: leva à tela de diálogo completo
        res1 = self.intro.pular_ou_concluir()
        self.assertEqual(res1, "")
        self.assertTrue(self.intro.concluido)
        self.assertEqual(self.intro.fase_atual, GerenciadorIntro.FASE_COMPLETO)

        # Segundo pulo: avança para o menu
        res2 = self.intro.pular_ou_concluir()
        self.assertEqual(res2, "menu")

    def test_eventos_teclado_escape_pula_direto_menu(self):
        """Pressionar ESC deve pular imediatamente para o menu."""
        self.intro.iniciar(tocar_trilha=False)
        ev_esc = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        res = self.intro.atualizar_eventos(ev_esc, (0, 0))
        self.assertEqual(res, "menu")

    def test_eventos_teclado_espaco(self):
        """Pressionar Espaço durante digitação completa a linha; na tela completa avança ao menu."""
        self.intro.iniciar(tocar_trilha=False)
        ev_space = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)

        # Durante digitação: conclui a linha atual
        self.assertEqual(self.intro.fase_atual, GerenciadorIntro.FASE_DIGITANDO)
        self.intro.atualizar_eventos(ev_space, (0, 0))
        self.assertEqual(self.intro.fase_atual, GerenciadorIntro.FASE_ESPERA)

        # Avança para o fim completo
        self.intro.pular_ou_concluir()
        self.assertEqual(self.intro.fase_atual, GerenciadorIntro.FASE_COMPLETO)

        # Espaço na tela completa vai ao menu
        res = self.intro.atualizar_eventos(ev_space, (0, 0))
        self.assertEqual(res, "menu")

    def test_clique_botao_pular(self):
        """Clicar no botão PULAR deve levar ao menu imediatamente."""
        self.intro.iniciar(tocar_trilha=False)
        pos_botao = self.intro.botao_pular.rect.center

        ev_down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1)
        ev_up = pygame.event.Event(pygame.MOUSEBUTTONUP, button=1)

        self.intro.atualizar_eventos(ev_down, pos_botao)
        res = self.intro.atualizar_eventos(ev_up, pos_botao)
        self.assertEqual(res, "menu")

    def test_renderizacao_desenhar(self):
        """Garante que desenhar() renderiza sem erros na fase individual e na fase completa."""
        self.intro.iniciar(tocar_trilha=False)
        self.intro.desenhar()

        # Fase de fadeout
        self.intro.fase_atual = GerenciadorIntro.FASE_FADEOUT
        self.intro.alpha_linha = 120
        self.intro.desenhar()

        # Fase completa
        self.intro.fase_atual = GerenciadorIntro.FASE_COMPLETO
        self.intro.alpha_completo = 255
        self.intro.desenhar()


if __name__ == "__main__":
    unittest.main()
