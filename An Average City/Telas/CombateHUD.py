"""
Módulo auxiliar para renderização da HUD, barras de status e efeitos visuais da TelaCombate.
Desacopla a responsabilidade puramente visual da lógica de turnos e combate.
"""

import math
from typing import Optional, List, Tuple, Any, Callable
import pygame
from Sistemas.Fontes import quebrar_texto
from Sistemas.SistemaEfeitos import (
    desenhar_icones_entidade,
    desenhar_tooltip_efeito,
    carregar_icone_efeito,
    entidade_anula_debuff_foco,
    obter_icone_recurso_entidade,
)


def desenhar_sombra_contato(
    tela: pygame.Surface,
    entidade: Any,
    deslocamento_y: float = 0,
    multiplicador_alfa: float = 1.0,
) -> None:
    """Renderiza uma elipse de sombra no chão sob os pés da entidade viva ou em fade de derrota."""
    if not entidade or (getattr(entidade, "hp", 0) <= 0 and getattr(entidade, "timer_fade_derrota", 0) <= 0):
        return
    rect = entidade.rect
    largura_sombra = max(34, int(rect.width * 0.72))
    altura_sombra = 14
    sombra_surf = pygame.Surface((largura_sombra, altura_sombra), pygame.SRCALPHA)
    alfa_sombra = int(115 * max(0.0, min(1.0, multiplicador_alfa)))
    pygame.draw.ellipse(sombra_surf, (0, 0, 0, alfa_sombra), (0, 0, largura_sombra, altura_sombra))
    x_sombra = rect.centerx - (largura_sombra // 2)
    y_sombra = rect.bottom - 7 + int(deslocamento_y)
    tela.blit(sombra_surf, (x_sombra, y_sombra))


def desenhar_barras_status(
    tela: pygame.Surface,
    entidade: Any,
    fonte_inimigo: pygame.font.Font,
    eh_minion_func: Callable[[Any], bool],
    deslocamento_flutuacao: float = 0,
    posicao_mouse: Optional[Tuple[int, int]] = None,
) -> Optional[Any]:
    """
    Renderiza a placa suspensa com nome, HP, MP e ícones de efeitos de status de inimigos/aliados.
    Retorna o efeito hovered se o mouse estiver sobre algum ícone.
    """
    if getattr(entidade, "is_player", False):
        return None

    rect = entidade.rect
    eh_aliado = eh_minion_func(entidade)
    eh_santuario = getattr(entidade, "is_santuario", False)
    classe_tag = f" [{entidade.classe}]" if getattr(entidade, "classe", None) else ""

    if eh_santuario:
        dur_txt = getattr(entidade, "duracao", 4)
        nome_texto = f"⛩ {entidade.nome} [Dur: {dur_txt} | {entidade.golpes_restantes()}/4]"
        cor_nome = (255, 110, 110) if getattr(entidade, "lado", "inimigo") == "inimigo" else (170, 255, 235)
    else:
        nome_texto = f"★ {entidade.nome[:16]}" if eh_aliado else f"{entidade.nome[:22]}{classe_tag}"
        if getattr(entidade, "congelado", False):
            nome_texto = f"❄ {nome_texto}"
        if getattr(entidade, "atordoado", False):
            nome_texto = f"💫 {nome_texto}"
        cor_nome = (
            (170, 255, 235)
            if eh_aliado
            else ((255, 215, 90) if getattr(entidade, "tipo", "") == "chefe" else (240, 240, 240))
        )

    txt_nome = fonte_inimigo.render(nome_texto, True, cor_nome)
    largura_placa = max(95, rect.width + 12, txt_nome.get_width() + 16)
    altura_placa = 28 if getattr(entidade, "max_mp", 0) > 0 else 20
    x_placa = rect.centerx - (largura_placa // 2)
    y_placa = rect.top - altura_placa - 14 + int(deslocamento_flutuacao)

    fundo_placa = pygame.Surface((largura_placa, altura_placa), pygame.SRCALPHA)
    cor_borda = (
        (235, 60, 60, 230)
        if eh_santuario
        else (
            (52, 210, 180, 230)
            if eh_aliado
            else ((255, 215, 90, 230) if getattr(entidade, "tipo", "") == "chefe" else (70, 80, 105, 220))
        )
    )
    pygame.draw.rect(fundo_placa, (16, 22, 30, 205), (0, 0, largura_placa, altura_placa), border_radius=6)
    pygame.draw.rect(fundo_placa, cor_borda, (0, 0, largura_placa, altura_placa), width=1, border_radius=6)
    tela.blit(fundo_placa, (x_placa, y_placa))
    tela.blit(txt_nome, (x_placa + (largura_placa - txt_nome.get_width()) // 2, y_placa + 2))

    bar_w = largura_placa - 12
    bar_h = 5
    x_bar = x_placa + 6
    y_bar = y_placa + 16
    pygame.draw.rect(tela, (70, 15, 20), (x_bar, y_bar, bar_w, bar_h), border_radius=2)
    if getattr(entidade, "max_hp", 0) > 0:
        porc_hp = max(0.0, min(1.0, entidade.hp / entidade.max_hp))
        if eh_santuario:
            cor_hp = (225, 45, 45) if porc_hp > 0.35 else (255, 130, 40)
        elif eh_aliado:
            cor_hp = (52, 225, 185) if porc_hp > 0.35 else (235, 165, 50)
        else:
            cor_hp = (45, 215, 85) if porc_hp > 0.35 else (230, 70, 50)
        pygame.draw.rect(tela, cor_hp, (x_bar, y_bar, int(bar_w * porc_hp), bar_h), border_radius=2)

    if getattr(entidade, "max_mp", 0) > 0:
        y_mp = y_bar + bar_h + 2
        pygame.draw.rect(tela, (15, 25, 60), (x_bar, y_mp, bar_w, 3), border_radius=1)
        porc_mp = max(0.0, min(1.0, entidade.mp / entidade.max_mp))
        pygame.draw.rect(tela, (40, 160, 255), (x_bar, y_mp, int(bar_w * porc_mp), 3), border_radius=1)

    y_icones = y_placa - 20
    hovered_ent = desenhar_icones_entidade(
        tela,
        entidade,
        x=rect.centerx,
        y=y_icones,
        tamanho=18,
        espacamento=4,
        posicao_mouse=posicao_mouse,
        alinhamento="centro",
    )
    return hovered_ent


def desenhar_destaque_alvo(
    tela: pygame.Surface,
    alvo: Any,
    nome_alvo_txt: str,
    fonte_inimigo: pygame.font.Font,
    pulso: int = 0,
) -> None:
    """Desenha a mira de seleção vermelha com cantos estilizados sobre o alvo em destaque."""
    txt_alvo = fonte_inimigo.render(f"▼ ALVO: {nome_alvo_txt.upper()} ▼", True, (255, 65, 65))
    tela.blit(txt_alvo, (alvo.rect.centerx - txt_alvo.get_width() // 2, alvo.rect.top - 46 + pulso))

    r = alvo.rect.inflate(12 + pulso, 12 + pulso)
    c_tam = 16
    c_cor = (240, 35, 35)
    c_cor_brilho = (255, 95, 95)
    w_ln = 3

    pygame.draw.rect(tela, c_cor, r, width=3, border_radius=6)
    pygame.draw.line(tela, c_cor_brilho, (r.left, r.top), (r.left + c_tam, r.top), w_ln + 1)
    pygame.draw.line(tela, c_cor_brilho, (r.left, r.top), (r.left, r.top + c_tam), w_ln + 1)
    pygame.draw.line(tela, c_cor_brilho, (r.right, r.top), (r.right - c_tam, r.top), w_ln + 1)
    pygame.draw.line(tela, c_cor_brilho, (r.right, r.top), (r.right, r.top + c_tam), w_ln + 1)
    pygame.draw.line(tela, c_cor_brilho, (r.left, r.bottom), (r.left + c_tam, r.bottom), w_ln + 1)
    pygame.draw.line(tela, c_cor_brilho, (r.left, r.bottom), (r.left, r.bottom - c_tam), w_ln + 1)
    pygame.draw.line(tela, c_cor_brilho, (r.right, r.bottom), (r.right - c_tam, r.bottom), w_ln + 1)
    pygame.draw.line(tela, c_cor_brilho, (r.right, r.bottom), (r.right, r.bottom - c_tam), w_ln + 1)


def desenhar_painel_log(
    tela: pygame.Surface,
    mensagem_log: str,
    fonte: pygame.font.Font,
    cooldown_feedback: int = 0,
    tempo_cooldown_maximo: int = 0,
) -> None:
    """Desenha a caixa superior com o histórico e logs de combate, com barra de cooldown dinâmica."""
    hud_log = pygame.Rect((tela.get_width() - 620) // 2, 20, 620, 70)
    pygame.draw.rect(tela, (22, 25, 36), hud_log, border_radius=10)
    cor_borda = (255, 210, 90) if cooldown_feedback > 0 else (110, 115, 140)
    pygame.draw.rect(tela, cor_borda, hud_log, width=2, border_radius=10)

    padding = 12
    linhas = quebrar_texto(mensagem_log, fonte, hud_log.width - padding * 2)
    total_altura = len(linhas) * fonte.get_linesize()
    y_inicio = hud_log.y + (hud_log.height - total_altura) // 2
    for indice_linha, linha in enumerate(linhas):
        surf = fonte.render(linha, True, (255, 255, 255))
        x = hud_log.x + (hud_log.width - surf.get_width()) // 2
        y = y_inicio + indice_linha * fonte.get_linesize()
        tela.blit(surf, (x, y))

    if cooldown_feedback > 0 and tempo_cooldown_maximo > 0:
        progresso = min(1.0, max(0.0, cooldown_feedback / float(tempo_cooldown_maximo)))
        largura_barra = int((hud_log.width - 16) * progresso)
        barra_rect = pygame.Rect(hud_log.x + 8, hud_log.bottom - 6, largura_barra, 3)
        pygame.draw.rect(tela, (255, 215, 90), barra_rect, border_radius=2)


def desenhar_cartoes_jogadores(
    tela: pygame.Surface,
    jogadores_status: List[Any],
    turno_ativo: Any,
    personagem_p1: Any,
    fonte_status: pygame.font.Font,
    eh_minion_func: Callable[[Any], bool],
    limite_minions_func: Callable[[Any], int],
    tipo_classe_func: Callable[[Any], str],
    obter_efeito_controle_func: Callable[[Any], Optional[str]],
    posicao_mouse: Optional[Tuple[int, int]] = None,
) -> Optional[Any]:
    """
    Desenha os cartões inferiores dos jogadores com barras de HP, PM, minions e efeitos de status.
    Retorna o efeito hovered ativo se houver foco do mouse em algum ícone.
    """
    largura_cartao = 290
    espaco_cartao = 20
    largura_total_cards = len(jogadores_status) * largura_cartao + (len(jogadores_status) - 1) * espaco_cartao
    x_base_status = (tela.get_width() - largura_total_cards) // 2
    y_base_status = 716

    hovered_resultado = None

    for indice, jogador in enumerate(jogadores_status):
        x_cartao = x_base_status + indice * (largura_cartao + espaco_cartao)
        rect_status = pygame.Rect(x_cartao, y_base_status, largura_cartao, 68)

        pygame.draw.rect(tela, (22, 24, 34), rect_status, border_radius=10)

        eh_morto = getattr(jogador, "hp", 0) <= 0
        eh_turno = (turno_ativo == jogador) and not eh_morto
        if eh_morto:
            cor_borda = (140, 50, 50)
            espessura_borda = 2
        elif eh_turno:
            cor_borda = (255, 210, 80)
            espessura_borda = 3
        else:
            cor_borda = (75, 80, 100)
            espessura_borda = 2
        pygame.draw.rect(tela, cor_borda, rect_status, width=espessura_borda, border_radius=10)

        nome_jogador = "JOGADOR 1" if jogador == personagem_p1 else "JOGADOR 2"
        if eh_morto:
            nome_jogador += " [DERROTADO]"
        else:
            efeito_controle = obter_efeito_controle_func(jogador)
            if efeito_controle == "Congelar":
                nome_jogador += " ❄"
            elif efeito_controle == "Atordoar":
                nome_jogador += " 💫"
        cor_nome = (180, 70, 70) if eh_morto else ((255, 230, 120) if eh_turno else (230, 230, 240))
        tela.blit(fonte_status.render(nome_jogador, True, cor_nome), (rect_status.x + 12, rect_status.y + 6))

        minions_j = getattr(jogador, "minions", [])
        minions_vivos = [m for m in minions_j if getattr(m, "hp", 0) > 0]
        classe_dano_j = tipo_classe_func(jogador)
        if minions_vivos or classe_dano_j == "Invocador":
            limite = limite_minions_func(jogador)
            txt_minions = fonte_status.render(f"MINIONS {len(minions_vivos)}/{limite}", True, (80, 235, 195))
            tela.blit(txt_minions, (rect_status.right - txt_minions.get_width() - 12, rect_status.y + 6))

        # Ícone de Vida (HP) e Barra de HP
        icone_vida = carregar_icone_efeito("Vida.png", 16)
        x_icone = rect_status.x + 10
        y_hp = rect_status.y + 28
        tela.blit(icone_vida, (x_icone, y_hp - 1))

        x_hp = rect_status.x + 30
        w_bar = 136
        h_bar = 13
        pygame.draw.rect(tela, (65, 14, 18), (x_hp, y_hp, w_bar, h_bar), border_radius=3)
        if jogador.max_hp > 0:
            porc_hp = max(0.0, min(1.0, jogador.hp / jogador.max_hp))
            pygame.draw.rect(tela, (40, 210, 80), (x_hp, y_hp, int(w_bar * porc_hp), h_bar), border_radius=3)
        txt_hp = fonte_status.render(f"HP {jogador.hp}/{jogador.max_hp}", True, (255, 255, 255))
        tela.blit(txt_hp, (x_hp + w_bar + 8, y_hp - 1))

        # Ícone de Mana/Foco e Barra de PM
        # Caso o jogador não possua a skill tree do feiticeiro que anula os debuffs do foco (F2), troca para Foco.png
        icone_recurso, _ = obter_icone_recurso_entidade(jogador, 16)
        y_mp = rect_status.y + 46
        tela.blit(icone_recurso, (x_icone, y_mp - 1))

        pygame.draw.rect(tela, (14, 22, 60), (x_hp, y_mp, w_bar, h_bar), border_radius=3)
        if jogador.max_mp > 0:
            porc_mp = max(0.0, min(1.0, jogador.mp / jogador.max_mp))
            pygame.draw.rect(tela, (30, 150, 255), (x_hp, y_mp, int(w_bar * porc_mp), h_bar), border_radius=3)
        txt_mp = fonte_status.render(f"PM {jogador.mp}/{jogador.max_mp}", True, (255, 255, 255))
        tela.blit(txt_mp, (x_hp + w_bar + 8, y_mp - 1))

        # Tooltips interativas para os ícones de Vida e Mana/Foco caso o mouse paire sobre eles
        if posicao_mouse:
            mx, my = posicao_mouse
            if pygame.Rect(x_icone, y_hp - 1, 16, 16).collidepoint(mx, my):
                hovered_resultado = {
                    "nome": "Vida (HP)",
                    "tag": "RECURSO",
                    "cor": (40, 210, 80),
                    "arquivo": "Vida.png",
                    "descricao": f"Vitalidade do jogador: {jogador.hp}/{jogador.max_hp} pontos de vida.",
                }
            elif pygame.Rect(x_icone, y_mp - 1, 16, 16).collidepoint(mx, my):
                if entidade_anula_debuff_foco(jogador):
                    hovered_resultado = {
                        "nome": "Mana (PM)",
                        "tag": "RECURSO",
                        "cor": (30, 150, 255),
                        "arquivo": "Mana.png",
                        "descricao": f"Pontos de Mana: {jogador.mp}/{jogador.max_mp}. Domínio Simples ativo (anula vulnerabilidade de foco).",
                    }
                else:
                    hovered_resultado = {
                        "nome": "Foco (PM)",
                        "tag": "FOCO",
                        "cor": (255, 140, 40),
                        "arquivo": "Foco.png",
                        "descricao": f"Pontos de Mana: {jogador.mp}/{jogador.max_mp}. Sem Domínio Simples: sofre +30% de dano durante o foco.",
                    }

        hovered_j = desenhar_icones_entidade(
            tela,
            jogador,
            x=rect_status.right - 10,
            y=y_hp - 3,
            tamanho=18,
            espacamento=4,
            posicao_mouse=posicao_mouse,
            alinhamento="direita",
        )
        if hovered_j:
            hovered_resultado = hovered_j

    return hovered_resultado
