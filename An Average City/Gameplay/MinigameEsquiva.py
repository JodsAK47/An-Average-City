import math
import random
import pygame
from typing import Optional, Dict, Any, Tuple, List
from Sistemas.Fontes import obter_fonte
from Sistemas.GerenciadorAudio import tocar_sfx
from Sistemas.SistemaUI import desenhar_painel_container


class MinigameEsquiva:
    """
    Controlador modernizado do Minigame de Esquiva em Tempo Real (QTE).
    Baseado na interface visual dos Minigames de Ataque e com velocidade balanceada.

    Gerencia:
    - O avanço rítmico dos projéteis móveis em direção à zona central (x=200);
    - Detecção imediata por Teclado ([ESPAÇO], [ENTER], [W], [↑]) e Clique de Mouse;
    - Zona Central de Parry (100% de redução no projétil / -33% total);
    - Zona Lateral de Esquiva (50% de redução no projétil / -16% total);
    - Partículas visuais, banner de feedback flutuante e suporte a múltiplos disparos.
    """

    def __init__(self, total_rodadas: int = 3, tela: Optional[pygame.Surface] = None):
        self.tela = tela
        self.largura = tela.get_width() if tela else 1000
        self.altura = tela.get_height() if tela else 800

        self.total_rodadas = total_rodadas
        self.barras: List[Dict[str, Any]] = []
        self.ativo: bool = False

        self.acertos: int = 0
        self.acertos_centro: int = 0
        self.reducao: float = 0.0

        self.dano_pendente: int = 0
        self.alvo: Any = None
        self.atacante_nome: str = ""
        self.efeitos_pendentes: List[str] = []
        self.chance_efeito_pendente: float = 0.0
        self.ultimo_feedback: str = ""

        self.acao_pendente: bool = False
        self.timer_encerramento: int = 0
        self.tempo_animacao: float = 0.0
        self.particulas: List[Dict[str, Any]] = []

        # Fontes do Minigame
        self.fonte_titulo = obter_fonte(17)
        self.fonte_subtitulo = obter_fonte(12)
        self.fonte_instrucao = obter_fonte(12)
        self.fonte_status = obter_fonte(13)
        self.fonte_feedback = obter_fonte(15)
        self.fonte_badge = obter_fonte(11)

        # Dimensões do Painel Central
        self.largura_painel = 520
        self.altura_painel = 290
        self.x_painel = (self.largura - self.largura_painel) // 2
        self.y_painel = (self.altura - self.altura_painel) // 2
        self.rect_painel = pygame.Rect(self.x_painel, self.y_painel, self.largura_painel, self.altura_painel)

        # Superfície de escurecimento de fundo
        self.superficie_overlay = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        self.superficie_overlay.fill((8, 10, 16, 175))

        # Dimensões da Trilha de Esquiva
        self.bar_w = 400
        self.bar_h = 32
        self.bar_x = self.x_painel + (self.largura_painel - self.bar_w) // 2
        self.bar_y = self.y_painel + 140
        self.ponto_centro = 200

    def esta_ativo(self) -> bool:
        return self.ativo

    def redimensionar(self, largura: int, altura: int):
        self.largura = largura
        self.altura = altura
        self.x_painel = (self.largura - self.largura_painel) // 2
        self.y_painel = (self.altura - self.altura_painel) // 2
        self.rect_painel = pygame.Rect(self.x_painel, self.y_painel, self.largura_painel, self.altura_painel)
        self.bar_x = self.x_painel + (self.largura_painel - self.bar_w) // 2
        self.bar_y = self.y_painel + 140
        self.superficie_overlay = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        self.superficie_overlay.fill((8, 10, 16, 175))

    def iniciar(self, velocidade_base: float, dano_pendente: int, alvo=None,
                atacante_nome: str = "", efeitos=None, chance_efeito: float = 0.0,
                tela: Optional[pygame.Surface] = None):
        if tela:
            self.tela = tela
            if tela.get_width() != self.largura or tela.get_height() != self.altura:
                self.redimensionar(tela.get_width(), tela.get_height())

        self.ativo = True
        self.barras = []
        self.acertos = 0
        self.acertos_centro = 0
        self.reducao = 0.0

        self.dano_pendente = dano_pendente
        self.alvo = alvo
        self.atacante_nome = atacante_nome or "Inimigo"
        self.efeitos_pendentes = list(efeitos or [])
        self.chance_efeito_pendente = chance_efeito
        self.ultimo_feedback = "⚡ PREPARE-SE PARA O PARRY!"
        self.acao_pendente = False
        self.timer_encerramento = 0
        self.tempo_animacao = 0.0
        self.particulas = []

        # Velocidade base balanceada para permitir tempo de reação confortável (~0.7s - 0.9s até o centro)
        vel_safe = max(2.5, float(velocidade_base))

        # Cada orbe sai de um lado diferente (alternando entre esquerda e direita)
        primeiro_lado = random.choice(["esquerda", "direita"])
        lados = [
            primeiro_lado if i % 2 == 0 else ("direita" if primeiro_lado == "esquerda" else "esquerda")
            for i in range(self.total_rodadas)
        ]

        # Cada orbe tem uma velocidade diferente
        # Multiplicadores distintos para diferenciar o ritmo de cada golpe
        fatores_vel = [0.88, 1.25, 1.05]
        random.shuffle(fatores_vel)
        vels = []
        for i in range(self.total_rodadas):
            fator = fatores_vel[i % len(fatores_vel)]
            v = max(2.4, round(vel_safe * fator, 2))
            if vels and v == vels[-1]:
                v = round(v + 0.35, 2)
            vels.append(v)

        # Cálculo do espaçamento rítmico: cada orbe chega ao centro em momentos cadenciados
        dist_base = 210.0
        t_chegada = dist_base / vels[0]

        for i in range(self.total_rodadas):
            lado = lados[i]
            vel = vels[i]
            direcao = 1 if lado == "esquerda" else -1

            if i == 0:
                x_pos = -12.0 if lado == "esquerda" else 412.0
            else:
                t_chegada += 48.0
                if lado == "esquerda":
                    x_pos = 200.0 - (vel * t_chegada)
                else:
                    x_pos = 200.0 + (vel * t_chegada)

            self.barras.append({
                "x": float(x_pos),
                "velocidade": vel,
                "lado": lado,
                "direcao": direcao,
                "ativa": True,
                "resultado": "pendente"
            })

    def processar_evento(self, evento: pygame.event.Event, posicao_mouse: Tuple[int, int]):
        """Captura eventos isolados de teclado e cliques de mouse."""
        if not self.ativo or self.timer_encerramento > 0:
            return

        if evento.type == pygame.KEYDOWN and evento.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_w, pygame.K_UP):
            self.acao_pendente = True
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self.acao_pendente = True

    def _gerar_particulas(self, x: float, y: float, cor: Tuple[int, int, int], qtd: int = 5):
        for _ in range(qtd):
            self.particulas.append({
                "x": x + random.uniform(-4, 4),
                "y": y + random.uniform(-4, 4),
                "vx": random.uniform(-2.8, 2.8),
                "vy": random.uniform(-2.8, 2.8),
                "cor": cor,
                "raio": random.randint(2, 4),
                "vida": random.randint(12, 22)
            })

    def atualizar(self, clicou: bool = False) -> Optional[Dict[str, Any]]:
        """
        Atualiza o movimento das barras e processa cliques de esquiva/parry.
        Retorna None enquanto ativo, ou um dicionário de resultado ao concluir.
        """
        if not self.ativo:
            return None

        self.tempo_animacao += 0.05

        # Atualiza partículas visuais
        for p in self.particulas[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vida"] -= 1
            if p["vida"] <= 0:
                self.particulas.remove(p)

        # Se já concluído, segura o feedback final por alguns frames antes de retornar
        if all(not b["ativa"] for b in self.barras):
            self.timer_encerramento += 1
            if self.timer_encerramento >= 24:
                self.ativo = False
                total_acertos = self.acertos + self.acertos_centro
                evitou_tudo = (total_acertos == self.total_rodadas or
                               self.acertos_centro >= (self.total_rodadas - 1))

                reducao_total = min(0.99, self.reducao)
                dano_calculado = max(1, int(self.dano_pendente * (1 - reducao_total)))

                if getattr(self.alvo, "god_mode", False):
                    dano_calculado = 0

                return {
                    "concluido": True,
                    "dano_tomado": dano_calculado,
                    "reducao_total": reducao_total,
                    "evitou_tudo": evitou_tudo,
                    "acertos": self.acertos,
                    "acertos_centro": self.acertos_centro,
                    "alvo": self.alvo,
                    "efeitos_pendentes": self.efeitos_pendentes,
                    "chance_efeito": self.chance_efeito_pendente,
                    "feedback": self.ultimo_feedback,
                }
            return None

        # Processamento de clique / comando de esquiva
        tentou_esquivar = self.acao_pendente or clicou
        self.acao_pendente = False

        if tentou_esquivar:
            barras_ativas = [b for b in self.barras if b["ativa"]]
            if barras_ativas:
                # Seleciona a orbe ativa mais próxima do centro
                barra_alvo = min(barras_ativas, key=lambda b: abs(b["x"] - self.ponto_centro))
                distancia = abs(barra_alvo["x"] - self.ponto_centro)
                barra_alvo["ativa"] = False

                bx_tela = self.bar_x + max(0, min(self.bar_w, barra_alvo["x"]))
                by_tela = self.bar_y + self.bar_h // 2

                if distancia <= 22:
                    self.acertos_centro += 1
                    self.reducao += 0.33
                    self.ultimo_feedback = "⚡ PARRY PERFEITO! (-33% DANO)"
                    barra_alvo["resultado"] = "parry"
                    self._gerar_particulas(bx_tela, by_tela, (50, 240, 140), qtd=10)
                    self._gerar_particulas(bx_tela, by_tela, (255, 230, 90), qtd=6)
                    try:
                        tocar_sfx("Acerto.wav", volume_relativo=1.0)
                    except Exception:
                        pass
                elif distancia <= 80:
                    self.acertos += 1
                    self.reducao += 0.16
                    self.ultimo_feedback = "💨 ESQUIVA SINCRONIZADA! (-16% DANO)"
                    barra_alvo["resultado"] = "esquiva"
                    self._gerar_particulas(bx_tela, by_tela, (70, 210, 255), qtd=8)
                    try:
                        tocar_sfx("Acerto.wav", volume_relativo=0.7)
                    except Exception:
                        pass
                else:
                    self.ultimo_feedback = "❌ ERROU O TEMPO!"
                    barra_alvo["resultado"] = "erro"
                    self._gerar_particulas(bx_tela, by_tela, (255, 70, 70), qtd=6)
                    try:
                        tocar_sfx("Dano.wav", volume_relativo=0.5)
                    except Exception:
                        pass

        # Atualiza a posição de cada orbe móvel respeitando sua direção
        for barra in self.barras:
            if barra["ativa"]:
                dir_mov = barra.get("direcao", 1)
                barra["x"] += barra["velocidade"] * dir_mov

                passou = False
                if dir_mov == 1 and barra["x"] >= 400:
                    passou = True
                elif dir_mov == -1 and barra["x"] <= 0:
                    passou = True

                if passou:
                    barra["ativa"] = False
                    barra["resultado"] = "perdida"
                    self.ultimo_feedback = "❌ PROJÉTIL PERDIDO!"
                    x_part = self.bar_x + (400 if dir_mov == 1 else 0)
                    self._gerar_particulas(x_part, self.bar_y + self.bar_h // 2, (255, 60, 60), qtd=5)
                    try:
                        tocar_sfx("Dano.wav", volume_relativo=0.5)
                    except Exception:
                        pass

        return None

    def desenhar(self, superficie: pygame.Surface, bar_x: Optional[int] = None, bar_y: Optional[int] = None,
                 bar_w: int = 400, bar_h: int = 30):
        """
        Renderiza o minigame de esquiva moderno estilizado.
        Compatível com chamadas legadas que passam bar_x e bar_y diretamente.
        """
        if not self.ativo:
            return

        # Modo legado simples se coordenadas forem especificadas explicitamente
        if bar_x is not None and bar_y is not None:
            self._desenhar_trilho_legado(superficie, bar_x, bar_y, bar_w, bar_h)
            return

        # 1. Overlay escurecido do combate
        superficie.blit(self.superficie_overlay, (0, 0))

        # 2. Painel central estilizado com borda de perigo carmesim
        cor_borda = (235, 75, 75)
        desenhar_painel_container(
            superficie,
            self.rect_painel,
            nome_sprite="painel_base.png",
            fallback_cor=(20, 24, 34),
            borda_cor=cor_borda
        )

        # 3. Cabeçalho do Painel
        badge_esq = self.fonte_subtitulo.render("🛡️ DEFESA EM TEMPO REAL", True, (255, 205, 65))
        superficie.blit(badge_esq, (self.x_painel + 22, self.y_painel + 16))

        txt_dano = self.fonte_subtitulo.render(f"DANO IMINENTE: {self.dano_pendente} HP", True, (255, 100, 100))
        superficie.blit(txt_dano, (self.x_painel + self.largura_painel - txt_dano.get_width() - 22, self.y_painel + 16))

        titulo_atacante = f"GOLPE DE {str(self.atacante_nome).upper()}!"
        txt_titulo = self.fonte_titulo.render(titulo_atacante, True, (255, 255, 255))
        superficie.blit(txt_titulo, (self.x_painel + (self.largura_painel - txt_titulo.get_width()) // 2, self.y_painel + 42))

        txt_instr = self.fonte_instrucao.render("PRESSIONE [ESPAÇO] OU CLIQUE NO CENTRO PARA PARRY!", True, (230, 235, 245))
        superficie.blit(txt_instr, (self.x_painel + (self.largura_painel - txt_instr.get_width()) // 2, self.y_painel + 68))

        # 4. Indicador de Rodadas (Badges circulares dos 3 projéteis)
        self._desenhar_indicadores_rodadas(superficie)

        # 5. Trilho Principal de Esquiva e Parry
        self._desenhar_trilho_moderno(superficie)

        # 6. Partículas
        for p in self.particulas:
            pygame.draw.circle(superficie, p["cor"], (int(p["x"]), int(p["y"])), p["raio"])

        # 7. Banner de Feedback Dinâmico Flutuante
        self._desenhar_feedback_flutuante(superficie)

    def _desenhar_indicadores_rodadas(self, superficie: pygame.Surface):
        y_indicadores = self.y_painel + 98
        largura_total = self.total_rodadas * 38
        x_inicio = self.x_painel + (self.largura_painel - largura_total) // 2

        for i, barra in enumerate(self.barras):
            bx = x_inicio + (i * 38)
            rect_ind = pygame.Rect(bx, y_indicadores, 26, 26)

            res = barra.get("resultado", "pendente")
            lado = barra.get("lado", "esquerda")
            if res == "parry":
                cor_fundo = (35, 160, 85)
                cor_borda = (60, 255, 140)
                simbolo = "✓"
            elif res == "esquiva":
                cor_fundo = (35, 130, 180)
                cor_borda = (80, 210, 255)
                simbolo = "•"
            elif res in ("erro", "perdida"):
                cor_fundo = (160, 40, 40)
                cor_borda = (255, 70, 70)
                simbolo = "✕"
            else:
                cor_fundo = (30, 34, 46)
                cor_borda = (90, 100, 120)
                simbolo = "▶" if lado == "esquerda" else "◀"

            pygame.draw.rect(superficie, cor_fundo, rect_ind, border_radius=6)
            pygame.draw.rect(superficie, cor_borda, rect_ind, width=2, border_radius=6)

            txt_s = self.fonte_badge.render(simbolo, True, (255, 255, 255))
            superficie.blit(txt_s, (rect_ind.x + (rect_ind.width - txt_s.get_width()) // 2,
                                    rect_ind.y + (rect_ind.height - txt_s.get_height()) // 2))

    def _desenhar_trilho_moderno(self, superficie: pygame.Surface):
        bx = self.bar_x
        by = self.bar_y
        bw = self.bar_w
        bh = self.bar_h

        # Fundo do trilho texturizado
        pygame.draw.rect(superficie, (14, 18, 28), (bx, by, bw, bh), border_radius=8)

        # Zona lateral de Esquiva (Âmbar/Dourado) de x=120 a x=280
        zona_esq_rect = pygame.Rect(bx + 120, by + 2, 160, bh - 4)
        pygame.draw.rect(superficie, (215, 160, 40), zona_esq_rect, border_radius=4)
        pygame.draw.rect(superficie, (255, 215, 80), zona_esq_rect, width=1, border_radius=4)

        # Zona central de Parry (Verde Esmeralda Pulsante) de x=178 a x=222
        pulso = int(math.sin(self.tempo_animacao * 4.0) * 15)
        cor_parry = (35, min(255, 220 + pulso), 110)
        zona_parry_rect = pygame.Rect(bx + 178, by + 1, 44, bh - 2)
        pygame.draw.rect(superficie, cor_parry, zona_parry_rect, border_radius=4)
        pygame.draw.rect(superficie, (255, 255, 255), zona_parry_rect, width=2, border_radius=4)

        # Retículo central de parry (indicador de alvo no centro)
        cx = bx + self.ponto_centro
        pygame.draw.line(superficie, (255, 255, 255), (cx, by - 6), (cx, by + bh + 6), 2)
        pygame.draw.polygon(superficie, (255, 240, 100), [(cx - 5, by - 8), (cx + 5, by - 8), (cx, by - 2)])
        pygame.draw.polygon(superficie, (255, 240, 100), [(cx - 5, by + bh + 8), (cx + 5, by + bh + 8), (cx, by + bh + 2)])

        # Borda externa do trilho
        pygame.draw.rect(superficie, (180, 190, 215), (bx, by, bw, bh), width=2, border_radius=8)

        # Texto PARRY no topo da zona central
        txt_parry = self.fonte_badge.render("PARRY", True, (255, 255, 255))
        superficie.blit(txt_parry, (cx - txt_parry.get_width() // 2, by - 19))

        # Orbes móveis de energia em direção ao centro
        for barra in self.barras:
            if not barra["ativa"]:
                continue
            if barra["x"] < 0 or barra["x"] > bw:
                continue

            px = bx + barra["x"]
            py = by + bh // 2
            dir_mov = barra.get("direcao", 1)
            vel = barra.get("velocidade", 4.0)

            # Rastro luminoso projetado atrás da orbe
            rastro_w = min(26, int(vel * 4.6))
            cor_rastro = (255, 95, 115) if dir_mov == 1 else (255, 145, 55)
            if dir_mov == 1:
                pygame.draw.line(superficie, cor_rastro, (px - rastro_w, py), (px, py), 4)
            else:
                pygame.draw.line(superficie, cor_rastro, (px + rastro_w, py), (px, py), 4)

            # Núcleo da Orbe estilizada
            raio_orbe = 10
            cor_coroa = (255, 215, 225) if dir_mov == 1 else (255, 230, 190)
            cor_nucleo = (255, 45, 65) if dir_mov == 1 else (255, 95, 30)

            pygame.draw.circle(superficie, cor_coroa, (int(px), int(py)), raio_orbe + 2, width=2)
            pygame.draw.circle(superficie, cor_nucleo, (int(px), int(py)), raio_orbe)
            pygame.draw.circle(superficie, (255, 255, 255), (int(px), int(py)), 4)

    def _desenhar_feedback_flutuante(self, superficie: pygame.Surface):
        feedback = self.ultimo_feedback or "PREPARE-SE PARA ESQUIVAR!"
        if "PARRY" in feedback:
            cor_txt = (80, 255, 150)
        elif "ESQUIVA" in feedback:
            cor_txt = (80, 220, 255)
        elif "ERROU" in feedback or "PERDIDO" in feedback:
            cor_txt = (255, 90, 90)
        else:
            cor_txt = (230, 240, 255)

        txt_feed = self.fonte_feedback.render(feedback, True, cor_txt)
        bg_rect = pygame.Rect(
            self.x_painel + (self.largura_painel - txt_feed.get_width() - 24) // 2,
            self.y_painel + self.altura_painel - 48,
            txt_feed.get_width() + 24,
            32
        )
        pygame.draw.rect(superficie, (12, 16, 24), bg_rect, border_radius=6)
        pygame.draw.rect(superficie, cor_txt, bg_rect, width=2, border_radius=6)
        superficie.blit(txt_feed, (bg_rect.x + 12, bg_rect.y + 6))

    def _desenhar_trilho_legado(self, superficie: pygame.Surface, bar_x: int, bar_y: int,
                                bar_w: int, bar_h: int):
        """Renderizador legado simplificado caso coordenadas externas sejam passadas."""
        pygame.draw.rect(superficie, (18, 22, 32), (bar_x, bar_y, bar_w, bar_h), border_radius=5)
        pygame.draw.rect(superficie, (230, 190, 50), (bar_x + 120, bar_y, 160, bar_h))
        pygame.draw.rect(superficie, (30, 220, 90), (bar_x + 180, bar_y, 40, bar_h))
        pygame.draw.rect(superficie, (240, 240, 240), (bar_x, bar_y, bar_w, bar_h), width=2, border_radius=5)

        for barra in self.barras:
            if not barra["ativa"] or barra["x"] < 0:
                continue
            bx = bar_x + barra["x"] - 4
            if bar_x <= bx <= bar_x + bar_w:
                pygame.draw.rect(superficie, (255, 60, 60), (bx, bar_y - 6, 8, bar_h + 12), border_radius=2)
