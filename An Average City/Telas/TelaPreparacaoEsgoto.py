import pygame

from Entidades.Personagem import personagem
from Sistemas.Fontes import obter_fonte, quebrar_texto
from Sistemas.Inventario import inventario_global
from Sistemas.Recursos import caminho_cenario
from Sistemas.SistemaUI import Botao, TelaBase


FUNDO = (12, 20, 26)
PAINEL = (23, 34, 43)
BORDA = (65, 94, 105)
CIANO = (75, 225, 230)
TEXTO = (235, 243, 246)
TEXTO_SECUNDARIO = (166, 190, 200)


class GerenciadorPreparacaoEsgoto(TelaBase):
    def __init__(self, tela):
        super().__init__(tela, nome="preparacao_esgoto")
        self.verso = "Sobrevivente"
        self.classe = "Físico"
        self.resultado = None
        self.fonte_titulo = obter_fonte(36)
        self.fonte_secao = obter_fonte(15)
        self.fonte_texto = obter_fonte(13)
        self.fonte_menor = obter_fonte(11)

        self.imagem_fundo = None
        try:
            imagem = pygame.image.load(caminho_cenario("Batalha Esgotos.png")).convert()
            self.imagem_fundo = pygame.transform.scale(imagem, (self.largura, self.altura))
        except (FileNotFoundError, pygame.error) as erro:
            print(f"[Aviso] Erro ao carregar preparação do esgoto: {erro}")

        self.overlay = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        self.overlay.fill((5, 12, 18, 175))
        centro_x = self.largura // 2
        self.painel = pygame.Rect(centro_x - 430, 55, 860, 690)
        self.botoes = {
            "loja": Botao(
                centro_x - 385, 550, 370, 60, "VISITAR LOJA",
                (38, 76, 69), (55, 110, 92), 370, 60,
                cor_texto=TEXTO, fonte_tamanho=15,
            ),
            "inventario": Botao(
                centro_x + 15, 550, 370, 60, "ABRIR INVENTÁRIO",
                (36, 59, 80), (52, 88, 115), 370, 60,
                cor_texto=TEXTO, fonte_tamanho=15,
            ),
            "voltar": Botao(
                centro_x - 385, 650, 250, 52, "VOLTAR AO ESGOTO",
                (45, 52, 62), (70, 82, 96), 250, 52,
                cor_texto=TEXTO_SECUNDARIO, fonte_tamanho=13,
            ),
            "lutar": Botao(
                centro_x + 15, 640, 370, 65, "ENFRENTAR DAVID MARTINS",
                (25, 115, 115), (30, 165, 160), 370, 65,
                cor_texto=TEXTO, fonte_tamanho=16,
            ),
        }

    def configurar(self, verso, classe):
        self.verso = verso
        self.classe = classe
        self.resultado = None
        self.botoes["lutar"].definir_texto("ENFRENTAR DAVID MARTINS")
        for botao in self.botoes.values():
            botao.pressionado = False

    def definir_resultado(self, resultado):
        self.resultado = resultado
        self.botoes["lutar"].definir_texto("ENFRENTAR NOVAMENTE")

    def atualizar_eventos(self, evento, posicao_mouse):
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            return "voltar"
        for acao, botao in self.botoes.items():
            if botao.checar_clique(evento, posicao_mouse):
                return acao
        return None

    def atualizar(self, posicao_mouse, estado_clique_mouse):
        for botao in self.botoes.values():
            botao.atualizar(posicao_mouse, estado_clique_mouse)

    def _texto(self, texto, posicao, fonte=None, cor=TEXTO, largura=None):
        fonte = fonte or self.fonte_texto
        linhas = quebrar_texto(texto, fonte, largura) if largura else [texto]
        x, y = posicao
        for linha in linhas:
            self.tela.blit(fonte.render(linha, True, cor), (x, y))
            y += fonte.get_linesize() + 4
        return y

    def desenhar(self):
        if self.imagem_fundo is not None:
            self.tela.blit(self.imagem_fundo, (0, 0))
        else:
            self.tela.fill(FUNDO)
        self.tela.blit(self.overlay, (0, 0))
        pygame.draw.rect(self.tela, PAINEL, self.painel, border_radius=12)
        pygame.draw.rect(self.tela, BORDA, self.painel, 2, border_radius=12)

        x = self.painel.x + 45
        self._texto("DESAFIO DOS ESGOTOS", (x, 80), self.fonte_secao, CIANO)
        self._texto("DAVID MARTINS", (x, 116), self.fonte_titulo)
        mensagens = {
            "vitoria": ("David Martins foi derrotado. Você pode se preparar para outro confronto.", (105, 230, 150)),
            "derrota": ("David Martins venceu. Reorganize seu equipamento antes de tentar novamente.", (255, 145, 130)),
            "fugiu": ("Você recuou da luta. Prepare-se antes de voltar à arena.", (245, 215, 115)),
        }
        mensagem, cor_mensagem = mensagens.get(
            self.resultado,
            ("Uma presença aguarda nas galerias. Prepare-se antes de entrar na luta.", TEXTO_SECUNDARIO),
        )
        self._texto(mensagem, (x, 185), cor=cor_mensagem, largura=770)
        pygame.draw.line(self.tela, BORDA, (x, 250), (self.painel.right - 45, 250), 1)

        self._texto("SEU PERSONAGEM", (x, 274), self.fonte_secao, CIANO)
        self._texto(f"{self.verso}  /  {self.classe}", (x, 311), largura=355)
        self._texto(f"NÍVEL {personagem.nivel}", (x, 355), self.fonte_secao)
        self._texto(f"VIDA  {personagem.hp}/{personagem.max_hp}", (x, 397), cor=(140, 235, 170))
        self._texto(f"MANA  {personagem.mp}/{personagem.max_mp}", (x, 432), cor=(130, 195, 255))
        self._texto(f"SUCATAS  {inventario_global.materiais_totais()}", (x, 467), cor=(245, 215, 115))

        x_kit = self.painel.centerx + 15
        self._texto("PROVISÕES", (x_kit, 274), self.fonte_secao, CIANO)
        consumiveis = [item for item in inventario_global.consumiveis if item.quantidade > 0]
        y = 313
        if not consumiveis:
            self._texto("Sem consumíveis. Visite a loja.", (x_kit, y), cor=TEXTO_SECUNDARIO, largura=370)
        for item in consumiveis[:4]:
            y = self._texto(f"{item.quantidade}x {item.nome}", (x_kit, y), self.fonte_menor, largura=365) + 10
        if len(consumiveis) > 4:
            self._texto(f"+{len(consumiveis) - 4} tipos no inventário", (x_kit, y), self.fonte_menor, TEXTO_SECUNDARIO)

        for botao in self.botoes.values():
            botao.desenhar(self.tela)
        self._texto(
            "Equipe seus itens e distribua os pontos de atributo no inventário.",
            (x, 516), self.fonte_menor, TEXTO_SECUNDARIO,
        )
