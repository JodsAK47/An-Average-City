import pygame
from Sistemas.Fontes import obter_fonte
from Sistemas.SistemaUI import Botao, TelaBase

class GerenciadorDialogo(TelaBase):
    def __init__(self, tela):
        super().__init__(tela, nome="dialogo")
        self.tela = tela
        self.largura = tela.get_width()
        self.altura = tela.get_height()

        self.fonte_nome = obter_fonte(24)
        self.fonte_texto = obter_fonte(18)
        self.fonte_opcoes = obter_fonte(16)

        self.ativo = False
        self.dados = []
        self.indice_atual = 0

        self.opcoes_retangulos = []
        self.indice_selecionado = 0
        self.retangulo_dialogo = pygame.Rect(0, 0, 0, 0)
        self.mouse_pressionado = False

        self.cor_overlay = (10, 10, 15, 200)
        self.cor_caixa = (35, 40, 55, 240)
        self.cor_borda = (80, 95, 120)
        self.cor_texto = (235, 235, 235)
        self.cor_nome = (255, 220, 100)
        self.cor_fundo_retrato = (25, 30, 40)
        self.cor_opcao_normal = (50, 60, 80)
        self.cor_opcao_hover = (85, 100, 130)

        self.superficie_overlay = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        self.superficie_overlay.fill(self.cor_overlay)

    def iniciar(self, dados_dialogo):
        if not dados_dialogo:
            return

        self.dados = dados_dialogo
        self.indice_atual = 0
        self.ativo = True
        self._preparar_no_atual()
        try:
            from Sistemas.GerenciadorAudio import tocar_sfx
            tocar_sfx("Dialogo.wav", volume_relativo=0.8)
        except Exception:
            pass

    def _preparar_no_atual(self):
        no_atual = self.dados[self.indice_atual]
        self.indice_selecionado = 0
        self.opcoes_retangulos = []

        opcoes = no_atual.get("opcoes", [])
        qtd_opcoes = max(1, len(opcoes))

        caixa_w = self.largura - 80
        caixa_h = self.altura - 70
        caixa_x = (self.largura - caixa_w) // 2
        caixa_y = (self.altura - caixa_h) // 2
        lista_x = caixa_x + caixa_w * 0.68
        y_base = caixa_y + caixa_h - 60 - (qtd_opcoes * 56)

        for i in range(qtd_opcoes):
            rect = pygame.Rect(int(lista_x - 250), int(y_base + i * 56), 500, 40)
            self.opcoes_retangulos.append(rect)

    def atualizar_eventos(self, evento, posicao_mouse):
        if not self.ativo:
            return None

        no_atual = self.dados[self.indice_atual]
        opcoes = no_atual.get("opcoes", [])
        tem_opcoes = len(opcoes) > 0

        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_UP:
                self.indice_selecionado = (self.indice_selecionado - 1) % max(1, len(self.opcoes_retangulos))
            elif evento.key == pygame.K_DOWN:
                self.indice_selecionado = (self.indice_selecionado + 1) % max(1, len(self.opcoes_retangulos))
            elif evento.key == pygame.K_RETURN:
                if tem_opcoes:
                    retorno = opcoes[self.indice_selecionado].get("retorno")
                    return self._avancar_ou_retornar(retorno)
                else:
                    return self._avancar_ou_retornar(None)

        if evento.type == pygame.MOUSEMOTION:
            for i, rect in enumerate(self.opcoes_retangulos):
                if rect.collidepoint(posicao_mouse):
                    self.indice_selecionado = i
                    break

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self.mouse_pressionado = True

        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            if self.mouse_pressionado:
                self.mouse_pressionado = False
                if not tem_opcoes and self.retangulo_dialogo.collidepoint(posicao_mouse):
                    return self._avancar_ou_retornar(None)

                for i, rect in enumerate(self.opcoes_retangulos):
                    if rect.collidepoint(posicao_mouse):
                        self.indice_selecionado = i
                        retorno = opcoes[i].get("retorno")
                        return self._avancar_ou_retornar(retorno)

        return None

    def _avancar_ou_retornar(self, retorno):
        try:
            from Sistemas.GerenciadorAudio import tocar_sfx
            tocar_sfx("Dialogo.wav", volume_relativo=0.8)
        except Exception:
            pass
        self.indice_atual += 1
        if self.indice_atual < len(self.dados):
            self._preparar_no_atual()
            return None
        else:
            self.ativo = False
            return retorno if retorno is not None else "fim_dialogo"

    def desenhar(self):
        if not self.ativo:
            return

        self.tela.blit(self.superficie_overlay, (0, 0))

        no_atual = self.dados[self.indice_atual]
        nome = no_atual.get("nome", "Desconhecido")
        texto = no_atual.get("texto", "")

        caixa_w = self.largura - 80
        caixa_h = self.altura - 70
        caixa_x = (self.largura - caixa_w) // 2
        caixa_y = (self.altura - caixa_h) // 2

        rect_caixa = pygame.Rect(caixa_x, caixa_y, caixa_w, caixa_h)
        self.retangulo_dialogo = rect_caixa
        pygame.draw.rect(self.tela, self.cor_caixa, rect_caixa, border_radius=16)
        pygame.draw.rect(self.tela, self.cor_borda, rect_caixa, width=3, border_radius=16)

        img_size = 220
        img_x = caixa_x + 38
        img_y = caixa_y + 38
        rect_img = pygame.Rect(img_x, img_y, img_size, img_size)

        pygame.draw.rect(self.tela, self.cor_fundo_retrato, rect_img, border_radius=10)
        pygame.draw.rect(self.tela, self.cor_borda, rect_img, width=2, border_radius=10)

        txt_img = self.fonte_opcoes.render("RETRATO", True, (100, 110, 130))
        self.tela.blit(txt_img, txt_img.get_rect(center=rect_img.center))

        texto_x = img_x + img_size + 40
        texto_y = img_y + 8
        texto_w = caixa_w - img_size - 120

        txt_nome = self.fonte_nome.render(nome, True, self.cor_nome)
        self.tela.blit(txt_nome, (texto_x, texto_y))

        deslocamento_y = texto_y + 42
        linhas = self._quebrar_texto(texto, self.fonte_texto, texto_w)
        for linha in linhas:
            txt_surf = self.fonte_texto.render(linha, True, self.cor_texto)
            self.tela.blit(txt_surf, (texto_x, deslocamento_y))
            deslocamento_y += 24

        opcoes = no_atual.get("opcoes", [])
        if len(opcoes) == 0:
            opcoes = [{"texto": "Continuar"}]

        lista_x = caixa_x + caixa_w * 0.68
        y_base = caixa_y + caixa_h - 60 - (len(opcoes) * 56)
        for i, opcao in enumerate(opcoes):
            rect = pygame.Rect(int(lista_x - 250), int(y_base + i * 56), 500, 40)
            selecionado = (i == self.indice_selecionado)
            cor_fundo = self.cor_opcao_hover if selecionado else self.cor_opcao_normal
            cor_borda = (255, 220, 100) if selecionado else self.cor_borda

            pygame.draw.rect(self.tela, cor_fundo, rect, border_radius=8)
            pygame.draw.rect(self.tela, cor_borda, rect, width=2, border_radius=8)

            texto_opcao = opcao.get("texto", "")
            cor_txt = (255, 255, 255) if selecionado else (200, 200, 200)
            txt_surf = self.fonte_opcoes.render(texto_opcao, True, cor_txt)
            self.tela.blit(txt_surf, txt_surf.get_rect(center=rect.center))

    def _quebrar_texto(self, texto, fonte, largura_maxima):
        linhas = []
        for paragrafo in texto.split("\n"):
            palavras = paragrafo.split()
            linha_atual = ""
            for palavra in palavras:
                teste = f"{linha_atual} {palavra}".strip()
                if fonte.size(teste)[0] <= largura_maxima:
                    linha_atual = teste
                else:
                    if linha_atual:
                        linhas.append(linha_atual)
                    linha_atual = palavra
            if linha_atual:
                linhas.append(linha_atual)
        return linhas
