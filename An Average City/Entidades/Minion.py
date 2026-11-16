import json
import os
import random
import pygame
from Sistemas.Fontes import obter_fonte
from Sistemas.Recursos import caminho_dados, caminho_imagem
from Gameplay.Habilidades import Habilidade
from Entidades.EntidadeCombate import EntidadeCombate


def carregar_habilidades_minions():
    try:
        with open(caminho_dados("habilidades_minions.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        print(f"⚠️ Erro ao carregar habilidades_minions.json: {e}")
    return {}


def carregar_minions_personagem():
    try:
        arquivo = caminho_dados("minions_personagem.json")
        if os.path.exists(arquivo):
            with open(arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Erro ao carregar minions_personagem.json: {e}")
    return {}


def carregar_minions_inimigos():
    try:
        arquivo = caminho_dados("minions_inimigos.json")
        if os.path.exists(arquivo):
            with open(arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Erro ao carregar minions_inimigos.json: {e}")
    return {}


def carregar_minions():
    personagem_minions = carregar_minions_personagem()
    inimigo_minions = carregar_minions_inimigos()

    unificado = {}
    unificado.update(personagem_minions)
    unificado.update(inimigo_minions)
    return unificado


BANCO_HABILIDADES_MINIONS = carregar_habilidades_minions()
BANCO_MINIONS_PERSONAGEM = carregar_minions_personagem()
BANCO_MINIONS_INIMIGOS = carregar_minions_inimigos()
BANCO_MINIONS = carregar_minions()


def criar_habilidade_minion(nome, verso):
    if not isinstance(nome, str):
        raise TypeError("Os ataques dos minions devem conter somente nomes de habilidades.")
    if nome not in BANCO_HABILIDADES_MINIONS:
        raise ValueError(f"Habilidade ausente em habilidades_minions.json: {nome}")
    dados = dict(BANCO_HABILIDADES_MINIONS[nome])
    dados["verso"] = verso
    return Habilidade(**dados)


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
        self.lado = "jogador" if (dono and getattr(dono, "is_player", False)) else "inimigo"
        self.congelado = False
        self.atordoado = False
        self.nivel = 1
        self.defendendo = False
        self.dormindo = False
        self.alvo_prioritario = None

        sab_dono = 1
        if dono is not None:
            if hasattr(dono, "obter_atributo_total"):
                sab_dono = int(dono.obter_atributo_total("Sab"))
            else:
                sab_dono = int(getattr(dono, "atributos", {}).get("Sab", 1))

        bonus_sab = max(0, sab_dono - 1)
        atributos_base = dict(atributos) if atributos is not None else {
            "For": 3, "Agi": 4, "Con": 3, "Sab": 4, "Int": 3, "Sor": 2
        }

        inc_sec = bonus_sab // 2
        self.atributos = {
            "For": int(atributos_base.get("For", 3)) + inc_sec,
            "Agi": int(atributos_base.get("Agi", 4)) + inc_sec,
            "Con": int(atributos_base.get("Con", 3)) + inc_sec,
            "Sab": int(atributos_base.get("Sab", 4)) + bonus_sab,
            "Int": int(atributos_base.get("Int", 3)) + inc_sec,
            "Sor": int(atributos_base.get("Sor", 2)) + (bonus_sab // 3),
        }

        hp_calculado = int(vida_maxima) + (bonus_sab * 4)

        self.max_hp = max(10, hp_calculado)
        self.hp = self.max_hp

        mp_base = int(max_mp)
        self.max_mp = max(5, mp_base + bonus_sab) if mp_base > 0 else 0
        self.mp = self.max_mp

        self.habilidades = {}
        self.ataques = []

        for nome_ataque in ataques_dados or ["Investida Espiritual"]:
            hab = criar_habilidade_minion(nome_ataque, verso)
            self.habilidades[hab.nome] = hab
            self.ataques.append(hab.nome)

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
            self.imagem_base = img_escala

            from Sistemas.SistemaOrientacao import sistema_orientacao
            if getattr(self, "inverter_horizontal", False):
                self.direcao_olhar = "oeste"
                self.imagem = pygame.transform.flip(img_escala, True, False)
            else:
                self.direcao_olhar = "leste"
                self.imagem = sistema_orientacao.aplicar_orientacao(self.imagem_base, nome_imagem, "leste")
        except (pygame.error, FileNotFoundError) as e:
            print(f"⚠️ Erro ao carregar imagem do minion ({nome_imagem}): {e}")
            self.imagem_base = pygame.Surface((70, 82))
            self.imagem_base.fill((52, 168, 148))
            self.imagem = self.imagem_base.copy()

        self.rect = self.imagem.get_rect(topleft=(x, y))
        self.convertida = False
        self.fonte_nome = obter_fonte(11)

    @property
    def eh_do_jogador(self) -> bool:
        return bool(self.dono and getattr(self.dono, "is_player", False))

    @property
    def eh_do_inimigo(self) -> bool:
        return not self.eh_do_jogador

    def obter_habilidade(self, nome):
        if nome in self.habilidades:
            return self.habilidades[nome]
        if self.habilidades:
            return next(iter(self.habilidades.values()))
        return criar_habilidade_minion("Investida Espiritual", self.verso)

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
        dano = super().receber_dano(quantidade)
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
    dados = None
    if dono is not None and getattr(dono, "is_player", False):
        dados = BANCO_MINIONS_PERSONAGEM.get(nome_minion)
    elif dono is not None and not getattr(dono, "is_player", False):
        dados = BANCO_MINIONS_INIMIGOS.get(nome_minion)

    if not dados:
        dados = BANCO_MINIONS.get(nome_minion)
    if not dados:
        if dono is not None and getattr(dono, "is_player", False) and BANCO_MINIONS_PERSONAGEM:
            dados = next(iter(BANCO_MINIONS_PERSONAGEM.values()), None)
        elif BANCO_MINIONS_INIMIGOS:
            dados = next(iter(BANCO_MINIONS_INIMIGOS.values()), None)
        else:
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
