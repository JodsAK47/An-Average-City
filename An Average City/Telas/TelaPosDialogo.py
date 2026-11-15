import pygame
from Sistemas.Fontes import obter_fonte, quebrar_texto
from Sistemas.SistemaUI import Botao, TelaBase

class GerenciadorPosDialogo(TelaBase):
    def __init__(self, tela):
        super().__init__(tela, nome="pos_dialogo")
        self.tela = tela
        self.largura = tela.get_width()
        self.altura = tela.get_height()

        self.fonte_status = obter_fonte(28)
        self.fonte_nome = obter_fonte(20)
        self.fonte_subtitulo = obter_fonte(16)
        self.fonte_texto = obter_fonte(15)
        self.fonte_efeito = obter_fonte(14)

        self.dados = {}
        self.sucesso = False
        self.titulo = ""
        self.nome_evento = ""
        self.narrativa = ""
        self.efeitos = []

        largura_btn = 260
        altura_btn = 46
        x_btn = (self.largura - largura_btn) // 2
        y_btn = min(self.altura - 130, int(self.altura * 0.76))
        self.btn_continuar = Botao(x_btn, y_btn, largura_btn, altura_btn, "AVANÇAR",
                                   (45, 95, 140), (65, 130, 190), largura_btn, altura_btn,
                                   cor_texto=(255, 255, 255), fonte_tamanho=14)

        self.tem_loja = False
        self.tipo_loja = "barista"
        self.btn_loja = None
        self.superficie_overlay = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        self.superficie_overlay.fill((10, 10, 16, 215))

    def configurar(self, dados_resultado):
        self.dados = dados_resultado or {}
        self.sucesso = bool(self.dados.get("sucesso", False))
        self.titulo = self.dados.get("titulo_resultado", "SUCESSO!" if self.sucesso else "FALHA!")
        evento = self.dados.get("evento")
        self.nome_evento = self.dados.get("nome_evento") or (evento.nome if evento else "Cenário")
        self.narrativa = self.dados.get("narrativa", "")
        self.efeitos = list(self.dados.get("efeitos", []))

        self.largura = self.tela.get_width()
        self.altura = self.tela.get_height()
        altura_btn = 46
        y_btn = min(self.altura - 130, int(self.altura * 0.76))
        nome_ev_lower = (self.nome_evento or "").lower()
        self.tem_loja = bool("perigo" in nome_ev_lower or "barista" in nome_ev_lower or "mantimentos" in nome_ev_lower)

        if self.tem_loja:
            self.tipo_loja = "perigo" if "perigo" in nome_ev_lower else "barista"
            if self.tipo_loja == "perigo" and not self.sucesso:
                self.tem_loja = False

        if self.tem_loja:
            txt_loja = "ENTRAR NA LOJA DO PERIGO 🛒" if self.tipo_loja == "perigo" else "ENTRAR NA LOJA DO BARISTA ☕"
            cor_norm = (140, 50, 50) if self.tipo_loja == "perigo" else (40, 115, 75)
            cor_hov = (180, 70, 70) if self.tipo_loja == "perigo" else (60, 155, 100)
            largura_loja = 250
            largura_cont = 210
            gap = 20
            total_w = largura_loja + largura_cont + gap
            x_loja = (self.largura - total_w) // 2
            x_cont = x_loja + largura_loja + gap
            self.btn_loja = Botao(x_loja, y_btn, largura_loja, altura_btn, txt_loja,
                                  cor_norm, cor_hov, largura_loja, altura_btn,
                                  cor_texto=(255, 255, 255), fonte_tamanho=12)
            self.btn_continuar = Botao(x_cont, y_btn, largura_cont, altura_btn, "AVANÇAR",
                                       (45, 95, 140), (65, 130, 190), largura_cont, altura_btn,
                                       cor_texto=(255, 255, 255), fonte_tamanho=14)
        else:
            self.btn_loja = None
            largura_btn = 260
            x_btn = (self.largura - largura_btn) // 2
            self.btn_continuar = Botao(x_btn, y_btn, largura_btn, altura_btn, "AVANÇAR",
                                       (45, 95, 140), (65, 130, 190), largura_btn, altura_btn,
                                       cor_texto=(255, 255, 255), fonte_tamanho=14)

    def atualizar_eventos(self, evento, posicao_mouse):
        if self.tem_loja and self.btn_loja and self.btn_loja.checar_clique(evento, posicao_mouse):
            return "abrir_loja"
        if evento.type == pygame.KEYDOWN and evento.key in (pygame.K_RETURN, pygame.K_SPACE):
            return "continuar"
        if self.btn_continuar.checar_clique(evento, posicao_mouse):
            return "continuar"
        return None

    def atualizar(self, posicao_mouse, estado_clique_mouse):
        if self.tem_loja and self.btn_loja:
            self.btn_loja.atualizar(posicao_mouse, estado_clique_mouse)
        self.btn_continuar.atualizar(posicao_mouse, estado_clique_mouse)

    def desenhar(self, posicao_mouse):
        self.tela.blit(self.superficie_overlay, (0, 0))

        largura_caixa = min(720, self.largura - 80)
        altura_caixa = min(540, self.altura - 100)
        x_caixa = (self.largura - largura_caixa) // 2
        y_caixa = (self.altura - altura_caixa) // 2
        rect_caixa = pygame.Rect(x_caixa, y_caixa, largura_caixa, altura_caixa)

        cor_borda = (70, 210, 125) if self.sucesso else (235, 75, 75)
        cor_titulo = (85, 240, 140) if self.sucesso else (255, 95, 95)
        cor_fundo = (24, 28, 38)

        pygame.draw.rect(self.tela, cor_fundo, rect_caixa, border_radius=12)
        pygame.draw.rect(self.tela, cor_borda, rect_caixa, width=3, border_radius=12)

        txt_tit = self.fonte_status.render(self.titulo, True, cor_titulo)
        self.tela.blit(txt_tit, txt_tit.get_rect(centerx=rect_caixa.centerx, top=y_caixa + 24))

        txt_sub = self.fonte_nome.render(self.nome_evento, True, (240, 240, 250))
        self.tela.blit(txt_sub, txt_sub.get_rect(centerx=rect_caixa.centerx, top=y_caixa + 68))

        pygame.draw.line(self.tela, (65, 75, 95), (x_caixa + 30, y_caixa + 104), (x_caixa + largura_caixa - 30, y_caixa + 104), 2)

        y_atual = y_caixa + 120
        largura_texto = largura_caixa - 60

        linhas_narrativa = quebrar_texto(self.narrativa, self.fonte_texto, largura_texto)

        for linha in linhas_narrativa:
            surf_linha = self.fonte_texto.render(linha, True, (220, 225, 235))
            self.tela.blit(surf_linha, (x_caixa + 30, y_atual))
            y_atual += self.fonte_texto.get_linesize()

        y_atual += 16
        txt_sec = self.fonte_subtitulo.render("CONSEQUÊNCIAS:", True, (255, 215, 90))
        self.tela.blit(txt_sec, (x_caixa + 30, y_atual))
        y_atual += self.fonte_subtitulo.get_linesize() + 6

        cor_item = (180, 235, 195) if self.sucesso else (245, 185, 185)
        for efeito in self.efeitos:
            prefixo = "" if efeito.startswith("•") else "• "
            surf_ef = self.fonte_efeito.render(f"{prefixo}{efeito}", True, cor_item)
            self.tela.blit(surf_ef, (x_caixa + 45, y_atual))
            y_atual += self.fonte_efeito.get_linesize() + 4

        y_bottom_btns = rect_caixa.bottom - 24
        if self.tem_loja and self.btn_loja:
            gap = 20
            total_w = self.btn_loja.rect.width + self.btn_continuar.rect.width + gap
            x_inicio = rect_caixa.centerx - total_w // 2
            self.btn_loja.rect.x = x_inicio
            self.btn_loja.rect.bottom = y_bottom_btns
            self.btn_continuar.rect.x = x_inicio + self.btn_loja.rect.width + gap
            self.btn_continuar.rect.bottom = y_bottom_btns
            self.btn_loja.desenhar(self.tela)
        else:
            self.btn_continuar.rect.centerx = rect_caixa.centerx
            self.btn_continuar.rect.bottom = y_bottom_btns
        self.btn_continuar.desenhar(self.tela)
