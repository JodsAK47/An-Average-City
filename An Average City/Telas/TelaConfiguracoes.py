import pygame
from typing import Tuple, Optional
from Sistemas.SistemaUI import Botao, TelaBase, desenhar_painel_container
from Sistemas.Fontes import obter_fonte
from Sistemas.Configuracoes import sistema_config, RESOLUCOES_DISPONIVEIS

FUNDO = (18, 22, 30)
PAINEL = (28, 35, 48)
PAINEL_TOPO = (36, 45, 62)
BORDA_PAINEL = (52, 65, 88)
BORDA_ATIVA = (255, 215, 60)
BORDA_AZUL = (70, 160, 240)

BARRA_FUNDO = (20, 25, 35)
BARRA_BORDA = (50, 62, 82)
BARRA_GERAL = (80, 175, 245)
BARRA_MUSICA = (70, 215, 130)
BARRA_SFX = (245, 175, 60)

TEXTO_BRANCO = (240, 245, 250)
TEXTO_CINZA = (155, 170, 190)
TEXTO_AMARELO = (255, 215, 60)
TEXTO_VERDE = (80, 230, 130)
TEXTO_VERMELHO = (240, 80, 80)

class GerenciadorConfiguracoesTela(TelaBase):

    def __init__(self, tela: pygame.Surface):
        super().__init__(tela, nome="config")
        self.tela = tela
        self.largura = self.tela.get_width()
        self.altura = self.tela.get_height()

        self.fonte_titulo = obter_fonte(22)
        self.fonte_sub = obter_fonte(12)
        self.fonte_secao = obter_fonte(15)
        self.fonte_item = obter_fonte(13)
        self.fonte_valor = obter_fonte(12)
        self.fonte_feedback = obter_fonte(13)
        self.fonte_dica = obter_fonte(11)

        self.voltar_clicado = False
        self.mensagem_feedback = ""
        self.cor_feedback = TEXTO_VERDE
        self.temporizador_feedback = 0

        self.rect_audio = pygame.Rect(45, 90, 440, 580)
        self.rect_video = pygame.Rect(515, 90, 440, 580)

        self.rect_barra_geral = pygame.Rect(65, 180, 280, 24)
        self.rect_barra_musica = pygame.Rect(65, 260, 280, 24)
        self.rect_barra_sfx = pygame.Rect(65, 340, 280, 24)

        self.btn_geral_menos = Botao(355, 178, 36, 28, "-", (42, 52, 70), (60, 75, 100), 38, 30, cor_texto=TEXTO_BRANCO, fonte_tamanho=16)
        self.btn_geral_mais = Botao(398, 178, 36, 28, "+", (42, 52, 70), (60, 75, 100), 38, 30, cor_texto=TEXTO_BRANCO, fonte_tamanho=16)

        self.btn_musica_menos = Botao(355, 258, 36, 28, "-", (42, 52, 70), (60, 75, 100), 38, 30, cor_texto=TEXTO_BRANCO, fonte_tamanho=16)
        self.btn_musica_mais = Botao(398, 258, 36, 28, "+", (42, 52, 70), (60, 75, 100), 38, 30, cor_texto=TEXTO_BRANCO, fonte_tamanho=16)

        self.btn_sfx_menos = Botao(355, 338, 36, 28, "-", (42, 52, 70), (60, 75, 100), 38, 30, cor_texto=TEXTO_BRANCO, fonte_tamanho=16)
        self.btn_sfx_mais = Botao(398, 338, 36, 28, "+", (42, 52, 70), (60, 75, 100), 38, 30, cor_texto=TEXTO_BRANCO, fonte_tamanho=16)

        self.btn_mudo = Botao(65, 410, 400, 42, "🔊 ÁUDIO: ATIVO", (40, 50, 68), (55, 70, 95), 404, 44, cor_texto=TEXTO_VERDE, fonte_tamanho=13)

        self.btn_res_ant = Botao(535, 175, 42, 40, "<", (45, 56, 75), (65, 82, 110), 44, 42, cor_texto=TEXTO_AMARELO, fonte_tamanho=16)
        self.btn_res_prox = Botao(893, 175, 42, 40, ">", (45, 56, 75), (65, 82, 110), 44, 42, cor_texto=TEXTO_AMARELO, fonte_tamanho=16)
        self.rect_display_res = pygame.Rect(585, 175, 300, 40)

        self.botoes_res_rapida = [
            {"resolucao": (1000, 800), "btn": Botao(535, 235, 195, 36, "1000x800 (Padrão)", (40, 50, 68), (58, 74, 100), 198, 38, cor_texto=TEXTO_BRANCO, fonte_tamanho=11)},
            {"resolucao": (1280, 720), "btn": Botao(740, 235, 195, 36, "1280x720 (HD)", (40, 50, 68), (58, 74, 100), 198, 38, cor_texto=TEXTO_BRANCO, fonte_tamanho=11)},
            {"resolucao": (1600, 900), "btn": Botao(535, 280, 195, 36, "1600x900 (HD+)", (40, 50, 68), (58, 74, 100), 198, 38, cor_texto=TEXTO_BRANCO, fonte_tamanho=11)},
            {"resolucao": (1920, 1080), "btn": Botao(740, 280, 195, 36, "1920x1080 (FHD)", (40, 50, 68), (58, 74, 100), 198, 38, cor_texto=TEXTO_BRANCO, fonte_tamanho=11)},
        ]

        self.btn_modo_tela = Botao(535, 345, 400, 42, "MODO: JANELA", (42, 54, 74), (60, 78, 105), 404, 44, cor_texto=TEXTO_BRANCO, fonte_tamanho=13)

        self.btn_aplicar_video = Botao(
            535, 415, 400, 44, "APLICAR VÍDEO AGORA",
            (32, 120, 65), (42, 155, 85), 404, 46,
            cor_texto=TEXTO_BRANCO, fonte_tamanho=13
        )

        self.btn_padroes = Botao(
            45, 695, 210, 48, "RESTAURAR PADRÕES",
            (140, 70, 30), (180, 90, 40), 214, 50,
            cor_texto=TEXTO_BRANCO, fonte_tamanho=12
        )
        self.btn_salvar = Botao(
            275, 695, 210, 48, "SALVAR CONFIG",
            (30, 140, 70), (40, 180, 90), 214, 50,
            cor_texto=TEXTO_BRANCO, fonte_tamanho=13,
            sprite_base_path="BVERDEM.png", sprite_hover_path="BVERDG.png", sprite_clique_path="BVERDEP.png"
        )
        self.btn_voltar = Botao(
            735, 695, 220, 48, "VOLTAR",
            (55, 62, 78), (76, 98, 122), 226, 52,
            cor_texto=TEXTO_BRANCO, fonte_tamanho=14,
            sprite_base_path="BACK.png", sprite_hover_path="BACK.png", sprite_clique_path="BACK.png"
        )

        self._sincronizar_textos()

    def _sincronizar_textos(self):
        if sistema_config.esta_mutado():
            self.btn_mudo.definir_texto("🔇 ÁUDIO: MUTADO")
            self.btn_mudo.cor_texto = TEXTO_VERMELHO
        else:
            self.btn_mudo.definir_texto("🔊 ÁUDIO: ATIVO")
            self.btn_mudo.cor_texto = TEXTO_VERDE

        if sistema_config.obter_tela_cheia():
            self.btn_modo_tela.definir_texto("MODO: TELA CHEIA (FULLSCREEN)")
            self.btn_modo_tela.cor_texto = TEXTO_AMARELO
        else:
            self.btn_modo_tela.definir_texto("MODO: JANELA")
            self.btn_modo_tela.cor_texto = TEXTO_BRANCO

    def mostrar_feedback(self, texto: str, cor=TEXTO_VERDE):
        self.mensagem_feedback = texto
        self.cor_feedback = cor
        self.temporizador_feedback = 180

    def _ajustar_volume_por_clique(self, barra_rect: pygame.Rect, posicao_mouse: Tuple[int, int]) -> float:
        x_relativo = posicao_mouse[0] - barra_rect.x
        proporcao = max(0.0, min(1.0, x_relativo / barra_rect.width))
        return round(round(proporcao * 20) / 20.0, 2)

    def atualizar_eventos(self, evento: pygame.event.Event, posicao_mouse: Tuple[int, int]) -> Optional[str]:
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            self.voltar_clicado = True
            return "menu"

        if self.btn_voltar.checar_clique(evento, posicao_mouse):
            self.voltar_clicado = True
            return "menu"

        if self.btn_salvar.checar_clique(evento, posicao_mouse):
            sistema_config.salvar()
            self.mostrar_feedback("✓ Configurações salvas com sucesso!", TEXTO_VERDE)
            return None

        if self.btn_padroes.checar_clique(evento, posicao_mouse):
            sistema_config.restaurar_padroes()
            self._sincronizar_textos()
            self.mostrar_feedback("✓ Configurações restauradas para o padrão!", TEXTO_AMARELO)
            return "video_alterado"

        if self.btn_geral_menos.checar_clique(evento, posicao_mouse):
            sistema_config.alterar_volume_geral(-0.1)
            return None
        if self.btn_geral_mais.checar_clique(evento, posicao_mouse):
            sistema_config.alterar_volume_geral(0.1)
            return None

        if self.btn_musica_menos.checar_clique(evento, posicao_mouse):
            sistema_config.alterar_volume_musica(-0.1)
            return None
        if self.btn_musica_mais.checar_clique(evento, posicao_mouse):
            sistema_config.alterar_volume_musica(0.1)
            return None

        if self.btn_sfx_menos.checar_clique(evento, posicao_mouse):
            sistema_config.alterar_volume_sfx(-0.1)
            return None
        if self.btn_sfx_mais.checar_clique(evento, posicao_mouse):
            sistema_config.alterar_volume_sfx(0.1)
            return None

        if self.btn_mudo.checar_clique(evento, posicao_mouse):
            sistema_config.alternar_mudo()
            self._sincronizar_textos()
            return None

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.rect_barra_geral.collidepoint(posicao_mouse):
                novo_vol = self._ajustar_volume_por_clique(self.rect_barra_geral, posicao_mouse)
                sistema_config.definir_volume_geral(novo_vol)
            elif self.rect_barra_musica.collidepoint(posicao_mouse):
                novo_vol = self._ajustar_volume_por_clique(self.rect_barra_musica, posicao_mouse)
                sistema_config.definir_volume_musica(novo_vol)
            elif self.rect_barra_sfx.collidepoint(posicao_mouse):
                novo_vol = self._ajustar_volume_por_clique(self.rect_barra_sfx, posicao_mouse)
                sistema_config.definir_volume_sfx(novo_vol)

        if self.btn_res_ant.checar_clique(evento, posicao_mouse):
            sistema_config.resolucao_anterior()
            return None
        if self.btn_res_prox.checar_clique(evento, posicao_mouse):
            sistema_config.proxima_resolucao()
            return None

        for item in self.botoes_res_rapida:
            if item["btn"].checar_clique(evento, posicao_mouse):
                larg, alt = item["resolucao"]
                sistema_config.definir_resolucao(larg, alt)
                return None

        if self.btn_modo_tela.checar_clique(evento, posicao_mouse):
            sistema_config.alternar_tela_cheia()
            self._sincronizar_textos()
            return None

        if self.btn_aplicar_video.checar_clique(evento, posicao_mouse):
            sistema_config.aplicar_video()
            sistema_config.salvar()
            self.mostrar_feedback("✓ Modo de vídeo aplicado com sucesso!", TEXTO_VERDE)
            return "video_alterado"

        return None

    def atualizar(self, posicao_mouse: Tuple[int, int], estado_clique_mouse: Tuple[bool, ...]):
        if self.temporizador_feedback > 0:
            self.temporizador_feedback -= 1

        self._sincronizar_textos()

        self.btn_geral_menos.atualizar(posicao_mouse, estado_clique_mouse)
        self.btn_geral_mais.atualizar(posicao_mouse, estado_clique_mouse)
        self.btn_musica_menos.atualizar(posicao_mouse, estado_clique_mouse)
        self.btn_musica_mais.atualizar(posicao_mouse, estado_clique_mouse)
        self.btn_sfx_menos.atualizar(posicao_mouse, estado_clique_mouse)
        self.btn_sfx_mais.atualizar(posicao_mouse, estado_clique_mouse)
        self.btn_mudo.atualizar(posicao_mouse, estado_clique_mouse)

        self.btn_res_ant.atualizar(posicao_mouse, estado_clique_mouse)
        self.btn_res_prox.atualizar(posicao_mouse, estado_clique_mouse)
        for item in self.botoes_res_rapida:
            item["btn"].atualizar(posicao_mouse, estado_clique_mouse)
        self.btn_modo_tela.atualizar(posicao_mouse, estado_clique_mouse)
        self.btn_aplicar_video.atualizar(posicao_mouse, estado_clique_mouse)

        self.btn_padroes.atualizar(posicao_mouse, estado_clique_mouse)
        self.btn_salvar.atualizar(posicao_mouse, estado_clique_mouse)
        self.btn_voltar.atualizar(posicao_mouse, estado_clique_mouse)

    def _desenhar_barra_volume(
        self,
        rect: pygame.Rect,
        valor: float,
        cor_preenchimento: Tuple[int, int, int],
        rotulo: str,
        valor_efetivo: float
    ):
        pygame.draw.rect(self.tela, BARRA_FUNDO, rect, border_radius=5)

        largura_ativa = int(rect.width * max(0.0, min(1.0, valor)))
        if largura_ativa > 0:
            rect_ativa = pygame.Rect(rect.x, rect.y, largura_ativa, rect.height)
            pygame.draw.rect(self.tela, cor_preenchimento, rect_ativa, border_radius=5)

        pygame.draw.rect(self.tela, BARRA_BORDA, rect, width=2, border_radius=5)

        txt_rotulo = self.fonte_item.render(rotulo, True, TEXTO_BRANCO)
        self.tela.blit(txt_rotulo, (rect.x, rect.y - 24))

        pct = int(valor * 100)
        str_pct = f"{pct}%" if not sistema_config.esta_mutado() else f"{pct}% (Mudo)"
        cor_pct = TEXTO_BRANCO if not sistema_config.esta_mutado() else TEXTO_CINZA
        txt_pct = self.fonte_valor.render(str_pct, True, cor_pct)
        self.tela.blit(txt_pct, (rect.right + 105, rect.y + 4))

    def desenhar(self):
        self.tela.fill(FUNDO)

        txt_titulo = self.fonte_titulo.render("CONFIGURAÇÕES DO SISTEMA", True, TEXTO_AMARELO)
        rect_titulo = txt_titulo.get_rect(center=(self.largura // 2, 42))
        self.tela.blit(txt_titulo, rect_titulo)

        txt_sub = self.fonte_sub.render(
            "Ajuste a resolução da janela, modo de exibição e controle os volumes de áudio.",
            True,
            TEXTO_CINZA
        )
        rect_sub = txt_sub.get_rect(center=(self.largura // 2, 68))
        self.tela.blit(txt_sub, rect_sub)

        desenhar_painel_container(self.tela, self.rect_audio, "painel_base.png", fallback_cor=PAINEL, borda_cor=BORDA_PAINEL)

        rect_cab_audio = pygame.Rect(self.rect_audio.x, self.rect_audio.y, self.rect_audio.width, 42)
        desenhar_painel_container(self.tela, rect_cab_audio, "painel_topo.png", fallback_cor=PAINEL_TOPO, borda_cor=BORDA_PAINEL, margem=10)
        txt_cab_audio = self.fonte_secao.render("🔊 ÁUDIO & SOM", True, TEXTO_AMARELO)
        self.tela.blit(txt_cab_audio, (rect_cab_audio.x + 16, rect_cab_audio.y + 12))

        self._desenhar_barra_volume(
            self.rect_barra_geral,
            sistema_config.obter_volume_geral(),
            BARRA_GERAL,
            "Volume Geral (Master):",
            sistema_config.obter_volume_geral()
        )
        self.btn_geral_menos.desenhar(self.tela)
        self.btn_geral_mais.desenhar(self.tela)

        self._desenhar_barra_volume(
            self.rect_barra_musica,
            sistema_config.obter_volume_musica(),
            BARRA_MUSICA,
            "Volume da Música (OST):",
            sistema_config.obter_volume_musica_efetivo()
        )
        self.btn_musica_menos.desenhar(self.tela)
        self.btn_musica_mais.desenhar(self.tela)

        self._desenhar_barra_volume(
            self.rect_barra_sfx,
            sistema_config.obter_volume_sfx(),
            BARRA_SFX,
            "Volume dos Efeitos Sonoros (SFX):",
            sistema_config.obter_volume_sfx_efetivo()
        )
        self.btn_sfx_menos.desenhar(self.tela)
        self.btn_sfx_mais.desenhar(self.tela)

        self.btn_mudo.desenhar(self.tela)

        txt_dica_audio = self.fonte_dica.render("• Clique na barra ou use [-] e [+] para ajustar.", True, TEXTO_CINZA)
        self.tela.blit(txt_dica_audio, (self.rect_audio.x + 20, self.rect_audio.bottom - 80))
        txt_dica_audio2 = self.fonte_dica.render("• O volume da música é atualizado em tempo real.", True, TEXTO_CINZA)
        self.tela.blit(txt_dica_audio2, (self.rect_audio.x + 20, self.rect_audio.bottom - 55))

        desenhar_painel_container(self.tela, self.rect_video, "painel_base.png", fallback_cor=PAINEL, borda_cor=BORDA_PAINEL)

        rect_cab_video = pygame.Rect(self.rect_video.x, self.rect_video.y, self.rect_video.width, 42)
        desenhar_painel_container(self.tela, rect_cab_video, "painel_topo.png", fallback_cor=PAINEL_TOPO, borda_cor=BORDA_PAINEL, margem=10)
        txt_cab_video = self.fonte_secao.render("🖥️ VÍDEO & RESOLUÇÃO", True, TEXTO_AMARELO)
        self.tela.blit(txt_cab_video, (rect_cab_video.x + 16, rect_cab_video.y + 12))

        txt_rot_res = self.fonte_item.render("Resolução da Janela:", True, TEXTO_BRANCO)
        self.tela.blit(txt_rot_res, (self.rect_video.x + 20, 150))

        self.btn_res_ant.desenhar(self.tela)
        self.btn_res_prox.desenhar(self.tela)

        desenhar_painel_container(self.tela, self.rect_display_res, "painel_card.png", fallback_cor=BARRA_FUNDO, borda_cor=BORDA_AZUL, margem=8)
        txt_res_atual = self.fonte_valor.render(sistema_config.obter_texto_resolucao_atual(), True, TEXTO_AMARELO)
        self.tela.blit(txt_res_atual, txt_res_atual.get_rect(center=self.rect_display_res.center))

        res_atual_tuple = sistema_config.obter_resolucao()
        for item in self.botoes_res_rapida:
            item["btn"].desenhar(self.tela)
            if item["resolucao"] == res_atual_tuple:
                pygame.draw.rect(self.tela, BORDA_ATIVA, item["btn"].rect, width=2, border_radius=item["btn"].borda_raio)

        txt_rot_modo = self.fonte_item.render("Modo de Exibição:", True, TEXTO_BRANCO)
        self.tela.blit(txt_rot_modo, (self.rect_video.x + 20, 324))
        self.btn_modo_tela.desenhar(self.tela)

        self.btn_aplicar_video.desenhar(self.tela)

        txt_dica_f11 = self.fonte_dica.render("• Pressione F11 para alternar Tela Cheia instantaneamente.", True, TEXTO_CINZA)
        self.tela.blit(txt_dica_f11, (self.rect_video.x + 20, self.rect_video.bottom - 80))
        txt_dica_prop = self.fonte_dica.render("• O jogo preserva proporção e escala sem distorções.", True, TEXTO_CINZA)
        self.tela.blit(txt_dica_prop, (self.rect_video.x + 20, self.rect_video.bottom - 55))

        self.btn_padroes.desenhar(self.tela)
        self.btn_salvar.desenhar(self.tela)
        self.btn_voltar.desenhar(self.tela)

        if self.temporizador_feedback > 0 and self.mensagem_feedback:
            txt_fb = self.fonte_feedback.render(self.mensagem_feedback, True, self.cor_feedback)
            largura_caixa = txt_fb.get_width() + 32
            altura_caixa = txt_fb.get_height() + 16
            rect_fb = pygame.Rect((self.largura - largura_caixa) // 2, 642, largura_caixa, altura_caixa)

            desenhar_painel_container(self.tela, rect_fb, "painel_retorno.png", fallback_cor=(16, 22, 30), borda_cor=self.cor_feedback, margem=8)
            self.tela.blit(txt_fb, (rect_fb.x + 16, rect_fb.y + 8))
