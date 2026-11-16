import os
import time
import math
from typing import Optional, Callable, Tuple
import pygame

try:
    import cv2
except ImportError:
    cv2 = None

from Sistemas.SistemaUI import TelaBase
from Sistemas.Fontes import obter_fonte
from Sistemas.Recursos import caminho_cutscene
from Sistemas.SistemaCutscene import sistema_cutscene

class GerenciadorCutscene(TelaBase):
    """
    Gerenciador de cutscenes dos chefes e finais de cada verso.
    Utiliza OpenCV para decodificação eficiente de vídeo sincronizado com áudio MP3 (via pygame.mixer),
    com identificador de estado ativo (em_cutscene), camada de sobreposição de Pixel Art (grade + scanlines)
    e botão de pular (Skip) auto-ocultável por inatividade do mouse.
    """

    MAPA_CUTSCENES = {
        "sukuna": {
            "video": "Sukuna Final Ultimate.mp4",
            "audio": "Sukuna Final Ultimate.mp3",
            "nome_chefe": "Sukuna",
            "verso": "Feiticeiro",
            "titulo": "CORTE FINAL - SUKUNA DERROTADO",
        },
        "feiticeiro": {
            "video": "Sukuna Final Ultimate.mp4",
            "audio": "Sukuna Final Ultimate.mp3",
            "nome_chefe": "Sukuna",
            "verso": "Feiticeiro",
            "titulo": "CORTE FINAL - SUKUNA DERROTADO",
        },
        "charlie": {
            "video": "Final KJ.mp4",
            "audio": "Final KJ.mp3",
            "nome_chefe": "Charlie",
            "verso": "Sobrevivente",
            "titulo": "GOLPE DE MISERICÓRDIA - CHARLIE DERROTADO",
        },
        "sobrevivente": {
            "video": "Final KJ.mp4",
            "audio": "Final KJ.mp3",
            "nome_chefe": "Charlie",
            "verso": "Sobrevivente",
            "titulo": "GOLPE DE MISERICÓRDIA - CHARLIE DERROTADO",
        },
        "estraga prazeres": {
            "placeholder": True,
            "nome_chefe": "Estraga Prazeres",
            "verso": "Agente",
            "titulo": "MISSÃO CONCLUÍDA - ESTRAGA PRAZERES NEUTRALIZADO",
        },
        "agente": {
            "placeholder": True,
            "nome_chefe": "Estraga Prazeres",
            "verso": "Agente",
            "titulo": "MISSÃO CONCLUÍDA - ESTRAGA PRAZERES NEUTRALIZADO",
        },
        "adam smasher": {
            "placeholder": True,
            "nome_chefe": "Adam Smasher",
            "verso": "Cyberpunk",
            "titulo": "LENDA DE NIGHT CITY - ADAM SMASHER DESTRUÍDO",
        },
        "cyberpunk": {
            "placeholder": True,
            "nome_chefe": "Adam Smasher",
            "verso": "Cyberpunk",
            "titulo": "LENDA DE NIGHT CITY - ADAM SMASHER DESTRUÍDO",
        },
    }

    # Tempo em segundos sem mover o mouse para o botão de skip sumir
    TEMPO_INATIVIDADE_MOUSE = 2.0

    def __init__(self, tela: pygame.Surface):
        super().__init__(tela, nome="cutscene")
        self.boss_atual = ""
        self.verso_atual = ""
        self.callback_conclusao: Optional[Callable[[], None]] = None

        self.ativo = False
        self.cap = None
        self.som_audio: Optional[pygame.mixer.Sound] = None
        self.canal_audio: Optional[pygame.mixer.Channel] = None

        self.tempo_inicio: float = 0.0
        self.fps: float = 30.0
        self.total_frames: int = 0
        self.duracao: float = 0.0
        self.frame_indice_atual: int = -1
        self.superficie_frame_atual: Optional[pygame.Surface] = None
        self.pos_frame: Tuple[int, int] = (0, 0)
        self.tam_frame: Tuple[int, int] = (self.largura, self.altura)

        self.eh_placeholder: bool = False
        self.duracao_placeholder: float = 7.0
        self.timer_scanline: float = 0.0

        # Filtro e camada de Pixel Art sobreposta ao vídeo
        self.filtro_pixel_art: bool = True
        self.camada_pixel_art: Optional[pygame.Surface] = None

        # Controle de visibilidade do botão de Skip por inatividade do mouse
        self.tempo_ultimo_movimento_mouse: float = 0.0
        self.posicao_mouse_anterior: Tuple[int, int] = (-1, -1)
        self.botao_pular_visivel: bool = True
        self.alpha_botao: float = 255.0

        self.fonte_titulo = obter_fonte(28)
        self.fonte_subtitulo = obter_fonte(18)
        self.fonte_info = obter_fonte(14)
        self.fonte_dica = obter_fonte(13)

        largura_btn = 150
        altura_btn = 38
        self.botao_pular = self.criar_botao(
            self.largura - largura_btn - 25, self.altura - altura_btn - 22,
            largura_btn, altura_btn, "PULAR [ESPAÇO]",
            cor_base=(20, 24, 34), cor_hover=(55, 68, 92),
            cor_texto=(235, 242, 255), fonte_tamanho=13, borda_raio=8,
            acao=self.finalizar
        )

    @property
    def em_cutscene(self) -> bool:
        """Identifica se o jogo está atualmente no meio de uma cutscene."""
        return self.ativo and sistema_cutscene.esta_em_cutscene()

    def esta_em_cutscene(self) -> bool:
        """Método helper para consultar se a cutscene está ativa."""
        return self.em_cutscene

    def iniciar(self, boss_nome: str = "", verso: str = "", callback_conclusao: Optional[Callable[[], None]] = None):
        self.finalizar()

        self.boss_atual = boss_nome or ""
        self.verso_atual = verso or ""
        self.callback_conclusao = callback_conclusao
        self.superficie_frame_atual = None
        self.frame_indice_atual = -1

        # Notifica o sistema central de cutscenes
        sistema_cutscene.iniciar_cutscene(self.boss_atual, self.verso_atual)

        # Inicializar estado do botão de skip visível ao abrir
        self.tempo_ultimo_movimento_mouse = time.perf_counter()
        self.posicao_mouse_anterior = (-1, -1)
        self.botao_pular_visivel = True
        self.alpha_botao = 255.0

        chave = (self.boss_atual or self.verso_atual or "").lower().strip()
        config = self.MAPA_CUTSCENES.get(chave)
        if not config:
            for k, cfg in self.MAPA_CUTSCENES.items():
                if k in chave or chave in k:
                    config = cfg
                    break

        if not config:
            if "feiticeiro" in chave or "sukuna" in chave:
                config = self.MAPA_CUTSCENES["sukuna"]
            elif "agente" in chave or "estraga" in chave:
                config = self.MAPA_CUTSCENES["agente"]
            else:
                config = self.MAPA_CUTSCENES["sobrevivente"]

        self.config_atual = config
        self.eh_placeholder = bool(config.get("placeholder", False))

        caminho_vid = caminho_cutscene(config.get("video", "")) if "video" in config else None
        if not self.eh_placeholder and caminho_vid and os.path.exists(caminho_vid) and cv2 is not None:
            try:
                self.cap = cv2.VideoCapture(caminho_vid)
                if not self.cap.isOpened():
                    self.eh_placeholder = True
                    self.cap = None
                else:
                    fps_val = self.cap.get(cv2.CAP_PROP_FPS)
                    self.fps = fps_val if fps_val > 0 else 30.0
                    self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    vid_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    vid_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    self.duracao = self.total_frames / self.fps if self.fps > 0 else 10.0

                    # Calcular escala para caber na tela mantendo proporção (letterbox)
                    escala_w = self.largura / max(1, vid_w)
                    escala_h = self.altura / max(1, vid_h)
                    escala = min(escala_w, escala_h)
                    dest_w = max(1, int(vid_w * escala))
                    dest_h = max(1, int(vid_h * escala))
                    self.tam_frame = (dest_w, dest_h)
                    self.pos_frame = ((self.largura - dest_w) // 2, (self.altura - dest_h) // 2)

                    # Pré-cria a camada de sobreposição de Pixel Art para aplicar sobre o vídeo
                    self.camada_pixel_art = sistema_cutscene.criar_camada_pixel_art(
                        dest_w, dest_h, tamanho_pixel=sistema_cutscene.tamanho_pixel
                    )

                    # Áudio sincronizado
                    caminho_aud = caminho_cutscene(config.get("audio", "")) if "audio" in config else None
                    if caminho_aud and os.path.exists(caminho_aud):
                        try:
                            self.som_audio = pygame.mixer.Sound(caminho_aud)
                            self.canal_audio = pygame.mixer.find_channel(True)
                            if self.canal_audio:
                                self.canal_audio.play(self.som_audio)
                        except (pygame.error, FileNotFoundError) as err:
                            print(f"[Aviso] Nao foi possivel reproduzir audio da cutscene: {err}")
                            self.som_audio = None
                            self.canal_audio = None

                    # Decodificar o primeiro frame imediatamente aplicando o filtro de Pixel Art
                    ret, frame = self.cap.read()
                    if ret:
                        self.frame_indice_atual = 0
                        if self.filtro_pixel_art and sistema_cutscene.filtro_pixel_art_ativo:
                            self.superficie_frame_atual = sistema_cutscene.pixelar_frame_cv2(
                                frame, dest_w, dest_h, tamanho_pixel=sistema_cutscene.tamanho_pixel
                            )
                        else:
                            resized = cv2.resize(frame, self.tam_frame, interpolation=cv2.INTER_LINEAR)
                            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                            self.superficie_frame_atual = pygame.image.frombuffer(rgb.tobytes(), self.tam_frame, "RGB")
            except Exception as erro:
                print(f"[Aviso] Erro ao carregar video da cutscene: {erro}")
                self.eh_placeholder = True
                if self.cap:
                    self.cap.release()
                    self.cap = None
        else:
            self.eh_placeholder = True

        if self.eh_placeholder:
            self.camada_pixel_art = sistema_cutscene.criar_camada_pixel_art(
                self.largura, self.altura, tamanho_pixel=sistema_cutscene.tamanho_pixel
            )

        self.tempo_inicio = time.perf_counter()
        self.ativo = True

    def finalizar(self):
        if not self.ativo and self.cap is None and self.canal_audio is None:
            return

        self.ativo = False
        sistema_cutscene.finalizar_cutscene()

        if self.canal_audio is not None:
            try:
                self.canal_audio.stop()
            except Exception:
                pass
            self.canal_audio = None

        if self.som_audio is not None:
            try:
                self.som_audio.stop()
            except Exception:
                pass
            self.som_audio = None

        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

        if self.callback_conclusao is not None:
            cb = self.callback_conclusao
            self.callback_conclusao = None
            cb()

    def registrar_movimento_mouse(self, posicao: Optional[Tuple[int, int]] = None):
        """Registra atividade do mouse para fazer o botão de skip surgir imediatamente."""
        self.tempo_ultimo_movimento_mouse = time.perf_counter()
        self.botao_pular_visivel = True
        self.alpha_botao = 255.0
        if posicao is not None:
            self.posicao_mouse_anterior = posicao

    def atualizar_eventos(self, evento: pygame.event.Event, posicao_mouse: Tuple[int, int]):
        if not self.ativo:
            return None

        # Ao mover o mouse, o botão ressurge imediatamente
        if evento.type == pygame.MOUSEMOTION:
            dx = abs(evento.pos[0] - self.posicao_mouse_anterior[0])
            dy = abs(evento.pos[1] - self.posicao_mouse_anterior[1])
            if dx > 0 or dy > 0:
                self.registrar_movimento_mouse(evento.pos)

        # Teclas de atalho para pular
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                self.finalizar()
                return "concluido"

        # Clique do mouse
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self.registrar_movimento_mouse(posicao_mouse)
            # Se o botão estiver visível e clicado, finaliza
            if self.botao_pular_visivel and self.botao_pular.rect.collidepoint(posicao_mouse):
                self.finalizar()
                return "concluido"

        if self.botao_pular_visivel:
            resultado_botao = self.botao_pular.checar_clique(evento, posicao_mouse)
            if resultado_botao:
                self.finalizar()
                return "concluido"

        return None

    def atualizar(self, posicao_mouse: Tuple[int, int], estado_clique_mouse: Tuple[bool, ...]):
        if not self.ativo:
            return

        # Detectar se o mouse se moveu entre frames
        if posicao_mouse != self.posicao_mouse_anterior:
            self.registrar_movimento_mouse(posicao_mouse)

        # Lógica de temporizador: se o mouse ficar parado por 2 segundos, o botão some suavemente
        tempo_sem_mover = time.perf_counter() - self.tempo_ultimo_movimento_mouse
        if tempo_sem_mover >= self.TEMPO_INATIVIDADE_MOUSE:
            # Fade out do botão após 2 segundos
            self.alpha_botao = max(0.0, self.alpha_botao - 18.0)
            if self.alpha_botao <= 0.0:
                self.botao_pular_visivel = False
        else:
            self.botao_pular_visivel = True
            self.alpha_botao = min(255.0, self.alpha_botao + 35.0)

        # Atualiza hover do botão quando estiver visível
        if self.botao_pular_visivel:
            self.botao_pular.atualizar(posicao_mouse, estado_clique_mouse)

        tempo_decorrido = time.perf_counter() - self.tempo_inicio

        if self.eh_placeholder:
            self.timer_scanline = tempo_decorrido
            if tempo_decorrido >= self.duracao_placeholder:
                self.finalizar()
            return

        if tempo_decorrido >= self.duracao:
            self.finalizar()
            return

        frame_alvo = int(tempo_decorrido * self.fps)
        if self.cap and frame_alvo > self.frame_indice_atual:
            ultimo_frame = None
            while self.frame_indice_atual < frame_alvo:
                ret, frame = self.cap.read()
                self.frame_indice_atual += 1
                if not ret:
                    self.finalizar()
                    return
                ultimo_frame = frame

            if ultimo_frame is not None and cv2 is not None:
                # Transforma o frame em pixel art nítido com nearest-neighbor
                if self.filtro_pixel_art and sistema_cutscene.filtro_pixel_art_ativo:
                    self.superficie_frame_atual = sistema_cutscene.pixelar_frame_cv2(
                        ultimo_frame, self.tam_frame[0], self.tam_frame[1], tamanho_pixel=sistema_cutscene.tamanho_pixel
                    )
                else:
                    resized = cv2.resize(ultimo_frame, self.tam_frame, interpolation=cv2.INTER_LINEAR)
                    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                    self.superficie_frame_atual = pygame.image.frombuffer(rgb.tobytes(), self.tam_frame, "RGB")

    def desenhar(self):
        self.tela.fill((0, 0, 0))

        if self.eh_placeholder:
            self._desenhar_placeholder_agente()
            # Aplica camada de Pixel Art sobre a tela placeholder
            if self.em_cutscene and self.filtro_pixel_art and self.camada_pixel_art is not None:
                self.tela.blit(self.camada_pixel_art, (0, 0))
        else:
            if self.superficie_frame_atual is not None:
                self.tela.blit(self.superficie_frame_atual, self.pos_frame)

            # Camada de Pixel Art (Overlay de grade, scanlines e vinheta aplicada sobre o vídeo)
            if self.em_cutscene and self.filtro_pixel_art and self.camada_pixel_art is not None:
                self.tela.blit(self.camada_pixel_art, self.pos_frame)

            # Barra de progresso discreta na base
            if self.duracao > 0:
                tempo_decorrido = max(0.0, time.perf_counter() - self.tempo_inicio)
                progresso = min(1.0, tempo_decorrido / self.duracao)
                largura_barra = int(self.largura * progresso)
                pygame.draw.rect(self.tela, (40, 45, 55), (0, self.altura - 4, self.largura, 4))
                pygame.draw.rect(self.tela, (230, 60, 60), (0, self.altura - 4, largura_barra, 4))

        # Desenhar botão de skip se estiver visível (fade in/out com suporte a alpha)
        if self.botao_pular_visivel and self.alpha_botao > 0:
            self._desenhar_botao_skip()

    def _desenhar_botao_skip(self):
        """Renderiza o botão de skip com efeito de fade alpha suave e borda iluminada."""
        alpha = int(max(0, min(255, self.alpha_botao)))
        rect = self.botao_pular.rect

        surf_btn = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        cor_base = self.botao_pular.cor_atual
        pygame.draw.rect(
            surf_btn,
            (cor_base[0], cor_base[1], cor_base[2], int(alpha * 0.90)),
            (0, 0, rect.width, rect.height),
            border_radius=self.botao_pular.borda_raio
        )
        # Borda sutil destacada
        cor_borda = (95, 130, 175, alpha) if self.botao_pular.cor_atual == self.botao_pular.cor_hover else (60, 75, 100, int(alpha * 0.8))
        pygame.draw.rect(
            surf_btn,
            cor_borda,
            (0, 0, rect.width, rect.height),
            width=2,
            border_radius=self.botao_pular.borda_raio
        )

        if self.botao_pular.txt_renderizado:
            txt_surf = self.botao_pular.txt_renderizado.copy()
            txt_surf.set_alpha(alpha)
            txt_rect = txt_surf.get_rect(center=(rect.width // 2, rect.height // 2))
            surf_btn.blit(txt_surf, txt_rect)

        self.tela.blit(surf_btn, rect.topleft)

    def _desenhar_placeholder_agente(self):
        """Renderiza uma tela cinemática estilizada em estilo terminal tático cyber para o Agente."""
        tempo_decorrido = time.perf_counter() - self.tempo_inicio

        # Fundo degradê digital
        for y in range(0, self.altura, 4):
            intensidade = int(10 + 6 * math.sin(y * 0.01 + tempo_decorrido * 2.0))
            pygame.draw.line(self.tela, (8, intensidade, intensidade + 12), (0, y), (self.largura, y), 4)

        # Grade cibernética
        cor_grade = (16, 32, 48)
        passo_grade = 50
        for x in range(0, self.largura, passo_grade):
            pygame.draw.line(self.tela, cor_grade, (x, 0), (x, self.altura), 1)
        for y in range(0, self.altura, passo_grade):
            pygame.draw.line(self.tela, cor_grade, (0, y), (self.largura, y), 1)

        # Linha de escaneamento móvel
        y_scan = int((tempo_decorrido * 140) % self.altura)
        surf_scan = pygame.Surface((self.largura, 20), pygame.SRCALPHA)
        surf_scan.fill((0, 200, 255, 30))
        self.tela.blit(surf_scan, (0, y_scan))

        # Moldura de dados táticos centrais
        box_w, box_h = 740, 420
        box_x = (self.largura - box_w) // 2
        box_y = (self.altura - box_h) // 2
        surf_painel = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        surf_painel.fill((12, 18, 28, 220))
        self.tela.blit(surf_painel, (box_x, box_y))
        pygame.draw.rect(self.tela, (0, 180, 220), (box_x, box_y, box_w, box_h), width=2, border_radius=8)

        # Cantos decorativos estilo HUD
        tamanho_canto = 20
        for cx, cy in [(box_x, box_y), (box_x + box_w, box_y), (box_x, box_y + box_h), (box_x + box_w, box_y + box_h)]:
            dx = -tamanho_canto if cx > box_x else tamanho_canto
            dy = -tamanho_canto if cy > box_y else tamanho_canto
            pygame.draw.line(self.tela, (0, 240, 255), (cx, cy), (cx + dx, cy), 3)
            pygame.draw.line(self.tela, (0, 240, 255), (cx, cy), (cx, cy + dy), 3)

        # Cabeçalho tático
        tag = self.fonte_subtitulo.render("[ PROTOCOLO DE CONCLUSÃO DE MISSÃO - AGENTE ]", True, (0, 220, 255))
        self.tela.blit(tag, (self.largura // 2 - tag.get_width() // 2, box_y + 25))

        # Alvo neutralizado
        titulo = self.fonte_titulo.render("ALVO: ESTRAGA PRAZERES [ELIMINADO]", True, (255, 75, 75))
        self.tela.blit(titulo, (self.largura // 2 - titulo.get_width() // 2, box_y + 75))

        # Aviso de Placeholder elegante
        aviso = self.fonte_subtitulo.render("// Cutscene Cinemática do Verso Agente em Desenvolvimento //", True, (255, 215, 80))
        self.tela.blit(aviso, (self.largura // 2 - aviso.get_width() // 2, box_y + 125))

        # Telemetria animada em terminal
        linhas_terminal = [
            "> Conexão neural estabilizada com a Central de Agentes.",
            "> Relatório de combate enviado com sucesso aos servidores centrais.",
            "> A anomalia da fenda urbana foi neutralizada pelos agentes de campo.",
            "> Status da Operação: SUCESSO ABSOLUTO.",
        ]

        linhas_visiveis = min(len(linhas_terminal), int(tempo_decorrido * 1.5) + 1)
        y_linha = box_y + 185
        for i in range(linhas_visiveis):
            txt = self.fonte_info.render(linhas_terminal[i], True, (160, 205, 230))
            self.tela.blit(txt, (box_x + 40, y_linha))
            y_linha += 30

        # Barra de telemetria / sincronização
        progresso_tempo = min(1.0, tempo_decorrido / self.duracao_placeholder)
        largura_carregando = int((box_w - 80) * progresso_tempo)
        pygame.draw.rect(self.tela, (20, 30, 45), (box_x + 40, box_y + box_h - 70, box_w - 80, 14), border_radius=7)
        pygame.draw.rect(self.tela, (0, 200, 255), (box_x + 40, box_y + box_h - 70, largura_carregando, 14), border_radius=7)

        dica = self.fonte_dica.render("Pressione [ESPAÇO] ou use o botão Pular para avançar", True, (120, 150, 180))
        self.tela.blit(dica, (self.largura // 2 - dica.get_width() // 2, box_y + box_h - 40))
