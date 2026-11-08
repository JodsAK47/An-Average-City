import json
import os
import random
import pygame
from Sistemas.Fontes import obter_fonte
from Sistemas.Recursos import caminho_dados, caminho_imagem
from Gameplay.Habilidades import Habilidade
from Entidades.EntidadeCombate import EntidadeCombate


def carregar_minions():
    try:
        arquivo = caminho_dados("minions.json")
        with open(arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ Aviso: arquivo minions.json não encontrado.")
        return {}


BANCO_MINIONS = carregar_minions()


class Minion(EntidadeCombate):
    def __init__(
        self,
        x=0,
        y=0,
        nome="Minion",
        vida_maxima=30,
        nome_imagem="Abelha.png",
        ataques_dados=None,
        atributos=None,
        max_mp=10,
        verso="Sobrevivente",
        dono=None,
        inverter_horizontal=False,
        descricao="",
    ):
        super().__init__(nome=nome, max_hp=vida_maxima, max_mp=max_mp, is_player=False)
        self.nome = nome
        self.verso = verso
        self.dono = dono
        self.arquivo_imagem = nome_imagem
        self.inverter_horizontal = bool(inverter_horizontal)
        self.descricao = descricao

        self.is_minion = True
        self.is_player = False
        self.congelado = False
        self.atordoado = False
        self.nivel = 1
        self.defendendo = False
        self.dormindo = False
        self.alvo_prioritario = None

        sab_dono = 1
        tem_i1 = False
        if dono is not None:
            if hasattr(dono, "obter_atributo_total"):
                sab_dono = int(dono.obter_atributo_total("Sab"))
            else:
                sab_dono = int(getattr(dono, "atributos", {}).get("Sab", 1))
            if hasattr(dono, "tem_talento"):
                tem_i1 = bool(dono.tem_talento("I1"))
            else:
                tem_i1 = "I1" in getattr(dono, "talentos", set())

        bonus_sab = max(0, sab_dono - 1)
        atributos_base = dict(atributos) if atributos is not None else {
            "For": 3, "Agi": 4, "Con": 3, "Sab": 4, "Int": 3, "Sor": 2
        }

        inc_sec = bonus_sab // 2
        inc_talento = 2 if tem_i1 else 0
        self.atributos = {
            "For": int(atributos_base.get("For", 3)) + inc_sec + inc_talento,
            "Agi": int(atributos_base.get("Agi", 4)) + inc_sec + inc_talento,
            "Con": int(atributos_base.get("Con", 3)) + inc_sec + inc_talento,
            "Sab": int(atributos_base.get("Sab", 4)) + bonus_sab + inc_talento,
            "Int": int(atributos_base.get("Int", 3)) + inc_sec + inc_talento,
            "Sor": int(atributos_base.get("Sor", 2)) + (bonus_sab // 3) + inc_talento,
        }

        hp_calculado = int(vida_maxima) + (bonus_sab * 4) + (inc_talento * 5)
        if tem_i1:
            hp_calculado = int(hp_calculado * 1.25)

        self.max_hp = max(10, hp_calculado)
        self.hp = self.max_hp

        self.max_mp = max(5, int(max_mp) + bonus_sab)
        self.mp = self.max_mp

        self.habilidades = {}
        self.ataques = []

        if ataques_dados:
            for item in ataques_dados:
                if isinstance(item, dict):
                    hab = Habilidade(
                        nome=item["nome"],
                        tipo=item.get("tipo", "Invocador"),
                        dano=item.get("dano", 6),
                        custo_mp=item.get("custo_mp", 0),
                        precisao=item.get("precisao", 0.90),
                        descricao=item.get("descricao", ""),
                        efeito=item.get("efeito"),
                        chance_efeito=item.get("chance_efeito", 0.0),
                        em_area=item.get("em_area", False),
                        verso=verso,
                    )
                    self.habilidades[hab.nome] = hab
                    self.ataques.append(hab.nome)
                elif isinstance(item, Habilidade):
                    self.habilidades[item.nome] = item
                    self.ataques.append(item.nome)
                elif isinstance(item, str):
                    self.ataques.append(item)

        if not self.ataques:
            hab_padrao = Habilidade(
                nome="Investida Espiritual",
                tipo="Invocador",
                dano=7,
                custo_mp=0,
                precisao=0.90,
                descricao="Ataque básico do minion.",
                verso=verso,
            )
            self.habilidades[hab_padrao.nome] = hab_padrao
            self.ataques.append(hab_padrao.nome)

        self.estatisticas = {
            "dano_causado": 0,
            "ataques_realizados": 0,
            "acertos": 0,
            "criticos": 0,
            "abates": 0,
            "dano_recebido": 0,
            "turnos_ativo": 0,
        }

        try:
            self.imagem_original = pygame.image.load(caminho_imagem(nome_imagem))
            w_orig, h_orig = self.imagem_original.get_size()
            altura_desejada = 82
            largura_desejada = max(45, int(w_orig * (altura_desejada / max(1, h_orig))))
            img_escala = pygame.transform.scale(self.imagem_original, (largura_desejada, altura_desejada))
            # aliados e skins ficam virados para a direita; inimigos são forçados para a esquerda
            if getattr(self, "is_minion", False):
                if getattr(self, "inverter_horizontal", False):
                    self.imagem = pygame.transform.flip(img_escala, True, False)
                else:
                    self.imagem = img_escala
            elif getattr(self, "is_player", False):
                self.imagem = img_escala
            else:
                self.imagem = pygame.transform.flip(img_escala, True, False)
        except (pygame.error, FileNotFoundError) as e:
            print(f"⚠️ Erro ao carregar imagem do minion ({nome_imagem}): {e}")
            self.imagem = pygame.Surface((70, 82))
            self.imagem.fill((52, 168, 148))

        self.rect = self.imagem.get_rect(topleft=(x, y))
        self.convertida = False
        self.fonte_nome = obter_fonte(11)

    def obter_habilidade(self, nome):
        if nome in self.habilidades:
            return self.habilidades[nome]
        if self.habilidades:
            return next(iter(self.habilidades.values()))
        return Habilidade("Investida Espiritual", "Invocador", 7, 0, 0.90, "Ataque básico.")

    def escolher_ataque(self):
        disponiveis = [
            nome for nome in self.ataques
            if self.obter_habilidade(nome).custo_mp <= self.mp
        ]
        if not disponiveis:
            return self.ataques[0]
        especiais = [
            nome for nome in disponiveis
            if self.obter_habilidade(nome).custo_mp > 0
        ]
        if especiais and random.random() < 0.65:
            return random.choice(especiais)
        return random.choice(disponiveis)

    def calcular_dano_ataque(self, hab):
        sab_minion = int(self.atributos.get("Sab", 1))
        for_minion = int(self.atributos.get("For", 1))
        dano_base = int(hab.dano) + sab_minion + (for_minion // 2)
        if self.dono is not None:
            tem_i4 = (
                self.dono.tem_talento("I4")
                if hasattr(self.dono, "tem_talento")
                else ("I4" in getattr(self.dono, "talentos", set()))
            )
            if tem_i4:
                dano_base = int(dano_base * 1.20)
        return max(1, dano_base)

    def curar_e_fortalecer(self, bonus_sab=2, cura_percentual=0.50):
        self.nivel += 1
        self.max_hp += 6 + max(0, int(bonus_sab))
        cura = max(8, int(self.max_hp * cura_percentual))
        self.hp = min(self.max_hp, self.hp + cura)
        self.mp = self.max_mp
        self.atributos["Sab"] = self.atributos.get("Sab", 1) + max(1, int(bonus_sab))
        self.atributos["For"] = self.atributos.get("For", 1) + 1

    def receber_dano(self, quantidade):
        dano = max(0, int(quantidade))
        self.hp = max(0, self.hp - dano)
        self.estatisticas["dano_recebido"] += dano
        return dano

    def registrar_ataque(self, dano=0, acertou=True, critico=False, abates=0):
        self.estatisticas["ataques_realizados"] += 1
        self.estatisticas["turnos_ativo"] += 1
        if acertou:
            self.estatisticas["acertos"] += 1
            self.estatisticas["dano_causado"] += max(0, int(dano))
        if critico:
            self.estatisticas["criticos"] += 1
        if abates > 0:
            self.estatisticas["abates"] += int(abates)

        if self.dono is not None and hasattr(self.dono, "estatisticas_minions"):
            self.dono.estatisticas_minions["dano_total_minions"] = (
                self.dono.estatisticas_minions.get("dano_total_minions", 0) + max(0, int(dano))
            )
            self.dono.estatisticas_minions["abates_minions"] = (
                self.dono.estatisticas_minions.get("abates_minions", 0) + max(0, int(abates))
            )

    def desenhar(self, tela, desenhar_nome=False):
        if self.hp > 0:
            if not self.convertida:
                try:
                    self.imagem = self.imagem.convert_alpha()
                except pygame.error:
                    pass
                self.convertida = True

            tela.blit(self.imagem, self.rect)
            if desenhar_nome:
                txt = self.fonte_nome.render(self.nome, True, (160, 255, 235))
                tela.blit(txt, (self.rect.centerx - txt.get_width() // 2, self.rect.y - 18))


def criar_minion(nome_minion, dono=None, x=0, y=0):
    dados = BANCO_MINIONS.get(nome_minion)
    if not dados:
        dados = next(iter(BANCO_MINIONS.values()), None)
    if not dados:
        return Minion(x=x, y=y, nome=nome_minion, dono=dono)

    return Minion(
        x=x,
        y=y,
        nome=dados.get("nome", nome_minion),
        vida_maxima=dados.get("max_hp", 30),
        nome_imagem=dados.get("arquivo_imagem", "Abelha.png"),
        ataques_dados=dados.get("ataques", []),
        atributos=dados.get("atributos"),
        max_mp=dados.get("max_mp", 10),
        verso=dados.get("verso", "Sobrevivente"),
        dono=dono,
        inverter_horizontal=dados.get("inverter_horizontal", False),
        descricao=dados.get("descricao", ""),
    )
