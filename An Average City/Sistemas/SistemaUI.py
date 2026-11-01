import math
from typing import Callable, Optional, Any, Dict, List, Tuple
import pygame
from Sistemas.Fontes import obter_fonte
from Sistemas.Recursos import caminho_botao, caminho_imagem, caminho_container

class Botao:

    def __init__(
        self,
        x: int,
        y: int,
        largura: int,
        altura: int,
        texto: str = "",
        cor_base: Tuple[int, int, int] = (50, 58, 72),
        cor_hover: Optional[Tuple[int, int, int]] = None,
        largura_hover: Optional[int] = None,
        altura_hover: Optional[int] = None,
        cor_texto: Tuple[int, int, int] = (240, 245, 250),
        fonte_tamanho: int = 16,
        sprite_base_path: Optional[str] = None,
        sprite_hover_path: Optional[str] = None,
        sprite_clique_path: Optional[str] = None,
        alternado: bool = False,
        ativo_inicial: bool = False,
        acao: Optional[Callable[[], Any]] = None,
        borda_raio: int = 6,
        tooltip: str = "",
        id_botao: Optional[str] = None,
        sem_texto: bool = False
    ):
        self.x_centro = x + largura // 2
        self.y_centro = y + altura // 2
        self.largura_base = largura
        self.altura_base = altura

        self.largura_hover = largura_hover if largura_hover is not None else largura + 6
        self.altura_hover = altura_hover if altura_hover is not None else altura + 4

        self.largura_clique = max(10, largura - 8)
        self.altura_clique = max(8, altura - 4)

        self.rect = pygame.Rect(x, y, largura, altura)
        self.pressionado = False
        self.alternado = alternado
        self.ativo = ativo_inicial
        self.sem_texto = sem_texto
        self.acao = acao
        self.borda_raio = borda_raio
        self.tooltip = tooltip
        self.id_botao = id_botao

        self.cor_base = cor_base
        if cor_hover is not None:
            self.cor_hover = cor_hover
        else:
            self.cor_hover = tuple(min(255, int(c * 1.3 + 25)) for c in cor_base)

        self.cor_texto = cor_texto
        self.cor_atual = self.cor_base
        self.texto = str(texto)
        self.fonte_tamanho = fonte_tamanho

        sprite_base_path = sprite_base_path or None
        sprite_hover_path = sprite_hover_path or sprite_base_path
        sprite_clique_path = sprite_clique_path or sprite_base_path

        self.usar_sprites = bool(sprite_base_path and sprite_clique_path)
        self.sprite_base = None
        self.sprite_hover = None
        self.sprite_clique = None
        self.sprite_atual = None

        if self.usar_sprites:
            try:
                caminho_base = caminho_botao(sprite_base_path)
                caminho_hover = caminho_botao(sprite_hover_path)
                caminho_clique = caminho_botao(sprite_clique_path)

                img_base = pygame.image.load(caminho_base)
                if pygame.display.get_surface() is not None:
                    img_base = img_base.convert_alpha()
                self.sprite_base = pygame.transform.scale(img_base, (largura, altura))

                img_hover = pygame.image.load(caminho_hover)
                if pygame.display.get_surface() is not None:
                    img_hover = img_hover.convert_alpha()
                self.sprite_hover = pygame.transform.scale(img_hover, (largura, altura))

                img_clique = pygame.image.load(caminho_clique)
                if pygame.display.get_surface() is not None:
                    img_clique = img_clique.convert_alpha()
                self.sprite_clique = pygame.transform.scale(img_clique, (largura, altura))

                self.sprite_atual = self.sprite_base
            except (FileNotFoundError, pygame.error) as erro:
                print(f"[Aviso] Nao foi possivel carregar os sprites do botao '{texto}': {erro}")
                self.usar_sprites = False

        self.fonte = obter_fonte(fonte_tamanho)
        self._atualizar_superficie_texto()

    def _atualizar_superficie_texto(self):
        if self.texto:
            self.txt_renderizado = self.fonte.render(self.texto, True, self.cor_texto)
            self.txt_rect = self.txt_renderizado.get_rect(center=self.rect.center)
        else:
            self.txt_renderizado = None
            self.txt_rect = self.rect.copy()

    def definir_texto(self, novo_texto: str):
        self.texto = str(novo_texto)
        self._atualizar_superficie_texto()

    def definir_ativo(self, ativo: bool):
        self.ativo = bool(ativo)

    def checar_clique(self, evento: pygame.event.Event, posicao_mouse: Tuple[int, int]) -> Any:
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.rect.collidepoint(posicao_mouse):
                self.pressionado = True

        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            if self.pressionado and self.rect.collidepoint(posicao_mouse):
                self.pressionado = False
                if self.alternado:
                    self.ativo = not self.ativo

                try:
                    from Sistemas.GerenciadorAudio import tocar_sfx
                    tocar_sfx("Interface.wav", volume_relativo=0.6)
                except Exception:
                    pass

                if self.acao is not None:
                    resultado = self.acao()
                    return resultado if resultado is not None else True
                return True
            self.pressionado = False

        return False

    def clicado(self, posicao_mouse: Tuple[int, int]) -> bool:
        return self.rect.collidepoint(posicao_mouse)

    def atualizar(self, posicao_mouse: Tuple[int, int], estado_clique_mouse: Tuple[bool, ...]):
        if self.alternado:
            if self.usar_sprites:
                self.sprite_atual = self.sprite_clique if self.ativo else self.sprite_base
            self.cor_atual = self.cor_hover if self.ativo else self.cor_base
            self.rect.width = self.largura_base
            self.rect.height = self.altura_base
            self.rect.center = (self.x_centro, self.y_centro)
            if self.txt_rect:
                self.txt_rect.center = self.rect.center
            return

        if self.rect.collidepoint(posicao_mouse):
            self.cor_atual = self.cor_hover
            if estado_clique_mouse[0]:
                if self.usar_sprites:
                    self.sprite_atual = self.sprite_clique
                self.rect.width = self.largura_clique
                self.rect.height = self.altura_clique
            else:
                if self.usar_sprites:
                    self.sprite_atual = self.sprite_hover
                self.rect.width = self.largura_hover
                self.rect.height = self.altura_hover
        else:
            if self.usar_sprites:
                self.sprite_atual = self.sprite_base
            self.cor_atual = self.cor_base
            self.rect.width = self.largura_base
            self.rect.height = self.altura_base

        self.rect.center = (self.x_centro, self.y_centro)
        if self.txt_rect:
            self.txt_rect.center = self.rect.center

    def desenhar(self, superficie: pygame.Surface):
        if self.usar_sprites and self.sprite_atual is not None:
            superficie.blit(self.sprite_atual, self.rect)
            if not self.sem_texto and self.txt_renderizado is not None:
                superficie.blit(self.txt_renderizado, self.txt_rect)
        else:
            pygame.draw.rect(superficie, self.cor_atual, self.rect, border_radius=self.borda_raio)
            if not self.sem_texto and self.txt_renderizado is not None:
                superficie.blit(self.txt_renderizado, self.txt_rect)

class TelaBase:

    def __init__(self, tela: pygame.Surface, gerenciador_telas=None, nome: str = "tela"):
        self.tela = tela
        self.largura = tela.get_width() if tela else 1000
        self.altura = tela.get_height() if tela else 800
        self.gerenciador_telas = gerenciador_telas
        self.nome = nome

        self.cor_fundo: Tuple[int, int, int] = (16, 20, 26)
        self.imagem_fundo: Optional[pygame.Surface] = None
        self.posicao_fundo: Tuple[int, int] = (0, 0)
        self.escala_fundo: float = 1.0

        self.botoes: List[Botao] = []
        self.mapa_botoes: Dict[str, Botao] = {}

        self.mensagem_feedback: Optional[str] = None
        self.cor_feedback: Tuple[int, int, int] = (100, 255, 140)
        self.temporizador_feedback: int = 0
        self.fonte_feedback = obter_fonte(14)

        self.voltar_clicado: bool = False

    def criar_botao(
        self,
        x: int,
        y: int,
        largura: int,
        altura: int,
        texto: str = "",
        cor_base: Tuple[int, int, int] = (50, 58, 72),
        cor_hover: Optional[Tuple[int, int, int]] = None,
        largura_hover: Optional[int] = None,
        altura_hover: Optional[int] = None,
        cor_texto: Tuple[int, int, int] = (240, 245, 250),
        fonte_tamanho: int = 16,
        sprite_base_path: Optional[str] = None,
        sprite_hover_path: Optional[str] = None,
        sprite_clique_path: Optional[str] = None,
        alternado: bool = False,
        ativo_inicial: bool = False,
        acao: Optional[Callable[[], Any]] = None,
        borda_raio: int = 6,
        id_botao: Optional[str] = None
    ) -> Botao:
        botao = Botao(
            x=x,
            y=y,
            largura=largura,
            altura=altura,
            texto=texto,
            cor_base=cor_base,
            cor_hover=cor_hover,
            largura_hover=largura_hover,
            altura_hover=altura_hover,
            cor_texto=cor_texto,
            fonte_tamanho=fonte_tamanho,
            sprite_base_path=sprite_base_path,
            sprite_hover_path=sprite_hover_path,
            sprite_clique_path=sprite_clique_path,
            alternado=alternado,
            ativo_inicial=ativo_inicial,
            acao=acao,
            borda_raio=borda_raio,
            id_botao=id_botao
        )
        self.adicionar_botao(botao, id_botao)
        return botao

    def adicionar_botao(self, botao: Botao, id_botao: Optional[str] = None):
        if botao not in self.botoes:
            self.botoes.append(botao)
        chave = id_botao or botao.id_botao
        if chave:
            self.mapa_botoes[chave] = botao

    def remover_botao(self, botao: Botao):
        if botao in self.botoes:
            self.botoes.remove(botao)
        for chave, b in list(self.mapa_botoes.items()):
            if b == botao:
                del self.mapa_botoes[chave]

    def limpar_botoes(self):
        self.botoes.clear()
        self.mapa_botoes.clear()

    def carregar_fundo(self, nome_arquivo: str, pasta: str = "sprites") -> bool:
        try:
            if pasta.lower() == "botoes":
                caminho = caminho_botao(nome_arquivo)
            else:
                caminho = caminho_imagem(nome_arquivo)

            imagem_original = pygame.image.load(caminho)
            if pygame.display.get_surface() is not None:
                imagem_original = imagem_original.convert()
            escala = max(self.largura / imagem_original.get_width(), self.altura / imagem_original.get_height())
            novo_tamanho = (int(imagem_original.get_width() * escala), int(imagem_original.get_height() * escala))
            self.imagem_fundo = pygame.transform.scale(imagem_original, novo_tamanho)
            x_fundo = (self.largura - novo_tamanho[0]) // 2
            y_fundo = (self.altura - novo_tamanho[1]) // 2
            self.posicao_fundo = (x_fundo, y_fundo)
            self.escala_fundo = escala
            return True
        except (FileNotFoundError, pygame.error) as erro:
            print(f"[Aviso] Nao foi possivel carregar o fundo '{nome_arquivo}': {erro}")
            self.imagem_fundo = None
            self.posicao_fundo = (0, 0)
            self.escala_fundo = 1.0
            return False

    def mostrar_feedback(self, mensagem: str, cor: Tuple[int, int, int] = (100, 255, 140), duracao: int = 120):
        self.mensagem_feedback = mensagem
        self.cor_feedback = cor
        self.temporizador_feedback = duracao

    def ao_entrar(self, **kwargs):
        self.voltar_clicado = False

    def ao_sair(self):
        pass

    def atualizar_eventos(self, evento: pygame.event.Event, posicao_mouse: Tuple[int, int]) -> Any:
        for botao in self.botoes:
            resultado = botao.checar_clique(evento, posicao_mouse)
            if resultado:
                return resultado
        return None

    def atualizar(self, posicao_mouse: Tuple[int, int], estado_clique_mouse: Tuple[bool, ...]):
        if self.temporizador_feedback > 0:
            self.temporizador_feedback -= 1

        for botao in self.botoes:
            botao.atualizar(posicao_mouse, estado_clique_mouse)

        self.atualizar_conteudo(posicao_mouse, estado_clique_mouse)

    def atualizar_conteudo(self, posicao_mouse: Tuple[int, int], estado_clique_mouse: Tuple[bool, ...]):
        pass

    def desenhar(self):
        if self.imagem_fundo is not None:
            self.tela.blit(self.imagem_fundo, self.posicao_fundo)
        else:
            self.tela.fill(self.cor_fundo)

        self.desenhar_conteudo()

        for botao in self.botoes:
            botao.desenhar(self.tela)

        self.desenhar_feedback()

    def desenhar_conteudo(self):
        pass

    def desenhar_feedback(self):
        if self.temporizador_feedback <= 0 or not self.mensagem_feedback:
            return

        alpha = min(255, self.temporizador_feedback * 6)
        surf_msg = self.fonte_feedback.render(self.mensagem_feedback, True, self.cor_feedback)
        largura_caixa = surf_msg.get_width() + 40
        altura_caixa = surf_msg.get_height() + 16
        x_caixa = (self.largura - largura_caixa) // 2
        y_caixa = 24

        overlay = pygame.Surface((largura_caixa, altura_caixa), pygame.SRCALPHA)
        overlay.fill((16, 20, 26, int(min(230, alpha))))
        pygame.draw.rect(overlay, (*self.cor_feedback[:3], int(alpha)), overlay.get_rect(), width=1, border_radius=6)
        surf_msg.set_alpha(alpha)
        overlay.blit(surf_msg, (20, 8))

        self.tela.blit(overlay, (x_caixa, y_caixa))

class GerenciadorTelas:

    def __init__(self, tela: Optional[pygame.Surface] = None):
        self.tela = tela
        self.telas: Dict[str, TelaBase] = {}
        self.estado_atual: Optional[str] = None

    def registrar_tela(self, nome: str, tela_instancia: Any) -> Any:
        self.telas[nome] = tela_instancia
        if hasattr(tela_instancia, 'gerenciador_telas'):
            tela_instancia.gerenciador_telas = self
        if hasattr(tela_instancia, 'nome'):
            tela_instancia.nome = nome
        return tela_instancia

    def trocar_tela(self, novo_estado: str, **kwargs) -> Optional[TelaBase]:
        if novo_estado not in self.telas:
            print(f"[Erro] GerenciadorTelas: tela '{novo_estado}' nao registrada.")
            return None

        if self.estado_atual and self.estado_atual in self.telas:
            tela_antiga = self.telas[self.estado_atual]
            if hasattr(tela_antiga, 'ao_sair'):
                tela_antiga.ao_sair()

        self.estado_atual = novo_estado
        tela_nova = self.telas[novo_estado]
        if hasattr(tela_nova, 'ao_entrar'):
            tela_nova.ao_entrar(**kwargs)

        return tela_nova

    def obter_tela_atual(self) -> Optional[TelaBase]:
        if self.estado_atual:
            return self.telas.get(self.estado_atual)
        return None

    def obter_tela(self, nome: str) -> Optional[TelaBase]:
        return self.telas.get(nome)

    def processar_evento(self, evento: pygame.event.Event, posicao_mouse: Tuple[int, int]) -> Any:
        tela = self.obter_tela_atual()
        if tela is not None:
            if hasattr(tela, 'atualizar_eventos'):
                return tela.atualizar_eventos(evento, posicao_mouse)
        return None

    def atualizar(self, posicao_mouse: Tuple[int, int], estado_clique_mouse: Tuple[bool, ...]):
        tela = self.obter_tela_atual()
        if tela is not None:
            if hasattr(tela, 'atualizar'):
                tela.atualizar(posicao_mouse, estado_clique_mouse)

    def desenhar(self):
        tela = self.obter_tela_atual()
        if tela is not None:
            if hasattr(tela, 'desenhar'):
                tela.desenhar()


# ==============================================================================
# SISTEMA DE CONTAINERS 8-BIT COM 9-SLICE
# ==============================================================================

_CACHE_CONTAINERS_RAW: Dict[str, Optional[pygame.Surface]] = {}
_CACHE_PAINEIS_9SLICE: Dict[Tuple[str, int, int, int], pygame.Surface] = {}

def obter_painel_container(
    nome_sprite: str = "painel_base.png",
    largura: int = 100,
    altura: int = 100,
    margem: int = 14
) -> Optional[pygame.Surface]:
    """
    Retorna uma Surface do container 8-bit redimensionada via 9-slice.
    Os cantos e detalhes pixel-art são preservados sem distorção.
    Resultados são cacheados em memória para alta performance (60 FPS estáveis).
    """
    if largura <= 0 or altura <= 0:
        return None

    chave = (nome_sprite, largura, altura, margem)
    if chave in _CACHE_PAINEIS_9SLICE:
        return _CACHE_PAINEIS_9SLICE[chave]

    if nome_sprite not in _CACHE_CONTAINERS_RAW:
        try:
            import os
            caminho = caminho_container(nome_sprite)
            if not os.path.exists(caminho):
                caminho = caminho_imagem(nome_sprite)
            img = pygame.image.load(caminho)
            if pygame.display.get_surface() is not None:
                img = img.convert_alpha()
            _CACHE_CONTAINERS_RAW[nome_sprite] = img
        except Exception as e:
            print(f"[Aviso] Nao foi possivel carregar sprite container '{nome_sprite}': {e}")
            _CACHE_CONTAINERS_RAW[nome_sprite] = None

    base = _CACHE_CONTAINERS_RAW.get(nome_sprite)
    if base is None:
        return None

    ow, oh = base.get_size()
    mx = min(margem, ow // 3, max(1, largura // 2))
    my = min(margem, oh // 3, max(1, altura // 2))

    surf = pygame.Surface((largura, altura), pygame.SRCALPHA)

    # Cantos
    tl = base.subsurface((0, 0, mx, my))
    tr = base.subsurface((ow - mx, 0, mx, my))
    bl = base.subsurface((0, oh - my, mx, my))
    br = base.subsurface((ow - mx, oh - my, mx, my))

    surf.blit(tl, (0, 0))
    surf.blit(tr, (largura - mx, 0))
    surf.blit(bl, (0, altura - my))
    surf.blit(br, (largura - mx, altura - my))

    # Bordas
    if largura > 2 * mx:
        t = pygame.transform.scale(base.subsurface((mx, 0, ow - 2 * mx, my)), (largura - 2 * mx, my))
        b = pygame.transform.scale(base.subsurface((mx, oh - my, ow - 2 * mx, my)), (largura - 2 * mx, my))
        surf.blit(t, (mx, 0))
        surf.blit(b, (mx, altura - my))

    if altura > 2 * my:
        l = pygame.transform.scale(base.subsurface((0, my, mx, oh - 2 * my)), (mx, altura - 2 * my))
        r = pygame.transform.scale(base.subsurface((ow - mx, my, mx, oh - 2 * my)), (mx, altura - 2 * my))
        surf.blit(l, (0, my))
        surf.blit(r, (largura - mx, my))

    # Centro
    if largura > 2 * mx and altura > 2 * my:
        c = pygame.transform.scale(base.subsurface((mx, my, ow - 2 * mx, oh - 2 * my)), (largura - 2 * mx, altura - 2 * my))
        surf.blit(c, (mx, my))

    if pygame.display.get_surface() is not None:
        surf = surf.convert_alpha()

    _CACHE_PAINEIS_9SLICE[chave] = surf
    return surf

def desenhar_painel_container(
    tela: pygame.Surface,
    rect: Any,
    nome_sprite: str = "painel_base.png",
    fallback_cor: Optional[Tuple[int, int, int]] = None,
    borda_cor: Optional[Tuple[int, int, int]] = None,
    margem: int = 14
) -> None:
    """
    Desenha um container estilizado no retângulo especificado usando 9-slice do sprite 8-bit.
    Se o sprite não puder ser carregado, renderiza com cores sólidas de fallback.
    """
    if not isinstance(rect, pygame.Rect):
        rect = pygame.Rect(rect)
    if rect.width <= 0 or rect.height <= 0:
        return

    painel = obter_painel_container(nome_sprite, rect.width, rect.height, margem)
    if painel is not None:
        tela.blit(painel, rect.topleft)
    else:
        if fallback_cor is not None:
            pygame.draw.rect(tela, fallback_cor, rect, border_radius=6)
        if borda_cor is not None:
            pygame.draw.rect(tela, borda_cor, rect, width=2, border_radius=6)
