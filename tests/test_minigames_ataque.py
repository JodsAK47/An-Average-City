import math
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

from Gameplay.MinigamesAtaque import GerenciadorMinigameAtaque, normalizar_classe_dano
from Gameplay.Habilidades import Habilidade, banco_habilidades
from Telas.TelaCombate import GerenciadorJogo
from Entidades.Personagem import personagem
from Entidades.Inimigo import Inimigo


class TestMinigamesAtaque(unittest.TestCase):

    def setUp(self):
        self.tela = pygame.Surface((1000, 800))
        self.mg = GerenciadorMinigameAtaque(self.tela)

    def test_normalizacao_classes(self):
        self.assertEqual(normalizar_classe_dano("Invocador"), "Invocador")
        self.assertEqual(normalizar_classe_dano("Invocacao"), "Invocador")
        self.assertEqual(normalizar_classe_dano("Distância"), "Distância")
        self.assertEqual(normalizar_classe_dano("distancia"), "Distância")
        self.assertEqual(normalizar_classe_dano("Magia"), "Magia")
        self.assertEqual(normalizar_classe_dano("Feiticeiro"), "Magia")
        self.assertEqual(normalizar_classe_dano("Físico"), "Físico")
        self.assertEqual(normalizar_classe_dano("fisico"), "Físico")
        self.assertEqual(normalizar_classe_dano("Lutador"), "Físico")

    # ==================== TESTES DE INVOCADOR ====================

    def test_invocador_estilo1_spam_espaco(self):
        """Invocador Tipo 1: Spam de Espaço para encher a barra de invocação sem duplo input no mesmo frame."""
        hab = Habilidade("Invocar Abelha", "Invocador", 20, 10, 1.0, "Invocação", estilo=1)
        self.mg.iniciar(hab)
        self.assertTrue(self.mg.esta_ativo())
        self.assertEqual(self.mg.classe_normalizada, "Invocador")
        self.assertEqual(self.mg.estilo, 1)

        progresso_inicial = self.mg.invoc_progresso
        ev_space = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
        ev_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(500, 400))

        # Pressionar espaço e clicar no mesmo frame não deve somar duas vezes
        self.mg.processar_evento(ev_space, (500, 400))
        prog_apos_espaco = self.mg.invoc_progresso
        self.mg.processar_evento(ev_click, (500, 400))
        self.assertEqual(self.mg.invoc_progresso, prog_apos_espaco)
        self.assertGreater(self.mg.invoc_progresso, progresso_inicial)

        # Continua pressionando espaço respeitando o cooldown de frames até 100%
        for _ in range(15):
            if self.mg.concluido:
                break
            self.mg.atualizar((500, 400), (False, False, False))
            self.mg.atualizar((500, 400), (False, False, False))
            self.mg.processar_evento(ev_space, (500, 400))

        self.assertTrue(self.mg.concluido)
        self.assertGreaterEqual(self.mg.resultado["multiplicador"], 1.35)
        self.assertTrue(self.mg.resultado["sucesso"])

    def test_invocador_estilo2_sequencia_teclas(self):
        """Invocador Tipo 2: Exibe 1 tecla por vez até o tempo acabar, avaliando pelos acertos."""
        hab = Habilidade("Invocar Pássaro", "Invocador", 25, 12, 1.0, "Invocação", estilo=2)
        self.mg.iniciar(hab)
        self.assertEqual(self.mg.classe_normalizada, "Invocador")
        self.assertEqual(self.mg.estilo, 2)
        self.assertEqual(len(self.mg.seq_teclas), 1)

        # Acerta 7 teclas uma por uma; nenhuma deve encerrar o minigame antes do tempo acabar
        for _ in range(7):
            tecla_anterior, key_char, _ = self.mg.seq_tecla_atual
            ev = pygame.event.Event(pygame.KEYDOWN, key=key_char)
            self.mg.processar_evento(ev, (0, 0))
            self.assertFalse(self.mg.concluido)
            self.assertNotEqual(self.mg.seq_tecla_atual[0], tecla_anterior)

        self.assertEqual(self.mg.seq_indice, 7)
        self.assertFalse(self.mg.concluido)

        # Só conclui quando o tempo termina
        while not self.mg.concluido:
            self.mg.atualizar((0, 0), (False, False, False))

        self.assertTrue(self.mg.concluido)
        self.assertGreaterEqual(self.mg.resultado["multiplicador"], 1.35)
        self.assertTrue(self.mg.resultado["sucesso"])

    # ==================== TESTES DE DISTÂNCIA ====================

    def test_distancia_estilo1_alvo_reflexo(self):
        """Distância Tipo 1: Múltiplos alvos que contam por quantidade atingida sem encerrar no primeiro."""
        hab = Habilidade("Boomerang", "Distância", 22, 8, 1.0, "Disparo", estilo=1)
        self.mg.iniciar(hab)
        self.assertEqual(self.mg.classe_normalizada, "Distância")
        self.assertEqual(self.mg.estilo, 1)
        self.assertEqual(len(self.mg.dist_alvos), 3)
        self.assertEqual(self.mg.dist_meta_alvos, 5)

        # Clica no primeiro alvo: conta 1 acerto e NÃO conclui ainda
        alvo_pos = (int(self.mg.dist_alvos[0]["x"]), int(self.mg.dist_alvos[0]["y"]))
        ev_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=alvo_pos)
        self.mg.processar_evento(ev_click, alvo_pos)
        self.assertEqual(self.mg.dist_alvos_atingidos, 1)
        self.assertFalse(self.mg.concluido)

        # Atinge os alvos restantes até completar os 5
        for _ in range(4):
            alvo_pos = (int(self.mg.dist_alvos[0]["x"]), int(self.mg.dist_alvos[0]["y"]))
            ev_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=alvo_pos)
            self.mg.processar_evento(ev_click, alvo_pos)

        self.assertTrue(self.mg.concluido)
        self.assertEqual(self.mg.dist_alvos_atingidos, 5)
        self.assertGreaterEqual(self.mg.resultado["multiplicador"], 1.40)
        self.assertIn("BULLSEYE", self.mg.resultado["feedback"])

    def test_distancia_estilo2_alinhamento_barras(self):
        """Distância Tipo 2: Barras surgem 1 por vez em lados opostos com a mesma velocidade."""
        hab = Habilidade("Estilingada", "Distância", 28, 10, 1.0, "Disparo", estilo=2)
        self.mg.iniciar(hab)
        self.assertEqual(self.mg.classe_normalizada, "Distância")
        self.assertEqual(self.mg.estilo, 2)

        # 1. Verifica se apenas a barra 1 surgiu inicialmente
        self.assertTrue(self.mg.alin_barra1_ativa)
        self.assertFalse(self.mg.alin_barra2_ativa)
        self.assertEqual(self.mg.alin_etapa, 1)

        # 2. Verifica se a velocidade é a mesma para ambas
        self.assertAlmostEqual(abs(self.mg.alin_barra1_vel), abs(self.mg.alin_barra2_vel), places=2)

        # 3. Trava a barra 1 no centro
        self.mg.alin_barra1_x = self.mg.alin_ponto_centro
        ev_space = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
        self.mg.processar_evento(ev_space, (0, 0))

        # Agora a barra 1 está travada e a barra 2 surgiu no lado oposto com a mesma velocidade
        self.assertTrue(self.mg.alin_barra1_travada)
        self.assertTrue(self.mg.alin_barra2_ativa)
        self.assertEqual(self.mg.alin_etapa, 2)
        self.assertFalse(self.mg.concluido)

        # 4. Trava a barra 2 no mesmo ponto para alinhamento perfeito
        self.mg.alin_barra2_x = self.mg.alin_ponto_centro
        self.mg.processar_evento(ev_space, (0, 0))

        self.assertTrue(self.mg.concluido)
        self.assertGreaterEqual(self.mg.resultado["multiplicador"], 1.40)
        self.assertIn("MIRA PERFEITAMENTE ALINHADA", self.mg.resultado["feedback"])

    # ==================== TESTES DE FEITICEIRO (MAGIA) ====================

    def test_feiticeiro_estilo1_esfera_movel(self):
        """Feiticeiro Tipo 1: Manter o cursor dentro de uma esfera em movimento sem encerramento por clique."""
        hab = Habilidade("Azul", "Magia", 35, 15, 1.0, "Arcano", estilo=1)
        self.mg.iniciar(hab)
        self.assertEqual(self.mg.classe_normalizada, "Magia")
        self.assertEqual(self.mg.estilo, 1)

        # Clicar ou apertar espaço não deve encerrar acidentalmente o minigame
        ev_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(500, 400))
        self.mg.processar_evento(ev_click, (500, 400))
        self.assertFalse(self.mg.concluido)

        # Simula manter o mouse na posição da esfera durante os frames necessários
        for _ in range(self.mg.tempo_total):
            if self.mg.concluido:
                break
            pos_esfera = (int(self.mg.esfera_pos[0]), int(self.mg.esfera_pos[1]))
            self.mg.atualizar(pos_esfera, (False, False, False))

        self.assertTrue(self.mg.concluido)
        self.assertGreaterEqual(self.mg.resultado["multiplicador"], 1.35)
        self.assertIn("CANALIZAÇÃO PERFEITA", self.mg.resultado["feedback"])

    def _conduzir_runa_pelo_caminho(self):
        """Helper de teste para arrastar a runa ao longo dos pontos do caminho arcano."""
        for pt in self.mg.drag_caminho_pontos:
            if self.mg.concluido:
                break
            alvo = (int(pt[0]), int(pt[1]))
            for _ in range(3):
                if self.mg.concluido:
                    break
                self.mg.atualizar(alvo, (True, False, False))

    def test_feiticeiro_estilo2_arrastar_runa(self):
        """Feiticeiro Tipo 2: Arrastar a runa pelo caminho arcano até o glifo ritual."""
        hab = Habilidade("Vermelho", "Magia", 40, 18, 1.0, "Arcano", estilo=2)
        self.mg.iniciar(hab)
        self.assertEqual(self.mg.classe_normalizada, "Magia")
        self.assertEqual(self.mg.estilo, 2)

        # Clica na runa
        pos_origem = (int(self.mg.drag_origem[0]), int(self.mg.drag_origem[1]))
        ev_down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos_origem)
        self.mg.processar_evento(ev_down, pos_origem)
        self.assertTrue(self.mg.drag_segurando)

        # Conduz seguindo o caminho até o glifo
        self._conduzir_runa_pelo_caminho()
        if not self.mg.concluido:
            pos_destino = (int(self.mg.drag_destino[0]), int(self.mg.drag_destino[1]))
            ev_up = pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=pos_destino)
            self.mg.processar_evento(ev_up, pos_destino)

        self.assertTrue(self.mg.concluido)
        self.assertGreaterEqual(self.mg.resultado["multiplicador"], 1.35)
        self.assertIn("RITUAL", self.mg.resultado["feedback"])

    def test_feiticeiro_estilo2_auto_ativacao_ao_alcancar_centro(self):
        """Feiticeiro Tipo 2: Auto-conclusão imediata ao conduzir a runa até o centro do glifo."""
        hab = Habilidade("Vermelho", "Magia", 40, 18, 1.0, "Arcano", estilo=2)
        self.mg.iniciar(hab)

        # Clica na runa e arrasta seguindo o caminho até o destino
        pos_origem = (int(self.mg.drag_origem[0]), int(self.mg.drag_origem[1]))
        ev_down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos_origem)
        self.mg.processar_evento(ev_down, pos_origem)
        self.assertTrue(self.mg.drag_segurando)

        self._conduzir_runa_pelo_caminho()

        # Deve auto-ativar ao alcançar o núcleo sem precisar soltar o clique
        self.assertTrue(self.mg.concluido)
        self.assertGreaterEqual(self.mg.resultado["multiplicador"], 1.35)
        self.assertIn("RITUAL PERFEITO", self.mg.resultado["feedback"])

    def test_feiticeiro_estilo2_caminho_dinamico_e_lentidao_fora_da_trilha(self):
        """Feiticeiro Tipo 2: Posições/caminhos variam, atalhos não vencem e sair da trilha reduz velocidade."""
        hab = Habilidade("Chamas Das Trevas", "Magia", 30, 10, 1.0, "Arcano", estilo=2)
        configuracoes = set()
        for _ in range(12):
            self.mg.iniciar(hab)
            configuracoes.add((
                round(self.mg.drag_origem[0], 1),
                round(self.mg.drag_origem[1], 1),
                round(self.mg.drag_destino[0], 1),
                round(self.mg.drag_destino[1], 1),
                self.mg.drag_caminho_tipo,
            ))
        self.assertGreater(len(configuracoes), 1)

        # Tecla D e clique direto no glifo não teletransportam mais
        ev_key = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d)
        self.mg.processar_evento(ev_key, (0, 0))
        self.assertFalse(self.mg.concluido)

        pos_dest = (int(self.mg.drag_destino[0]), int(self.mg.drag_destino[1]))
        ev_click_dest = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos_dest)
        self.mg.processar_evento(ev_click_dest, pos_dest)
        self.assertFalse(self.mg.concluido)

        # Inicia arrasto e força a runa para longe da trilha para medir lentidão
        pos_origem = (int(self.mg.drag_origem[0]), int(self.mg.drag_origem[1]))
        ev_down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos_origem)
        self.mg.processar_evento(ev_down, pos_origem)
        self.assertTrue(self.mg.drag_segurando)

        self.mg.drag_pos_atual = [float(self.mg.x_painel + 40), float(self.mg.y_painel + 90)]
        # Garante que esse ponto esteja fora da trilha caso a origem tenha ficado perto
        if self.mg._distancia_ponto_ao_caminho(*self.mg.drag_pos_atual) <= self.mg.drag_raio_caminho:
            self.mg.drag_pos_atual = [float(self.mg.x_painel + self.mg.largura_painel // 2), float(self.mg.y_painel + self.mg.altura_painel - 40)]

        pos_antes = list(self.mg.drag_pos_atual)
        alvo_longe = (self.mg.x_painel + self.mg.largura_painel - 40, self.mg.y_painel + 160)
        self.mg.atualizar(alvo_longe, (True, False, False))
        deslocamento = math.hypot(self.mg.drag_pos_atual[0] - pos_antes[0], self.mg.drag_pos_atual[1] - pos_antes[1])
        self.assertTrue(self.mg.drag_fora_caminho)
        self.assertLessEqual(deslocamento, 2.0)

    def test_feiticeiro_estilo2_recuperacao_ao_soltar_longe(self):
        """Feiticeiro Tipo 2: Soltar longe não trava o jogo e retorna suavemente para a origem."""
        hab = Habilidade("Mare Dagua", "Magia", 25, 8, 1.0, "Arcano", estilo=2)
        self.mg.iniciar(hab)

        # Inicia arrasto e desloca seguindo os primeiros pontos do caminho
        pos_origem = (int(self.mg.drag_origem[0]), int(self.mg.drag_origem[1]))
        ev_down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos_origem)
        self.mg.processar_evento(ev_down, pos_origem)

        ponto_meio = self.mg.drag_caminho_pontos[3]
        self.mg.atualizar((int(ponto_meio[0]), int(ponto_meio[1])), (True, False, False))
        self.mg.atualizar((int(ponto_meio[0]), int(ponto_meio[1])), (False, False, False))  # soltou

        self.assertFalse(self.mg.drag_segurando)
        self.assertFalse(self.mg.concluido)

        # Atualiza frames subsequentes: a runa deve flutuar em direção à origem
        dist_antes = math.hypot(self.mg.drag_pos_atual[0] - self.mg.drag_origem[0], self.mg.drag_pos_atual[1] - self.mg.drag_origem[1])
        self.mg.atualizar((int(ponto_meio[0]), int(ponto_meio[1])), (False, False, False))
        dist_depois = math.hypot(self.mg.drag_pos_atual[0] - self.mg.drag_origem[0], self.mg.drag_pos_atual[1] - self.mg.drag_origem[1])
        self.assertLess(dist_depois, dist_antes)

    def test_feiticeiro_estilo2_renderizacao_e_animacao(self):
        """Feiticeiro Tipo 2: Renderização visual de origem, caminho dinâmico, glifo e runa sem exceções."""
        hab = Habilidade("Vermelho", "Magia", 40, 18, 1.0, "Arcano", estilo=2)
        self.mg.iniciar(hab)

        # 1. Desenha no estado inicial
        self.mg.desenhar(self.tela)

        # 2. Atualiza e desenha com animação de pulso e fluxo de conduíte
        self.mg.atualizar((500, 400), (False, False, False))
        self.assertGreater(self.mg.tempo_animacao, 0.0)
        self.mg.desenhar(self.tela)

        # 3. Segura a runa e desenha arrastando
        pos_origem = (int(self.mg.drag_origem[0]), int(self.mg.drag_origem[1]))
        ev_down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos_origem)
        self.mg.processar_evento(ev_down, pos_origem)
        self.mg.atualizar((pos_origem[0] + 50, pos_origem[1] + 20), (True, False, False))
        self.mg.desenhar(self.tela)

        # 4. Redimensionamento de tela não quebra renderização
        self.mg.redimensionar(1280, 720)
        self.mg.desenhar(self.tela)

    # ==================== TESTES DE LUTADOR (FÍSICO) ====================

    def test_lutador_estilo1_combo_ritmico(self):
        """Lutador Tipo 1: Acertar a barra de timing consecutivamente."""
        hab = Habilidade("Machadada", "Físico", 30, 8, 1.0, "Golpe", estilo=1)
        self.mg.iniciar(hab)
        self.assertEqual(self.mg.classe_normalizada, "Físico")
        self.assertEqual(self.mg.estilo, 1)

        centro_zona = self.mg.combo_trilha_x + self.mg.combo_trilha_w / 2

        # Acerta 5 vezes no centro
        ev_click = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
        for _ in range(5):
            self.mg.combo_cursor_x = centro_zona
            self.mg.processar_evento(ev_click, (0, 0))

        self.assertTrue(self.mg.concluido)
        self.assertEqual(self.mg.combo_atual, 5)
        self.assertGreaterEqual(self.mg.resultado["multiplicador"], 1.45)
        self.assertIn("COMBO DEVASTADOR", self.mg.resultado["feedback"])

    def test_lutador_estilo1_preserva_combo_ao_errar_ultimo(self):
        """Lutador Tipo 1: Errar após já ter 3 hits preserva o Bom Combo (1.25x)."""
        hab = Habilidade("Machadada", "Físico", 30, 8, 1.0, "Golpe", estilo=1)
        self.mg.iniciar(hab)

        centro_zona = self.mg.combo_trilha_x + self.mg.combo_trilha_w / 2
        ev_click = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
        for _ in range(3):
            self.mg.combo_cursor_x = centro_zona
            self.mg.processar_evento(ev_click, (0, 0))

        self.assertFalse(self.mg.concluido)
        # Erra o 4º golpe fora da zona
        self.mg.combo_cursor_x = self.mg.combo_trilha_x
        self.mg.processar_evento(ev_click, (0, 0))

        self.assertTrue(self.mg.concluido)
        self.assertTrue(self.mg.resultado["sucesso"])
        self.assertAlmostEqual(self.mg.resultado["multiplicador"], 1.25, places=2)
        self.assertIn("BOM COMBO", self.mg.resultado["feedback"])

    def test_lutador_estilo2_carregar_forca(self):
        """Lutador Tipo 2: Segurar tecla para carregar barra de força e soltar no ponto ideal (80-95%)."""
        hab = Habilidade("HamBat", "Físico", 38, 14, 1.0, "Impacto", estilo=2)
        self.mg.iniciar(hab)
        self.assertEqual(self.mg.classe_normalizada, "Físico")
        self.assertEqual(self.mg.estilo, 2)

        ev_down = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
        self.mg.processar_evento(ev_down, (0, 0))
        self.assertTrue(self.mg.forca_segurando)

        # Simula carregamento até atingir a faixa ideal (88%)
        self.mg.forca_atual = 88.0

        ev_up = pygame.event.Event(pygame.KEYUP, key=pygame.K_SPACE)
        self.mg.processar_evento(ev_up, (0, 0))

        self.assertTrue(self.mg.concluido)
        self.assertGreaterEqual(self.mg.resultado["multiplicador"], 1.40)
        self.assertIn("FORÇA MÁXIMA DEVASTADORA", self.mg.resultado["feedback"])

    def test_lutador_estilo2_tolerancia_no_topo_antes_sobrecarga(self):
        """Lutador Tipo 2: Pequena tolerância ao tocar 100% antes de acionar sobrecarga."""
        hab = Habilidade("HamBat", "Físico", 38, 14, 1.0, "Impacto", estilo=2)
        self.mg.iniciar(hab)

        self.mg.forca_segurando = True
        self.mg.forca_atual = 99.5

        class TeclasSimuladas:
            def __getitem__(self, key):
                return key == pygame.K_SPACE

        # Primeiro frame ao bater 100%: ainda não estoura em overcharge
        self.mg.atualizar((0, 0), (False, False, False), teclas_pressionadas=TeclasSimuladas())
        self.assertFalse(self.mg.forca_overcharge)
        self.assertFalse(self.mg.concluido)

        # Segurar continuamente por >= 12 frames no topo aciona sobrecarga
        for _ in range(11):
            self.mg.atualizar((0, 0), (False, False, False), teclas_pressionadas=TeclasSimuladas())

        self.assertTrue(self.mg.forca_overcharge)
        self.assertTrue(self.mg.concluido)

    # ==================== TESTE DE INTEGRAÇÃO COM COMBATE ====================

    def test_integracao_combate_executar_ataque_com_minigame(self):
        """Verifica se o resultado do minigame escala o dano do ataque e gera logs enriquecidos."""
        jogo = GerenciadorJogo(self.tela)
        jogo.minigames_ataque_ativos = True

        inimigo = Inimigo(500, 400, 200, "Maldição 4.png", nome="Alvo Teste")
        inimigo.rect = pygame.Rect(500, 400, 60, 80)
        personagem.rect = pygame.Rect(100, 400, 60, 80)
        personagem.mp = 50

        jogo.ordem_turnos = [personagem, inimigo]
        jogo.indice_turno = 0

        hab = banco_habilidades.get("Machadada")
        if not hab:
            hab = Habilidade("Machadada", "Físico", 30, 8, 1.0, "Corte", estilo=1)

        # Inicia minigame de ataque
        jogo.iniciar_minigame_ataque(hab, alvo=inimigo, jogador_ativo=personagem)
        self.assertEqual(jogo.menu_acoes_estado, "minigame_ataque")
        self.assertTrue(jogo.minigame_ataque.esta_ativo())

        # Conclui minigame com resultado excelente
        resultado = {
            "concluido": True,
            "multiplicador": 1.45,
            "feedback": "COMBO CRÍTICO (+45%)",
            "sucesso": True,
            "screen_shake": True
        }
        hp_antes = inimigo.hp
        jogo.finalizar_minigame_ataque(resultado)

        # Dano deve ter sido aplicado com o bônus
        self.assertLess(inimigo.hp, hp_antes)
        self.assertIn("COMBO CRÍTICO (+45%)", jogo.mensagem_log)
        self.assertEqual(jogo.menu_acoes_estado, "principal")

    def test_chance_erro_acerto_garantido_quando_minigame_perfeito(self):
        """Golpe com baixa precisão base (ex: 0.50) NUNCA erra se o minigame for perfeito (chance_erro=0.0)."""
        jogo = GerenciadorJogo(self.tela)
        jogo.minigames_ataque_ativos = True

        inimigo = Inimigo(500, 400, 200, "Maldição 4.png", nome="Alvo Teste")
        inimigo.rect = pygame.Rect(500, 400, 60, 80)
        personagem.rect = pygame.Rect(100, 400, 60, 80)
        personagem.mp = 50
        personagem.god_mode = False

        jogo.ordem_turnos = [personagem, inimigo]
        jogo.indice_turno = 0

        hab = Habilidade("Ataque Impreciso", "Físico", 30, 5, 0.10, "Corte", estilo=1)
        banco_habilidades["Ataque Impreciso"] = hab

        resultado_perfeito = {
            "concluido": True,
            "multiplicador": 1.45,
            "feedback": "🎯 BULLSEYE! TIRO PERFEITO (+45%)",
            "sucesso": True,
            "desempenho": 1.0,
            "chance_erro": 0.0
        }

        # Executa 20 vezes para assegurar que com chance_erro=0.0 NUNCA erra, mesmo com hab.precisao=0.10
        for _ in range(20):
            inimigo.hp = 200
            personagem.mp = 50
            jogo.iniciar_minigame_ataque(hab, alvo=inimigo, jogador_ativo=personagem)
            jogo.finalizar_minigame_ataque(resultado_perfeito)
            self.assertNotIn("mas ERROU!", jogo.mensagem_log)
            self.assertIn("BULLSEYE", jogo.mensagem_log)
            self.assertLess(inimigo.hp, 200)

    def test_chance_erro_erro_garantido_quando_minigame_falha(self):
        """Golpe com 100% de precisão base ERRA se o jogador falhar completamente o minigame (chance_erro=1.0)."""
        jogo = GerenciadorJogo(self.tela)
        jogo.minigames_ataque_ativos = True

        inimigo = Inimigo(500, 400, 200, "Maldição 4.png", nome="Alvo Teste")
        inimigo.rect = pygame.Rect(500, 400, 60, 80)
        personagem.rect = pygame.Rect(100, 400, 60, 80)
        personagem.mp = 50
        personagem.god_mode = False

        jogo.ordem_turnos = [personagem, inimigo]
        jogo.indice_turno = 0

        hab = Habilidade("Ataque Preciso", "Físico", 30, 5, 1.0, "Corte", estilo=1)
        banco_habilidades["Ataque Preciso"] = hab

        resultado_falha = {
            "concluido": True,
            "multiplicador": 0.70,
            "feedback": "❌ ERROU O ALVO! (-30%)",
            "sucesso": False,
            "desempenho": 0.0,
            "chance_erro": 1.0
        }

        hp_inicial = inimigo.hp
        jogo.iniciar_minigame_ataque(hab, alvo=inimigo, jogador_ativo=personagem)
        jogo.finalizar_minigame_ataque(resultado_falha)

        # Deve registrar que ERROU e o inimigo não toma dano
        self.assertIn("mas ERROU!", jogo.mensagem_log)
        self.assertIn("ERROU O ALVO!", jogo.mensagem_log)
        self.assertEqual(inimigo.hp, hp_inicial)

    def test_invocacao_com_chance_erro_minigame(self):
        """Minigame de invocação: sucesso invoca com bônus de vida, falha cancela a invocação."""
        jogo = GerenciadorJogo(self.tela)
        jogo.minigames_ataque_ativos = True
        personagem.god_mode = False

        hab = Habilidade("Invocar Abelha Teste", "Invocador", 0, 10, 1.0, "Invocação", estilo=1, minion="Abelha")
        banco_habilidades["Invocar Abelha Teste"] = hab

        # Caso 1: Sucesso total no minigame de invocação
        resultado_sucesso = {
            "concluido": True,
            "multiplicador": 1.40,
            "feedback": "⚡ INCRÍVEL!",
            "sucesso": True,
            "desempenho": 1.0,
            "chance_erro": 0.0
        }
        jogo.iniciar_minigame_ataque(hab, alvo=None, jogador_ativo=personagem)
        jogo.finalizar_minigame_ataque(resultado_sucesso)
        self.assertIn("invocou", jogo.mensagem_log)
        minions_ativos = jogo.obter_minions_vivos(personagem)
        self.assertGreaterEqual(len(minions_ativos), 1)

        # Caso 2: Falha total no minigame de invocação
        resultado_falha = {
            "concluido": True,
            "multiplicador": 0.85,
            "feedback": "❌ SEQUÊNCIA INTERROMPIDA",
            "sucesso": False,
            "desempenho": 0.0,
            "chance_erro": 1.0
        }
        qtd_antes = len(jogo.obter_minions_vivos(personagem))
        jogo.iniciar_minigame_ataque(hab, alvo=None, jogador_ativo=personagem)
        jogo.finalizar_minigame_ataque(resultado_falha)
        self.assertIn("a invocação FALHOU!", jogo.mensagem_log)
        self.assertEqual(len(jogo.obter_minions_vivos(personagem)), qtd_antes)

    def test_lutador_sobrecarga_gera_chance_erro_total(self):
        """Lutador Tipo 2 com sobrecarga gera chance_erro = 1.0 e sucesso = False."""
        hab = Habilidade("HamBat", "Físico", 38, 14, 1.0, "Impacto", estilo=2)
        self.mg.iniciar(hab)

        # Simula sobrecarga passando de 100%
        self.mg.forca_overcharge = True
        self.mg._finalizar_lutador_forca()

        self.assertTrue(self.mg.concluido)
        self.assertFalse(self.mg.resultado["sucesso"])
        self.assertEqual(self.mg.resultado["chance_erro"], 1.0)
        self.assertEqual(self.mg.resultado["desempenho"], 0.0)
        self.assertIn("SOBRECARGA", self.mg.resultado["feedback"])

    def test_ultimates_nao_possuem_minigame_no_gerenciador(self):
        """Verifica se habilidades marcadas como is_ultimate=True não disparam minigame."""
        hab_ult = Habilidade("Fúria Brutal Teste", "Físico", 80, 10, 1.0, "Impacto", estilo=1, is_ultimate=True)
        self.mg.iniciar(hab_ult)

        # Deve ser concluído instantaneamente com perfeição, sem minigame interativo
        self.assertTrue(self.mg.concluido)
        self.assertTrue(self.mg.resultado["sucesso"])
        self.assertEqual(self.mg.resultado["desempenho"], 1.0)
        self.assertEqual(self.mg.resultado["chance_erro"], 0.0)

    def test_tela_combate_executa_ultimate_direto_sem_minigame(self):
        """Verifica se a TelaCombate executa a ultimate diretamente sem abrir o menu modal de minigame."""
        from Entidades.EntidadeCombate import EntidadeCombate
        jogo = GerenciadorJogo(self.tela)
        jogo.minigames_ataque_ativos = True

        jogador = EntidadeCombate("Herói", max_hp=100, max_mp=10, is_player=True)
        inimigo = Inimigo(500, 400, 100, "Maldição 4.png", nome="Monstro Alvo")
        inimigo.rect = pygame.Rect(500, 400, 60, 80)
        jogo.ordem_turnos = [jogador, inimigo]

        hab_ult = Habilidade("Relâmpago Celeste Teste", "Distância", 90, 10, 1.0, "Disparo", estilo=1, is_ultimate=True, em_area=False)
        banco_habilidades["Relâmpago Celeste Teste"] = hab_ult

        # Ao chamar iniciar_minigame_ataque com ultimate, deve executar diretamente o ataque
        jogo.iniciar_minigame_ataque(hab_ult, alvo=inimigo, jogador_ativo=jogador)

        # O estado não deve ser "minigame_ataque"
        self.assertNotEqual(jogo.menu_acoes_estado, "minigame_ataque")
        self.assertEqual(jogo.menu_acoes_estado, "principal")
        self.assertIn("Relâmpago Celeste Teste", jogo.mensagem_log)
        self.assertLess(inimigo.hp, 100)


if __name__ == "__main__":
    unittest.main()
