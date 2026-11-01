import math
import pygame
from Sistemas.Fontes import obter_fonte
from Sistemas.Recursos import caminho_botao, caminho_imagem
from Sistemas.SistemaUI import Botao, TelaBase, GerenciadorTelas
from Sistemas.SaveSystem import save_global

class GerenciadorMenu(TelaBase):
    def __init__(self, tela):
        super().__init__(tela, nome="menu")
        self.tela = tela

        largura_tela = self.tela.get_width()
        altura_tela = self.tela.get_height()

        caminho_fundo = caminho_imagem("Menu.png")
        try:
            imagem_fundo = pygame.image.load(caminho_fundo).convert()
            escala = max(largura_tela / imagem_fundo.get_width(), altura_tela / imagem_fundo.get_height())
            tamanho_fundo = (int(imagem_fundo.get_width() * escala), int(imagem_fundo.get_height() * escala))
            imagem_fundo = pygame.transform.scale(imagem_fundo, tamanho_fundo)
            x_fundo = (largura_tela - tamanho_fundo[0]) // 2
            y_fundo = (altura_tela - tamanho_fundo[1]) // 2
            self.imagem_fundo = imagem_fundo
            self.posicao_fundo = (x_fundo, y_fundo)
            self.escala_fundo = escala
        except (FileNotFoundError, pygame.error) as erro:
            self.imagem_fundo = None
            self.posicao_fundo = (0, 0)
            self.escala_fundo = 1.0
            print(f"Aviso: nao foi possivel carregar o fundo do menu: {erro}")

        self.fonte_titulo = obter_fonte(60)
        self.txt_titulo = self.fonte_titulo.render("MENU", True, (255, 255, 255))

        largura_alvo_titulo = 310
        x_titulo = (largura_tela - largura_alvo_titulo) // 2
        y_titulo = 35

        self.imagem_titulo = None
        for nome_titulo in ("Titulo.png", "Titulo.jpg"):
            try:
                img_carregada = pygame.image.load(caminho_imagem(nome_titulo)).convert_alpha()
                caixa_delimitadora = img_carregada.get_bounding_rect()
                if caixa_delimitadora.width > 0 and caixa_delimitadora.height > 0:
                    img_carregada = img_carregada.subsurface(caixa_delimitadora).copy()
                largura_orig, altura_orig = img_carregada.get_size()
                proporcao = largura_orig / max(1, altura_orig)
                altura_alvo_titulo = int(largura_alvo_titulo / proporcao)
                self.imagem_titulo = pygame.transform.smoothscale(img_carregada, (largura_alvo_titulo, altura_alvo_titulo))
                break
            except (FileNotFoundError, pygame.error):
                continue

        if self.imagem_titulo is not None:
            self.titulo_rect = pygame.Rect(x_titulo, y_titulo, self.imagem_titulo.get_width(), self.imagem_titulo.get_height())
        else:
            self.titulo_rect = pygame.Rect(x_titulo, y_titulo, largura_alvo_titulo, 140)

        self.posicao_titulo = self.titulo_rect.topleft
        self.titulo_anim_rect = self.titulo_rect.copy()
        self.titulo_anim_tempo = 0.0
        self.titulo_surface = self.imagem_titulo if self.imagem_titulo is not None else self.txt_titulo

        sprite_jogar_base = "BVERDEM.png"
        sprite_jogar_hover = "BVERDG.png"
        sprite_jogar_clique = "BVERDEP.png"

        sprite_classe_base = "BYELLM.png"
        sprite_classe_hover = "BYELLG.png"
        sprite_classe_clique = "BYELLP.png"

        sprite_conquistas_base = "BVIOLETM.png"
        sprite_conquistas_hover = "BVIOLETG.png"
        sprite_conquistas_clique = "BVIOLETP.png"

        sprite_config_base = "BAZULM.png"
        sprite_config_hover = "BAZULG.png"
        sprite_config_clique = "BAZULP.png"

        sprite_sair_base = "BREDM.png"
        sprite_sair_hover = "BREDG.png"
        sprite_sair_clique = "BREDP.png"

        largura_botao = 190
        altura_botao = 48
        x_botao = (largura_tela - largura_botao) // 2
        y_inicial_botoes = 245
        espacamento_botoes = 62

        self.botoes = {
            "jogar": Botao(x_botao, y_inicial_botoes + 0 * espacamento_botoes, largura_botao, altura_botao, "JOGAR", (0, 200, 0), (0, 255, 0), 198, 52, cor_texto=(0, 0, 0), fonte_tamanho=22, sprite_base_path=sprite_jogar_base, sprite_hover_path=sprite_jogar_hover, sprite_clique_path=sprite_jogar_clique),
            "classe": Botao(x_botao, y_inicial_botoes + 1 * espacamento_botoes, largura_botao, altura_botao, "VERSO", (200, 200, 0), (255, 255, 0), 198, 52, cor_texto=(0, 0, 0), fonte_tamanho=22, sprite_base_path=sprite_classe_base, sprite_hover_path=sprite_classe_hover, sprite_clique_path=sprite_classe_clique),
            "conquistas": Botao(x_botao, y_inicial_botoes + 2 * espacamento_botoes, largura_botao, altura_botao, "CONQUISTAS", (135, 50, 195), (175, 80, 235), 198, 52, cor_texto=(0, 0, 0), fonte_tamanho=17, sprite_base_path=sprite_conquistas_base, sprite_hover_path=sprite_conquistas_hover, sprite_clique_path=sprite_conquistas_clique),
            "config": Botao(x_botao, y_inicial_botoes + 3 * espacamento_botoes, largura_botao, altura_botao, "OPÇÕES", (0, 120, 210), (0, 160, 250), 198, 52, cor_texto=(0, 0, 0), fonte_tamanho=18, sprite_base_path=sprite_config_base, sprite_hover_path=sprite_config_hover, sprite_clique_path=sprite_config_clique),
            "sair": Botao(x_botao, y_inicial_botoes + 4 * espacamento_botoes, largura_botao, altura_botao, "SAIR", (200, 0, 0), (255, 0, 0), 198, 52, cor_texto=(0, 0, 0), fonte_tamanho=22, sprite_base_path=sprite_sair_base, sprite_hover_path=sprite_sair_hover, sprite_clique_path=sprite_sair_clique),
        }
        self.botao_jogar = self.botoes["jogar"]
        self.botao_classe = self.botoes["classe"]
        self.botao_conquistas = self.botoes["conquistas"]
        self.botao_config = self.botoes["config"]
        self.botao_sair = self.botoes["sair"]
        self.lista_botoes = list(self.botoes.values())

        largura_sw, altura_sw = 80, 40
        x_sw = self.tela.get_width() - largura_sw - 20
        y_sw = 20
        self.switch_2p = Botao(
            x_sw, y_sw, largura_sw, altura_sw, "",
            (120, 120, 120), (180, 180, 180), largura_sw, altura_sw,
            cor_texto=(0, 0, 0), fonte_tamanho=22,
            sprite_base_path="SOFF.png",
            sprite_hover_path="SOFF.png",
            sprite_clique_path="SON.png",
            alternado=True,
            ativo_inicial=False,
        )
        self.switch_2p.sem_texto = True
        self.duas_pessoas = False

        largura_sr = 100
        altura_sr = 40
        y_sr = self.tela.get_height() - altura_sr - 20

        self.botao_salvar = Botao(
            25, y_sr, largura_sr, altura_sr, "SALVAR", (30, 140, 70), (40, 180, 90), 104, 44,
            cor_texto=(0, 0, 0), fonte_tamanho=13,
            sprite_base_path="BVERDEM.png", sprite_hover_path="BVERDG.png", sprite_clique_path="BVERDEP.png"
        )
        self.botao_reset = Botao(
            135, y_sr, largura_sr, altura_sr, "RESET", (160, 40, 40), (200, 50, 50), 104, 44,
            cor_texto=(0, 0, 0), fonte_tamanho=13,
            sprite_base_path="BREDM.png", sprite_hover_path="BREDG.png", sprite_clique_path="BREDP.png"
        )

        self.fonte_feedback = obter_fonte(12)
        self.mensagem_feedback = ""
        self.cor_feedback = (100, 255, 140)
        self.temporizador_feedback = 0

        self.rect_porta_esgoto = pygame.Rect(
            self.posicao_fundo[0] + int(72 * self.escala_fundo),
            self.posicao_fundo[1] + int(375 * self.escala_fundo),
            int(143 * self.escala_fundo),
            int(490 * self.escala_fundo)
        )

        self.rect_porta_cheats = pygame.Rect(
            self.posicao_fundo[0] + int(1045 * self.escala_fundo),
            self.posicao_fundo[1] + int(250 * self.escala_fundo),
            int(107 * self.escala_fundo),
            int(678 * self.escala_fundo)
        )
        self.rect_sewer_access = self.rect_porta_esgoto

    def checar_clique_esgoto(self, evento, posicao_mouse):
        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            if self.botao_salvar.rect.collidepoint(posicao_mouse) or self.botao_reset.rect.collidepoint(posicao_mouse):
                return False
            if self.rect_porta_esgoto.collidepoint(posicao_mouse):
                return True
        return False

    def checar_clique_porta_cheats(self, evento, posicao_mouse):
        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            if self.switch_2p.rect.collidepoint(posicao_mouse):
                return None
            if self.rect_porta_cheats.collidepoint(posicao_mouse):
                if save_global.tem_member_card():
                    return "cheats"
                return None
        return None

    def checar_clique_sewer(self, evento, posicao_mouse):
        return self.checar_clique_esgoto(evento, posicao_mouse)

    def mostrar_feedback(self, texto, cor=(100, 255, 140)):
        self.mensagem_feedback = texto
        self.cor_feedback = cor
        self.temporizador_feedback = 180

    def buscar_botao(self, nome_botao):
        return self.botoes.get(nome_botao.lower())

    def atualizar(self, posicao_mouse, estado_clique_mouse):
        self.titulo_anim_tempo += 0.018

        for botao in self.lista_botoes:
            botao.atualizar(posicao_mouse, estado_clique_mouse)
        self.switch_2p.atualizar(posicao_mouse, estado_clique_mouse)
        self.botao_salvar.atualizar(posicao_mouse, estado_clique_mouse)
        self.botao_reset.atualizar(posicao_mouse, estado_clique_mouse)

        if self.temporizador_feedback > 0:
            self.temporizador_feedback -= 1

        if self.imagem_titulo is not None:
            deslocamento_y = int(math.sin(self.titulo_anim_tempo * 2.2) * 10)
            deslocamento_x = int(math.sin(self.titulo_anim_tempo * 1.4) * 6)
            inclinacao = math.sin(self.titulo_anim_tempo * 1.8) * 4.0

            self.titulo_surface = pygame.transform.rotate(self.imagem_titulo, inclinacao)
            centro_x = self.titulo_rect.centerx + deslocamento_x
            centro_y = self.titulo_rect.centery + deslocamento_y
            self.titulo_anim_rect = self.titulo_surface.get_rect(center=(centro_x, centro_y))
        else:
            pulsacao = 1.0 + math.sin(self.titulo_anim_tempo * 2.2) * 0.025
            titulo_base = pygame.transform.scale(self.txt_titulo, (
                int(self.txt_titulo.get_width() * pulsacao),
                int(self.txt_titulo.get_height() * pulsacao)
            ))
            self.titulo_surface = titulo_base
            self.titulo_anim_rect = titulo_base.get_rect(center=self.titulo_rect.center)
            self.titulo_anim_rect.x += int(math.sin(self.titulo_anim_tempo * 1.2) * 8)

    def desenhar(self):
        if self.imagem_fundo is not None:
            self.tela.blit(self.imagem_fundo, self.posicao_fundo)
        else:
            self.tela.fill((30, 30, 40))

        if self.imagem_titulo is not None:
            self.tela.blit(self.titulo_surface, self.titulo_anim_rect)
        else:
            pygame.draw.rect(self.tela, (80, 80, 200), self.titulo_rect)
            self.tela.blit(self.titulo_surface, self.titulo_anim_rect)

        for botao in self.lista_botoes:
            botao.desenhar(self.tela)
        self.switch_2p.desenhar(self.tela)

        self.botao_salvar.desenhar(self.tela)
        self.botao_reset.desenhar(self.tela)

        if self.temporizador_feedback > 0 and self.mensagem_feedback:
            txt_fb = self.fonte_feedback.render(self.mensagem_feedback, True, self.cor_feedback)
            bg_rect = pygame.Rect(23, 715, txt_fb.get_width() + 8, txt_fb.get_height() + 4)
            pygame.draw.rect(self.tela, (15, 20, 28), bg_rect, border_radius=4)
            self.tela.blit(txt_fb, (27, 717))

TelaMenu = GerenciadorMenu
