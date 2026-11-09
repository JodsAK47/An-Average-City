import pygame
from typing import Tuple
from Sistemas.SistemaUI import TelaBase, Botao
from Sistemas.Fontes import obter_fonte

class GerenciadorVitoria(TelaBase):
    def __init__(self, tela: pygame.Surface):
        super().__init__(tela, nome="tela_vitoria")
        self.cor_fundo = (10, 36, 18)
        self.pontos = 0

        largura_botao = 260
        altura_botao = 52
        x_botao = (self.largura - largura_botao) // 2
        self.botao_menu = self.criar_botao(
            x_botao, 510, largura_botao, altura_botao, "VOLTAR AO MENU",
            cor_base=(28, 110, 48), cor_hover=(45, 165, 75),
            cor_texto=(255, 255, 255), fonte_tamanho=17, borda_raio=8,
            acao=lambda: "menu"
        )
        self.fonte_titulo = obter_fonte(52)
        self.fonte_subtitulo = obter_fonte(20)
        self.fonte_pontos = obter_fonte(28)
        self.fonte_dica = obter_fonte(13)

    def desenhar_conteudo(self):
        # Gradiente suave no fundo
        for y in range(0, self.altura, 4):
            fator = y / self.altura
            r = int(10 + fator * 12)
            g = int(28 + fator * 22)
            b = int(14 + fator * 16)
            pygame.draw.rect(self.tela, (r, g, b), (0, y, self.largura, 4))

        # Título VITÓRIA com sombra
        txt_sombra = self.fonte_titulo.render("VITÓRIA!", True, (0, 0, 0))
        txt_titulo = self.fonte_titulo.render("VITÓRIA!", True, (255, 215, 60))
        x_tit = (self.largura - txt_titulo.get_width()) // 2
        y_tit = 190
        self.tela.blit(txt_sombra, (x_tit + 3, y_tit + 3))
        self.tela.blit(txt_titulo, (x_tit, y_tit))

        # Linha divisória estética dourada
        comp_linha = 360
        x_linha = (self.largura - comp_linha) // 2
        y_linha = y_tit + txt_titulo.get_height() + 8
        pygame.draw.line(self.tela, (218, 165, 32), (x_linha, y_linha), (x_linha + comp_linha, y_linha), 2)

        # Frase temática
        txt_sub = self.fonte_subtitulo.render("O Chefe foi derrotado e seu bolso está a salvo!", True, (200, 245, 215))
        self.tela.blit(txt_sub, txt_sub.get_rect(center=(self.largura // 2, y_linha + 32)))

        # Placa de Pontos Conquistados estilizada
        txt_pontos = self.fonte_pontos.render(f"Pontos Conquistados: {self.pontos}", True, (255, 225, 90))
        rect_pts = txt_pontos.get_rect(center=(self.largura // 2, 340))
        placa_pts = rect_pts.inflate(40, 18)
        surf_pts_bg = pygame.Surface((placa_pts.width, placa_pts.height), pygame.SRCALPHA)
        surf_pts_bg.fill((10, 24, 16, 220))
        self.tela.blit(surf_pts_bg, placa_pts)
        pygame.draw.rect(self.tela, (60, 160, 95), placa_pts, width=2, border_radius=8)
        self.tela.blit(txt_pontos, rect_pts)

        # Dica de atalho no rodapé
        txt_dica = self.fonte_dica.render("[ESC] ou [ENTER] Voltar ao Menu", True, (130, 180, 145))
        self.tela.blit(txt_dica, txt_dica.get_rect(center=(self.largura // 2, 600)))
