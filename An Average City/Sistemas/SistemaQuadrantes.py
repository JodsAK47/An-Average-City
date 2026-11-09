"""
Sistema de Quadrantes e Gerenciamento de Orientação de Inimigos
Divide a tela em dois quadrantes (Leste e Oeste) e gerencia para qual lado
as entidades/inimigos estão viradas com base no seu ponto na tela.
"""

from typing import Tuple, Union, Optional, Dict, Any
import pygame


class Quadrante:
    OESTE = "oeste"  # Lado esquerdo da tela (0 <= x < divisor)
    LESTE = "leste"  # Lado direito da tela (divisor <= x <= largura)


class DirecaoOlhar:
    OESTE = "oeste"       # Olhando para a esquerda (flip horizontal)
    LESTE = "leste"       # Olhando para a direita (sprite original)
    ESQUERDA = "oeste"
    DIREITA = "leste"
    FRONTAL = "frontal"


class SistemaQuadrantes:
    """
    Sistema que analisa a posição de entidades na tela, categoriza em quadrantes
    (Leste / Oeste) e gerencia automaticamente a orientação do sprite (facing).
    """

    def __init__(self, largura_padrao: int = 1000):
        self.largura_padrao = largura_padrao

    def _obter_largura_efetiva(self, largura_tela: Optional[int] = None) -> int:
        if largura_tela is not None and largura_tela > 0:
            return largura_tela
        
        # Tenta obter a largura da tela ativa no pygame se disponível
        superficie = pygame.display.get_surface()
        if superficie is not None:
            w = superficie.get_width()
            if w > 0:
                return w
                
        return self.largura_padrao

    def obter_ponto(self, entidade_ou_pos: Any) -> Tuple[int, int]:
        """
        Extrai as coordenadas (x, y) de uma entidade ou tupla/lista.
        Usa o centro do rect quando disponível para maior precisão visual.
        """
        if hasattr(entidade_ou_pos, "rect") and isinstance(entidade_ou_pos.rect, pygame.Rect):
            return entidade_ou_pos.rect.center
        if isinstance(entidade_ou_pos, (tuple, list)) and len(entidade_ou_pos) >= 2:
            return int(entidade_ou_pos[0]), int(entidade_ou_pos[1])
        if hasattr(entidade_ou_pos, "x") and hasattr(entidade_ou_pos, "y"):
            return int(entidade_ou_pos.x), int(entidade_ou_pos.y)
        return (0, 0)

    def identificar_quadrante(
        self,
        entidade_ou_pos: Any,
        largura_tela: Optional[int] = None
    ) -> str:
        """
        Verifica em qual quadrante (Oeste ou Leste) o ponto/entidade se encontra.
        - Oeste: x < (largura_tela / 2)
        - Leste: x >= (largura_tela / 2)
        """
        largura = self._obter_largura_efetiva(largura_tela)
        divisor = largura / 2.0
        px, _ = self.obter_ponto(entidade_ou_pos)

        if px < divisor:
            return Quadrante.OESTE
        return Quadrante.LESTE

    def obter_detalhes_posicao(
        self,
        entidade_ou_pos: Any,
        largura_tela: Optional[int] = None,
        altura_tela: Optional[int] = 600
    ) -> Dict[str, Any]:
        """
        Retorna informações completas sobre o ponto da tela:
        - coordenadas exatas (x, y)
        - quadrante atual ('oeste' ou 'leste')
        - divisor central da tela (metade da largura)
        - distância relativa ao centro
        - percentual da largura horizontal (0.0 a 1.0)
        - direção sugerida de combate
        """
        largura = self._obter_largura_efetiva(largura_tela)
        divisor = largura / 2.0
        px, py = self.obter_ponto(entidade_ou_pos)
        quadrante = Quadrante.OESTE if px < divisor else Quadrante.LESTE

        percentual_x = max(0.0, min(1.0, px / float(largura))) if largura > 0 else 0.5
        distancia_centro_x = px - divisor

        # Direção sugerida em combate (olhar em direção ao centro)
        direcao_sugerida = DirecaoOlhar.OESTE if quadrante == Quadrante.LESTE else DirecaoOlhar.LESTE

        direcao_atual = getattr(entidade_ou_pos, "direcao_olhar", None)

        return {
            "ponto": (px, py),
            "quadrante": quadrante,
            "divisor_x": divisor,
            "distancia_centro_x": distancia_centro_x,
            "percentual_x": round(percentual_x, 3),
            "direcao_atual": direcao_atual,
            "direcao_sugerida": direcao_sugerida,
        }

    def calcular_direcao_olhar(
        self,
        entidade_ou_pos: Any,
        modo: str = "para_centro",
        alvo: Optional[Any] = None,
        largura_tela: Optional[int] = None
    ) -> str:
        """
        Calcula para qual lado a entidade deve estar virada.
        
        Modos:
        - 'para_centro' (padrão): se está no Leste, olha para o Oeste. Se está no Oeste, olha para o Leste.
        - 'para_alvo': vira para onde o alvo fornecido estiver (se alvo à esquerda, vira Oeste; se à direita, Leste).
        - 'mesmo_quadrante': se no Leste, olha para Leste; se no Oeste, olha para Oeste.
        - 'leste'/'oeste': força diretamente a direção desejada.
        """
        modo_limpo = str(modo).lower().strip()

        if modo_limpo in ("leste", "direita", "east", "right"):
            return DirecaoOlhar.LESTE
        if modo_limpo in ("oeste", "esquerda", "west", "left"):
            return DirecaoOlhar.OESTE

        px, _ = self.obter_ponto(entidade_ou_pos)

        if modo_limpo == "para_alvo" and alvo is not None:
            alvo_x, _ = self.obter_ponto(alvo)
            if alvo_x < px:
                return DirecaoOlhar.OESTE
            return DirecaoOlhar.LESTE

        quadrante = self.identificar_quadrante(entidade_ou_pos, largura_tela=largura_tela)

        if modo_limpo == "mesmo_quadrante":
            return DirecaoOlhar.LESTE if quadrante == Quadrante.LESTE else DirecaoOlhar.OESTE

        # Modo padrão 'para_centro':
        # No quadrante Leste (direita), o inimigo olha para o Oeste (esquerda).
        # No quadrante Oeste (esquerda), o inimigo olha para o Leste (direita).
        if quadrante == Quadrante.LESTE:
            return DirecaoOlhar.OESTE
        return DirecaoOlhar.LESTE

    def gerenciar_orientacao(
        self,
        inimigo: Any,
        modo: str = "para_centro",
        alvo: Optional[Any] = None,
        largura_tela: Optional[int] = None
    ) -> str:
        """
        Verifica o ponto do inimigo na tela, define seu quadrante
        e gerencia para qual lado ele fica virado, atualizando seu sprite e atributos.
        """
        quadrante = self.identificar_quadrante(inimigo, largura_tela=largura_tela)
        direcao = self.calcular_direcao_olhar(inimigo, modo=modo, alvo=alvo, largura_tela=largura_tela)

        # Atualiza o quadrante registrado na entidade
        inimigo.quadrante = quadrante

        # Atualiza a orientação no inimigo se ele possuir o método virar_para
        if hasattr(inimigo, "virar_para") and callable(inimigo.virar_para):
            inimigo.virar_para(direcao)
        else:
            inimigo.direcao_olhar = direcao

        return direcao

    def gerenciar_todos(
        self,
        inimigos: list,
        modo: str = "para_centro",
        alvo: Optional[Any] = None,
        largura_tela: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Aplica a verificação de quadrante e orientação para uma coleção de inimigos.
        Retorna um sumário com o total de inimigos em cada quadrante.
        """
        resumo = {
            Quadrante.OESTE: 0,
            Quadrante.LESTE: 0,
            "inimigos_gerenciados": 0,
            "detalhes": []
        }

        for inimigo in inimigos:
            if inimigo is None:
                continue
            direcao_aplicada = self.gerenciar_orientacao(
                inimigo,
                modo=modo,
                alvo=alvo,
                largura_tela=largura_tela
            )
            quad = getattr(inimigo, "quadrante", self.identificar_quadrante(inimigo, largura_tela))
            if quad in resumo:
                resumo[quad] += 1
            resumo["inimigos_gerenciados"] += 1
            resumo["detalhes"].append({
                "nome": getattr(inimigo, "nome", "Inimigo"),
                "ponto": self.obter_ponto(inimigo),
                "quadrante": quad,
                "direcao": direcao_aplicada,
            })

        return resumo


# Instância global para uso direto
sistema_quadrantes = SistemaQuadrantes()
