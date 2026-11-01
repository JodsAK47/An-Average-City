import json
import os
from Sistemas.Recursos import caminho_dados

CAMINHO_DADOS = caminho_dados()

class Habilidade:
    def __init__(
        self,
        nome,
        tipo,
        dano,
        custo_mp,
        precisao,
        descricao,
        efeito=None,
        chance_efeito=0.0,
        em_area=False,
        verso="Nenhum",
        is_ultimate=False,
        minion=None,
        estilo=None,
    ):
        self.nome = nome
        self.tipo = tipo
        self.dano = dano
        self.custo_mp = custo_mp
        self.precisao = precisao
        self.descricao = descricao
        self.efeito = efeito
        self.chance_efeito = chance_efeito
        self.em_area = em_area
        self.verso = verso
        self.is_ultimate = is_ultimate
        self.minion = minion
        self.estilo = estilo

    def custo_para(self, entidade=None):
        if callable(self.custo_mp):
            return self.custo_mp(entidade)
        return self.custo_mp

def custo_ultimate_total(entidade):
    return getattr(entidade, "max_mp", 0)

ULTIMATES_POR_VERSO_CLASSE = {}
banco_habilidades = {}

def carregar_habilidades_jogador():
    try:
        arquivo = caminho_dados("habilidades_jogador.json")
        with open(arquivo, "r", encoding="utf-8") as f:
            dados = json.load(f)

            for k, v in dados.get("habilidades", {}).items():
                hab = Habilidade(
                    nome=v["nome"],
                    tipo=v["tipo"],
                    dano=v["dano"],
                    custo_mp=v.get("custo_mp", 0),
                    precisao=v["precisao"],
                    descricao=v["descricao"],
                    efeito=v.get("efeito"),
                    chance_efeito=v.get("chance_efeito", 0.0),
                    em_area=v.get("em_area", False),
                    verso=v.get("verso", "Nenhum"),
                    is_ultimate=False,
                    minion=v.get("minion"),
                    estilo=v["estilo"],
                )
                banco_habilidades[k] = hab

            for k, v in dados.get("ultimates", {}).items():
                partes = k.split("|")
                if len(partes) == 2:
                    verso, classe = partes
                    ult = Habilidade(
                        nome=v["nome"],
                        tipo=v["tipo"],
                        dano=v["dano"],
                        custo_mp=custo_ultimate_total,
                        precisao=v["precisao"],
                        descricao=v["descricao"],
                        efeito=v.get("efeito"),
                        chance_efeito=v.get("chance_efeito", 0.0),
                        em_area=v.get("em_area", False),
                        verso=v.get("verso", "Nenhum"),
                        is_ultimate=True,
                        minion=v.get("minion"),
                    )
                    ULTIMATES_POR_VERSO_CLASSE[(verso, classe)] = ult
                    banco_habilidades[ult.nome] = ult

    except FileNotFoundError:
        print("⚠️ Erro: arquivo habilidades_jogador.json não encontrado.")

carregar_habilidades_jogador()

def obter_habilidades_normais(verso, classe):
    return [
        nome for nome, hab in banco_habilidades.items()
        if hab.verso == verso and hab.tipo == classe and not hab.is_ultimate
    ]

def obter_ultimate(verso, classe):
    return ULTIMATES_POR_VERSO_CLASSE.get((verso, classe))
