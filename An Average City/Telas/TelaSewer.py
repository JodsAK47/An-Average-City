import math
import pygame
from Sistemas.SistemaUI import Botao, TelaBase
from Sistemas.Fontes import obter_fonte
import os
from Sistemas.Recursos import caminho_imagem, caminho_cenario, caminho_item
from Sistemas.SaveSystem import save_global

COR_FUNDO = (12, 16, 20)
PAINEL_BG = (20, 26, 32)
BORDA_PAINEL = (45, 60, 72)
VERDE_NEON = (0, 255, 140)
VERDE_ESCURO = (15, 55, 30)
CIANO = (50, 220, 255)
AMARELO_OURO = (255, 215, 60)
VERMELHO_ALERTA = (255, 75, 75)
TEXTO_BRANCO = (245, 248, 250)
TEXTO_CINZA = (160, 175, 190)

class GerenciadorSewerTela(TelaBase):
    def __init__(self, tela):
        super().__init__(tela, nome="sewer")
        self.tela = tela
        self.largura = tela.get_width()
        self.altura = tela.get_height()

        self.fonte_titulo = obter_fonte(18)
        self.fonte_sub = obter_fonte(12)
        self.fonte_texto = obter_fonte(13)
        self.fonte_botao = obter_fonte(13)
        self.fonte_tooltip = obter_fonte(11)

        self.tempo_anim = 0.0
        self.modal_aberto = False

        self.msg_aviso = ""
        self.cor_aviso = VERDE_NEON
        self.timer_aviso = 0

        self.imagem_fundo = None
        self.posicao_fundo = (0, 0)
        self.escala_fundo = 1.0

        try:
            caminho_fundo = caminho_cenario("EsgotoTrancado.png")
            if not os.path.exists(caminho_fundo):
                caminho_fundo = caminho_imagem("EsgotoTrancado.png")
            if not os.path.exists(caminho_fundo):
                caminho_fundo = caminho_imagem("SewerAccess.png")
            raw_fundo = pygame.image.load(caminho_fundo).convert()
            w_raw, h_raw = raw_fundo.get_size()
            escala = max(self.largura / w_raw, self.altura / h_raw)
            w_novo = int(w_raw * escala)
            h_novo = int(h_raw * escala)
            self.imagem_fundo = pygame.transform.scale(raw_fundo, (w_novo, h_novo))
            self.posicao_fundo = ((self.largura - w_novo) // 2, (self.altura - h_novo) // 2)
            self.escala_fundo = escala
        except Exception as e:
            print(f"[Aviso] Erro ao carregar fundo do esgoto: {e}")

        self.rect_saida = pygame.Rect(
            self.posicao_fundo[0] + int(740 * self.escala_fundo),
            self.posicao_fundo[1] + int(110 * self.escala_fundo),
            int(215 * self.escala_fundo),
            int(610 * self.escala_fundo)
        )

        self.rect_porta_restrita = pygame.Rect(
            self.posicao_fundo[0] + int(160 * self.escala_fundo),
            self.posicao_fundo[1] + int(130 * self.escala_fundo),
            int(225 * self.escala_fundo),
            int(350 * self.escala_fundo)
        )

        largura_card_chao = int(50 * self.escala_fundo)
        altura_card_chao = int(34 * self.escala_fundo)
        self.rect_card_chao = pygame.Rect(
            self.posicao_fundo[0] + int(505 * self.escala_fundo),
            self.posicao_fundo[1] + int(590 * self.escala_fundo),
            largura_card_chao,
            altura_card_chao
        )

        self.sprite_card_chao = None
        self.sprite_card_modal = None
        try:
            card_bruto = pygame.image.load(caminho_item("MemberCard.png")).convert_alpha()
            mini = pygame.transform.scale(card_bruto, (largura_card_chao, altura_card_chao))
            self.sprite_card_chao = pygame.transform.rotate(mini, -10)
            self.sprite_card_modal = pygame.transform.scale(card_bruto, (270, 180))
        except Exception as e:
            print(f"[Aviso] Erro ao carregar sprite do MemberCard: {e}")

        modal_cx = self.largura // 2
        modal_cy = self.altura // 2
        self.rect_modal = pygame.Rect(modal_cx - 260, modal_cy - 210, 520, 430)

        self.btn_pegar_card = Botao(
            self.rect_modal.x + 35, self.rect_modal.bottom - 65, 215, 44,
            "PEGAR CARTÃO", (25, 60, 40), (35, 95, 60), 220, 48,
            cor_texto=VERDE_NEON, fonte_tamanho=13
        )

        self.btn_deixar_card = Botao(
            self.rect_modal.right - 250, self.rect_modal.bottom - 65, 215, 44,
            "DEIXAR NO CHÃO", (50, 30, 35), (75, 40, 45), 220, 48,
            cor_texto=VERMELHO_ALERTA, fonte_tamanho=13
        )

    def mostrar_aviso(self, texto, cor=VERDE_NEON, duracao=180):
        self.msg_aviso = texto
        self.cor_aviso = cor
        self.timer_aviso = duracao

    def atualizar_eventos(self, evento, posicao_mouse):
        if self.modal_aberto:
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                self.modal_aberto = False
                self.mostrar_aviso("Você guardou o cartão no chão.", TEXTO_CINZA)
                return None

            if self.btn_pegar_card.checar_clique(evento, posicao_mouse):
                save_global.coletar_member_card()
                self.modal_aberto = False
                self.msg_aviso = ""
                self.timer_aviso = 0
                return None

            if self.btn_deixar_card.checar_clique(evento, posicao_mouse):
                self.modal_aberto = False
                self.mostrar_aviso("Você decidiu não mexer no cartão por enquanto.", TEXTO_CINZA)
                return None

            return None

        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            if self.rect_saida.collidepoint(posicao_mouse):
                return "menu"

            if not save_global.tem_member_card():
                retangulo_clique_card = self.rect_card_chao.inflate(20, 20)
                if retangulo_clique_card.collidepoint(posicao_mouse):
                    self.modal_aberto = True
                    return None

            if self.rect_porta_restrita.collidepoint(posicao_mouse):
                self.mostrar_aviso("Túnel alagado do esgoto. Não há passagem por aqui.", TEXTO_CINZA, 160)
                return None

        return None

    def atualizar(self, posicao_mouse, estado_clique_mouse):
        self.tempo_anim += 0.05

        if self.timer_aviso > 0:
            self.timer_aviso -= 1

        if self.modal_aberto:
            self.btn_pegar_card.atualizar(posicao_mouse, estado_clique_mouse)
            self.btn_deixar_card.atualizar(posicao_mouse, estado_clique_mouse)

    def desenhar(self):
        if self.imagem_fundo is not None:
            self.tela.blit(self.imagem_fundo, self.posicao_fundo)
        else:
            self.tela.fill(COR_FUNDO)

        posicao_mouse = pygame.mouse.get_pos()
        tem_card = save_global.tem_member_card()

        if not tem_card and self.sprite_card_chao is not None:
            self.tela.blit(self.sprite_card_chao, self.rect_card_chao.topleft)

        if not self.modal_aberto and self.rect_saida.collidepoint(posicao_mouse):
            surf_saida = self.fonte_tooltip.render("🚪 SAÍDA PARA A RUA // Clique na porta para voltar ao Menu", True, CIANO)
            caixa_saida = pygame.Rect(self.rect_saida.centerx - surf_saida.get_width() // 2 - 8,
                                    self.rect_saida.y + 40,
                                    surf_saida.get_width() + 16, surf_saida.get_height() + 8)
            pygame.draw.rect(self.tela, (14, 18, 24), caixa_saida, border_radius=5)
            pygame.draw.rect(self.tela, CIANO, caixa_saida, width=1, border_radius=5)
            self.tela.blit(surf_saida, (caixa_saida.x + 8, caixa_saida.y + 4))

        hud_rect = pygame.Rect(25, 20, 480, 48)
        pygame.draw.rect(self.tela, (18, 24, 30), hud_rect, border_radius=6)
        pygame.draw.rect(self.tela, BORDA_PAINEL, hud_rect, width=1, border_radius=6)

        txt_local = self.fonte_sub.render("LOCAL: REDE DE ESGOTOS // ESCONDERIJO SUBTERRÂNEO", True, CIANO)
        self.tela.blit(txt_local, (hud_rect.x + 12, hud_rect.y + 7))

        if tem_card:
            txt_card_status = self.fonte_tooltip.render("MEMBER CARD: ATIVO", True, VERDE_NEON)
        else:
            txt_card_status = self.fonte_tooltip.render("MEMBER CARD: INDISPONÍVEL", True, (255, 120, 120))
        self.tela.blit(txt_card_status, (hud_rect.x + 12, hud_rect.y + 27))

        if self.timer_aviso > 0 and self.msg_aviso:
            surf_av = self.fonte_texto.render(self.msg_aviso, True, self.cor_aviso)
            largura_av = surf_av.get_width() + 30
            altura_av = surf_av.get_height() + 14
            rect_av = pygame.Rect((self.largura - largura_av) // 2, 85, largura_av, altura_av)
            pygame.draw.rect(self.tela, (12, 16, 22), rect_av, border_radius=6)
            pygame.draw.rect(self.tela, self.cor_aviso, rect_av, width=2, border_radius=6)
            self.tela.blit(surf_av, (rect_av.x + 15, rect_av.y + 7))

        if self.modal_aberto:
            overlay = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 195))
            self.tela.blit(overlay, (0, 0))

            pygame.draw.rect(self.tela, PAINEL_BG, self.rect_modal, border_radius=10)
            pygame.draw.rect(self.tela, AMARELO_OURO, self.rect_modal, width=2, border_radius=10)

            txt_m_tit = self.fonte_titulo.render("ITEM ENCONTRADO NO CHÃO", True, AMARELO_OURO)
            self.tela.blit(txt_m_tit, (self.rect_modal.centerx - txt_m_tit.get_width() // 2, self.rect_modal.y + 18))

            if self.sprite_card_modal is not None:
                retangulo_card = self.sprite_card_modal.get_rect(center=(self.rect_modal.centerx, self.rect_modal.y + 150))
                moldura_card = retangulo_card.inflate(10, 10)
                pygame.draw.rect(self.tela, (30, 26, 18), moldura_card, border_radius=8)
                pygame.draw.rect(self.tela, AMARELO_OURO, moldura_card, width=2, border_radius=8)
                self.tela.blit(self.sprite_card_modal, retangulo_card.topleft)

            txt_nome_item = self.fonte_titulo.render("MEMBER CARD", True, VERDE_NEON)
            self.tela.blit(txt_nome_item, (self.rect_modal.centerx - txt_nome_item.get_width() // 2, self.rect_modal.y + 255))

            linhas_desc = [
                "Cartão de membro exclusivo com insígnia dourada gravada.",
                "Foi abandonado discretamente sob a bancada do terminal."
            ]
            for idx, linha in enumerate(linhas_desc):
                txt_l = self.fonte_tooltip.render(linha, True, TEXTO_CINZA)
                self.tela.blit(txt_l, (self.rect_modal.centerx - txt_l.get_width() // 2, self.rect_modal.y + 288 + idx * 20))

            self.btn_pegar_card.desenhar(self.tela)
            self.btn_deixar_card.desenhar(self.tela)
