# -*- coding: utf-8 -*-
"""
Testes unitários para o Sistema de Orientação de Sprites (Facing)
Valida:
- Resolução e carregamento da configuração orientacao_sprites.json.
- Lógica de determinação de flip baseada na orientação nativa e direção desejada.
- Orientação correta de Inimigos (sprites nativas à direita são espelhadas para encarar o jogador à esquerda).
- Orientação correta de Minions e Jogador (aliados encarando os inimigos à direita por padrão).
- Métodos virar_para, olhar_para e olhar_para_alvo com preservação do centro de colisão (rect).
- Integração da orientação com ataques físicos e teleporte na TelaCombate.
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

from Sistemas.SistemaOrientacao import sistema_orientacao, OrientacaoNativa
from Entidades.Personagem import Personagem, personagem
from Entidades.Inimigo import Inimigo
from Entidades.Minion import Minion, criar_minion
from Telas.TelaCombate import TelaCombate


class TestSistemaOrientacao(unittest.TestCase):

    def test_carregamento_configuracao_e_nativas(self):
        """Verifica se o sistema carregou corretamente as orientações nativas de sprites conhecidas."""
        self.assertEqual(sistema_orientacao.obter_orientacao_nativa("Hound.png"), OrientacaoNativa.LESTE)
        self.assertEqual(sistema_orientacao.obter_orientacao_nativa("Passaro.png"), OrientacaoNativa.LESTE)
        self.assertEqual(sistema_orientacao.obter_orientacao_nativa("Passaro_Olhudo.png"), OrientacaoNativa.LESTE)
        self.assertEqual(sistema_orientacao.obter_orientacao_nativa("Abelha.png"), OrientacaoNativa.LESTE)
        self.assertEqual(sistema_orientacao.obter_orientacao_nativa("Drone.png"), OrientacaoNativa.LESTE)

        self.assertEqual(sistema_orientacao.obter_orientacao_nativa("Torreta.png"), OrientacaoNativa.LESTE)
        self.assertEqual(sistema_orientacao.obter_orientacao_nativa("Cachorro.png"), OrientacaoNativa.LESTE)
        self.assertEqual(sistema_orientacao.obter_orientacao_nativa("Nue.png"), OrientacaoNativa.LESTE)
        self.assertEqual(sistema_orientacao.obter_orientacao_nativa("pixil.png"), OrientacaoNativa.LESTE)
        self.assertEqual(sistema_orientacao.obter_orientacao_nativa("Cyborg Skin.png"), OrientacaoNativa.LESTE)
        self.assertEqual(sistema_orientacao.obter_orientacao_nativa("Jogo.png"), OrientacaoNativa.LESTE)
        self.assertEqual(sistema_orientacao.obter_orientacao_nativa("Sukuna.png"), OrientacaoNativa.LESTE)
        self.assertEqual(sistema_orientacao.obter_orientacao_nativa("Maldição 4.png"), OrientacaoNativa.LESTE)

        self.assertEqual(sistema_orientacao.obter_orientacao_nativa("Mahoraga.png"), OrientacaoNativa.FRONTAL)
        self.assertEqual(sistema_orientacao.obter_orientacao_nativa("Santuario.png"), OrientacaoNativa.FRONTAL)
        self.assertEqual(sistema_orientacao.obter_orientacao_nativa("Spike.png"), OrientacaoNativa.FRONTAL)

    def test_logica_precisa_flip(self):
        """Valida que precisa_flip retorna o booleano exato sem depender de suposições cegas."""
        # Sprite nativo à direita (ex: Hound):
        # Para olhar a leste (sua direção nativa): NÃO precisa de flip
        self.assertFalse(sistema_orientacao.precisa_flip("Hound.png", "leste"))
        # Para olhar a oeste (encarar jogador): PRECISA de flip
        self.assertTrue(sistema_orientacao.precisa_flip("Hound.png", "oeste"))

        # Sprite nativo à direita (ex: Torreta):
        self.assertFalse(sistema_orientacao.precisa_flip("Torreta.png", "leste"))
        self.assertTrue(sistema_orientacao.precisa_flip("Torreta.png", "oeste"))

        # Sprite frontal (ex: Mahoraga):
        self.assertFalse(sistema_orientacao.precisa_flip("Mahoraga.png", "leste"))
        self.assertFalse(sistema_orientacao.precisa_flip("Mahoraga.png", "oeste"))

    def test_normalizacao_direcao(self):
        """Valida a conversão de sinônimos para os padrões 'leste', 'oeste' e 'frontal'."""
        for sin in ["direita", "leste", "east", "right", "d", "DIREITA"]:
            self.assertEqual(sistema_orientacao.normalizar_direcao(sin), OrientacaoNativa.LESTE)

        for sin in ["esquerda", "oeste", "west", "left", "e", "ESQUERDA"]:
            self.assertEqual(sistema_orientacao.normalizar_direcao(sin), OrientacaoNativa.OESTE)

        for sin in ["frontal", "centro", "front", "meio"]:
            self.assertEqual(sistema_orientacao.normalizar_direcao(sin), OrientacaoNativa.FRONTAL)

    def test_inimigo_hound_olha_oeste_com_flip(self):
        """Garante que o Hound na posição de inimigo (olhando para oeste) É espelhado para encarar o jogador."""
        hound = Inimigo(x=700, y=400, vida_maxima=45, nome_imagem="Hound.png", nome="Hound Teste")
        self.assertEqual(hound.direcao_olhar, "oeste")
        # Hound é nativo leste; ao encarar oeste, sua imagem deve ser um flip de imagem_base
        w, h = hound.imagem.get_size()
        pixel_base_esq = hound.imagem_base.get_at((5, h // 2))
        pixel_render_dir = hound.imagem.get_at((w - 6, h // 2))
        self.assertEqual(pixel_base_esq, pixel_render_dir)

        # Se virarmos para leste, aí sim desfaz o flip e fica igual à imagem_base
        hound.virar_para("leste")
        self.assertEqual(hound.direcao_olhar, "leste")
        pixel_render_esq = hound.imagem.get_at((5, h // 2))
        self.assertEqual(pixel_base_esq, pixel_render_esq)

    def test_inimigo_torreta_olha_oeste_com_flip(self):
        """Garante que a Torreta na posição de inimigo (olhando para oeste) É espelhada para encarar o jogador."""
        torreta = Inimigo(x=700, y=400, vida_maxima=30, nome_imagem="Torreta.png", nome="Torreta Teste")
        self.assertEqual(torreta.direcao_olhar, "oeste")
        w, h = torreta.imagem.get_size()
        pixel_base_esq = torreta.imagem_base.get_at((5, h // 2))
        pixel_render_dir = torreta.imagem.get_at((w - 6, h // 2))
        self.assertEqual(pixel_base_esq, pixel_render_dir)

    def test_preservacao_centro_rect_ao_virar(self):
        """Valida que virar_para mantém o centro geométrico do rect (sem saltos de posição)."""
        inimigo = Inimigo(x=700, y=400, vida_maxima=50, nome_imagem="Hound.png")
        centro_inicial = inimigo.rect.center

        inimigo.virar_para("leste")
        self.assertEqual(inimigo.rect.center, centro_inicial)

        inimigo.virar_para("oeste")
        self.assertEqual(inimigo.rect.center, centro_inicial)

    def test_minion_cachorro_orientacao(self):
        """Valida que minions no lado do jogador (olhando para leste) encaram os inimigos à direita."""
        cao = Minion(x=350, y=400, nome="Cão Divino", nome_imagem="Cachorro.png")
        self.assertEqual(cao.direcao_olhar, "leste")
        # Cão Divino é nativo leste, então para olhar leste NÃO precisa de flip
        w_c, h_c = cao.imagem.get_size()
        pixel_c_base = cao.imagem_base.get_at((5, h_c // 2))
        pixel_c_atual = cao.imagem.get_at((5, h_c // 2))
        self.assertEqual(pixel_c_base, pixel_c_atual)

    def test_olhar_para_alvo(self):
        """Valida a detecção dinâmica de alvo à esquerda vs direita."""
        p = Personagem(x=200, y=400, nome_imagem="pixil.png")
        self.assertEqual(p.direcao_olhar, "leste")

        # Alvo à direita (x=700) -> deve permanecer olhando para leste
        alvo_direita = Inimigo(x=700, y=400, vida_maxima=40, nome_imagem="Hound.png")
        p.olhar_para_alvo(alvo_direita)
        self.assertEqual(p.direcao_olhar, "leste")

        # Alvo à esquerda (x=50) -> deve virar para oeste
        alvo_esquerda = Inimigo(x=50, y=400, vida_maxima=40, nome_imagem="Hound.png")
        p.olhar_para_alvo(alvo_esquerda)
        self.assertEqual(p.direcao_olhar, "oeste")

    def test_tela_combate_orientacao_em_ataque_fisico(self):
        """Garante que atacantes encaram o alvo durante o teleporte e retornam à direção correta."""
        tela = pygame.display.get_surface()
        jogo = TelaCombate(tela)

        p = Personagem(x=260, y=400, nome_imagem="pixil.png")
        inimigo = Inimigo(x=740, y=400, vida_maxima=50, nome_imagem="Hound.png")
        jogo.ordem_turnos = [p, inimigo]

        # Jogador (à esquerda em x=260) ataca inimigo (à direita em x=740)
        jogo.disparar_ataque_fisico_teleporte(p, inimigo, duracao=10)
        jogo.atualizar_animacao_ataque_fisico()
        self.assertEqual(p.direcao_olhar, "leste")

        # Inimigo (à direita em x=740) ataca jogador (à esquerda em x=260)
        jogo.disparar_ataque_fisico_teleporte(inimigo, p, duracao=10)
        jogo.atualizar_animacao_ataque_fisico()
        # O inimigo foi posicionado à direita do jogador, olhando para o oeste em direção a ele
        self.assertEqual(inimigo.direcao_olhar, "oeste")

        # Finaliza animação e avança turno
        jogo.avancar_turno()
        self.assertIsNone(jogo.animacao_ataque_fisico)
        self.assertEqual(inimigo.direcao_olhar, "oeste")

    def test_todos_summons_em_combate_encaram_inimigos_a_direita(self):
        """Valida que todos os summons (inclusive os que tinham inverter_horizontal no JSON) encaram a direita no combate."""
        tela = pygame.display.get_surface()
        jogo = TelaCombate(tela)

        nomes_summons = ["Abelha Soldado", "Pássaro Olhudo", "Torreta Sentinela", "Drone Caçador", "Cão Divino", "Nue"]
        for nome_summon in nomes_summons:
            m = jogo.invocar_minion(nome_summon, dono=personagem)
            self.assertEqual(m.direcao_olhar, "leste", f"Summon '{nome_summon}' deve olhar para leste (direita)")
            # Como todas as artes base são nativas à direita, olhar para leste significa que a imagem NÃO está invertida
            w, h = m.imagem.get_size()
            mesma_imagem = all(
                m.imagem.get_at((x, y)) == m.imagem_base.get_at((x, y))
                for x in range(0, w, 4) for y in range(0, h, 4)
            )
            self.assertTrue(mesma_imagem, f"Summon '{nome_summon}' deve usar a orientação voltada para a direita")
            jogo.ordem_turnos.remove(m)


if __name__ == "__main__":
    unittest.main()
