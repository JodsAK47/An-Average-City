# -*- coding: utf-8 -*-
"""
Testes unitários para a exibição dos ícones de Vida (HP) e Mana/Foco (PM)
na HUD do combate e alternância dinâmica do ícone de recurso com base
na skill tree do Feiticeiro (talento F2 - Domínio Simples).
"""

import os
import sys
import unittest
import pygame

# Inicialização headless do Pygame para testes
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

# Assegura que o diretório do projeto esteja no sys.path
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
DIRETORIO_RAIZ = os.path.abspath(os.path.join(DIRETORIO_ATUAL, ".."))
if DIRETORIO_RAIZ not in sys.path:
    sys.path.insert(0, DIRETORIO_RAIZ)
DIRETORIO_PROJETO = os.path.join(DIRETORIO_RAIZ, "An Average City")
if DIRETORIO_PROJETO not in sys.path:
    sys.path.insert(0, DIRETORIO_PROJETO)

pygame.init()
pygame.display.set_mode((1000, 768))

from Sistemas.SistemaEfeitos import (
    carregar_icone_efeito,
    obter_efeitos_ativos,
    entidade_anula_debuff_foco,
    obter_icone_recurso_entidade,
    CONFIG_EFEITOS,
)
from Telas.CombateHUD import desenhar_cartoes_jogadores
from Entidades.Personagem import Personagem, personagem


class EntidadeSimulada:
    """Entidade fictícia para testes de verificação de talentos e efeitos."""
    def __init__(self, hp=100, max_hp=100, mp=10, max_mp=10, talentos=None):
        self.hp = hp
        self.max_hp = max_hp
        self.mp = mp
        self.max_mp = max_mp
        self.talentos = talentos or {}
        self.recuperando = False
        self.focado = False
        self.is_player = True
        self.rect = pygame.Rect(100, 100, 32, 32)

    def tem_talento(self, id_talento: str) -> bool:
        if isinstance(self.talentos, dict):
            return bool(self.talentos.get(id_talento, False))
        if isinstance(self.talentos, (set, list, tuple)):
            return id_talento in self.talentos
        return False


class TestHUDIconesVidaManaEFoco(unittest.TestCase):

    def setUp(self):
        self.tela = pygame.Surface((1024, 768))
        self.fonte = pygame.font.Font(None, 16)

    def test_carregamento_sprites_vida_mana_foco(self):
        """Verifica se os sprites Vida.png, Mana.png e Foco.png carregam corretamente."""
        surf_vida = carregar_icone_efeito("Vida.png", 16)
        surf_mana = carregar_icone_efeito("Mana.png", 16)
        surf_foco = carregar_icone_efeito("Foco.png", 16)

        self.assertIsNotNone(surf_vida)
        self.assertEqual(surf_vida.get_size(), (16, 16))

        self.assertIsNotNone(surf_mana)
        self.assertEqual(surf_mana.get_size(), (16, 16))

        self.assertIsNotNone(surf_foco)
        self.assertEqual(surf_foco.get_size(), (16, 16))

    def test_entidade_anula_debuff_foco(self):
        """Testa detecção do talento F2 do Feiticeiro (Domínio Simples)."""
        jogador_sem_talento = EntidadeSimulada(talentos={})
        self.assertFalse(entidade_anula_debuff_foco(jogador_sem_talento))

        jogador_com_f1 = EntidadeSimulada(talentos={"F1": True})
        self.assertFalse(entidade_anula_debuff_foco(jogador_com_f1))

        jogador_com_f2_dict = EntidadeSimulada(talentos={"F1": True, "F2": True})
        self.assertTrue(entidade_anula_debuff_foco(jogador_com_f2_dict))

        jogador_com_f2_set = EntidadeSimulada(talentos={"F2"})
        self.assertTrue(entidade_anula_debuff_foco(jogador_com_f2_set))

    def test_obter_icone_recurso_entidade_alterna_mana_e_foco(self):
        """
        Garante que o ícone retornado é Mana.png para quem possui F2,
        e Foco.png para quem NÃO possui o talento F2.
        """
        jogador_com_f2 = EntidadeSimulada(talentos={"F2": True})
        _, nome_arq_com_f2 = obter_icone_recurso_entidade(jogador_com_f2, 16)
        self.assertEqual(nome_arq_com_f2, "Mana.png")

        jogador_sem_f2 = EntidadeSimulada(talentos={})
        _, nome_arq_sem_f2 = obter_icone_recurso_entidade(jogador_sem_f2, 16)
        self.assertEqual(nome_arq_sem_f2, "Foco.png")

    def test_efeitos_ativos_foco_debuff_vs_buff_com_f2(self):
        """
        Em obter_efeitos_ativos:
        - Sem F2: o efeito de foco é exibido como debuff com Foco.png.
        - Com F2: o debuff é anulado e vira buff estável com Mana.png.
        """
        jogador_focado_sem_f2 = EntidadeSimulada(talentos={})
        jogador_focado_sem_f2.recuperando = True
        efeitos_sem_f2 = obter_efeitos_ativos(jogador_focado_sem_f2)

        efeito_foco_sem_f2 = next((e for e in efeitos_sem_f2 if "foco" in e.get("nome", "").lower() or e.get("id") == "recuperando"), None)
        self.assertIsNotNone(efeito_foco_sem_f2)
        self.assertEqual(efeito_foco_sem_f2.get("arquivo"), "Foco.png")
        self.assertEqual(efeito_foco_sem_f2.get("tag"), "DEBUFF")

        jogador_focado_com_f2 = EntidadeSimulada(talentos={"F2": True})
        jogador_focado_com_f2.recuperando = True
        efeitos_com_f2 = obter_efeitos_ativos(jogador_focado_com_f2)

        efeito_foco_com_f2 = next((e for e in efeitos_com_f2 if "foco" in e.get("nome", "").lower() or e.get("id") == "foco_estavel"), None)
        self.assertIsNotNone(efeito_foco_com_f2)
        self.assertEqual(efeito_foco_com_f2.get("arquivo"), "Mana.png")
        self.assertEqual(efeito_foco_com_f2.get("tag"), "BUFF")

    def test_combate_hud_renderiza_cartoes_e_tooltips_icones(self):
        """Testa desenho dos cartões na CombateHUD e hover nos ícones de Vida e Mana/Foco."""
        jogador1 = EntidadeSimulada(talentos={"F2": True})
        jogadores = [jogador1]

        # 1. Renderização geral sem mouse sobre ícones
        hovered = desenhar_cartoes_jogadores(
            tela=self.tela,
            jogadores_status=jogadores,
            turno_ativo=jogador1,
            personagem_p1=jogador1,
            fonte_status=self.fonte,
            eh_minion_func=lambda j: False,
            limite_minions_func=lambda j: 2,
            tipo_classe_func=lambda j: "Feiticeiro",
            obter_efeito_controle_func=lambda j: None,
            posicao_mouse=(0, 0),
        )
        self.assertIsNone(hovered)

        # 2. Hover sobre o ícone de Vida (rect_status.x + 10, y_hp - 1)
        # Para 1 jogador centralizado: x_cartao = (1024 - 290) // 2 = 367.
        # y_base_status = 716, y_hp = 716 + 28 = 744.
        x_icone_esperado = 367 + 10  # 377
        y_icone_hp_esperado = 744 - 1  # 743

        hovered_vida = desenhar_cartoes_jogadores(
            tela=self.tela,
            jogadores_status=jogadores,
            turno_ativo=jogador1,
            personagem_p1=jogador1,
            fonte_status=self.fonte,
            eh_minion_func=lambda j: False,
            limite_minions_func=lambda j: 2,
            tipo_classe_func=lambda j: "Feiticeiro",
            obter_efeito_controle_func=lambda j: None,
            posicao_mouse=(x_icone_esperado + 4, y_icone_hp_esperado + 4),
        )
        self.assertIsNotNone(hovered_vida)
        self.assertEqual(hovered_vida.get("arquivo"), "Vida.png")
        self.assertIn("Vida", hovered_vida.get("nome"))

        # 3. Hover sobre o ícone de Mana do jogador COM F2
        y_icone_mp_esperado = 716 + 46 - 1  # 761
        hovered_mana = desenhar_cartoes_jogadores(
            tela=self.tela,
            jogadores_status=jogadores,
            turno_ativo=jogador1,
            personagem_p1=jogador1,
            fonte_status=self.fonte,
            eh_minion_func=lambda j: False,
            limite_minions_func=lambda j: 2,
            tipo_classe_func=lambda j: "Feiticeiro",
            obter_efeito_controle_func=lambda j: None,
            posicao_mouse=(x_icone_esperado + 4, y_icone_mp_esperado + 4),
        )
        self.assertIsNotNone(hovered_mana)
        self.assertEqual(hovered_mana.get("arquivo"), "Mana.png")
        self.assertIn("Mana", hovered_mana.get("nome"))

        # 4. Hover sobre o ícone de recurso do jogador SEM F2 -> deve ser Foco.png
        jogador_sem_f2 = EntidadeSimulada(talentos={})
        hovered_foco = desenhar_cartoes_jogadores(
            tela=self.tela,
            jogadores_status=[jogador_sem_f2],
            turno_ativo=jogador_sem_f2,
            personagem_p1=jogador_sem_f2,
            fonte_status=self.fonte,
            eh_minion_func=lambda j: False,
            limite_minions_func=lambda j: 2,
            tipo_classe_func=lambda j: "Guerreiro",
            obter_efeito_controle_func=lambda j: None,
            posicao_mouse=(x_icone_esperado + 4, y_icone_mp_esperado + 4),
        )
        self.assertIsNotNone(hovered_foco)
        self.assertEqual(hovered_foco.get("arquivo"), "Foco.png")
        self.assertIn("Foco", hovered_foco.get("nome"))

    def test_tela_combate_integracao_icones(self):
        """Testa o desenho dos cartões e ícones dentro de uma instância real de TelaCombate."""
        from Telas.TelaCombate import TelaCombate
        tela_combate = TelaCombate(self.tela)

        # Sem F2
        personagem.talentos = {}
        personagem.hp = 100
        personagem.max_hp = 100
        personagem.mp = 10
        personagem.max_mp = 10

        # Para tela_combate com 1 jogador centralizado (tela width 1024)
        x_cartao = (self.tela.get_width() - 290) // 2
        y_base = 716
        x_icone = x_cartao + 10
        y_hp_icone = y_base + 28 - 1
        y_mp_icone = y_base + 46 - 1

        # Mouse sobre ícone de vida
        tela_combate.desenhar((x_icone + 3, y_hp_icone + 3))
        self.assertIsNotNone(tela_combate.ultimo_efeito_hovered)
        self.assertEqual(tela_combate.ultimo_efeito_hovered.get("arquivo"), "Vida.png")

        # Mouse sobre ícone de recurso sem F2 -> Foco.png
        tela_combate.desenhar((x_icone + 3, y_mp_icone + 3))
        self.assertIsNotNone(tela_combate.ultimo_efeito_hovered)
        self.assertEqual(tela_combate.ultimo_efeito_hovered.get("arquivo"), "Foco.png")

        # Com F2
        personagem.talentos = {"F2": True}
        tela_combate.desenhar((x_icone + 3, y_mp_icone + 3))
        self.assertIsNotNone(tela_combate.ultimo_efeito_hovered)
        self.assertEqual(tela_combate.ultimo_efeito_hovered.get("arquivo"), "Mana.png")


if __name__ == "__main__":
    unittest.main()
