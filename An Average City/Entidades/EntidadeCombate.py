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
        self.envenenado = False
        self.turnos_fogo = 0
        self.turnos_veneno = 0
        self.bloqueando = False
        self.recuperando = False
        self.focado = False
        self.god_mode = False
        self.efeitos_ativos = {}

        self.rect = pygame.Rect(0, 0, 100, 100)
        self.imagem = None

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
        elif "venen" in efeito_str:
            self.envenenado = True
            self.turnos_veneno = 3

    def limpar_status(self):
        self.congelado = False
        self.atordoado = False
        self.bloqueando = False
        self.recuperando = False
        self.focado = False

    def executar_turno(self, contexto: Any = None):
        """
        Método abstrato/polimórfico executado na vez da entidade.
        Subclasses devem sobrescrever conforme sua IA ou regras.
        """
        pass
