import pygame
import time
import math
from Sistemas.Recursos import caminho_imagem
from Sistemas.Fontes import obter_fonte
from Entidades.EntidadeCombate import EntidadeCombate, aplicar_mascara_transparencia


class Spike(EntidadeCombate):
    """
    Spike plantada pela Ultimate da Estraga Prazeres (Killjoy).
    - Detona de acordo com a duração do som (aproximadamente 50 segundos).
    - Se detonar, expande uma colossal esfera negra com auras e efeitos brancos,
      eliminando todos os jogadores (Game Over instantâneo).
    - Pode ser desarmada através do minigame com a esfera centralizada e bullet hell.
    - Ao ser desarmada, exibe o novo frame (Spike Desarmada.png) no chão antes de ser deletada da tela.
    """
    def __init__(self, x=500, y=460, dono=None, tempo_total=50.0):
        super().__init__(nome="Spike", max_hp=100, max_mp=0, is_player=False)
        self.dono = dono
        self.lado = "inimigo"
        self.is_spike = True
        self.is_minion = False
        self.tipo = "dispositivo"
        self.classe = "Distância"
        self.verso = "Agente"

        self.ativa = True
        self.desarmada = False
        self.detonando = False
        self.detonada = False
        self.deletar = False

        self.tempo_plantio = time.time()
        self.tempo_total = float(tempo_total)
        self.progresso_desarme = 0.0
        self.checkpoint_50 = False

        self.timer_desarmada = 110  # Tempo em frames exibindo o frame desarmado antes de deletar
        self.particulas_fumaca = []

        self.x = x
        self.y = y
        self.imagem_plantada = None
        self.imagem_desarmada = None
        self.imagem = None

        self._carregar_sprites()
        self.imagem = self.imagem_plantada
        self.rect = self.imagem.get_rect(center=(x, y))
        self.fonte_timer = obter_fonte(12)

    def _carregar_sprites(self):
        # 1. Carrega sprite da Spike armada/plantada (Spike.png)
        altura_plantada = 85
        try:
            caminho_plantada = caminho_imagem("Spike.png")
            img_original = pygame.image.load(caminho_plantada)
            w_orig, h_orig = img_original.get_size()

            if w_orig >= 2100 and h_orig >= 1346:
                crop = img_original.subsurface((1462, 408, 2100 - 1462, 1346 - 408))
            else:
                crop = img_original

            largura_plantada = max(40, int(crop.get_width() * (altura_plantada / max(1, crop.get_height()))))
            img_escala = pygame.transform.smoothscale(crop, (largura_plantada, altura_plantada)).convert_alpha()

            aplicar_mascara_transparencia(img_escala, corte_zero=18, fade_max=50)
            self.imagem_plantada = img_escala
        except Exception as e:
            print(f"[Aviso] Falha ao carregar sprite Spike.png: {e}")
            self.imagem_plantada = pygame.Surface((57, altura_plantada), pygame.SRCALPHA)
            pygame.draw.polygon(self.imagem_plantada, (50, 50, 60), [(28, 5), (52, 75), (5, 75)])
            pygame.draw.circle(self.imagem_plantada, (255, 60, 60), (28, 45), 10)

        # 2. Carrega o novo frame da Spike desarmada (Spike Desarmada.png)
        altura_desarmada = 55
        try:
            caminho_desarmada = caminho_imagem("Spike Desarmada.png")
            img_des_orig = pygame.image.load(caminho_desarmada)
            w_des, h_des = img_des_orig.get_size()

            if w_des >= 335 + 354 and h_des >= 302 + 209:
                crop_des = img_des_orig.subsurface((335, 302, 354, 209))
            else:
                crop_des = img_des_orig

            largura_desarmada = max(50, int(crop_des.get_width() * (altura_desarmada / max(1, crop_des.get_height()))))
            img_des_escala = pygame.transform.smoothscale(crop_des, (largura_desarmada, altura_desarmada)).convert_alpha()

            aplicar_mascara_transparencia(img_des_escala, corte_zero=16, fade_max=45)
            self.imagem_desarmada = img_des_escala
        except Exception as e:
            print(f"[Aviso] Falha ao carregar sprite Spike Desarmada.png: {e}")
            self.imagem_desarmada = pygame.Surface((90, altura_desarmada), pygame.SRCALPHA)
            pygame.draw.rect(self.imagem_desarmada, (40, 45, 50), (5, 10, 80, 35), border_radius=6)
            pygame.draw.circle(self.imagem_desarmada, (60, 235, 160), (45, 27), 8)

    def tempo_restante(self):
        if not self.ativa or self.desarmada:
            return 0.0
        decorrido = time.time() - self.tempo_plantio
        return max(0.0, self.tempo_total - decorrido)

    def desarmar(self):
        self.desarmada = True
        self.ativa = False
        self.progresso_desarme = 1.0

        # Troca a sprite para o novo frame da Spike desarmada
        if self.imagem_desarmada:
            y_chao = self.rect.bottom
            self.imagem = self.imagem_desarmada
            self.rect = self.imagem.get_rect(midbottom=(self.x, y_chao))
        self.timer_desarmada = 110

    def atualizar(self):
        if self.desarmada:
            if self.timer_desarmada > 0:
                self.timer_desarmada -= 1
                # Emite leves faíscas verdes/fumaça de desarme
                if self.timer_desarmada > 20 and self.timer_desarmada % 6 == 0:
                    import random
                    self.particulas_fumaca.append({
                        "x": self.rect.centerx + random.uniform(-20, 20),
                        "y": self.rect.centery + random.uniform(-10, 10),
                        "vx": random.uniform(-0.5, 0.5),
                        "vy": random.uniform(-1.2, -0.4),
                        "vida": 25,
                        "vida_max": 25
                    })
            else:
                self.deletar = True

        # Atualiza partículas de fumaça do desarme
        part_vivas = []
        for p in self.particulas_fumaca:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vida"] -= 1
            if p["vida"] > 0:
                part_vivas.append(p)
        self.particulas_fumaca = part_vivas

    def desenhar(self, tela, tempo_animacao=0.0):
        if not self.imagem or self.deletar:
            return

        # Sombra de contato no chão
        w_sombra = int(self.imagem.get_width() * 0.95)
        h_sombra = 14
        sombra_surf = pygame.Surface((w_sombra, h_sombra), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra_surf, (0, 0, 0, 140), (0, 0, w_sombra, h_sombra))
        tela.blit(sombra_surf, (self.rect.centerx - w_sombra // 2, self.rect.bottom - 7))

        # Desenha a sprite com fade-out nos últimos 30 frames se desarmada
        if self.desarmada and self.timer_desarmada < 30:
            alfa = int(255 * (max(0, self.timer_desarmada) / 30.0))
            surf_fade = self.imagem.copy()
            surf_fade.set_alpha(alfa)
            tela.blit(surf_fade, self.rect)
        else:
            tela.blit(self.imagem, self.rect)

        # Fumaça / faíscas de desarme
        for p in self.particulas_fumaca:
            alfa_p = int(180 * (p["vida"] / float(p["vida_max"])))
            surf_p = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(surf_p, (80, 240, 170, alfa_p), (3, 3), 3)
            tela.blit(surf_p, (int(p["x"]) - 3, int(p["y"]) - 3), special_flags=pygame.BLEND_ADD)

        # Efeito de luz LED pulsante da Spike enquanto ativa
        t_restante = self.tempo_restante()
        if self.ativa and not self.desarmada:
            if t_restante > 30:
                freq = 2.0
            elif t_restante > 15:
                freq = 4.0
            elif t_restante > 5:
                freq = 7.0
            else:
                freq = 12.0

            pulso = (math.sin(time.time() * freq * math.pi) + 1.0) / 2.0
            raio_luz = int(6 + pulso * 6)
            alfa_luz = int(120 + pulso * 135)

            cor_luz = (255, 40, 40) if t_restante <= 15 else (255, 140, 30)
            luz_surf = pygame.Surface((raio_luz * 2, raio_luz * 2), pygame.SRCALPHA)
            pygame.draw.circle(luz_surf, (*cor_luz, alfa_luz), (raio_luz, raio_luz), raio_luz)
            pygame.draw.circle(luz_surf, (255, 255, 255, min(255, alfa_luz + 50)), (raio_luz, raio_luz), max(2, raio_luz // 2))
            tela.blit(luz_surf, (self.rect.centerx - raio_luz, self.rect.centery - 10 - raio_luz), special_flags=pygame.BLEND_ADD)

            txt_timer = f"SPIKE {t_restante:.1f}s"
            surf_timer = self.fonte_timer.render(txt_timer, True, cor_luz)
            bg_rect = pygame.Rect(self.rect.centerx - surf_timer.get_width() // 2 - 6, self.rect.top - 24, surf_timer.get_width() + 12, 18)
            pygame.draw.rect(tela, (15, 15, 22, 210), bg_rect, border_radius=5)
            pygame.draw.rect(tela, cor_luz, bg_rect, width=1, border_radius=5)
            tela.blit(surf_timer, (bg_rect.x + 6, bg_rect.y + 2))

            if self.progresso_desarme > 0:
                bar_w = 60
                bar_h = 5
                bx = self.rect.centerx - bar_w // 2
                by = self.rect.top - 5
                pygame.draw.rect(tela, (25, 28, 35), (bx, by, bar_w, bar_h), border_radius=2)
                cor_p = (50, 240, 160) if self.checkpoint_50 else (60, 190, 255)
                pw = int(bar_w * min(1.0, self.progresso_desarme))
                pygame.draw.rect(tela, cor_p, (bx, by, pw, bar_h), border_radius=2)
                pygame.draw.rect(tela, (180, 210, 230), (bx, by, bar_w, bar_h), width=1, border_radius=2)
        elif self.desarmada and not self.deletar:
            alfa_txt = min(255, int(255 * (self.timer_desarmada / 40.0)))
            txt_desarmada = self.fonte_timer.render("DESARMADA", True, (60, 235, 160))
            surf_bg = pygame.Surface((txt_desarmada.get_width() + 12, 18), pygame.SRCALPHA)
            pygame.draw.rect(surf_bg, (10, 30, 20, min(210, alfa_txt)), (0, 0, surf_bg.get_width(), 18), border_radius=5)
            pygame.draw.rect(surf_bg, (60, 235, 160, alfa_txt), (0, 0, surf_bg.get_width(), 18), width=1, border_radius=5)
            surf_bg.blit(txt_desarmada, (6, 2))
            surf_bg.set_alpha(alfa_txt)
            tela.blit(surf_bg, (self.rect.centerx - surf_bg.get_width() // 2, self.rect.top - 22))
