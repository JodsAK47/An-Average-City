import pygame
from Sistemas.SistemaUI import Botao, TelaBase, desenhar_painel_container
from Sistemas.Fontes import obter_fonte
from Sistemas.Recursos import caminho_botao
from Sistemas.Conquistas import sistema_conquistas

FUNDO = (22, 26, 36)
PAINEL = (32, 38, 52)
PAINEL_DETALHES = (36, 44, 60)
CARD_DESBLOQUEADO = (42, 52, 70)
CARD_BLOQUEADO = (28, 33, 44)
BORDA_DESBLOQUEADA = (100, 130, 170)
BORDA_BLOQUEADA = (50, 56, 70)
BORDA_SELECIONADA = (255, 215, 60)
OURO = (245, 205, 55)
TEXTO_BRANCO = (240, 242, 245)
TEXTO_SECUNDARIO = (175, 185, 200)
TEXTO_BLOQUEADO = (120, 130, 145)
VERDE_STATUS = (70, 220, 120)
VERMELHO_STATUS = (210, 80, 80)

class GerenciadorConquistasTela(TelaBase):
    def __init__(self, tela):
        super().__init__(tela, nome="conquistas")
        self.tela = tela
        self.fonte_titulo = obter_fonte(20)
        self.fonte_nome = obter_fonte(14)
        self.fonte_desc = obter_fonte(12)
        self.fonte_status = obter_fonte(11)

        self.scroll_y = 0.0
        self.scroll_alvo = 0.0
        self.voltar_clicado = False

        self.rect_lista = pygame.Rect(40, 90, 510, 670)
        self.rect_detalhes = pygame.Rect(570, 90, 390, 580)

        self.botao_voltar = Botao(
            720, 700, 240, 50, "VOLTAR", (55, 62, 78), (76, 98, 122), 250, 55,
            cor_texto=TEXTO_BRANCO, fonte_tamanho=14,
            sprite_base_path="BACK.png", sprite_hover_path="BACK.png", sprite_clique_path="BACK.png",
        )

        self.conquista_selecionada = None
        if sistema_conquistas.conquistas:
            self.conquista_selecionada = sistema_conquistas.conquistas[0]

    def _quebrar_texto(self, texto, fonte, largura_maxima):
        linhas = []
        for paragrafo in texto.split("\n"):
            palavras = paragrafo.split()
            if not palavras:
                linhas.append("")
                continue
            linha = ""
            for palavra in palavras:
                tentativa = f"{linha} {palavra}".strip()
                if fonte.size(tentativa)[0] <= largura_maxima:
                    linha = tentativa
                else:
                    if linha:
                        linhas.append(linha)
                    linha = palavra
            if linha:
                linhas.append(linha)
        return linhas

    def atualizar_eventos(self, evento, posicao_mouse):
        if self.botao_voltar.checar_clique(evento, posicao_mouse):
            self.voltar_clicado = True
            return "menu"

        if evento.type == pygame.MOUSEWHEEL:
            if self.rect_lista.collidepoint(posicao_mouse):
                self.scroll_alvo -= evento.y * 55

        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            if self.rect_lista.collidepoint(posicao_mouse):
                deslocamento_y = self.rect_lista.y + 10 - int(self.scroll_y)
                largura_card = self.rect_lista.width - 24
                altura_card = 76
                espacamento = 10

                for c in sistema_conquistas.conquistas:
                    rect_item = pygame.Rect(self.rect_lista.x + 10, deslocamento_y, largura_card, altura_card)
                    if rect_item.collidepoint(posicao_mouse):
                        self.conquista_selecionada = c
                        break
                    deslocamento_y += altura_card + espacamento

        return None

    def atualizar(self, posicao_mouse, estado_clique_mouse):
        self.botao_voltar.atualizar(posicao_mouse, estado_clique_mouse)

        total_itens = len(sistema_conquistas.conquistas)
        altura_conteudo = total_itens * (76 + 10) + 20
        max_scroll = max(0, altura_conteudo - self.rect_lista.height)

        self.scroll_alvo = max(0.0, min(self.scroll_alvo, float(max_scroll)))
        self.scroll_y += (self.scroll_alvo - self.scroll_y) * 0.35

    def desenhar(self):
        self.tela.fill(FUNDO)

        desenhar_painel_container(self.tela, (40, 20, 920, 55), "painel_topo.png", fallback_cor=PAINEL, borda_cor=BORDA_DESBLOQUEADA)

        txt_titulo = self.fonte_titulo.render("SALA DE CONQUISTAS", True, OURO)
        self.tela.blit(txt_titulo, (60, 32))

        desbloqueadas = sistema_conquistas.total_desbloqueadas()
        total = sistema_conquistas.total_conquistas()
        porcentagem = int((desbloqueadas / total) * 100) if total > 0 else 0
        txt_progresso = self.fonte_desc.render(f"Progresso: {desbloqueadas}/{total} ({porcentagem}%)", True, TEXTO_BRANCO)
        self.tela.blit(txt_progresso, (960 - 40 - txt_progresso.get_width(), 36))

        desenhar_painel_container(self.tela, self.rect_lista, "painel_base.png", fallback_cor=PAINEL, borda_cor=BORDA_DESBLOQUEADA)

        superficie_clip = self.tela.subsurface(self.rect_lista)

        largura_card = self.rect_lista.width - 24
        altura_card = 76
        espacamento = 10
        y_rel = 10 - int(self.scroll_y)

        for c in sistema_conquistas.conquistas:
            retangulo_card_local = pygame.Rect(10, y_rel, largura_card, altura_card)

            if retangulo_card_local.bottom >= 0 and retangulo_card_local.top <= self.rect_lista.height:
                esta_ativa = c.desbloqueada
                selecionada = (self.conquista_selecionada == c)

                cor_fundo_card = CARD_DESBLOQUEADO if esta_ativa else CARD_BLOQUEADO
                cor_borda = BORDA_SELECIONADA if selecionada else (BORDA_DESBLOQUEADA if esta_ativa else BORDA_BLOQUEADA)
                sprite_card = "painel_ouro.png" if selecionada else ("painel_card.png" if esta_ativa else "painel_base.png")
                desenhar_painel_container(superficie_clip, retangulo_card_local, sprite_card, fallback_cor=cor_fundo_card, borda_cor=cor_borda, margem=8)

                icone_surf = c.obter_icone(desbloqueada=esta_ativa, tamanho=(52, 52))
                superficie_clip.blit(icone_surf, (retangulo_card_local.x + 10, retangulo_card_local.y + 12))

                cor_texto_nome = TEXTO_BRANCO if esta_ativa else TEXTO_BLOQUEADO
                txt_nome = self.fonte_nome.render(c.nome, True, cor_texto_nome)
                superficie_clip.blit(txt_nome, (retangulo_card_local.x + 72, retangulo_card_local.y + 14))

                if esta_ativa:
                    txt_st = self.fonte_status.render("✓ DESBLOQUEADA", True, VERDE_STATUS)
                else:
                    txt_st = self.fonte_status.render("🔒 BLOQUEADA", True, TEXTO_BLOQUEADO)
                superficie_clip.blit(txt_st, (retangulo_card_local.x + 72, retangulo_card_local.y + 44))

            y_rel += altura_card + espacamento

        total_altura_conteudo = len(sistema_conquistas.conquistas) * (altura_card + espacamento) + 20
        if total_altura_conteudo > self.rect_lista.height:
            trilho_h = self.rect_lista.height - 16
            proporcao = self.rect_lista.height / total_altura_conteudo
            polegar_h = max(24, int(trilho_h * proporcao))
            max_scroll = total_altura_conteudo - self.rect_lista.height
            pos_y_polegar = int((self.scroll_y / max_scroll) * (trilho_h - polegar_h))
            rect_polegar = pygame.Rect(self.rect_lista.right - 10, self.rect_lista.y + 8 + pos_y_polegar, 5, polegar_h)
            pygame.draw.rect(self.tela, OURO, rect_polegar, border_radius=3)

        desenhar_painel_container(self.tela, self.rect_detalhes, "painel_detalhes.png", fallback_cor=PAINEL_DETALHES, borda_cor=BORDA_DESBLOQUEADA)

        if self.conquista_selecionada:
            c = self.conquista_selecionada
            esta_ativa = c.desbloqueada

            frame_icone = pygame.Rect(self.rect_detalhes.centerx - 70, self.rect_detalhes.y + 30, 140, 140)
            cor_moldura = OURO if esta_ativa else BORDA_BLOQUEADA
            sprite_moldura = "painel_ouro.png" if esta_ativa else "painel_card.png"
            desenhar_painel_container(self.tela, frame_icone, sprite_moldura, fallback_cor=(20, 24, 32), borda_cor=cor_moldura, margem=10)

            icone_grande = c.obter_icone(desbloqueada=esta_ativa, tamanho=(110, 110))
            rect_icone_grande = icone_grande.get_rect(center=frame_icone.center)
            self.tela.blit(icone_grande, rect_icone_grande)

            if esta_ativa:
                txt_badge = self.fonte_nome.render("★ CONQUISTADA ★", True, OURO)
            else:
                txt_badge = self.fonte_nome.render("🔒 NÃO OBTIDA (P&B)", True, TEXTO_BLOQUEADO)
            self.tela.blit(txt_badge, txt_badge.get_rect(center=(self.rect_detalhes.centerx, frame_icone.bottom + 25)))

            y_div = frame_icone.bottom + 50
            pygame.draw.line(self.tela, BORDA_BLOQUEADA, (self.rect_detalhes.x + 30, y_div), (self.rect_detalhes.right - 30, y_div), 2)

            y_cursor = y_div + 20
            cor_nome = OURO if esta_ativa else TEXTO_BRANCO
            for linha in self._quebrar_texto(c.nome.upper(), self.fonte_titulo, self.rect_detalhes.width - 60):
                surf_l = self.fonte_titulo.render(linha, True, cor_nome)
                self.tela.blit(surf_l, surf_l.get_rect(centerx=self.rect_detalhes.centerx, top=y_cursor))
                y_cursor += 26

            y_cursor += 15
            txt_sec = self.fonte_status.render("COMO LIBERAR:", True, OURO)
            self.tela.blit(txt_sec, (self.rect_detalhes.x + 35, y_cursor))
            y_cursor += 22

            retangulo_caixa_desc = pygame.Rect(self.rect_detalhes.x + 30, y_cursor, self.rect_detalhes.width - 60, 130)
            desenhar_painel_container(self.tela, retangulo_caixa_desc, "painel_card.png", fallback_cor=(25, 30, 42), borda_cor=BORDA_BLOQUEADA, margem=8)

            y_texto_desc = retangulo_caixa_desc.y + 12
            for linha in self._quebrar_texto(c.como_liberar, self.fonte_desc, retangulo_caixa_desc.width - 24):
                surf_desc = self.fonte_desc.render(linha, True, TEXTO_BRANCO)
                self.tela.blit(surf_desc, (retangulo_caixa_desc.x + 12, y_texto_desc))
                y_texto_desc += 20

        self.botao_voltar.desenhar(self.tela)
