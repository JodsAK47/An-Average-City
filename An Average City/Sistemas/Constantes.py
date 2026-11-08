"""
Constantes e Enums Universais para o jogo An Average City.
Padroniza identificadores de Versos, Classes, Atributos e evita duplicação de dados.
"""

import unicodedata
from enum import Enum


def normalizar_identificador(texto: str) -> str:
    """
    Remove acentos, espaços extras e converte para minúsculas.
    Exemplo: 'Físico' -> 'fisico', 'Distância' -> 'distancia', '  Sobrevivente  ' -> 'sobrevivente'.
    """
    if not texto:
        return ""
    texto_str = str(texto).strip().lower()
    # Remove acentos via decomposição Unicode
    normalizado = unicodedata.normalize("NFD", texto_str)
    sem_acentos = "".join(c for c in normalizado if unicodedata.category(c) != "Mn")
    return sem_acentos


class Verso(str, Enum):
    SOBREVIVENTE = "Sobrevivente"
    AGENTE = "Agente"
    FEITICEIRO = "Feiticeiro"

    @classmethod
    def normalizar(cls, valor: str):
        v = normalizar_identificador(valor)
        if v in ("sobrevivente", "survivor"):
            return cls.SOBREVIVENTE
        if v in ("agente", "agent"):
            return cls.AGENTE
        if v in ("feiticeiro", "sorcerer"):
            return cls.FEITICEIRO
        return cls.SOBREVIVENTE


class Classe(str, Enum):
    FISICO = "Físico"
    DISTANCIA = "Distância"
    MAGIA = "Magia"
    INVOCADOR = "Invocador"

    @classmethod
    def normalizar(cls, valor: str):
        c = normalizar_identificador(valor)
        if c in ("fisico", "forca"):
            return cls.FISICO
        if c in ("distancia", "agilidade"):
            return cls.DISTANCIA
        if c in ("magia", "intelecto"):
            return cls.MAGIA
        if c in ("invocador", "invocacao", "sabedoria"):
            return cls.INVOCADOR
        return cls.FISICO


MAPA_ATRIBUTO_CLASSE = {
    Classe.FISICO: "For",
    "Físico": "For",
    "Fisico": "For",
    Classe.MAGIA: "Int",
    "Magia": "Int",
    Classe.DISTANCIA: "Agi",
    "Distância": "Agi",
    "Distancia": "Agi",
    Classe.INVOCADOR: "Sab",
    "Invocador": "Sab",
    "Invocação": "Sab",
    "Invocacao": "Sab",
}

# Tabela canônica de equipamentos iniciais (sem duplicatas)
TABELA_EQUIPAMENTOS_INICIAIS = {
    (Verso.SOBREVIVENTE, Classe.FISICO): ("Machado", {"For": 2}),
    (Verso.SOBREVIVENTE, Classe.DISTANCIA): ("Estilingue", {"Agi": 2}),
    (Verso.SOBREVIVENTE, Classe.MAGIA): ("Pedra Preciosa Multicor", {"Int": 2}),
    (Verso.SOBREVIVENTE, Classe.INVOCADOR): ("Flauta de Pã", {"Sab": 2}),

    (Verso.AGENTE, Classe.FISICO): ("Faca de Confronto", {"For": 2}),
    (Verso.AGENTE, Classe.DISTANCIA): ("Vandal", {"Agi": 2}),
    (Verso.AGENTE, Classe.MAGIA): ("Rocha De Radianita", {"Int": 2}),
    (Verso.AGENTE, Classe.INVOCADOR): ("Bracelete de Comando", {"Sab": 2}),

    (Verso.FEITICEIRO, Classe.FISICO): ("Katana", {"For": 2}),
    (Verso.FEITICEIRO, Classe.DISTANCIA): ("Amplificador de alcance", {"Agi": 2}),
    (Verso.FEITICEIRO, Classe.MAGIA): ("Ferramenta Amaldiçoada", {"Int": 2}),
    (Verso.FEITICEIRO, Classe.INVOCADOR): ("Amuleto das Dez Sombras", {"Sab": 2}),
}

# Multiplicadores de dano canônicos (sem duplicatas)
MULTIPLICADORES_VERSO_TIPO = {
    (Verso.SOBREVIVENTE, Classe.FISICO): 2.0,
    (Verso.SOBREVIVENTE, Classe.INVOCADOR): 1.8,
    (Verso.AGENTE, Classe.DISTANCIA): 1.8,
    (Verso.AGENTE, Classe.INVOCADOR): 1.8,
    (Verso.FEITICEIRO, Classe.MAGIA): 2.0,
    (Verso.FEITICEIRO, Classe.INVOCADOR): 2.0,
}

# Suporte retrocompatível a buscas diretas com strings (com ou sem acento / maiúsculas)
for (_v, _c), _item in list(TABELA_EQUIPAMENTOS_INICIAIS.items()):
    TABELA_EQUIPAMENTOS_INICIAIS[(_v.value, _c.value)] = _item
    TABELA_EQUIPAMENTOS_INICIAIS[(normalizar_identificador(_v.value), normalizar_identificador(_c.value))] = _item

for (_v, _c), _mult in list(MULTIPLICADORES_VERSO_TIPO.items()):
    MULTIPLICADORES_VERSO_TIPO[(_v.value, _c.value)] = _mult
    MULTIPLICADORES_VERSO_TIPO[(normalizar_identificador(_v.value), normalizar_identificador(_c.value))] = _mult


def obter_equipamento_inicial(verso, classe_dano):
    v = Verso.normalizar(verso)
    c = Classe.normalizar(classe_dano)
    return TABELA_EQUIPAMENTOS_INICIAIS.get((v, c), ("Equipamento Padrão", {}))


def obter_multiplicador_verso_classe(verso, classe_dano) -> float:
    v = Verso.normalizar(verso)
    c = Classe.normalizar(classe_dano)
    return MULTIPLICADORES_VERSO_TIPO.get((v, c), 1.0)


# Mapeamento canônico das músicas (OSTs) de combate e chefe por Verso
MAPA_MUSICA_VERSO = {
    Verso.SOBREVIVENTE: {
        "combate": "Sobrevivente Combate.mp3",
        "boss": "Sobrevivente Boss.mp3",
    },
    Verso.AGENTE: {
        "combate": "Agente Combate.mp3",
        "boss": "Agente Boss.mp3",
    },
    Verso.FEITICEIRO: {
        "combate": "Feiticeiro Combate.mp3",
        "boss": "Feiticeiro Boss.mp3",
    },
}


def obter_musica_combate(verso=None, eh_chefe: bool = False) -> str:
    """
    Retorna o nome do arquivo da OST de combate ou chefe correspondente ao verso.
    Exemplos:
      obter_musica_combate("Sobrevivente", eh_chefe=False) -> "Sobrevivente Combate.mp3"
      obter_musica_combate("Agente", eh_chefe=True) -> "Agente Boss.mp3"
      obter_musica_combate("Feiticeiro", eh_chefe=True) -> "Feiticeiro Boss.mp3"
    """
    v = Verso.normalizar(verso)
    tipo = "boss" if eh_chefe else "combate"
    sub_map = MAPA_MUSICA_VERSO.get(v, MAPA_MUSICA_VERSO[Verso.SOBREVIVENTE])
    return sub_map[tipo]

