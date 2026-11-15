import pygame
from Sistemas.Recursos import caminho_imagem
from Sistemas.Fontes import obter_fonte
from Entidades.EntidadeCombate import EntidadeCombate, aplicar_mascara_transparencia


class Santuario(EntidadeCombate):
    """
    Pequeno Santuário invocado pela Ultimate de Sukuna (Santuário Malevolente).
    - Possui tamanho semelhante a uma invocação (altura aproximada de 85px).
    - Começa com duração de 4 turnos.
    - Perde 1 ponto de duração por rodada e 1 ponto por ataque recebido.
    - Causa dano contínuo em área utilizando a sprite de Cortes com tremor de tela.
    """
    def __init__(self, x=580, y=405, dono=None, lado="inimigo"):
        self.dono = dono
        self.lado = lado  # 'inimigo' se conjurado por Sukuna chefe, 'aliado' se conjurado por jogador
        self.is_santuario = True
        self.is_player = False
        self.is_minion = (lado == "aliado")
        self.tipo = "invocacao"
        self.classe = "Magia"
        self.verso = "Feiticeiro"

        # Inicializa atributos específicos antes de chamar super()
        # pois EntidadeCombate.__init__ atribui self.hp = max_hp, acionando o setter
        self.max_ataques = 4
        self.ataques_recebidos = 0
        self.duracao_maxima = 4
        self.duracao = 4
        self.max_hp = 100
        self._hp = 100
        self.max_mp = 0
        self.mp = 0

        super().__init__(nome="Pequeno Santuário", max_hp=100, max_mp=0, is_player=(lado == "aliado"))

        self.congelado = False
        self.atordoado = False
        self.xp = 80
        self.atributos = {
            "For": 8,
            "Agi": 5,
            "Con": 10,
            "Sab": 10,
            "Int": 12,
            "Sor": 1,
        }
        self.ataques = ["Cortes Malevolentes"]

        self._carregar_sprite()
        self.rect = self.imagem.get_rect(center=(x, y))
        self.fonte_nome = obter_fonte(11)

    def _carregar_sprite(self):
        altura_desejada = 85  # Semelhante a uma invocação (Minion usa 82)
        try:
            caminho = caminho_imagem("Santuario.png")
            img_original = pygame.image.load(caminho)
            w_orig, h_orig = img_original.get_size()
            largura_desejada = max(55, int(w_orig * (altura_desejada / max(1, h_orig))))
            img_escala = pygame.transform.scale(img_original, (largura_desejada, altura_desejada)).convert_alpha()
            aplicar_mascara_transparencia(img_escala, corte_zero=18, fade_max=50)
            self.imagem = img_escala
        except Exception as e:
            print(f"[Aviso] Falha ao carregar sprite Santuario.png: {e}")
            self.imagem = pygame.Surface((64, altura_desejada), pygame.SRCALPHA)
            pygame.draw.rect(self.imagem, (180, 30, 45), (0, 0, 64, altura_desejada), border_radius=6)

    @property
    def hp(self):
        return getattr(self, "_hp", getattr(self, "max_hp", 100))

    @hp.setter
    def hp(self, novo_valor):
        if not hasattr(self, "_hp"):
            self._hp = int(novo_valor)
            return

        if not hasattr(self, "ataques_recebidos"):
            self.ataques_recebidos = 0
        if not hasattr(self, "max_ataques"):
            self.max_ataques = 4
        if not hasattr(self, "duracao"):
            self.duracao = 4
        if not hasattr(self, "duracao_maxima"):
            self.duracao_maxima = 4

        if novo_valor < self._hp:
            # Qualquer ataque recebido também reduz a duração do santuário em 1.
            self.ataques_recebidos = min(self.max_ataques, self.ataques_recebidos + 1)
            self.duracao = max(0, self.duracao - 1)
            duracao_max = max(1, self.duracao_maxima)
            self._hp = max(0, int((self.duracao / duracao_max) * 100))
            if self.duracao <= 0:
                self._hp = 0
        else:
            self._hp = min(getattr(self, "max_hp", 100), max(0, int(novo_valor)))

    def golpes_restantes(self):
        return max(0, int(getattr(self, "duracao", 0)))

    def perder_duracao_rodada(self):
        """
        Perde 1 ponto de duração no fim de cada rodada completa.
        Quando a duração chega a 0, o santuário se desfaz.
        """
        self.duracao = max(0, int(getattr(self, "duracao", 4)) - 1)
        duracao_max = max(1, int(getattr(self, "duracao_maxima", 4)))
        self._hp = max(0, int((self.duracao / duracao_max) * 100))
        if self.duracao <= 0:
            self._hp = 0
        return self.duracao

    def receber_dano(self, quantidade):
        dano_solicitado = int(quantidade)
        if dano_solicitado <= 0 or getattr(self, "_hp", 0) <= 0 or getattr(self, "duracao", 0) <= 0:
            return 0
        # Cada ataque recebido válido reduz a duração do santuário em 1 golpe.
        self.hp = self._hp - 1
        return int(getattr(self, "max_hp", 100) * 0.25)

    def obter_habilidade(self, nome=None):
        from Entidades.Minion import criar_habilidade_minion
        return criar_habilidade_minion("Cortes Malevolentes", self.verso)

    def desenhar(self, tela, desenhar_nome=False):
        if getattr(self, "_hp", 0) > 0:
            tela.blit(self.imagem, self.rect)
            if desenhar_nome:
                txt = self.fonte_nome.render(
                    f"{self.nome} [Dur: {getattr(self, 'duracao', 4)} | {self.golpes_restantes()}/4]",
                    True,
                    (255, 130, 130)
                )
                tela.blit(txt, (self.rect.centerx - txt.get_width() // 2, self.rect.y - 18))
