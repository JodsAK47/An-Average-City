"""
Sistema de Orientação de Sprites (Facing)
Gerencia de forma centralizada e definitiva para qual lado cada sprite do jogo
foi desenhada originalmente (orientação nativa) e se precisa ser invertida
horizontalmente (flip) para olhar na direção desejada (Leste ou Oeste).
"""

from pathlib import Path
from typing import Dict, Optional, Any
import json
import pygame

from Sistemas.Recursos import caminho_dados


class OrientacaoNativa:
    DIREITA = "leste"
    ESQUERDA = "oeste"
    FRONTAL = "frontal"
    LESTE = "leste"
    OESTE = "oeste"


class SistemaOrientacao:
    """
    Controlador central de orientação e espelhamento de sprites.
    Consulta 'Dados/orientacao_sprites.json' e fornece métodos simples
    para EntidadeCombate, Inimigo, Minion e Personagem.
    """

    _INSTANCIA = None

    def __new__(cls, *args, **kwargs):
        if cls._INSTANCIA is None:
            cls._INSTANCIA = super().__new__(cls)
            cls._INSTANCIA._inicializado = False
        return cls._INSTANCIA

    def __init__(self):
        if getattr(self, "_inicializado", False):
            return
        self._inicializado = True
        self._cache_orientacoes: Dict[str, str] = {}
        self.carregar_configuracao()

    @staticmethod
    def normalizar_direcao(direcao: Any) -> str:
        """
        Normaliza qualquer variante de string para 'leste', 'oeste' ou 'frontal'.
        Exemplos: 'direita', 'east', 'right' -> 'leste'
                  'esquerda', 'west', 'left' -> 'oeste'
        """
        if not direcao:
            return OrientacaoNativa.LESTE
        d = str(direcao).strip().lower()
        if d in ("leste", "direita", "east", "right", "d"):
            return OrientacaoNativa.LESTE
        if d in ("oeste", "esquerda", "west", "left", "e"):
            return OrientacaoNativa.OESTE
        if d in ("frontal", "centro", "front", "f", "meio"):
            return OrientacaoNativa.FRONTAL
        return OrientacaoNativa.LESTE

    @staticmethod
    def _normalizar_nome_arquivo(arquivo_ou_nome: Any) -> str:
        if not arquivo_ou_nome:
            return ""
        # Extrai apenas o nome base (ex: 'Sprites/Inimigos/Hound.png' -> 'hound.png')
        p = Path(str(arquivo_ou_nome))
        return p.name.strip().lower()

    def carregar_configuracao(self):
        """
        Carrega o dicionário de orientações de 'orientacao_sprites.json'.
        Garante um conjunto de valores padrão caso o arquivo não exista ou falhe.
        """
        padroes = {
            "pixil.png": "leste",
            "pixil_cyber.png": "leste",
            "pixil_ouro.png": "leste",
            "pixil_sombra.png": "leste",
            "cyborg skin.png": "leste",
            "abelha.png": "leste",
            "hound.png": "leste",
            "passaro.png": "leste",
            "passaro_olhudo.png": "leste",
            "drone.png": "leste",
            "torreta.png": "leste",
            "cachorro.png": "leste",
            "nue.png": "leste",
            "confinamento.png": "leste",
            "confinamento_destruido.png": "leste",
            "jogo.png": "leste",
            "sukuna.png": "leste",
            "maldição 4.png": "leste",
            "maldicao 4.png": "leste",
            "mahoraga.png": "frontal",
            "santuario.png": "frontal",
            "spike.png": "frontal",
            "spike desarmada.png": "frontal",
        }
        self._cache_orientacoes = padroes.copy()

        try:
            caminho = caminho_dados("orientacao_sprites.json")
            if Path(caminho).exists():
                with open(caminho, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                for chave, item in dados.items():
                    if chave.startswith("_"):
                        continue
                    chave_norm = self._normalizar_nome_arquivo(chave)
                    if isinstance(item, dict):
                        nativa = item.get("orientacao_nativa", "direita")
                    else:
                        nativa = str(item)
                    self._cache_orientacoes[chave_norm] = self.normalizar_direcao(nativa)
        except Exception as e:
            print(f"[Aviso] Erro ao carregar orientacao_sprites.json: {e}")

    def registrar_sprite(self, arquivo_imagem: str, orientacao_nativa: str):
        """Permite registrar ou sobrescrever dinamicamente a orientação de uma sprite."""
        chave = self._normalizar_nome_arquivo(arquivo_imagem)
        self._cache_orientacoes[chave] = self.normalizar_direcao(orientacao_nativa)

    def obter_orientacao_nativa(
        self, arquivo_imagem: Optional[str], fallback: str = "direita"
    ) -> str:
        """
        Retorna a orientação nativa ('leste', 'oeste' ou 'frontal') da sprite dada.
        """
        if not arquivo_imagem:
            return self.normalizar_direcao(fallback)

        chave = self._normalizar_nome_arquivo(arquivo_imagem)
        if chave in self._cache_orientacoes:
            return self._cache_orientacoes[chave]

        # Tenta sem extensão ou com busca parcial
        stem = Path(chave).stem
        for k, v in self._cache_orientacoes.items():
            if Path(k).stem == stem:
                return v

        return self.normalizar_direcao(fallback)

    def precisa_flip(
        self,
        arquivo_imagem: Optional[str],
        direcao_desejada: str,
        orientacao_nativa: Optional[str] = None,
    ) -> bool:
        """
        Determina se uma sprite precisa de flip horizontal para encarar a direção desejada.

        Regras:
        - Frontal: nunca requer flip (retorna False).
        - Nativa Leste (virada para direita): requer flip se desejar olhar para Oeste (esquerda).
        - Nativa Oeste (virada para esquerda): requer flip se desejar olhar para Leste (direita).
        """
        desejada = self.normalizar_direcao(direcao_desejada)
        if desejada == OrientacaoNativa.FRONTAL:
            return False

        if orientacao_nativa is not None:
            nativa = self.normalizar_direcao(orientacao_nativa)
        else:
            nativa = self.obter_orientacao_nativa(arquivo_imagem)

        if nativa == OrientacaoNativa.FRONTAL:
            return False

        if nativa == OrientacaoNativa.LESTE:
            return desejada == OrientacaoNativa.OESTE

        if nativa == OrientacaoNativa.OESTE:
            return desejada == OrientacaoNativa.LESTE

        return False

    def aplicar_orientacao(
        self,
        imagem_base: pygame.Surface,
        arquivo_imagem: Optional[str],
        direcao_desejada: str,
        orientacao_nativa: Optional[str] = None,
    ) -> pygame.Surface:
        """
        Retorna uma nova Surface corretamente orientada para direcao_desejada.
        Se precisa_flip for verdadeiro, executa pygame.transform.flip(imagem_base, True, False).
        Caso contrário, retorna imagem_base.copy().
        """
        if imagem_base is None:
            return None

        deve_inverter = self.precisa_flip(
            arquivo_imagem, direcao_desejada, orientacao_nativa
        )
        if deve_inverter:
            return pygame.transform.flip(imagem_base, True, False)
        return imagem_base.copy()


# Instância global para uso direto
sistema_orientacao = SistemaOrientacao()
