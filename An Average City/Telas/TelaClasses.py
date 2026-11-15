import pygame
from Sistemas.SistemaUI import Botao, TelaBase
from Sistemas.Fontes import obter_fonte, quebrar_texto

FUNDO = (25, 30, 42)
TEXTO = (235, 235, 235)
TEXTO_SECUNDARIO = (180, 190, 205)
AZUL_DESTAQUE = (76, 98, 122)

CORES_CLASSES = {
    "Físico": (189, 118, 52),
    "Distância": (186, 52, 52),
    "Magia": (128, 78, 168),
    "Invocador": (52, 168, 148),
}

ATRIBUTO_BASE_CLASSE = {
    "Físico": "Força (FOR)",
    "Distância": "Agilidade (AGI)",
    "Magia": "Intelecto (INT)",
    "Invocador": "Sabedoria (SAB)",
}

class GerenciadorClasses(TelaBase):
    def __init__(self, tela):
        super().__init__(tela, nome="classes")
        self.tela = tela
        self.fonte_titulo = obter_fonte(24)
        self.fonte_card = obter_fonte(18)
        self.fonte_desc = obter_fonte(16)
        self.fonte_attr = obter_fonte(12)
        self.aviso = "Escolha uma classe"
        self.voltar_clicado = False

        self.opcoes = ["Físico", "Distância", "Magia", "Invocador"]
        self.classe_atual = "Físico"

        self.botao_voltar = Botao(60, 700, 180, 45, "VOLTAR", (55, 62, 78), (90, 100, 120), 185, 50, cor_texto=TEXTO, fonte_tamanho=16)
        self.botao_selecionar = Botao(760, 700, 180, 45, "CONFIRMAR", AZUL_DESTAQUE, (95, 120, 145), 185, 50, cor_texto=TEXTO, fonte_tamanho=16)

        self.rects = {
            "Físico": pygame.Rect(61, 180, 200, 430),
            "Distância": pygame.Rect(287, 180, 200, 430),
            "Magia": pygame.Rect(513, 180, 200, 430),
            "Invocador": pygame.Rect(739, 180, 200, 430),
        }

    def atualizar_eventos(self, evento, posicao_mouse):
        if self.botao_voltar.checar_clique(evento, posicao_mouse):
            self.voltar_clicado = True
            return None

        if self.botao_selecionar.checar_clique(evento, posicao_mouse):
            return self.classe_atual

        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            for nome, rect in self.rects.items():
                if rect.collidepoint(posicao_mouse):
                    self.classe_atual = nome
                    return None

        return None

    def atualizar(self, posicao_mouse, estado_clique_mouse):
        self.botao_voltar.atualizar(posicao_mouse, estado_clique_mouse)
        self.botao_selecionar.atualizar(posicao_mouse, estado_clique_mouse)

    def desenhar(self):
        self.tela.fill(FUNDO)

        titulo = self.fonte_titulo.render("SELECIONE A CLASSE", True, TEXTO)
        self.tela.blit(titulo, titulo.get_rect(center=(500, 70)))

        subtitulo = self.fonte_desc.render("Escolha a forma de combate do seu personagem.", True, TEXTO_SECUNDARIO)
        self.tela.blit(subtitulo, subtitulo.get_rect(center=(500, 110)))

        if getattr(self, "aviso", None):
            aviso_txt = self.fonte_desc.render(self.aviso, True, (255, 230, 100))
            self.tela.blit(aviso_txt, aviso_txt.get_rect(center=(500, 145)))

        for nome in self.opcoes:
            rect = self.rects[nome]
            selecionado = nome == self.classe_atual
            cor_fundo = (42, 50, 64) if not selecionado else (58, 70, 90)
            pygame.draw.rect(self.tela, cor_fundo, rect, border_radius=18)
            pygame.draw.rect(self.tela, CORES_CLASSES[nome], rect, 3, border_radius=18)

            if selecionado:
                pygame.draw.rect(self.tela, (255, 255, 120), rect.inflate(-12, -12), 3, border_radius=16)

            circulo = pygame.Rect(rect.centerx - 45, rect.y + 35, 90, 90)
            pygame.draw.circle(self.tela, CORES_CLASSES[nome], circulo.center, 36)
            pygame.draw.circle(self.tela, (255, 255, 255), circulo.center, 36, 2)

            fonte_nome = self.fonte_card if len(nome) >= 8 else self.fonte_titulo
            nome_render = fonte_nome.render(nome.upper(), True, TEXTO)
            self.tela.blit(nome_render, nome_render.get_rect(center=(rect.centerx, rect.y + 165)))

            attr_txt = self.fonte_attr.render(f"Base: {ATRIBUTO_BASE_CLASSE[nome]}", True, CORES_CLASSES[nome])
            self.tela.blit(attr_txt, attr_txt.get_rect(center=(rect.centerx, rect.y + 198)))

            descricao = {
                "Físico": "Ataques fortes e diretos, com potência em corpo a corpo.",
                "Distância": "Precisão e alcance, com dano a longa distância.",
                "Magia": "Poder arcano e habilidades especiais de controle.",
                "Invocador": "Usa Sabedoria para invocar minions que lutam automaticamente.",
            }[nome]
            linhas_descricao = quebrar_texto(descricao, self.fonte_desc, rect.width - 26)
            inicio_y = rect.y + 235
            for indice, linha in enumerate(linhas_descricao):
                texto = self.fonte_desc.render(linha, True, TEXTO_SECUNDARIO)
                self.tela.blit(texto, (rect.x + 13, inicio_y + indice * 20))

        self.botao_voltar.desenhar(self.tela)
        self.botao_selecionar.desenhar(self.tela)
