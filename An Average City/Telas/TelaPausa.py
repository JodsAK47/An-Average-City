import pygame
from typing import Optional, Tuple
from Sistemas.SistemaUI import TelaBase, Botao
from Sistemas.Fontes import obter_fonte
from Entidades.Personagem import personagem

class GerenciadorPausa(TelaBase):
    """
    Menu de pausa sobreposto ao jogo (combate, inventário, etc.).
    Permite:
      - Continuar a partida exatamente de onde parou (ESC / botão Continuar).
      - Acessar a tela de configurações (áudio, vídeo, controles) e retornar à pausa.
      - Retornar ao menu principal (título), resetando o progresso da partida atual.
    """

    def __init__(self, tela: pygame.Surface):
        super().__init__(tela, nome="pausa")
        self.tela = tela
        self.largura = self.tela.get_width()
        self.altura = self.tela.get_height()

        self.estado_anterior = "jogo"
        self.superficie_fundo: Optional[pygame.Surface] = None

        # Fontes do modal
        self.fonte_titulo = obter_fonte(26)
        self.fonte_subtitulo = obter_fonte(14)
        self.fonte_info = obter_fonte(12)
        self.fonte_dica = obter_fonte(11)

        # Dimensões do modal central
        self.largura_painel = 420
        self.altura_painel = 370
        self.x_painel = (self.largura - self.largura_painel) // 2
        self.y_painel = (self.altura - self.altura_painel) // 2
        self.rect_painel = pygame.Rect(self.x_painel, self.y_painel, self.largura_painel, self.altura_painel)

        # Botões do menu de pausa
        largura_btn = 310
        altura_btn = 46
        x_btn = (self.largura - largura_btn) // 2
        y_primeiro_btn = self.y_painel + 130
        espacamento_btn = 60

        self.btn_continuar = Botao(
            x_btn,
            y_primeiro_btn,
            largura_btn,
            altura_btn,
            "▶ CONTINUAR (ESC)",
            cor_base=(35, 115, 75),
            cor_hover=(48, 160, 102),
            largura_hover=largura_btn + 4,
            altura_hover=altura_btn + 2,
            cor_texto=(245, 255, 245),
            fonte_tamanho=13,
            borda_raio=8
        )

        self.btn_config = Botao(
            x_btn,
            y_primeiro_btn + espacamento_btn,
            largura_btn,
            altura_btn,
            "⚙ CONFIGURAÇÕES",
            cor_base=(48, 62, 90),
            cor_hover=(70, 92, 132),
            largura_hover=largura_btn + 4,
            altura_hover=altura_btn + 2,
            cor_texto=(235, 245, 255),
            fonte_tamanho=13,
            borda_raio=8
        )

        self.btn_menu = Botao(
            x_btn,
            y_primeiro_btn + espacamento_btn * 2,
            largura_btn,
            altura_btn,
            "🏠 TELA DE TÍTULO",
            cor_base=(120, 36, 46),
            cor_hover=(165, 48, 60),
            largura_hover=largura_btn + 4,
            altura_hover=altura_btn + 2,
            cor_texto=(255, 235, 235),
            fonte_tamanho=13,
            borda_raio=8
        )

        self.botoes = [self.btn_continuar, self.btn_config, self.btn_menu]

    def abrir(self, estado_anterior: str = "jogo"):
        """Congela a tela atual e prepara o menu de pausa."""
        self.estado_anterior = estado_anterior
        try:
            self.superficie_fundo = self.tela.copy()
        except Exception:
            self.superficie_fundo = None

    def fechar(self):
        """Libera o snapshot da tela."""
        self.superficie_fundo = None

    def atualizar_eventos(self, evento: pygame.event.Event, posicao_mouse: Tuple[int, int]) -> Optional[str]:
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_ESCAPE, pygame.K_p):
                return "continuar"

        if self.btn_continuar.checar_clique(evento, posicao_mouse):
            return "continuar"

        if self.btn_config.checar_clique(evento, posicao_mouse):
            return "config"

        if self.btn_menu.checar_clique(evento, posicao_mouse):
            return "menu"

        return None

    def atualizar(self, posicao_mouse: Tuple[int, int], estado_clique_mouse: Tuple[bool, ...]):
        for btn in self.botoes:
            btn.atualizar(posicao_mouse, estado_clique_mouse)

    def desenhar(self):
        # 1. Desenha o fundo congelado da tela anterior
        if self.superficie_fundo is not None:
            self.tela.blit(self.superficie_fundo, (0, 0))
        else:
            self.tela.fill((16, 20, 28))

        # 2. Camada escura semi-transparente para dar destaque ao painel modal
        overlay = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        overlay.fill((8, 12, 18, 195))
        self.tela.blit(overlay, (0, 0))

        # 3. Sombra do painel central
        sombra = pygame.Rect(self.rect_painel.x + 6, self.rect_painel.y + 8, self.largura_painel, self.altura_painel)
        sombra_surf = pygame.Surface((self.largura_painel, self.altura_painel), pygame.SRCALPHA)
        sombra_surf.fill((0, 0, 0, 110))
        self.tela.blit(sombra_surf, sombra.topleft)

        # 4. Caixa principal do modal
        pygame.draw.rect(self.tela, (24, 30, 42), self.rect_painel, border_radius=12)
        pygame.draw.rect(self.tela, (65, 85, 120), self.rect_painel, width=2, border_radius=12)

        # Faixa superior de destaque
        faixa_topo = pygame.Rect(self.rect_painel.x, self.rect_painel.y, self.largura_painel, 58)
        pygame.draw.rect(self.tela, (32, 40, 56), faixa_topo, border_top_left_radius=12, border_top_right_radius=12)
        pygame.draw.line(self.tela, (80, 105, 145), (faixa_topo.left, faixa_topo.bottom), (faixa_topo.right, faixa_topo.bottom), 1)

        # 5. Título
        surf_titulo = self.fonte_titulo.render("JOGO PAUSADO", True, (255, 220, 110))
        self.tela.blit(surf_titulo, surf_titulo.get_rect(center=(self.rect_painel.centerx, self.rect_painel.y + 30)))

        # 6. Informações contextuais (modo atual / status)
        if self.estado_anterior == "jogo":
            contexto_txt = "Combate em Andamento"
        elif self.estado_anterior == "pos_luta":
            contexto_txt = "Inventário / Descanso"
        elif self.estado_anterior == "selecao_cenario":
            contexto_txt = "Seleção de Caminho"
        elif self.estado_anterior == "loja":
            contexto_txt = "Loja de Itens"
        else:
            contexto_txt = "Partida em Andamento"

        hp_info = f"HP: {int(personagem.hp)}/{int(personagem.max_hp)}" if hasattr(personagem, 'hp') else ""
        info_linha = f"{contexto_txt}  •  {hp_info}" if hp_info else contexto_txt
        surf_info = self.fonte_info.render(info_linha, True, (170, 185, 205))
        self.tela.blit(surf_info, surf_info.get_rect(center=(self.rect_painel.centerx, self.rect_painel.y + 88)))

        # Linha divisória
        pygame.draw.line(self.tela, (48, 60, 80), (self.rect_painel.x + 30, self.rect_painel.y + 112), (self.rect_painel.right - 30, self.rect_painel.y + 112), 1)

        # 7. Renderização dos botões
        for btn in self.botoes:
            btn.desenhar(self.tela)

        # 8. Dica de atalho no rodapé
        surf_dica = self.fonte_dica.render("Pressione [ESC] ou [P] para continuar", True, (130, 145, 170))
        self.tela.blit(surf_dica, surf_dica.get_rect(center=(self.rect_painel.centerx, self.rect_painel.bottom - 22)))

TelaPausa = GerenciadorPausa
