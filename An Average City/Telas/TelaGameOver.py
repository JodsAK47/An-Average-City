import os
import math
import random
from typing import Optional, Tuple
import pygame

from Sistemas.SistemaUI import TelaBase, Botao
from Sistemas.Fontes import obter_fonte
from Sistemas.Recursos import caminho_cenario, caminho_imagem

class GerenciadorGameOver(TelaBase):
    """
    Tela de Game Over temática para cada verso (Feiticeiro, Sobrevivente, Agente).
    Apresenta uma camada preta de transparência (alpha) sobre o fundo temático
    para escurecer o cenário e maximizar a legibilidade dos textos e botões.
    Inclui opção para retornar ao 'MENU PRINCIPAL'.
    """

    CORES_VERSO = {
        "feiticeiro": {
            "primaria": (220, 40, 70),
            "borda": (170, 30, 60),
            "tag": "VERSO: FEITICEIRO",
            "img": "GameOver Feiticeiro.png",
        },
        "sobrevivente": {
            "primaria": (230, 95, 35),
            "borda": (180, 70, 25),
            "tag": "VERSO: SOBREVIVENTE",
            "img": "GameOver Sobrevivente.png",
        },
        "agente": {
            "primaria": (0, 195, 240),
            "borda": (0, 140, 180),
            "tag": "VERSO: AGENTE",
            "img": "GameOver Agente.png",
        },
    }

    def __init__(self, tela: pygame.Surface):
        super().__init__(tela, nome="game_over")
        self.verso = "Sobrevivente"
        self.pontos = 0
        self.cache_fundos = {}
        self.superficie_fundo_atual: Optional[pygame.Surface] = None
        self.eh_placeholder_agente = False

        # Camada preta de transparência para escurecer a arte de fundo e melhorar o contraste
        self.camada_escurecimento = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        self.camada_escurecimento.fill((0, 0, 0, 165))

        # Fontes elegantes
        self.fonte_titulo = obter_fonte(56)
        self.fonte_subtitulo = obter_fonte(20)
        self.fonte_pontos = obter_fonte(28)
        self.fonte_badge = obter_fonte(14)
        self.fonte_dica = obter_fonte(13)

        # Botões de alta visibilidade
        largura_botao = 300
        altura_botao = 54
        x_botao = (self.largura - largura_botao) // 2

        self.botao_menu = self.criar_botao(
            x_botao, 495, largura_botao, altura_botao, "MENU PRINCIPAL",
            cor_base=(38, 44, 56), cor_hover=(60, 70, 88),
            cor_texto=(240, 245, 250), fonte_tamanho=16, borda_raio=8,
            acao=lambda: "menu"
        )

        self.definir_verso("Sobrevivente")

    def definir_verso(self, verso: str):
        self.verso = verso if verso and verso != "Nenhuma" else "Sobrevivente"
        chave = self.verso.lower().strip()

        config = self.CORES_VERSO.get(chave, self.CORES_VERSO["sobrevivente"])
        nome_img = config["img"]

        # Buscar arquivo de imagem nos diretórios de cenários e sprites
        caminho_arquivo = None
        for tentativa in [caminho_cenario(nome_img), caminho_imagem(nome_img)]:
            if os.path.exists(tentativa):
                caminho_arquivo = tentativa
                break

        if caminho_arquivo in self.cache_fundos:
            self.superficie_fundo_atual = self.cache_fundos[caminho_arquivo]
            self.eh_placeholder_agente = False
        elif caminho_arquivo:
            try:
                img_carregada = pygame.image.load(caminho_arquivo)
                if pygame.display.get_surface() is not None:
                    img_carregada = img_carregada.convert()
                self.superficie_fundo_atual = pygame.transform.scale(img_carregada, (self.largura, self.altura))
                self.cache_fundos[caminho_arquivo] = self.superficie_fundo_atual
                self.eh_placeholder_agente = False
            except (pygame.error, FileNotFoundError) as err:
                print(f"[Aviso] Nao foi possivel carregar imagem de game over '{nome_img}': {err}")
                self.superficie_fundo_atual = self._gerar_fundo_procedural(chave)
        else:
            # Imagem inexistente: gerar background procedural temático
            self.superficie_fundo_atual = self._gerar_fundo_procedural(chave)
            if chave == "agente":
                self.eh_placeholder_agente = True

        # Atualizar cores do botão de menu de acordo com o verso
        cor_prim = config["primaria"]
        cor_hover = tuple(min(255, int(c * 1.25 + 20)) for c in cor_prim)
        self.botao_menu.cor_hover = cor_hover

    def _gerar_fundo_procedural(self, chave_verso: str) -> pygame.Surface:
        """Gera uma atmosfera procedural temática caso a arte oficial não esteja presente no disco."""
        surf = pygame.Surface((self.largura, self.altura))
        rng = random.Random(42)

        if chave_verso == "agente":
            # Estilo Cybernetic Blue/Slate
            for y in range(0, self.altura, 2):
                tom = int(10 + (y / self.altura) * 16)
                pygame.draw.line(surf, (8, tom, tom + 14), (0, y), (self.largura, y))
            # Grade digital
            for x in range(0, self.largura, 40):
                pygame.draw.line(surf, (14, 28, 42), (x, 0), (x, self.altura), 1)
            for y in range(0, self.altura, 40):
                pygame.draw.line(surf, (14, 28, 42), (0, y), (self.largura, y), 1)
        elif chave_verso == "feiticeiro":
            # Estilo Cursed Crimson/Purple
            for y in range(0, self.altura, 2):
                fator = y / self.altura
                r = int(24 + fator * 22)
                g = int(6 + fator * 4)
                b = int(14 + fator * 16)
                pygame.draw.line(surf, (r, g, b), (0, y), (self.largura, y))
        else:
            # Estilo Sobrevivente: Cinzas, ruínas e brumas vermelhas
            for y in range(0, self.altura, 2):
                fator = y / self.altura
                r = int(28 + fator * 25)
                g = int(10 + fator * 8)
                b = int(8 + fator * 6)
                pygame.draw.line(surf, (r, g, b), (0, y), (self.largura, y))

            # Partículas de brasas/cinzas estáticas
            for _ in range(120):
                px = rng.randint(0, self.largura)
                py = rng.randint(0, self.altura)
                raio = rng.randint(1, 3)
                cor_brasa = (rng.randint(180, 240), rng.randint(60, 110), 20)
                pygame.draw.circle(surf, cor_brasa, (px, py), raio)

        return surf

    def atualizar_eventos(self, evento: pygame.event.Event, posicao_mouse: Tuple[int, int]):
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_ESCAPE, pygame.K_m, pygame.K_RETURN, pygame.K_SPACE):
                return "menu"

        res_menu = self.botao_menu.checar_clique(evento, posicao_mouse)
        if res_menu:
            return res_menu

        return None

    def desenhar(self):
        # 1. Desenhar a arte de fundo do verso
        if self.superficie_fundo_atual is not None:
            self.tela.blit(self.superficie_fundo_atual, (0, 0))
        else:
            self.tela.fill((14, 8, 8))

        # 2. Camada preta de transparência (escurece a imagem e garante máxima legibilidade dos botões)
        self.tela.blit(self.camada_escurecimento, (0, 0))

        # 3. Conteúdo da tela de Game Over
        self.desenhar_conteudo()

        # 4. Botão de retorno ao menu
        self.botao_menu.desenhar(self.tela)

    def desenhar_conteudo(self):
        chave = (self.verso or "sobrevivente").lower().strip()
        config = self.CORES_VERSO.get(chave, self.CORES_VERSO["sobrevivente"])

        # Tag do Verso (Badge no topo)
        tag_texto = f"[ {config['tag']} ]"
        surf_tag = self.fonte_badge.render(tag_texto, True, config["primaria"])
        rect_tag = surf_tag.get_rect(center=(self.largura // 2, 170))

        # Fundo do Badge
        bg_badge = rect_tag.inflate(24, 10)
        surf_badge_bg = pygame.Surface((bg_badge.width, bg_badge.height), pygame.SRCALPHA)
        surf_badge_bg.fill((16, 18, 26, 210))
        self.tela.blit(surf_badge_bg, bg_badge)
        pygame.draw.rect(self.tela, config["borda"], bg_badge, width=2, border_radius=6)
        self.tela.blit(surf_tag, rect_tag)

        # Título GAME OVER com sombra para destaque dramático
        txt_titulo_sombra = self.fonte_titulo.render("GAME OVER", True, (0, 0, 0))
        txt_titulo = self.fonte_titulo.render("GAME OVER", True, (255, 45, 45))
        x_tit = (self.largura - txt_titulo.get_width()) // 2
        y_tit = 210
        self.tela.blit(txt_titulo_sombra, (x_tit + 3, y_tit + 3))
        self.tela.blit(txt_titulo, (x_tit, y_tit))

        # Linha divisória estética sob o título
        comprimento_linha = 380
        x_linha = (self.largura - comprimento_linha) // 2
        y_linha = y_tit + txt_titulo.get_height() + 8
        pygame.draw.line(self.tela, config["borda"], (x_linha, y_linha), (x_linha + comprimento_linha, y_linha), 2)

        # Placa de Pontos com fundo estilizado
        txt_pontos = self.fonte_pontos.render(f"Pontos Conquistados: {self.pontos}", True, (255, 215, 75))
        rect_pts = txt_pontos.get_rect(center=(self.largura // 2, 320))
        placa_pts = rect_pts.inflate(36, 16)
        surf_pts_bg = pygame.Surface((placa_pts.width, placa_pts.height), pygame.SRCALPHA)
        surf_pts_bg.fill((12, 16, 24, 200))
        self.tela.blit(surf_pts_bg, placa_pts)
        pygame.draw.rect(self.tela, (70, 75, 95), placa_pts, width=1, border_radius=6)
        self.tela.blit(txt_pontos, rect_pts)

        # Frase temática
        frase = "A cidade cobrou seu tributo. Reagrupe-se e tente novamente."
        if chave == "feiticeiro":
            frase = "Sua energia amaldiçoada se extinguiu no combate."
        elif chave == "agente":
            frase = "Sinal vital perdido. Os agentes falharam na contenção."

        txt_frase = self.fonte_subtitulo.render(frase, True, (190, 200, 215))
        self.tela.blit(txt_frase, txt_frase.get_rect(center=(self.largura // 2, 385)))

        # Dica de atalhos no rodapé
        txt_dica = self.fonte_dica.render("[ESC] ou [M] Voltar ao Menu", True, (130, 140, 160))
        self.tela.blit(txt_dica, txt_dica.get_rect(center=(self.largura // 2, 620)))
