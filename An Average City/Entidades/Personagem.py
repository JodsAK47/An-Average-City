import pygame
from Sistemas.Recursos import caminho_imagem
from Entidades.EntidadeCombate import EntidadeCombate

class Personagem(EntidadeCombate):
    def __init__(self, x, y, nome_imagem="pixil.png", nome="Jogador 1"):
        super().__init__(nome=nome, max_hp=100, max_mp=10, is_player=True)
        self.nome = nome
        self.max_hp = 100
        self.hp = 100
        self.max_mp = 10
        self.mp = 0

        self.nivel = 1
        self.xp = 0
        self.pontos_atributo = 0
        self.atributos = {"For": 1, "Agi": 1, "Con": 1, "Sab": 1, "Int": 1, "Sor": 1}
        self.ataques = []
        self.ultimates_desbloqueadas = set()
        self.minions = []
        self.estatisticas_minions = {
            "invocacoes": 0,
            "dano_total_minions": 0,
            "abates_minions": 0,
        }

        self.congelado = False
        self.atordoado = False
        self.bloqueando = False
        self.recuperando = False
        self.focado = False
        self.is_player = True
        self.talentos = set()
        self.god_mode = False
        self.nome_imagem = nome_imagem

        try:
            self.imagem_original = pygame.image.load(caminho_imagem(nome_imagem))
            w_orig, h_orig = self.imagem_original.get_size()
            altura_desejada = 115
            largura_desejada = int(w_orig * (altura_desejada / max(1, h_orig)))
            self.imagem = pygame.transform.scale(self.imagem_original, (largura_desejada, altura_desejada))
            # skins e aliados devem ficar virados para a direita
            self.imagem = self.imagem
        except (pygame.error, FileNotFoundError) as e:
            print(f"⚠️ Erro ao carregar imagem: {e}")
            self.imagem = pygame.Surface((100, 115))
            self.imagem.fill((0, 200, 100))

        self.rect = self.imagem.get_rect(topleft=(x, y))
        self.convertida = False

    def tem_talento(self, id_talento):
        return id_talento in self.talentos

    def obter_bonus_equipamento(self, atributo):
        from Sistemas.Inventario import inventario_global
        return inventario_global.obter_bonus_atributo(atributo)

    def obter_atributo_total(self, atributo):
        base = int(self.atributos.get(atributo, 1))
        return base + self.obter_bonus_equipamento(atributo)

    def trocar_skin(self, nova_imagem):
        self.nome_imagem = nova_imagem
        try:
            self.imagem_original = pygame.image.load(caminho_imagem(nova_imagem))
            w_orig, h_orig = self.imagem_original.get_size()
            altura_desejada = 115
            largura_desejada = int(w_orig * (altura_desejada / max(1, h_orig)))
            self.imagem = pygame.transform.scale(self.imagem_original, (largura_desejada, altura_desejada))
            # skins do jogador sempre ficam para a direita
            self.rect.size = self.imagem.get_size()
            self.convertida = False
        except (pygame.error, FileNotFoundError) as e:
            print(f"⚠️ Erro ao carregar nova skin '{nova_imagem}': {e}")

    def tem_ultimate_desbloqueada(self, verso, classe=None):
        nodo_req = {"Sobrevivente": "S4", "Agente": "A4", "Feiticeiro": "F4", "Invocador": "I4"}.get(verso)
        talentos = getattr(self, "talentos", set())
        if nodo_req and nodo_req in talentos:
            return True
        if classe == "Invocador" and "I4" in talentos:
            return True
        ultimates = getattr(self, "ultimates_desbloqueadas", set())
        if verso in ultimates:
            return True
        if classe and (verso, classe) in ultimates:
            return True
        return False

    def resetar(self, resetar_cheats: bool = False):
        if resetar_cheats:
            talentos_salvos = set()
            ultimates_salvas = set()
            skin_salva = 'pixil.png'
            god_mode_salvo = False
        else:
            talentos_salvos = set(getattr(self, 'talentos', set()))
            ultimates_salvas = set(getattr(self, 'ultimates_desbloqueadas', set()))
            skin_salva = getattr(self, 'nome_imagem', 'pixil.png')
            god_mode_salvo = getattr(self, 'god_mode', False)
        nome_salvo = getattr(self, 'nome', 'Jogador 1')
        self.__init__(self.rect.x, self.rect.y, nome_imagem=skin_salva, nome=nome_salvo)
        self.talentos = talentos_salvos
        self.ultimates_desbloqueadas = ultimates_salvas
        self.god_mode = god_mode_salvo

    def desenhar(self, tela):
        if not self.convertida:
            try:
                self.imagem = self.imagem.convert_alpha()
            except pygame.error:
                pass
            self.convertida = True

        tela.blit(self.imagem, self.rect)

personagem = Personagem(150, 350, "pixil.png", nome="Jogador 1")
personagem.is_player = True
