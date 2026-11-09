import pygame
from Sistemas.Fontes import obter_fonte
from Sistemas.Recursos import caminho_imagem, caminho_dados
from Entidades.EntidadeCombate import EntidadeCombate

import json
import os

CAMINHO_DADOS = caminho_dados()

def carregar_habilidades_inimigos():
    try:
        from Gameplay.Habilidades import Habilidade
        with open(os.path.join(CAMINHO_DADOS, "habilidades_inimigos.json"), "r", encoding="utf-8") as f:
            dados = json.load(f)
            banco = {}
            for k, v in dados.items():
                banco[k] = Habilidade(
                    nome=v["nome"],
                    tipo=v["tipo"],
                    dano=v["dano"],
                    custo_mp=v["custo_mp"],
                    precisao=v["precisao"],
                    descricao=v["descricao"],
                    efeito=v.get("efeito"),
                    chance_efeito=v.get("chance_efeito", 0.0),
                    em_area=v.get("em_area", False),
                    verso=v.get("verso", "Inimigo"),
                    is_ultimate=v.get("is_ultimate", False),
                    minion=v.get("minion")
                )
            return banco
    except FileNotFoundError:
        print("[Aviso] Erro: arquivo habilidades_inimigos.json não encontrado.")
        return {}

_banco_habilidades_inimigos = None

def obter_banco_habilidades_inimigos():
    global _banco_habilidades_inimigos
    if _banco_habilidades_inimigos is None:
        _banco_habilidades_inimigos = carregar_habilidades_inimigos()
    return _banco_habilidades_inimigos

class Inimigo(EntidadeCombate):
    def __init__(self, x, y, vida_maxima, nome_imagem, nome="Inimigo", ataques=None, xp=0, atributos=None, max_mp=None, tipo="comum", classe=None):
        super().__init__(nome=nome, max_hp=vida_maxima, max_mp=max_mp or 10, atributos=atributos, is_player=False)
        self.nome = nome
        self.tipo = tipo
        self.classe = classe
        self.arquivo_imagem = nome_imagem
        self.max_hp = vida_maxima
        self.hp = vida_maxima
        self.ataques = ataques if ataques is not None else ["Soco"]
        banco = obter_banco_habilidades_inimigos()
        if max_mp is not None:
            self.max_mp = max_mp
        else:
            custo_max_mp = max(
                (
                    banco[nome_ataque].custo_mp
                    for nome_ataque in self.ataques
                    if nome_ataque in banco
                ),
                default=0,
            )
            self.max_mp = max(10, custo_max_mp * 3)
        self.mp = 10 if "sukuna" in self.nome.lower() else 0

        self.congelado = False
        self.atordoado = False
        self.xp = xp
        self.carga_confinamento = 0
        self.max_carga_confinamento = 5
        self.eh_confinamento = bool("confinamento" in self.nome.lower() or "Confinamento" in self.ataques)

        self.derrotado = False
        self.timer_fade_derrota = 0
        self.max_fade_derrota = 45
        self.particulas_derrota = []
        self.imagem_destruida_base = None

        self.atributos = atributos if atributos is not None else {"For": 1, "Agi": 1, "Int": 1, "Sor": 1}
        self.is_player = False

        try:
            self.imagem_original = pygame.image.load(caminho_imagem(nome_imagem))
            w_orig, h_orig = self.imagem_original.get_size()
            altura_desejada = 125 if (tipo in ("chefe", "grande") or "chefe" in nome.lower() or "sukuna" in nome.lower() or "especial" in nome.lower()) else 110
            largura_desejada = int(w_orig * (altura_desejada / max(1, h_orig)))
            self.imagem_base = pygame.transform.scale(self.imagem_original, (largura_desejada, altura_desejada))
        except (pygame.error, FileNotFoundError) as e:
            print(f"[Aviso] Erro ao carregar imagem do inimigo ({nome_imagem}): {e}")
            self.imagem_base = pygame.Surface((100, 110))
            self.imagem_base.fill((200, 50, 50))

        if self.eh_confinamento:
            try:
                dest_path = caminho_imagem("Confinamento_destruido.png")
                orig_dest = pygame.image.load(dest_path)
                w_d, h_d = orig_dest.get_size()
                proporcao = 125.0 / 449.0
                alt_dest = max(20, int(h_d * proporcao))
                larg_dest = max(20, int(w_d * proporcao))
                self.imagem_destruida_base = pygame.transform.scale(orig_dest, (larg_dest, alt_dest))
            except Exception as e:
                print(f"[Aviso] Não foi possível carregar Confinamento_destruido.png: {e}")
                self.imagem_destruida_base = None

        self.imagem_viva_base = self.imagem_base.copy()

        from Sistemas.SistemaOrientacao import sistema_orientacao
        self.direcao_olhar = "oeste"
        self.quadrante = "leste"
        self.imagem = sistema_orientacao.aplicar_orientacao(self.imagem_base, nome_imagem, "oeste")
        self.rect = self.imagem.get_rect(topleft=(x, y))
        self.convertida = False
        self.fonte_nome = obter_fonte(13)

        # Atualiza a orientação inicial de acordo com o quadrante em que foi criado (se já tiver posição x definida)
        if x > 0:
            self.atualizar_orientacao_por_quadrante()

    def receber_dano(self, quantidade: int) -> int:
        dano_causado = super().receber_dano(quantidade)
        if self.hp <= 0 and not self.derrotado:
            self.acionar_derrota()
        return dano_causado

    def acionar_derrota(self):
        if not self.derrotado:
            self.derrotado = True
            self.timer_fade_derrota = self.max_fade_derrota
            if self.eh_confinamento and getattr(self, "imagem_destruida_base", None) is not None:
                centro_x = self.rect.centerx
                bottom_y = self.rect.bottom
                from Sistemas.SistemaOrientacao import sistema_orientacao
                self.imagem = sistema_orientacao.aplicar_orientacao(
                    self.imagem_destruida_base, "Confinamento_destruido.png", self.direcao_olhar
                )
                self.rect = self.imagem.get_rect(midbottom=(centro_x, bottom_y))
                self.convertida = False

    def restaurar_estado_vivo(self):
        self.derrotado = False
        self.timer_fade_derrota = 0
        self.particulas_derrota.clear()
        if hasattr(self, 'imagem_viva_base') and self.imagem_viva_base is not None:
            centro_x = self.rect.centerx
            bottom_y = self.rect.bottom
            self.imagem_base = self.imagem_viva_base.copy()
            from Sistemas.SistemaOrientacao import sistema_orientacao
            self.imagem = sistema_orientacao.aplicar_orientacao(
                self.imagem_base, self.arquivo_imagem, self.direcao_olhar
            )
            self.rect = self.imagem.get_rect(midbottom=(centro_x, bottom_y))
            self.convertida = False

    def atualizar_animacao_derrota(self):
        if self.derrotado and self.timer_fade_derrota > 0:
            self.timer_fade_derrota -= 1
            if self.timer_fade_derrota % 5 == 0:
                import random
                if self.eh_confinamento:
                    cor_p = (255, 215, 60) if random.random() < 0.6 else (70, 220, 245)
                elif "sukuna" in self.nome.lower():
                    cor_p = (220, 45, 65) if random.random() < 0.5 else (180, 80, 255)
                else:
                    cor_p = (160, 185, 210)
                self.particulas_derrota.append({
                    "x": self.rect.centerx + random.uniform(-18, 18),
                    "y": self.rect.centery + random.uniform(-12, 12),
                    "vx": random.uniform(-0.6, 0.6),
                    "vy": random.uniform(-1.5, -0.5),
                    "vida": 22,
                    "vida_max": 22,
                    "cor": cor_p
                })

        part_vivas = []
        for p in self.particulas_derrota:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vida"] -= 1
            if p["vida"] > 0:
                part_vivas.append(p)
        self.particulas_derrota = part_vivas

    def virar_para(self, direcao: str):
        """
        Altera para qual lado o inimigo está virado ('leste' ou 'oeste').
        Preserva a posição central do rect para evitar deslocamento indesejado.
        Utiliza o SistemaOrientacao para respeitar a orientação nativa do sprite.
        """
        return super().virar_para(direcao)

    def obter_quadrante(self, largura_tela=None) -> str:
        """
        Retorna em qual quadrante ('oeste' ou 'leste') o inimigo está posicionado.
        """
        from Sistemas.SistemaQuadrantes import sistema_quadrantes
        return sistema_quadrantes.identificar_quadrante(self, largura_tela=largura_tela)

    def obter_ponto_tela(self):
        """
        Retorna as coordenadas (x, y) do ponto central do inimigo na tela.
        """
        from Sistemas.SistemaQuadrantes import sistema_quadrantes
        return sistema_quadrantes.obter_ponto(self)

    def obter_info_posicao(self, largura_tela=None):
        """
        Retorna informações detalhadas de posicionamento, quadrante e orientação.
        """
        from Sistemas.SistemaQuadrantes import sistema_quadrantes
        return sistema_quadrantes.obter_detalhes_posicao(self, largura_tela=largura_tela)

    def atualizar_orientacao_por_quadrante(self, largura_tela=None, modo="para_centro", alvo=None):
        """
        Verifica o ponto na tela e gerencia para qual lado o inimigo fica virado.
        """
        from Sistemas.SistemaQuadrantes import sistema_quadrantes
        return sistema_quadrantes.gerenciar_orientacao(self, modo=modo, alvo=alvo, largura_tela=largura_tela)

    def obter_habilidade(self, nome):
        banco = obter_banco_habilidades_inimigos()
        return banco.get(nome, banco.get("Soco"))

    def clone(self):
        novo_inimigo = Inimigo(
            self.rect.x,
            self.rect.y,
            self.max_hp,
            self.arquivo_imagem,
            self.nome,
            list(self.ataques),
            self.xp,
            dict(self.atributos),
            max_mp=self.max_mp,
            tipo=self.tipo,
            classe=self.classe
        )
        novo_inimigo.hp = self.hp
        novo_inimigo.mp = self.mp
        novo_inimigo.congelado = self.congelado
        novo_inimigo.atordoado = self.atordoado
        novo_inimigo.queimando = getattr(self, "queimando", False)
        novo_inimigo.envenenado = getattr(self, "envenenado", False)
        novo_inimigo.cego = getattr(self, "cego", False)
        novo_inimigo.turnos_cegueira = getattr(self, "turnos_cegueira", 0)
        novo_inimigo.turnos_fogo = getattr(self, "turnos_fogo", 0)
        novo_inimigo.turnos_veneno = getattr(self, "turnos_veneno", 0)
        novo_inimigo.carga_confinamento = self.carga_confinamento
        novo_inimigo.max_carga_confinamento = self.max_carga_confinamento
        novo_inimigo.eh_confinamento = self.eh_confinamento
        novo_inimigo.imagem_destruida_base = getattr(self, "imagem_destruida_base", None)
        novo_inimigo.imagem_viva_base = getattr(self, "imagem_viva_base", None)
        novo_inimigo.virar_para(self.direcao_olhar)
        novo_inimigo.quadrante = self.quadrante
        return novo_inimigo

    def desenhar(self, tela, desenhar_nome=True):
        if self.hp > 0:
            if not self.convertida:
                try:
                    self.imagem = self.imagem.convert_alpha()
                except pygame.error:
                    pass
                self.convertida = True

            tela.blit(self.imagem, self.rect)

            if desenhar_nome:
                txt = self.fonte_nome.render(self.nome, True, (255, 255, 255))
                tela.blit(txt, (self.rect.centerx - txt.get_width()//2, self.rect.y - 20))

            if getattr(self, "eh_confinamento", False):
                bw = 74
                bh = 9
                bx = self.rect.centerx - bw // 2
                by = self.rect.bottom + 6
                pygame.draw.rect(tela, (15, 20, 28), (bx, by, bw, bh), border_radius=4)
                max_c = max(1, getattr(self, "max_carga_confinamento", 5))
                seg_w = (bw - 6) // max_c
                for seg in range(max_c):
                    seg_x = bx + 2 + seg * (seg_w + 1)
                    if seg < getattr(self, "carga_confinamento", 0):
                        cor_seg = (255, 60, 60) if self.carga_confinamento >= (max_c - 1) else (255, 200, 40)
                        pygame.draw.rect(tela, cor_seg, (seg_x, by + 2, seg_w, bh - 4), border_radius=2)
                    else:
                        pygame.draw.rect(tela, (40, 45, 60), (seg_x, by + 2, seg_w, bh - 4), border_radius=2)
                pygame.draw.rect(tela, (70, 160, 220), (bx, by, bw, bh), width=1, border_radius=4)
                txt_carga = self.fonte_nome.render(f"CARGA: {self.carga_confinamento}/{max_c}", True, (255, 220, 80))
                tela.blit(txt_carga, (self.rect.centerx - txt_carga.get_width() // 2, by + bh + 2))

        elif self.timer_fade_derrota > 0:
            if not self.convertida:
                try:
                    self.imagem = self.imagem.convert_alpha()
                except pygame.error:
                    pass
                self.convertida = True

            # Efeito fade-out estilo Spike nos frames restantes
            alfa = int(255 * (max(0, self.timer_fade_derrota) / float(self.max_fade_derrota)))
            surf_fade = self.imagem.copy()
            surf_fade.set_alpha(alfa)
            tela.blit(surf_fade, self.rect)

            # Partículas de fumaça / faíscas de derrota
            for p in self.particulas_derrota:
                alfa_p = int(190 * (p["vida"] / float(p["vida_max"])))
                surf_p = pygame.Surface((6, 6), pygame.SRCALPHA)
                cor_p = p.get("cor", (160, 185, 210))
                pygame.draw.circle(surf_p, (cor_p[0], cor_p[1], cor_p[2], alfa_p), (3, 3), 3)
                tela.blit(surf_p, (int(p["x"]) - 3, int(p["y"]) - 3), special_flags=pygame.BLEND_ADD)
