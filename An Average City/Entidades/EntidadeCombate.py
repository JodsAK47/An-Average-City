"""
Superclasse base para todas as entidades de combate (Jogadores, Inimigos, Minions, Dispositivos).
Implementa propriedades comuns e polimorfismo para processamento de turnos.
"""

from typing import Dict, Any, Optional
import pygame


class EntidadeCombate(pygame.sprite.Sprite):
    def __init__(
        self,
        nome: str,
        max_hp: int,
        max_mp: int = 0,
        atributos: Optional[Dict[str, int]] = None,
        is_player: bool = False,
    ):
        super().__init__()
        self.nome = nome
        self.max_hp = max(1, int(max_hp))
        self.hp = self.max_hp
        self.max_mp = max(0, int(max_mp))
        self.mp = 0

        self.atributos = dict(atributos) if atributos else {
            "For": 1, "Agi": 1, "Con": 1, "Sab": 1, "Int": 1, "Sor": 1
        }
        self.is_player = bool(is_player)

        # Status de controle de grupo (CC) e combate
        self.congelado = False
        self.atordoado = False
        self.queimando = False
        self.eletrocutado = False
        self.envenenado = False
        self.cego = False
        self.turnos_fogo = 0
        self.turnos_eletrocutado = 0
        self.turnos_veneno = 0
        self.turnos_cegueira = 0
        self.bloqueando = False
        self.recuperando = False
        self.focado = False
        self.god_mode = False
        self.efeitos_ativos = {}

        self.rect = pygame.Rect(0, 0, 100, 100)
        self.imagem = None
        self.imagem_base = None
        self.arquivo_imagem = None
        self.orientacao_nativa = None
        self.direcao_olhar = "leste"
        self.convertida = False

    @property
    def esta_vivo(self) -> bool:
        return self.hp > 0

    def tem_talento(self, id_talento: str) -> bool:
        return False

    def obter_bonus_equipamento(self, atributo: str) -> int:
        return 0

    def obter_atributo_total(self, atributo: str) -> int:
        base = int(self.atributos.get(atributo, 1))
        return base + self.obter_bonus_equipamento(atributo)

    def receber_dano(self, quantidade: int) -> int:
        if self.god_mode:
            return 0
        dano_real = max(0, int(quantidade))
        if self.bloqueando:
            dano_real = max(1, dano_real // 2)
        self.hp = max(0, self.hp - dano_real)
        return dano_real

    def curar_hp(self, quantidade: int) -> int:
        cura = max(0, int(quantidade))
        hp_anterior = self.hp
        self.hp = min(self.max_hp, self.hp + cura)
        return self.hp - hp_anterior

    def curar_mp(self, quantidade: int) -> int:
        rec = max(0, int(quantidade))
        mp_anterior = self.mp
        self.mp = min(self.max_mp, self.mp + rec)
        return self.mp - mp_anterior

    def gastar_mp(self, quantidade: int) -> bool:
        custo = max(0, int(quantidade))
        if self.mp >= custo:
            self.mp -= custo
            return True
        return False

    def aplicar_status(self, efeito: str):
        if not efeito:
            return
        efeito_str = str(efeito).strip().lower()
        if "congel" in efeito_str:
            self.congelado = True
        elif "atordo" in efeito_str or "stun" in efeito_str:
            self.atordoado = True
        elif "queim" in efeito_str or "fogo" in efeito_str:
            self.queimando = True
            self.turnos_fogo = 2
        elif "eletroc" in efeito_str or "choque" in efeito_str:
            self.eletrocutado = True
            self.turnos_eletrocutado = 2
            self.atordoado = True
        elif "venen" in efeito_str:
            self.envenenado = True
            self.turnos_veneno = 3
        elif "ceg" in efeito_str or "blind" in efeito_str:
            self.cego = True
            self.turnos_cegueira = 2

    def limpar_status(self):
        self.congelado = False
        self.atordoado = False
        self.bloqueando = False
        self.recuperando = False
        self.focado = False
        self.cego = False
        self.turnos_cegueira = 0

    def virar_para(self, direcao: str, forcar: bool = False) -> bool:
        """
        Altera para qual lado a entidade está virada ('leste' ou 'oeste').
        Consulta o SistemaOrientacao para respeitar a orientação nativa do sprite.
        Preserva a posição central do rect para evitar deslocamento indesejado.
        """
        from Sistemas.SistemaOrientacao import sistema_orientacao
        direcao_normalizada = sistema_orientacao.normalizar_direcao(direcao)
        if not forcar and getattr(self, "direcao_olhar", None) == direcao_normalizada and getattr(self, "imagem", None) is not None:
            return False

        imagem_base = getattr(self, "imagem_base", None)
        if imagem_base is None:
            self.direcao_olhar = direcao_normalizada
            return False

        centro_anterior = self.rect.center if hasattr(self, "rect") and self.rect else None
        arquivo = getattr(self, "arquivo_imagem", getattr(self, "nome_imagem", None))
        nativa = getattr(self, "orientacao_nativa", None)

        self.imagem = sistema_orientacao.aplicar_orientacao(imagem_base, arquivo, direcao_normalizada, nativa)
        self.direcao_olhar = direcao_normalizada
        self.convertida = False

        if centro_anterior and hasattr(self, "rect") and self.rect:
            self.rect = self.imagem.get_rect(center=centro_anterior)
        return True

    def olhar_para(self, direcao: str) -> bool:
        """Alias intuitivo para virar_para."""
        return self.virar_para(direcao)

    def olhar_para_alvo(self, alvo: Any) -> bool:
        """
        Vira a entidade para encarar horizontalmente o alvo informado.
        Aceita outra entidade, um pygame.Rect ou tupla/lista (x, y).
        """
        if alvo is None or not hasattr(self, "rect"):
            return False
        alvo_x = None
        if hasattr(alvo, "rect") and alvo.rect:
            alvo_x = alvo.rect.centerx
        elif isinstance(alvo, (tuple, list)) and len(alvo) >= 1:
            alvo_x = alvo[0]
        elif hasattr(alvo, "x"):
            alvo_x = alvo.x

        if alvo_x is None:
            return False

        nova_direcao = "oeste" if alvo_x < self.rect.centerx else "leste"
        return self.virar_para(nova_direcao)

    def executar_turno(self, contexto: Any = None):
        """
        Método abstrato/polimórfico executado na vez da entidade.
        Subclasses devem sobrescrever conforme sua IA ou regras.
        """
        pass
