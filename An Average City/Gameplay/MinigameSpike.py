import math
import random
import time
import pygame
from Entidades.Spike import Spike
from Sistemas.SistemaUI import Botao
from Sistemas.Configuracoes import sistema_config


class MinigameSpike:
    """
    Controlador encapsulado do Minigame da Spike (Killjoy).
    Gerencia:
    - O dispositivo Spike em campo e contagem regressiva de 50s;
    - Som contínuo de bip e parada;
    - Minigame de desarme estacionário centralizado com barragem Bullet Hell;
    - Partículas de desarme e expansão da esfera negra de detonação.
    """

    def __init__(self, tela, fonte_status, fonte_inimigo, snd_spike_beep=None,
                 callback_tocar_corte=None, callback_shake=None):
        self.tela = tela
        self.fonte_status = fonte_status
        self.fonte_inimigo = fonte_inimigo
        self.snd_spike_beep = snd_spike_beep
        self.callback_tocar_corte = callback_tocar_corte
        self.callback_shake = callback_shake

        self.spike = None
        self.canal_spike = None

        self.desarmando = False
        self.spike_detonando = False
        self.spike_raio_detonacao = 0.0
        self.spike_tempo_detonacao = 0.0

        w_tela = self.tela.get_width()
        h_tela = self.tela.get_height()
        self.esfera_desarme_pos = [w_tela / 2.0, h_tela / 2.0]
        self.esfera_desarme_raio = 50
        self.esfera_desarme_tempo = 0.0
        self.bloqueio_desarme_timer = 0
        self.progresso_desarme = 0.0
        self.checkpoint_50 = False

        self.projeteis_bullet_hell = []
        self.particulas_desarme = []
        self.particulas_detonacao = []
        self.timer_spawn_projeteis = 0
        self.invulnerabilidade_mouse = 0

        w_btn = 200
        h_btn = 36
        x_btn = (w_tela - w_btn) // 2
        y_btn = h_tela - 70
        self.btn_cancelar = Botao(
            x_btn, y_btn, w_btn, h_btn, "CANCELAR DESARME (ESC)",
            (50, 60, 80), (80, 100, 130), w_btn, h_btn,
            cor_texto=(255, 255, 255), fonte_tamanho=12
        )

    def esta_ativa(self):
        return bool(self.spike and self.spike.ativa and not self.spike.desarmada)

    def esta_desarmando(self):
        return self.desarmando

    def plantar(self, dono=None):
        self.parar_som()
        cx = self.tela.get_width() // 2
        cy = self.tela.get_height() // 2 + 10
        self.spike = Spike(x=cx, y=cy, dono=dono, tempo_total=50.0)
        self.desarmando = False
        self.spike_detonando = False
        self.spike_raio_detonacao = 0.0
        self.spike_tempo_detonacao = 0.0
        self.particulas_detonacao.clear()
        self.projeteis_bullet_hell.clear()
        self.particulas_desarme.clear()
        self.progresso_desarme = 0.0
        self.checkpoint_50 = False

        if self.snd_spike_beep is not None:
            try:
                vol = sistema_config.obter_volume_sfx_efetivo() * 0.90
                self.canal_spike = pygame.mixer.find_channel(True)
                if self.canal_spike:
                    self.canal_spike.set_volume(max(0.0, min(1.0, vol)))
                    self.canal_spike.play(self.snd_spike_beep)
            except Exception as e:
                print(f"[Aviso] Erro ao reproduzir som da Spike: {e}")

    def parar_som(self):
        try:
            if getattr(self, "canal_spike", None) is not None:
                self.canal_spike.stop()
        except Exception:
            pass

    def iniciar_desarme(self):
        self.desarmando = True
        self.esfera_desarme_pos = [self.tela.get_width() / 2.0, self.tela.get_height() / 2.0]
        self.esfera_desarme_raio = 50
        self.esfera_desarme_tempo = 0.0
        self.bloqueio_desarme_timer = 0
        self.projeteis_bullet_hell.clear()
        self.particulas_desarme.clear()
        self.timer_spawn_projeteis = 0
        self.invulnerabilidade_mouse = 0
        self.progresso_desarme = self.spike.progresso_desarme if self.spike else 0.0
        self.checkpoint_50 = self.spike.checkpoint_50 if self.spike else False

    def cancelar_desarme(self):
        if self.spike:
            self.spike.progresso_desarme = self.progresso_desarme
            self.spike.checkpoint_50 = self.checkpoint_50
        self.desarmando = False

    def atualizar_timer(self, jogadores):
        """
        Atualiza o tempo da Spike em campo (detonação e esfera negra).
        Retorna 'detonou' se o tempo acabou.
        """
        if not self.spike:
            return None

        if self.spike.desarmada:
            self.spike.atualizar()
            if getattr(self.spike, "deletar", False):
                self.spike = None
            return None

        if not self.spike.ativa:
            return None

        t_rest = self.spike.tempo_restante()

        # Tremor quando o tempo está esgotando
        if t_rest <= 10.0 and not self.spike_detonando:
            if random.random() < 0.25 and self.callback_shake:
                self.callback_shake(duracao=3, intensidade=2 if t_rest > 4.0 else 4)

        # Inicia expansão da esfera negra
        if t_rest <= 5.0 and not self.spike_detonando:
            self.spike_detonando = True
            self.spike_tempo_detonacao = time.time()
            self.spike.detonando = True

        if self.spike_detonando:
            tempo_det = time.time() - self.spike_tempo_detonacao
            progresso = min(1.0, max(0.0, tempo_det / 4.5))
            self.spike_raio_detonacao = int(1500 * (progresso ** 2.3))

            intensidade_shake = min(22, int(4 + progresso * 18))
            if self.callback_shake:
                self.callback_shake(duracao=5, intensidade=intensidade_shake)

            if len(self.particulas_detonacao) < 40:
                cx = self.spike.rect.centerx if self.spike else self.tela.get_width() // 2
                cy = self.spike.rect.centery if self.spike else (self.tela.get_height() // 2 + 10)
                r = max(10, self.spike_raio_detonacao)
                ang = random.uniform(0, 2 * math.pi)
                vel = random.uniform(4.0, 10.0)
                self.particulas_detonacao.append({
                    "x": cx + math.cos(ang) * (r * 0.95),
                    "y": cy + math.sin(ang) * (r * 0.95),
                    "vx": math.cos(ang) * vel,
                    "vy": math.sin(ang) * vel,
                    "raio": random.randint(2, 5),
                    "vida": random.randint(12, 24)
                })

            vivas_det = []
            for p in self.particulas_detonacao:
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                p["vida"] -= 1
                if p["vida"] > 0:
                    vivas_det.append(p)
            self.particulas_detonacao = vivas_det

            if t_rest <= 0.0 or progresso >= 1.0:
                self.spike.detonada = True
                self.spike.ativa = False
                for j in jogadores:
                    j.hp = 0
                return "detonou"

        return None

    def processar_minigame(self, posicao_mouse, estado_clique_mouse, clicou, jogadores):
        """
        Processa interação de desarme da Spike e colisão com balas bullet hell.
        Retorna 'sucesso', 'cancelado' ou None.
        """
        if not self.spike or not self.spike.ativa or self.spike.desarmada:
            self.desarmando = False
            return "cancelado"

        self.btn_cancelar.atualizar(posicao_mouse, estado_clique_mouse)
        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_ESCAPE] or (clicou and self.btn_cancelar.clicado(posicao_mouse)):
            self.cancelar_desarme()
            return "cancelado"

        w_tela = float(self.tela.get_width())
        h_tela = float(self.tela.get_height())
        cx, cy = w_tela / 2.0, h_tela / 2.0
        self.esfera_desarme_pos = [cx, cy]

        if self.bloqueio_desarme_timer > 0:
            self.bloqueio_desarme_timer -= 1

        dist_mouse = math.hypot(posicao_mouse[0] - cx, posicao_mouse[1] - cy)
        dentro = dist_mouse <= self.esfera_desarme_raio

        if dentro:
            if self.bloqueio_desarme_timer <= 0:
                incremento = 1.0 / (7.5 * 60.0)
                self.progresso_desarme = min(1.0, self.progresso_desarme + incremento)
                if self.progresso_desarme >= 0.5:
                    self.checkpoint_50 = True
                self.spike.progresso_desarme = self.progresso_desarme
                self.spike.checkpoint_50 = self.checkpoint_50

                if random.random() < 0.45:
                    self.particulas_desarme.append({
                        "x": posicao_mouse[0] + random.uniform(-4, 4),
                        "y": posicao_mouse[1] + random.uniform(-4, 4),
                        "vx": (cx - posicao_mouse[0]) * 0.12 + random.uniform(-1, 1),
                        "vy": (cy - posicao_mouse[1]) * 0.12 + random.uniform(-1, 1),
                        "vida": 12,
                        "cor": random.choice([(50, 255, 180), (100, 230, 255), (255, 255, 255)])
                    })
        else:
            p_min = 0.50 if self.checkpoint_50 else 0.0
            self.progresso_desarme = max(p_min, self.progresso_desarme - 0.0016)
            self.spike.progresso_desarme = self.progresso_desarme

        if self.progresso_desarme >= 1.0:
            self.spike.desarmar()
            self.parar_som()
            if self.callback_tocar_corte:
                self.callback_tocar_corte(volume_relativo=0.7)
            if self.callback_shake:
                self.callback_shake(duracao=16, intensidade=6)
            for b in self.projeteis_bullet_hell:
                for _ in range(4):
                    self.particulas_desarme.append({
                        "x": b["x"], "y": b["y"],
                        "vx": random.uniform(-4, 4), "vy": random.uniform(-4, 4),
                        "vida": 20, "cor": (80, 255, 180)
                    })
            self.projeteis_bullet_hell.clear()
            self.desarmando = False
            return "sucesso"

        # Spawn de projéteis convergentes
        self.timer_spawn_projeteis += 1
        if self.timer_spawn_projeteis >= 28 and len(self.projeteis_bullet_hell) < 20:
            self.timer_spawn_projeteis = 0
            padrao = random.choice(["convergencia_radial", "barragem_bordas", "fogo_cruzado", "vortice_espiral"])

            if padrao == "convergencia_radial":
                num_balas = random.randint(7, 8)
                ang_base = random.uniform(0, 2 * math.pi)
                brecha = random.randint(0, num_balas - 1)
                for bi in range(num_balas):
                    if bi == brecha or bi == (brecha + 1) % num_balas:
                        continue
                    ang = ang_base + (bi / num_balas) * 2 * math.pi
                    px = cx + math.cos(ang) * 750.0
                    py = cy + math.sin(ang) * 750.0
                    ang_mov = ang + math.pi
                    vel = random.uniform(2.0, 2.7)
                    self.projeteis_bullet_hell.append({
                        "x": px, "y": py,
                        "vx": math.cos(ang_mov) * vel,
                        "vy": math.sin(ang_mov) * vel,
                        "raio": 6, "cor": (255, 60, 90), "tipo": "radial"
                    })

            elif padrao == "barragem_bordas":
                borda = random.choice(["esquerda", "direita", "cima", "baixo"])
                for _ in range(random.randint(2, 3)):
                    if borda == "esquerda":
                        px = -35.0
                        py = random.uniform(120, max(160.0, h_tela - 120.0))
                    elif borda == "direita":
                        px = w_tela + 35.0
                        py = random.uniform(120, max(160.0, h_tela - 120.0))
                    elif borda == "cima":
                        px = random.uniform(180, max(220.0, w_tela - 180.0))
                        py = -35.0
                    else:
                        px = random.uniform(180, max(220.0, w_tela - 180.0))
                        py = h_tela + 35.0

                    target_x = cx + random.uniform(-40, 40)
                    target_y = cy + random.uniform(-40, 40)
                    ang_m = math.atan2(target_y - py, target_x - px)
                    vel = random.uniform(2.6, 3.4)
                    self.projeteis_bullet_hell.append({
                        "x": px, "y": py,
                        "vx": math.cos(ang_m) * vel,
                        "vy": math.sin(ang_m) * vel,
                        "raio": 6, "cor": (255, 140, 30), "tipo": "plasma"
                    })

            elif padrao == "fogo_cruzado":
                canto = random.choice([
                    (-35.0, -35.0),
                    (w_tela + 35.0, h_tela + 35.0),
                    (w_tela + 35.0, -35.0),
                    (-35.0, h_tela + 35.0),
                ])
                ang_base_m = math.atan2(cy - canto[1], cx - canto[0])
                for offset_ang in [-0.09, 0.09]:
                    vel = random.uniform(2.8, 3.6)
                    self.projeteis_bullet_hell.append({
                        "x": canto[0], "y": canto[1],
                        "vx": math.cos(ang_base_m + offset_ang) * vel,
                        "vy": math.sin(ang_base_m + offset_ang) * vel,
                        "raio": 5, "cor": (70, 220, 255), "tipo": "laser"
                    })

            elif padrao == "vortice_espiral":
                curva = random.choice([-0.008, 0.008])
                for ang_i in [0, 2 * math.pi / 3, 4 * math.pi / 3]:
                    ang = ang_i + random.uniform(-0.15, 0.15)
                    px = cx + math.cos(ang) * 750.0
                    py = cy + math.sin(ang) * 750.0
                    ang_mov = ang + math.pi + (0.28 if curva > 0 else -0.28)
                    vel = 2.2
                    self.projeteis_bullet_hell.append({
                        "x": px, "y": py,
                        "vx": math.cos(ang_mov) * vel,
                        "vy": math.sin(ang_mov) * vel,
                        "curva": curva,
                        "raio": 6, "cor": (255, 225, 70), "tipo": "espiral"
                    })

        projeteis_vivos = []
        if self.invulnerabilidade_mouse > 0:
            self.invulnerabilidade_mouse -= 1

        mx, my = posicao_mouse
        for b in self.projeteis_bullet_hell:
            if b.get("curva", 0) != 0:
                c = b["curva"]
                novo_vx = b["vx"] * math.cos(c) - b["vy"] * math.sin(c)
                novo_vy = b["vx"] * math.sin(c) + b["vy"] * math.cos(c)
                b["vx"], b["vy"] = novo_vx, novo_vy

            b["x"] += b["vx"]
            b["y"] += b["vy"]

            dist_cursor = math.hypot(mx - b["x"], my - b["y"])
            if self.invulnerabilidade_mouse <= 0 and dist_cursor < (8 + b["raio"]):
                self.invulnerabilidade_mouse = 36
                self.bloqueio_desarme_timer = 15
                if self.callback_shake:
                    self.callback_shake(duracao=5, intensidade=4)

                for j in jogadores:
                    if j.hp > 0 and not getattr(j, "god_mode", False):
                        j.hp = max(1, j.hp - 5)

                p_min = 0.50 if self.checkpoint_50 else 0.0
                self.progresso_desarme = max(p_min, self.progresso_desarme - 0.05)
                self.spike.progresso_desarme = self.progresso_desarme

                for _ in range(8):
                    self.particulas_desarme.append({
                        "x": mx, "y": my,
                        "vx": random.uniform(-3, 3), "vy": random.uniform(-3, 3),
                        "vida": 14, "cor": (255, 60, 60)
                    })
                continue

            if -70 <= b["x"] <= w_tela + 70 and -70 <= b["y"] <= h_tela + 70:
                projeteis_vivos.append(b)
        self.projeteis_bullet_hell = projeteis_vivos

        part_vivas = []
        for p in self.particulas_desarme:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vida"] -= 1
            if p["vida"] > 0:
                part_vivas.append(p)
        self.particulas_desarme = part_vivas

        return None

    def desenhar_minigame(self, superficie, posicao_mouse, tempo_animacao=0.0):
        overlay = pygame.Surface((superficie.get_width(), superficie.get_height()), pygame.SRCALPHA)
        overlay.fill((8, 10, 16, 215))
        superficie.blit(overlay, (0, 0))

        w_hud = 540
        h_hud = 62
        hx = (superficie.get_width() - w_hud) // 2
        hy = 85
        pygame.draw.rect(superficie, (18, 22, 32), (hx, hy, w_hud, h_hud), border_radius=10)
        pygame.draw.rect(superficie, (70, 160, 220), (hx, hy, w_hud, h_hud), width=2, border_radius=10)

        t_rest = self.spike.tempo_restante() if self.spike else 0.0
        txt_titulo = self.fonte_status.render("MINIGAME DE DESARME DA SPIKE", True, (240, 245, 255))
        superficie.blit(txt_titulo, (hx + 16, hy + 8))

        cor_timer = (255, 60, 60) if t_rest <= 15 else (255, 180, 50)
        txt_timer = self.fonte_status.render(f"DETONAÇÃO: {t_rest:.1f}s", True, cor_timer)
        superficie.blit(txt_timer, (hx + w_hud - txt_timer.get_width() - 16, hy + 8))

        bx = hx + 16
        by = hy + 34
        bw = w_hud - 32
        bh = 16
        pygame.draw.rect(superficie, (30, 34, 46), (bx, by, bw, bh), border_radius=5)

        prog = max(0.0, min(1.0, self.progresso_desarme))
        largura_preenchida = int(bw * prog)
        cor_barra = (50, 240, 170) if self.checkpoint_50 else (45, 180, 255)
        if largura_preenchida > 0:
            pygame.draw.rect(superficie, cor_barra, (bx, by, largura_preenchida, bh), border_radius=5)

        meio_x = bx + bw // 2
        pygame.draw.line(superficie, (255, 255, 255), (meio_x, by - 3), (meio_x, by + bh + 3), 2)
        pygame.draw.rect(superficie, (160, 185, 215), (bx, by, bw, bh), width=2, border_radius=5)

        txt_pct = self.fonte_inimigo.render(f"{int(prog * 100)}%", True, (255, 255, 255))
        superficie.blit(txt_pct, (bx + (bw - txt_pct.get_width()) // 2, by + 1))

        # Projéteis Bullet Hell
        for b in self.projeteis_bullet_hell:
            x, y, r = int(b["x"]), int(b["y"]), int(b["raio"])
            cor = b.get("cor", (255, 80, 80))
            halo_surf = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
            pygame.draw.circle(halo_surf, (*cor, 80), (r * 2, r * 2), r * 2)
            pygame.draw.circle(halo_surf, (255, 255, 255, 180), (r * 2, r * 2), max(2, r // 2))
            superficie.blit(halo_surf, (x - r * 2, y - r * 2), special_flags=pygame.BLEND_ADD)
            pygame.draw.circle(superficie, cor, (x, y), r)
            pygame.draw.circle(superficie, (255, 255, 255), (x, y), max(1, r - 3))

        # Esfera Centralizada
        cx, cy = int(self.esfera_desarme_pos[0]), int(self.esfera_desarme_pos[1])
        raio = self.esfera_desarme_raio
        dist = math.hypot(posicao_mouse[0] - cx, posicao_mouse[1] - cy)
        dentro = dist <= raio

        bloqueado = self.bloqueio_desarme_timer > 0
        if bloqueado:
            cor_esfera = (255, 50, 50)
            alfa_esfera = 90
        elif dentro:
            cor_esfera = (50, 255, 180)
            alfa_esfera = 65
        else:
            cor_esfera = (255, 80, 80)
            alfa_esfera = 40

        esfera_surf = pygame.Surface((raio * 2 + 20, raio * 2 + 20), pygame.SRCALPHA)
        pygame.draw.circle(esfera_surf, (*cor_esfera, alfa_esfera), (raio + 10, raio + 10), raio)
        pygame.draw.circle(esfera_surf, (*cor_esfera, 230), (raio + 10, raio + 10), raio, width=3)
        pulso_raio = raio + int(math.sin(tempo_animacao * 8.0) * 4)
        pygame.draw.circle(esfera_surf, (*cor_esfera, 130), (raio + 10, raio + 10), pulso_raio, width=1)
        superficie.blit(esfera_surf, (cx - raio - 10, cy - raio - 10))

        if bloqueado:
            txt_status_esfera = "⚡ IMPACTO! DESARME TRAVADO!"
        elif dentro:
            txt_status_esfera = "● DESARMANDO..."
        else:
            txt_status_esfera = "⚠️ FORA DA ESFERA! (-PROGRESSO)"

        surf_lbl = self.fonte_inimigo.render(txt_status_esfera, True, cor_esfera)
        superficie.blit(surf_lbl, (cx - surf_lbl.get_width() // 2, cy + raio + 12))

        for p in self.particulas_desarme:
            pygame.draw.circle(superficie, p.get("cor", (255, 255, 255)), (int(p["x"]), int(p["y"])), 3)

        mx, my = posicao_mouse
        cor_m = (255, 255, 255) if self.invulnerabilidade_mouse % 4 < 2 else (255, 100, 100)
        pygame.draw.circle(superficie, cor_m, (mx, my), 8, width=2)
        pygame.draw.circle(superficie, (255, 50, 50) if not dentro else (50, 255, 180), (mx, my), 3)

        self.btn_cancelar.desenhar(superficie)

    def desenhar_detonacao(self, superficie, tempo_animacao=0.0):
        centro = self.spike.rect.center if self.spike else (superficie.get_width() // 2, 410)
        raio = int(self.spike_raio_detonacao)
        if raio <= 0:
            return

        pygame.draw.circle(superficie, (0, 0, 0), centro, raio)
        pygame.draw.circle(superficie, (255, 255, 255), centro, raio, width=max(4, min(12, raio // 18)))
        pygame.draw.circle(superficie, (220, 240, 255), centro, max(1, raio - 5), width=max(2, min(6, raio // 35)))

        raio_onda1 = raio + int(math.sin(tempo_animacao * 15.0) * 8 + 14)
        if raio_onda1 > 0:
            pygame.draw.circle(superficie, (255, 255, 255), centro, raio_onda1, width=3)

        raio_onda2 = max(1, raio - 28)
        if raio_onda2 > 0:
            pygame.draw.circle(superficie, (200, 230, 255), centro, raio_onda2, width=2)

        num_raios = 32
        for i in range(num_raios):
            ang = (i / num_raios) * 2 * math.pi + (tempo_animacao * 4.0)
            tam_raio = random.randint(20, 65)
            x1 = centro[0] + math.cos(ang) * (raio - 4)
            y1 = centro[1] + math.sin(ang) * (raio - 4)
            x2 = centro[0] + math.cos(ang) * (raio + tam_raio)
            y2 = centro[1] + math.sin(ang) * (raio + tam_raio)
            pygame.draw.line(superficie, (255, 255, 255), (x1, y1), (x2, y2), random.randint(2, 4))

        for p in self.particulas_detonacao:
            pygame.draw.circle(superficie, (255, 255, 255), (int(p["x"]), int(p["y"])), int(p.get("raio", 3)))
