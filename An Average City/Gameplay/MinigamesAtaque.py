import math
import random
import pygame
from typing import Optional, Dict, Any, Tuple, List
from Sistemas.Fontes import obter_fonte
from Sistemas.GerenciadorAudio import tocar_sfx
from Sistemas.SistemaUI import desenhar_painel_container


def normalizar_classe_dano(tipo: str) -> str:
    s = str(tipo or "").strip().lower()
    if "invoc" in s:
        return "Invocador"
    elif "dist" in s:
        return "Distância"
    elif "mag" in s or "feitic" in s:
        return "Magia"
    elif "fis" in s or "fís" in s or "luta" in s:
        return "Físico"
    return "Físico"


class GerenciadorMinigameAtaque:
    """
    Controlador central dos minigames de ataque baseados na classe e estilo do golpe:
    1. Invocador (Controle):
       - Estilo 1: Spam de Espaço para canalizar invocação
       - Estilo 2: Sequência de Teclas (QTE rítmico)
    2. Distância (Precisão):
       - Estilo 1: Clique rápido no retículo/alvo na tela
       - Estilo 2: Alinhamento de duas barras móveis no centro
    3. Feiticeiro / Magia (Controle):
       - Estilo 1: Manter o cursor dentro de uma esfera em movimento
       - Estilo 2: Arrastar a runa/núcleo para o glifo ritual
    4. Lutador / Físico (Impacto):
       - Estilo 1: Acertar a barra de timing consecutivamente no mesmo lugar até errar
       - Estilo 2: Segurar a tecla de força e soltar na zona de impacto máximo
    """

    def __init__(self, tela: Optional[pygame.Surface] = None):
        self.tela = tela
        self.largura = tela.get_width() if tela else 1000
        self.altura = tela.get_height() if tela else 800

        self.ativo: bool = False
        self.hab: Any = None
        self.alvo: Any = None
        self.jogador_ativo: Any = None

        self.classe_normalizada: str = "Físico"
        self.estilo: int = 1

        self.tempo_total: int = 180
        self.tempo_restante: int = 180
        self.timer_encerramento: int = 0  # Pausa de feedback final antes de concluir

        self.concluido: bool = False
        self.resultado: Optional[Dict[str, Any]] = None

        # Fontes do Minigame
        self.fonte_titulo = obter_fonte(17)
        self.fonte_subtitulo = obter_fonte(12)
        self.fonte_instrucao = obter_fonte(12)
        self.fonte_status = obter_fonte(14)
        self.fonte_feedback = obter_fonte(15)
        self.fonte_tecla = obter_fonte(18)
        self.fonte_badge = obter_fonte(10)
        self.tempo_animacao: float = 0.0

        # Retângulo do container central
        self.largura_painel = 520
        self.altura_painel = 320
        self.x_painel = (self.largura - self.largura_painel) // 2
        self.y_painel = (self.altura - self.altura_painel) // 2
        self.rect_painel = pygame.Rect(self.x_painel, self.y_painel, self.largura_painel, self.altura_painel)

        # Superfície de escurecimento de fundo
        self.superficie_overlay = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        self.superficie_overlay.fill((8, 10, 16, 175))

        # Variáveis de estado para cada minigame
        # Invocador 1 (Spam)
        self.invoc_progresso: float = 0.0

        # Invocador 2 (Sequência)
        self.seq_teclas: List[Tuple[str, int, int]] = []
        self.seq_indice: int = 0
        self.seq_erros: int = 0

        # Distância 1 (Alvo Rápido)
        self.dist_alvo_x: float = 500.0
        self.dist_alvo_y: float = 400.0
        self.dist_alvo_raio: float = 38.0
        self.dist_anel_escala: float = 2.6

        # Distância 2 (Alinhamento de 2 barras)
        self.alin_ponto_centro: float = 500.0
        self.alin_trilha_x: float = 300.0
        self.alin_trilha_w: float = 400.0
        self.alin_velocidade_base: float = 5.8
        self.alin_barra1_x: float = 310.0
        self.alin_barra2_x: float = 690.0
        self.alin_barra1_vel: float = 5.8
        self.alin_barra2_vel: float = -5.8
        self.alin_barra1_ativa: bool = True
        self.alin_barra1_travada: bool = False
        self.alin_barra2_ativa: bool = False
        self.alin_barra2_travada: bool = False
        self.alin_etapa: int = 1

        # Feiticeiro 1 (Esfera móvel)
        self.esfera_pos: List[float] = [500.0, 400.0]
        self.esfera_raio: float = 44.0
        self.esfera_tempo_dentro: int = 0
        self.esfera_tempo_decorrido: float = 0.0

        # Feiticeiro 2 (Arrastar objeto)
        self.drag_origem: Tuple[float, float] = (330.0, 400.0)
        self.drag_destino: Tuple[float, float] = (670.0, 400.0)
        self.drag_raio_origem: float = 30.0
        self.drag_raio_destino: float = 44.0
        self.drag_pos_atual: List[float] = [330.0, 400.0]
        self.drag_segurando: bool = False

        # Lutador 1 (Combo rítmico)
        self.combo_cursor_x: float = 500.0
        self.combo_cursor_vel: float = 6.8
        self.combo_trilha_x: float = 300.0
        self.combo_trilha_w: float = 400.0
        self.combo_zona_w: float = 68.0
        self.combo_atual: int = 0
        self.combo_maximo: int = 5

        # Lutador 2 (Barra de força)
        self.forca_atual: float = 0.0
        self.forca_segurando: bool = False
        self.forca_overcharge: bool = False

        # Rastro de partículas e animações
        self.particulas: List[Dict[str, Any]] = []

    def redimensionar(self, largura: int, altura: int):
        """Atualiza dimensões caso a resolução da janela mude."""
        self.largura = max(300, largura)
        self.altura = max(200, altura)
        self.x_painel = (self.largura - self.largura_painel) // 2
        self.y_painel = (self.altura - self.altura_painel) // 2
        self.rect_painel = pygame.Rect(self.x_painel, self.y_painel, self.largura_painel, self.altura_painel)
        self.superficie_overlay = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        self.superficie_overlay.fill((8, 10, 16, 175))

    def esta_ativo(self) -> bool:
        return self.ativo

    def iniciar(self, hab: Any, alvo: Any = None, jogador_ativo: Any = None):
        """Inicializa o minigame adequado conforme o tipo de dano e o estilo da habilidade."""
        self.ativo = True
        self.hab = hab
        self.alvo = alvo
        self.jogador_ativo = jogador_ativo

        self.classe_normalizada = normalizar_classe_dano(getattr(hab, "tipo", "Físico"))
        self.estilo = getattr(hab, "estilo", 1) or 1
        if self.estilo not in (1, 2):
            self.estilo = 1

        self.concluido = False
        self.resultado = None
        self.timer_encerramento = 0
        self.tempo_animacao = 0.0
        self.particulas.clear()

        # Ultimates não possuem minigame: disparam diretamente com sucesso total
        if getattr(hab, "is_ultimate", False):
            self.concluir_instantaneamente(sucesso=True)
            return

        # Configura o minigame específico
        if self.classe_normalizada == "Invocador":
            if self.estilo == 1:
                # Spam de espaço
                self.tempo_total = 160  # ~2.6 segundos
                self.tempo_restante = self.tempo_total
                self.invoc_progresso = 15.0
            else:
                # Sequência de teclas
                self.tempo_total = 210  # ~3.5 segundos
                self.tempo_restante = self.tempo_total
                opcoes_teclas = [
                    ("W", pygame.K_w, pygame.K_UP),
                    ("A", pygame.K_a, pygame.K_LEFT),
                    ("S", pygame.K_s, pygame.K_DOWN),
                    ("D", pygame.K_d, pygame.K_RIGHT),
                ]
                self.seq_teclas = [random.choice(opcoes_teclas) for _ in range(4)]
                self.seq_indice = 0
                self.seq_erros = 0

        elif self.classe_normalizada == "Distância":
            if self.estilo == 1:
                # Alvo rápido de precisão: janela de tempo bem mais rápida para reflexo ágil
                self.tempo_total = 54  # ~0.9 segundos (bem mais rápido!)
                self.tempo_restante = self.tempo_total
                margem_x = 110
                margem_y = 65
                self.dist_alvo_x = random.randint(self.x_painel + margem_x, self.x_painel + self.largura_painel - margem_x)
                self.dist_alvo_y = random.randint(self.y_painel + margem_y + 40, self.y_painel + self.altura_painel - margem_y)
                self.dist_alvo_raio = 36.0
                self.dist_anel_escala = 2.6
            else:
                # Alinhamento de duas barras: surgem uma por vez em lados opostos com a mesma velocidade
                self.tempo_total = 220  # ~3.6 segundos para as duas etapas
                self.tempo_restante = self.tempo_total
                self.alin_ponto_centro = float(self.x_painel + self.largura_painel // 2)
                self.alin_trilha_w = 380.0
                self.alin_trilha_x = float(self.x_painel + (self.largura_painel - self.alin_trilha_w) // 2)

                # Mesma velocidade constante para ambas as barras
                self.alin_velocidade_base = 5.8
                self.alin_etapa = 1

                # Barra 1: surge no lado esquerdo
                self.alin_barra1_x = self.alin_trilha_x + 12.0
                self.alin_barra1_vel = self.alin_velocidade_base
                self.alin_barra1_ativa = True
                self.alin_barra1_travada = False

                # Barra 2: surge posteriormente no lado oposto (direito) com a mesma velocidade
                self.alin_barra2_x = self.alin_trilha_x + self.alin_trilha_w - 12.0
                self.alin_barra2_vel = -self.alin_velocidade_base
                self.alin_barra2_ativa = False
                self.alin_barra2_travada = False

        elif self.classe_normalizada == "Magia":
            if self.estilo == 1:
                # Manter o mouse na esfera móvel
                self.tempo_total = 170  # ~2.8 segundos
                self.tempo_restante = self.tempo_total
                self.esfera_pos = [float(self.x_painel + self.largura_painel // 2), float(self.y_painel + self.altura_painel // 2 + 10)]
                self.esfera_raio = 44.0
                self.esfera_tempo_dentro = 0
                self.esfera_tempo_decorrido = 0.0
            else:
                # Arrastar runa para o glifo ritual
                self.tempo_total = 180  # 3.0 segundos
                self.tempo_restante = self.tempo_total
                self.drag_origem = (float(self.x_painel + 90), float(self.y_painel + 185))
                self.drag_destino = (float(self.x_painel + self.largura_painel - 90), float(self.y_painel + 185))
                self.drag_raio_origem = 30.0
                self.drag_raio_destino = 44.0
                self.drag_pos_atual = list(self.drag_origem)
                self.drag_segurando = False

        else:  # Físico / Lutadores
            if self.estilo == 1:
                # Acertar a barra de timing repetidamente
                self.tempo_total = 260  # Até 4.3 segundos
                self.tempo_restante = self.tempo_total
                self.combo_trilha_w = 380.0
                self.combo_trilha_x = float(self.x_painel + (self.largura_painel - self.combo_trilha_w) // 2)
                self.combo_cursor_x = self.combo_trilha_x + 20.0
                self.combo_cursor_vel = 7.0
                self.combo_zona_w = 66.0
                self.combo_atual = 0
                self.combo_maximo = 5
            else:
                # Segurar força e soltar na zona de impacto
                self.tempo_total = 180  # 3.0 segundos
                self.tempo_restante = self.tempo_total
                self.forca_atual = 0.0
                self.forca_segurando = False
                self.forca_overcharge = False

        try:
            tocar_sfx("Interface.wav", volume_relativo=0.6)
        except Exception:
            pass

    def concluir_instantaneamente(self, sucesso: bool = True):
        """Conclui o minigame de imediato (usado por testes ou skips)."""
        mult = 1.35 if sucesso else 0.8
        feed = "PERFEITO!" if sucesso else "REGULAR"
        desempenho = 1.0 if sucesso else 0.0
        chance_erro = 0.0 if sucesso else 1.0
        self._definir_resultado(mult, feed, sucesso=sucesso, desempenho=desempenho, chance_erro=chance_erro)
        self.ativo = False
        self.timer_encerramento = 0
        self.tempo_animacao = 0.0

    def processar_evento(self, evento: pygame.event.Event, posicao_mouse: Tuple[int, int]):
        """Captura eventos isolados de teclado e cliques de mouse."""
        if not self.ativo or self.concluido:
            return

        # 1. Invocador Estilo 1: Spam de Espaço
        if self.classe_normalizada == "Invocador" and self.estilo == 1:
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_SPACE:
                self.invoc_progresso = min(100.0, self.invoc_progresso + 11.5)
                self._gerar_particulas(self.x_painel + self.largura_painel // 2, self.y_painel + 175, (60, 240, 130), 4)
                try:
                    tocar_sfx("Interface.wav", volume_relativo=0.4)
                except Exception:
                    pass
                if self.invoc_progresso >= 100.0:
                    self._finalizar_invocador_spam()
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if self.rect_painel.collidepoint(posicao_mouse):
                    self.invoc_progresso = min(100.0, self.invoc_progresso + 9.5)
                    self._gerar_particulas(posicao_mouse[0], posicao_mouse[1], (60, 240, 130), 3)

        # 2. Invocador Estilo 2: Sequência de Teclas
        elif self.classe_normalizada == "Invocador" and self.estilo == 2:
            if evento.type == pygame.KEYDOWN:
                if self.seq_indice < len(self.seq_teclas):
                    alvo_nome, k_char, k_arrow = self.seq_teclas[self.seq_indice]
                    if evento.key in (k_char, k_arrow):
                        self.seq_indice += 1
                        try:
                            tocar_sfx("Interface.wav", volume_relativo=0.7)
                        except Exception:
                            pass
                        if self.seq_indice >= len(self.seq_teclas):
                            self._finalizar_invocador_sequencia()
                    else:
                        self.seq_erros += 1
                        try:
                            tocar_sfx("Dano.wav", volume_relativo=0.4)
                        except Exception:
                            pass

        # 3. Distância Estilo 1: Retículo / Alvo Rápido
        elif self.classe_normalizada == "Distância" and self.estilo == 1:
            if (evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1) or \
               (evento.type == pygame.KEYDOWN and evento.key in (pygame.K_SPACE, pygame.K_RETURN)):
                dist = math.hypot(posicao_mouse[0] - self.dist_alvo_x, posicao_mouse[1] - self.dist_alvo_y)
                self._finalizar_distancia_alvo(dist)

        # 4. Distância Estilo 2: Alinhamento das Barras (1 por vez em lados opostos com mesma velocidade)
        elif self.classe_normalizada == "Distância" and self.estilo == 2:
            if (evento.type == pygame.KEYDOWN and evento.key in (pygame.K_SPACE, pygame.K_RETURN)) or \
               (evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1):
                if self.alin_etapa == 1:
                    # Trava a barra 1 e aciona a barra 2 no lado oposto com a mesma velocidade
                    self.alin_barra1_travada = True
                    self.alin_etapa = 2
                    self.alin_barra2_ativa = True
                    try:
                        tocar_sfx("Interface.wav", volume_relativo=0.85)
                    except Exception:
                        pass
                    self._gerar_particulas(self.alin_barra1_x, self.y_painel + 155, (50, 200, 255), 8)
                else:
                    # Trava a barra 2 e conclui o alinhamento
                    self.alin_barra2_travada = True
                    self._finalizar_distancia_alinhamento()

        # 5. Feiticeiro Estilo 1: Disparo antecipado de concentração
        elif self.classe_normalizada == "Magia" and self.estilo == 1:
            if (evento.type == pygame.KEYDOWN and evento.key in (pygame.K_SPACE, pygame.K_RETURN)) or \
               (evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1):
                self._finalizar_feiticeiro_esfera()

        # 6. Feiticeiro Estilo 2: Arrastar Runa
        elif self.classe_normalizada == "Magia" and self.estilo == 2:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                dist_pos = math.hypot(posicao_mouse[0] - self.drag_pos_atual[0], posicao_mouse[1] - self.drag_pos_atual[1])
                dist_orig = math.hypot(posicao_mouse[0] - self.drag_origem[0], posicao_mouse[1] - self.drag_origem[1])
                dist_dest = math.hypot(posicao_mouse[0] - self.drag_destino[0], posicao_mouse[1] - self.drag_destino[1])

                # Clique na runa ou próximo à base de origem inicia o arrasto
                if dist_pos <= self.drag_raio_origem + 28 or dist_orig <= self.drag_raio_origem + 28:
                    self.drag_segurando = True
                # Se clicou diretamente no glifo de destino, teletransporta e ativa
                elif dist_dest <= self.drag_raio_destino + 15:
                    self.drag_pos_atual = list(self.drag_destino)
                    self._finalizar_feiticeiro_arrastar(0.0)

            elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
                if self.drag_segurando:
                    self.drag_segurando = False
                    dist_dest = math.hypot(self.drag_pos_atual[0] - self.drag_destino[0], self.drag_pos_atual[1] - self.drag_destino[1])
                    if dist_dest <= self.drag_raio_destino * 1.5:
                        self._finalizar_feiticeiro_arrastar(dist_dest)
                    else:
                        self._gerar_particulas(self.drag_pos_atual[0], self.drag_pos_atual[1], (180, 110, 255), 4)

            elif evento.type == pygame.KEYDOWN and evento.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_d, pygame.K_RIGHT):
                self.drag_pos_atual = list(self.drag_destino)
                self._finalizar_feiticeiro_arrastar(0.0)

        # 7. Lutador Estilo 1: Combo de Timing
        elif self.classe_normalizada == "Físico" and self.estilo == 1:
            if (evento.type == pygame.KEYDOWN and evento.key in (pygame.K_SPACE, pygame.K_RETURN)) or \
               (evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1):
                centro_trilha = self.combo_trilha_x + self.combo_trilha_w / 2
                dist_zona = abs(self.combo_cursor_x - centro_trilha)
                if dist_zona <= (self.combo_zona_w / 2):
                    self.combo_atual += 1
                    try:
                        tocar_sfx("Soco.wav", volume_relativo=0.85)
                    except Exception:
                        pass
                    self._gerar_particulas(self.combo_cursor_x, self.y_painel + 185, (255, 190, 40), 6)
                    # Inverte e aumenta velocidade
                    direcao = -1 if self.combo_cursor_vel > 0 else 1
                    self.combo_cursor_vel = direcao * (abs(self.combo_cursor_vel) + 1.8)
                    if self.combo_atual >= self.combo_maximo:
                        self._finalizar_lutador_combo()
                else:
                    # Errou o tempo da barra
                    self._finalizar_lutador_combo(errou=True)

        # 8. Lutador Estilo 2: Carregar Força
        elif self.classe_normalizada == "Físico" and self.estilo == 2:
            if evento.type == pygame.KEYDOWN and evento.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.forca_segurando = True
            elif evento.type == pygame.KEYUP and evento.key in (pygame.K_SPACE, pygame.K_RETURN):
                if self.forca_segurando:
                    self.forca_segurando = False
                    self._finalizar_lutador_forca()
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if self.rect_painel.collidepoint(posicao_mouse):
                    self.forca_segurando = True
            elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
                if self.forca_segurando:
                    self.forca_segurando = False
                    self._finalizar_lutador_forca()

    def atualizar(self, posicao_mouse: Tuple[int, int], estado_clique_mouse: Tuple[bool, ...], teclas_pressionadas=None) -> Optional[Dict[str, Any]]:
        """Atualiza a lógica contínua dos minigames em tempo real."""
        if not self.ativo:
            return None

        # Se já concluído, segura o feedback por alguns frames antes de retornar o resultado ao combate
        if self.concluido:
            self.timer_encerramento += 1
            if self.timer_encerramento >= 14:
                self.ativo = False
                res = dict(self.resultado or {})
                res["concluido"] = True
                return res
            return None

        self.tempo_restante -= 1
        self.tempo_animacao += 0.05

        # Atualiza partículas visuais
        for p in self.particulas[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vida"] -= 1
            if p["vida"] <= 0:
                self.particulas.remove(p)

        # Lógica contínua por minigame
        if self.classe_normalizada == "Invocador":
            if self.estilo == 1:
                # Decaimento suave da barra
                self.invoc_progresso = max(0.0, self.invoc_progresso - 0.28)
                if self.tempo_restante <= 0:
                    self._finalizar_invocador_spam()
            else:
                if self.tempo_restante <= 0:
                    self._finalizar_invocador_sequencia()

        elif self.classe_normalizada == "Distância":
            if self.estilo == 1:
                # Anel de mira contrai de forma bem mais rápida
                progresso_tempo = max(0.0, self.tempo_restante / max(1, self.tempo_total))
                self.dist_anel_escala = 1.0 + (progresso_tempo * 1.8)
                if self.tempo_restante <= 0 and not self.concluido:
                    self._finalizar_distancia_alvo(999.0)
            else:
                # Etapa 1: Movimento da Barra 1 (surgida na esquerda)
                if self.alin_etapa == 1 and self.alin_barra1_ativa and not self.alin_barra1_travada:
                    self.alin_barra1_x += self.alin_barra1_vel
                    if self.alin_barra1_x < self.alin_trilha_x or self.alin_barra1_x > (self.alin_trilha_x + self.alin_trilha_w):
                        self.alin_barra1_vel *= -1
                        self.alin_barra1_x = max(self.alin_trilha_x, min(self.alin_barra1_x, self.alin_trilha_x + self.alin_trilha_w))

                # Etapa 2: Movimento da Barra 2 (surgida no lado oposto com a MESMA velocidade)
                elif self.alin_etapa == 2 and self.alin_barra2_ativa and not self.alin_barra2_travada:
                    self.alin_barra2_x += self.alin_barra2_vel
                    if self.alin_barra2_x < self.alin_trilha_x or self.alin_barra2_x > (self.alin_trilha_x + self.alin_trilha_w):
                        self.alin_barra2_vel *= -1
                        self.alin_barra2_x = max(self.alin_trilha_x, min(self.alin_barra2_x, self.alin_trilha_x + self.alin_trilha_w))

                if self.tempo_restante <= 0 and not self.concluido:
                    self._finalizar_distancia_alinhamento()

        elif self.classe_normalizada == "Magia":
            if self.estilo == 1:
                # Esfera se move em órbita suave
                self.esfera_tempo_decorrido += 0.04
                cx = self.x_painel + self.largura_painel // 2
                cy = self.y_painel + self.altura_painel // 2 + 10
                self.esfera_pos[0] = cx + math.sin(self.esfera_tempo_decorrido * 1.1) * 150 + math.cos(self.esfera_tempo_decorrido * 0.6) * 45
                self.esfera_pos[1] = cy + math.cos(self.esfera_tempo_decorrido * 1.3) * 60 + math.sin(self.esfera_tempo_decorrido * 0.8) * 30

                # Verifica se o mouse está dentro da esfera
                dist_mouse = math.hypot(posicao_mouse[0] - self.esfera_pos[0], posicao_mouse[1] - self.esfera_pos[1])
                if dist_mouse <= self.esfera_raio:
                    self.esfera_tempo_dentro += 1
                    if random.random() < 0.4:
                        self._gerar_particulas(posicao_mouse[0], posicao_mouse[1], (180, 100, 255), 2)
                    # Encerra antecipadamente se atingir 75% de canalização perfeita
                    if self.esfera_tempo_dentro >= int(self.tempo_total * 0.72):
                        self._finalizar_feiticeiro_esfera()

                if self.tempo_restante <= 0 and not self.concluido:
                    self._finalizar_feiticeiro_esfera()
            else:
                # Arrastar runa com o mouse
                clicando = estado_clique_mouse[0] if estado_clique_mouse else False

                # Detecção contínua de clique para não perder início de arrasto
                if clicando and not self.drag_segurando:
                    dist_pos = math.hypot(posicao_mouse[0] - self.drag_pos_atual[0], posicao_mouse[1] - self.drag_pos_atual[1])
                    dist_orig = math.hypot(posicao_mouse[0] - self.drag_origem[0], posicao_mouse[1] - self.drag_origem[1])
                    if dist_pos <= self.drag_raio_origem + 30 or dist_orig <= self.drag_raio_origem + 30:
                        self.drag_segurando = True

                if self.drag_segurando:
                    min_x = float(self.x_painel + 30)
                    max_x = float(self.x_painel + self.largura_painel - 30)
                    min_y = float(self.y_painel + 80)
                    max_y = float(self.y_painel + self.altura_painel - 30)

                    self.drag_pos_atual[0] = max(min_x, min(float(posicao_mouse[0]), max_x))
                    self.drag_pos_atual[1] = max(min_y, min(float(posicao_mouse[1]), max_y))

                    if not clicando:
                        self.drag_segurando = False
                        dist_dest = math.hypot(self.drag_pos_atual[0] - self.drag_destino[0], self.drag_pos_atual[1] - self.drag_destino[1])
                        if dist_dest <= self.drag_raio_destino * 1.5:
                            self._finalizar_feiticeiro_arrastar(dist_dest)
                    else:
                        dist_dest = math.hypot(self.drag_pos_atual[0] - self.drag_destino[0], self.drag_pos_atual[1] - self.drag_destino[1])

                        # Efeito magnético de atração suave ao se aproximar do centro do glifo
                        if dist_dest <= self.drag_raio_destino + 25:
                            fator_ima = 0.22
                            self.drag_pos_atual[0] += (self.drag_destino[0] - self.drag_pos_atual[0]) * fator_ima
                            self.drag_pos_atual[1] += (self.drag_destino[1] - self.drag_pos_atual[1]) * fator_ima
                            dist_dest = math.hypot(self.drag_pos_atual[0] - self.drag_destino[0], self.drag_pos_atual[1] - self.drag_destino[1])

                        if random.random() < 0.4:
                            self._gerar_particulas(self.drag_pos_atual[0], self.drag_pos_atual[1], (180, 120, 255), 2)

                        # Encaixe automático imediato ao alcançar o núcleo do glifo!
                        if dist_dest <= 26.0:
                            self.drag_pos_atual = list(self.drag_destino)
                            self._finalizar_feiticeiro_arrastar(dist_dest)
                else:
                    # Se solta longe do destino, retorna suavemente para a origem
                    dist_orig = math.hypot(self.drag_pos_atual[0] - self.drag_origem[0], self.drag_pos_atual[1] - self.drag_origem[1])
                    if dist_orig > 4.0 and not self.concluido:
                        self.drag_pos_atual[0] += (self.drag_origem[0] - self.drag_pos_atual[0]) * 0.18
                        self.drag_pos_atual[1] += (self.drag_origem[1] - self.drag_pos_atual[1]) * 0.18

                if self.tempo_restante <= 0 and not self.concluido:
                    dist_dest = math.hypot(self.drag_pos_atual[0] - self.drag_destino[0], self.drag_pos_atual[1] - self.drag_destino[1])
                    if dist_dest <= self.drag_raio_destino * 1.5:
                        self._finalizar_feiticeiro_arrastar(dist_dest)
                    else:
                        self._finalizar_feiticeiro_arrastar(999.0)

        else:  # Físico / Lutador
            if self.estilo == 1:
                # Movimento contínuo do cursor de timing
                self.combo_cursor_x += self.combo_cursor_vel
                if self.combo_cursor_x < self.combo_trilha_x or self.combo_cursor_x > (self.combo_trilha_x + self.combo_trilha_w):
                    self.combo_cursor_vel *= -1
                    self.combo_cursor_x = max(self.combo_trilha_x, min(self.combo_cursor_x, self.combo_trilha_x + self.combo_trilha_w))

                if self.tempo_restante <= 0 and not self.concluido:
                    self._finalizar_lutador_combo(errou=True)
            else:
                # Sincronização automática contínua de carga e liberação
                espaco_down = bool(teclas_pressionadas[pygame.K_SPACE]) if teclas_pressionadas is not None else False
                mouse_down = bool(estado_clique_mouse[0]) if estado_clique_mouse else False

                if espaco_down or (mouse_down and self.rect_painel.collidepoint(posicao_mouse)):
                    self.forca_segurando = True

                if self.forca_segurando:
                    if not espaco_down and not mouse_down:
                        self.forca_segurando = False
                        self._finalizar_lutador_forca()
                    else:
                        self.forca_atual += 1.65
                        if random.random() < 0.3:
                            self._gerar_particulas(self.x_painel + self.largura_painel // 2, self.y_painel + 185, (255, 120, 40), 2)

                        if self.forca_atual >= 100.0:
                            self.forca_overcharge = True
                            self.forca_segurando = False
                            self._finalizar_lutador_forca()

                if self.tempo_restante <= 0 and not self.concluido:
                    self._finalizar_lutador_forca()

        # Garantia absoluta de finalização quando tempo zera
        if self.tempo_restante <= 0 and not self.concluido:
            if self.classe_normalizada == "Invocador":
                if self.estilo == 1:
                    self._finalizar_invocador_spam()
                else:
                    self._finalizar_invocador_sequencia()
            elif self.classe_normalizada == "Distância":
                if self.estilo == 1:
                    self._finalizar_distancia_alvo(999.0)
                else:
                    self._finalizar_distancia_alinhamento()
            elif self.classe_normalizada == "Magia":
                if self.estilo == 1:
                    self._finalizar_feiticeiro_esfera()
                else:
                    self._finalizar_feiticeiro_arrastar(999.0)
            else:
                if self.estilo == 1:
                    self._finalizar_lutador_combo(errou=True)
                else:
                    self._finalizar_lutador_forca()

        return None

    def _gerar_particulas(self, x: float, y: float, cor: Tuple[int, int, int], qtd: int = 4):
        for _ in range(qtd):
            self.particulas.append({
                "x": x + random.uniform(-4, 4),
                "y": y + random.uniform(-4, 4),
                "vx": random.uniform(-2.5, 2.5),
                "vy": random.uniform(-2.5, 2.5),
                "cor": cor,
                "raio": random.randint(2, 4),
                "vida": random.randint(12, 22)
            })

    # ==================== FINALIZAÇÕES DE RESULTADO ====================

    def _definir_resultado(self, multiplicador: float, feedback: str, sucesso: bool, screen_shake: bool = False, desempenho: float = 1.0, chance_erro: float = 0.0):
        self.concluido = True
        self.timer_encerramento = 0
        self.tempo_animacao = 0.0
        self.resultado = {
            "concluido": True,
            "multiplicador": multiplicador,
            "feedback": feedback,
            "sucesso": sucesso,
            "screen_shake": screen_shake,
            "desempenho": float(desempenho),
            "chance_erro": float(chance_erro)
        }
        try:
            if sucesso and chance_erro <= 0.2:
                tocar_sfx("Acerto.wav", volume_relativo=0.9)
            else:
                tocar_sfx("Dano.wav", volume_relativo=0.6)
        except Exception:
            pass

    def _finalizar_invocador_spam(self):
        pct = self.invoc_progresso
        if pct >= 88.0:
            self._definir_resultado(1.40, "⚡ INCRÍVEL! Sincronização Perfeita (+40%)", sucesso=True, desempenho=1.0, chance_erro=0.0)
        elif pct >= 55.0:
            self._definir_resultado(1.20, "✨ BOM! Invocação Estável (+20%)", sucesso=True, desempenho=0.85, chance_erro=0.0)
        elif pct >= 25.0:
            self._definir_resultado(1.00, "CANALIZAÇÃO REGULAR", sucesso=True, desempenho=0.50, chance_erro=0.20)
        else:
            self._definir_resultado(0.85, "⚠️ Invocação Fraca (-15%)", sucesso=False, desempenho=0.15, chance_erro=(0.75 if pct > 0 else 1.0))

    def _finalizar_invocador_sequencia(self):
        total = len(self.seq_teclas)
        acertos = self.seq_indice
        if acertos == total and self.seq_erros == 0:
            self._definir_resultado(1.40, "⚡ PERFEITO! Sequência Rápida (+40%)", sucesso=True, desempenho=1.0, chance_erro=0.0)
        elif acertos == total:
            self._definir_resultado(1.20, "✨ SUCESSO! Sequência Concluída (+20%)", sucesso=True, desempenho=0.85, chance_erro=0.0)
        elif acertos >= 2:
            self._definir_resultado(1.00, "COMANDO PARCIAL", sucesso=True, desempenho=0.50, chance_erro=0.25)
        else:
            self._definir_resultado(0.75, "❌ SEQUÊNCIA INTERROMPIDA (-25%)", sucesso=False, desempenho=(0.10 if acertos == 1 else 0.0), chance_erro=(0.80 if acertos == 1 else 1.0))

    def _finalizar_distancia_alvo(self, dist: float):
        if dist <= 22.0:
            self._definir_resultado(1.45, "🎯 BULLSEYE! TIRO PERFEITO (+45%)", sucesso=True, screen_shake=True, desempenho=1.0, chance_erro=0.0)
        elif dist <= 50.0:
            self._definir_resultado(1.20, "🏹 BOM DISPARO! (+20%)", sucesso=True, desempenho=0.80, chance_erro=0.0)
        elif dist <= 85.0:
            self._definir_resultado(1.00, "TIRO REGULAR", sucesso=True, desempenho=0.50, chance_erro=0.25)
        else:
            self._definir_resultado(0.70, "❌ ERROU O ALVO! (-30%)", sucesso=False, desempenho=0.0, chance_erro=1.0)

    def _finalizar_distancia_alinhamento(self):
        if self.tempo_restante <= 0 and not (self.alin_barra1_travada and self.alin_barra2_travada):
            self._definir_resultado(0.70, "❌ TEMPO ESGOTADO! (MIRA PERDIDA)", sucesso=False, desempenho=0.0, chance_erro=1.0)
            try:
                tocar_sfx("Dano.wav", volume_relativo=0.5)
            except Exception:
                pass
            return

        diff = abs(self.alin_barra1_x - self.alin_barra2_x)
        dist_centro = abs(((self.alin_barra1_x + self.alin_barra2_x) / 2) - self.alin_ponto_centro)
        erro_total = diff + dist_centro * 0.35

        if erro_total <= 24.0:
            self._definir_resultado(1.45, "🎯 MIRA PERFEITAMENTE ALINHADA! (+45%)", sucesso=True, screen_shake=True, desempenho=1.0, chance_erro=0.0)
            self._gerar_particulas(self.alin_barra2_x, self.y_painel + 155, (255, 220, 80), 12)
            try:
                tocar_sfx("Acerto.wav", volume_relativo=1.0)
            except Exception:
                pass
        elif erro_total <= 65.0:
            self._definir_resultado(1.25, "🏹 MIRA SINCRONIZADA (+25%)", sucesso=True, desempenho=0.85, chance_erro=0.0)
            self._gerar_particulas(self.alin_barra2_x, self.y_painel + 155, (50, 210, 255), 8)
            try:
                tocar_sfx("Acerto.wav", volume_relativo=0.8)
            except Exception:
                pass
        elif erro_total <= 120.0:
            self._definir_resultado(1.05, "MIRA PARCIAL (+5%)", sucesso=True, desempenho=0.55, chance_erro=0.20)
            try:
                tocar_sfx("Interface.wav", volume_relativo=0.7)
            except Exception:
                pass
        else:
            self._definir_resultado(0.75, "❌ MIRA DESALINHADA (-25%)", sucesso=False, desempenho=0.0, chance_erro=1.0)
            try:
                tocar_sfx("Dano.wav", volume_relativo=0.5)
            except Exception:
                pass

    def _finalizar_feiticeiro_esfera(self):
        taxa = self.esfera_tempo_dentro / max(1, self.tempo_total)
        if taxa >= 0.70:
            self._definir_resultado(1.40, "⚡ CANALIZAÇÃO PERFEITA! PODER MÁXIMO (+40%)", sucesso=True, screen_shake=True, desempenho=1.0, chance_erro=0.0)
        elif taxa >= 0.40:
            self._definir_resultado(1.20, "✨ CANALIZAÇÃO ESTÁVEL (+20%)", sucesso=True, desempenho=0.80, chance_erro=0.0)
        elif taxa >= 0.20:
            self._definir_resultado(1.00, "CANALIZAÇÃO PARCIAL", sucesso=True, desempenho=0.50, chance_erro=0.25)
        else:
            self._definir_resultado(0.75, "❌ FALHA DE CONCENTRAÇÃO (-25%)", sucesso=False, desempenho=max(0.0, taxa), chance_erro=(0.85 if taxa > 0.05 else 1.0))

    def _finalizar_feiticeiro_arrastar(self, dist_dest: float):
        if dist_dest <= 26.0:
            self._definir_resultado(1.40, "⚡ RITUAL PERFEITO NO NÚCLEO (+40%)", sucesso=True, screen_shake=True, desempenho=1.0, chance_erro=0.0)
            self._gerar_particulas(self.drag_destino[0], self.drag_destino[1], (255, 220, 90), qtd=12)
            self._gerar_particulas(self.drag_destino[0], self.drag_destino[1], (200, 110, 255), qtd=10)
            try:
                tocar_sfx("Acerto.wav", volume_relativo=1.0)
            except Exception:
                pass
        elif dist_dest <= self.drag_raio_destino:
            self._definir_resultado(1.25, "✨ GLIFO ATIVADO COM SUCESSO (+25%)", sucesso=True, desempenho=0.85, chance_erro=0.0)
            self._gerar_particulas(self.drag_destino[0], self.drag_destino[1], (180, 130, 255), qtd=8)
            try:
                tocar_sfx("Acerto.wav", volume_relativo=0.85)
            except Exception:
                pass
        elif dist_dest <= self.drag_raio_destino * 1.5:
            self._definir_resultado(1.05, "RITUAL PARCIAL (+5%)", sucesso=True, desempenho=0.60, chance_erro=0.20)
            try:
                tocar_sfx("Interface.wav", volume_relativo=0.7)
            except Exception:
                pass
        else:
            self._definir_resultado(0.75, "❌ RITUAL INCOMPLETO (-25%)", sucesso=False, desempenho=0.0, chance_erro=1.0)
            try:
                tocar_sfx("Dano.wav", volume_relativo=0.5)
            except Exception:
                pass

    def _finalizar_lutador_combo(self, errou: bool = False):
        if errou or self.combo_atual == 0:
            self._definir_resultado(0.70, "❌ ERROU O TEMPO DE IMPACTO (-30%)", sucesso=False, desempenho=0.0, chance_erro=1.0)
        elif self.combo_atual >= 4:
            self._definir_resultado(1.45, f"💥 COMBO DEVASTADOR! ({self.combo_atual} HITS! +45%)", sucesso=True, screen_shake=True, desempenho=1.0, chance_erro=0.0)
        elif self.combo_atual >= 2:
            self._definir_resultado(1.25, f"👊 BOM COMBO! ({self.combo_atual} HITS! +25%)", sucesso=True, desempenho=0.80, chance_erro=0.0)
        else:
            self._definir_resultado(1.05, "IMPACTO REGULAR (+5%)", sucesso=True, desempenho=0.50, chance_erro=0.25)

    def _finalizar_lutador_forca(self):
        if self.forca_overcharge:
            self._definir_resultado(0.70, "⚠️ SOBRECARGA! IMPACTO DESPERDIÇADO (-30%)", sucesso=False, desempenho=0.0, chance_erro=1.0)
        elif self.tempo_restante <= 0 and self.forca_atual <= 1.0:
            self._definir_resultado(0.70, "❌ TEMPO ESGOTADO! SEM FORÇA", sucesso=False, desempenho=0.0, chance_erro=1.0)
        elif 80.0 <= self.forca_atual <= 95.0:
            self._definir_resultado(1.45, "💥 FORÇA MÁXIMA DEVASTADORA! (+45%)", sucesso=True, screen_shake=True, desempenho=1.0, chance_erro=0.0)
        elif 60.0 <= self.forca_atual < 80.0:
            self._definir_resultado(1.20, "👊 GOLPE FORTE! (+20%)", sucesso=True, desempenho=0.80, chance_erro=0.0)
        elif self.forca_atual > 95.0:
            self._definir_resultado(1.10, "FORÇA EXCESSIVA", sucesso=True, desempenho=0.65, chance_erro=0.15)
        else:
            self._definir_resultado(0.80, "FORÇA INSUFICIENTE (-20%)", sucesso=False, desempenho=0.30, chance_erro=0.65)

    # ==================== RENDERIZAÇÃO VISUAL ====================

    def desenhar(self, superficie: pygame.Surface):
        if not self.ativo:
            return

        # 1. Overlay escurecido
        superficie.blit(self.superficie_overlay, (0, 0))

        # Cores temáticas por classe
        cores_classe = {
            "Invocador": ((40, 180, 90), (60, 240, 130), "INVOCADOR • CONTROLE"),
            "Distância": ((0, 140, 220), (50, 210, 255), "DISTÂNCIA • PRECISÃO"),
            "Magia": ((140, 50, 200), (200, 90, 255), "FEITICEIRO • CONTROLE"),
            "Físico": ((210, 60, 30), (255, 120, 50), "LUTADOR • IMPACTO"),
        }
        cor_base_classe, cor_tema, rotulo_classe = cores_classe.get(self.classe_normalizada, ((80, 90, 110), (180, 190, 210), "ATAQUE"))

        # 2. Painel central
        desenhar_painel_container(
            superficie,
            self.rect_painel,
            nome_sprite="painel_base.png",
            fallback_cor=(20, 24, 34),
            borda_cor=cor_tema
        )

        # 3. Cabeçalho do Painel
        nome_hab = getattr(self.hab, "nome", "Ataque").upper()
        txt_titulo = self.fonte_titulo.render(nome_hab, True, (255, 255, 255))
        superficie.blit(txt_titulo, (self.x_painel + (self.largura_painel - txt_titulo.get_width()) // 2, self.y_painel + 16))

        txt_sub = self.fonte_subtitulo.render(f"[ {rotulo_classe} ]", True, cor_tema)
        superficie.blit(txt_sub, (self.x_painel + (self.largura_painel - txt_sub.get_width()) // 2, self.y_painel + 44))

        # 4. Barra de tempo restante no topo do painel
        prog_tempo = max(0.0, self.tempo_restante / max(1, self.tempo_total))
        w_tempo = int((self.largura_painel - 40) * prog_tempo)
        rect_timer_bg = pygame.Rect(self.x_painel + 20, self.y_painel + 68, self.largura_painel - 40, 6)
        rect_timer_fg = pygame.Rect(self.x_painel + 20, self.y_painel + 68, w_tempo, 6)
        pygame.draw.rect(superficie, (30, 35, 48), rect_timer_bg, border_radius=3)
        cor_timer = (60, 220, 100) if prog_tempo > 0.4 else ((240, 200, 40) if prog_tempo > 0.2 else (240, 60, 60))
        if w_tempo > 0:
            pygame.draw.rect(superficie, cor_timer, rect_timer_fg, border_radius=3)

        # 5. Desenho das partículas
        for p in self.particulas:
            pygame.draw.circle(superficie, p["cor"], (int(p["x"]), int(p["y"])), p["raio"])

        # 6. Renderização da mecânica ativa
        if self.classe_normalizada == "Invocador":
            if self.estilo == 1:
                self._desenhar_invocador_spam(superficie, cor_tema)
            else:
                self._desenhar_invocador_sequencia(superficie, cor_tema)

        elif self.classe_normalizada == "Distância":
            if self.estilo == 1:
                self._desenhar_distancia_alvo(superficie, cor_tema)
            else:
                self._desenhar_distancia_alinhamento(superficie, cor_tema)

        elif self.classe_normalizada == "Magia":
            if self.estilo == 1:
                self._desenhar_feiticeiro_esfera(superficie, cor_tema)
            else:
                self._desenhar_feiticeiro_arrastar(superficie, cor_tema)

        else:  # Físico / Lutador
            if self.estilo == 1:
                self._desenhar_lutador_combo(superficie, cor_tema)
            else:
                self._desenhar_lutador_forca(superficie, cor_tema)

        # 7. Exibição do feedback final ao concluir
        if self.concluido and self.resultado:
            self._desenhar_feedback_final(superficie)

    # ---------- Renderizadores Específicos ----------

    def _desenhar_invocador_spam(self, tela: pygame.Surface, cor_tema: Tuple[int, int, int]):
        bx = self.x_painel + 60
        by = self.y_painel + 155
        bw = self.largura_painel - 120
        bh = 32

        pygame.draw.rect(tela, (25, 30, 42), (bx, by, bw, bh), border_radius=8)
        largura_ativa = int(bw * (self.invoc_progresso / 100.0))
        if largura_ativa > 0:
            cor_barra = (60, 220, 130) if self.invoc_progresso < 88.0 else (255, 220, 60)
            pygame.draw.rect(tela, cor_barra, (bx, by, largura_ativa, bh), border_radius=8)
        pygame.draw.rect(tela, cor_tema, (bx, by, bw, bh), width=2, border_radius=8)

        # Marcador da meta 88%
        x_meta = bx + int(bw * 0.88)
        pygame.draw.line(tela, (255, 255, 255), (x_meta, by - 4), (x_meta, by + bh + 4), 2)

        txt_pct = self.fonte_status.render(f"{int(self.invoc_progresso)}%", True, (255, 255, 255))
        tela.blit(txt_pct, (bx + (bw - txt_pct.get_width()) // 2, by + 6))

        txt_instr = self.fonte_instrucao.render("⚡ APERTE [ESPAÇO] REPETIDAMENTE PARA INVOCAR! ⚡", True, (240, 245, 255))
        tela.blit(txt_instr, (self.x_painel + (self.largura_painel - txt_instr.get_width()) // 2, self.y_painel + 225))

    def _desenhar_invocador_sequencia(self, tela: pygame.Surface, cor_tema: Tuple[int, int, int]):
        num_teclas = len(self.seq_teclas)
        tamanho_caixa = 54
        espacamento = 24
        largura_total = num_teclas * tamanho_caixa + (num_teclas - 1) * espacamento
        x_inicio = self.x_painel + (self.largura_painel - largura_total) // 2
        y_pos = self.y_painel + 140

        for i, (nome_tecla, _, _) in enumerate(self.seq_teclas):
            cx = x_inicio + i * (tamanho_caixa + espacamento)
            rect_caixa = pygame.Rect(cx, y_pos, tamanho_caixa, tamanho_caixa)

            if i < self.seq_indice:
                # Concluída
                pygame.draw.rect(tela, (35, 130, 70), rect_caixa, border_radius=10)
                pygame.draw.rect(tela, (60, 240, 130), rect_caixa, width=3, border_radius=10)
                txt_ok = self.fonte_tecla.render("✓", True, (255, 255, 255))
                tela.blit(txt_ok, (cx + (tamanho_caixa - txt_ok.get_width()) // 2, y_pos + (tamanho_caixa - txt_ok.get_height()) // 2))
            elif i == self.seq_indice:
                # Tecla ativa
                pygame.draw.rect(tela, (55, 65, 90), rect_caixa, border_radius=10)
                pygame.draw.rect(tela, (255, 220, 60), rect_caixa, width=3, border_radius=10)
                txt_letra = self.fonte_tecla.render(nome_tecla, True, (255, 220, 60))
                tela.blit(txt_letra, (cx + (tamanho_caixa - txt_letra.get_width()) // 2, y_pos + (tamanho_caixa - txt_letra.get_height()) // 2))
            else:
                # Próximas
                pygame.draw.rect(tela, (25, 30, 42), rect_caixa, border_radius=10)
                pygame.draw.rect(tela, (60, 70, 90), rect_caixa, width=2, border_radius=10)
                txt_letra = self.fonte_tecla.render(nome_tecla, True, (150, 160, 180))
                tela.blit(txt_letra, (cx + (tamanho_caixa - txt_letra.get_width()) // 2, y_pos + (tamanho_caixa - txt_letra.get_height()) // 2))

        txt_instr = self.fonte_instrucao.render("DIGITE A SEQUÊNCIA DE TECLAS NO MOMENTO CERTO!", True, (240, 245, 255))
        tela.blit(txt_instr, (self.x_painel + (self.largura_painel - txt_instr.get_width()) // 2, self.y_painel + 225))

    def _desenhar_distancia_alvo(self, tela: pygame.Surface, cor_tema: Tuple[int, int, int]):
        ax, ay = int(self.dist_alvo_x), int(self.dist_alvo_y)

        # Anel de contração de tempo rápida
        raio_anel = int(self.dist_alvo_raio * self.dist_anel_escala)
        if raio_anel > 0:
            pygame.draw.circle(tela, (255, 215, 60), (ax, ay), raio_anel, width=2)

        # Retículo central
        pygame.draw.circle(tela, (20, 50, 80), (ax, ay), int(self.dist_alvo_raio))
        pygame.draw.circle(tela, (40, 160, 240), (ax, ay), int(self.dist_alvo_raio), width=2)
        pygame.draw.circle(tela, (255, 60, 60), (ax, ay), 18)
        pygame.draw.circle(tela, (255, 255, 255), (ax, ay), 7)

        # Cruz de mira
        pygame.draw.line(tela, (240, 240, 240), (ax - 48, ay), (ax + 48, ay), 2)
        pygame.draw.line(tela, (240, 240, 240), (ax, ay - 48), (ax, ay + 48), 2)

        txt_instr = self.fonte_instrucao.render("DISPARO RÁPIDO! CLIQUE NO CENTRO DO ALVO AGORA!", True, (255, 230, 90))
        tela.blit(txt_instr, (self.x_painel + (self.largura_painel - txt_instr.get_width()) // 2, self.y_painel + 240))

    def _desenhar_distancia_alinhamento(self, tela: pygame.Surface, cor_tema: Tuple[int, int, int]):
        tx = int(self.alin_trilha_x)
        ty = self.y_painel + 155
        tw = int(self.alin_trilha_w)
        th = 32

        # 1. Trilha de Precisão
        pygame.draw.rect(tela, (20, 26, 38), (tx, ty, tw, th), border_radius=6)

        # 2. Zona central de referência
        zx = int(self.alin_ponto_centro - 24)
        pygame.draw.rect(tela, (25, 75, 55), (zx, ty, 48, th))
        pygame.draw.rect(tela, (50, 220, 120), (zx, ty, 48, th), width=2)
        pygame.draw.rect(tela, (60, 75, 100), (tx, ty, tw, th), width=2, border_radius=6)

        # Linha central de mira
        cx = int(self.alin_ponto_centro)
        pygame.draw.line(tela, (255, 255, 255), (cx, ty - 4), (cx, ty + th + 4), 1)

        # 3. Badges de Etapas (Topo da Trilha)
        fonte_badge = getattr(self, "fonte_badge", None) or getattr(self, "fonte_subtitulo", None) or obter_fonte(10)
        b1_badge_txt = "1. BARRA ESQ: TRAVADA ✓" if self.alin_barra1_travada else "1. BARRA ESQ: ATIVA ▶"
        cor_b1_badge = (60, 220, 140) if self.alin_barra1_travada else (70, 200, 255)
        txt_b1 = fonte_badge.render(b1_badge_txt, True, cor_b1_badge)
        tela.blit(txt_b1, (tx, ty - 22))

        b2_badge_txt = "2. BARRA DIR: TRAVADA ✓" if self.alin_barra2_travada else ("2. BARRA DIR: ATIVA ◀" if self.alin_barra2_ativa else "2. BARRA DIR: AGUARDANDO...")
        cor_b2_badge = (60, 220, 140) if self.alin_barra2_travada else ((255, 140, 70) if self.alin_barra2_ativa else (120, 130, 150))
        txt_b2 = fonte_badge.render(b2_badge_txt, True, cor_b2_badge)
        tela.blit(txt_b2, (tx + tw - txt_b2.get_width(), ty - 22))

        # 4. Barra 1 (Ciano / Azul) - ativa na etapa 1 e fica travada visível na etapa 2
        if self.alin_barra1_ativa:
            b1_x = int(self.alin_barra1_x)
            cor_b1 = (80, 230, 255) if not self.alin_barra1_travada else (50, 180, 220)
            pygame.draw.rect(tela, cor_b1, (b1_x - 6, ty - 6, 12, th + 12), border_radius=3)
            pygame.draw.rect(tela, (255, 255, 255), (b1_x - 6, ty - 6, 12, th + 12), width=1, border_radius=3)
            # Guia vertical se travada
            if self.alin_barra1_travada:
                pygame.draw.line(tela, (100, 220, 255), (b1_x, ty - 12), (b1_x, ty + th + 12), 1)

        # 5. Barra 2 (Laranja / Carmesim) - surge na etapa 2 no lado oposto com a mesma velocidade
        if self.alin_barra2_ativa:
            b2_x = int(self.alin_barra2_x)
            cor_b2 = (255, 120, 70) if not self.alin_barra2_travada else (255, 80, 60)
            pygame.draw.rect(tela, cor_b2, (b2_x - 6, ty - 6, 12, th + 12), border_radius=3)
            pygame.draw.rect(tela, (255, 240, 240), (b2_x - 6, ty - 6, 12, th + 12), width=1, border_radius=3)

        # 6. Texto de Instrução Dinâmico
        if self.alin_etapa == 1:
            msg_instr = "ETAPA 1/2: TRAVE A PRIMEIRA BARRA COM [ESPAÇO] OU CLIQUE!"
        else:
            msg_instr = "ETAPA 2/2: ALINHE A SEGUNDA BARRA NA MESMA POSIÇÃO DA PRIMEIRA!"
        txt_instr = self.fonte_instrucao.render(msg_instr, True, (240, 245, 255))
        tela.blit(txt_instr, (self.x_painel + (self.largura_painel - txt_instr.get_width()) // 2, self.y_painel + 225))

    def _desenhar_feiticeiro_esfera(self, tela: pygame.Surface, cor_tema: Tuple[int, int, int]):
        ex, ey = int(self.esfera_pos[0]), int(self.esfera_pos[1])
        raio = int(self.esfera_raio)

        # Esfera mágica com pulso
        pygame.draw.circle(tela, (55, 20, 85), (ex, ey), raio)
        pygame.draw.circle(tela, (180, 90, 255), (ex, ey), raio, width=3)
        pygame.draw.circle(tela, (230, 180, 255), (ex, ey), max(4, raio - 18), width=2)
        pygame.draw.circle(tela, (255, 255, 255), (ex, ey), 8)

        # Barra de canalização na base
        bx = self.x_painel + 70
        by = self.y_painel + 205
        bw = self.largura_painel - 140
        bh = 16
        pct = self.esfera_tempo_dentro / max(1, self.tempo_total)
        pygame.draw.rect(tela, (25, 30, 42), (bx, by, bw, bh), border_radius=6)
        if pct > 0:
            pygame.draw.rect(tela, (180, 90, 255), (bx, by, int(bw * min(1.0, pct)), bh), border_radius=6)
        pygame.draw.rect(tela, (100, 70, 140), (bx, by, bw, bh), width=2, border_radius=6)

        txt_instr = self.fonte_instrucao.render("MANTENHA O MOUSE DENTRO DA ESFERA MÁGICA!", True, (240, 245, 255))
        tela.blit(txt_instr, (self.x_painel + (self.largura_painel - txt_instr.get_width()) // 2, self.y_painel + 240))

    def _desenhar_feiticeiro_arrastar(self, tela: pygame.Surface, cor_tema: Tuple[int, int, int]):
        origem = getattr(self, "drag_origem", None) or (float(self.x_painel + 90), float(self.y_painel + 185))
        ox, oy = int(origem[0]), int(origem[1])
        destino = getattr(self, "drag_destino", None) or (float(self.x_painel + self.largura_painel - 90), float(self.y_painel + 185))
        dx, dy = int(destino[0]), int(destino[1])
        fonte_badge = getattr(self, "fonte_badge", None) or getattr(self, "fonte_subtitulo", None) or obter_fonte(10)
        tempo_anim = getattr(self, "tempo_animacao", 0.0)

        # 1. Base / Pedestal de Origem
        pygame.draw.circle(tela, (24, 28, 42), (ox, oy), int(self.drag_raio_origem) + 6)
        pygame.draw.circle(tela, (70, 85, 120), (ox, oy), int(self.drag_raio_origem) + 6, width=2)
        txt_origem = fonte_badge.render("ORIGEM", True, (140, 160, 190))
        tela.blit(txt_origem, (ox - txt_origem.get_width() // 2, oy + int(self.drag_raio_origem) + 10))

        # 2. Conduíte Mágico entre Origem e Glifo (pontos de fluxo guiando até o destino)
        pygame.draw.line(tela, (45, 55, 80), (ox, oy), (dx, dy), 2)
        passos = 6
        for p in range(1, passos):
            frac = p / passos
            fx = ox + (dx - ox) * frac
            fy = oy + (dy - oy) * frac
            pulso_seta = int(math.sin(tempo_anim * 5.0 + p) * 3)
            pygame.draw.circle(tela, (140, 115, 210), (int(fx + pulso_seta), int(fy)), 3)

        # 3. Glifo Ritual de Destino (Receptáculo Arcano)
        dist_atual_dest = math.hypot(self.drag_pos_atual[0] - dx, self.drag_pos_atual[1] - dy)
        glifo_destaque = dist_atual_dest <= self.drag_raio_destino + 30

        cor_borda_glifo = (255, 215, 80) if glifo_destaque else (170, 95, 245)
        cor_fundo_glifo = (45, 30, 65) if glifo_destaque else (28, 22, 45)

        pygame.draw.circle(tela, cor_fundo_glifo, (dx, dy), int(self.drag_raio_destino))
        pygame.draw.circle(tela, cor_borda_glifo, (dx, dy), int(self.drag_raio_destino), width=3)
        pulso_r = 14 + int(math.sin(tempo_anim * 4.0) * 3)
        pygame.draw.circle(tela, (255, 230, 120) if glifo_destaque else (190, 140, 255), (dx, dy), pulso_r, width=2)

        txt_dest = self.fonte_subtitulo.render("GLIFO", True, (255, 240, 180) if glifo_destaque else (210, 190, 255))
        tela.blit(txt_dest, (dx - txt_dest.get_width() // 2, dy - 7))

        txt_glifo_sub = fonte_badge.render("DESTINO", True, (180, 160, 220))
        tela.blit(txt_glifo_sub, (dx - txt_glifo_sub.get_width() // 2, dy + int(self.drag_raio_destino) + 10))

        # 4. Runa que é arrastada
        px, py = int(self.drag_pos_atual[0]), int(self.drag_pos_atual[1])

        # Feixe de energia conectando a runa ao seu altar de origem enquanto arrastada
        if self.drag_segurando or math.hypot(px - ox, py - oy) > 10:
            pygame.draw.line(tela, (140, 100, 240), (ox, oy), (px, py), 2)

        cor_runa_borda = (255, 220, 80) if self.drag_segurando else (110, 200, 255)
        cor_runa_corpo = (50, 40, 80) if self.drag_segurando else (30, 45, 75)

        if self.drag_segurando:
            pygame.draw.circle(tela, (180, 130, 255), (px, py), int(self.drag_raio_origem) + 5, width=1)

        pygame.draw.circle(tela, cor_runa_corpo, (px, py), int(self.drag_raio_origem))
        pygame.draw.circle(tela, cor_runa_borda, (px, py), int(self.drag_raio_origem), width=3)
        pygame.draw.circle(tela, (255, 255, 255), (px, py), 7)

        if self.drag_segurando:
            txt_instr = self.fonte_instrucao.render("CONDUZA A RUNA ATÉ O CENTRO DO GLIFO RITUAL!", True, (255, 230, 100))
        else:
            txt_instr = self.fonte_instrucao.render("CLIQUE E ARRASTE A RUNA ATÉ O GLIFO! (OU [D] / [ESPAÇO])", True, (240, 245, 255))
        tela.blit(txt_instr, (self.x_painel + (self.largura_painel - txt_instr.get_width()) // 2, self.y_painel + 242))

    def _desenhar_lutador_combo(self, tela: pygame.Surface, cor_tema: Tuple[int, int, int]):
        tx = int(self.combo_trilha_x)
        ty = self.y_painel + 145
        tw = int(self.combo_trilha_w)
        th = 32

        pygame.draw.rect(tela, (25, 28, 38), (tx, ty, tw, th), border_radius=6)

        # Zona central de impacto
        zx = int(tx + (tw - self.combo_zona_w) // 2)
        pygame.draw.rect(tela, (160, 45, 25), (zx, ty, int(self.combo_zona_w), th))
        pygame.draw.rect(tela, (255, 180, 50), (zx, ty, int(self.combo_zona_w), th), width=2)
        pygame.draw.rect(tela, (70, 80, 100), (tx, ty, tw, th), width=2, border_radius=6)

        # Cursor de impacto
        cx = int(self.combo_cursor_x)
        pygame.draw.rect(tela, (255, 240, 240), (cx - 6, ty - 6, 12, th + 12), border_radius=3)

        # Contador de combo
        txt_combo = self.fonte_titulo.render(f"COMBO: {self.combo_atual} / {self.combo_maximo}", True, (255, 200, 50))
        tela.blit(txt_combo, (self.x_painel + (self.largura_painel - txt_combo.get_width()) // 2, self.y_painel + 195))

        txt_instr = self.fonte_instrucao.render("ACERTE A ZONA CENTRAL VÁRIAS VEZES EM SEGUIDA!", True, (240, 245, 255))
        tela.blit(txt_instr, (self.x_painel + (self.largura_painel - txt_instr.get_width()) // 2, self.y_painel + 240))

    def _desenhar_lutador_forca(self, tela: pygame.Surface, cor_tema: Tuple[int, int, int]):
        bx = self.x_painel + 60
        by = self.y_painel + 145
        bw = self.largura_painel - 120
        bh = 32

        pygame.draw.rect(tela, (25, 28, 38), (bx, by, bw, bh), border_radius=8)

        # Zona doce (80% a 95%)
        z_inicio = bx + int(bw * 0.80)
        z_fim = bx + int(bw * 0.95)
        pygame.draw.rect(tela, (180, 50, 30), (z_inicio, by, z_fim - z_inicio, bh))
        pygame.draw.rect(tela, (255, 215, 60), (z_inicio, by, z_fim - z_inicio, bh), width=2)

        # Barra carregada
        w_ativa = int(bw * min(1.0, self.forca_atual / 100.0))
        if w_ativa > 0:
            cor_forca = (255, 60, 60) if self.forca_overcharge else ((255, 215, 60) if 80.0 <= self.forca_atual <= 95.0 else (255, 140, 40))
            pygame.draw.rect(tela, cor_forca, (bx, by, w_ativa, bh), border_radius=8)

        pygame.draw.rect(tela, cor_tema, (bx, by, bw, bh), width=2, border_radius=8)

        txt_valor = self.fonte_status.render(f"{int(self.forca_atual)}%", True, (255, 255, 255))
        tela.blit(txt_valor, (bx + (bw - txt_valor.get_width()) // 2, by + 6))

        txt_instr = self.fonte_instrucao.render("SEGURE [ESPAÇO] E SOLTE DENTRO DA ZONA DE IMPACTO (80-95%)!", True, (240, 245, 255))
        tela.blit(txt_instr, (self.x_painel + (self.largura_painel - txt_instr.get_width()) // 2, self.y_painel + 235))

    def _desenhar_feedback_final(self, tela: pygame.Surface):
        feedback_texto = self.resultado.get("feedback", "")
        sucesso = self.resultado.get("sucesso", True)
        chance_erro = float(self.resultado.get("chance_erro", 0.0))
        cor_txt = (100, 255, 140) if sucesso and chance_erro <= 0.25 else (255, 90, 90)

        if chance_erro <= 0.0:
            txt_prec = " • ACERTO GARANTIDO!"
        elif chance_erro >= 0.99:
            txt_prec = " • GOLPE ERROU!"
        else:
            prec_pct = int(round((1.0 - chance_erro) * 100))
            txt_prec = f" • CHANCE DE ACERTO: {prec_pct}%"

        texto_exibicao = f"{feedback_texto}{txt_prec}"
        txt_feed = self.fonte_feedback.render(texto_exibicao, True, cor_txt)
        bg_rect = pygame.Rect(
            self.x_painel + (self.largura_painel - txt_feed.get_width() - 24) // 2,
            self.y_painel + self.altura_painel - 48,
            txt_feed.get_width() + 24,
            32
        )
        pygame.draw.rect(tela, (12, 16, 24), bg_rect, border_radius=6)
        pygame.draw.rect(tela, cor_txt, bg_rect, width=2, border_radius=6)
        tela.blit(txt_feed, (bg_rect.x + 12, bg_rect.y + 6))
