import os
import json
def _obter_personagem_padrao():
    from Entidades.Personagem import personagem
    return personagem

class Consumivel:
    def __init__(self, nome, descricao, rec_hp=0, rec_mp=0, arquivo_imagem=None):
        self.nome = nome
        self.descricao = descricao
        self.quantidade = 1
        self.tipo = "consumivel"
        self.atributos_bonus = {}
        self.rec_hp = rec_hp
        self.rec_mp = rec_mp
        self.arquivo_imagem = arquivo_imagem or obter_arquivo_imagem_item(nome)

    def usar(self, alvo=None):
        if self.quantidade <= 0:
            return False
        alvo_final = alvo if alvo is not None else _obter_personagem_padrao()
        fator = 2 if getattr(alvo_final, "tem_talento", lambda t: False)("S2") else 1
        alvo_final.hp = min(alvo_final.max_hp, alvo_final.hp + (self.rec_hp * fator))
        alvo_final.mp = min(alvo_final.max_mp, alvo_final.mp + (self.rec_mp * fator))
        self.quantidade -= 1

        try:
            from Sistemas.GerenciadorAudio import tocar_sfx
            nome_norm = (self.nome or "").lower()
            if any(termo in nome_norm for termo in ["marmita", "comida", "refeicao", "refeição", "alimento", "pao", "pão"]):
                tocar_sfx("Comer.wav")
            else:
                tocar_sfx("Beber.wav")
        except Exception:
            pass

        from Sistemas.Conquistas import sistema_conquistas
        sistema_conquistas.desbloquear("alquimista")
        return True

class Material:
    def __init__(self, nome, descricao, arquivo_imagem=None):
        self.nome = nome
        self.descricao = descricao
        self.quantidade = 1
        self.tipo = "material"
        self.arquivo_imagem = arquivo_imagem or obter_arquivo_imagem_item(nome)

    def usar(self, alvo=None):
        return False

class ItemBilhete:
    def __init__(self, quantidade=1, arquivo_imagem="TIcket.png"):
        self.nome = "Bilhete do Dormitório"
        self.descricao = "Permite dormir no dormitório para recuperar mais HP e PM."
        self.quantidade = quantidade
        self.tipo = "bilhete"
        self.arquivo_imagem = arquivo_imagem

    def usar(self, alvo=None):
        return False

CATEGORIAS_EQUIPAMENTO = ("arma", "capacete", "peitoral", "calca", "bota", "amuleto")

_CATALOGO_EQUIPAMENTOS_PADRAO = [
    {"nome": "Capacete de Ferro", "categoria": "capacete", "atributos_bonus": {"Con": 2}},
    {"nome": "Capacete Tático", "categoria": "capacete", "atributos_bonus": {"Sab": 2, "Agi": 1}},
    {"nome": "Capuz Sombrio", "categoria": "capacete", "atributos_bonus": {"Int": 2, "Sor": 1}},
    {"nome": "Peitoral de Aço", "categoria": "peitoral", "atributos_bonus": {"Con": 3, "For": 1}},
    {"nome": "Colete Balístico", "categoria": "peitoral", "atributos_bonus": {"Con": 2, "Agi": 2}},
    {"nome": "Manto Arcano", "categoria": "peitoral", "atributos_bonus": {"Int": 3, "Sab": 1}},
    {"nome": "Calça Reforçada", "categoria": "calca", "atributos_bonus": {"Con": 2, "For": 1}},
    {"nome": "Calça Tática", "categoria": "calca", "atributos_bonus": {"Agi": 2, "Con": 1}},
    {"nome": "Calça de Feiticeiro", "categoria": "calca", "atributos_bonus": {"Sab": 2, "Int": 1}},
    {"nome": "Botas de Combate", "categoria": "bota", "atributos_bonus": {"For": 2, "Agi": 1}},
    {"nome": "Botas Velozes", "categoria": "bota", "atributos_bonus": {"Agi": 3}},
    {"nome": "Botas Místicas", "categoria": "bota", "atributos_bonus": {"Int": 1, "Sab": 1, "Sor": 1}},
    {"nome": "Amuleto do Mago", "categoria": "amuleto", "atributos_bonus": {"Int": 2}},
    {"nome": "Amuleto da Força", "categoria": "amuleto", "atributos_bonus": {"For": 2}},
    {"nome": "Amuleto da Agilidade", "categoria": "amuleto", "atributos_bonus": {"Agi": 2}},
    {"nome": "Amuleto da Sorte", "categoria": "amuleto", "atributos_bonus": {"Sor": 2}},
    {"nome": "Amuleto Vital", "categoria": "amuleto", "atributos_bonus": {"Con": 2}},
    {"nome": "Amuleto da Sabedoria", "categoria": "amuleto", "atributos_bonus": {"Sab": 2}},
]

_DADOS_ITENS_CACHE = None

def carregar_dados_itens():
    global _DADOS_ITENS_CACHE
    if _DADOS_ITENS_CACHE is not None:
        return _DADOS_ITENS_CACHE
    try:
        from Sistemas.Recursos import caminho_dados
        arquivo = caminho_dados("itens.json")
        if os.path.exists(arquivo):
            with open(arquivo, "r", encoding="utf-8") as f:
                _DADOS_ITENS_CACHE = json.load(f)
                return _DADOS_ITENS_CACHE
    except Exception as e:
        print(f"[Aviso] Nao foi possivel carregar itens.json: {e}")
    return {}


MAPA_SPRITES_ITENS = {
    # Consumíveis com arte própria
    "pocao de vida": "Pocao Cura.png",
    "poção de vida": "Pocao Cura.png",
    "pocao de mana": "Pocao Mana.png",
    "poção de mana": "Pocao Mana.png",
    "pocao de vida reforcada": "Pocao Recuperacao.png",
    "poção de vida reforçada": "Pocao Recuperacao.png",
    "cha de mana concentrado": "Cha.png",
    "chá de mana concentrado": "Cha.png",
    "cafe expresso revigorante": "Cafe.png",
    "café expresso revigorante": "Cafe.png",
    "marmita nutritiva especial": "Marmita.png",
    "marmita": "Marmita.png",

    # Materiais com arte própria
    "sucata": "Sucata.png",

    # Especiais com arte própria
    "bilhete do dormitorio": "TIcket.png",
    "bilhete do dormitório": "TIcket.png",
    "bilhete dormitorio": "TIcket.png",
    "bilhete dormitório": "TIcket.png",
    "bilhete": "TIcket.png",
    "ticket": "TIcket.png",
    "ticket de dormir": "TIcket.png",
    "ticket do dormitorio": "TIcket.png",
    "ticket do dormitório": "TIcket.png",
    "polidor de itens": "Polidor.png",
    "polidor": "Polidor.png",

    # Equipamentos com arte própria
    "machado": "Lucy O Machado.png",
    "lucy o machado": "Lucy O Machado.png",
    "estilingue": "Estilingue.png",
    "pedra preciosa multicor": "Gema.png",
    "gema": "Gema.png",
    "flauta de pa": "Flauta.png",
    "flauta de pã": "Flauta.png",
    "flauta": "Flauta.png",
    "faca de confronto": "Faca.png",
    "faca": "Faca.png",
    "vandal": "Vandal.png",
    "rocha de radianita": "Radianita.png",
    "radianita": "Radianita.png",
    "bracelete de comando": "Bracelete.png",
    "bracelete": "Bracelete.png",
    "katana": "Katana.png",
    "amplificador de alcance": "Megafone.png",
    "megafone": "Megafone.png",
    "ferramenta amaldicoada": "Ferramenta Amaldicoada.png",
    "ferramenta amaldiçoada": "Ferramenta Amaldicoada.png",
    "amuleto das dez sombras": "Amuleto Sombrio.png",
    "amuleto das sombras": "Amuleto Sombrio.png",
    "amuleto sombrio": "Amuleto Sombrio.png",

    # Cartão do Clube / Member Card
    "member card": "MemberCard.png",
    "membercard": "MemberCard.png",
    "cartao do clube": "MemberCard.png",
    "cartão do clube": "MemberCard.png",
    "cartao de membro": "MemberCard.png",
    "cartão de membro": "MemberCard.png",
    "cartao": "MemberCard.png",
    "cartão": "MemberCard.png",
}

ARTES_OFICIAIS_INVENTARIO = {
    "Pocao Cura.png",
    "Pocao Recuperacao.png",
    "Pocao Mana.png",
    "Cha.png",
    "Cafe.png",
    "Marmita.png",
    "Sucata.png",
    "TIcket.png",
    "Ticket.png",
    "MemberCard.png",
    "Polidor.png",
    "Lucy O Machado.png",
    "Estilingue.png",
    "Gema.png",
    "Flauta.png",
    "Faca.png",
    "Vandal.png",
    "Radianita.png",
    "Bracelete.png",
    "Katana.png",
    "Megafone.png",
    "Ferramenta Amaldicoada.png",
    "Amuleto Sombrio.png",
}

_ARTES_OFICIAIS_LOWER = {a.lower() for a in ARTES_OFICIAIS_INVENTARIO}

def eh_arte_placeholder(item_ou_arquivo) -> bool:
    """Verifica se o item está usando arte provisória (placeholder) em vez de arte final."""
    if not item_ou_arquivo:
        return True
    nome_arquivo = item_ou_arquivo
    if hasattr(item_ou_arquivo, "arquivo_imagem") and item_ou_arquivo.arquivo_imagem:
        nome_arquivo = item_ou_arquivo.arquivo_imagem
    elif hasattr(item_ou_arquivo, "nome"):
        nome_arquivo = obter_arquivo_imagem_item(item_ou_arquivo)
    elif isinstance(item_ou_arquivo, dict):
        nome_arquivo = item_ou_arquivo.get("arquivo_imagem") or obter_arquivo_imagem_item(item_ou_arquivo)
    elif isinstance(item_ou_arquivo, str) and not item_ou_arquivo.lower().endswith(".png"):
        nome_arquivo = obter_arquivo_imagem_item(item_ou_arquivo)
    else:
        nome_arquivo = item_ou_arquivo

    nome_base = os.path.basename(str(nome_arquivo))
    if "placeholder" in nome_base.lower():
        return True
    return nome_base not in ARTES_OFICIAIS_INVENTARIO and nome_base.lower() not in _ARTES_OFICIAIS_LOWER

def obter_arquivo_imagem_item(item_ou_nome) -> str:
    """Resolve o arquivo de imagem adequado para um item ou retorna o placeholder correspondente."""
    if not item_ou_nome:
        return "Placeholder.png"

    if hasattr(item_ou_nome, "arquivo_imagem") and item_ou_nome.arquivo_imagem:
        return str(item_ou_nome.arquivo_imagem)

    if isinstance(item_ou_nome, dict) and item_ou_nome.get("arquivo_imagem"):
        return str(item_ou_nome["arquivo_imagem"])

    nome_str = getattr(item_ou_nome, "nome", None)
    if nome_str is None:
        if isinstance(item_ou_nome, dict):
            nome_str = item_ou_nome.get("nome", item_ou_nome.get("id", ""))
        else:
            nome_str = str(item_ou_nome)

    nome_norm = str(nome_str).strip().lower()

    if nome_norm in MAPA_SPRITES_ITENS:
        return MAPA_SPRITES_ITENS[nome_norm]

    dados = carregar_dados_itens()
    if isinstance(dados, dict):
        for it in obter_todos_itens_catalogo():
            if it.get("nome", "").lower() == nome_norm or it.get("id", "").lower() == nome_norm:
                if it.get("arquivo_imagem"):
                    return it["arquivo_imagem"]

    categoria = getattr(item_ou_nome, "categoria", None)
    if not categoria and isinstance(item_ou_nome, dict):
        categoria = item_ou_nome.get("categoria")

    if categoria == "arma":
        return "Placeholder_Arma.png"
    elif categoria in ("capacete", "peitoral", "calca", "bota"):
        return "Placeholder_Armadura.png"
    elif categoria == "amuleto":
        return "Placeholder_Acessorio.png"

    return "Placeholder.png"

_CACHE_SPRITES_ITENS = {}

def limpar_cache_sprites_itens():
    global _CACHE_SPRITES_ITENS
    _CACHE_SPRITES_ITENS.clear()

def carregar_sprite_item(item_ou_nome, tamanho=(32, 32)):
    """Carrega, redimensiona e armazena em cache o sprite de um item ou seu respectivo placeholder."""
    global _CACHE_SPRITES_ITENS
    nome_arquivo = obter_arquivo_imagem_item(item_ou_nome)
    tamanho_tupla = (int(tamanho[0]), int(tamanho[1]))
    chave = (str(nome_arquivo).lower(), tamanho_tupla)
    if chave in _CACHE_SPRITES_ITENS:
        return _CACHE_SPRITES_ITENS[chave]

    from Sistemas.Recursos import caminho_imagem, caminho_item
    import pygame

    caminho = caminho_item(nome_arquivo)
    surf_orig = None
    if caminho and os.path.exists(caminho) and os.path.isfile(caminho):
        try:
            surf_orig = pygame.image.load(caminho).convert_alpha()
        except Exception:
            surf_orig = None

    if surf_orig is None:
        caminho_ph = caminho_imagem("Placeholder.png")
        if caminho_ph and os.path.exists(caminho_ph):
            try:
                surf_orig = pygame.image.load(caminho_ph).convert_alpha()
            except Exception:
                surf_orig = None

    if surf_orig is None:
        surf_orig = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.rect(surf_orig, (35, 42, 58, 230), (2, 2, 28, 28), border_radius=4)
        pygame.draw.rect(surf_orig, (75, 95, 130), (2, 2, 28, 28), width=2, border_radius=4)

    w_orig, h_orig = surf_orig.get_size()
    alvo_w, alvo_h = tamanho_tupla
    fator = min(alvo_w / max(1, w_orig), alvo_h / max(1, h_orig))
    novo_w = max(1, int(w_orig * fator))
    novo_h = max(1, int(h_orig * fator))

    surf_escalada = pygame.transform.scale(surf_orig, (novo_w, novo_h))

    surf_final = pygame.Surface(tamanho_tupla, pygame.SRCALPHA)
    pos_x = (alvo_w - novo_w) // 2
    pos_y = (alvo_h - novo_h) // 2
    surf_final.blit(surf_escalada, (pos_x, pos_y))

    _CACHE_SPRITES_ITENS[chave] = surf_final
    return surf_final

def obter_catalogo_equipamentos():
    dados = carregar_dados_itens()
    if isinstance(dados, dict) and "equipamentos" in dados and dados["equipamentos"]:
        return [
            {
                "nome": eq["nome"],
                "categoria": eq.get("categoria", "arma"),
                "atributos_bonus": dict(eq.get("atributos_bonus", {})),
                "descricao": eq.get("descricao", ""),
                "id": eq.get("id", ""),
                "raridade": eq.get("raridade", "comum"),
                "preco_compra": eq.get("preco_compra", 2),
                "preco_venda": eq.get("preco_venda", 1),
                "arquivo_imagem": eq.get("arquivo_imagem", ""),
            }
            for eq in dados["equipamentos"]
        ]
    return list(_CATALOGO_EQUIPAMENTOS_PADRAO)

CATALOGO_EQUIPAMENTOS = obter_catalogo_equipamentos()

def obter_todos_itens_catalogo():
    dados = carregar_dados_itens()
    if isinstance(dados, dict):
        todos = []
        for chave in ("consumiveis", "materiais", "especiais", "equipamentos"):
            lista = dados.get(chave)
            if isinstance(lista, list):
                todos.extend(lista)
        if todos:
            return todos
        for v in dados.values():
            if isinstance(v, list):
                todos.extend(v)
        return todos
    elif isinstance(dados, list):
        return list(dados)
    return []

def obter_item_por_id_ou_nome(identificador):
    if not identificador:
        return None
    id_alvo = str(identificador).strip().lower()
    for item in obter_todos_itens_catalogo():
        if item.get("id", "").lower() == id_alvo or item.get("nome", "").lower() == id_alvo:
            return dict(item)
    return None


def _normalizar_categoria(categoria, nome=""):
    if categoria:
        c = str(categoria).strip().lower()
        mapa = {
            "arma": "arma",
            "equipamento": "arma",
            "capacete": "capacete",
            "elmo": "capacete",
            "capuz": "capacete",
            "peitoral": "peitoral",
            "colete": "peitoral",
            "manto": "peitoral",
            "armadura": "peitoral",
            "calca": "calca",
            "calça": "calca",
            "calcas": "calca",
            "calças": "calca",
            "bota": "bota",
            "botas": "bota",
            "amuleto": "amuleto",
            "amuletos": "amuleto",
        }
        if c in mapa:
            return mapa[c]

    nome_low = str(nome or "").strip().lower()
    if any(p in nome_low for p in ("capacete", "elmo", "capuz")):
        return "capacete"
    if any(p in nome_low for p in ("peitoral", "colete", "manto", "armadura")):
        return "peitoral"
    if any(p in nome_low for p in ("calça", "calca")):
        return "calca"
    if any(p in nome_low for p in ("bota", "botas")):
        return "bota"
    if "amuleto" in nome_low:
        return "amuleto"
    return "arma"


class ItemPolidor:
    def __init__(self, quantidade=0, arquivo_imagem="Polidor.png"):
        self.nome = "Polidor de Itens"
        self.descricao = "Dobra permanentemente os bônus do equipamento."
        self.quantidade = quantidade
        self.tipo = "polidor"
        self.arquivo_imagem = arquivo_imagem

    def usar(self, alvo=None):
        if self.quantidade <= 0:
            return False
        equipamento_alvo = None
        if isinstance(alvo, Equipamento):
            equipamento_alvo = alvo
        elif alvo is not None and hasattr(alvo, "obter_equipamento_alvo"):
            equipamento_alvo = alvo.obter_equipamento_alvo()
        elif alvo is not None and hasattr(alvo, "equipamento_slot") and alvo.equipamento_slot is not None:
            equipamento_alvo = alvo.equipamento_slot
        else:
            equipamento_alvo = inventario_global.obter_equipamento_alvo()

        if equipamento_alvo is not None:
            equipamento_alvo.polir()
            self.quantidade -= 1
            return True
        return False


class Equipamento:
    def __init__(self, nome, atributos_bonus, categoria=None, descricao=None, arquivo_imagem=None):
        self.nome = nome
        self.atributos_bonus = dict(atributos_bonus)
        self.nivel = 1
        self.polido = False
        self.fator_polimento = 1
        self.categoria = _normalizar_categoria(categoria, nome)
        self.tipo = "equipamento"
        self.quantidade = 1
        self._descricao_custom = descricao
        self.arquivo_imagem = arquivo_imagem or obter_arquivo_imagem_item(self)

    @property
    def descricao(self):
        if self._descricao_custom:
            return self._descricao_custom
        bonus_str = ", ".join(f"+{v} {k}" for k, v in self.atributos_bonus.items() if v > 0)
        cat_legivel = {
            "arma": "Arma",
            "capacete": "Capacete",
            "peitoral": "Peitoral",
            "calca": "Calça",
            "bota": "Bota",
            "amuleto": "Amuleto",
        }.get(self.categoria, "Equipamento")
        return f"{cat_legivel} ({bonus_str})" if bonus_str else cat_legivel

    @descricao.setter
    def descricao(self, valor):
        self._descricao_custom = valor

    def melhorar(self):
        self.nivel += 1
        for k in self.atributos_bonus:
            if self.atributos_bonus[k] > 0:
                self.atributos_bonus[k] += 1 * self.fator_polimento

    def polir(self):
        self.polido = True
        self.fator_polimento *= 2
        for k in self.atributos_bonus:
            if self.atributos_bonus[k] > 0:
                self.atributos_bonus[k] *= 2
        return True

    def usar(self, alvo=None):
        return inventario_global.equipar(self, jogador=alvo)


class _SlotsEquipamentoJogador:
    """Armazena os slots de equipamentos vestidos por um jogador adicional."""

    def __init__(self, jogador=None):
        self.jogador = jogador
        self.equipamento_slot = None
        self.capacete_slot = None
        self.peitoral_slot = None
        self.calca_slot = None
        self.bota_slot = None
        self.amuletos_slots = []
        self.equipamento_selecionado = None


class SistemaInventario:
    MAX_AMULETOS = 3

    def __init__(self):
        self.consumiveis = []
        self.materiais = []
        self.equipamento_slot = None
        self.capacete_slot = None
        self.peitoral_slot = None
        self.calca_slot = None
        self.bota_slot = None
        self.amuletos_slots = []
        self.equipamentos_inventario = []
        self.equipamento_selecionado = None
        self._slots_extras = {}
        self.item_bilhete = ItemBilhete(quantidade=1)
        self.item_polidor = ItemPolidor(quantidade=0)

    def _eh_jogador_principal(self, jogador):
        if jogador is None:
            return True
        padrao = _obter_personagem_padrao()
        return padrao is not None and jogador is padrao

    def _obter_registro(self, jogador=None, criar=True):
        if self._eh_jogador_principal(jogador):
            return self
        chave = id(jogador)
        reg = self._slots_extras.get(chave)
        if reg is None and criar:
            reg = _SlotsEquipamentoJogador(jogador)
            self._slots_extras[chave] = reg
        return reg

    def _todos_registros(self):
        return [self] + list(self._slots_extras.values())

    def definir_equipamento_selecionado(self, equipamento, jogador=None):
        reg = self._obter_registro(jogador)
        reg.equipamento_selecionado = equipamento

    def obter_dono_equipamento(self, equipamento):
        if equipamento is None:
            return None
        for reg in self._todos_registros():
            slots_normais = (
                reg.equipamento_slot,
                reg.capacete_slot,
                reg.peitoral_slot,
                reg.calca_slot,
                reg.bota_slot,
            )
            if any(eq is equipamento for eq in slots_normais) or any(am is equipamento for am in reg.amuletos_slots):
                return _obter_personagem_padrao() if reg is self else reg.jogador
        return None

    @property
    def capacete(self):
        return self.capacete_slot

    @capacete.setter
    def capacete(self, valor):
        self.capacete_slot = valor

    @property
    def peitoral(self):
        return self.peitoral_slot

    @peitoral.setter
    def peitoral(self, valor):
        self.peitoral_slot = valor

    @property
    def calca(self):
        return self.calca_slot

    @calca.setter
    def calca(self, valor):
        self.calca_slot = valor

    @property
    def bota(self):
        return self.bota_slot

    @bota.setter
    def bota(self, valor):
        self.bota_slot = valor

    @property
    def amuletos(self):
        return self.amuletos_slots

    @amuletos.setter
    def amuletos(self, valor):
        self.amuletos_slots = list(valor) if valor is not None else []

    @property
    def bilhetes_dormitorio(self):
        return self.item_bilhete.quantidade

    @bilhetes_dormitorio.setter
    def bilhetes_dormitorio(self, valor):
        self.item_bilhete.quantidade = max(0, int(valor))

    def obter_bilhetes_dormitorio(self):
        return self.item_bilhete.quantidade

    def adicionar_bilhete_dormitorio(self, quantidade=1):
        self.item_bilhete.quantidade += max(0, int(quantidade))

    def consumir_bilhete_dormitorio(self, quantidade=1):
        qtd = max(0, int(quantidade))
        if self.item_bilhete.quantidade >= qtd and qtd > 0:
            self.item_bilhete.quantidade -= qtd
            return True
        return False

    @property
    def polidores_itens(self):
        return self.item_polidor.quantidade

    @polidores_itens.setter
    def polidores_itens(self, valor):
        self.item_polidor.quantidade = max(0, int(valor))

    @property
    def polidores(self):
        return self.item_polidor.quantidade

    @polidores.setter
    def polidores(self, valor):
        self.item_polidor.quantidade = max(0, int(valor))

    def obter_polidores_itens(self):
        return self.item_polidor.quantidade

    def adicionar_polidor_itens(self, quantidade=1):
        self.item_polidor.quantidade += max(0, int(quantidade))

    def consumir_polidor_itens(self, quantidade=1):
        qtd = max(0, int(quantidade))
        if self.item_polidor.quantidade >= qtd and qtd > 0:
            self.item_polidor.quantidade -= qtd
            return True
        return False

    def obter_equipamento_alvo(self, jogador=None):
        reg = self._obter_registro(jogador, criar=False)
        if reg is None:
            return None
        equipados = self.todos_equipamentos_equipados(jogador=jogador)
        if reg.equipamento_selecionado is not None and reg.equipamento_selecionado in equipados:
            return reg.equipamento_selecionado
        if reg.equipamento_slot is not None:
            return reg.equipamento_slot
        if equipados:
            return equipados[0]
        return None

    def usar_polidor_itens(self, equipamento=None, jogador=None):
        alvo = equipamento if equipamento is not None else self.obter_equipamento_alvo(jogador=jogador)
        if alvo is None or self.item_polidor.quantidade <= 0:
            return False
        return self.item_polidor.usar(alvo)

    def usar_polidor(self, equipamento=None, jogador=None):
        return self.usar_polidor_itens(equipamento, jogador=jogador)

    def adicionar_consumivel(self, nome, descricao, rec_hp, rec_mp):
        for c in self.consumiveis:
            if c.nome == nome:
                c.quantidade += 1
                return
        self.consumiveis.append(Consumivel(nome, descricao, rec_hp, rec_mp))

    def adicionar_material(self, nome, descricao):
        for m in self.materiais:
            if m.nome == nome:
                m.quantidade += 1
                return
        self.materiais.append(Material(nome, descricao))

    def pode_equipar(self, equipamento, substituir=True, jogador=None):
        if not isinstance(equipamento, Equipamento):
            return False
        reg = self._obter_registro(jogador)
        cat = getattr(equipamento, "categoria", "arma")
        if cat == "amuleto":
            if any(a.nome == equipamento.nome for a in reg.amuletos_slots):
                return False
            if len(reg.amuletos_slots) >= self.MAX_AMULETOS:
                return False
            return True
        if not substituir:
            mapa_slot = {
                "arma": reg.equipamento_slot,
                "capacete": reg.capacete_slot,
                "peitoral": reg.peitoral_slot,
                "calca": reg.calca_slot,
                "bota": reg.bota_slot,
            }
            return mapa_slot.get(cat) is None
        return True

    _MAPA_ATRIBUTO_SLOT = {
        "arma": "equipamento_slot",
        "capacete": "capacete_slot",
        "peitoral": "peitoral_slot",
        "calca": "calca_slot",
        "bota": "bota_slot",
    }

    def equipar(self, equipamento, jogador=None):
        if equipamento is None:
            return False
        from Sistemas.Conquistas import sistema_conquistas
        reg = self._obter_registro(jogador)
        cat = getattr(equipamento, "categoria", "arma")

        dono_anterior = self.obter_dono_equipamento(equipamento)
        if dono_anterior is not None and self._obter_registro(dono_anterior, criar=False) is not reg:
            self.desequipar(equipamento, jogador=dono_anterior)

        if cat == "amuleto":
            if any(a.nome == equipamento.nome for a in reg.amuletos_slots):
                return False
            if len(reg.amuletos_slots) >= self.MAX_AMULETOS:
                return False
            if equipamento in self.equipamentos_inventario:
                self.equipamentos_inventario.remove(equipamento)
            reg.amuletos_slots.append(equipamento)
            reg.equipamento_selecionado = equipamento
            sistema_conquistas.desbloquear('moda_em_primeiro_lugar')
            return True

        attr_slot = self._MAPA_ATRIBUTO_SLOT.get(cat, "equipamento_slot")
        atual = getattr(reg, attr_slot)
        if atual is equipamento:
            reg.equipamento_selecionado = equipamento
            return True

        indice_origem = None
        if equipamento in self.equipamentos_inventario:
            indice_origem = self.equipamentos_inventario.index(equipamento)

        if atual is not None and atual not in self.equipamentos_inventario:
            if indice_origem is not None:
                self.equipamentos_inventario[indice_origem] = atual
            else:
                self.equipamentos_inventario.append(atual)
        elif indice_origem is not None:
            self.equipamentos_inventario.pop(indice_origem)

        setattr(reg, attr_slot, equipamento)
        reg.equipamento_selecionado = equipamento
        sistema_conquistas.desbloquear('moda_em_primeiro_lugar')
        return True

    def _desequipar_no_registro(self, reg, equipamento_ou_categoria):
        alvo = None
        if isinstance(equipamento_ou_categoria, Equipamento):
            alvo = equipamento_ou_categoria
            if alvo is reg.equipamento_slot:
                reg.equipamento_slot = None
            elif alvo is reg.capacete_slot:
                reg.capacete_slot = None
            elif alvo is reg.peitoral_slot:
                reg.peitoral_slot = None
            elif alvo is reg.calca_slot:
                reg.calca_slot = None
            elif alvo is reg.bota_slot:
                reg.bota_slot = None
            elif alvo in reg.amuletos_slots:
                reg.amuletos_slots.remove(alvo)
            else:
                return None
        elif isinstance(equipamento_ou_categoria, str):
            cat = _normalizar_categoria(equipamento_ou_categoria)
            if cat == "capacete" and reg.capacete_slot:
                alvo, reg.capacete_slot = reg.capacete_slot, None
            elif cat == "peitoral" and reg.peitoral_slot:
                alvo, reg.peitoral_slot = reg.peitoral_slot, None
            elif cat == "calca" and reg.calca_slot:
                alvo, reg.calca_slot = reg.calca_slot, None
            elif cat == "bota" and reg.bota_slot:
                alvo, reg.bota_slot = reg.bota_slot, None
            elif cat == "amuleto" and reg.amuletos_slots:
                alvo = reg.amuletos_slots.pop(0)
            elif cat == "arma" and reg.equipamento_slot:
                alvo, reg.equipamento_slot = reg.equipamento_slot, None
        return alvo

    def desequipar(self, equipamento_ou_categoria, jogador=None):
        alvo = None
        reg_alvo = None
        if jogador is not None:
            reg = self._obter_registro(jogador, criar=False)
            if reg is not None:
                alvo = self._desequipar_no_registro(reg, equipamento_ou_categoria)
                reg_alvo = reg
        else:
            for reg in self._todos_registros():
                alvo = self._desequipar_no_registro(reg, equipamento_ou_categoria)
                if alvo is not None:
                    reg_alvo = reg
                    break

        if alvo is not None:
            if alvo not in self.equipamentos_inventario:
                self.equipamentos_inventario.append(alvo)
            if reg_alvo is not None and reg_alvo.equipamento_selecionado is alvo:
                dono_reg = None if reg_alvo is self else reg_alvo.jogador
                reg_alvo.equipamento_selecionado = self.obter_equipamento_alvo(jogador=dono_reg)
            return True
        return False

    def adicionar_equipamento(self, equipamento, auto_equipar=True, jogador=None):
        if not isinstance(equipamento, Equipamento):
            return None
        if auto_equipar and self.pode_equipar(equipamento, substituir=False, jogador=jogador):
            self.equipar(equipamento, jogador=jogador)
        else:
            if equipamento not in self.equipamentos_inventario:
                self.equipamentos_inventario.append(equipamento)
        return equipamento

    def gerar_equipamento_aleatorio(self, categoria=None):
        import random
        opcoes = CATALOGO_EQUIPAMENTOS
        if categoria:
            cat_norm = _normalizar_categoria(categoria)
            filtradas = [item for item in CATALOGO_EQUIPAMENTOS if item["categoria"] == cat_norm]
            if filtradas:
                opcoes = filtradas

        nomes_amuletos_equipados = {a.nome for a in self.amuletos_slots}
        opcoes_preferenciais = [
            item for item in opcoes
            if not (item["categoria"] == "amuleto" and item["nome"] in nomes_amuletos_equipados)
        ]
        escolha = random.choice(opcoes_preferenciais if opcoes_preferenciais else opcoes)
        return Equipamento(escolha["nome"], dict(escolha["atributos_bonus"]), categoria=escolha["categoria"], arquivo_imagem=escolha.get("arquivo_imagem"))

    def custo_compra_equipamento(self):
        custo = 2
        if getattr(_obter_personagem_padrao(), "tem_talento", lambda t: False)("S2"):
            custo = max(1, custo // 2)
        return custo

    def adicionar_sucata(self, quantidade=1):
        for _ in range(max(0, int(quantidade))):
            self.adicionar_material("Sucata", "Material para melhorar equipamentos.")

    def comprar_equipamento_loja(self, categoria=None, custo=None, jogador=None):
        custo_final = self.custo_compra_equipamento() if custo is None else max(0, int(custo))
        if self.materiais_totais() < custo_final:
            return None
        if custo_final > 0:
            self.consumir_materiais(custo_final)
        novo_eq = self.gerar_equipamento_aleatorio(categoria=categoria)
        self.adicionar_equipamento(novo_eq, auto_equipar=True, jogador=jogador)
        return novo_eq

    def obter_slots_equipamento(self, jogador=None):
        reg = self._obter_registro(jogador, criar=False)
        if reg is None:
            return [
                ("ARMA", None), ("CAP", None), ("PEIT", None), ("CALÇ", None), ("BOTA", None),
                ("AMU1", None), ("AMU2", None), ("AMU3", None),
            ]
        return [
            ("ARMA", reg.equipamento_slot),
            ("CAP", reg.capacete_slot),
            ("PEIT", reg.peitoral_slot),
            ("CALÇ", reg.calca_slot),
            ("BOTA", reg.bota_slot),
            ("AMU1", reg.amuletos_slots[0] if len(reg.amuletos_slots) > 0 else None),
            ("AMU2", reg.amuletos_slots[1] if len(reg.amuletos_slots) > 1 else None),
            ("AMU3", reg.amuletos_slots[2] if len(reg.amuletos_slots) > 2 else None),
        ]

    def todos_equipamentos_equipados(self, jogador=None, incluir_todos=False):
        equips = []
        registros = self._todos_registros() if incluir_todos else [self._obter_registro(jogador, criar=False)]
        for reg in registros:
            if reg is None:
                continue
            for eq in (reg.equipamento_slot, reg.capacete_slot, reg.peitoral_slot, reg.calca_slot, reg.bota_slot):
                if eq is not None:
                    equips.append(eq)
            for am in reg.amuletos_slots:
                if am is not None:
                    equips.append(am)
        return equips

    def obter_bonus_atributo(self, atributo, jogador=None):
        total = 0
        for eq in self.todos_equipamentos_equipados(jogador=jogador):
            total += int(eq.atributos_bonus.get(atributo, 0))
        return total

    def obter_todos_bonus_atributos(self, jogador=None):
        totais = {"For": 0, "Agi": 0, "Con": 0, "Sab": 0, "Int": 0, "Sor": 0}
        for eq in self.todos_equipamentos_equipados(jogador=jogador):
            for k, v in eq.atributos_bonus.items():
                totais[k] = totais.get(k, 0) + int(v)
        return totais

    def obter_bonus_defesa(self, jogador=None):
        """Retorna o bônus total de armadura e defesa plana concedido pelos equipamentos equipados."""
        total = 0
        for eq in self.todos_equipamentos_equipados(jogador=jogador):
            total += int(eq.atributos_bonus.get("Def", 0))
            total += int(eq.atributos_bonus.get("Armadura", 0))
            total += int(eq.atributos_bonus.get("Defesa", 0))
        return total

    def limpar_equipamentos(self, jogador=None):
        """Desequipa todos os itens de todos os slots de equipamento (ou apenas do jogador informado)."""
        registros = self._todos_registros() if jogador is None else [self._obter_registro(jogador, criar=False)]
        for reg in registros:
            if reg is None:
                continue
            reg.equipamento_slot = None
            reg.capacete_slot = None
            reg.peitoral_slot = None
            reg.calca_slot = None
            reg.bota_slot = None
            reg.amuletos_slots = []
            reg.equipamento_selecionado = None
        if jogador is None:
            self._slots_extras.clear()

    def adicionar_item_por_id(self, item_id, quantidade=1):
        item = obter_item_por_id_ou_nome(item_id)
        if not item:
            return False
        tipo = item.get("tipo", "")
        nome = item.get("nome", "")
        desc = item.get("descricao", "")
        qtd = max(1, int(quantidade))
        if tipo == "consumivel":
            for _ in range(qtd):
                self.adicionar_consumivel(nome, desc, item.get("rec_hp", 0), item.get("rec_mp", 0))
            return True
        elif tipo == "material":
            for _ in range(qtd):
                self.adicionar_material(nome, desc)
            return True
        elif tipo == "bilhete":
            self.adicionar_bilhete_dormitorio(qtd)
            return True
        elif tipo == "polidor":
            self.adicionar_polidor_itens(qtd)
            return True
        elif tipo == "equipamento":
            for _ in range(qtd):
                eq = Equipamento(nome, item.get("atributos_bonus", {}), categoria=item.get("categoria", "arma"), descricao=desc)
                self.adicionar_equipamento(eq, auto_equipar=False)
            return True
        return False

    def resetar(self):
        self.consumiveis.clear()
        self.materiais.clear()
        self.limpar_equipamentos()
        self.equipamentos_inventario.clear()
        self.item_bilhete = ItemBilhete(quantidade=1)
        self.item_polidor = ItemPolidor(quantidade=0)

    def itens_do_inventario(self):
        itens = list(self.consumiveis) + list(self.materiais)
        if self.item_bilhete.quantidade > 0:
            itens.append(self.item_bilhete)
        if self.item_polidor.quantidade > 0:
            itens.append(self.item_polidor)
        itens.extend(self.equipamentos_inventario)
        return itens

    def custo_melhoria(self, equipamento=None, jogador=None):
        alvo = equipamento if equipamento is not None else self.obter_equipamento_alvo(jogador=jogador)
        if not alvo:
            return 0
        custo = alvo.nivel * 2
        alvo_jogador = jogador if jogador is not None else _obter_personagem_padrao()
        if getattr(alvo_jogador, "tem_talento", lambda t: False)("S2"):
            custo = max(1, custo // 2)
        return custo

    def materiais_totais(self):
        return sum(m.quantidade for m in self.materiais)

    def consumir_materiais(self, quantidade):
        gastos = 0
        for m in self.materiais:
            while m.quantidade > 0 and gastos < quantidade:
                m.quantidade -= 1
                gastos += 1
        self.materiais = [m for m in self.materiais if m.quantidade > 0]

inventario_global = SistemaInventario()






