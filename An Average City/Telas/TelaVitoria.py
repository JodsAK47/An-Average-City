import pygame
from Sistemas.SistemaUI import TelaBase, Botao
from Sistemas.Fontes import obter_fonte

class GerenciadorVitoria(TelaBase):
    def __init__(self, tela):
        super().__init__(tela, nome="tela_vitoria")
        self.cor_fundo = (10, 40, 10)
        self.botao_menu = self.criar_botao(
            400, 600, 200, 50, "VOLTAR AO MENU",
            cor_base=(30, 100, 30), cor_hover=(50, 150, 50),
            cor_texto=(255, 255, 255),
            acao=lambda: "menu"
        )
        self.fonte_titulo = obter_fonte(40)
        self.fonte_texto = obter_fonte(20)

    def desenhar_conteudo(self):
        titulo = self.fonte_titulo.render("VITÓRIA!", True, (255, 215, 0))
        texto = self.fonte_texto.render("O Chefe foi derrotado e seu bolso está a salvo!", True, (200, 255, 200))

        self.tela.blit(titulo, (self.largura // 2 - titulo.get_width() // 2, 250))
        self.tela.blit(texto, (self.largura // 2 - texto.get_width() // 2, 350))

