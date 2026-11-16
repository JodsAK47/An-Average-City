import math
import random

import pygame
from Sistemas.SistemaUI import Botao, TelaBase, desenhar_painel_container
from Sistemas.Fontes import obter_fonte, quebrar_texto
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

TEMA_NORMAL = {
    "fundo": FUNDO,
    "painel": PAINEL,
    "detalhes": PAINEL_DETALHES,
    "card": CARD_DESBLOQUEADO,
    "bloqueado": CARD_BLOQUEADO,
    "borda": BORDA_DESBLOQUEADA,
    "borda_bloqueada": BORDA_BLOQUEADA,
    "selecao": BORDA_SELECIONADA,
    "destaque": OURO,
    "texto": TEXTO_BRANCO,
    "texto_bloqueado": TEXTO_BLOQUEADO,
    "status": VERDE_STATUS,
}
TEMA_PLATINA = {
    "fundo": (32, 25, 12),
    "painel": (54, 42, 23),
    "detalhes": (63, 48, 25),
    "card": (77, 59, 29),
    "bloqueado": (45, 36, 22),
    "borda": (190, 148, 61),
    "borda_bloqueada": (123, 96, 46),
    "selecao": (255, 229, 135),
    "destaque": (255, 220, 111),
    "texto": (255, 245, 211),
    "texto_bloqueado": (196, 170, 112),
    "status": (255, 225, 133),
}

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
        self.platinado = False
        self.tema = TEMA_NORMAL
        self.brilhos = []
        self._intervalo_brilhos = 0
        self._gerador_brilhos = random.Random()
        self._camada_brilhos = pygame.Surface(self.tela.get_size(), pygame.SRCALPHA)
        self._botao_com_sprites = self.botao_voltar.usar_sprites
        self._obter_conquistas_visiveis()

    def _obter_conquistas_visiveis(self):
        conquistas = sistema_conquistas.obter_conquistas_visiveis()
        if self.conquista_selecionada not in conquistas:
            id_anterior = getattr(self.conquista_selecionada, "id", None)
            self.conquista_selecionada = next(
                (conquista for conquista in conquistas if conquista.id == id_anterior),
                conquistas[0] if conquistas else None,
            )
        altura_conteudo = len(conquistas) * 86 + 20
        max_scroll = max(0, altura_conteudo - self.rect_lista.height)
        self.scroll_alvo = max(0.0, min(self.scroll_alvo, float(max_scroll)))
        self.scroll_y = max(0.0, min(self.scroll_y, float(max_scroll)))
        return conquistas

    def _sincronizar_tema(self):
        platinado = sistema_conquistas.esta_platinado()
        if platinado == self.platinado:
            return
        self.platinado = platinado
        self.tema = TEMA_PLATINA if platinado else TEMA_NORMAL
        self.brilhos.clear()
        self._intervalo_brilhos = 0
        self.botao_voltar.usar_sprites = False if platinado else self._botao_com_sprites
        if platinado:
            self.botao_voltar.definir_cores((123, 88, 28), (180, 133, 43), self.tema["texto"])
            for _ in range(6):
                self._criar_brilho()
        else:
            self.botao_voltar.definir_cores((55, 62, 78), (76, 98, 122), TEXTO_BRANCO)

    def _criar_brilho(self):
        if len(self.brilhos) >= 36:
            return
        self.brilhos.append({
            "x": self._gerador_brilhos.uniform(18, self.largura - 18),
            "y": self._gerador_brilhos.uniform(15, self.altura - 15),
            "idade": 0,
            "duracao": self._gerador_brilhos.randint(75, 135),
            "tamanho": self._gerador_brilhos.uniform(2.5, 5.0),
        })

    def _atualizar_brilhos(self):
        if not self.platinado:
            return
        for brilho in self.brilhos:
            brilho["idade"] += 1
            brilho["y"] -= 0.12
        self.brilhos[:] = [brilho for brilho in self.brilhos if brilho["idade"] < brilho["duracao"]]
        self._intervalo_brilhos -= 1
        if self._intervalo_brilhos <= 0:
            self._criar_brilho()
            self._intervalo_brilhos = 5

    def _desenhar_brilhos(self):
        if not self.platinado:
            return
        self._camada_brilhos.fill((0, 0, 0, 0))
        for brilho in self.brilhos:
            intensidade = math.sin(math.pi * brilho["idade"] / brilho["duracao"])
            alpha = int(175 * intensidade)
            x, y = int(brilho["x"]), int(brilho["y"])
            raio = max(1, int(brilho["tamanho"] * (0.5 + intensidade * 0.5)))
            pygame.draw.circle(self._camada_brilhos, (255, 198, 68, alpha // 5), (x, y), raio * 3)
            pygame.draw.line(self._camada_brilhos, (255, 225, 133, alpha), (x - raio, y), (x + raio, y), 1)
            pygame.draw.line(self._camada_brilhos, (255, 225, 133, alpha), (x, y - raio), (x, y + raio), 1)
            pygame.draw.circle(self._camada_brilhos, (255, 251, 222, alpha), (x, y), 1)
        self.tela.blit(self._camada_brilhos, (0, 0))

    def _desenhar_painel(self, superficie, rect, sprite, cor, borda, margem=8):
        if not self.platinado:
            desenhar_painel_container(superficie, rect, sprite, fallback_cor=cor, borda_cor=borda, margem=margem)
            return
        rect = pygame.Rect(rect)
        pygame.draw.rect(superficie, cor, rect, border_radius=7)
        pygame.draw.rect(superficie, borda, rect, width=2, border_radius=7)
        if rect.width > 20 and rect.height > 20:
            pygame.draw.rect(superficie, (107, 81, 34), rect.inflate(-8, -8), width=1, border_radius=4)

    def atualizar_eventos(self, evento, posicao_mouse):
        conquistas = self._obter_conquistas_visiveis()
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

                for c in conquistas:
                    rect_item = pygame.Rect(self.rect_lista.x + 10, deslocamento_y, largura_card, altura_card)
                    if rect_item.collidepoint(posicao_mouse):
                        self.conquista_selecionada = c
                        break
                    deslocamento_y += altura_card + espacamento

        return None

    def atualizar(self, posicao_mouse, estado_clique_mouse):
        self._sincronizar_tema()
        self._obter_conquistas_visiveis()
        self._atualizar_brilhos()
        self.botao_voltar.atualizar(posicao_mouse, estado_clique_mouse)
        self.scroll_y += (self.scroll_alvo - self.scroll_y) * 0.35

    def desenhar(self):
        self._sincronizar_tema()
        conquistas = self._obter_conquistas_visiveis()
        tema = self.tema
        self.tela.fill(tema["fundo"])

        self._desenhar_painel(self.tela, (40, 20, 920, 55), "painel_topo.png", tema["painel"], tema["borda"])

        titulo = "JOGO PLATINADO" if self.platinado else "SALA DE CONQUISTAS"
        txt_titulo = self.fonte_titulo.render(titulo, True, tema["destaque"])
        self.tela.blit(txt_titulo, (60, 32))

        desbloqueadas = sum(conquista.desbloqueada for conquista in conquistas)
        total = len(conquistas)
        porcentagem = int((desbloqueadas / total) * 100) if total > 0 else 0
        txt_progresso = self.fonte_desc.render(f"Progresso: {desbloqueadas}/{total} ({porcentagem}%)", True, tema["texto"])
        self.tela.blit(txt_progresso, (960 - 40 - txt_progresso.get_width(), 36))

        self._desenhar_painel(self.tela, self.rect_lista, "painel_base.png", tema["painel"], tema["borda"])

        superficie_clip = self.tela.subsurface(self.rect_lista)

        largura_card = self.rect_lista.width - 24
        altura_card = 76
        espacamento = 10
        y_rel = 10 - int(self.scroll_y)

        for c in conquistas:
            retangulo_card_local = pygame.Rect(10, y_rel, largura_card, altura_card)

            if retangulo_card_local.bottom >= 0 and retangulo_card_local.top <= self.rect_lista.height:
                esta_ativa = c.desbloqueada
                selecionada = (self.conquista_selecionada == c)
                progresso_secreto = sistema_conquistas.obter_progresso_easter_egg() if c.id == "easter_egg" else None

                cor_fundo_card = tema["card"] if esta_ativa else tema["bloqueado"]
                cor_borda = tema["selecao"] if selecionada else (tema["borda"] if esta_ativa else tema["borda_bloqueada"])
                sprite_card = "painel_ouro.png" if selecionada else ("painel_card.png" if esta_ativa else "painel_base.png")
                self._desenhar_painel(superficie_clip, retangulo_card_local, sprite_card, cor_fundo_card, cor_borda)

                icone_surf = c.obter_icone(desbloqueada=esta_ativa, tamanho=(52, 52))
                superficie_clip.blit(icone_surf, (retangulo_card_local.x + 10, retangulo_card_local.y + 12))

                cor_texto_nome = tema["texto"] if esta_ativa or progresso_secreto is not None else tema["texto_bloqueado"]
                txt_nome = self.fonte_nome.render(c.nome, True, cor_texto_nome)
                superficie_clip.blit(txt_nome, (retangulo_card_local.x + 72, retangulo_card_local.y + 14))

                if progresso_secreto is not None:
                    status = f"✓ DESBLOQUEADA · {progresso_secreto}%" if esta_ativa else f"PROGRESSO: {progresso_secreto}%"
                    txt_st = self.fonte_status.render(status, True, tema["destaque"])
                    barra = pygame.Rect(retangulo_card_local.x + 72, retangulo_card_local.y + 65, 200, 4)
                    pygame.draw.rect(superficie_clip, tema["borda_bloqueada"], barra, border_radius=2)
                    preenchimento = barra.copy()
                    preenchimento.width = int(barra.width * progresso_secreto / 100)
                    if preenchimento.width:
                        pygame.draw.rect(superficie_clip, tema["destaque"], preenchimento, border_radius=2)
                elif esta_ativa:
                    txt_st = self.fonte_status.render("✓ DESBLOQUEADA", True, tema["status"])
                else:
                    txt_st = self.fonte_status.render("🔒 BLOQUEADA", True, tema["texto_bloqueado"])
                superficie_clip.blit(txt_st, (retangulo_card_local.x + 72, retangulo_card_local.y + 44))

            y_rel += altura_card + espacamento

        total_altura_conteudo = len(conquistas) * (altura_card + espacamento) + 20
        if total_altura_conteudo > self.rect_lista.height:
            trilho_h = self.rect_lista.height - 16
            proporcao = self.rect_lista.height / total_altura_conteudo
            polegar_h = max(24, int(trilho_h * proporcao))
            max_scroll = total_altura_conteudo - self.rect_lista.height
            pos_y_polegar = int((self.scroll_y / max_scroll) * (trilho_h - polegar_h))
            rect_polegar = pygame.Rect(self.rect_lista.right - 10, self.rect_lista.y + 8 + pos_y_polegar, 5, polegar_h)
            pygame.draw.rect(self.tela, tema["destaque"], rect_polegar, border_radius=3)

        self._desenhar_painel(self.tela, self.rect_detalhes, "painel_detalhes.png", tema["detalhes"], tema["borda"])

        if self.conquista_selecionada:
            c = self.conquista_selecionada
            esta_ativa = c.desbloqueada
            progresso_secreto = sistema_conquistas.obter_progresso_easter_egg() if c.id == "easter_egg" else None

            frame_icone = pygame.Rect(self.rect_detalhes.centerx - 70, self.rect_detalhes.y + 30, 140, 140)
            cor_moldura = tema["destaque"] if esta_ativa else tema["borda_bloqueada"]
            sprite_moldura = "painel_ouro.png" if esta_ativa else "painel_card.png"
            self._desenhar_painel(self.tela, frame_icone, sprite_moldura, tema["fundo"], cor_moldura, margem=10)

            icone_grande = c.obter_icone(desbloqueada=esta_ativa, tamanho=(110, 110))
            rect_icone_grande = icone_grande.get_rect(center=frame_icone.center)
            self.tela.blit(icone_grande, rect_icone_grande)

            if progresso_secreto is not None:
                badge = f"★ CONQUISTADA · {progresso_secreto}% ★" if esta_ativa else f"PROGRESSO: {progresso_secreto}%"
                txt_badge = self.fonte_nome.render(badge, True, tema["destaque"])
                barra = pygame.Rect(self.rect_detalhes.centerx - 100, frame_icone.bottom + 40, 200, 4)
                pygame.draw.rect(self.tela, tema["borda_bloqueada"], barra, border_radius=2)
                preenchimento = barra.copy()
                preenchimento.width = int(barra.width * progresso_secreto / 100)
                if preenchimento.width:
                    pygame.draw.rect(self.tela, tema["destaque"], preenchimento, border_radius=2)
            elif esta_ativa:
                txt_badge = self.fonte_nome.render("★ CONQUISTADA ★", True, tema["destaque"])
            else:
                txt_badge = self.fonte_nome.render("🔒 NÃO OBTIDA (P&B)", True, tema["texto_bloqueado"])
            self.tela.blit(txt_badge, txt_badge.get_rect(center=(self.rect_detalhes.centerx, frame_icone.bottom + 25)))

            y_div = frame_icone.bottom + 50
            pygame.draw.line(self.tela, tema["borda_bloqueada"], (self.rect_detalhes.x + 30, y_div), (self.rect_detalhes.right - 30, y_div), 2)

            y_cursor = y_div + 20
            cor_nome = tema["destaque"] if esta_ativa else tema["texto"]
            for linha in quebrar_texto(c.nome.upper(), self.fonte_titulo, self.rect_detalhes.width - 60):
                surf_l = self.fonte_titulo.render(linha, True, cor_nome)
                self.tela.blit(surf_l, surf_l.get_rect(centerx=self.rect_detalhes.centerx, top=y_cursor))
                y_cursor += 26

            y_cursor += 15
            titulo_descricao = "DESCRIÇÃO:" if c.id == "easter_egg" else "COMO LIBERAR:"
            txt_sec = self.fonte_status.render(titulo_descricao, True, tema["destaque"])
            self.tela.blit(txt_sec, (self.rect_detalhes.x + 35, y_cursor))
            y_cursor += 22

            retangulo_caixa_desc = pygame.Rect(self.rect_detalhes.x + 30, y_cursor, self.rect_detalhes.width - 60, 130)
            self._desenhar_painel(self.tela, retangulo_caixa_desc, "painel_card.png", tema["painel"], tema["borda_bloqueada"])

            y_texto_desc = retangulo_caixa_desc.y + 12
            for linha in quebrar_texto(c.como_liberar, self.fonte_desc, retangulo_caixa_desc.width - 24):
                surf_desc = self.fonte_desc.render(linha, True, tema["texto"])
                self.tela.blit(surf_desc, (retangulo_caixa_desc.x + 12, y_texto_desc))
                y_texto_desc += 20

        self.botao_voltar.desenhar(self.tela)
        if self.platinado:
            pygame.draw.rect(self.tela, tema["borda"], self.botao_voltar.rect, 2, border_radius=6)
        self._desenhar_brilhos()
