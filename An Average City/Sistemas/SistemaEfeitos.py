"""
Sistema de Gerenciamento e Exibição de Efeitos (Buffs e Debuffs)
Exibe ícones discretos próximos à barra de vida de Personagens, Minions e Inimigos,
com tooltips informativos ao passar o mouse por cima.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pygame

from .Recursos import DIRETORIO_PROJETO
from .Fontes import obter_fonte

# Diretório dos ícones de buffs e debuffs
DIR_DE_BUFFS = Path(DIRETORIO_PROJETO) / "Sprites" / "De_Buffs"

# Mapeamento canônico de configurações e descrições dos efeitos
CONFIG_EFEITOS: Dict[str, Dict[str, Any]] = {
    "congelado": {
        "id": "congelado",
        "nome": "Congelado",
        "tipo": "debuff",
        "arquivo": "Congelado.png",
        "cor": (80, 190, 255),
        "tag": "DEBUFF",
        "descricao": "Paralisado pelo gelo extremo! Incapacitado de se mover ou agir nesta rodada.",
    },
    "atordoado": {
        "id": "atordoado",
        "nome": "Atordoado",
        "tipo": "debuff",
        "arquivo": "Atordoado.png",
        "cor": (255, 210, 60),
        "tag": "DEBUFF",
        "descricao": "Tonto e atordoado! Incapaz de realizar ações ou atacar neste turno.",
    },
    "eletrocutar": {
        "id": "eletrocutar",
        "nome": "Eletrocutado",
        "tipo": "debuff",
        "arquivo": "Choque.png",
        "cor": (255, 235, 60),
        "tag": "DEBUFF",
        "descricao": "Eletrocutado! Atordoado no primeiro turno e sofre dano elétrico contínuo durante 2 rodadas.",
    },
    "eletrocutado": {
        "id": "eletrocutar",
        "nome": "Eletrocutado",
        "tipo": "debuff",
        "arquivo": "Choque.png",
        "cor": (255, 235, 60),
        "tag": "DEBUFF",
        "descricao": "Eletrocutado! Atordoado no primeiro turno e sofre dano elétrico contínuo durante 2 rodadas.",
    },
    "choque": {
        "id": "eletrocutar",
        "nome": "Eletrocutado",
        "tipo": "debuff",
        "arquivo": "Choque.png",
        "cor": (255, 235, 60),
        "tag": "DEBUFF",
        "descricao": "Eletrocutado! Atordoado no primeiro turno e sofre dano elétrico contínuo durante 2 rodadas.",
    },
    "fogo": {
        "id": "fogo",
        "nome": "Queimando",
        "tipo": "debuff",
        "arquivo": "Fogo.png",
        "cor": (255, 95, 45),
        "tag": "DEBUFF",
        "descricao": "Em chamas! Sofre dano de fogo contínuo a cada rodada de combate.",
    },
    "veneno": {
        "id": "veneno",
        "nome": "Envenenado",
        "tipo": "debuff",
        "arquivo": "Veneno.png",
        "cor": (130, 240, 80),
        "tag": "DEBUFF",
        "descricao": "Toxina mortal! Perde pontos de vida gradualmente ao final de cada rodada.",
    },
    "cegueira": {
        "id": "cegueira",
        "nome": "Cegueira",
        "tipo": "debuff",
        "arquivo": "Cego.png",
        "cor": (175, 175, 195),
        "tag": "DEBUFF",
        "descricao": "Visão ofuscada e turva! A chance de falhar ou errar ataques aumenta em +20%.",
    },
    "cego": {
        "id": "cegueira",
        "nome": "Cegueira",
        "tipo": "debuff",
        "arquivo": "Cego.png",
        "cor": (175, 175, 195),
        "tag": "DEBUFF",
        "descricao": "Visão ofuscada e turva! A chance de falhar ou errar ataques aumenta em +20%.",
    },
    "bloqueio": {
        "id": "bloqueio",
        "nome": "Bloqueando",
        "tipo": "buff",
        "arquivo": "Escudo.png",
        "cor": (70, 225, 255),
        "tag": "BUFF",
        "descricao": "Postura defensiva ativa! Todo dano recebido é reduzido em 50%.",
    },
    "vida": {
        "id": "vida",
        "nome": "Vida",
        "tipo": "buff",
        "arquivo": "Vida.png",
        "cor": (40, 210, 80),
        "tag": "RECURSO",
        "descricao": "Pontos de Vida (HP): Vitalidade física do personagem.",
    },
    "mana": {
        "id": "mana",
        "nome": "Mana",
        "tipo": "buff",
        "arquivo": "Mana.png",
        "cor": (30, 150, 255),
        "tag": "RECURSO",
        "descricao": "Pontos de Mana (PM): Energia mágica para conjuração de habilidades e magias.",
    },
    "recuperando": {
        "id": "recuperando",
        "nome": "Foco",
        "tipo": "debuff",
        "arquivo": "Foco.png",
        "cor": (255, 95, 45),
        "tag": "DEBUFF",
        "descricao": "Estado de Foco ativo: Regenera PM na rodada, porém vulnerável (+30% dano sofrido).",
    },
    "foco": {
        "id": "foco",
        "nome": "Foco",
        "tipo": "debuff",
        "arquivo": "Foco.png",
        "cor": (255, 95, 45),
        "tag": "DEBUFF",
        "descricao": "Estado de Foco ativo: Regenera PM na rodada, porém vulnerável (+30% dano sofrido).",
    },
    "god_mode": {
        "id": "god_mode",
        "nome": "Invulnerável",
        "tipo": "buff",
        "arquivo": "Escudo.png",
        "cor": (255, 230, 90),
        "tag": "BUFF",
        "descricao": "Modo Divino ativo: Totalmente imune a qualquer dano e efeitos negativos.",
    },
    "confinamento": {
        "id": "confinamento",
        "nome": "Carga de Contenção",
        "tipo": "buff",
        "arquivo": "Atordoado.png",
        "cor": (255, 175, 50),
        "tag": "ESPECIAL",
        "descricao": "Acumulando energia cinética! Ao atingir 5 cargas, detona um pulso que atordoa todos os oponentes.",
    },
    "santuario": {
        "id": "santuario",
        "nome": "Santuário Ativo",
        "tipo": "buff",
        "arquivo": "Fogo.png",
        "cor": (255, 80, 80),
        "tag": "DOMÍNIO",
        "descricao": "Expansão de Domínio: Dispara tempestades devastadoras de cortes contínuos em área.",
    },
}

# Cache de superfícies carregadas e redimensionadas
_cache_icones: Dict[Tuple[str, int], pygame.Surface] = {}


def carregar_icone_efeito(nome_arquivo_ou_id: str, tamanho: int = 20) -> pygame.Surface:
    """
    Carrega o ícone da pasta Sprites/De_Buffs redimensionado para o tamanho desejado.
    Utiliza cache em memória para máximo desempenho.
    """
    # Descobre o nome do arquivo a partir do ID ou usa o nome direto
    arquivo = nome_arquivo_ou_id
    if nome_arquivo_ou_id in CONFIG_EFEITOS:
        arquivo = CONFIG_EFEITOS[nome_arquivo_ou_id]["arquivo"]

    chave_cache = (arquivo, tamanho)
    if chave_cache in _cache_icones:
        return _cache_icones[chave_cache]

    caminho = DIR_DE_BUFFS / arquivo
    if caminho.exists():
        try:
            img = pygame.image.load(str(caminho))
            if pygame.display.get_surface() is not None:
                img = img.convert_alpha()
            elif img.get_bitsize() < 24:
                img = img.convert(32)
            icone = pygame.transform.smoothscale(img, (tamanho, tamanho))
            _cache_icones[chave_cache] = icone
            return icone
        except Exception as e:
            print(f"[Aviso] Falha ao carregar ícone {arquivo}: {e}")

    # Fallback gráfico estilizado caso o arquivo não seja encontrado
    surf_fallback = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
    pygame.draw.circle(surf_fallback, (40, 50, 70, 220), (tamanho // 2, tamanho // 2), tamanho // 2)
    pygame.draw.circle(surf_fallback, (200, 220, 255, 240), (tamanho // 2, tamanho // 2), tamanho // 2, width=1)
    _cache_icones[chave_cache] = surf_fallback
    return surf_fallback


def entidade_anula_debuff_foco(entidade: Any) -> bool:
    """
    Verifica se a entidade possui o talento F2 (Domínio Simples) da árvore do Feiticeiro,
    que anula os debuffs e a vulnerabilidade de dano extra associados ao Foco.
    """
    if entidade is None:
        return False
    if hasattr(entidade, "tem_talento") and callable(entidade.tem_talento):
        try:
            if bool(entidade.tem_talento("F2")):
                return True
        except Exception:
            pass
    talentos = getattr(entidade, "talentos", None)
    if talentos:
        if isinstance(talentos, dict) and bool(talentos.get("F2")):
            return True
        if isinstance(talentos, (set, list, tuple)) and "F2" in talentos:
            return True
    return False


def obter_icone_recurso_entidade(entidade: Any, tamanho: int = 16) -> Tuple[pygame.Surface, str]:
    """
    Retorna a superfície do ícone e o nome do arquivo para o recurso de Mana/Foco da entidade:
    - Se a entidade possui o talento F2 do Feiticeiro (que anula os debuffs do foco), usa 'Mana.png'.
    - Caso contrário, troca o ícone para 'Foco.png'.
    """
    arquivo = "Mana.png" if entidade_anula_debuff_foco(entidade) else "Foco.png"
    return carregar_icone_efeito(arquivo, tamanho), arquivo


def obter_efeitos_ativos(entidade: Any) -> List[Dict[str, Any]]:
    """
    Varre a entidade (Personagem, Minion ou Inimigo) e retorna uma lista
    com todos os efeitos positivos (buffs) e negativos (debuffs) ativos no momento.
    """
    if not entidade or getattr(entidade, "hp", 0) <= 0:
        return []

    efeitos: List[Dict[str, Any]] = []

    # 1. Congelado
    if getattr(entidade, "congelado", False):
        info = dict(CONFIG_EFEITOS["congelado"])
        efeitos.append(info)

    # 2. Atordoado
    if getattr(entidade, "atordoado", False) and not getattr(entidade, "eletrocutado", False):
        info = dict(CONFIG_EFEITOS["atordoado"])
        efeitos.append(info)

    # 3. Eletrocutado / Choque
    if getattr(entidade, "eletrocutado", False):
        info = dict(CONFIG_EFEITOS["eletrocutar"])
        turnos = getattr(entidade, "turnos_eletrocutado", 0)
        if turnos > 0:
            info["duracao_texto"] = f"Duração: {turnos} rodada{'s' if turnos > 1 else ''}"
        efeitos.append(info)

    # 4. Fogo / Queimando
    if getattr(entidade, "queimando", False):
        info = dict(CONFIG_EFEITOS["fogo"])
        turnos = getattr(entidade, "turnos_fogo", 0)
        if turnos > 0:
            info["duracao_texto"] = f"Duração: {turnos} rodada{'s' if turnos > 1 else ''}"
        efeitos.append(info)

    # 4. Veneno / Envenenado
    if getattr(entidade, "envenenado", False):
        info = dict(CONFIG_EFEITOS["veneno"])
        turnos = getattr(entidade, "turnos_veneno", 0)
        if turnos > 0:
            info["duracao_texto"] = f"Duração: {turnos} rodada{'s' if turnos > 1 else ''}"
        efeitos.append(info)

    # 5. Cegueira / Cego
    if getattr(entidade, "cego", False):
        info = dict(CONFIG_EFEITOS["cegueira"])
        turnos = getattr(entidade, "turnos_cegueira", 0)
        if turnos > 0:
            info["duracao_texto"] = f"Duração: {turnos} rodada{'s' if turnos > 1 else ''}"
        efeitos.append(info)

    # 5. Bloqueio (Buff)
    if getattr(entidade, "bloqueando", False):
        info = dict(CONFIG_EFEITOS["bloqueio"])
        efeitos.append(info)

    # 6. Foco / Recuperando (Alterna entre Buff e Debuff dependendo do talento F2)
    if getattr(entidade, "recuperando", False) or getattr(entidade, "focado", False):
        if entidade_anula_debuff_foco(entidade):
            info = {
                "id": "foco_estavel",
                "nome": "Foco (Domínio Simples)",
                "tipo": "buff",
                "arquivo": "Mana.png",
                "cor": (80, 190, 255),
                "tag": "BUFF",
                "descricao": "Estado de Foco ativo: Regenera PM na rodada sem penalidade de dano (Domínio Simples F2).",
            }
        else:
            info = dict(CONFIG_EFEITOS["recuperando"])
        efeitos.append(info)

    # 7. Modo Deus (Buff)
    if getattr(entidade, "god_mode", False):
        info = dict(CONFIG_EFEITOS["god_mode"])
        efeitos.append(info)

    # 8. Carga de Confinamento (Inimigo especial)
    if getattr(entidade, "eh_confinamento", False):
        cargas = getattr(entidade, "carga_confinamento", 0)
        max_cargas = getattr(entidade, "max_carga_confinamento", 5)
        if cargas > 0:
            info = dict(CONFIG_EFEITOS["confinamento"])
            info["duracao_texto"] = f"Cargas: {cargas}/{max_cargas}"
            info["descricao"] = f"Acumulando energia ({cargas}/{max_cargas} cargas). Ao atingir {max_cargas}, atordoa todos os oponentes."
            efeitos.append(info)

    # 9. Santuário Malevolente ativo
    if getattr(entidade, "is_santuario", False):
        dur = getattr(entidade, "duracao", 4)
        info = dict(CONFIG_EFEITOS["santuario"])
        info["duracao_texto"] = f"Duração restante: {dur} rodada{'s' if dur > 1 else ''}"
        efeitos.append(info)

    # 10. Efeitos customizados no dicionário efeitos_ativos da entidade
    extras = getattr(entidade, "efeitos_ativos", {})
    if isinstance(extras, dict):
        for chave, dados in extras.items():
            if chave not in [e["id"] for e in efeitos]:
                if isinstance(dados, dict):
                    efeitos.append(dados)
                elif chave in CONFIG_EFEITOS:
                    efeitos.append(dict(CONFIG_EFEITOS[chave]))

    return efeitos


def desenhar_icones_entidade(
    surface: pygame.Surface,
    entidade: Any,
    x: int,
    y: int,
    tamanho: int = 18,
    espacamento: int = 4,
    posicao_mouse: Optional[Tuple[int, int]] = None,
    alinhamento: str = "centro",
) -> Optional[Dict[str, Any]]:
    """
    Renderiza os ícones discretos de efeitos próximos à barra de vida.
    Retorna o dicionário de informações do efeito caso o mouse esteja passando por cima (hover).
    """
    efeitos = obter_efeitos_ativos(entidade)
    if not efeitos:
        return None

    total_icones = len(efeitos)
    largura_total = total_icones * tamanho + (total_icones - 1) * espacamento

    if alinhamento == "centro":
        x_inicial = x - (largura_total // 2)
    elif alinhamento == "direita":
        x_inicial = x - largura_total
    else:  # esquerda
        x_inicial = x

    efeito_hovered: Optional[Dict[str, Any]] = None

    for i, info in enumerate(efeitos):
        ix = x_inicial + i * (tamanho + espacamento)
        iy = y

        rect_icone = pygame.Rect(ix, iy, tamanho, tamanho)
        esta_hover = posicao_mouse is not None and rect_icone.collidepoint(posicao_mouse)
        if esta_hover:
            efeito_hovered = info

        # Fundo discreto arredondado tipo "pill"
        cor_tipo = (245, 75, 75) if info.get("tipo") == "debuff" else (55, 220, 165)
        if info.get("tag") == "ESPECIAL":
            cor_tipo = (255, 185, 45)

        # Fundo semi-transparente escuro
        surf_fundo = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
        alfa_bg = 230 if esta_hover else 185
        pygame.draw.rect(surf_fundo, (14, 18, 26, alfa_bg), (0, 0, tamanho, tamanho), border_radius=4)
        surface.blit(surf_fundo, (ix, iy))

        # Ícone centralizado
        icone_surf = carregar_icone_efeito(info["arquivo"], tamanho=tamanho - 2)
        surface.blit(icone_surf, (ix + 1, iy + 1))

        # Borda sutil identificando o tipo (buff/debuff)
        largura_borda = 2 if esta_hover else 1
        pygame.draw.rect(surface, cor_tipo, (ix, iy, tamanho, tamanho), width=largura_borda, border_radius=4)

    return efeito_hovered


def desenhar_tooltip_efeito(
    surface: pygame.Surface,
    info_efeito: Dict[str, Any],
    posicao_mouse: Tuple[int, int],
    fonte_titulo: Optional[pygame.font.Font] = None,
    fonte_texto: Optional[pygame.font.Font] = None,
):
    """
    Desenha uma tooltip elegante, moderna e discreta flutuando ao lado do mouse
    exibindo nome, categoria (Buff/Debuff) e a descrição completa do efeito.
    """
    if not info_efeito or not posicao_mouse:
        return

    f_tit = fonte_titulo or obter_fonte(14)
    f_corpo = fonte_texto or obter_fonte(12)

    nome = info_efeito.get("nome", "Efeito")
    tipo = info_efeito.get("tipo", "debuff").upper()
    tag = info_efeito.get("tag", tipo)
    descricao = info_efeito.get("descricao", "")
    duracao_txt = info_efeito.get("duracao_texto", "")

    cor_accent = (245, 80, 80) if info_efeito.get("tipo") == "debuff" else (60, 235, 175)
    if tag == "ESPECIAL":
        cor_accent = (255, 195, 50)
    elif tag == "DOMÍNIO":
        cor_accent = (255, 70, 70)

    # Renderiza textos
    txt_nome = f_tit.render(nome, True, (255, 255, 255))
    txt_tag = f_corpo.render(f"[{tag}]", True, cor_accent)

    # Quebra a descrição em linhas de até ~36 caracteres
    palavras = descricao.split(" ")
    linhas_desc = []
    linha_atual = ""
    for p in palavras:
        teste = f"{linha_atual} {p}".strip()
        if len(teste) > 36:
            linhas_desc.append(linha_atual)
            linha_atual = p
        else:
            linha_atual = teste
    if linha_atual:
        linhas_desc.append(linha_atual)

    # Calcula dimensões da tooltip
    largura_interna = max(
        txt_nome.get_width() + txt_tag.get_width() + 32,
        max((f_corpo.size(l)[0] for l in linhas_desc), default=120),
    )
    if duracao_txt:
        largura_interna = max(largura_interna, f_corpo.size(duracao_txt)[0])

    largura_box = max(190, largura_interna + 24)
    altura_box = 32 + len(linhas_desc) * 16 + (18 if duracao_txt else 0)

    # Posicionamento inteligente (clamp na tela)
    tela_w, tela_h = surface.get_size()
    tx = posicao_mouse[0] + 16
    ty = posicao_mouse[1] + 16

    if tx + largura_box > tela_w - 8:
        tx = posicao_mouse[0] - largura_box - 12
    if ty + altura_box > tela_h - 8:
        ty = posicao_mouse[1] - altura_box - 8
    tx = max(8, tx)
    ty = max(8, ty)

    # Caixa de fundo com gradiente e borda
    rect_box = pygame.Rect(tx, ty, largura_box, altura_box)
    surf_bg = pygame.Surface((largura_box, altura_box), pygame.SRCALPHA)
    pygame.draw.rect(surf_bg, (18, 22, 32, 245), (0, 0, largura_box, altura_box), border_radius=8)
    surface.blit(surf_bg, (tx, ty))

    # Borda temática
    pygame.draw.rect(surface, cor_accent, rect_box, width=2, border_radius=8)

    # Mini ícone no cabeçalho da tooltip
    mini_icone = carregar_icone_efeito(info_efeito.get("arquivo", ""), tamanho=18)
    surface.blit(mini_icone, (tx + 10, ty + 8))

    # Título e Tag
    surface.blit(txt_nome, (tx + 34, ty + 7))
    surface.blit(txt_tag, (tx + largura_box - txt_tag.get_width() - 10, ty + 8))

    # Linha divisória
    pygame.draw.line(surface, (60, 70, 95), (tx + 8, ty + 28), (tx + largura_box - 8, ty + 28), 1)

    # Texto da descrição
    y_texto = ty + 33
    for l in linhas_desc:
        txt_l = f_corpo.render(l, True, (215, 225, 240))
        surface.blit(txt_l, (tx + 10, y_texto))
        y_texto += 16

    # Duração (se houver)
    if duracao_txt:
        txt_dur = f_corpo.render(duracao_txt, True, (255, 215, 110))
        surface.blit(txt_dur, (tx + 10, y_texto + 2))
