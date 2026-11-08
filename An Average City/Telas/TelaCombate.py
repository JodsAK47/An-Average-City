import os
import time
import math
import pygame
import random
from Entidades.Personagem import personagem, Personagem
from Entidades.Santuario import Santuario
from Entidades.Spike import Spike
from Sistemas.SistemaUI import Botao, TelaBase
from Gameplay.MinigameSpike import MinigameSpike
from Gameplay.MinigameEsquiva import MinigameEsquiva
from Gameplay.MinigamesAtaque import GerenciadorMinigameAtaque
from Sistemas.Constantes import (
    Verso,
    Classe,
    normalizar_identificador,
    obter_equipamento_inicial,
    obter_multiplicador_verso_classe,
    obter_musica_combate,
)
from Gameplay.Habilidades import banco_habilidades, obter_ultimate
from Sistemas.Fontes import obter_fonte, quebrar_texto
from Gameplay.GeracaoFases import GeradorFase, BANCO_INIMIGOS, _criar_inimigo_a_partir_template, executar_efeito_evento
from Sistemas.Recursos import caminho_imagem, caminho_sfx, caminho_vfx
from Sistemas.GerenciadorAudio import tocar_sfx
from Sistemas.SistemaEfeitos import (
    obter_efeitos_ativos,
    desenhar_icones_entidade,
    desenhar_tooltip_efeito,
    carregar_icone_efeito,
    entidade_anula_debuff_foco,
    obter_icone_recurso_entidade,
)

MAPA_ATRIBUTO_CLASSE = {
    "Físico": "For",
    "Fisico": "For",
    "Magia": "Int",
    "Distância": "Agi",
    "Distancia": "Agi",
    "Invocador": "Sab",
    "Invocação": "Sab",
    "Invocacao": "Sab",
}

TABELA_EQUIPAMENTOS_INICIAIS = {
    ("Sobrevivente", "Físico"): ("Machado", {"For": 2}),
    ("Sobrevivente", "Fisico"): ("Machado", {"For": 2}),
    ("Sobrevivente", "Distância"): ("Estilingue", {"Agi": 2}),
    ("Sobrevivente", "Distancia"): ("Estilingue", {"Agi": 2}),
    ("Sobrevivente", "Magia"): ("Pedra Preciosa Multicor", {"Int": 2}),
    ("Sobrevivente", "Invocador"): ("Flauta de Pã", {"Sab": 2}),
    ("Survivor", "Físico"): ("Machado", {"For": 2}),
    ("Survivor", "Fisico"): ("Machado", {"For": 2}),
    ("Survivor", "Distância"): ("Estilingue", {"Agi": 2}),
    ("Survivor", "Distancia"): ("Estilingue", {"Agi": 2}),
    ("Survivor", "Magia"): ("Pedra Preciosa Multicor", {"Int": 2}),
    ("Survivor", "Invocador"): ("Flauta de Pã", {"Sab": 2}),

    ("Agente", "Físico"): ("Faca de Confronto", {"For": 2}),
    ("Agente", "Fisico"): ("Faca de Confronto", {"For": 2}),
    ("Agente", "Distância"): ("Vandal", {"Agi": 2}),
    ("Agente", "Distancia"): ("Vandal", {"Agi": 2}),
    ("Agente", "Magia"): ("Rocha De Radianita", {"Int": 2}),
    ("Agente", "Invocador"): ("Bracelete de Comando", {"Sab": 2}),
    ("Agent", "Físico"): ("Faca de Confronto", {"For": 2}),
    ("Agent", "Fisico"): ("Faca de Confronto", {"For": 2}),
    ("Agent", "Distância"): ("Vandal", {"Agi": 2}),
    ("Agent", "Distancia"): ("Vandal", {"Agi": 2}),
    ("Agent", "Magia"): ("Rocha De Radianita", {"Int": 2}),
    ("Agent", "Invocador"): ("Bracelete de Comando", {"Sab": 2}),

    ("Feiticeiro", "Físico"): ("Katana", {"For": 2}),
    ("Feiticeiro", "Fisico"): ("Katana", {"For": 2}),
    ("Feiticeiro", "Distância"): ("Amplificador de alcance", {"Agi": 2}),
    ("Feiticeiro", "Distancia"): ("Amplificador de alcance", {"Agi": 2}),
    ("Feiticeiro", "Magia"): ("Ferramenta Amaldiçoada", {"Int": 2}),
    ("Feiticeiro", "Invocador"): ("Amuleto das Dez Sombras", {"Sab": 2}),
    ("Sorcerer", "Físico"): ("Katana", {"For": 2}),
    ("Sorcerer", "Fisico"): ("Katana", {"For": 2}),
    ("Sorcerer", "Distância"): ("Amplificador de alcance", {"Agi": 2}),
    ("Sorcerer", "Distancia"): ("Amplificador de alcance", {"Agi": 2}),
    ("Sorcerer", "Magia"): ("Ferramenta Amaldiçoada", {"Int": 2}),
    ("Sorcerer", "Invocador"): ("Amuleto das Dez Sombras", {"Sab": 2}),
}

def _obter_equipamento_inicial(verso, classe_dano):
    if (verso, classe_dano) in TABELA_EQUIPAMENTOS_INICIAIS:
        return TABELA_EQUIPAMENTOS_INICIAIS[(verso, classe_dano)]

    v_str = str(verso or "").strip().lower()
    c_str = str(classe_dano or "").strip().lower()

    for (k_v, k_c), item in TABELA_EQUIPAMENTOS_INICIAIS.items():
        if k_v.lower() == v_str and k_c.lower() == c_str:
            return item

    mapa_v = {
        "sobrevivente": "Sobrevivente", "survivor": "Sobrevivente",
        "agente": "Agente", "agent": "Agente",
        "feiticeiro": "Feiticeiro", "sorcerer": "Feiticeiro",
    }
    mapa_c = {
        "fisico": "Físico", "físico": "Físico",
        "distancia": "Distância", "distância": "Distância",
        "magia": "Magia",
        "invocador": "Invocador",
    }
    v_norm = mapa_v.get(v_str, verso)
    c_norm = mapa_c.get(c_str, classe_dano)
    return TABELA_EQUIPAMENTOS_INICIAIS.get((v_norm, c_norm), ("Equipamento Padrão", {}))

MULTIPLICADORES_VERSO_TIPO = {
    ("Sobrevivente", "Físico"): 2.0,
    ("Sobrevivente", "Fisico"): 2.0,
    ("Survivor", "Físico"): 2.0,
    ("Survivor", "Fisico"): 2.0,
    ("Feiticeiro", "Magia"): 2.0,
    ("Sorcerer", "Magia"): 2.0,
    ("Agente", "Distância"): 1.8,
    ("Agente", "Distancia"): 1.8,
    ("Agent", "Distância"): 1.8,
    ("Agent", "Distancia"): 1.8,
    ("Sobrevivente", "Invocador"): 1.8,
    ("Survivor", "Invocador"): 1.8,
    ("Sobrevivente", "Invocação"): 1.8,
    ("Sobrevivente", "Invocacao"): 1.8,
    ("Survivor", "Invocação"): 1.8,
    ("Survivor", "Invocacao"): 1.8,
    ("Agente", "Invocador"): 1.8,
    ("Agent", "Invocador"): 1.8,
    ("Agente", "Invocação"): 1.8,
    ("Agente", "Invocacao"): 1.8,
    ("Agent", "Invocação"): 1.8,
    ("Agent", "Invocacao"): 1.8,
    ("Feiticeiro", "Invocador"): 2.0,
    ("Sorcerer", "Invocador"): 2.0,
    ("Feiticeiro", "Invocação"): 2.0,
    ("Feiticeiro", "Invocacao"): 2.0,
    ("Sorcerer", "Invocação"): 2.0,
    ("Sorcerer", "Invocacao"): 2.0,
}

class GerenciadorJogo(TelaBase):
    def __init__(self, tela):
        super().__init__(tela, nome="combate")
        self.tela = tela
        self.duas_pessoas = False
        self.personagem2 = None
        self.classe_jogador2 = None
        self.classe_jogador2_tipo = None
        self.ordem_turnos = [personagem]
        self.minions_ativos = []

        self.indice_turno = 0
        self.classe_atual = "Nenhuma"
        self.ataque_selecionado = None
        self.botoes_habilidades_dinamicos = []
        self.musica_luta = self.obter_musica_combate(eh_chefe=False)
        self.xp_calculado = False 

        self.turno_jogador_iniciado = False
        self.menu_acoes_estado = "principal"
        self.clique_anterior = False
        self.timer_inimigo = 0
        self.tempo_espera_inimigo = 120  # Aumentado em 50% (era 80)
        self.cooldown_feedback = 0
        self.tempo_cooldown_maximo = 75  # Aumentado em 50% (era 50)
        self.acao_pos_feedback = None
        self.alvo_destaque = None
        self.derrota_processada = False
        self.evento_neutro = None
        self.multiplicador_recompensa = 1.0
        self.efeito_hovered_ativo = None
        self.derrota_processada = False
        self.cooldown_feedback = 0
        self.acao_pos_feedback = None
        self.ultimo_chefe_combate = None
        self.fase_numero = 1
        self.gerador_fases = GeradorFase(self.fase_numero)
        self.partida_atual = 1
        self.total_partidas = 9
        self.pontos_jogo = 0
        self.kills_total = 0
        self.dano_causado_total = 0
        self.dificuldade_total = 0
        self.ultimo_resultado_batalha = None

        self.esquiva_x = 0
        self.esquiva_dir = 1
        self.esquiva_vel = 4.8
        self.barras_esquiva = []
        self.rodada_esquiva = 0
        self.espera_esquiva = 0
        self.total_rodadas_esquiva = 3
        self.acertos_esquiva = 0
        self.acertos_centro_esquiva = 0
        self.reducao_esquiva = 0.0
        self.dano_pendente = 0
        self.atacante_nome = ""
        self.efeitos_pendentes = []
        self.chance_efeito_pendente = 0.0
        self.minigame_esquiva = MinigameEsquiva(total_rodadas=3, tela=self.tela)

        self.minigame_ataque = GerenciadorMinigameAtaque(self.tela)
        self.minigames_ataque_ativos = True

        hud_x = (self.tela.get_width() - 640) // 2
        largura_btn = 125
        gap = 16
        y_btn = 640
        h_btn = 46
        self.btn_agir      = Botao(hud_x + 25 + 0 * (largura_btn + gap), y_btn, largura_btn, h_btn, "AGIR", (140, 25, 25), (190, 40, 40), largura_btn + 4, h_btn + 4, cor_texto=(255,255,255), fonte_tamanho=12)
        self.btn_ataque    = self.btn_agir
        self.btn_foco      = Botao(hud_x + 25 + 1 * (largura_btn + gap), y_btn, largura_btn, h_btn, "FOCO", (25, 120, 45), (40, 170, 65), largura_btn + 4, h_btn + 4, cor_texto=(255,255,255), fonte_tamanho=12)
        self.btn_recuperar = self.btn_foco
        self.btn_item      = Botao(hud_x + 25 + 2 * (largura_btn + gap), y_btn, largura_btn, h_btn, "ITEM", (25, 95, 140), (40, 145, 210), largura_btn + 4, h_btn + 4, cor_texto=(255,255,255), fonte_tamanho=12)
        self.btn_fugir     = Botao(hud_x + 25 + 3 * (largura_btn + gap), y_btn, largura_btn, h_btn, "FUGIR", (60, 60, 75), (95, 95, 115), largura_btn + 4, h_btn + 4, cor_texto=(255,255,255), fonte_tamanho=12)
        self.btn_voltar    = Botao(hud_x + 25 + 3 * (largura_btn + gap), y_btn, largura_btn, h_btn, "VOLTAR", (75, 75, 85), (110, 110, 120), largura_btn + 4, h_btn + 4, cor_texto=(255,255,255), fonte_tamanho=12)
        self.btn_desarmar_spike = Botao(hud_x + 25 + 3 * (largura_btn + gap), y_btn, largura_btn, h_btn, "DESARMAR", (20, 110, 140), (35, 170, 220), largura_btn + 4, h_btn + 4, cor_texto=(200, 255, 255), fonte_tamanho=11)
        self.btn_cancelar_desarme = Botao((self.tela.get_width() - 180) // 2, 665, 180, 36, "CANCELAR (ESC)", (60, 25, 30), (100, 35, 45), 184, 40, cor_texto=(255, 180, 180), fonte_tamanho=12)
        self.btn_pausa = Botao(845, 24, 125, 42, "⏸ MENU", (32, 38, 54), (50, 64, 88), 128, 44, cor_texto=(230, 235, 245), fonte_tamanho=12, borda_raio=8)

        # Botões do submenu AGIR (Atacar, Bloquear, Voltar)
        self.btn_agir_atacar   = Botao(hud_x + 25 + 0 * (largura_btn + gap), y_btn, largura_btn, h_btn, "ATACAR", (140, 25, 25), (190, 40, 40), largura_btn + 4, h_btn + 4, cor_texto=(255,255,255), fonte_tamanho=12)
        self.btn_agir_bloquear = Botao(hud_x + 25 + 1 * (largura_btn + gap), y_btn, largura_btn, h_btn, "BLOQUEAR", (150, 120, 20), (200, 160, 30), largura_btn + 4, h_btn + 4, cor_texto=(255,255,255), fonte_tamanho=12)
        self.btn_bloquear      = self.btn_agir_bloquear
        self.btn_agir_voltar   = Botao(hud_x + 25 + 3 * (largura_btn + gap), y_btn, largura_btn, h_btn, "VOLTAR", (75, 75, 85), (110, 110, 120), largura_btn + 4, h_btn + 4, cor_texto=(255,255,255), fonte_tamanho=12)

        # Botões dinâmicos do submenu ITEM
        self.botoes_itens_dinamicos = []
        self.btn_voltar_itens  = Botao(hud_x + 25 + 3 * (largura_btn + gap), y_btn, largura_btn, h_btn, "VOLTAR", (75, 75, 85), (110, 110, 120), largura_btn + 4, h_btn + 4, cor_texto=(255,255,255), fonte_tamanho=12)

        # Botões dinâmicos do submenu MINIONS do Invocador
        self.botoes_minions_dinamicos = []
        self.btn_voltar_minions = Botao(hud_x + 25 + 3 * (largura_btn + gap), y_btn, largura_btn, h_btn, "VOLTAR", (75, 75, 85), (110, 110, 120), largura_btn + 4, h_btn + 4, cor_texto=(255,255,255), fonte_tamanho=12)

        # Alvo prioritário para os minions (Comando ATINGIR)
        self.alvo_prioritario_minions = None

        # Botões do submenu COMANDOS do Invocador
        self.btn_cmd_atingir   = Botao(hud_x + 25 + 0 * (largura_btn + gap), y_btn, largura_btn, h_btn, "ATINGIR", (140, 45, 45), (190, 65, 65), largura_btn + 4, h_btn + 4, cor_texto=(255,255,255), fonte_tamanho=11)
        self.btn_cmd_defender  = Botao(hud_x + 25 + 1 * (largura_btn + gap), y_btn, largura_btn, h_btn, "DEFENDER", (35, 95, 145), (50, 140, 205), largura_btn + 4, h_btn + 4, cor_texto=(255,255,255), fonte_tamanho=11)
        self.btn_cmd_descansar = Botao(hud_x + 25 + 2 * (largura_btn + gap), y_btn, largura_btn, h_btn, "DESCANSAR", (35, 130, 95), (50, 180, 135), largura_btn + 4, h_btn + 4, cor_texto=(255,255,255), fonte_tamanho=11)
        self.btn_cmd_voltar    = Botao(hud_x + 25 + 3 * (largura_btn + gap), y_btn, largura_btn, h_btn, "VOLTAR", (75, 75, 85), (110, 110, 120), largura_btn + 4, h_btn + 4, cor_texto=(255,255,255), fonte_tamanho=11)

        self.fundo_luta = self._carregar_fundo_luta()
        self.fundo_luta_redimensionado = None
        self.fundo_luta_tamanho = None
        self.tempo_animacao = 0.0

        try:
            img_c = pygame.image.load(caminho_imagem("Cortes.png"))
            self.surf_cortes = pygame.transform.scale(img_c, (780, 560))
        except Exception as e:
            print(f"[Aviso] Nao foi possivel carregar Cortes.png: {e}")
            self.surf_cortes = None

        self.pool_cortes_spam = []
        try:
            img_spam = pygame.image.load(caminho_imagem("Cortes Spam.png")).convert()
            w_sp, h_sp = img_spam.get_size()
            crops = [
                img_spam.subsurface((70, 70, max(20, w_sp // 2 - 70), max(20, h_sp // 2 - 70))),
                img_spam.subsurface((w_sp // 2, 70, max(20, w_sp // 2 - 70), max(20, h_sp // 2 - 70))),
                img_spam.subsurface((70, h_sp // 2, max(20, w_sp // 2 - 70), max(20, h_sp // 2 - 70))),
                img_spam.subsurface((w_sp // 2, h_sp // 2, max(20, w_sp // 2 - 70), max(20, h_sp // 2 - 70))),
            ]
            angulos = [-60, -35, -15, 0, 15, 35, 60, 90, 120, 150, 180, 210, 240, 300]
            tamanhos = [(120, 80), (160, 105), (200, 130)]
            for crop in crops:
                for sz in tamanhos:
                    s = pygame.transform.scale(crop, sz)
                    for ang in angulos:
                        r = pygame.transform.rotate(s, ang)
                        self.pool_cortes_spam.append(r)
        except Exception as e:
            print(f"[Aviso] Nao foi possivel pre-renderizar cortes spam: {e}")
            self.pool_cortes_spam = []

        self.particulas_cortes_santuario = []
        self.intervalo_spawn_cortes = 0
        self.timer_som_cortes_santuario = 0
        self.timer_shake_santuario = 0
        self.rodada_numero = 1

        self.shake_duracao = 0
        self.shake_intensidade = 0
        self.animacao_cortes_duracao = 0
        self.animacao_cortes_max = 0
        self.pos_cortes_x = (self.tela.get_width() - 780) // 2
        self.pos_cortes_y = (self.tela.get_height() - 560) // 2

        self.fonte = obter_fonte(14)
        self.fonte_titulos = obter_fonte(14)
        self.fonte_status = pygame.font.SysFont(["consolas", "courier", "arial"], 14, bold=True)
        self.fonte_inimigo = obter_fonte(12)
        self.mensagem_log = "A batalha começou!"
        self.ataque_jogador_ativo = None

        # Carregamento do som de SFX de corte
        self.snd_corte = None
        try:
            if pygame.mixer.get_init():
                caminho_som_corte = caminho_sfx("corte.wav")
                if os.path.exists(caminho_som_corte):
                    self.snd_corte = pygame.mixer.Sound(caminho_som_corte)
        except Exception as e:
            print(f"[Aviso] Nao foi possivel carregar SFX corte.wav: {e}")

        # Carregamento do som de SFX de foco
        self.snd_foco = None
        try:
            if pygame.mixer.get_init():
                caminho_som_foco = caminho_sfx("Foco.wav")
                if os.path.exists(caminho_som_foco):
                    self.snd_foco = pygame.mixer.Sound(caminho_som_foco)
        except Exception as e:
            print(f"[Aviso] Nao foi possivel carregar SFX Foco.wav: {e}")

        # Carregamento do sprite visual de corte
        self.img_vfx_corte = None
        try:
            caminho_img_corte = caminho_vfx("corte_vfx.png")
            if os.path.exists(caminho_img_corte):
                self.img_vfx_corte = pygame.image.load(caminho_img_corte).convert_alpha()
        except Exception as e:
            print(f"[Aviso] Nao foi possivel carregar corte_vfx.png: {e}")

        self.animacoes_vfx_cortes = []
        self.timer_som_cortes_santuario = 0

        # Ultimate da Estraga Prazeres: Spike e Minigame de Desarme (Bullet Hell)
        self.spike = None
        self.spike_detonando = False
        self.spike_raio_detonacao = 0.0
        self.spike_tempo_detonacao = 0.0
        self.particulas_detonacao_spike = []

        self.snd_spike_beep = None
        self.canal_spike = None
        try:
            if pygame.mixer.get_init():
                caminho_snd_spike = caminho_sfx("Spike Beep.mp3")
                if os.path.exists(caminho_snd_spike):
                    self.snd_spike_beep = pygame.mixer.Sound(caminho_snd_spike)
        except Exception as e:
            print(f"[Aviso] Nao foi possivel carregar Spike Beep.mp3: {e}")

        # Som de desarme ao clicar na bomba (Desarmar.mp3)
        self.snd_desarmar = None
        try:
            if pygame.mixer.get_init():
                caminho_snd_desarmar = caminho_sfx("Desarmar.mp3")
                if os.path.exists(caminho_snd_desarmar):
                    self.snd_desarmar = pygame.mixer.Sound(caminho_snd_desarmar)
        except Exception as e:
            print(f"[Aviso] Nao foi possivel carregar Desarmar.mp3: {e}")

        self.esfera_desarme_pos = [640.0, 360.0]
        self.esfera_desarme_raio = 50
        self.esfera_desarme_tempo = 0.0
        self.bloqueio_desarme_timer = 0
        self.projeteis_bullet_hell = []
        self.particulas_desarme = []
        self.timer_spawn_projeteis = 0
        self.invulnerabilidade_mouse = 0
        self.progresso_desarme_minigame = 0.0
        self.checkpoint_desarme_50 = False

        if not hasattr(personagem, 'nivel'): personagem.nivel = 1
        if not hasattr(personagem, 'xp'): personagem.xp = 0
        if not hasattr(personagem, 'pontos_atributo'): personagem.pontos_atributo = 0
        if not hasattr(personagem, 'atributos'): 
            personagem.atributos = {"For": 1, "Agi": 1, "Con": 1, "Sab": 1, "Int": 1, "Sor": 1}

    def tocar_vfx_corte(self, volume_relativo=1.0):
        if self.snd_corte is not None:
            try:
                from Sistemas.Configuracoes import sistema_config
                vol = sistema_config.obter_volume_sfx_efetivo() * volume_relativo
                self.snd_corte.set_volume(max(0.0, min(1.0, vol)))
                self.snd_corte.play()
            except Exception as e:
                print(f"[Aviso] Erro ao reproduzir SFX de corte: {e}")
        else:
            tocar_sfx("corte.wav", volume_relativo=volume_relativo)

    def tocar_sfx_corte(self, volume_relativo=1.0):
        self.tocar_vfx_corte(volume_relativo=volume_relativo)

    def tocar_sfx_soco(self, volume_relativo=1.0):
        tocar_sfx("Soco.wav", volume_relativo=volume_relativo)

    def tocar_sfx_mordida(self, volume_relativo=1.0):
        tocar_sfx("Mordida.wav", volume_relativo=volume_relativo)

    def tocar_sfx_acerto(self, volume_relativo=1.0):
        tocar_sfx("Acerto.wav", volume_relativo=volume_relativo)

    def tocar_sfx_dano(self, volume_relativo=1.0):
        tocar_sfx("Dano.wav", volume_relativo=volume_relativo)

    def tocar_som_desarmar(self, volume_relativo=1.0):
        if getattr(self, "snd_desarmar", None) is not None:
            try:
                from Sistemas.Configuracoes import sistema_config
                vol = sistema_config.obter_volume_sfx_efetivo() * volume_relativo
                self.snd_desarmar.set_volume(max(0.0, min(1.0, vol)))
                self.snd_desarmar.play()
            except Exception as e:
                print(f"[Aviso] Erro ao reproduzir som de desarme: {e}")

    def disparar_vfx_corte_alvo(self, alvo, duracao=14):
        if not alvo:
            return
        rect = getattr(alvo, "rect", None)
        if rect:
            self.animacoes_vfx_cortes.append({
                "x": rect.centerx,
                "y": rect.centery,
                "duracao": duracao,
                "duracao_max": duracao,
                "rotacao": random.choice([-30, -15, 0, 15, 30, 45]),
                "flip": random.choice([True, False]),
            })

    def disparar_screen_shake(self, duracao=25, intensidade=6):
        self.shake_duracao = max(self.shake_duracao, duracao)
        self.shake_intensidade = intensidade

    def disparar_animacao_cortes(self, duracao=32):
        self.animacao_cortes_duracao = duracao
        self.animacao_cortes_max = duracao
        self.disparar_screen_shake(duracao=duracao, intensidade=7)

    def invocar_santuario(self, dono=None):
        for ent in list(self.ordem_turnos):
            if getattr(ent, "is_santuario", False):
                ent._hp = 0

        lado = "aliado" if getattr(dono, "is_player", False) else "inimigo"
        px, py = (395, 405) if lado == "aliado" else (575, 405)
        santuario = Santuario(x=px, y=py, dono=dono, lado=lado)

        pos_insercao = min(len(self.ordem_turnos), self.indice_turno + 1)
        self.ordem_turnos.insert(pos_insercao, santuario)
        self.atualizar_posicoes_inimigos()
        return santuario

    def atualizar_cortes_santuario(self):
        santuarios_ativos = [e for e in self.ordem_turnos if getattr(e, "is_santuario", False) and getattr(e, "hp", 0) > 0]
        if santuarios_ativos:
            # Tremer tela suavemente e periodicamente para dar ambientação sem trepidação excessiva
            self.timer_shake_santuario = getattr(self, "timer_shake_santuario", 0) + 1
            if self.timer_shake_santuario % 12 < 3:
                self.shake_duracao = max(self.shake_duracao, 2)
                self.shake_intensidade = max(self.shake_intensidade, 1)

            # Efeito sonoro suave e espaçado para os cortes do domínio
            self.timer_som_cortes_santuario = getattr(self, "timer_som_cortes_santuario", 0) + 1
            if self.timer_som_cortes_santuario >= 32:
                self.timer_som_cortes_santuario = 0
                self.tocar_vfx_corte(volume_relativo=0.20)

            # Spawn suave e cadenciado de cortes saindo do santuário
            self.intervalo_spawn_cortes = getattr(self, "intervalo_spawn_cortes", 0) + 1
            if self.intervalo_spawn_cortes >= 4:
                self.intervalo_spawn_cortes = 0
                for sant in santuarios_ativos:
                    if self.pool_cortes_spam:
                        angulo = random.uniform(0, 2 * math.pi)
                        velocidade = random.uniform(7.0, 13.0)
                        self.particulas_cortes_santuario.append({
                            "x": float(sant.rect.centerx),
                            "y": float(sant.rect.centery),
                            "vx": math.cos(angulo) * velocidade,
                            "vy": math.sin(angulo) * velocidade,
                            "surf": random.choice(self.pool_cortes_spam),
                            "vida": 16,
                        })

        particulas_vivas = []
        for p in self.particulas_cortes_santuario:
            p["vida"] -= 1
            if p["vida"] > 0:
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                particulas_vivas.append(p)
        self.particulas_cortes_santuario = particulas_vivas

        anim_vivas = []
        for a in getattr(self, "animacoes_vfx_cortes", []):
            a["duracao"] -= 1
            if a["duracao"] > 0:
                anim_vivas.append(a)
        self.animacoes_vfx_cortes = anim_vivas

    def plantar_spike(self, dono=None):
        self.parar_som_spike()
        self.spike = Spike(x=640, y=410, dono=dono, tempo_total=50.0)
        self.spike_detonando = False
        self.spike_raio_detonacao = 0.0
        self.spike_tempo_detonacao = 0.0
        self.particulas_detonacao_spike.clear()
        self.projeteis_bullet_hell.clear()
        self.particulas_desarme.clear()
        self.progresso_desarme_minigame = 0.0
        self.checkpoint_desarme_50 = False

        if self.snd_spike_beep is not None:
            try:
                from Sistemas.Configuracoes import sistema_config
                vol = sistema_config.obter_volume_sfx_efetivo() * 0.90
                self.canal_spike = pygame.mixer.find_channel(True)
                if self.canal_spike:
                    self.canal_spike.set_volume(max(0.0, min(1.0, vol)))
                    self.canal_spike.play(self.snd_spike_beep)
            except Exception as e:
                print(f"[Aviso] Erro ao reproduzir som da Spike: {e}")

    def parar_som_spike(self):
        try:
            if getattr(self, "canal_spike", None) is not None:
                self.canal_spike.stop()
        except Exception:
            pass

    def atualizar_spike_e_detonacao(self):
        if not getattr(self, "spike", None):
            return

        # Se a Spike já foi desarmada, atualiza a exibição do novo frame e deleta quando expirar
        if self.spike.desarmada:
            self.spike.atualizar()
            if getattr(self.spike, "deletar", False):
                self.spike = None
            return

        if not self.spike.ativa:
            return

        t_rest = self.spike.tempo_restante()

        # Tremor ambiental sutil quando o tempo se esgota
        if t_rest <= 10.0 and not self.spike_detonando:
            if random.random() < 0.25:
                self.shake_duracao = max(self.shake_duracao, 3)
                self.shake_intensidade = max(self.shake_intensidade, 2 if t_rest > 4.0 else 4)

        # Inicia expansão da esfera negra por volta dos ~45s (5s restantes para 50s)
        if t_rest <= 5.0 and not self.spike_detonando:
            self.spike_detonando = True
            self.spike_tempo_detonacao = time.time()
            self.spike.detonando = True

        if self.spike_detonando:
            tempo_det = time.time() - self.spike_tempo_detonacao
            progresso = min(1.0, max(0.0, tempo_det / 4.5))
            self.spike_raio_detonacao = int(1500 * (progresso ** 2.3))

            intensidade_shake = min(22, int(4 + progresso * 18))
            self.shake_duracao = max(self.shake_duracao, 5)
            self.shake_intensidade = max(self.shake_intensidade, intensidade_shake)

            if len(self.particulas_detonacao_spike) < 40:
                cx = self.spike.rect.centerx if self.spike else 640
                cy = self.spike.rect.centery if self.spike else 410
                r = max(10, self.spike_raio_detonacao)
                ang = random.uniform(0, 2 * math.pi)
                vel = random.uniform(4.0, 10.0)
                self.particulas_detonacao_spike.append({
                    "x": cx + math.cos(ang) * (r * 0.95),
                    "y": cy + math.sin(ang) * (r * 0.95),
                    "vx": math.cos(ang) * vel,
                    "vy": math.sin(ang) * vel,
                    "raio": random.randint(2, 5),
                    "vida": random.randint(12, 24)
                })

            vivas_det = []
            for p in self.particulas_detonacao_spike:
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                p["vida"] -= 1
                if p["vida"] > 0:
                    vivas_det.append(p)
            self.particulas_detonacao_spike = vivas_det

            # Se esgotou o tempo (50s) ou a esfera cobriu a tela: GAME OVER!
            if t_rest <= 0.0 or progresso >= 1.0:
                self.spike.detonada = True
                self.spike.ativa = False
                for j in self.obter_jogadores():
                    j.hp = 0
                self.mensagem_log = "💀 A SPIKE DETONOU! A esfera negra consumiu tudo e eliminou a equipe!"
                self.iniciar_cooldown_feedback(80, lambda: "game_over")

    def iniciar_minigame_desarme_spike(self):
        self.tocar_som_desarmar(volume_relativo=1.0)
        self.menu_acoes_estado = "desarmando_spike"
        self.esfera_desarme_pos = [640.0, 360.0]  # Esfera centralizada e estacionária
        self.esfera_desarme_raio = 50
        self.esfera_desarme_tempo = 0.0
        self.bloqueio_desarme_timer = 0
        self.projeteis_bullet_hell.clear()
        self.particulas_desarme.clear()
        self.timer_spawn_projeteis = 0
        self.invulnerabilidade_mouse = 0
        self.progresso_desarme_minigame = self.spike.progresso_desarme if self.spike else 0.0
        self.checkpoint_desarme_50 = self.spike.checkpoint_50 if self.spike else False

    def _processar_minigame_spike(self, posicao_mouse, estado_clique_mouse, clicou):
        if not self.spike or not self.spike.ativa or self.spike.desarmada:
            self.menu_acoes_estado = "principal"
            return None

        # Botão cancelar ou tecla ESC
        self.btn_cancelar_desarme.atualizar(posicao_mouse, estado_clique_mouse)
        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_ESCAPE] or (clicou and self.btn_cancelar_desarme.clicado(posicao_mouse)):
            self.spike.progresso_desarme = self.progresso_desarme_minigame
            self.spike.checkpoint_50 = self.checkpoint_desarme_50
            self.menu_acoes_estado = "principal"
            self.mensagem_log = "Desarme interrompido. A Spike continua armada!"
            return None

        # A bola NÃO se mexe: fica fixa e perfeitamente centralizada
        cx, cy = 640.0, 360.0
        self.esfera_desarme_pos = [cx, cy]

        if getattr(self, "bloqueio_desarme_timer", 0) > 0:
            self.bloqueio_desarme_timer -= 1

        dist_mouse = math.hypot(posicao_mouse[0] - cx, posicao_mouse[1] - cy)
        dentro = dist_mouse <= self.esfera_desarme_raio

        if dentro:
            if getattr(self, "bloqueio_desarme_timer", 0) <= 0:
                incremento = 1.0 / (7.5 * 60.0)
                self.progresso_desarme_minigame = min(1.0, self.progresso_desarme_minigame + incremento)
                if self.progresso_desarme_minigame >= 0.5:
                    self.checkpoint_desarme_50 = True
                self.spike.progresso_desarme = self.progresso_desarme_minigame
                self.spike.checkpoint_50 = self.checkpoint_desarme_50

                if random.random() < 0.45:
                    self.particulas_desarme.append({
                        "x": posicao_mouse[0] + random.uniform(-4, 4),
                        "y": posicao_mouse[1] + random.uniform(-4, 4),
                        "vx": (cx - posicao_mouse[0]) * 0.12 + random.uniform(-1, 1),
                        "vy": (cy - posicao_mouse[1]) * 0.12 + random.uniform(-1, 1),
                        "vida": 12,
                        "cor": random.choice([(50, 255, 180), (100, 230, 255), (255, 255, 255)])
                    })
        else:
            # O Bullet Hell força o jogador para fora: regride o progresso rapidamente
            p_min = 0.50 if self.checkpoint_desarme_50 else 0.0
            self.progresso_desarme_minigame = max(p_min, self.progresso_desarme_minigame - 0.0016)
            self.spike.progresso_desarme = self.progresso_desarme_minigame

        # Conclusão do desarme: 100%
        if self.progresso_desarme_minigame >= 1.0:
            self.spike.desarmar()  # Aplica o novo frame da Spike desarmada e inicia o timer antes de deletar
            self.parar_som_spike()
            self.tocar_vfx_corte(volume_relativo=0.7)
            self.disparar_screen_shake(duracao=16, intensidade=6)
            for b in self.projeteis_bullet_hell:
                for _ in range(4):
                    self.particulas_desarme.append({
                        "x": b["x"], "y": b["y"],
                        "vx": random.uniform(-4, 4), "vy": random.uniform(-4, 4),
                        "vida": 20, "cor": (80, 255, 180)
                    })
            self.projeteis_bullet_hell.clear()
            self.mensagem_log = "✅ A SPIKE FOI DESARMADA COM SUCESSO! A detonação foi prevenida!"
            self.menu_acoes_estado = "principal"
            self.iniciar_cooldown_feedback(65, self.avancar_turno)
            return None

        # Spawn de projéteis do Bullet Hell: TODAS AS BALAS VÊM DE FORA DA TELA EM DIREÇÃO AO CENTRO
        self.timer_spawn_projeteis += 1
        if self.timer_spawn_projeteis >= 28 and len(self.projeteis_bullet_hell) < 20:
            self.timer_spawn_projeteis = 0
            padrao = random.choice(["convergencia_radial", "barragem_bordas", "fogo_cruzado", "vortice_espiral"])

            if padrao == "convergencia_radial":
                num_balas = random.randint(7, 8)
                ang_base = random.uniform(0, 2 * math.pi)
                brecha = random.randint(0, num_balas - 1)
                for bi in range(num_balas):
                    if bi == brecha or bi == (brecha + 1) % num_balas:
                        continue  # brecha ampla para manobra segura do jogador
                    ang = ang_base + (bi / num_balas) * 2 * math.pi
                    px = cx + math.cos(ang) * 750.0
                    py = cy + math.sin(ang) * 750.0
                    ang_mov = ang + math.pi  # Aponta exatamente para o centro
                    vel = random.uniform(2.0, 2.7)
                    self.projeteis_bullet_hell.append({
                        "x": px, "y": py,
                        "vx": math.cos(ang_mov) * vel,
                        "vy": math.sin(ang_mov) * vel,
                        "raio": 6, "cor": (255, 60, 90), "tipo": "radial"
                    })

            elif padrao == "barragem_bordas":
                borda = random.choice(["esquerda", "direita", "cima", "baixo"])
                for _ in range(random.randint(2, 3)):
                    if borda == "esquerda":
                        px = -35.0
                        py = random.uniform(120, 600)
                    elif borda == "direita":
                        px = 1315.0
                        py = random.uniform(120, 600)
                    elif borda == "cima":
                        px = random.uniform(180, 1100)
                        py = -35.0
                    else:
                        px = random.uniform(180, 1100)
                        py = 755.0

                    target_x = cx + random.uniform(-40, 40)
                    target_y = cy + random.uniform(-40, 40)
                    ang_m = math.atan2(target_y - py, target_x - px)
                    vel = random.uniform(2.6, 3.4)
                    self.projeteis_bullet_hell.append({
                        "x": px, "y": py,
                        "vx": math.cos(ang_m) * vel,
                        "vy": math.sin(ang_m) * vel,
                        "raio": 6, "cor": (255, 140, 30), "tipo": "plasma"
                    })

            elif padrao == "fogo_cruzado":
                canto = random.choice([(-35.0, -35.0), (1315.0, 755.0), (1315.0, -35.0), (-35.0, 755.0)])
                ang_base_m = math.atan2(cy - canto[1], cx - canto[0])
                for offset_ang in [-0.09, 0.09]:
                    vel = random.uniform(2.8, 3.6)
                    self.projeteis_bullet_hell.append({
                        "x": canto[0], "y": canto[1],
                        "vx": math.cos(ang_base_m + offset_ang) * vel,
                        "vy": math.sin(ang_base_m + offset_ang) * vel,
                        "raio": 5, "cor": (70, 220, 255), "tipo": "laser"
                    })

            elif padrao == "vortice_espiral":
                curva = random.choice([-0.008, 0.008])
                for ang_i in [0, 2 * math.pi / 3, 4 * math.pi / 3]:
                    ang = ang_i + random.uniform(-0.15, 0.15)
                    px = cx + math.cos(ang) * 750.0
                    py = cy + math.sin(ang) * 750.0
                    ang_mov = ang + math.pi + (0.28 if curva > 0 else -0.28)
                    vel = 2.2
                    self.projeteis_bullet_hell.append({
                        "x": px, "y": py,
                        "vx": math.cos(ang_mov) * vel,
                        "vy": math.sin(ang_mov) * vel,
                        "curva": curva,
                        "raio": 6, "cor": (255, 225, 70), "tipo": "espiral"
                    })

        # Atualiza posição dos projéteis
        projeteis_vivos = []
        if self.invulnerabilidade_mouse > 0:
            self.invulnerabilidade_mouse -= 1

        mx, my = posicao_mouse
        for b in self.projeteis_bullet_hell:
            if b.get("curva", 0) != 0:
                c = b["curva"]
                novo_vx = b["vx"] * math.cos(c) - b["vy"] * math.sin(c)
                novo_vy = b["vx"] * math.sin(c) + b["vy"] * math.cos(c)
                b["vx"], b["vy"] = novo_vx, novo_vy

            b["x"] += b["vx"]
            b["y"] += b["vy"]

            dist_cursor = math.hypot(mx - b["x"], my - b["y"])
            if self.invulnerabilidade_mouse <= 0 and dist_cursor < (8 + b["raio"]):
                # O Bullet Hell colide e ATRAPALHA O PROGRESSO
                self.invulnerabilidade_mouse = 36
                self.bloqueio_desarme_timer = 15  # Trava o avanço do progresso por 15 frames
                self.disparar_screen_shake(duracao=5, intensidade=4)

                for j in self.obter_jogadores():
                    if j.hp > 0 and not getattr(j, "god_mode", False):
                        j.hp = max(1, j.hp - 5)

                p_min = 0.50 if self.checkpoint_desarme_50 else 0.0
                self.progresso_desarme_minigame = max(p_min, self.progresso_desarme_minigame - 0.05)
                self.spike.progresso_desarme = self.progresso_desarme_minigame

                for _ in range(8):
                    self.particulas_desarme.append({
                        "x": mx, "y": my,
                        "vx": random.uniform(-3, 3), "vy": random.uniform(-3, 3),
                        "vida": 14, "cor": (255, 60, 60)
                    })
                continue

            if -70 <= b["x"] <= 1350 and -70 <= b["y"] <= 790:
                projeteis_vivos.append(b)
        self.projeteis_bullet_hell = projeteis_vivos

        part_vivas = []
        for p in self.particulas_desarme:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vida"] -= 1
            if p["vida"] > 0:
                part_vivas.append(p)
        self.particulas_desarme = part_vivas

        return None

    def _desenhar_minigame_spike(self, posicao_mouse):
        overlay = pygame.Surface((self.tela.get_width(), self.tela.get_height()), pygame.SRCALPHA)
        overlay.fill((8, 10, 16, 215))
        self.tela.blit(overlay, (0, 0))

        w_hud = 540
        h_hud = 62
        hx = (self.tela.get_width() - w_hud) // 2
        hy = 85
        pygame.draw.rect(self.tela, (18, 22, 32), (hx, hy, w_hud, h_hud), border_radius=10)
        pygame.draw.rect(self.tela, (70, 160, 220), (hx, hy, w_hud, h_hud), width=2, border_radius=10)

        t_rest = self.spike.tempo_restante() if self.spike else 0.0
        txt_titulo = self.fonte_status.render("MINIGAME DE DESARME DA SPIKE", True, (240, 245, 255))
        self.tela.blit(txt_titulo, (hx + 16, hy + 8))

        cor_timer = (255, 60, 60) if t_rest <= 15 else (255, 180, 50)
        txt_timer = self.fonte_status.render(f"DETONAÇÃO: {t_rest:.1f}s", True, cor_timer)
        self.tela.blit(txt_timer, (hx + w_hud - txt_timer.get_width() - 16, hy + 8))

        bx = hx + 16
        by = hy + 34
        bw = w_hud - 32
        bh = 16
        pygame.draw.rect(self.tela, (30, 34, 46), (bx, by, bw, bh), border_radius=5)

        prog = max(0.0, min(1.0, self.progresso_desarme_minigame))
        largura_preenchida = int(bw * prog)
        cor_barra = (50, 240, 170) if getattr(self, "checkpoint_desarme_50", False) else (45, 180, 255)
        if largura_preenchida > 0:
            pygame.draw.rect(self.tela, cor_barra, (bx, by, largura_preenchida, bh), border_radius=5)

        meio_x = bx + bw // 2
        pygame.draw.line(self.tela, (255, 255, 255), (meio_x, by - 3), (meio_x, by + bh + 3), 2)
        pygame.draw.rect(self.tela, (160, 185, 215), (bx, by, bw, bh), width=2, border_radius=5)

        txt_pct = self.fonte_inimigo.render(f"{int(prog * 100)}%", True, (255, 255, 255))
        self.tela.blit(txt_pct, (bx + (bw - txt_pct.get_width()) // 2, by + 1))

        # Desenha os projéteis do Bullet Hell convergindo de fora da tela
        for b in self.projeteis_bullet_hell:
            x, y, r = int(b["x"]), int(b["y"]), int(b["raio"])
            cor = b.get("cor", (255, 80, 80))
            halo_surf = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
            pygame.draw.circle(halo_surf, (*cor, 80), (r * 2, r * 2), r * 2)
            pygame.draw.circle(halo_surf, (255, 255, 255, 180), (r * 2, r * 2), max(2, r // 2))
            self.tela.blit(halo_surf, (x - r * 2, y - r * 2), special_flags=pygame.BLEND_ADD)
            pygame.draw.circle(self.tela, cor, (x, y), r)
            pygame.draw.circle(self.tela, (255, 255, 255), (x, y), max(1, r - 3))

        # Esfera Centralizada e Imóvel
        cx, cy = int(self.esfera_desarme_pos[0]), int(self.esfera_desarme_pos[1])
        raio = self.esfera_desarme_raio
        dist = math.hypot(posicao_mouse[0] - cx, posicao_mouse[1] - cy)
        dentro = dist <= raio

        bloqueado = getattr(self, "bloqueio_desarme_timer", 0) > 0
        if bloqueado:
            cor_esfera = (255, 50, 50)
            alfa_esfera = 90
        elif dentro:
            cor_esfera = (50, 255, 180)
            alfa_esfera = 65
        else:
            cor_esfera = (255, 80, 80)
            alfa_esfera = 40

        esfera_surf = pygame.Surface((raio * 2 + 20, raio * 2 + 20), pygame.SRCALPHA)
        pygame.draw.circle(esfera_surf, (*cor_esfera, alfa_esfera), (raio + 10, raio + 10), raio)
        pygame.draw.circle(esfera_surf, (*cor_esfera, 230), (raio + 10, raio + 10), raio, width=3)
        pulso_raio = raio + int(math.sin(self.tempo_animacao * 8.0) * 4)
        pygame.draw.circle(esfera_surf, (*cor_esfera, 130), (raio + 10, raio + 10), pulso_raio, width=1)
        self.tela.blit(esfera_surf, (cx - raio - 10, cy - raio - 10))

        if bloqueado:
            txt_status_esfera = "⚡ IMPACTO! DESARME TRAVADO!"
        elif dentro:
            txt_status_esfera = "● DESARMANDO..."
        else:
            txt_status_esfera = "⚠️ FORA DA ESFERA! (-PROGRESSO)"

        surf_lbl = self.fonte_inimigo.render(txt_status_esfera, True, cor_esfera)
        self.tela.blit(surf_lbl, (cx - surf_lbl.get_width() // 2, cy + raio + 12))

        for p in self.particulas_desarme:
            pygame.draw.circle(self.tela, p.get("cor", (255, 255, 255)), (int(p["x"]), int(p["y"])), 3)

        mx, my = posicao_mouse
        cor_m = (255, 255, 255) if self.invulnerabilidade_mouse % 4 < 2 else (255, 100, 100)
        pygame.draw.circle(self.tela, cor_m, (mx, my), 8, width=2)
        pygame.draw.circle(self.tela, (255, 50, 50) if not dentro else (50, 255, 180), (mx, my), 3)

        self.btn_cancelar_desarme.desenhar(self.tela)

    def _desenhar_detonacao_spike(self):
        centro = self.spike.rect.center if self.spike else (self.tela.get_width() // 2, 410)
        raio = int(self.spike_raio_detonacao)
        if raio <= 0:
            return

        # 1. Esfera negra maciça
        pygame.draw.circle(self.tela, (0, 0, 0), centro, raio)

        # 2. Borda externa e auras brancas resplandecentes
        pygame.draw.circle(self.tela, (255, 255, 255), centro, raio, width=max(4, min(12, raio // 18)))
        pygame.draw.circle(self.tela, (220, 240, 255), centro, max(1, raio - 5), width=max(2, min(6, raio // 35)))

        raio_onda1 = raio + int(math.sin(self.tempo_animacao * 15.0) * 8 + 14)
        if raio_onda1 > 0:
            pygame.draw.circle(self.tela, (255, 255, 255), centro, raio_onda1, width=3)

        raio_onda2 = max(1, raio - 28)
        if raio_onda2 > 0:
            pygame.draw.circle(self.tela, (200, 230, 255), centro, raio_onda2, width=2)

        # 3. Feixes e espinhos brancos radiando para fora
        num_raios = 32
        for i in range(num_raios):
            ang = (i / num_raios) * 2 * math.pi + (self.tempo_animacao * 4.0)
            tam_raio = random.randint(20, 65)
            x1 = centro[0] + math.cos(ang) * (raio - 4)
            y1 = centro[1] + math.sin(ang) * (raio - 4)
            x2 = centro[0] + math.cos(ang) * (raio + tam_raio)
            y2 = centro[1] + math.sin(ang) * (raio + tam_raio)
            pygame.draw.line(self.tela, (255, 255, 255), (x1, y1), (x2, y2), random.randint(2, 4))

        # 4. Partículas brancas dispersas
        for p in self.particulas_detonacao_spike:
            pygame.draw.circle(self.tela, (255, 255, 255), (int(p["x"]), int(p["y"])), int(p.get("raio", 3)))

    def processar_fim_rodada(self):
        self.rodada_numero = getattr(self, "rodada_numero", 1) + 1
        santuarios = [e for e in self.ordem_turnos if getattr(e, "is_santuario", False) and getattr(e, "hp", 0) > 0]
        for santuario in santuarios:
            duracao_restante = santuario.perder_duracao_rodada()
            if duracao_restante <= 0 or santuario.hp <= 0:
                santuario._hp = 0
                self.mensagem_log = "💨 O Pequeno Santuário esgotou sua duração e desmoronou!"

        # Processamento de dano contínuo (DoT) para Queimando e Envenenado
        for ent in self.ordem_turnos:
            if getattr(ent, "hp", 0) <= 0:
                continue
            if getattr(ent, "queimando", False):
                dano_fogo = max(1, int(getattr(ent, "max_hp", 100) * 0.05))
                ent.hp = max(0, ent.hp - dano_fogo)
                turnos = getattr(ent, "turnos_fogo", 1) - 1
                setattr(ent, "turnos_fogo", turnos)
                if turnos <= 0:
                    ent.queimando = False
            if getattr(ent, "envenenado", False):
                dano_veneno = max(1, int(getattr(ent, "max_hp", 100) * 0.04))
                ent.hp = max(0, ent.hp - dano_veneno)
                turnos = getattr(ent, "turnos_veneno", 1) - 1
                setattr(ent, "turnos_veneno", turnos)
                if turnos <= 0:
                    ent.envenenado = False

        for m in self.obter_minions_vivos():
            m.defendendo = False

    def eh_minion(self, entidade):
        return bool(getattr(entidade, "is_minion", False))

    def eh_inimigo(self, entidade):
        return not getattr(entidade, "is_player", False) and not getattr(entidade, "is_minion", False)

    def obter_efeito_controle(self, entidade):
        if getattr(entidade, "congelado", False):
            return "Congelar"
        if getattr(entidade, "atordoado", False):
            return "Atordoar"
        return None

    def aplicar_efeito_controle(self, entidade, efeito):
        if not efeito:
            return None
        ef_lower = str(efeito).strip().lower()
        if "congel" in ef_lower:
            entidade.congelado = True
            return "CONGELOU!"
        if "atordo" in ef_lower or "stun" in ef_lower:
            entidade.atordoado = True
            return "ATORDOADO!"
        if "queim" in ef_lower or "fogo" in ef_lower:
            entidade.queimando = True
            setattr(entidade, "turnos_fogo", 2)
            return "EM CHAMAS!"
        if "venen" in ef_lower or "poison" in ef_lower:
            entidade.envenenado = True
            setattr(entidade, "turnos_veneno", 3)
            return "ENVENENOU!"
        return None

    def limpar_efeitos_controle(self, entidade):
        entidade.congelado = False
        entidade.atordoado = False

    def obter_efeitos_ataque_inimigo(self, inimigo, habilidade):
        efeito = getattr(habilidade, "efeito", None)
        efeitos = [efeito] if efeito else []
        chance = getattr(habilidade, "chance_efeito", 0.0)

        if getattr(inimigo, "tipo", None) == "chefe":
            if "Atordoar" not in efeitos:
                efeitos.append("Atordoar")
            chance = chance or 0.25

        return efeitos, chance

    def aplicar_efeitos_controle(self, entidade, efeitos):
        mensagens = []
        for efeito in efeitos:
            mensagem = self.aplicar_efeito_controle(entidade, efeito)
            if mensagem and mensagem not in mensagens:
                mensagens.append(mensagem)
        return mensagens

    def obter_minions_vivos(self, dono=None):
        minions = [
            ent for ent in self.ordem_turnos
            if self.eh_minion(ent) and getattr(ent, "hp", 0) > 0
        ]
        if dono is not None:
            minions = [m for m in minions if getattr(m, "dono", None) is dono]
        return minions

    def limite_minions(self, jogador=None):
        alvo = jogador if jogador is not None else personagem
        return 3 if self.tem_talento(alvo, "I3") else 2

    def invocar_minion(self, nome_minion, dono=None):
        from Entidades.Minion import criar_minion
        dono_final = dono if dono is not None else personagem
        vivos_dono = self.obter_minions_vivos(dono_final)
        limite = self.limite_minions(dono_final)

        if len(vivos_dono) >= limite:
            return None

        novo_minion = criar_minion(nome_minion, dono=dono_final)
        if novo_minion not in self.minions_ativos:
            self.minions_ativos.append(novo_minion)
        if hasattr(dono_final, "minions") and novo_minion not in dono_final.minions:
            dono_final.minions.append(novo_minion)
        if hasattr(dono_final, "estatisticas_minions"):
            dono_final.estatisticas_minions["invocacoes"] = dono_final.estatisticas_minions.get("invocacoes", 0) + 1

        if novo_minion not in self.ordem_turnos:
            pos_insercao = min(len(self.ordem_turnos), self.indice_turno + 1)
            self.ordem_turnos.insert(pos_insercao, novo_minion)

        self.atualizar_posicoes_inimigos()
        return novo_minion

    def _carregar_fundo_luta(self):
        try:
            imagem = pygame.image.load(caminho_imagem("Fight.png"))
            if pygame.display.get_surface() is not None:
                imagem = imagem.convert_alpha()
            return imagem
        except (pygame.error, FileNotFoundError) as e:
            print(f"[Aviso] Nao foi possivel carregar 'Fight.png': {e}")
            return None

    def _atualizar_ataques_jogador(self, jogador, verso, classe_dano):
        if not verso or not classe_dano or verso == "Nenhuma":
            return

        ataques = [
            nome for nome, hab in banco_habilidades.items()
            if hab.verso == verso and hab.tipo == classe_dano and not getattr(hab, 'is_ultimate', False)
        ]

        ultimate = obter_ultimate(verso, classe_dano)
        nodo_req = {"Sobrevivente": "S4", "Agente": "A4", "Feiticeiro": "F4"}.get(verso)
        ultimates_desbloqueadas = set(getattr(jogador, 'ultimates_desbloqueadas', set()))
        talentos_jogador = set(getattr(jogador, 'talentos', set()))

        is_desbloqueada = (
            (nodo_req and nodo_req in talentos_jogador)
            or (classe_dano == "Invocador" and "I4" in talentos_jogador)
            or (verso in ultimates_desbloqueadas)
            or ((verso, classe_dano) in ultimates_desbloqueadas)
            or (ultimate and ultimate.nome in ultimates_desbloqueadas)
        )

        if ultimate and is_desbloqueada:
            if ultimate.nome not in ataques:
                ataques.append(ultimate.nome)

        jogador.ataques = ataques

    def _aplicar_classe_personagem2(self):
        if getattr(self, 'personagem2', None) is None:
            return
        verso = getattr(self, 'classe_jogador2', None)
        classe_dano = getattr(self, 'classe_jogador2_tipo', None)
        if not verso or not classe_dano:
            return

        from Sistemas.SaveSystem import save_global
        talentos_verso = list(save_global.obter_progresso_verso(verso))
        talentos_inv = list(save_global.obter_progresso_verso("Invocador"))
        desab_verso = save_global.obter_habilidades_desabilitadas(verso)
        desab_inv = save_global.obter_habilidades_desabilitadas("Invocador")
        desabilitadas = set(desab_verso) | set(desab_inv)
        talentos_ativos = [t for t in (talentos_verso + talentos_inv) if t not in desabilitadas]
        self.personagem2.talentos = set(talentos_ativos)

        if not hasattr(self.personagem2, "ultimates_desbloqueadas"):
            self.personagem2.ultimates_desbloqueadas = set()

        mapa_nodos = {"Sobrevivente": "S4", "Agente": "A4", "Feiticeiro": "F4"}
        classes_todas = ["Físico", "Distância", "Magia", "Invocador"]
        nodo_ult = mapa_nodos.get(verso)
        if nodo_ult and nodo_ult in talentos_verso and nodo_ult not in desabilitadas:
            self.personagem2.ultimates_desbloqueadas.add(verso)
            for cl in classes_todas:
                self.personagem2.ultimates_desbloqueadas.add((verso, cl))

        if "I4" in talentos_inv and "I4" not in desabilitadas:
            self.personagem2.ultimates_desbloqueadas.add("Invocador")
            for v in ("Sobrevivente", "Agente", "Feiticeiro", "Invocador"):
                self.personagem2.ultimates_desbloqueadas.add((v, "Invocador"))

        chave_aplicada = f"{verso}-{classe_dano}"
        if getattr(self.personagem2, 'classe_aplicada', None) == chave_aplicada:
            return

        self._atualizar_ataques_jogador(self.personagem2, verso, classe_dano)

        if attr_classe := MAPA_ATRIBUTO_CLASSE.get(classe_dano):
            self.personagem2.atributos[attr_classe] = int(self.personagem2.atributos.get(attr_classe, 1)) + 3

        self.personagem2.is_player = True
        self.personagem2.classe_aplicada = chave_aplicada

    def atualizar_posicoes_inimigos(self):
        inimigos_vivos = [entidade for entidade in self.ordem_turnos if self.eh_inimigo(entidade) and (entidade.hp > 0 or getattr(entidade, 'timer_fade_derrota', 0) > 0)]
        santuarios = [e for e in inimigos_vivos if getattr(e, "is_santuario", False)]
        outros_inimigos = [e for e in inimigos_vivos if not getattr(e, "is_santuario", False)]

        for sant in santuarios:
            if getattr(sant, "lado", "inimigo") == "inimigo":
                sant.rect.center = (575, 405)
            else:
                sant.rect.center = (395, 405)

        quantidade_inimigos = len(outros_inimigos)

        posicoes_inimigos = {
            1: [(740, 400)],
            2: [(670, 335), (780, 465)],
            3: [(770, 315), (635, 400), (770, 485)],
            4: [(630, 325), (790, 325), (630, 475), (790, 475)],
        }

        layout_inimigos = posicoes_inimigos.get(quantidade_inimigos, [(740, 400)] * quantidade_inimigos)
        for inimigo, (px, py) in zip(outros_inimigos, layout_inimigos):
            if inimigo.hp > 0:
                inimigo.rect.center = (px, py)
                if hasattr(inimigo, 'atualizar_orientacao_por_quadrante'):
                    inimigo.atualizar_orientacao_por_quadrante()

        centro_x_jogadores = 260
        jogadores_vivos = [entidade for entidade in self.ordem_turnos if getattr(entidade, 'is_player', False) and entidade.hp > 0]
        if len(jogadores_vivos) == 1:
            jogadores_vivos[0].rect.center = (centro_x_jogadores, 400)
        elif len(jogadores_vivos) == 2:
            jogadores_vivos[0].rect.center = (centro_x_jogadores, 335)
            jogadores_vivos[1].rect.center = (centro_x_jogadores, 465)

        minions_vivos = self.obter_minions_vivos()
        qtd_minions = len(minions_vivos)
        posicoes_minions = {
            1: [(395, 405)],
            2: [(395, 340), (395, 465)],
            3: [(395, 290), (395, 400), (395, 510)],
        }
        layout_minions = posicoes_minions.get(qtd_minions, [(395, 320 + idx * 90) for idx in range(qtd_minions)])
        for minion, (mx, my) in zip(minions_vivos, layout_minions):
            minion.rect.center = (mx, my)

    def _eh_habilidade_minion(self, nome_hab):
        hab = banco_habilidades.get(nome_hab)
        if not hab:
            return False
        return bool(getattr(hab, "minion", None) or getattr(hab, "tipo", None) == "Invocador")

    def obter_summons_invocador_combate(self, jogador=None):
        alvo = jogador if jogador is not None else (self.jogadores[self.indice_jogador_ativo] if hasattr(self, "jogadores") and self.jogadores else personagem)
        ataques = getattr(alvo, "ataques", [])
        return [nome for nome in ataques if self._eh_habilidade_minion(nome)]

    def gerar_botoes_minions(self, jogador=None):
        self.botoes_minions_dinamicos = []
        alvo = jogador if jogador is not None else (self.jogadores[self.indice_jogador_ativo] if hasattr(self, "jogadores") and self.jogadores else personagem)
        summons = self.obter_summons_invocador_combate(alvo)
        qtd = len(summons)

        hud_rect = self.obter_rect_hud_acoes(estado="minions")
        hud_x = hud_rect.x
        hud_y = hud_rect.y

        largura_btn = 125
        gap_x = 16
        inicio_x = hud_x + 25
        y_inicial = hud_y + 44
        h_btn = 46
        gap_y = 10

        if qtd <= 3:
            linhas = 1
        else:
            linhas = math.ceil((qtd + 1) / 4)

        for idx, nome_hab in enumerate(summons):
            if idx < (linhas - 1) * 4:
                row = idx // 4
                col = idx % 4
            else:
                row = linhas - 1
                col = idx - (linhas - 1) * 4

            bx = inicio_x + col * (largura_btn + gap_x)
            by = y_inicial + row * (h_btn + gap_y)

            label = nome_hab
            if label.upper().startswith("INVOCAR "):
                label = "INV. " + label[8:]
            elif label.upper().startswith("IMPLANTAR "):
                label = "IMP. " + label[10:]
            texto_btn = label.upper()[:12]

            hab = banco_habilidades.get(nome_hab)
            eh_ultimate = getattr(hab, "is_ultimate", False) if hab else False

            if eh_ultimate:
                cor_btn = (140, 90, 20)
                cor_hover = (190, 130, 30)
            else:
                cor_btn = (25, 110, 125)
                cor_hover = (40, 160, 180)

            btn = Botao(
                bx, by, largura_btn, h_btn, texto_btn,
                cor_btn, cor_hover,
                largura_btn + 4, h_btn + 4,
                cor_texto=(255, 255, 255), fonte_tamanho=11
            )
            self.botoes_minions_dinamicos.append({
                "botao": btn,
                "nome": nome_hab,
                "habilidade": hab
            })

        # Botão VOLTAR sempre no último slot da grade
        row_v = linhas - 1
        col_v = 3
        bx_v = inicio_x + col_v * (largura_btn + gap_x)
        by_v = y_inicial + row_v * (h_btn + gap_y)
        self.btn_voltar_minions = Botao(
            bx_v, by_v, largura_btn, h_btn, "VOLTAR",
            (75, 75, 85), (110, 110, 120),
            largura_btn + 4, h_btn + 4,
            cor_texto=(255, 255, 255), fonte_tamanho=11
        )

    def gerar_botoes_ataque(self, jogador=None):
        self.botoes_habilidades_dinamicos = []
        alvo = jogador if jogador is not None else personagem
        ataques = list(getattr(alvo, "ataques", []))

        eh_invocador = (self.tipo_classe_do_jogador(alvo) == "Invocador") or any(self._eh_habilidade_minion(n) for n in ataques)

        hud_x = (self.tela.get_width() - 640) // 2
        hud_largura = 640
        y_botoes = 640
        altura_botao = 46

        if eh_invocador:
            outros_ataques = [n for n in ataques if not self._eh_habilidade_minion(n)]
            total_botoes = len(outros_ataques) + 2  # outros ataques + botão MINIONS + botão COMANDOS

            if total_botoes <= 3:
                largura_btn = 125
                espaco = 16
                inicio_x = hud_x + 25
                cur_idx = 0
                for nome_hab in outros_ataques:
                    bx = inicio_x + cur_idx * (largura_btn + espaco)
                    btn = Botao(bx, y_botoes, largura_btn, altura_botao, nome_hab.upper()[:12], (0, 100, 150), (0, 150, 200), largura_btn + 4, altura_botao + 4, cor_texto=(255, 255, 255), fonte_tamanho=11)
                    self.botoes_habilidades_dinamicos.append({"botao": btn, "nome": nome_hab, "tipo": "ataque"})
                    cur_idx += 1

                bx_minions = inicio_x + cur_idx * (largura_btn + espaco)
                btn_minions = Botao(
                    bx_minions, y_botoes, largura_btn, altura_botao, "MINIONS",
                    (52, 168, 148), (68, 205, 182),
                    largura_btn + 4, altura_botao + 4,
                    cor_texto=(255, 255, 255), fonte_tamanho=11
                )
                self.botoes_habilidades_dinamicos.append({"botao": btn_minions, "nome": "MINIONS", "tipo": "minions"})
                cur_idx += 1

                bx_comandos = inicio_x + cur_idx * (largura_btn + espaco)
                btn_comandos = Botao(
                    bx_comandos, y_botoes, largura_btn, altura_botao, "COMANDOS",
                    (35, 115, 145), (50, 160, 195),
                    largura_btn + 4, altura_botao + 4,
                    cor_texto=(255, 255, 255), fonte_tamanho=11
                )
                self.botoes_habilidades_dinamicos.append({"botao": btn_comandos, "nome": "COMANDOS", "tipo": "comandos"})

                self.btn_voltar = Botao(hud_x + hud_largura - largura_btn - 25, y_botoes, largura_btn, altura_botao, "VOLTAR", (75, 75, 85), (110, 110, 120), largura_btn + 4, altura_botao + 4, cor_texto=(255, 255, 255), fonte_tamanho=11)
            else:
                largura_btn = 105
                espaco = 10
                inicio_x = hud_x + 15
                cur_idx = 0
                for nome_hab in outros_ataques:
                    bx = inicio_x + cur_idx * (largura_btn + espaco)
                    btn = Botao(bx, y_botoes, largura_btn, altura_botao, nome_hab.upper()[:10], (0, 100, 150), (0, 150, 200), largura_btn + 4, altura_botao + 4, cor_texto=(255, 255, 255), fonte_tamanho=10)
                    self.botoes_habilidades_dinamicos.append({"botao": btn, "nome": nome_hab, "tipo": "ataque"})
                    cur_idx += 1

                bx_minions = inicio_x + cur_idx * (largura_btn + espaco)
                btn_minions = Botao(
                    bx_minions, y_botoes, largura_btn, altura_botao, "MINIONS",
                    (52, 168, 148), (68, 205, 182),
                    largura_btn + 4, altura_botao + 4,
                    cor_texto=(255, 255, 255), fonte_tamanho=10
                )
                self.botoes_habilidades_dinamicos.append({"botao": btn_minions, "nome": "MINIONS", "tipo": "minions"})
                cur_idx += 1

                bx_comandos = inicio_x + cur_idx * (largura_btn + espaco)
                btn_comandos = Botao(
                    bx_comandos, y_botoes, largura_btn, altura_botao, "COMANDOS",
                    (35, 115, 145), (50, 160, 195),
                    largura_btn + 4, altura_botao + 4,
                    cor_texto=(255, 255, 255), fonte_tamanho=10
                )
                self.botoes_habilidades_dinamicos.append({"botao": btn_comandos, "nome": "COMANDOS", "tipo": "comandos"})

                self.btn_voltar = Botao(hud_x + hud_largura - largura_btn - 15, y_botoes, largura_btn, altura_botao, "VOLTAR", (75, 75, 85), (110, 110, 120), largura_btn + 4, altura_botao + 4, cor_texto=(255, 255, 255), fonte_tamanho=10)
        else:
            total_botoes = len(ataques)
            if total_botoes <= 3:
                largura_btn = 125
                espaco = 16
                inicio_x = hud_x + 25
                for idx, nome_hab in enumerate(ataques):
                    bx = inicio_x + idx * (largura_btn + espaco)
                    btn = Botao(bx, y_botoes, largura_btn, altura_botao, nome_hab.upper()[:12], (0, 100, 150), (0, 150, 200), largura_btn + 4, altura_botao + 4, cor_texto=(255, 255, 255), fonte_tamanho=11)
                    self.botoes_habilidades_dinamicos.append({"botao": btn, "nome": nome_hab, "tipo": "ataque"})
                self.btn_voltar = Botao(hud_x + hud_largura - largura_btn - 25, y_botoes, largura_btn, altura_botao, "VOLTAR", (75, 75, 85), (110, 110, 120), largura_btn + 4, altura_botao + 4, cor_texto=(255, 255, 255), fonte_tamanho=11)
            else:
                largura_btn = 105
                espaco = 10
                inicio_x = hud_x + 15
                for idx, nome_hab in enumerate(ataques):
                    bx = inicio_x + idx * (largura_btn + espaco)
                    btn = Botao(bx, y_botoes, largura_btn, altura_botao, nome_hab.upper()[:10], (0, 100, 150), (0, 150, 200), largura_btn + 4, altura_botao + 4, cor_texto=(255, 255, 255), fonte_tamanho=10)
                    self.botoes_habilidades_dinamicos.append({"botao": btn, "nome": nome_hab, "tipo": "ataque"})
                self.btn_voltar = Botao(hud_x + hud_largura - largura_btn - 15, y_botoes, largura_btn, altura_botao, "VOLTAR", (75, 75, 85), (110, 110, 120), largura_btn + 4, altura_botao + 4, cor_texto=(255, 255, 255), fonte_tamanho=10)

    def obter_itens_consumiveis_combate(self):
        try:
            from Sistemas.Inventario import inventario_global
            return [c for c in getattr(inventario_global, "consumiveis", []) if getattr(c, "quantidade", 0) > 0]
        except Exception:
            return []

    def obter_rect_hud_acoes(self, estado=None):
        w_tela = self.tela.get_width()
        largura = 640
        x = (w_tela - largura) // 2
        base_bottom_y = 702
        altura_padrao = 106

        estado_alvo = estado if estado is not None else self.menu_acoes_estado
        if estado_alvo == "itens":
            itens = self.obter_itens_consumiveis_combate()
            qtd_itens = len(itens)
            if qtd_itens <= 3:
                linhas = 1
            else:
                linhas = math.ceil((qtd_itens + 1) / 4)
            altura = altura_padrao + (linhas - 1) * 56
            y = base_bottom_y - altura
            return pygame.Rect(x, y, largura, altura)
        elif estado_alvo == "minions":
            summons = self.obter_summons_invocador_combate()
            qtd_summons = len(summons)
            if qtd_summons <= 3:
                linhas = 1
            else:
                linhas = math.ceil((qtd_summons + 1) / 4)
            altura = altura_padrao + (linhas - 1) * 56
            y = base_bottom_y - altura
            return pygame.Rect(x, y, largura, altura)

        return pygame.Rect(x, 596, largura, altura_padrao)

    def gerar_botoes_itens(self, jogador=None):
        self.botoes_itens_dinamicos = []
        itens = self.obter_itens_consumiveis_combate()
        qtd_itens = len(itens)

        hud_rect = self.obter_rect_hud_acoes(estado="itens")
        hud_x = hud_rect.x
        hud_y = hud_rect.y

        largura_btn = 125
        gap_x = 16
        inicio_x = hud_x + 25
        y_inicial = hud_y + 44
        h_btn = 46
        gap_y = 10

        if qtd_itens <= 3:
            linhas = 1
        else:
            linhas = math.ceil((qtd_itens + 1) / 4)

        for idx, item in enumerate(itens):
            if idx < (linhas - 1) * 4:
                row = idx // 4
                col = idx % 4
            else:
                row = linhas - 1
                col = idx - (linhas - 1) * 4

            bx = inicio_x + col * (largura_btn + gap_x)
            by = y_inicial + row * (h_btn + gap_y)

            nome_display = item.nome
            if len(nome_display) > 11:
                nome_display = nome_display[:10] + "."
            texto_btn = f"{nome_display} ({item.quantidade})"
            btn = Botao(
                bx, by, largura_btn, h_btn, texto_btn,
                (25, 95, 140), (40, 145, 210),
                largura_btn + 4, h_btn + 4,
                cor_texto=(255, 255, 255), fonte_tamanho=10
            )
            self.botoes_itens_dinamicos.append({"botao": btn, "item": item})

        # Botão VOLTAR sempre no último slot (canto inferior direito) da grade
        row_v = linhas - 1
        col_v = 3
        bx_v = inicio_x + col_v * (largura_btn + gap_x)
        by_v = y_inicial + row_v * (h_btn + gap_y)
        self.btn_voltar_itens = Botao(
            bx_v, by_v, largura_btn, h_btn, "VOLTAR",
            (75, 75, 85), (110, 110, 120),
            largura_btn + 4, h_btn + 4,
            cor_texto=(255, 255, 255), fonte_tamanho=11
        )

    def usar_item_combate(self, item, jogador_atual=None):
        if jogador_atual is None:
            jogador_atual = self.jogadores[self.indice_jogador_ativo] if hasattr(self, "jogadores") and self.jogadores else personagem

        if getattr(item, "quantidade", 0) <= 0:
            self.mensagem_log = f"Item {getattr(item, 'nome', 'desconhecido')} esgotado!"
            return False

        hp_antes = jogador_atual.hp
        mp_antes = jogador_atual.mp

        item.usar(jogador_atual)

        hp_rec = max(0, jogador_atual.hp - hp_antes)
        mp_rec = max(0, jogador_atual.mp - mp_antes)

        detalhes = []
        if hp_rec > 0:
            detalhes.append(f"+{hp_rec} HP")
        if mp_rec > 0:
            detalhes.append(f"+{mp_rec} PM")
        txt_rec = f" ({', '.join(detalhes)})" if detalhes else ""

        self.mensagem_log = f"🧪 {jogador_atual.nome} usou {item.nome}{txt_rec}!"
        self.menu_acoes_estado = "principal"
        self.iniciar_cooldown_feedback(45, self.avancar_turno)
        return True

    def _custo_habilidade(self, hab, jogador_ativo=None):
        jogador_ativo = jogador_ativo or personagem
        return hab.custo_para(jogador_ativo) if hasattr(hab, "custo_para") else hab.custo_mp

    def configurar_classe(self, novo_verso, nova_classe_dano):
        if getattr(self, "classe_dano_atual", None) and getattr(self, "classe_dano_atual") != nova_classe_dano:
            if attr_antigo := MAPA_ATRIBUTO_CLASSE.get(self.classe_dano_atual):
                personagem.atributos[attr_antigo] = max(1, personagem.atributos.get(attr_antigo, 1) - 3)

        self.classe_atual = novo_verso
        self.classe_dano_atual = nova_classe_dano
        self.musica_luta = self.obter_musica_combate(eh_chefe=(getattr(self, 'partida_atual', 1) >= getattr(self, 'total_partidas', 3)), verso=novo_verso)
        try:
            from Sistemas import gerenciador_musica
            gerenciador_musica.definir_verso(novo_verso)
        except Exception:
            pass

        self._atualizar_ataques_jogador(personagem, novo_verso, nova_classe_dano)

        if attr_novo := MAPA_ATRIBUTO_CLASSE.get(nova_classe_dano):
            personagem.atributos[attr_novo] = personagem.atributos.get(attr_novo, 1) + 3

        from Sistemas.Inventario import inventario_global, Equipamento
        eq_nome, eq_attr = _obter_equipamento_inicial(novo_verso, nova_classe_dano)
        inventario_global.equipar(Equipamento(eq_nome, eq_attr, categoria="arma"))

        self.gerar_botoes_ataque(personagem)

    def calcular_pontos_desempenho(self, xp_ganho=0, dano_causado=0, inimigos_eliminados=0, dificuldade_total=0):
        hp_restante = max(0, int(personagem.hp))
        hp_total = max(1, int(personagem.max_hp))
        hp_bonus = int((hp_restante / hp_total) * 150)

        dano_causado = max(0, int(dano_causado))
        inimigos_eliminados = max(0, int(inimigos_eliminados))
        dificuldade_total = max(0, int(dificuldade_total))

        kill_bonus = inimigos_eliminados * 150
        dano_bonus = int(dano_causado * 0.35)
        dificuldade_bonus = int(dificuldade_total * 0.5)
        xp_bonus = int(xp_ganho * 0.5)
        partida_bonus = self.partida_atual * 50

        return hp_bonus + kill_bonus + dano_bonus + dificuldade_bonus + xp_bonus + partida_bonus

    def obter_musica_combate(self, eh_chefe: bool = False, verso: str = None):
        v = verso or self.classe_atual
        return obter_musica_combate(v, eh_chefe=eh_chefe)

    MULTIPLICADOR_COOLDOWN_ACOES = 1.5  # Aumenta o cooldown entre ações em 50%

    def iniciar_cooldown_feedback(self, frames: int = 75, acao=None):
        if frames > 1:
            frames_ajustados = int(round(frames * self.MULTIPLICADOR_COOLDOWN_ACOES))
        else:
            frames_ajustados = max(0, int(frames))
        self.cooldown_feedback = frames_ajustados
        self.tempo_cooldown_maximo = max(1, frames_ajustados)
        self.acao_pos_feedback = acao

    def configurar_cenario(self, id_cenario, rolagem_forcada=None):
        dados_efeito = None
        self.dados_ultimo_evento = None
        self.evento_neutro = None
        self.multiplicador_recompensa = 1.0
        self.efeito_hovered_ativo = None
        self.gerador_fases.fase_num = self.fase_numero
        self.minions_ativos.clear()
        if hasattr(personagem, "minions"):
            personagem.minions.clear()

        if getattr(self, 'duas_pessoas', False):
            if self.personagem2 is None:
                self.personagem2 = Personagem(150, 350, "pixil.png", nome="Jogador 2")
                self.personagem2.nome = "Jogador 2"
                setattr(self.personagem2, 'is_player', True)
            if hasattr(self.personagem2, "minions"):
                self.personagem2.minions.clear()
            self._aplicar_classe_personagem2()

        if id_cenario in ("ignorar_evento", "cancelar_evento", "dormir"):
            self.fase_numero += 1
            self.gerador_fases.fase_num = self.fase_numero
            if self.partida_atual >= self.total_partidas:
                chefe = self.gerador_fases.gerar_chefe_verso(self.classe_atual)
                inimigos_fase = [chefe]
                self.musica_luta = self.obter_musica_combate(eh_chefe=True)
                self.mensagem_log = "👑 CHEFE FINAL APARECEU!"
            else:
                inimigos_fase = self.gerador_fases.gerar_inimigos_aleatorios(self.fase_numero, quantidade=2, verso=self.classe_atual)
                self.musica_luta = self.obter_musica_combate(eh_chefe=False)
                if id_cenario == "dormir":
                    self.mensagem_log = "💤 Você descansou no dormitório e seguiu para a próxima batalha!"
                else:
                    self.mensagem_log = "⚑ Você ignorou o evento e seguiu para a próxima batalha!"
        elif id_cenario.startswith("evento_acao:") or id_cenario.startswith("evento_neutro_"):
            if id_cenario.startswith("evento_neutro_"):
                prefixo_id = id_cenario.split(":", 1)[0]
                sufixo_num = prefixo_id.split("_")[-1]
                if sufixo_num.isdigit():
                    self.fase_numero = int(sufixo_num)
                else:
                    self.fase_numero += 1
            else:
                self.fase_numero += 1
            self.gerador_fases.fase_num = self.fase_numero
            dados_efeito = executar_efeito_evento(id_cenario, jogo_tela=self, rolagem_forcada=rolagem_forcada)
            self.evento_neutro = dados_efeito["evento"]
            self.multiplicador_recompensa = dados_efeito.get("multiplicador_recompensa", 1.0)
            if self.partida_atual >= self.total_partidas:
                chefe = self.gerador_fases.gerar_chefe_verso(self.classe_atual)
                inimigos_fase = [chefe]
                self.musica_luta = self.obter_musica_combate(eh_chefe=True)
                self.mensagem_log = f"👑 CHEFE FINAL! {dados_efeito['mensagem']}"
            else:
                inimigos_fase = self.gerador_fases.gerar_inimigos_aleatorios(
                    self.fase_numero,
                    quantidade=dados_efeito["quantidade_inimigos"],
                    verso=self.classe_atual,
                    multiplicador_extra=dados_efeito["multiplicador_forca"],
                )
                self.musica_luta = self.obter_musica_combate(eh_chefe=(len(inimigos_fase) == 1 and self.multiplicador_recompensa > 1.0))
                self.mensagem_log = dados_efeito["mensagem"]
        elif self.partida_atual >= self.total_partidas:
            chefe = self.gerador_fases.gerar_chefe_verso(self.classe_atual)
            inimigos_fase = [chefe]
            self.musica_luta = self.obter_musica_combate(eh_chefe=True)
            self.mensagem_log = "👑 CHEFE FINAL APARECEU!"
        else:
            inimigos_fase = []
            self.mensagem_log = "⚠️ Cenário não identificado."
            self.musica_luta = self.obter_musica_combate(eh_chefe=False)

        self.ordem_turnos = [personagem]
        if getattr(self, 'duas_pessoas', False) and self.personagem2 is not None:
            self.ordem_turnos.append(self.personagem2)

        self.ordem_turnos.extend(inimigos_fase)

        for ent in self.ordem_turnos:
            if not getattr(ent, 'is_player', False):
                ent.hp = ent.max_hp
                ent.mp = getattr(ent, 'max_mp', 0)
            ent.congelado = False
            if not hasattr(ent, 'atributos'):
                ent.atributos = {"For": 1, "Agi": 1, "Int": 1, "Sor": 1}

        self.indice_turno = 0
        self.atualizar_posicoes_inimigos()
        self.dados_ultimo_evento = dados_efeito
        return dados_efeito

    def reiniciar(self):
        inimigos_atuais = [entidade for entidade in self.ordem_turnos if self.eh_inimigo(entidade)]
        if not inimigos_atuais:
            inimigos_atuais = self.gerador_fases.gerar_inimigos_aleatorios(self.fase_numero, quantidade=2, verso=self.classe_atual)

        self.minions_ativos.clear()
        if hasattr(personagem, "minions"):
            personagem.minions.clear()

        if not getattr(self, 'duas_pessoas', False):
            self.personagem2 = None
            self.classe_jogador2 = None
            self.classe_jogador2_tipo = None
        elif self.personagem2 is None:
            self.personagem2 = Personagem(150, 350, "pixil.png", nome="Jogador 2")
            self.personagem2.nome = "Jogador 2"
            setattr(self.personagem2, 'is_player', True)
        if self.personagem2 is not None and hasattr(self.personagem2, "minions"):
            self.personagem2.minions.clear()

        if getattr(self, 'classe_atual', 'Nenhuma') != 'Nenhuma' and getattr(self, 'classe_dano_atual', None):
            self._atualizar_ataques_jogador(personagem, self.classe_atual, self.classe_dano_atual)
            from Sistemas.Inventario import inventario_global, Equipamento
            if inventario_global.equipamento_slot is None:
                eq_nome, eq_attr = _obter_equipamento_inicial(self.classe_atual, self.classe_dano_atual)
                inventario_global.equipar(Equipamento(eq_nome, eq_attr, categoria="arma"))
        self._aplicar_classe_personagem2()

        self.ordem_turnos = [personagem]
        if getattr(self, 'duas_pessoas', False) and self.personagem2 is not None:
            self.ordem_turnos.append(self.personagem2)
        self.ordem_turnos.extend(inimigos_atuais)

        for entidade in self.ordem_turnos:
            entidade.congelado = False
            if getattr(entidade, 'is_player', False):
                if getattr(entidade, 'hp', 0) <= 0:
                    entidade.hp = max(1, int(getattr(entidade, 'max_hp', 100) * 0.30))
            else:
                entidade.hp = entidade.max_hp
                entidade.mp = getattr(entidade, 'max_mp', 0)

        self.ordem_turnos.sort(key=lambda entidade: entidade.atributos.get("Agi", 0), reverse=True)

        personagem.bloqueando = False
        personagem.recuperando = False
        personagem.focado = False
        self.turno_jogador_iniciado = False
        self.indice_turno = 0
        self.timer_inimigo = 0
        self.menu_acoes_estado = "principal"
        self.ataque_selecionado = None
        self.xp_calculado = False
        self.pontos_salvos_na_partida = False
        self.derrota_processada = False
        self.cooldown_feedback = 0
        self.acao_pos_feedback = None
        self.ultimo_chefe_combate = None
        self.gerar_botoes_ataque(personagem)
        self.atualizar_posicoes_inimigos()

        if self.evento_neutro is None and "👑" not in self.mensagem_log and "💤" not in self.mensagem_log and "⚑" not in self.mensagem_log:
            primeiro_na_ordem = self.ordem_turnos[0]
            if primeiro_na_ordem == personagem:
                self.mensagem_log = "⚡ Você é o mais rápido! Seu Turno!"
            elif getattr(self, 'personagem2', None) is not None and primeiro_na_ordem == self.personagem2:
                self.mensagem_log = "⚡ Jogador 2 é o mais rápido! Turno do Jogador 2!"
            else:
                self.mensagem_log = f"⚠️ {primeiro_na_ordem.nome} é mais rápido e começa!"

    def calcular_chance_drop_bilhete(self, inimigo):
        tipo = getattr(inimigo, "tipo", "").lower()
        max_hp = getattr(inimigo, "max_hp", 30)
        xp = getattr(inimigo, "xp", 20)
        nome = getattr(inimigo, "nome", "").lower()

        if tipo == "chefe" or "chefe" in nome or "sukuna" in nome or "nemesis" in nome or "comandante supremo" in nome or max_hp >= 120 or xp >= 200:
            return 0.35
        elif tipo == "grande" or "especial" in nome or "aberração" in nome or "gigante" in nome or "mecanoide" in nome or max_hp >= 60 or xp >= 70:
            return 0.20
        elif tipo == "medio" or max_hp >= 40 or xp >= 40:
            return 0.10
        else:
            return 0.05

    def calcular_chance_drop_equipamento(self, inimigo):
        tipo = getattr(inimigo, "tipo", "").lower()
        max_hp = getattr(inimigo, "max_hp", 30)
        xp = getattr(inimigo, "xp", 20)
        nome = getattr(inimigo, "nome", "").lower()

        if tipo == "chefe" or "chefe" in nome or "sukuna" in nome or "nemesis" in nome or "comandante supremo" in nome or max_hp >= 120 or xp >= 200:
            return 0.50
        elif tipo == "grande" or "especial" in nome or "aberração" in nome or "gigante" in nome or "mecanoide" in nome or max_hp >= 60 or xp >= 70:
            return 0.30
        elif tipo == "medio" or max_hp >= 40 or xp >= 40:
            return 0.20
        else:
            return 0.12

    def recuperar_apos_batalha(self, dormir=False):
        from Sistemas.Inventario import inventario_global
        dormiu = False
        if dormir:
            if inventario_global.consumir_bilhete_dormitorio(1):
                dormiu = True

        percentual_hp = 0.70 if dormiu else 0.30
        pontos_mp = 7 if dormiu else 3

        cura_info = {
            "hp": 0,
            "mp": 0,
            "percentual_hp": int(percentual_hp * 100),
            "pontos_mp": pontos_mp,
            "dormiu": dormiu,
            "jogadores": []
        }

        for jogador in self.obter_jogadores():
            hp_antes = jogador.hp
            mp_antes = jogador.mp
            jogador.hp = min(jogador.max_hp, jogador.hp + int(jogador.max_hp * percentual_hp))
            jogador.mp = min(jogador.max_mp, jogador.mp + pontos_mp)
            ganho_hp = int(jogador.hp - hp_antes)
            ganho_mp = int(jogador.mp - mp_antes)
            cura_info["hp"] = max(cura_info["hp"], ganho_hp)
            cura_info["mp"] = max(cura_info["mp"], ganho_mp)
            cura_info["jogadores"].append({
                "nome": getattr(jogador, 'nome', 'Jogador'),
                "hp": ganho_hp,
                "mp": ganho_mp
            })
        return cura_info

    def avancar_turno(self):
        self.alvo_destaque = None
        self.indice_turno += 1
        self.timer_inimigo = 0
        self.turno_jogador_iniciado = False
        self.menu_acoes_estado = "principal"

    def calcular_bonus_atributo(self, atacante, tipo_ataque):
        attr = MAPA_ATRIBUTO_CLASSE.get(tipo_ataque)
        if not attr:
            return 0
        bonus = getattr(atacante, 'atributos', {}).get(attr, 0)
        if getattr(atacante, 'is_player', False):
            from Sistemas.Inventario import inventario_global
            bonus += inventario_global.obter_bonus_atributo(attr)
        return bonus

    def calcular_defesa_passiva(self, entidade):
        """
        Calcula a defesa passiva do jogador a partir de sua Constituição (Con // 2)
        somada ao bônus de Armadura/Defesa fornecido pelos equipamentos de proteção.
        """
        if not entidade or not getattr(entidade, "is_player", False):
            return 0
        con = getattr(entidade, "atributos", {}).get("Con", 0)
        def_equip = 0
        try:
            from Sistemas.Inventario import inventario_global
            con += inventario_global.obter_bonus_atributo("Con")
            def_equip = inventario_global.obter_bonus_defesa()
        except Exception:
            pass
        defesa_con = max(0, con // 2)
        return defesa_con + max(0, def_equip)

    def obter_jogadores(self):
        jogadores = [personagem]
        if getattr(self, 'personagem2', None) is not None:
            jogadores.append(self.personagem2)
        return [jogador for jogador in jogadores if jogador is not None]

    def nome_exibicao(self, entidade):
        if entidade is None:
            return "alvo"
        if entidade == personagem:
            return "Jogador 1"
        if getattr(self, 'personagem2', None) is not None and entidade == self.personagem2:
            return "Jogador 2"
        if hasattr(entidade, 'nome') and entidade.nome:
            return entidade.nome
        return "alvo"

    def classe_do_jogador(self, jogador):
        if jogador == getattr(self, 'personagem2', None):
            return getattr(self, 'classe_jogador2', 'Nenhuma')
        return self.classe_atual

    def tipo_classe_do_jogador(self, jogador):
        if jogador == getattr(self, 'personagem2', None):
            return getattr(self, 'classe_jogador2_tipo', None)
        return getattr(self, 'classe_dano_atual', None)

    def tem_talento(self, entidade, id_talento):
        if not entidade or not getattr(entidade, 'is_player', False):
            return False
        if hasattr(entidade, 'tem_talento'):
            return entidade.tem_talento(id_talento)
        return id_talento in getattr(entidade, 'talentos', set())

    def velocidade_esquiva(self, entidade):
        agilidade = int(getattr(getattr(entidade, 'atributos', {}), 'get', lambda *args, **kwargs: 1)('Agi', 1))
        if getattr(entidade, 'is_player', False):
            from Sistemas.Inventario import inventario_global
            agilidade += inventario_global.obter_bonus_atributo("Agi")
        # Redução balanceada de velocidade por ponto de agilidade (até -35% de velocidade)
        reducao = min(0.35, max(0.0, agilidade * 0.015))
        vel = max(2.8, self.esquiva_vel * (1.0 - reducao))
        if self.tem_talento(entidade, "A3"):
            vel = max(2.4, vel * 0.85)
        return vel

    def executar_turno_minion(self, minion, alvo_forcado=None):
        if not minion or getattr(minion, "hp", 0) <= 0:
            return None
        if getattr(minion, "defendendo", False):
            self.mensagem_log = f"🛡️ {minion.nome} está defendendo e não ataca neste turno!"
            return self.mensagem_log
        if getattr(minion, "dormindo", False):
            minion.dormindo = False
            self.mensagem_log = f"💤 {minion.nome} está descansando/dormindo e não ataca neste turno!"
            return self.mensagem_log

        inimigos_vivos = [e for e in self.ordem_turnos if self.eh_inimigo(e) and e.hp > 0]
        if not inimigos_vivos:
            return None

        nome_golpe = minion.escolher_ataque()
        hab = minion.obter_habilidade(nome_golpe)
        custo = getattr(hab, "custo_mp", 0)
        if callable(custo):
            custo = custo(minion)
        minion.mp = max(0, minion.mp - int(custo))

        dano_final = minion.calcular_dano_ataque(hab)
        dono = getattr(minion, "dono", None) or personagem
        tem_i2 = self.tem_talento(dono, "I2")

        sorte_minion = int(getattr(minion, "atributos", {}).get("Sor", 2))
        chance_crit = min(1.0, 0.08 + (sorte_minion * 0.01))
        critico = False
        if getattr(dono, "god_mode", False):
            critico = True
            dano_final = max(dano_final, 9999)
        elif random.random() < chance_crit:
            critico = True
            dano_final = int(dano_final * 1.6)

        precisao_final = 1.0 if getattr(dono, "god_mode", False) else float(hab.precisao)
        if tem_i2:
            precisao_final = min(1.0, precisao_final + 0.10)

        if not critico and random.random() > precisao_final:
            minion.registrar_ataque(dano=0, acertou=False, critico=False, abates=0)
            self.mensagem_log = f"🐾 {minion.nome} usou {hab.nome}, mas ERROU!"
            return self.mensagem_log

        nome_hab_minion = (hab.nome or "").lower()
        if "mordida" in nome_hab_minion:
            self.tocar_sfx_mordida(volume_relativo=0.85)
        elif "soco" in nome_hab_minion:
            self.tocar_sfx_soco(volume_relativo=0.85)
        elif "corte" in nome_hab_minion:
            self.tocar_vfx_corte(volume_relativo=0.85)

        alvo_prioritario = alvo_forcado
        if not alvo_prioritario:
            alvo_pref = getattr(minion, "alvo_prioritario", None) or getattr(self, "alvo_prioritario_minions", None)
            if alvo_pref in inimigos_vivos and getattr(alvo_pref, "hp", 0) > 0:
                alvo_prioritario = alvo_pref

        alvo_principal = alvo_prioritario if (alvo_prioritario in inimigos_vivos) else random.choice(inimigos_vivos)
        alvos = inimigos_vivos if hab.em_area else [alvo_principal]

        dano_total_turno = 0
        abates_turno = 0
        efeitos_aplicados = []

        for alvo in alvos:
            alvo.hp = max(0, alvo.hp - dano_final)
            dano_total_turno += int(dano_final)
            self.dano_causado_total += int(dano_final)
            if alvo.hp <= 0:
                abates_turno += 1
                self.kills_total += 1
                self.dificuldade_total += max(1, int(getattr(alvo, "xp", 0)))
                from Sistemas.Conquistas import sistema_conquistas
                sistema_conquistas.desbloquear("primeiro_sangue")
            elif hab.efeito and random.random() < hab.chance_efeito:
                efeito_aplicado = self.aplicar_efeito_controle(alvo, hab.efeito)
                if efeito_aplicado and efeito_aplicado not in efeitos_aplicados:
                    efeitos_aplicados.append(efeito_aplicado)

        minion.registrar_ataque(dano=dano_total_turno, acertou=True, critico=critico, abates=abates_turno)

        if tem_i2 and (critico or abates_turno > 0):
            dono.mp = min(dono.max_mp, dono.mp + 1)

        prefixo = "🎯 CRÍTICO DO MINION! " if critico else "🐾 "
        txt_alvo = "EM ÁREA (TODOS OS INIMIGOS)" if hab.em_area else self.nome_exibicao(alvo_principal)
        self.alvo_destaque = alvos if hab.em_area else alvo_principal
        msg = f"{prefixo}{minion.nome} usou {hab.nome} no alvo {txt_alvo}! ({dano_final} dano)"
        if efeitos_aplicados:
            msg += f" {' '.join(efeitos_aplicados)}"
        self.mensagem_log = msg
        return self.mensagem_log

    def executar_turno_santuario(self, santuario):
        if not santuario or santuario.hp <= 0:
            self.avancar_turno()
            return

        if santuario.dono and getattr(santuario.dono, "hp", 0) <= 0:
            santuario._hp = 0
            self.mensagem_log = "💨 O Santuário ruiu com a queda de seu conjurador!"
            self.iniciar_cooldown_feedback(75, self.avancar_turno)
            return

        if getattr(santuario, "lado", "inimigo") == "inimigo":
            alvos = [j for j in self.obter_jogadores() if j.hp > 0] + self.obter_minions_vivos()
        else:
            alvos = [e for e in self.ordem_turnos if self.eh_inimigo(e) and not getattr(e, "is_santuario", False) and e.hp > 0]

        if not alvos:
            self.avancar_turno()
            return

        self.disparar_animacao_cortes(duracao=36)
        self.disparar_screen_shake(duracao=36, intensidade=8)
        self.tocar_vfx_corte(volume_relativo=1.0)

        dano_aplicado = 0
        for alvo in alvos:
            self.disparar_vfx_corte_alvo(alvo)
            dano_corte = max(8, int(getattr(alvo, "max_hp", 100) * 0.10))
            if getattr(alvo, "is_player", False):
                if getattr(alvo, "god_mode", False):
                    dano_corte = 0
                alvo.hp = max(0, alvo.hp - dano_corte)
            elif hasattr(alvo, "receber_dano"):
                alvo.receber_dano(dano_corte)
            else:
                alvo.hp = max(0, alvo.hp - dano_corte)
            dano_aplicado = dano_corte

        self.mensagem_log = f"⚔️ O Santuário desfere CORTES em área! (-{dano_aplicado} HP) [Duração: {santuario.duracao}/4]"
        self.iniciar_cooldown_feedback(65, self.avancar_turno)

    def executar_ataque_jogador(
        self,
        nome_habilidade,
        alvo_principal=None,
        jogador_ativo=None,
        multiplicador_minigame=1.0,
        feedback_minigame="",
        chance_erro_minigame=None,
        desempenho_minigame=None
    ):
        jogador_ativo = jogador_ativo or personagem
        hab = nome_habilidade if hasattr(nome_habilidade, 'dano') else banco_habilidades.get(nome_habilidade)
        if not hab:
            return
        minion_invocado = None
        inimigos_vivos = [entidade for entidade in self.ordem_turnos if self.eh_inimigo(entidade) and entidade.hp > 0]
        custo_mp = self._custo_habilidade(hab, jogador_ativo)

        jogador_ativo.mp = max(0, jogador_ativo.mp - custo_mp)

        nome_hab_lower = hab.nome.lower()
        if "corte" in nome_hab_lower or "clivagem" in nome_hab_lower or "desmantelar" in nome_hab_lower:
            self.tocar_vfx_corte(volume_relativo=0.9)
            if alvo_principal:
                self.disparar_vfx_corte_alvo(alvo_principal)
        elif "soco" in nome_hab_lower or "flash negro" in nome_hab_lower or "colisão 24 frames" in nome_hab_lower:
            self.tocar_sfx_soco(volume_relativo=0.9)
        elif "mordida" in nome_hab_lower:
            self.tocar_sfx_mordida(volume_relativo=0.9)

        if hab.nome in ("Plantar Spike", "Spike"):
            self.plantar_spike(dono=jogador_ativo)
            self.disparar_screen_shake(duracao=30, intensidade=6)
            self.mensagem_log = f"💣 ULTIMATE! {self.nome_exibicao(jogador_ativo)} plantou a Spike! (Detona em 50s!)"
            self.menu_acoes_estado = "principal"
            self.ataque_selecionado = None
            self.iniciar_cooldown_feedback(35, self.avancar_turno)
            return

        if hab.nome == "Santuário Malevolente" or getattr(hab, "minion", None) == "Pequeno Santuário":
            santuario = self.invocar_santuario(dono=jogador_ativo)
            self.disparar_animacao_cortes(duracao=38)
            self.disparar_screen_shake(duracao=38, intensidade=8)
            self.tocar_vfx_corte(volume_relativo=1.0)
            self.mensagem_log = f"⛩️ EXPANSÃO DE DOMÍNIO! {self.nome_exibicao(jogador_ativo)} manifestou o Santuário Malevolente!"
            self.menu_acoes_estado = "principal"
            self.ataque_selecionado = None
            self.iniciar_cooldown_feedback(35, self.avancar_turno)
            return

        if getattr(hab, "minion", None) or hab.tipo == "Invocador":
            errou_invocacao = False
            if chance_erro_minigame is not None:
                chance_invoc = float(chance_erro_minigame)
                if self.tem_talento(jogador_ativo, "A1"):
                    chance_invoc = max(0.0, chance_invoc - 0.05)
                if getattr(jogador_ativo, 'god_mode', False):
                    chance_invoc = 0.0
                errou_invocacao = (random.random() < chance_invoc)

            if errou_invocacao:
                nome_minion_alvo = getattr(hab, "minion", "minion")
                self.mensagem_log = f"💨 {self.nome_exibicao(jogador_ativo)} tentou invocar {nome_minion_alvo}, mas a invocação FALHOU!"
                if feedback_minigame:
                    self.mensagem_log += f" [{feedback_minigame}]"
                self.menu_acoes_estado = "principal"
                self.ataque_selecionado = None
                self.iniciar_cooldown_feedback(75, self.avancar_turno)
                return

            if getattr(hab, "minion", None):
                minion_invocado = self.invocar_minion(hab.minion, dono=jogador_ativo)
                if minion_invocado is None:
                    limite = self.limite_minions(jogador_ativo)
                    self.mensagem_log = f"⚠️ {self.nome_exibicao(jogador_ativo)} já atingiu o limite de summons ({limite})!"
                    self.menu_acoes_estado = "principal"
                    self.ataque_selecionado = None
                    self.iniciar_cooldown_feedback(35, self.avancar_turno)
                    return

                if getattr(hab, "is_ultimate", False):
                    for m in self.obter_minions_vivos(jogador_ativo):
                        if m is not minion_invocado:
                            m.curar_e_fortalecer(bonus_sab=3)

            if getattr(hab, "is_ultimate", False):
                self.mensagem_log = f"✨ {self.nome_exibicao(jogador_ativo)} liberou {hab.nome} e invocou {minion_invocado.nome if minion_invocado else 'seu minion'}!"
            else:
                self.mensagem_log = f"✨ {self.nome_exibicao(jogador_ativo)} invocou {minion_invocado.nome if minion_invocado else 'seu minion'}!"

            if feedback_minigame:
                self.mensagem_log += f" [{feedback_minigame}]"
            if minion_invocado and multiplicador_minigame > 1.0:
                bonus_hp = int(minion_invocado.max_hp * (multiplicador_minigame - 1.0))
                minion_invocado.max_hp += bonus_hp
                minion_invocado.hp += bonus_hp

            self.menu_acoes_estado = "principal"
            self.ataque_selecionado = None
            self.iniciar_cooldown_feedback(35, self.avancar_turno)
            return

        dano_base = hab.dano

        classe_jogador = self.classe_do_jogador(jogador_ativo)
        mult_verso = MULTIPLICADORES_VERSO_TIPO.get((classe_jogador, hab.tipo), 1.0)
        dano_base = int(dano_base * mult_verso)

        dano_final = dano_base + self.calcular_bonus_atributo(jogador_ativo, hab.tipo)
        if multiplicador_minigame != 1.0:
            dano_final = max(1, int(dano_final * multiplicador_minigame))

        tem_a2 = self.tem_talento(jogador_ativo, "A2")
        chance_crit_base = 0.15 if tem_a2 else 0.05
        sorte_jogador = getattr(jogador_ativo, "atributos", {}).get("Sor", 1)
        if getattr(jogador_ativo, 'is_player', False):
            from Sistemas.Inventario import inventario_global
            sorte_jogador += inventario_global.obter_bonus_atributo("Sor")
        chance_crit = min(1.0, chance_crit_base + (sorte_jogador * 0.005))
        mult_crit = 3.0 if tem_a2 else 1.5

        critico = False
        if getattr(jogador_ativo, 'god_mode', False):
            critico = True
            dano_final = max(dano_final, 9999)
        elif random.random() < chance_crit:
            critico = True
            dano_final = int(dano_final * mult_crit)
            from Sistemas.Conquistas import sistema_conquistas
            sistema_conquistas.desbloquear("critico_devastador")

        # Chance de errar baseada no desempenho do minigame de ataque
        if chance_erro_minigame is not None:
            chance_erro_final = float(chance_erro_minigame)
            if self.tem_talento(jogador_ativo, "A1"):
                chance_erro_final = max(0.0, chance_erro_final - 0.05)
            if getattr(jogador_ativo, 'god_mode', False):
                chance_erro_final = 0.0
            errou = (random.random() < chance_erro_final)
            if errou:
                critico = False
        else:
            precisao_final = 1.0 if getattr(jogador_ativo, 'god_mode', False) else hab.precisao
            if self.tem_talento(jogador_ativo, "A1"):
                precisao_final = min(1.0, precisao_final + 0.05)
            errou = (not critico and random.random() > precisao_final)

        if alvo_principal is None and inimigos_vivos:
            alvo_principal = inimigos_vivos[0]
        alvos = inimigos_vivos if hab.em_area else ([alvo_principal] if alvo_principal else [])
        self.alvo_destaque = alvos if hab.em_area else alvo_principal
        texto_alvo = "EM ÁREA (TODOS OS INIMIGOS)" if hab.em_area else (self.nome_exibicao(alvo_principal) if alvo_principal else "alvo")

        if not critico and errou:
            if minion_invocado is not None:
                self.mensagem_log = f"✨ {self.nome_exibicao(jogador_ativo)} invocou {minion_invocado.nome} contra o alvo {texto_alvo}, mas o golpe errou!"
            else:
                self.mensagem_log = f"💨 {self.nome_exibicao(jogador_ativo)} tentou {hab.nome} no alvo {texto_alvo}, mas ERROU!"
            if feedback_minigame:
                self.mensagem_log += f" [{feedback_minigame}]"
        else:
            msg = f"⚡ GOD MODE! " if getattr(jogador_ativo, 'god_mode', False) else (f"🎯 CRÍTICO! " if critico else f"💥 ")
            efeitos_aplicados = []
            if minion_invocado is not None:
                msg += f"{self.nome_exibicao(jogador_ativo)} invocou {minion_invocado.nome} contra o alvo {texto_alvo}! ({dano_final} dano)"
            else:
                msg += f"{self.nome_exibicao(jogador_ativo)} usou {hab.nome} no alvo {texto_alvo}! ({dano_final} dano)"

            if feedback_minigame:
                msg += f" [{feedback_minigame}]"

            self.tocar_sfx_acerto(volume_relativo=0.85)

            for alvo in alvos:
                alvo.hp -= dano_final
                alvo.hp = max(0, alvo.hp)

                if getattr(jogador_ativo, 'is_player', False):
                    self.dano_causado_total += int(dano_final)
                    if alvo.hp <= 0:
                        self.kills_total += 1
                        self.dificuldade_total += max(1, int(getattr(alvo, 'xp', 0)))
                        from Sistemas.Conquistas import sistema_conquistas
                        sistema_conquistas.desbloquear("primeiro_sangue")

                # Se Sukuna for derrotado, seu santuario colapsa imediatamente
                if "sukuna" in getattr(alvo, "nome", "").lower() and alvo.hp <= 0:
                    for ent in self.ordem_turnos:
                        if getattr(ent, "is_santuario", False) and getattr(ent, "lado", "") == "inimigo":
                            ent._hp = 0

                if hab.efeito and random.random() < hab.chance_efeito:
                    efeito_aplicado = self.aplicar_efeito_controle(alvo, hab.efeito)
                    if efeito_aplicado and efeito_aplicado not in efeitos_aplicados:
                        efeitos_aplicados.append(efeito_aplicado)

            if alvo_principal and getattr(alvo_principal, "is_santuario", False) and not hab.em_area:
                if alvo_principal.hp <= 0:
                    msg = f"💥 O Pequeno Santuário foi DESTRUÍDO pelos ataques de {self.nome_exibicao(jogador_ativo)}!"
                else:
                    msg = f"⚔️ {self.nome_exibicao(jogador_ativo)} atacou o Santuário! [Duração: {alvo_principal.duracao}/4]"

            if efeitos_aplicados:
                msg += f" {' '.join(efeitos_aplicados)}"
            self.mensagem_log = msg

        self.menu_acoes_estado = "principal"
        self.ataque_selecionado = None
        cd_frames = 35 if (desempenho_minigame is not None or chance_erro_minigame is not None) else 75
        self.iniciar_cooldown_feedback(cd_frames, self.avancar_turno)

    def iniciar_minigame_ataque(self, hab, alvo=None, jogador_ativo=None):
        """Dispara o minigame interativo correspondente ao ataque do jogador."""
        if getattr(hab, "is_ultimate", False):
            self.executar_ataque_jogador(hab.nome, alvo_principal=alvo, jogador_ativo=jogador_ativo)
            return

        self.alvo_destaque = alvo
        self.menu_acoes_estado = "minigame_ataque"
        self.minigame_ataque.iniciar(hab, alvo=alvo, jogador_ativo=jogador_ativo)

    def finalizar_minigame_ataque(self, resultado):
        """Conclui o minigame de ataque e repassa multiplicadores e precisão baseados no desempenho."""
        mult = resultado.get("multiplicador", 1.0)
        feedback = resultado.get("feedback", "")
        desempenho = resultado.get("desempenho", 1.0)
        chance_erro = resultado.get("chance_erro", 0.0)
        shake = resultado.get("screen_shake", False)
        if shake:
            self.disparar_screen_shake(duracao=16, intensidade=6)

        hab = self.minigame_ataque.hab
        alvo = self.minigame_ataque.alvo
        jogador = self.minigame_ataque.jogador_ativo

        self.executar_ataque_jogador(
            hab.nome,
            alvo_principal=alvo,
            jogador_ativo=jogador,
            multiplicador_minigame=mult,
            feedback_minigame=feedback,
            chance_erro_minigame=chance_erro,
            desempenho_minigame=desempenho
        )

    def processar_evento(self, evento, posicao_mouse):
        """Encaminha eventos de entrada (clique e teclas) aos minigames ativos."""
        if self.menu_acoes_estado == "minigame_ataque" and getattr(self, "minigame_ataque", None) and self.minigame_ataque.esta_ativo():
            self.minigame_ataque.processar_evento(evento, posicao_mouse)
        elif self.menu_acoes_estado == "esquivando" and getattr(self, "minigame_esquiva", None) and self.minigame_esquiva.esta_ativo():
            self.minigame_esquiva.processar_evento(evento, posicao_mouse)

    def atualizar(self, posicao_mouse, estado_clique_mouse):
        self.tempo_animacao += 0.04
        self.atualizar_posicoes_inimigos()
        self.atualizar_cortes_santuario()
        self.atualizar_spike_e_detonacao()

        for e in self.ordem_turnos:
            if getattr(e, 'hp', 0) <= 0 and hasattr(e, 'acionar_derrota') and not getattr(e, 'derrotado', False):
                e.acionar_derrota()
            if hasattr(e, 'atualizar_animacao_derrota'):
                e.atualizar_animacao_derrota()

        for j in self.obter_jogadores():
            if getattr(j, 'god_mode', False):
                j.hp = j.max_hp
                j.mp = j.max_mp
                self.limpar_efeitos_controle(j)

        clique_agora = estado_clique_mouse[0] if isinstance(estado_clique_mouse, (tuple, list)) else bool(estado_clique_mouse)
        clicou = not clique_agora and self.clique_anterior

        self.btn_pausa.atualizar(posicao_mouse, estado_clique_mouse)
        if clicou and self.btn_pausa.clicado(posicao_mouse):
            self.clique_anterior = clique_agora
            return "pausa"

        # Se estiver no minigame de desarme da Spike, processa a lógica de bullet hell e mouse na esfera
        if self.menu_acoes_estado == "desarmando_spike":
            res_minigame = self._processar_minigame_spike(posicao_mouse, estado_clique_mouse, clicou)
            self.clique_anterior = clique_agora
            return res_minigame

        # Cooldown ativo durante ações para garantir feedback visual adequado
        if self.cooldown_feedback > 0:
            self.cooldown_feedback -= 1
            if self.cooldown_feedback == 0 and callable(self.acao_pos_feedback):
                acao = self.acao_pos_feedback
                self.acao_pos_feedback = None
                resultado_acao = acao()
                if resultado_acao:
                    self.clique_anterior = clique_agora
                    return resultado_acao
            self.clique_anterior = clique_agora
            return None

        inimigos_vivos = [entidade for entidade in self.ordem_turnos if self.eh_inimigo(entidade) and entidade.hp > 0]
        jogadores_vivos = [entidade for entidade in self.ordem_turnos if getattr(entidade, 'is_player', False) and entidade.hp > 0]

        if not jogadores_vivos:
            if not getattr(self, 'derrota_processada', False):
                self.derrota_processada = True
                self.pontos_jogo = 0
                from Sistemas.Conquistas import sistema_conquistas
                sistema_conquistas.desbloquear("acontece_com_todos")
                self.mensagem_log = "💀 Você foi derrotado!"
                self.ultimo_chefe_combate = None
                for inimigo in self.ordem_turnos:
                    if self.eh_inimigo(inimigo):
                        nome_i = getattr(inimigo, "nome", "").lower()
                        if "sukuna" in nome_i:
                            self.ultimo_chefe_combate = "Sukuna"
                            break
                        elif "charlie" in nome_i:
                            self.ultimo_chefe_combate = "Charlie"
                            break
                        elif "estraga prazeres" in nome_i:
                            self.ultimo_chefe_combate = "Estraga Prazeres"
                            break
                self.iniciar_cooldown_feedback(30, lambda: "game_over")
                self.clique_anterior = clique_agora
                return None
            return "game_over" 

        if not inimigos_vivos:
            if not self.xp_calculado:
                multiplicador_rec = getattr(self, "multiplicador_recompensa", 1.0)
                xp_base = sum(getattr(entidade, 'xp', 0) for entidade in self.ordem_turnos if self.eh_inimigo(entidade))
                xp_ganho = int(xp_base * multiplicador_rec)
                jogadores_participantes = [entidade for entidade in self.ordem_turnos if getattr(entidade, 'is_player', False)]
                for jogador in jogadores_participantes:
                    jogador.xp += xp_ganho
                    novo_nivel = (jogador.xp // 100) + 1
                    if novo_nivel > jogador.nivel:
                        niveis_ganhos = novo_nivel - jogador.nivel
                        jogador.pontos_atributo += (3 * niveis_ganhos)
                        jogador.nivel = novo_nivel

                self.pontos_jogo += int(self.calcular_pontos_desempenho(xp_ganho) * multiplicador_rec)
                self.xp_calculado = True

                from Sistemas.Conquistas import sistema_conquistas
                if self.classe_atual == "Sobrevivente":
                    sistema_conquistas.desbloquear("vitoria_sobrevivente")
                elif self.classe_atual == "Agente":
                    sistema_conquistas.desbloquear("vitoria_agente")
                elif self.classe_atual == "Feiticeiro":
                    sistema_conquistas.desbloquear("vitoria_feiticeiro")

                from Sistemas.Inventario import inventario_global
                inimigos_derrotados = [e for e in self.ordem_turnos if self.eh_inimigo(e)]
                self.ultimo_chefe_derrotado = None
                for inimigo_chefe in inimigos_derrotados:
                    nome_ch = getattr(inimigo_chefe, 'nome', '').lower()
                    if 'sukuna' in nome_ch:
                        self.ultimo_chefe_derrotado = 'Sukuna'
                        break
                    elif 'charlie' in nome_ch:
                        self.ultimo_chefe_derrotado = 'Charlie'
                        break
                    elif 'estraga prazeres' in nome_ch:
                        self.ultimo_chefe_derrotado = 'Estraga Prazeres'
                        break
                drop_msg = []
                itens_obtidos = []
                for inimigo in inimigos_derrotados:
                    if random.random() < 0.3:
                        inventario_global.adicionar_consumivel("Poção de Vida", "Restaura 30 HP", 30, 0)
                        drop_msg.append("Vida")
                        itens_obtidos.append("Poção de Vida")
                    elif random.random() < 0.2:
                        inventario_global.adicionar_consumivel("Poção de Mana", "Restaura 10 MP", 0, 10)
                        drop_msg.append("Mana")
                        itens_obtidos.append("Poção de Mana")
                    if random.random() < 0.4:
                        inventario_global.adicionar_material("Sucata", "Melhora equips.")
                        drop_msg.append("Sucata")
                        itens_obtidos.append("Sucata")

                    chance_bilhete = self.calcular_chance_drop_bilhete(inimigo)
                    if random.random() < chance_bilhete:
                        inventario_global.adicionar_bilhete_dormitorio(1)
                        drop_msg.append("Bilhete Dormitório")
                        itens_obtidos.append("Bilhete do Dormitório")

                    chance_equip = self.calcular_chance_drop_equipamento(inimigo)
                    if random.random() < chance_equip:
                        novo_eq = inventario_global.gerar_equipamento_aleatorio()
                        inventario_global.adicionar_equipamento(novo_eq, auto_equipar=True)
                        drop_msg.append(novo_eq.nome)
                        itens_obtidos.append(novo_eq.nome)

                if drop_msg:
                    self.mensagem_log = f"🎉 Vitória! Drops: {', '.join(drop_msg)}"
                else:
                    self.mensagem_log = f"🎉 Vitória! +{xp_ganho} XP ganho!"

                cura_info = self.recuperar_apos_batalha(dormir=False)
                self.ultimo_resultado_batalha = {
                    "cura": cura_info,
                    "itens": itens_obtidos,
                    "xp": xp_ganho,
                    "mensagem": f"Vitória! +{xp_ganho} XP e {self.pontos_jogo} pontos ganhos."
                }

                if self.partida_atual >= self.total_partidas:
                    sistema_conquistas.desbloquear("chefe_derrotado")
                    self.mensagem_log = f"🏆 CHEFE DERROTADO! Pontos ganhos: {self.pontos_jogo}"
                    self.iniciar_cooldown_feedback(75, lambda: "fim_jogo")
                    self.clique_anterior = clique_agora
                    return None

                self.partida_atual += 1
                self.iniciar_cooldown_feedback(70, lambda: "vitoria")
                self.clique_anterior = clique_agora
                return None
            return "vitoria"

        if not self.ordem_turnos:
            self.clique_anterior = clique_agora
            return None

        total_entidades = len(self.ordem_turnos)
        if self.indice_turno >= total_entidades:
            self.indice_turno = 0
            self.processar_fim_rodada()

        passos_busca = 0
        while self.ordem_turnos[self.indice_turno].hp <= 0 and passos_busca < total_entidades:
            self.indice_turno = (self.indice_turno + 1) % total_entidades
            passos_busca += 1
            if self.indice_turno == 0:
                self.processar_fim_rodada()

        entidade_atual = self.ordem_turnos[self.indice_turno]
        clique_agora = estado_clique_mouse[0] if isinstance(estado_clique_mouse, (tuple, list)) else bool(estado_clique_mouse)
        clicou = not clique_agora and self.clique_anterior

        self.btn_pausa.atualizar(posicao_mouse, estado_clique_mouse)
        if clicou and self.btn_pausa.clicado(posicao_mouse):
            self.clique_anterior = clique_agora
            return "pausa"

        # 1. Processamento prioritário dos minigames ativos (executa a cada frame sem travar)
        if self.menu_acoes_estado == "minigame_ataque":
            teclas = pygame.key.get_pressed()
            resultado = self.minigame_ataque.atualizar(posicao_mouse, estado_clique_mouse, teclas)
            if resultado and resultado.get("concluido"):
                self.finalizar_minigame_ataque(resultado)
            self.clique_anterior = clique_agora
            return None

        if self.menu_acoes_estado == "esquivando":
            resultado_esquiva = self.minigame_esquiva.atualizar(clicou=clicou)
            self.barras_esquiva = self.minigame_esquiva.barras
            self.acertos_esquiva = self.minigame_esquiva.acertos
            self.acertos_centro_esquiva = self.minigame_esquiva.acertos_centro
            self.reducao_esquiva = self.minigame_esquiva.reducao
            if self.minigame_esquiva.ultimo_feedback:
                self.mensagem_log = self.minigame_esquiva.ultimo_feedback

            if resultado_esquiva and resultado_esquiva.get("concluido"):
                alvo_esquivando = getattr(self, 'alvo_jogador_pendente', personagem)
                condicoes_evitadas = resultado_esquiva.get("evitou_tudo", False)
                dano_tomado = resultado_esquiva.get("dano_tomado", 0)

                minions_guarda = self.obter_minions_vivos(alvo_esquivando)
                if dano_tomado > 1 and self.tem_talento(alvo_esquivando, "I3") and minions_guarda:
                    absorvido = max(1, int(dano_tomado * 0.25))
                    minions_guarda[0].receber_dano(absorvido)
                    dano_tomado = max(1, dano_tomado - absorvido)

                alvo_esquivando.hp = max(0, alvo_esquivando.hp - dano_tomado)
                if dano_tomado > 0:
                    self.tocar_sfx_dano(volume_relativo=0.85)

                if condicoes_evitadas:
                    if self.acertos_centro_esquiva >= 2:
                        from Sistemas.Conquistas import sistema_conquistas
                        sistema_conquistas.desbloquear("mestre_esquiva")
                    if dano_tomado <= 1 and self.dano_pendente > 1:
                        self.mensagem_log = f"✨ Esquiva completa! Apenas {dano_tomado} dano."
                    else:
                        self.mensagem_log = f"💨 Esquiva concluída! {dano_tomado} dano."
                else:
                    msg_base = f"❌ Esquiva incompleta! {dano_tomado} dano."
                    if self.efeitos_pendentes and random.random() < self.chance_efeito_pendente:
                        if self.tem_talento(alvo_esquivando, "S3"):
                            msg_base += " (Imune a efeitos!)"
                        else:
                            efeitos_aplicados = self.aplicar_efeitos_controle(alvo_esquivando, self.efeitos_pendentes)
                            if efeitos_aplicados:
                                msg_base += f" {' '.join(efeitos_aplicados)}"
                    self.mensagem_log = msg_base
                self.menu_acoes_estado = "principal"
                self.barras_esquiva = []
                self.iniciar_cooldown_feedback(35, self.avancar_turno)
            self.clique_anterior = clique_agora
            return None

        if entidade_atual == personagem or (getattr(self, 'personagem2', None) is not None and entidade_atual == self.personagem2):
            jogador_atual = entidade_atual
            efeito_controle = self.obter_efeito_controle(jogador_atual)
            if efeito_controle:
                if self.timer_inimigo == 0:
                    status = "CONGELADO" if efeito_controle == "Congelar" else "ATORDOADO"
                    icone = "❄️" if efeito_controle == "Congelar" else "💫"
                    if getattr(self, 'duas_pessoas', False):
                        nome_j = self.nome_exibicao(jogador_atual)
                        self.mensagem_log = f"{icone} {nome_j} está {status} e perdeu o turno!"
                    else:
                        self.mensagem_log = f"{icone} Você está {status} e perdeu o turno!"
                self.timer_inimigo += 1
                if self.timer_inimigo >= self.tempo_espera_inimigo:
                    self.limpar_efeitos_controle(jogador_atual)
                    self.iniciar_cooldown_feedback(45, self.avancar_turno)
            else:
                if not self.turno_jogador_iniciado:
                    self.turno_jogador_iniciado = True
                    jogador_atual.bloqueando = False
                    jogador_atual.recuperando = False
                    jogador_atual.focado = False
                    self.mensagem_log = "Seu Turno!" if jogador_atual == personagem else "Turno do Jogador 2!"
                    if jogador_atual.mp < jogador_atual.max_mp:
                        ganho_passivo = 2 if self.tem_talento(jogador_atual, "F1") else 1
                        jogador_atual.mp = min(jogador_atual.max_mp, jogador_atual.mp + ganho_passivo)

                # Clique direto na Spike em qualquer estado de ação do jogador
                if clicou and getattr(self, "spike", None) and self.spike.ativa and not self.spike.desarmada and self.spike.rect.collidepoint(posicao_mouse):
                    self.iniciar_minigame_desarme_spike()
                    self.clique_anterior = clique_agora
                    return None

                manipuladores_menu = {
                    "principal": lambda: self._processar_menu_principal(jogador_atual, posicao_mouse, estado_clique_mouse, clicou),
                    "agir": lambda: self._processar_menu_agir(jogador_atual, posicao_mouse, estado_clique_mouse, clicou),
                    "ataques": lambda: self._processar_menu_ataques(jogador_atual, posicao_mouse, estado_clique_mouse, clicou),
                    "minions": lambda: self._processar_menu_minions(jogador_atual, posicao_mouse, estado_clique_mouse, clicou),
                    "comandos": lambda: self._processar_menu_comandos(jogador_atual, posicao_mouse, estado_clique_mouse, clicou),
                    "itens": lambda: self._processar_menu_itens(jogador_atual, posicao_mouse, estado_clique_mouse, clicou),
                    "selecionar_alvo": lambda: self._processar_menu_selecionar_alvo(jogador_atual, posicao_mouse, estado_clique_mouse, clicou, inimigos_vivos),
                    "selecionar_alvo_comando_atingir": lambda: self._processar_selecao_alvo_atingir(jogador_atual, posicao_mouse, estado_clique_mouse, clicou, inimigos_vivos),
                    "selecionar_minion_comando_defender": lambda: self._processar_selecao_minion_defender(jogador_atual, posicao_mouse, estado_clique_mouse, clicou),
                    "selecionar_minion_comando_descansar": lambda: self._processar_selecao_minion_descansar(jogador_atual, posicao_mouse, estado_clique_mouse, clicou),
                }
                if manipulador := manipuladores_menu.get(self.menu_acoes_estado):
                    if resultado_menu := manipulador():
                        return resultado_menu

            self.clique_anterior = clique_agora
            return None

        if self.eh_minion(entidade_atual):
            efeito_controle = self.obter_efeito_controle(entidade_atual)
            if efeito_controle:
                if self.timer_inimigo == 0:
                    status = "CONGELADO" if efeito_controle == "Congelar" else "ATORDOADO"
                    icone = "❄️" if efeito_controle == "Congelar" else "💫"
                    self.mensagem_log = f"{icone} {entidade_atual.nome} está {status}!"
                self.timer_inimigo += 1
                if self.timer_inimigo >= max(25, self.tempo_espera_inimigo // 2):
                    self.limpar_efeitos_controle(entidade_atual)
                    self.iniciar_cooldown_feedback(40, self.avancar_turno)
            elif getattr(entidade_atual, "defendendo", False):
                if self.timer_inimigo == 0:
                    self.mensagem_log = f"🛡️ {entidade_atual.nome} está em guarda defendendo e não ataca!"
                self.timer_inimigo += 1
                if self.timer_inimigo >= max(35, self.tempo_espera_inimigo // 2):
                    self.iniciar_cooldown_feedback(40, self.avancar_turno)
            elif getattr(entidade_atual, "dormindo", False):
                if self.timer_inimigo == 0:
                    self.mensagem_log = f"💤 {entidade_atual.nome} está descansando/dormindo e não ataca!"
                self.timer_inimigo += 1
                if self.timer_inimigo >= max(35, self.tempo_espera_inimigo // 2):
                    entidade_atual.dormindo = False
                    self.iniciar_cooldown_feedback(40, self.avancar_turno)
            else:
                if self.timer_inimigo == 0:
                    self.mensagem_log = f"🐾 Turno de {entidade_atual.nome}..."
                self.timer_inimigo += 1
                if self.timer_inimigo >= max(35, self.tempo_espera_inimigo // 2):
                    if entidade_atual.mp < entidade_atual.max_mp:
                        entidade_atual.mp = min(entidade_atual.max_mp, entidade_atual.mp + 1)
                    self.executar_turno_minion(entidade_atual)
                    self.iniciar_cooldown_feedback(75, self.avancar_turno)
            self.clique_anterior = clique_agora
            return None

        if getattr(entidade_atual, "is_santuario", False):
            efeito_controle = self.obter_efeito_controle(entidade_atual)
            if efeito_controle:
                self.limpar_efeitos_controle(entidade_atual)
                self.iniciar_cooldown_feedback(30, self.avancar_turno)
                self.clique_anterior = clique_agora
                return None

            if self.timer_inimigo == 0:
                self.mensagem_log = f"⛩️ Turno do {entidade_atual.nome}..."
            self.timer_inimigo += 1
            if self.timer_inimigo >= max(35, self.tempo_espera_inimigo // 2):
                self.executar_turno_santuario(entidade_atual)
            self.clique_anterior = clique_agora
            return None

        # Turno do Inimigo
        nome_inimigo = entidade_atual.nome
        efeito_controle = self.obter_efeito_controle(entidade_atual)
        if efeito_controle:
            if self.timer_inimigo == 0:
                status = "CONGELADO" if efeito_controle == "Congelar" else "ATORDOADO"
                icone = "❄️" if efeito_controle == "Congelar" else "💫"
                self.mensagem_log = f"{icone} {nome_inimigo} {status}!"
            self.timer_inimigo += 1
            if self.timer_inimigo >= self.tempo_espera_inimigo:
                self.limpar_efeitos_controle(entidade_atual)
                self.iniciar_cooldown_feedback(45, self.avancar_turno)
        else:
            if self.timer_inimigo == 0:
                self.mensagem_log = f"⚠️ Turno de {nome_inimigo}..."
                if entidade_atual.mp < getattr(entidade_atual, "max_mp", 10):
                    ganho_mp = 3 if getattr(entidade_atual, "tipo", "") == "chefe" else 1
                    entidade_atual.mp = min(entidade_atual.max_mp, entidade_atual.mp + ganho_mp)
            self.timer_inimigo += 1
            if self.timer_inimigo >= self.tempo_espera_inimigo:
                eh_confinamento = (
                    "confinamento" in nome_inimigo.lower()
                    or getattr(entidade_atual, "eh_confinamento", False)
                    or "Confinamento" in getattr(entidade_atual, "ataques", [])
                )

                if eh_confinamento:
                    carga_atual = getattr(entidade_atual, "carga_confinamento", 0) + 1
                    max_c = getattr(entidade_atual, "max_carga_confinamento", 5)
                    entidade_atual.carga_confinamento = carga_atual

                    if carga_atual < max_c:
                        self.disparar_screen_shake(duracao=10, intensidade=3)
                        self.mensagem_log = f"⚡ [CONFINAMENTO] O dispositivo está carregando... ({carga_atual}/{max_c} rodadas)!"
                        self.iniciar_cooldown_feedback(55, self.avancar_turno)
                        self.clique_anterior = clique_agora
                        return None
                    else:
                        entidade_atual.carga_confinamento = 0
                        self.disparar_screen_shake(duracao=40, intensidade=9)
                        self.tocar_som_desarmar(volume_relativo=1.0)

                        for jogador in self.obter_jogadores():
                            if not getattr(jogador, "god_mode", False):
                                self.aplicar_efeito_controle(jogador, "Atordoar")
                                jogador.atordoado = True

                        for minion in self.obter_minions_vivos():
                            if getattr(minion, "dono", None) in self.obter_jogadores():
                                self.aplicar_efeito_controle(minion, "Atordoar")
                                minion.atordoado = True

                        self.mensagem_log = "🚨 [CONFINAMENTO ATIVADO!] Onda de choque expansiva! TODOS OS OPONENTES FORAM ATORDOADOS!"
                        self.iniciar_cooldown_feedback(75, self.avancar_turno)
                        self.clique_anterior = clique_agora
                        return None

                ataques_possiveis = [a for a in entidade_atual.ataques if entidade_atual.obter_habilidade(a).custo_mp <= entidade_atual.mp]
                if not ataques_possiveis:
                    ataques_possiveis = [entidade_atual.ataques[0]] if entidade_atual.ataques else ["Soco"]

                santuario_ativo = any(getattr(e, "is_santuario", False) and e.hp > 0 for e in self.ordem_turnos)
                eh_sukuna = ("sukuna" in nome_inimigo.lower() or "Santuário Malevolente" in entidade_atual.ataques)
                eh_estraga_prazeres = ("estraga prazeres" in nome_inimigo.lower() or "Plantar Spike" in entidade_atual.ataques or "Spike" in entidade_atual.ataques)
                spike_ativa = (getattr(self, "spike", None) is not None and getattr(self.spike, "ativa", False))

                if eh_sukuna and not santuario_ativo and entidade_atual.mp >= 10:
                    nome_golpe_inimigo = "Santuário Malevolente"
                elif eh_estraga_prazeres and not spike_ativa and entidade_atual.mp >= 10:
                    nome_golpe_inimigo = "Plantar Spike"
                else:
                    especiais = [a for a in ataques_possiveis if entidade_atual.obter_habilidade(a).custo_mp > 0 and a not in ("Santuário Malevolente", "Plantar Spike", "Spike")]
                    if not especiais:
                        especiais = [a for a in ataques_possiveis if a not in ("Santuário Malevolente", "Plantar Spike", "Spike")]
                    if not especiais:
                        especiais = ataques_possiveis
                    if especiais and random.random() < 0.70:
                        nome_golpe_inimigo = random.choice(especiais)
                    else:
                        nome_golpe_inimigo = random.choice(ataques_possiveis)

                hab_usada = entidade_atual.obter_habilidade(nome_golpe_inimigo)

                entidade_atual.mp -= hab_usada.custo_mp
                entidade_atual.mp = max(0, entidade_atual.mp)
                if entidade_atual.mp == 0:
                    from Sistemas.Conquistas import sistema_conquistas
                    sistema_conquistas.desbloquear("mana_esgotada")

                if nome_golpe_inimigo in ("Plantar Spike", "Spike"):
                    self.plantar_spike(dono=entidade_atual)
                    self.disparar_screen_shake(duracao=32, intensidade=6)
                    self.mensagem_log = f"💣 ULTIMATE! {nome_inimigo} PLANTOU A SPIKE! Desarme-a antes que ela exploda!"
                    self.iniciar_cooldown_feedback(65, self.avancar_turno)
                    self.clique_anterior = clique_agora
                    return None

                if nome_golpe_inimigo == "Santuário Malevolente" or getattr(hab_usada, "minion", None) == "Pequeno Santuário":
                    santuario = self.invocar_santuario(dono=entidade_atual)
                    self.disparar_animacao_cortes(duracao=38)
                    self.disparar_screen_shake(duracao=38, intensidade=8)
                    self.tocar_vfx_corte(volume_relativo=1.0)
                    self.mensagem_log = f"⛩️ EXPANSÃO DE DOMÍNIO! {nome_inimigo} manifestou o Santuário Malevolente!"
                    self.iniciar_cooldown_feedback(65, self.avancar_turno)
                    self.clique_anterior = clique_agora
                    return None

                nome_golpe_lower = (hab_usada.nome or "").lower()
                eh_ataque_corte = (
                    "sukuna" in nome_inimigo.lower()
                    or "clivagem" in nome_golpe_lower
                    or "desmantelar" in nome_golpe_lower
                    or "corte" in nome_golpe_lower
                )
                if eh_ataque_corte:
                    self.tocar_vfx_corte(volume_relativo=0.9)
                elif "soco" in nome_golpe_lower:
                    self.tocar_sfx_soco(volume_relativo=0.9)
                elif "mordida" in nome_golpe_lower:
                    self.tocar_sfx_mordida(volume_relativo=0.9)

                bonus_inimigo = self.calcular_bonus_atributo(entidade_atual, hab_usada.tipo)
                dano_inimigo = hab_usada.dano + bonus_inimigo

                classe_inimigo = getattr(entidade_atual, "classe", None)
                if classe_inimigo and getattr(hab_usada, "tipo", None):
                    c_norm = str(classe_inimigo).strip().lower()
                    t_norm = str(hab_usada.tipo).strip().lower()
                    eh_fisico = c_norm in ("físico", "fisico") and t_norm in ("físico", "fisico")
                    eh_distancia = c_norm in ("distância", "distancia") and t_norm in ("distância", "distancia")
                    eh_magia = c_norm == "magia" and t_norm == "magia"
                    eh_invoc = c_norm in ("invocador", "invocação", "invocacao") and t_norm in ("invocador", "invocação", "invocacao")
                    if c_norm == t_norm or eh_fisico or eh_distancia or eh_magia or eh_invoc:
                        dano_inimigo = int(dano_inimigo * 1.25)

                sorte_inimigo = getattr(entidade_atual, "atributos", {}).get("Sor", 1)
                chance_crit_inimigo = min(1.0, 0.05 + (sorte_inimigo * 0.001))
                critico = False
                if random.random() < chance_crit_inimigo:
                    critico = True
                    dano_inimigo = int(dano_inimigo * 1.5)

                jogadores_vivos = [j for j in self.obter_jogadores() if j.hp > 0]
                minions_vivos = self.obter_minions_vivos()

                minions_defendendo = [m for m in minions_vivos if getattr(m, "defendendo", False)]
                if minions_defendendo:
                    alvo_minion = random.choice(minions_defendendo)
                    self.alvo_destaque = alvo_minion
                    efeitos_ataque, chance_efeito = self.obter_efeitos_ataque_inimigo(entidade_atual, hab_usada)
                    if not critico and random.random() > hab_usada.precisao:
                        self.mensagem_log = f"💨 {nome_inimigo} atacou o alvo {alvo_minion.nome}, mas ERROU!"
                    else:
                        if eh_ataque_corte:
                            self.disparar_vfx_corte_alvo(alvo_minion)
                        alvo_minion.receber_dano(dano_inimigo)
                        if dano_inimigo > 0:
                            self.tocar_sfx_dano(volume_relativo=0.8)
                        efeitos_aplicados = []
                        if efeitos_ataque and random.random() < chance_efeito:
                            efeitos_aplicados = self.aplicar_efeitos_controle(alvo_minion, efeitos_ataque)
                        if alvo_minion.hp <= 0:
                            self.mensagem_log = f"💥 {nome_inimigo} destruiu o defensor {alvo_minion.nome}! ({dano_inimigo} dano)"
                        else:
                            self.mensagem_log = f"🛡️ {nome_inimigo} atacou o defensor {alvo_minion.nome}! ({dano_inimigo} dano)"
                            if efeitos_aplicados:
                                self.mensagem_log += f" {' '.join(efeitos_aplicados)}"
                    self.iniciar_cooldown_feedback(75, self.avancar_turno)
                    self.clique_anterior = clique_agora
                    return None
                elif minions_vivos and random.random() < 0.45:
                    alvo_minion = random.choice(minions_vivos)
                    self.alvo_destaque = alvo_minion
                    efeitos_ataque, chance_efeito = self.obter_efeitos_ataque_inimigo(entidade_atual, hab_usada)
                    if not critico and random.random() > hab_usada.precisao:
                        self.mensagem_log = f"💨 {nome_inimigo} atacou o alvo {alvo_minion.nome}, mas ERROU!"
                    else:
                        if eh_ataque_corte:
                            self.disparar_vfx_corte_alvo(alvo_minion)
                        alvo_minion.receber_dano(dano_inimigo)
                        if dano_inimigo > 0:
                            self.tocar_sfx_dano(volume_relativo=0.8)
                        efeitos_aplicados = []
                        if efeitos_ataque and random.random() < chance_efeito:
                            efeitos_aplicados = self.aplicar_efeitos_controle(alvo_minion, efeitos_ataque)
                        if alvo_minion.hp <= 0:
                            self.mensagem_log = f"💥 {nome_inimigo} destruiu o alvo {alvo_minion.nome}! ({dano_inimigo} dano)"
                        else:
                            self.mensagem_log = f"🐾 {nome_inimigo} atacou o alvo {alvo_minion.nome}! ({dano_inimigo} dano)"
                            if efeitos_aplicados:
                                self.mensagem_log += f" {' '.join(efeitos_aplicados)}"
                    self.iniciar_cooldown_feedback(75, self.avancar_turno)
                    self.clique_anterior = clique_agora
                    return None

                if not jogadores_vivos:
                    self.clique_anterior = clique_agora
                    return None
                alvo_jogador = random.choice(jogadores_vivos)
                self.alvo_jogador_pendente = alvo_jogador
                self.alvo_destaque = alvo_jogador

                precisao_inimigo = hab_usada.precisao
                if self.tem_talento(alvo_jogador, "A3"):
                    precisao_inimigo = max(0.15, precisao_inimigo - 0.20)

                if not critico and random.random() > precisao_inimigo:
                    self.mensagem_log = f"💨 {nome_inimigo} usou {hab_usada.nome} no alvo {self.nome_exibicao(alvo_jogador)}, mas ERROU!"
                    self.iniciar_cooldown_feedback(75, self.avancar_turno)
                else:

                    if alvo_jogador.recuperando or getattr(alvo_jogador, "focado", False):
                        if not self.tem_talento(alvo_jogador, "F2"):
                            dano_inimigo += max(1, int(dano_inimigo * 0.30))

                    # Mitigação por Defesa Passiva e Armadura (Con // 2 + bônus de itens)
                    defesa_passiva = self.calcular_defesa_passiva(alvo_jogador)
                    dano_inimigo = max(1, dano_inimigo - defesa_passiva)

                    if alvo_jogador.bloqueando:
                        dano_reduzido = max(1, int(dano_inimigo * 0.5))
                        if getattr(alvo_jogador, 'god_mode', False):
                            dano_reduzido = 0
                        alvo_jogador.hp -= dano_reduzido
                        alvo_jogador.hp = max(0, alvo_jogador.hp)
                        if dano_reduzido > 0:
                            self.tocar_sfx_dano(volume_relativo=0.75)
                        self.mensagem_log = f"🛡️ DEFESA do alvo {self.nome_exibicao(alvo_jogador)}! {dano_reduzido} dano."
                        self.iniciar_cooldown_feedback(75, self.avancar_turno)
                    else:
                        self.menu_acoes_estado = "esquivando"
                        self.dano_pendente = dano_inimigo
                        self.atacante_nome = nome_inimigo
                        self.alvo_jogador_pendente = alvo_jogador
                        self.alvo_destaque = alvo_jogador
                        self.efeitos_pendentes, self.chance_efeito_pendente = self.obter_efeitos_ataque_inimigo(entidade_atual, hab_usada)
                        velocidade_base = self.velocidade_esquiva(alvo_jogador)

                        self.minigame_esquiva.iniciar(
                            velocidade_base=velocidade_base,
                            dano_pendente=dano_inimigo,
                            alvo=alvo_jogador,
                            atacante_nome=nome_inimigo,
                            efeitos=self.efeitos_pendentes,
                            chance_efeito=self.chance_efeito_pendente,
                            tela=self.tela
                        )
                        self.barras_esquiva = self.minigame_esquiva.barras
                        self.rodada_esquiva = 0
                        self.espera_esquiva = 0
                        self.acertos_esquiva = 0
                        self.acertos_centro_esquiva = 0
                        self.reducao_esquiva = 0.0

                        if critico:
                            self.mensagem_log = f"⚠️ CRÍTICO DE {nome_inimigo}! Alvo {self.nome_exibicao(alvo_jogador)}: PARRY RÁPIDO!"
                        else:
                            self.mensagem_log = f"⚠️ {nome_inimigo} ataca o alvo {self.nome_exibicao(alvo_jogador)}! [ESPAÇO] ou CLIQUE para esquivar!"

        self.clique_anterior = clique_agora

    def _desenhar_sombra_contato(self, entidade, deslocamento_y=0, multiplicador_alfa=1.0):
        if not entidade or (getattr(entidade, 'hp', 0) <= 0 and getattr(entidade, 'timer_fade_derrota', 0) <= 0):
            return
        rect = entidade.rect
        largura_sombra = max(34, int(rect.width * 0.72))
        altura_sombra = 14
        sombra_surf = pygame.Surface((largura_sombra, altura_sombra), pygame.SRCALPHA)
        alfa_sombra = int(115 * max(0.0, min(1.0, multiplicador_alfa)))
        pygame.draw.ellipse(sombra_surf, (0, 0, 0, alfa_sombra), (0, 0, largura_sombra, altura_sombra))
        x_sombra = rect.centerx - (largura_sombra // 2)
        y_sombra = rect.bottom - 7 + int(deslocamento_y)
        self.tela.blit(sombra_surf, (x_sombra, y_sombra))

    def desenhar_barras_status(self, entidade, deslocamento_flutuacao=0, posicao_mouse=None):
        if getattr(entidade, 'is_player', False):
            return

        rect = entidade.rect
        eh_aliado = self.eh_minion(entidade)
        eh_santuario = getattr(entidade, "is_santuario", False)
        classe_tag = f" [{entidade.classe}]" if getattr(entidade, "classe", None) else ""
        if eh_santuario:
            dur_txt = getattr(entidade, "duracao", 4)
            nome_texto = f"⛩ {entidade.nome} [Dur: {dur_txt} | {entidade.golpes_restantes()}/4]"
            cor_nome = (255, 110, 110) if getattr(entidade, "lado", "inimigo") == "inimigo" else (170, 255, 235)
        else:
            nome_texto = f"★ {entidade.nome[:16]}" if eh_aliado else f"{entidade.nome[:22]}{classe_tag}"
            if getattr(entidade, "congelado", False):
                nome_texto = f"❄ {nome_texto}"
            if getattr(entidade, "atordoado", False):
                nome_texto = f"💫 {nome_texto}"
            cor_nome = (170, 255, 235) if eh_aliado else ((255, 215, 90) if getattr(entidade, "tipo", "") == "chefe" else (240, 240, 240))
        txt_nome = self.fonte_inimigo.render(nome_texto, True, cor_nome)

        largura_placa = max(95, rect.width + 12, txt_nome.get_width() + 16)
        altura_placa = 28 if getattr(entidade, 'max_mp', 0) > 0 else 20
        x_placa = rect.centerx - (largura_placa // 2)
        y_placa = rect.top - altura_placa - 14 + int(deslocamento_flutuacao)

        fundo_placa = pygame.Surface((largura_placa, altura_placa), pygame.SRCALPHA)
        cor_borda = (235, 60, 60, 230) if eh_santuario else ((52, 210, 180, 230) if eh_aliado else ((255, 215, 90, 230) if getattr(entidade, "tipo", "") == "chefe" else (70, 80, 105, 220)))
        pygame.draw.rect(fundo_placa, (16, 22, 30, 205), (0, 0, largura_placa, altura_placa), border_radius=6)
        pygame.draw.rect(fundo_placa, cor_borda, (0, 0, largura_placa, altura_placa), width=1, border_radius=6)
        self.tela.blit(fundo_placa, (x_placa, y_placa))
        self.tela.blit(txt_nome, (x_placa + (largura_placa - txt_nome.get_width()) // 2, y_placa + 2))

        bar_w = largura_placa - 12
        bar_h = 5
        x_bar = x_placa + 6
        y_bar = y_placa + 16
        pygame.draw.rect(self.tela, (70, 15, 20), (x_bar, y_bar, bar_w, bar_h), border_radius=2)
        if getattr(entidade, 'max_hp', 0) > 0:
            porc_hp = max(0.0, min(1.0, entidade.hp / entidade.max_hp))
            if eh_santuario:
                cor_hp = (225, 45, 45) if porc_hp > 0.35 else (255, 130, 40)
            elif eh_aliado:
                cor_hp = (52, 225, 185) if porc_hp > 0.35 else (235, 165, 50)
            else:
                cor_hp = (45, 215, 85) if porc_hp > 0.35 else (230, 70, 50)
            pygame.draw.rect(self.tela, cor_hp, (x_bar, y_bar, int(bar_w * porc_hp), bar_h), border_radius=2)

        if getattr(entidade, 'max_mp', 0) > 0:
            y_mp = y_bar + bar_h + 2
            pygame.draw.rect(self.tela, (15, 25, 60), (x_bar, y_mp, bar_w, 3), border_radius=1)
            porc_mp = max(0.0, min(1.0, entidade.mp / entidade.max_mp))
            pygame.draw.rect(self.tela, (40, 160, 255), (x_bar, y_mp, int(bar_w * porc_mp), 3), border_radius=1)

        # Ícones discretos de De_Buffs logo acima da placa de vida
        y_icones = y_placa - 20
        hovered_ent = desenhar_icones_entidade(
            self.tela,
            entidade,
            x=rect.centerx,
            y=y_icones,
            tamanho=18,
            espacamento=4,
            posicao_mouse=posicao_mouse,
            alinhamento="centro"
        )
        if hovered_ent:
            self.efeito_hovered_ativo = hovered_ent

    def desenhar(self, posicao_mouse=None):
        if posicao_mouse is None:
            posicao_mouse = pygame.mouse.get_pos()
        tamanho_tela = self.tela.get_size()
        if self.fundo_luta is not None:
            if self.fundo_luta_redimensionado is None or self.fundo_luta_tamanho != tamanho_tela:
                self.fundo_luta_redimensionado = pygame.transform.scale(self.fundo_luta, tamanho_tela)
                self.fundo_luta_tamanho = tamanho_tela
            self.tela.blit(self.fundo_luta_redimensionado, (0, 0))
        else:
            self.tela.fill((20, 20, 20))

        entidades_para_desenhar = [
            e for e in self.ordem_turnos
            if getattr(e, 'hp', 0) > 0 or getattr(e, 'timer_fade_derrota', 0) > 0
        ]
        for entidade in entidades_para_desenhar:
            alfa_sombra = 1.0
            if getattr(entidade, 'hp', 0) <= 0:
                alfa_sombra = max(0.0, getattr(entidade, 'timer_fade_derrota', 0) / float(getattr(entidade, 'max_fade_derrota', 35)))
            if alfa_sombra > 0:
                self._desenhar_sombra_contato(entidade, multiplicador_alfa=alfa_sombra)

        entidades_ordenadas = sorted(entidades_para_desenhar, key=lambda e: e.rect.bottom)
        for idx, entidade in enumerate(entidades_ordenadas):
            fase = idx * 1.3
            bob = (math.sin(self.tempo_animacao * 3.0 + fase) * 2.2) if getattr(entidade, 'hp', 0) > 0 else 0
            rect_original = entidade.rect.copy()
            entidade.rect.y += int(bob)

            if getattr(entidade, 'is_player', False):
                entidade.desenhar(self.tela)
                if getattr(entidade, 'hp', 0) > 0:
                    hovered_arena = desenhar_icones_entidade(
                        self.tela,
                        entidade,
                        x=entidade.rect.centerx,
                        y=entidade.rect.top - 22 + int(bob),
                        tamanho=18,
                        espacamento=4,
                        posicao_mouse=posicao_mouse,
                        alinhamento="centro"
                    )
                    if hovered_arena:
                        self.efeito_hovered_ativo = hovered_arena
            else:
                if hasattr(entidade, 'desenhar'):
                    try:
                        entidade.desenhar(self.tela, desenhar_nome=False)
                    except TypeError:
                        entidade.desenhar(self.tela)

            if getattr(entidade, 'hp', 0) > 0:
                self.desenhar_barras_status(entidade, deslocamento_flutuacao=bob, posicao_mouse=posicao_mouse)
            entidade.rect = rect_original

        # Renderização da Spike se estiver no campo
        if getattr(self, "spike", None) is not None:
            self.spike.desenhar(self.tela, self.tempo_animacao)

        # Renderização contínua e otimizada dos cortes saindo do Santuário (Cortes Spam.png)
        if getattr(self, 'particulas_cortes_santuario', None):
            for p in self.particulas_cortes_santuario:
                surf = p.get("surf")
                if surf:
                    pos_x = int(p["x"] - surf.get_width() // 2)
                    pos_y = int(p["y"] - surf.get_height() // 2)
                    self.tela.blit(surf, (pos_x, pos_y), special_flags=pygame.BLEND_ADD)

        indice_seguro = self.indice_turno if self.indice_turno < len(self.ordem_turnos) else 0
        turno_ativo = self.ordem_turnos[indice_seguro] if self.ordem_turnos else None
        if turno_ativo is not None and getattr(turno_ativo, 'is_player', False) and turno_ativo.hp > 0:
            indicador_y = turno_ativo.rect.top - 24 + int(math.sin(self.tempo_animacao * 5.0) * 3)
            txt_indicador = "▲ SEU TURNO ▲" if turno_ativo == personagem else "▲ TURNO J2 ▲"
            seta_surf = self.fonte_inimigo.render(txt_indicador, True, (255, 220, 90))
            self.tela.blit(seta_surf, (turno_ativo.rect.centerx - seta_surf.get_width() // 2, indicador_y))

        alvos_com_contorno = []
        if self.menu_acoes_estado in ("selecionar_alvo", "selecionar_alvo_comando_atingir"):
            inimigos = [entidade for entidade in self.ordem_turnos if self.eh_inimigo(entidade) and entidade.hp > 0]
            for alvo in inimigos:
                if alvo.rect.collidepoint(posicao_mouse):
                    alvos_com_contorno.append(alvo)
                    break
        elif self.menu_acoes_estado in ("selecionar_minion_comando_defender", "selecionar_minion_comando_descansar"):
            minions = self.obter_minions_vivos()
            for alvo in minions:
                if alvo.rect.inflate(16, 16).collidepoint(posicao_mouse):
                    alvos_com_contorno.append(alvo)
                    break
        elif getattr(self, "alvo_destaque", None) is not None:
            if isinstance(self.alvo_destaque, list):
                alvos_com_contorno.extend([a for a in self.alvo_destaque if getattr(a, "hp", 0) > 0])
            elif getattr(self.alvo_destaque, "hp", 0) > 0:
                alvos_com_contorno.append(self.alvo_destaque)

        pulso = int(math.sin(self.tempo_animacao * 6.0) * 3)
        for alvo in alvos_com_contorno:
            nome_alvo_txt = self.nome_exibicao(alvo)
            eh_minion_alvo = self.eh_minion(alvo)
            if eh_minion_alvo and self.menu_acoes_estado == "selecionar_minion_comando_defender":
                c_cor = (35, 95, 145)
                c_cor_brilho = (60, 165, 235)
                txt_alvo = self.fonte_inimigo.render(f"▼ DEFENDER: {nome_alvo_txt.upper()} ▼", True, c_cor_brilho)
            elif eh_minion_alvo and self.menu_acoes_estado == "selecionar_minion_comando_descansar":
                c_cor = (35, 130, 95)
                c_cor_brilho = (60, 210, 155)
                txt_alvo = self.fonte_inimigo.render(f"▼ DESCANSAR: {nome_alvo_txt.upper()} ▼", True, c_cor_brilho)
            else:
                c_cor = (240, 35, 35)
                c_cor_brilho = (255, 95, 95)
                txt_alvo = self.fonte_inimigo.render(f"▼ ALVO: {nome_alvo_txt.upper()} ▼", True, c_cor_brilho)
            self.tela.blit(txt_alvo, (alvo.rect.centerx - txt_alvo.get_width() // 2, alvo.rect.top - 46 + pulso))

            r = alvo.rect.inflate(12 + pulso, 12 + pulso)
            c_tam = 16
            w_ln = 3
            # Contorno retangular completo
            pygame.draw.rect(self.tela, c_cor, r, width=3, border_radius=6)
            # Cantos destacados
            pygame.draw.line(self.tela, c_cor_brilho, (r.left, r.top), (r.left + c_tam, r.top), w_ln + 1)
            pygame.draw.line(self.tela, c_cor_brilho, (r.left, r.top), (r.left, r.top + c_tam), w_ln + 1)
            pygame.draw.line(self.tela, c_cor_brilho, (r.right, r.top), (r.right - c_tam, r.top), w_ln + 1)
            pygame.draw.line(self.tela, c_cor_brilho, (r.right, r.top), (r.right, r.top + c_tam), w_ln + 1)
            pygame.draw.line(self.tela, c_cor_brilho, (r.left, r.bottom), (r.left + c_tam, r.bottom), w_ln + 1)
            pygame.draw.line(self.tela, c_cor_brilho, (r.left, r.bottom), (r.left - c_tam, r.bottom), w_ln + 1)
            pygame.draw.line(self.tela, c_cor_brilho, (r.right, r.bottom), (r.right - c_tam, r.bottom), w_ln + 1)
            pygame.draw.line(self.tela, c_cor_brilho, (r.right, r.bottom), (r.right, r.bottom - c_tam), w_ln + 1)
        if self.menu_acoes_estado == "minigame_ataque" and getattr(self, "minigame_ataque", None) and self.minigame_ataque.esta_ativo():
            self.minigame_ataque.desenhar(self.tela)

        if self.menu_acoes_estado == "esquivando":
            if getattr(self, "minigame_esquiva", None) and self.minigame_esquiva.esta_ativo():
                self.minigame_esquiva.desenhar(self.tela)
            else:
                painel_w = 460
                painel_h = 56
                painel_x = (self.tela.get_width() - painel_w) // 2
                painel_y = 250
                painel_surf = pygame.Surface((painel_w, painel_h), pygame.SRCALPHA)
                pygame.draw.rect(painel_surf, (15, 18, 28, 220), (0, 0, painel_w, painel_h), border_radius=10)
                pygame.draw.rect(painel_surf, (255, 215, 80, 200), (0, 0, painel_w, painel_h), width=2, border_radius=10)
                self.tela.blit(painel_surf, (painel_x, painel_y))

                bar_w = 400
                bar_h = 24
                bar_x = (self.tela.get_width() - bar_w) // 2
                bar_y = painel_y + (painel_h - bar_h) // 2

                pygame.draw.rect(self.tela, (40, 42, 52), (bar_x, bar_y, bar_w, bar_h), border_radius=5)
                pygame.draw.rect(self.tela, (210, 180, 30), (bar_x + 120, bar_y, 160, bar_h))
                pygame.draw.rect(self.tela, (30, 220, 90), (bar_x + 180, bar_y, 40, bar_h))
                pygame.draw.rect(self.tela, (240, 240, 240), (bar_x, bar_y, bar_w, bar_h), width=2, border_radius=5)

                for barra in self.barras_esquiva:
                    if not barra["ativa"] or barra["x"] < 0:
                        continue
                    bx = bar_x + barra["x"] - 4
                    if bar_x <= bx <= bar_x + bar_w:
                        pygame.draw.rect(self.tela, (255, 60, 60), (bx, bar_y - 6, 8, bar_h + 12), border_radius=2)

        contador_partida = pygame.Rect(30, 25, 175, 42)
        pygame.draw.rect(self.tela, (24, 26, 36), contador_partida, border_radius=10)
        pygame.draw.rect(self.tela, (255, 210, 90), contador_partida, width=2, border_radius=10)
        texto_partida = self.fonte_titulos.render(f"PARTIDA {self.partida_atual}/{self.total_partidas}", True, (255, 255, 255))
        self.tela.blit(texto_partida, (contador_partida.x + 14, contador_partida.y + 11))
        self.btn_pausa.desenhar(self.tela)

        hud_log = pygame.Rect((self.tela.get_width() - 620) // 2, 20, 620, 70)
        pygame.draw.rect(self.tela, (22, 25, 36), hud_log, border_radius=10)
        cor_borda = (255, 210, 90) if getattr(self, 'cooldown_feedback', 0) > 0 else (110, 115, 140)
        pygame.draw.rect(self.tela, cor_borda, hud_log, width=2, border_radius=10)
        padding = 12
        linhas = quebrar_texto(self.mensagem_log, self.fonte, hud_log.width - padding*2)
        total_altura = len(linhas) * self.fonte.get_linesize()
        y_inicio = hud_log.y + (hud_log.height - total_altura) // 2
        for indice_linha, linha in enumerate(linhas):
            surf = self.fonte.render(linha, True, (255, 255, 255))
            x = hud_log.x + (hud_log.width - surf.get_width()) // 2
            y = y_inicio + indice_linha * self.fonte.get_linesize()
            self.tela.blit(surf, (x, y))

        if getattr(self, 'cooldown_feedback', 0) > 0 and getattr(self, 'tempo_cooldown_maximo', 0) > 0:
            progresso = min(1.0, max(0.0, self.cooldown_feedback / float(self.tempo_cooldown_maximo)))
            largura_barra = int((hud_log.width - 16) * progresso)
            barra_rect = pygame.Rect(hud_log.x + 8, hud_log.bottom - 6, largura_barra, 3)
            pygame.draw.rect(self.tela, (255, 215, 90), barra_rect, border_radius=2)

        hud_acoes = self.obter_rect_hud_acoes()
        pygame.draw.rect(self.tela, (20, 22, 32), hud_acoes, border_radius=12)
        pygame.draw.rect(self.tela, (85, 95, 120), hud_acoes, width=2, border_radius=12)
        titulos_menu = {
            "principal": "AÇÕES",
            "agir": "AGIR",
            "ataques": "HABILIDADES",
            "minions": "MINIONS",
            "comandos": "COMANDOS",
            "itens": "ITENS",
            "selecionar_alvo": "SELECIONAR ALVO",
            "selecionar_alvo_comando_atingir": "ORDEM: ATINGIR",
            "selecionar_minion_comando_defender": "ORDEM: DEFENDER",
            "selecionar_minion_comando_descansar": "ORDEM: DESCANSAR",
        }
        titulo_hud = titulos_menu.get(self.menu_acoes_estado, "AÇÕES")
        self.tela.blit(self.fonte_titulos.render(titulo_hud, True, (180, 190, 215)), (hud_acoes.x + 16, hud_acoes.y + 8))
        jogadores_status = [personagem]
        if getattr(self, 'duas_pessoas', False) and getattr(self, 'personagem2', None) is not None:
            jogadores_status.append(self.personagem2)

        largura_cartao = 290
        espaco_cartao = 20
        largura_total_cards = len(jogadores_status) * largura_cartao + (len(jogadores_status) - 1) * espaco_cartao
        x_base_status = (self.tela.get_width() - largura_total_cards) // 2
        y_base_status = 716

        for indice, jogador in enumerate(jogadores_status):
            x_cartao = x_base_status + indice * (largura_cartao + espaco_cartao)
            rect_status = pygame.Rect(x_cartao, y_base_status, largura_cartao, 68)

            pygame.draw.rect(self.tela, (22, 24, 34), rect_status, border_radius=10)

            eh_morto = getattr(jogador, 'hp', 0) <= 0
            eh_turno = (turno_ativo == jogador) and not eh_morto
            if eh_morto:
                cor_borda = (140, 50, 50)
                espessura_borda = 2
            elif eh_turno:
                cor_borda = (255, 210, 80)
                espessura_borda = 3
            else:
                cor_borda = (75, 80, 100)
                espessura_borda = 2
            pygame.draw.rect(self.tela, cor_borda, rect_status, width=espessura_borda, border_radius=10)

            nome_jogador = "JOGADOR 1" if jogador == personagem else "JOGADOR 2"
            if eh_morto:
                nome_jogador += " [DERROTADO]"
            else:
                efeito_controle = self.obter_efeito_controle(jogador)
                if efeito_controle == "Congelar":
                    nome_jogador += " ❄"
                elif efeito_controle == "Atordoar":
                    nome_jogador += " 💫"
            cor_nome = (180, 70, 70) if eh_morto else ((255, 230, 120) if eh_turno else (230, 230, 240))
            self.tela.blit(self.fonte_status.render(nome_jogador, True, cor_nome), (rect_status.x + 12, rect_status.y + 6))

            minions_j = self.obter_minions_vivos(jogador)
            classe_dano_j = self.tipo_classe_do_jogador(jogador)
            if minions_j or classe_dano_j == "Invocador":
                txt_minions = self.fonte_status.render(f"MINIONS {len(minions_j)}/{self.limite_minions(jogador)}", True, (80, 235, 195))
                self.tela.blit(txt_minions, (rect_status.right - txt_minions.get_width() - 12, rect_status.y + 6))

            # Ícone de Vida (HP) e Barra de HP
            icone_vida = carregar_icone_efeito("Vida.png", 16)
            x_icone = rect_status.x + 10
            y_hp = rect_status.y + 28
            self.tela.blit(icone_vida, (x_icone, y_hp - 1))

            x_hp = rect_status.x + 30
            w_bar = 136
            h_bar = 13
            pygame.draw.rect(self.tela, (65, 14, 18), (x_hp, y_hp, w_bar, h_bar), border_radius=3)
            if jogador.max_hp > 0:
                porc_hp = max(0.0, min(1.0, jogador.hp / jogador.max_hp))
                pygame.draw.rect(self.tela, (40, 210, 80), (x_hp, y_hp, int(w_bar * porc_hp), h_bar), border_radius=3)
            txt_hp = self.fonte_status.render(f"HP {jogador.hp}/{jogador.max_hp}", True, (255, 255, 255))
            self.tela.blit(txt_hp, (x_hp + w_bar + 8, y_hp - 1))

            # Ícone de Mana/Foco e Barra de PM
            # Caso o jogador não possua a skill tree do feiticeiro que anula os debuffs do foco (F2), troca para Foco.png
            icone_recurso, _ = obter_icone_recurso_entidade(jogador, 16)
            y_mp = rect_status.y + 46
            self.tela.blit(icone_recurso, (x_icone, y_mp - 1))

            pygame.draw.rect(self.tela, (14, 22, 60), (x_hp, y_mp, w_bar, h_bar), border_radius=3)
            if jogador.max_mp > 0:
                porc_mp = max(0.0, min(1.0, jogador.mp / jogador.max_mp))
                pygame.draw.rect(self.tela, (30, 150, 255), (x_hp, y_mp, int(w_bar * porc_mp), h_bar), border_radius=3)
            txt_mp = self.fonte_status.render(f"PM {jogador.mp}/{jogador.max_mp}", True, (255, 255, 255))
            self.tela.blit(txt_mp, (x_hp + w_bar + 8, y_mp - 1))

            # Tooltip interativa nos ícones de Vida e Mana/Foco
            if posicao_mouse:
                mx, my = posicao_mouse
                if pygame.Rect(x_icone, y_hp - 1, 16, 16).collidepoint(mx, my):
                    self.efeito_hovered_ativo = {
                        "nome": "Vida (HP)",
                        "tag": "RECURSO",
                        "cor": (40, 210, 80),
                        "arquivo": "Vida.png",
                        "descricao": f"Vitalidade do jogador: {jogador.hp}/{jogador.max_hp} pontos de vida.",
                    }
                elif pygame.Rect(x_icone, y_mp - 1, 16, 16).collidepoint(mx, my):
                    if entidade_anula_debuff_foco(jogador):
                        self.efeito_hovered_ativo = {
                            "nome": "Mana (PM)",
                            "tag": "RECURSO",
                            "cor": (30, 150, 255),
                            "arquivo": "Mana.png",
                            "descricao": f"Pontos de Mana: {jogador.mp}/{jogador.max_mp}. Domínio Simples ativo (anula vulnerabilidade de foco).",
                        }
                    else:
                        self.efeito_hovered_ativo = {
                            "nome": "Foco (PM)",
                            "tag": "FOCO",
                            "cor": (255, 140, 40),
                            "arquivo": "Foco.png",
                            "descricao": f"Pontos de Mana: {jogador.mp}/{jogador.max_mp}. Sem Domínio Simples: sofre +30% de dano durante o foco.",
                        }

            # Ícones discretos de De_Buffs na placa do jogador ao lado da barra de HP
            hovered_j = desenhar_icones_entidade(
                self.tela,
                jogador,
                x=rect_status.right - 10,
                y=y_hp - 3,
                tamanho=18,
                espacamento=4,
                posicao_mouse=posicao_mouse,
                alinhamento="direita"
            )
            if hovered_j:
                self.efeito_hovered_ativo = hovered_j

        if turno_ativo is not None and getattr(turno_ativo, 'hp', 0) > 0 and turno_ativo in (personagem, getattr(self, 'personagem2', None)) and not self.obter_efeito_controle(turno_ativo):
            desenhadores_menu = {
                "principal": self._desenhar_menu_principal,
                "agir": self._desenhar_menu_agir,
                "ataques": self._desenhar_menu_ataques,
                "minions": self._desenhar_menu_minions,
                "comandos": self._desenhar_menu_comandos,
                "itens": self._desenhar_menu_itens,
                "selecionar_alvo": self._desenhar_menu_selecionar_alvo,
                "selecionar_alvo_comando_atingir": self._desenhar_menu_selecionar_alvo,
                "selecionar_minion_comando_defender": self._desenhar_menu_selecionar_alvo,
                "selecionar_minion_comando_descansar": self._desenhar_menu_selecionar_alvo,
            }
            if desenhador := desenhadores_menu.get(self.menu_acoes_estado):
                desenhador()

        # Renderização da tempestade de cortes (Cortes.png)
        if self.animacao_cortes_duracao > 0:
            self.animacao_cortes_duracao -= 1
            if self.surf_cortes is not None:
                c_offset_x = random.randint(-18, 18)
                c_offset_y = random.randint(-18, 18)
                self.tela.blit(self.surf_cortes, (self.pos_cortes_x + c_offset_x, self.pos_cortes_y + c_offset_y), special_flags=pygame.BLEND_ADD)

        # Renderização visual dos cortes nos alvos atingidos (corte_vfx.png)
        if getattr(self, "img_vfx_corte", None) is not None and getattr(self, "animacoes_vfx_cortes", None):
            for a in self.animacoes_vfx_cortes:
                progresso = a["duracao"] / float(max(1, a.get("duracao_max", 14)))
                largura_vfx = int(220 * (1.2 - 0.2 * progresso))
                altura_vfx = int(140 * (1.2 - 0.2 * progresso))
                surf_vfx = pygame.transform.scale(self.img_vfx_corte, (largura_vfx, altura_vfx))
                if a.get("flip", False):
                    surf_vfx = pygame.transform.flip(surf_vfx, True, False)
                if a.get("rotacao", 0) != 0:
                    surf_vfx = pygame.transform.rotate(surf_vfx, a["rotacao"])
                vx = int(a["x"] - surf_vfx.get_width() // 2)
                vy = int(a["y"] - surf_vfx.get_height() // 2)
                self.tela.blit(surf_vfx, (vx, vy), special_flags=pygame.BLEND_ADD)

        # Renderização do minigame de desarme da Spike (Bullet Hell + Esfera)
        if self.menu_acoes_estado == "desarmando_spike":
            self._desenhar_minigame_spike(posicao_mouse)

        # Renderização da explosão colossal da Spike (esfera preta com efeitos brancos)
        if getattr(self, "spike_detonando", False) or (getattr(self, "spike", None) and getattr(self.spike, "detonada", False)):
            self._desenhar_detonacao_spike()

        # Efeito de tremor de tela (Screen Shake)
        if self.shake_duracao > 0:
            self.shake_duracao -= 1
            shake_x = random.randint(-self.shake_intensidade, self.shake_intensidade)
            shake_y = random.randint(-self.shake_intensidade, self.shake_intensidade)
            if shake_x != 0 or shake_y != 0:
                surf_shake = self.tela.copy()
                self.tela.fill((16, 10, 14))
                self.tela.blit(surf_shake, (shake_x, shake_y))

        # Renderização da tooltip do efeito hovered (no topo de todas as camadas)
        if getattr(self, "efeito_hovered_ativo", None):
            self.ultimo_efeito_hovered = self.efeito_hovered_ativo
            desenhar_tooltip_efeito(self.tela, self.efeito_hovered_ativo, posicao_mouse)
            self.efeito_hovered_ativo = None
        else:
            self.ultimo_efeito_hovered = None

    def _desenhar_menu_principal(self):
        self.btn_agir.desenhar(self.tela)
        self.btn_foco.desenhar(self.tela)
        self.btn_item.desenhar(self.tela)
        if getattr(self, "spike", None) is not None and self.spike.ativa and not self.spike.desarmada:
            self.btn_desarmar_spike.desenhar(self.tela)
        else:
            self.btn_fugir.desenhar(self.tela)

    def _desenhar_menu_agir(self):
        self.btn_agir_atacar.desenhar(self.tela)
        self.btn_agir_bloquear.desenhar(self.tela)
        self.btn_agir_voltar.desenhar(self.tela)

    def _desenhar_menu_itens(self):
        for item_info in self.botoes_itens_dinamicos:
            item_info["botao"].desenhar(self.tela)
        self.btn_voltar_itens.desenhar(self.tela)

    def _desenhar_menu_ataques(self):
        for item_habilidade in self.botoes_habilidades_dinamicos:
            item_habilidade["botao"].desenhar(self.tela)
        self.btn_voltar.desenhar(self.tela)

    def _desenhar_menu_minions(self):
        for item_minion in self.botoes_minions_dinamicos:
            item_minion["botao"].desenhar(self.tela)
        self.btn_voltar_minions.desenhar(self.tela)

    def _desenhar_menu_comandos(self):
        self.btn_cmd_atingir.desenhar(self.tela)
        self.btn_cmd_defender.desenhar(self.tela)
        self.btn_cmd_descansar.desenhar(self.tela)
        self.btn_cmd_voltar.desenhar(self.tela)

    def _desenhar_menu_selecionar_alvo(self):
        self.btn_voltar.desenhar(self.tela)

    def executar_foco(self, jogador_atual=None):
        """
        Executa a ação Foco para o jogador:
        Recupera PM (com bônus de F1 e F2), cura HP se tiver F3, ativa o estado Foco
        e exibe o log de retorno atualizado.
        """
        if getattr(self, "snd_foco", None):
            try:
                from Sistemas.Configuracoes import sistema_config
                self.snd_foco.set_volume(sistema_config.obter_volume_sfx_efetivo())
                self.snd_foco.play()
            except Exception:
                pass
        if jogador_atual is None:
            jogador_atual = self.jogadores[self.indice_jogador_ativo] if hasattr(self, "jogadores") and self.jogadores else personagem
        pm_rec = 2 if self.tem_talento(jogador_atual, "F1") else 1
        if self.tem_talento(jogador_atual, "F2"):
            pm_rec += 2
        jogador_atual.mp = min(jogador_atual.max_mp, jogador_atual.mp + pm_rec)
        jogador_atual.recuperando = True
        jogador_atual.focado = True

        hp_rec = 0
        if self.tem_talento(jogador_atual, "F3"):
            hp_rec = max(1, int(jogador_atual.max_hp * 0.10))
            jogador_atual.hp = min(jogador_atual.max_hp, jogador_atual.hp + hp_rec)

        txt_hp = f" e +{hp_rec} HP" if hp_rec > 0 else ""
        if self.tem_talento(jogador_atual, "F2"):
            txt_dano = "sem penalidade de dano (F2)!"
        else:
            txt_dano = "mas sofrerá +30% dano!"
        self.mensagem_log = f"🧘 FOCO: +{pm_rec} PM{txt_hp}, {txt_dano}"
        self.iniciar_cooldown_feedback(50, self.avancar_turno)
        return {"pm": pm_rec, "hp": hp_rec}

    def focar(self, jogador_atual=None):
        return self.executar_foco(jogador_atual)

    def recuperar(self, jogador_atual=None):
        return self.executar_foco(jogador_atual)

    def _processar_menu_principal(self, jogador_atual, posicao_mouse, estado_clique_mouse, clicou):
        nome_turno = "Seu Turno!" if jogador_atual == personagem else "Turno do Jogador 2!"
        if (
            "usou" not in self.mensagem_log
            and "invocou" not in self.mensagem_log
            and "ERROU" not in self.mensagem_log
            and "falhou" not in self.mensagem_log.lower()
            and "CRÍTICO" not in self.mensagem_log
            and "rápido" not in self.mensagem_log
            and "⚑" not in self.mensagem_log
            and "🎲" not in self.mensagem_log
            and "👑" not in self.mensagem_log
        ):
            self.mensagem_log = nome_turno

        self.btn_agir.atualizar(posicao_mouse, estado_clique_mouse)
        self.btn_foco.atualizar(posicao_mouse, estado_clique_mouse)
        self.btn_item.atualizar(posicao_mouse, estado_clique_mouse)

        spike_ativa = (getattr(self, "spike", None) is not None and self.spike.ativa and not self.spike.desarmada)
        if spike_ativa:
            self.btn_desarmar_spike.atualizar(posicao_mouse, estado_clique_mouse)
        else:
            self.btn_fugir.atualizar(posicao_mouse, estado_clique_mouse)

        if not clicou:
            return None

        # Clique no botão DESARMAR ou diretamente na Spike sobre a arena
        if spike_ativa:
            if self.btn_desarmar_spike.clicado(posicao_mouse) or (self.spike and self.spike.rect.collidepoint(posicao_mouse)):
                self.iniciar_minigame_desarme_spike()
                return None

        if self.btn_agir.clicado(posicao_mouse):
            self.menu_acoes_estado = "agir"
        elif self.btn_foco.clicado(posicao_mouse) or self.btn_recuperar.clicado(posicao_mouse):
            self.executar_foco(jogador_atual)
        elif self.btn_item.clicado(posicao_mouse):
            self.menu_acoes_estado = "itens"
            self.gerar_botoes_itens(jogador_atual)
            if not self.obter_itens_consumiveis_combate():
                self.mensagem_log = "Nenhum item consumível no inventário!"
        elif self.btn_fugir.clicado(posicao_mouse):
            chance_fuga = 1.0 if self.tem_talento(jogador_atual, "S1") else 0.50
            if random.random() < chance_fuga:
                from Sistemas.Conquistas import sistema_conquistas
                sistema_conquistas.desbloquear("fuga_estrategica")
                self.pontos_jogo = 0
                self.partida_atual = min(self.total_partidas, self.partida_atual + 1)
                cura_info = self.recuperar_apos_batalha(dormir=False)
                self.ultimo_resultado_batalha = {
                    "cura": cura_info,
                    "itens": [],
                    "xp": 0,
                    "mensagem": "Fuga bem-sucedida! Você saiu do combate sem ganhar pontos."
                }
                return "fugiu"
            else:
                self.mensagem_log = "❌ FUGA falhou!"
                self.iniciar_cooldown_feedback(50, self.avancar_turno)
        return None

    def _processar_menu_agir(self, jogador_atual, posicao_mouse, estado_clique_mouse, clicou):
        self.btn_agir_atacar.atualizar(posicao_mouse, estado_clique_mouse)
        self.btn_agir_bloquear.atualizar(posicao_mouse, estado_clique_mouse)
        self.btn_agir_voltar.atualizar(posicao_mouse, estado_clique_mouse)

        if not clicou:
            return None

        if self.btn_agir_voltar.clicado(posicao_mouse):
            self.menu_acoes_estado = "principal"
            return None

        if self.btn_agir_atacar.clicado(posicao_mouse):
            self.gerar_botoes_ataque(jogador_atual)
            self.menu_acoes_estado = "ataques"
        elif self.btn_agir_bloquear.clicado(posicao_mouse):
            jogador_atual.bloqueando = True
            self.mensagem_log = "🛡️ BLOQUEAR: Dano reduzido em 50%!"
            self.iniciar_cooldown_feedback(45, self.avancar_turno)
            self.menu_acoes_estado = "principal"
        return None

    def _processar_menu_itens(self, jogador_atual, posicao_mouse, estado_clique_mouse, clicou):
        self.btn_voltar_itens.atualizar(posicao_mouse, estado_clique_mouse)
        for item_info in self.botoes_itens_dinamicos:
            item_info["botao"].atualizar(posicao_mouse, estado_clique_mouse)

        if not clicou:
            return None

        if self.btn_voltar_itens.clicado(posicao_mouse):
            self.menu_acoes_estado = "principal"
            return None

        for item_info in self.botoes_itens_dinamicos:
            if item_info["botao"].clicado(posicao_mouse):
                item = item_info["item"]
                self.usar_item_combate(item, jogador_atual)
                break
        return None

    def _processar_menu_ataques(self, jogador_atual, posicao_mouse, estado_clique_mouse, clicou):
        self.btn_voltar.atualizar(posicao_mouse, estado_clique_mouse)
        for item_habilidade in self.botoes_habilidades_dinamicos:
            item_habilidade["botao"].atualizar(posicao_mouse, estado_clique_mouse)

        if not clicou:
            return None

        if self.btn_voltar.clicado(posicao_mouse):
            self.menu_acoes_estado = "agir"
            return None

        for item_habilidade in self.botoes_habilidades_dinamicos:
            if item_habilidade["botao"].clicado(posicao_mouse):
                if item_habilidade.get("tipo") == "minions":
                    self.gerar_botoes_minions(jogador_atual)
                    self.menu_acoes_estado = "minions"
                    return None
                elif item_habilidade.get("tipo") == "comandos":
                    self.menu_acoes_estado = "comandos"
                    return None

                hab = banco_habilidades.get(item_habilidade["nome"])
                if not hab:
                    continue
                if getattr(hab, "minion", None) or hab.tipo == "Invocador":
                    limite = self.limite_minions(jogador_atual)
                    if len(self.obter_minions_vivos(jogador_atual)) >= limite:
                        self.mensagem_log = f"⚠️ Limite de summons atingido ({limite}/{limite})!"
                        self.iniciar_cooldown_feedback(35)
                        break
                custo_mp = self._custo_habilidade(hab, jogador_atual)
                if jogador_atual.mp >= custo_mp:
                    self.ataque_selecionado = item_habilidade["nome"]
                    self.ataque_jogador_ativo = jogador_atual
                    eh_ultimate = getattr(hab, "is_ultimate", False)
                    if hab.em_area or hab.tipo == "Invocador" or getattr(hab, "minion", None):
                        if getattr(self, "minigames_ataque_ativos", True) and not eh_ultimate:
                            self.iniciar_minigame_ataque(hab, alvo=None, jogador_ativo=jogador_atual)
                        else:
                            self.executar_ataque_jogador(item_habilidade["nome"], jogador_ativo=jogador_atual)
                    else:
                        self.menu_acoes_estado = "selecionar_alvo"
                else:
                    self.mensagem_log = f"💧 PM Insuficiente para {hab.nome}!"
                    self.iniciar_cooldown_feedback(35)
                    self.menu_acoes_estado = "agir"
                break
        return None

    def _processar_menu_minions(self, jogador_atual, posicao_mouse, estado_clique_mouse, clicou):
        self.btn_voltar_minions.atualizar(posicao_mouse, estado_clique_mouse)
        for item_minion in self.botoes_minions_dinamicos:
            item_minion["botao"].atualizar(posicao_mouse, estado_clique_mouse)

        if not clicou:
            return None

        if self.btn_voltar_minions.clicado(posicao_mouse):
            self.menu_acoes_estado = "ataques"
            return None

        for item_minion in self.botoes_minions_dinamicos:
            if item_minion["botao"].clicado(posicao_mouse):
                nome_hab = item_minion["nome"]
                hab = item_minion.get("habilidade") or banco_habilidades.get(nome_hab)
                if not hab:
                    continue
                if getattr(hab, "minion", None) or hab.tipo == "Invocador":
                    limite = self.limite_minions(jogador_atual)
                    if len(self.obter_minions_vivos(jogador_atual)) >= limite:
                        self.mensagem_log = f"⚠️ Limite de summons atingido ({limite}/{limite})!"
                        self.iniciar_cooldown_feedback(35)
                        break
                custo_mp = self._custo_habilidade(hab, jogador_atual)
                if jogador_atual.mp >= custo_mp:
                    self.ataque_selecionado = nome_hab
                    self.ataque_jogador_ativo = jogador_atual
                    eh_ultimate = getattr(hab, "is_ultimate", False)
                    if hab.em_area or hab.tipo == "Invocador" or getattr(hab, "minion", None):
                        if getattr(self, "minigames_ataque_ativos", True) and not eh_ultimate:
                            self.iniciar_minigame_ataque(hab, alvo=None, jogador_ativo=jogador_atual)
                        else:
                            self.executar_ataque_jogador(nome_hab, jogador_ativo=jogador_atual)
                    else:
                        self.menu_acoes_estado = "selecionar_alvo"
                else:
                    self.mensagem_log = f"💧 PM Insuficiente para {hab.nome}!"
                    self.iniciar_cooldown_feedback(35)
                    self.menu_acoes_estado = "minions"
                break
        return None

    def _processar_menu_selecionar_alvo(self, jogador_atual, posicao_mouse, estado_clique_mouse, clicou, inimigos_vivos):
        alvo_hover = None
        for a in inimigos_vivos:
            if a.rect.collidepoint(posicao_mouse):
                alvo_hover = a
                break

        if alvo_hover:
            self.mensagem_log = f"🎯 Alvo: {self.nome_exibicao(alvo_hover)} | Clique para atacar com {self.ataque_selecionado.upper()}!"
        else:
            self.mensagem_log = f"🎯 Escolha o alvo para {self.ataque_selecionado.upper()}!"

        self.btn_voltar.atualizar(posicao_mouse, estado_clique_mouse)

        if not clicou:
            return None

        if self.btn_voltar.clicado(posicao_mouse):
            self.alvo_destaque = None
            if self._eh_habilidade_minion(self.ataque_selecionado):
                self.menu_acoes_estado = "minions"
            else:
                self.menu_acoes_estado = "ataques"
        else:
            for alvo in inimigos_vivos:
                if alvo.rect.collidepoint(posicao_mouse):
                    self.alvo_destaque = alvo
                    hab = banco_habilidades.get(self.ataque_selecionado)
                    eh_ultimate = getattr(hab, "is_ultimate", False) if hab else False
                    if getattr(self, "minigames_ataque_ativos", True) and hab and not eh_ultimate:
                        self.iniciar_minigame_ataque(hab, alvo=alvo, jogador_ativo=jogador_atual)
                    else:
                        self.executar_ataque_jogador(self.ataque_selecionado, alvo, jogador_ativo=jogador_atual)
                    break
        return None

    def _processar_menu_comandos(self, jogador_atual, posicao_mouse, estado_clique_mouse, clicou):
        self.btn_cmd_atingir.atualizar(posicao_mouse, estado_clique_mouse)
        self.btn_cmd_defender.atualizar(posicao_mouse, estado_clique_mouse)
        self.btn_cmd_descansar.atualizar(posicao_mouse, estado_clique_mouse)
        self.btn_cmd_voltar.atualizar(posicao_mouse, estado_clique_mouse)

        if not clicou:
            return None

        if self.btn_cmd_voltar.clicado(posicao_mouse):
            self.menu_acoes_estado = "ataques"
            return None

        minions_vivos = self.obter_minions_vivos(jogador_atual)

        if self.btn_cmd_atingir.clicado(posicao_mouse):
            if not minions_vivos:
                self.mensagem_log = "⚠️ Você não possui nenhum summon em campo!"
                self.iniciar_cooldown_feedback(35)
                return None
            self.menu_acoes_estado = "selecionar_alvo_comando_atingir"
            return None

        elif self.btn_cmd_defender.clicado(posicao_mouse):
            if not minions_vivos:
                self.mensagem_log = "⚠️ Você não possui nenhum summon em campo!"
                self.iniciar_cooldown_feedback(35)
                return None
            self.menu_acoes_estado = "selecionar_minion_comando_defender"
            return None

        elif self.btn_cmd_descansar.clicado(posicao_mouse):
            if not minions_vivos:
                self.mensagem_log = "⚠️ Você não possui nenhum summon em campo!"
                self.iniciar_cooldown_feedback(35)
                return None
            self.menu_acoes_estado = "selecionar_minion_comando_descansar"
            return None

        return None

    def _processar_selecao_alvo_atingir(self, jogador_atual, posicao_mouse, estado_clique_mouse, clicou, inimigos_vivos):
        alvo_hover = None
        for a in inimigos_vivos:
            if a.rect.collidepoint(posicao_mouse):
                alvo_hover = a
                break

        if alvo_hover:
            self.mensagem_log = f"🎯 ATINGIR: Focar em {self.nome_exibicao(alvo_hover)}? Clique para ordenar os summons!"
        else:
            self.mensagem_log = "🎯 ATINGIR: Selecione o inimigo que todos os summons focarão!"

        self.btn_voltar.atualizar(posicao_mouse, estado_clique_mouse)
        if not clicou:
            return None

        if self.btn_voltar.clicado(posicao_mouse):
            self.alvo_destaque = None
            self.menu_acoes_estado = "comandos"
            return None

        for alvo in inimigos_vivos:
            if alvo.rect.collidepoint(posicao_mouse):
                self.alvo_destaque = alvo
                self.alvo_prioritario_minions = alvo
                for m in self.obter_minions_vivos(jogador_atual):
                    m.alvo_prioritario = alvo
                    m.defendendo = False
                self.mensagem_log = f"🎯 COMANDO: Todos os summons agora focam em {self.nome_exibicao(alvo)}!"
                self.iniciar_cooldown_feedback(45, self.avancar_turno)
                self.menu_acoes_estado = "principal"
                break
        return None

    def _processar_selecao_minion_defender(self, jogador_atual, posicao_mouse, estado_clique_mouse, clicou):
        minions_vivos = self.obter_minions_vivos(jogador_atual)
        if not minions_vivos:
            self.mensagem_log = "⚠️ Nenhum summon disponível para defender!"
            self.menu_acoes_estado = "comandos"
            return None

        alvo_hover = None
        for m in minions_vivos:
            if m.rect.inflate(16, 16).collidepoint(posicao_mouse):
                alvo_hover = m
                break

        if alvo_hover:
            self.mensagem_log = f"🛡️ DEFENDER: Ordenar que {alvo_hover.nome} defenda a equipe? Clique para confirmar!"
        else:
            self.mensagem_log = "🛡️ DEFENDER: Clique no summon alvo para defender a equipe!"

        self.btn_voltar.atualizar(posicao_mouse, estado_clique_mouse)
        if not clicou:
            return None

        if self.btn_voltar.clicado(posicao_mouse):
            self.alvo_destaque = None
            self.menu_acoes_estado = "comandos"
            return None

        for m in minions_vivos:
            if m.rect.inflate(16, 16).collidepoint(posicao_mouse):
                self.alvo_destaque = m
                m.defendendo = True
                m.dormindo = False
                self.mensagem_log = f"🛡️ COMANDO: {m.nome} defenderá a equipe e chamará a atenção dos inimigos!"
                self.iniciar_cooldown_feedback(45, self.avancar_turno)
                self.menu_acoes_estado = "principal"
                break
        return None

    def _processar_selecao_minion_descansar(self, jogador_atual, posicao_mouse, estado_clique_mouse, clicou):
        minions_vivos = self.obter_minions_vivos(jogador_atual)
        if not minions_vivos:
            self.mensagem_log = "⚠️ Nenhum summon disponível para descansar!"
            self.menu_acoes_estado = "comandos"
            return None

        alvo_hover = None
        for m in minions_vivos:
            if m.rect.inflate(16, 16).collidepoint(posicao_mouse):
                alvo_hover = m
                break

        if alvo_hover:
            cura_estimada = max(1, int(getattr(alvo_hover, "max_hp", 10) * 0.10))
            self.mensagem_log = f"💤 DESCANSAR: {alvo_hover.nome} (+{cura_estimada} HP)? Ele dormirá este turno. Clique para confirmar!"
        else:
            self.mensagem_log = "💤 DESCANSAR: Clique no summon para descansar e curar 10% do HP!"

        self.btn_voltar.atualizar(posicao_mouse, estado_clique_mouse)
        if not clicou:
            return None

        if self.btn_voltar.clicado(posicao_mouse):
            self.alvo_destaque = None
            self.menu_acoes_estado = "comandos"
            return None

        for m in minions_vivos:
            if m.rect.inflate(16, 16).collidepoint(posicao_mouse):
                self.alvo_destaque = m
                cura = max(1, int(getattr(m, "max_hp", 10) * 0.10))
                m.hp = min(getattr(m, "max_hp", 10), m.hp + cura)
                m.dormindo = True
                m.defendendo = False
                self.mensagem_log = f"💤 COMANDO: {m.nome} descansou (+{cura} HP) e dormirá este turno!"
                self.iniciar_cooldown_feedback(45, self.avancar_turno)
                self.menu_acoes_estado = "principal"
                break
        return None

TelaCombate = GerenciadorJogo
