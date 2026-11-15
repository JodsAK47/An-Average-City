from typing import Optional
import pygame

try:
    import cv2
except ImportError:
    cv2 = None

class SistemaCutscene:
    """
    Sistema que monitora e identifica se o jogo está atualmente no meio de uma cutscene,
    gerenciando os efeitos visuais temáticos, como o filtro e a camada de sobreposição de Pixel Art.
    """

    def __init__(self):
        self.em_cutscene: bool = False
        self.chefe_atual: str = ""
        self.verso_atual: str = ""
        self.filtro_pixel_art_ativo: bool = True
        self.tamanho_pixel: int = 4
        self.intensidade_grade: int = 32
        self.intensidade_scanline: int = 24

    def esta_em_cutscene(self) -> bool:
        """Retorna True se o jogo estiver atualmente reproduzindo uma cutscene."""
        return self.em_cutscene

    def iniciar_cutscene(self, chefe: str = "", verso: str = ""):
        """Marca o estado do jogo como estando no meio de uma cutscene."""
        self.em_cutscene = True
        self.chefe_atual = chefe or ""
        self.verso_atual = verso or ""

    def finalizar_cutscene(self):
        """Marca o fim da cutscene atual."""
        self.em_cutscene = False
        self.chefe_atual = ""
        self.verso_atual = ""

    def criar_camada_pixel_art(
        self,
        largura: int,
        altura: int,
        tamanho_pixel: Optional[int] = None
    ) -> pygame.Surface:
        """
        Cria uma camada de sobreposição (overlay) transparente com grade de pixels,
        scanlines de CRT e vinheta sutil para ser desenhada sobre o vídeo.
        """
        tam = tamanho_pixel if tamanho_pixel is not None else self.tamanho_pixel
        tam = max(1, tam)

        camada = pygame.Surface((largura, altura), pygame.SRCALPHA)
        camada.fill((0, 0, 0, 0))

        # 1. Linhas sutis de grade de pixels (Matriz de pixels estilo retro monitor / handheld)
        cor_grade = (0, 0, 0, self.intensidade_grade)
        for x in range(0, largura, tam):
            pygame.draw.line(camada, cor_grade, (x, 0), (x, altura), 1)
        for y in range(0, altura, tam):
            pygame.draw.line(camada, cor_grade, (0, y), (largura, y), 1)

        # 2. Linhas de varredura (Scanlines retrô alternadas)
        cor_scanline = (0, 0, 0, self.intensidade_scanline)
        for y in range(0, altura, tam * 2):
            pygame.draw.rect(camada, cor_scanline, (0, y, largura, tam))

        # 3. Vinheta suave nas bordas do vídeo para estética cinematográfica retro
        raio_borda = max(4, min(largura, altura) // 25)
        for i in range(raio_borda):
            alpha_borda = int(45 * (1.0 - i / raio_borda))
            pygame.draw.rect(camada, (0, 0, 0, alpha_borda), (i, i, largura - 2 * i, altura - 2 * i), 1)

        return camada

    def pixelar_frame_cv2(
        self,
        frame,
        dest_w: int,
        dest_h: int,
        tamanho_pixel: Optional[int] = None
    ) -> pygame.Surface:
        """
        Aplica pixelização no frame usando OpenCV com interpolação nearest-neighbor,
        gerando blocos nítidos de pixel art em menos de 6ms.
        """
        tam = tamanho_pixel if tamanho_pixel is not None else self.tamanho_pixel
        tam = max(1, tam)

        pw = max(1, dest_w // tam)
        ph = max(1, dest_h // tam)

        if cv2 is not None:
            # Reduz a resolução do frame
            pequeno = cv2.resize(frame, (pw, ph), interpolation=cv2.INTER_LINEAR)
            # Converte BGR para RGB na baixa resolução (otimização de cache e throughput)
            rgb_pequeno = cv2.cvtColor(pequeno, cv2.COLOR_BGR2RGB)
            # Upscale com vizinho mais próximo para criar os blocos de pixel
            pixelado = cv2.resize(rgb_pequeno, (dest_w, dest_h), interpolation=cv2.INTER_NEAREST)
            return pygame.image.frombuffer(pixelado.tobytes(), (dest_w, dest_h), "RGB")

        # Fallback sem cv2
        return pygame.Surface((dest_w, dest_h))

    def pixelar_superficie(
        self,
        superficie: pygame.Surface,
        tamanho_pixel: Optional[int] = None
    ) -> pygame.Surface:
        """
        Aplica pixelização em uma Surface pura do Pygame (fallback universal).
        """
        tam = tamanho_pixel if tamanho_pixel is not None else self.tamanho_pixel
        tam = max(1, tam)
        w, h = superficie.get_size()
        pw = max(1, w // tam)
        ph = max(1, h // tam)

        pequena = pygame.transform.scale(superficie, (pw, ph))
        return pygame.transform.scale(pequena, (w, h))

sistema_cutscene = SistemaCutscene()
