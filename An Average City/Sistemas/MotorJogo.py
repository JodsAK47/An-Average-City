import os
import sys
from pathlib import Path

DIRETORIO_RAIZ = Path(__file__).resolve().parent.parent
if str(DIRETORIO_RAIZ) not in sys.path:
    sys.path.insert(0, str(DIRETORIO_RAIZ))
try:
    os.chdir(str(DIRETORIO_RAIZ))
except Exception:
    pass

import pygame
from Telas import (
    GerenciadorMenu,
    GerenciadorIntro,
    GerenciadorJogo,
    GerenciadorGameOver,
    GerenciadorClasses,
    GerenciadorVerso,
    GerenciadorVitoria,
    GerenciadorConquistasTela,
    GerenciadorCheatsTela,
    GerenciadorSewerTela,
    GerenciadorSelecao,
    GerenciadorPosLuta,
    GerenciadorDialogo,
    GerenciadorCutscene,

    GerenciadorConfiguracoesTela,
    GerenciadorPosDialogo,
    GerenciadorLoja,
    GerenciadorPausa,
)
from Sistemas import (
    save_global,
    sistema_conquistas,
    inventario_global,
    caminho_musica,
    sistema_config,
    gerenciador_musica,
    obter_musica_combate,
    sistema_cutscene,
)

def esta_em_cutscene() -> bool:
    return sistema_cutscene.esta_em_cutscene() or estado == "cutscene" 
from Entidades import personagem
from Gameplay import obter_dialogo_evento

pygame.init()
pygame.mixer.init()

LARGURA = 1000
ALTURA = 800
tela = pygame.Surface((LARGURA, ALTURA))
tela_cheia = sistema_config.obter_tela_cheia()
tela_real = sistema_config.aplicar_video()
if tela_real is None:
    tela_real = pygame.display.set_mode((LARGURA, ALTURA), pygame.RESIZABLE)
pygame.display.set_caption("Menu RPG")
relogio = pygame.time.Clock()

intro_tela = GerenciadorIntro(tela)
menu_tela = GerenciadorMenu(tela)
jogo_tela = GerenciadorJogo(tela)
game_over_tela = GerenciadorGameOver(tela)
selecao_tela = GerenciadorSelecao(tela)
conquistas_tela = GerenciadorConquistasTela(tela)
cheats_tela = GerenciadorCheatsTela(tela)
sewer_tela = GerenciadorSewerTela(tela)
classes_tela = GerenciadorClasses(tela)
verso_tela = GerenciadorVerso(tela)
pos_luta_tela = GerenciadorPosLuta(tela)
dialogo_tela = GerenciadorDialogo(tela)
pos_dialogo_tela = GerenciadorPosDialogo(tela)
vitoria_tela = GerenciadorVitoria(tela)
cutscene_tela = GerenciadorCutscene(tela)

config_tela = GerenciadorConfiguracoesTela(tela)
loja_tela = GerenciadorLoja(tela)
pausa_tela = GerenciadorPausa(tela)
estado_anterior_config = "menu"

classe_jogador1 = None
classe_jogador2 = None
verso_jogador1 = None
verso_jogador2 = None
alvo_classes = None
verso_menu_selecionado = None

def tocar_musica(nome_arquivo, fade_out_ms=600, fade_in_ms=800, verso=None):
    gerenciador_musica.tocar(
        nome_arquivo,
        fade_out_ms=fade_out_ms,
        fade_in_ms=fade_in_ms,
        verso=verso,
    )

intro_tela.iniciar(tocar_trilha=True)

estado = "intro"
rodando = True

def reiniciar_para_menu():
    global alvo_classes, verso_jogador1, verso_jogador2, classe_jogador1, classe_jogador2
    alvo_classes = None
    verso_jogador1 = None
    verso_jogador2 = None
    classe_jogador1 = None
    classe_jogador2 = None
    from Sistemas.Inventario import inventario_global
    inventario_global.resetar()
    personagem.resetar()
    jogo_tela.partida_atual = 1
    jogo_tela.pontos_jogo = max(0, jogo_tela.pontos_jogo)
    jogo_tela.classe_atual = "Nenhuma"
    jogo_tela.duas_pessoas = False
    jogo_tela.personagem2 = None
    jogo_tela.classe_jogador2 = None
    jogo_tela.classe_jogador2_tipo = None
    menu_tela.duas_pessoas = False
    menu_tela.switch_2p.ativo = False
    jogo_tela.menu_acoes_estado = "principal"
    jogo_tela.ataque_selecionado = None
    if getattr(pausa_tela, "superficie_fundo", None) is not None:
        pausa_tela.fechar()
    if getattr(cutscene_tela, 'ativo', False):
        cutscene_tela.finalizar()
    tocar_musica("Menu.mp3")
    return "menu"

def resetar_jogo():
    global verso_menu_selecionado
    save_global.resetar_tudo()
    sistema_conquistas.resetar_todas()
    verso_menu_selecionado = None
    verso_tela.verso_ativo = None
    verso_tela.progresso_por_verso = {verso: [] for verso in verso_tela.versos}
    verso_tela.pontos = save_global.obter_pontos()
    verso_tela.sincronizar_habilidades_ativas()
    personagem.resetar(resetar_cheats=True)
    personagem.talentos = set()
    personagem.ultimates_desbloqueadas = set()
    cheats_tela.resetar()
    if hasattr(jogo_tela, 'personagem2') and jogo_tela.personagem2 is not None:
        jogo_tela.personagem2.resetar(resetar_cheats=True)
        jogo_tela.personagem2.talentos = set()
        jogo_tela.personagem2.ultimates_desbloqueadas = set()
        jogo_tela.personagem2.god_mode = False
        jogo_tela.personagem2.classe_aplicada = None
    if hasattr(sewer_tela, 'modal_aberto'):
        sewer_tela.modal_aberto = False
    menu_tela.mostrar_feedback("⚠️ SAVE RESETADO COM SUCESSO!", (255, 100, 100))

def registrar_pontos_partida():
    pontos_partida = max(0, int(jogo_tela.pontos_jogo))
    if not getattr(jogo_tela, 'pontos_salvos_na_partida', False):
        save_global.registrar_partida(pontos_partida)
        jogo_tela.pontos_salvos_na_partida = True
    return pontos_partida

def tratar_eventos_menu(evento, posicao_mouse):
    global estado, rodando, alvo_classes, verso_menu_selecionado, verso_jogador1, verso_jogador2
    botoes_menu = menu_tela.botoes

    if botoes_menu["jogar"].checar_clique(evento, posicao_mouse):
        verso_escolhido_anteriormente = verso_menu_selecionado or (
            jogo_tela.classe_atual if getattr(jogo_tela, 'classe_atual', 'Nenhuma') != 'Nenhuma' else None
        )
        if getattr(menu_tela, 'duas_pessoas', False):
            alvo_classes = 1
            verso_jogador1 = None
            verso_jogador2 = None
            verso_tela.modo = "visualizacao"
            verso_tela.alvo_personagem = personagem
            verso_tela.verso_atual = verso_escolhido_anteriormente or "Sobrevivente"
            verso_tela.sincronizar_habilidades_ativas()
            verso_tela.habilidade_foco = None
            verso_tela.aviso = "Escolha o Verso para JOGADOR 1"
            return "verso"
        else:
            if verso_escolhido_anteriormente:
                jogo_tela.classe_atual = verso_escolhido_anteriormente
                alvo_classes = 1
                verso_jogador1 = verso_escolhido_anteriormente
                classes_tela.aviso = f"Verso: {verso_escolhido_anteriormente} | Escolha SUA CLASSE"
                classes_tela.classe_atual = "Físico"
                return "classes"
            alvo_classes = 1
            verso_jogador1 = None
            verso_tela.modo = "visualizacao"
            verso_tela.alvo_personagem = personagem
            verso_tela.verso_atual = "Sobrevivente"
            verso_tela.sincronizar_habilidades_ativas()
            verso_tela.habilidade_foco = None
            verso_tela.aviso = "Escolha seu Verso"
            return "verso"

    if botoes_menu["classe"].checar_clique(evento, posicao_mouse):
        verso_tela.modo = "menu"
        verso_ativo = verso_menu_selecionado or (
            jogo_tela.classe_atual if getattr(jogo_tela, 'classe_atual', 'Nenhuma') != 'Nenhuma' else None
        )
        verso_tela.verso_ativo = verso_ativo
        verso_tela.verso_atual = verso_ativo if verso_ativo else "Sobrevivente"
        verso_tela.pontos = save_global.obter_pontos()
        verso_tela.sincronizar_habilidades_ativas()
        verso_tela.aviso = ""
        return "verso"

    if botoes_menu["conquistas"].checar_clique(evento, posicao_mouse):
        return "conquistas"

    btn_menu_cfg = botoes_menu.get("menu") or botoes_menu.get("config")
    if btn_menu_cfg and btn_menu_cfg.checar_clique(evento, posicao_mouse):
        estado_anterior_config = "menu"
        return "config"

    if menu_tela.botao_salvar.checar_clique(evento, posicao_mouse):
        save_global.salvar()
        sistema_conquistas.salvar()
        menu_tela.mostrar_feedback("✓ JOGO SALVO COM SUCESSO!", (100, 255, 140))
        return None

    if menu_tela.botao_reset.checar_clique(evento, posicao_mouse):
        resetar_jogo()
        return None

    if menu_tela.checar_clique_esgoto(evento, posicao_mouse):
        return "sewer"

    if (destino_porta := menu_tela.checar_clique_porta_cheats(evento, posicao_mouse)):
        if destino_porta == "cheats":
            return "cheats"

    if menu_tela.switch_2p.checar_clique(evento, posicao_mouse):
        menu_tela.duas_pessoas = menu_tela.switch_2p.ativo
        if menu_tela.duas_pessoas:
            sistema_conquistas.desbloquear("cooperativo")
        else:
            jogo_tela.duas_pessoas = False
            jogo_tela.personagem2 = None
            jogo_tela.classe_jogador2 = None
            jogo_tela.classe_jogador2_tipo = None
        return None

    if botoes_menu["sair"].checar_clique(evento, posicao_mouse):
        rodando = False
        return None

    return None

def tratar_eventos_classes(evento, posicao_mouse):
    global alvo_classes, classe_jogador1, classe_jogador2, verso_jogador1, verso_jogador2
    escolha_classe = classes_tela.atualizar_eventos(evento, posicao_mouse)
    target = alvo_classes if alvo_classes is not None else 1

    if classes_tela.voltar_clicado:
        classes_tela.voltar_clicado = False
        if getattr(menu_tela, 'duas_pessoas', False):
            if target == 2:
                # Volta para a seleção de verso do Jogador 2
                alvo_classes = 2
                verso_tela.modo = "visualizacao"
                verso_tela.alvo_personagem = getattr(jogo_tela, 'personagem2', None)
                verso_tela.verso_atual = verso_jogador2 or "Sobrevivente"
                verso_tela.sincronizar_habilidades_ativas()
                verso_tela.habilidade_foco = None
                verso_tela.aviso = "Escolha o Verso para JOGADOR 2"
                return "verso"
            else:
                # Volta para a seleção de verso do Jogador 1
                alvo_classes = 1
                verso_tela.modo = "visualizacao"
                verso_tela.alvo_personagem = personagem
                verso_tela.verso_atual = verso_jogador1 or "Sobrevivente"
                verso_tela.sincronizar_habilidades_ativas()
                verso_tela.habilidade_foco = None
                verso_tela.aviso = "Escolha o Verso para JOGADOR 1"
                return "verso"
        else:
            alvo_classes = 1
            verso_tela.modo = "visualizacao"
            verso_tela.alvo_personagem = personagem
            verso_tela.verso_atual = verso_jogador1 or "Sobrevivente"
            verso_tela.sincronizar_habilidades_ativas()
            verso_tela.habilidade_foco = None
            verso_tela.aviso = "Escolha seu Verso"
            return "verso"

    if escolha_classe:
        if isinstance(escolha_classe, tuple):
            verso_escolhido, classe_escolhida = escolha_classe
        else:
            classe_escolhida = escolha_classe
            if target == 1:
                verso_escolhido = verso_jogador1 or getattr(jogo_tela, 'classe_atual', 'Sobrevivente')
            else:
                verso_escolhido = verso_jogador2 or getattr(jogo_tela, 'classe_jogador2', 'Sobrevivente')

        if target == 1:
            from Sistemas.Inventario import inventario_global
            inventario_global.resetar()
            verso_jogador1 = verso_escolhido
            classe_jogador1 = classe_escolhida
            jogo_tela.configurar_classe(verso_jogador1, classe_jogador1)
            verso_tela.aplicar_talentos_ao_personagem(personagem, verso=verso_jogador1)
            if getattr(menu_tela, 'duas_pessoas', False):
                # Jogador 1 terminou classe -> agora Jogador 2 escolhe seu VERSO!
                alvo_classes = 2
                verso_tela.modo = "visualizacao"
                verso_tela.alvo_personagem = getattr(jogo_tela, 'personagem2', None)
                verso_tela.verso_atual = verso_jogador2 or "Sobrevivente"
                verso_tela.sincronizar_habilidades_ativas()
                verso_tela.habilidade_foco = None
                verso_tela.aviso = "Escolha o Verso para JOGADOR 2"
                return "verso"
            else:
                jogo_tela.duas_pessoas = False
                jogo_tela.personagem2 = None
                jogo_tela.classe_jogador2 = None
                jogo_tela.classe_jogador2_tipo = None
                jogo_tela.reiniciar()
                tocar_musica(jogo_tela.musica_luta)
                alvo_classes = None
                return "jogo"
        elif target == 2:
            verso_jogador2 = verso_escolhido
            classe_jogador2 = classe_escolhida
            jogo_tela.classe_jogador2 = verso_jogador2
            jogo_tela.classe_jogador2_tipo = classe_jogador2
            jogo_tela.duas_pessoas = True
            jogo_tela.reiniciar()
            if jogo_tela.personagem2 is not None:
                verso_tela.aplicar_talentos_ao_personagem(jogo_tela.personagem2, verso=verso_jogador2)
                jogo_tela.personagem2.classe_aplicada = None
                jogo_tela._aplicar_classe_personagem2()
            tocar_musica(jogo_tela.musica_luta)
            alvo_classes = None
            return "jogo"
        else:
            from Sistemas.Inventario import inventario_global
            inventario_global.resetar()
            jogo_tela.configurar_classe(verso_escolhido, classe_escolhida)
            verso_tela.aplicar_talentos_ao_personagem(personagem, verso=verso_escolhido)
            jogo_tela.reiniciar()
            tocar_musica(jogo_tela.musica_luta)
            alvo_classes = None
            return "jogo"
    return None

def tratar_eventos_verso(evento, posicao_mouse):
    global alvo_classes, verso_menu_selecionado, verso_jogador1, verso_jogador2
    escolha_verso = verso_tela.atualizar_eventos(evento, posicao_mouse)

    if verso_tela.voltar_clicado:
        verso_tela.voltar_clicado = False
        if getattr(menu_tela, 'duas_pessoas', False) and alvo_classes == 2:
            # Jogador 2 voltou da tela de verso -> retorna à escolha de classe do Jogador 1
            alvo_classes = 1
            classes_tela.aviso = f"J1: {verso_jogador1} | Escolha CLASSE para JOGADOR 1"
            return "classes"
        else:
            alvo_classes = None
            return "menu"

    if escolha_verso:
        gerenciador_musica.definir_verso(escolha_verso)
        if getattr(verso_tela, "modo", "menu") == "visualizacao":
            target = alvo_classes if alvo_classes is not None else 1
            if target == 1:
                verso_jogador1 = escolha_verso
                jogo_tela.classe_atual = escolha_verso
                jogo_tela.musica_luta = jogo_tela.obter_musica_combate(eh_chefe=False, verso=escolha_verso)
                verso_tela.aplicar_talentos_ao_personagem(personagem, verso=escolha_verso)
                if getattr(menu_tela, 'duas_pessoas', False):
                    classes_tela.aviso = f"J1: {escolha_verso} | Escolha CLASSE para JOGADOR 1"
                else:
                    classes_tela.aviso = f"Verso: {escolha_verso} | Escolha SUA CLASSE"
                classes_tela.classe_atual = "Físico"
                return "classes"
            elif target == 2:
                verso_jogador2 = escolha_verso
                jogo_tela.classe_jogador2 = escolha_verso
                classes_tela.aviso = f"J2: {escolha_verso} | Escolha CLASSE para JOGADOR 2"
                classes_tela.classe_atual = "Físico"
                return "classes"
        else:
            verso_menu_selecionado = escolha_verso
            jogo_tela.classe_atual = escolha_verso
            verso_tela.verso_ativo = escolha_verso
            verso_tela.aplicar_talentos_ao_personagem(personagem, verso=escolha_verso)
            verso_tela.aviso = f"Verso {escolha_verso} definido como ativo!"
            save_global.salvar()
            return None
    return None

def tratar_eventos_jogo(evento, posicao_mouse):
    if evento.type == pygame.KEYDOWN and evento.key in (pygame.K_ESCAPE, pygame.K_p):
        pausa_tela.abrir("jogo")
        return "pausa"
    if getattr(jogo_tela, "btn_pausa", None) and jogo_tela.btn_pausa.checar_clique(evento, posicao_mouse):
        pausa_tela.abrir("jogo")
        return "pausa"
    if hasattr(jogo_tela, "processar_evento"):
        jogo_tela.processar_evento(evento, posicao_mouse)
    return None

def tratar_eventos_pos_luta(evento, posicao_mouse):
    if getattr(jogo_tela, 'duas_pessoas', False) and getattr(jogo_tela, 'personagem2', None) is not None:
        pos_luta_tela.jogadores = [personagem, jogo_tela.personagem2]
    else:
        pos_luta_tela.jogadores = [personagem]

    resultado_tela = pos_luta_tela.atualizar_eventos(evento, posicao_mouse)
    if resultado_tela == "continuar":
        selecao_tela.recarregar_opcoes()
        return "selecao_cenario"
    elif resultado_tela == "pausa":
        pausa_tela.abrir("pos_luta")
        return "pausa"
    if evento.type == pygame.KEYDOWN and evento.key in (pygame.K_ESCAPE, pygame.K_p):
        pausa_tela.abrir("pos_luta")
        return "pausa"
    return None

def tratar_eventos_selecao_cenario(evento, posicao_mouse):
    if evento.type == pygame.KEYDOWN and evento.key in (pygame.K_ESCAPE, pygame.K_p):
        pausa_tela.abrir("selecao_cenario")
        return "pausa"
    escolha_cenario = selecao_tela.atualizar_eventos(evento, posicao_mouse)
    if escolha_cenario == "dormir":
        jogo_tela.recuperar_apos_batalha(dormir=True)
        jogo_tela.configurar_cenario("dormir")
        jogo_tela.reiniciar()
        tocar_musica(jogo_tela.musica_luta)
        return "jogo"
    elif escolha_cenario:
        if "evento" in escolha_cenario:
            dados_dialogo = obter_dialogo_evento(escolha_cenario)
            dialogo_tela.iniciar(dados_dialogo)
            return "dialogo"
        else:
            jogo_tela.configurar_cenario(escolha_cenario)
            jogo_tela.reiniciar()
            tocar_musica(jogo_tela.musica_luta)
            return "jogo"
    return None

def tratar_eventos_dialogo(evento, posicao_mouse):
    resultado_dialogo = dialogo_tela.atualizar_eventos(evento, posicao_mouse)
    if resultado_dialogo == "cancelar_evento":
        jogo_tela.configurar_cenario("ignorar_evento")
        jogo_tela.reiniciar()
        tocar_musica(jogo_tela.musica_luta)
        return "jogo"
    elif resultado_dialogo:
        dados_efeito = jogo_tela.configurar_cenario(resultado_dialogo)
        if dados_efeito and isinstance(dados_efeito, dict):
            pos_dialogo_tela.configurar(dados_efeito)
            return "pos_dialogo"
        jogo_tela.reiniciar()
        tocar_musica(jogo_tela.musica_luta)
        return "jogo"
    return None

def tratar_eventos_pos_dialogo(evento, posicao_mouse):
    resultado_pos = pos_dialogo_tela.atualizar_eventos(evento, posicao_mouse)
    if resultado_pos == "abrir_loja":
        tipo = getattr(pos_dialogo_tela, "tipo_loja", "barista")
        sucesso = getattr(pos_dialogo_tela, "sucesso", True)
        loja_tela.configurar_loja(tipo, sucesso=sucesso)
        return "loja"
    if resultado_pos == "continuar":
        jogo_tela.reiniciar()
        tocar_musica(jogo_tela.musica_luta)
        return "jogo"
    return None

def tratar_eventos_loja(evento, posicao_mouse):
    if evento.type == pygame.KEYDOWN and evento.key in (pygame.K_ESCAPE, pygame.K_p):
        pausa_tela.abrir("loja")
        return "pausa"
    resultado_loja = loja_tela.atualizar_eventos(evento, posicao_mouse)
    if resultado_loja in ("continuar", "jogo", "voltar"):
        jogo_tela.reiniciar()
        tocar_musica(jogo_tela.musica_luta)
        return "jogo"
    return None

def tratar_eventos_conquistas(evento, posicao_mouse):
    resultado_conquistas = conquistas_tela.atualizar_eventos(evento, posicao_mouse)
    if resultado_conquistas == "menu" or conquistas_tela.voltar_clicado:
        conquistas_tela.voltar_clicado = False
        return "menu"
    return None

def tratar_eventos_sewer(evento, posicao_mouse):
    resultado_sewer = sewer_tela.atualizar_eventos(evento, posicao_mouse)
    if resultado_sewer == "menu":
        return "menu"
    return None

def iniciar_batalha_customizada(nomes_inimigos):
    from Gameplay.GeracaoFases import BANCO_INIMIGOS, _criar_inimigo_a_partir_template

    if getattr(jogo_tela, 'classe_atual', 'Nenhuma') in ('Nenhuma', None):
        jogo_tela.classe_atual = "Feiticeiro"
    if not getattr(jogo_tela, 'classe_dano_atual', None) or jogo_tela.classe_dano_atual == "Nenhuma":
        jogo_tela.classe_dano_atual = "Magia"

    if personagem.hp <= 0:
        personagem.hp = personagem.max_hp
    personagem.bloqueando = False
    personagem.recuperando = False

    contagem_nomes = {}
    for nome in nomes_inimigos:
        contagem_nomes[nome] = contagem_nomes.get(nome, 0) + 1

    indices_atuais = {nome: 0 for nome in contagem_nomes}
    instancias_inimigos = []

    for nome in nomes_inimigos:
        tmpl = next((t for t in BANCO_INIMIGOS if t.get("nome") == nome), None)
        if tmpl:
            ini = _criar_inimigo_a_partir_template(tmpl, x=740, y=400)
            if contagem_nomes[nome] > 1:
                indices_atuais[nome] += 1
                ini.nome = f"{tmpl.get('nome')} #{indices_atuais[nome]}"
            else:
                ini.nome = tmpl.get("nome")

            nome_lower = ini.nome.lower()
            if "confinamento" in nome_lower or getattr(ini, "eh_confinamento", False):
                ini.eh_confinamento = True
                ini.carga_confinamento = 0
                ini.max_carga_confinamento = 5

            if "sukuna" in nome_lower or "estraga prazeres" in nome_lower:
                ini.mp = min(getattr(ini, "max_mp", 40), 10)

            instancias_inimigos.append(ini)

    if not instancias_inimigos:
        return None

    jogo_tela.fase_numero = max(1, len(instancias_inimigos))
    jogo_tela.partida_atual = 1

    tem_chefe = any(
        getattr(ini, "tipo", "") == "chefe" or
        any(k in ini.nome.lower() for k in ("sukuna", "estraga prazeres", "charlie"))
        for ini in instancias_inimigos
    )
    if tem_chefe:
        jogo_tela.total_partidas = 1
        jogo_tela.partida_atual = 1
    verso_batalha = getattr(jogo_tela, 'classe_atual', 'Feiticeiro')
    for ini in instancias_inimigos:
        nome_l = getattr(ini, 'nome', '').lower()
        if "sukuna" in nome_l:
            verso_batalha = "Feiticeiro"
            break
        elif "estraga prazeres" in nome_l:
            verso_batalha = "Agente"
            break
        elif "charlie" in nome_l:
            verso_batalha = "Sobrevivente"
            break
        elif getattr(ini, 'verso', None):
            verso_batalha = ini.verso

    musica = jogo_tela.obter_musica_combate(eh_chefe=tem_chefe, verso=verso_batalha)
    jogo_tela.musica_luta = musica

    participantes = [personagem]
    if personagem.hp <= 0:
        personagem.hp = personagem.max_hp
    if getattr(jogo_tela, 'duas_pessoas', False) and getattr(jogo_tela, 'personagem2', None) is not None:
        if jogo_tela.personagem2.hp <= 0:
            jogo_tela.personagem2.hp = jogo_tela.personagem2.max_hp
        participantes.append(jogo_tela.personagem2)
    participantes.extend(instancias_inimigos)

    jogo_tela.ordem_turnos = participantes
    jogo_tela.reiniciar()
    tocar_musica(musica)
    return "jogo"

def tratar_eventos_cheats(evento, posicao_mouse):
    resultado_cheats = cheats_tela.atualizar_eventos(evento, posicao_mouse)
    if isinstance(resultado_cheats, tuple) and resultado_cheats[0] == "batalhar_custom":
        nomes_inimigos = resultado_cheats[1]
        if nomes_inimigos:
            return iniciar_batalha_customizada(nomes_inimigos)

    if resultado_cheats == "batalhar_sukuna":
        return iniciar_batalha_customizada(["Sukuna"])
    if resultado_cheats == "batalhar_estraga_prazeres":
        return iniciar_batalha_customizada(["Estraga Prazeres"])
    if resultado_cheats == "batalhar_confinamento":
        return iniciar_batalha_customizada(["Confinamento"])

    if resultado_cheats in ("menu", "sewer") or cheats_tela.voltar_clicado:
        cheats_tela.voltar_clicado = False
        return "menu"
    return None

def tratar_eventos_pausa(evento, posicao_mouse):
    global estado_anterior_config
    resultado = pausa_tela.atualizar_eventos(evento, posicao_mouse)
    if resultado == "continuar":
        origem = getattr(pausa_tela, "estado_anterior", "jogo")
        pausa_tela.fechar()
        return origem
    elif resultado == "config":
        estado_anterior_config = "pausa"
        return "config"
    elif resultado == "menu":
        pausa_tela.fechar()
        return reiniciar_para_menu()
    return None

def tratar_eventos_config(evento, posicao_mouse):
    global tela_real, tela_cheia, estado_anterior_config
    resultado_config = config_tela.atualizar_eventos(evento, posicao_mouse)
    if resultado_config == "menu" or config_tela.voltar_clicado:
        config_tela.voltar_clicado = False
        destino = estado_anterior_config
        estado_anterior_config = "menu"
        return destino
    elif resultado_config == "video_alterado":
        nova_tela = pygame.display.get_surface()
        if nova_tela is not None:
            tela_real = nova_tela
        tela_cheia = sistema_config.obter_tela_cheia()
        return None
    return None

def tratar_eventos_game_over(evento, posicao_mouse):
    resultado = game_over_tela.atualizar_eventos(evento, posicao_mouse)
    if resultado == "menu":
        return reiniciar_para_menu()
    elif resultado == "reiniciar":
        from Sistemas.Inventario import inventario_global
        inventario_global.resetar()
        personagem.resetar()
        if getattr(jogo_tela, 'duas_pessoas', False) and getattr(jogo_tela, 'personagem2', None) is not None:
            jogo_tela.personagem2.resetar()
            jogo_tela.personagem2.classe_aplicada = None
        verso_atual = getattr(game_over_tela, 'verso', getattr(jogo_tela, 'classe_atual', 'Sobrevivente'))
        if verso_atual in ('Nenhuma', None):
            verso_atual = 'Sobrevivente'
        classe_tipo = getattr(jogo_tela, 'classe_dano_atual', 'Magia' if verso_atual == 'Feiticeiro' else 'Físico')
        jogo_tela.configurar_classe(verso_atual, classe_tipo)
        verso_tela.aplicar_talentos_ao_personagem(personagem, verso=verso_atual)
        if getattr(jogo_tela, 'duas_pessoas', False) and getattr(jogo_tela, 'personagem2', None) is not None:
            verso_tela.aplicar_talentos_ao_personagem(jogo_tela.personagem2, verso=getattr(jogo_tela, 'classe_jogador2', verso_atual))
            jogo_tela._aplicar_classe_personagem2()
        jogo_tela.partida_atual = 1
        jogo_tela.pontos_jogo = 0
        jogo_tela.reiniciar()
        tocar_musica(jogo_tela.musica_luta)
        return "jogo"
    return None

def tratar_eventos_cutscene(evento, posicao_mouse):
    cutscene_tela.atualizar_eventos(evento, posicao_mouse)
    # A finalização da cutscene dispara callback_conclusao, que define 'estado'
    # para 'game_over' ou 'tela_vitoria'. Retornamos None para não sobrescrever 'estado'.
    return None

def tratar_eventos_vitoria(evento, posicao_mouse):
    if evento.type == pygame.KEYDOWN and evento.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
        return reiniciar_para_menu()
    if vitoria_tela.botao_menu.checar_clique(evento, posicao_mouse):
        return reiniciar_para_menu()
    return None

def tratar_eventos_intro(evento, posicao_mouse):
    global estado
    resultado = intro_tela.atualizar_eventos(evento, posicao_mouse)
    if resultado == "menu":
        tocar_musica("Menu.mp3", fade_out_ms=600, fade_in_ms=800)
        estado = "menu"
        return "menu"
    return None

DISTRIBUIDOR_EVENTOS = {
    "intro": tratar_eventos_intro,
    "menu": tratar_eventos_menu,
    "jogo": tratar_eventos_jogo,
    "pausa": tratar_eventos_pausa,
    "classes": tratar_eventos_classes,
    "verso": tratar_eventos_verso,
    "game_over": tratar_eventos_game_over,
    "cutscene": tratar_eventos_cutscene,
    "tela_vitoria": tratar_eventos_vitoria,
    "pos_luta": tratar_eventos_pos_luta,
    "selecao_cenario": tratar_eventos_selecao_cenario,
    "dialogo": tratar_eventos_dialogo,
    "pos_dialogo": tratar_eventos_pos_dialogo,
    "loja": tratar_eventos_loja,
    "conquistas": tratar_eventos_conquistas,
    "config": tratar_eventos_config,
    "sewer": tratar_eventos_sewer,
    "cheats": tratar_eventos_cheats,
}

def atualizar_estado_atual(posicao_mouse, estado_clique_mouse):
    global estado
    if estado == "intro":
        resultado_intro = intro_tela.atualizar(posicao_mouse, estado_clique_mouse)
        if resultado_intro == "menu":
            tocar_musica("Menu.mp3", fade_out_ms=600, fade_in_ms=800)
            estado = "menu"
        return
    if estado == "jogo":
        resultado_jogo = jogo_tela.atualizar(posicao_mouse, estado_clique_mouse)
        if resultado_jogo == "pausa":
            pausa_tela.abrir("jogo")
            estado = "pausa"
            return
        elif resultado_jogo == "game_over":
            pontos_finais = registrar_pontos_partida()
            game_over_tela.pontos = pontos_finais
            gerenciador_musica.parar()

            verso_derrota = getattr(jogo_tela, 'classe_atual', 'Sobrevivente')
            perdeu_para_chefe = getattr(jogo_tela, 'perdeu_para_chefe', False)
            boss_nome = getattr(jogo_tela, 'ultimo_chefe_combate', None)

            if not perdeu_para_chefe:
                # O jogador foi derrotado por inimigos comuns: tela de game over direta sem cutscene
                game_over_tela.pontos = pontos_finais
                game_over_tela.definir_verso(verso_derrota)
                tocar_musica("GameOver.mp3")
                estado = "game_over"
            else:
                if not boss_nome:
                    for ent in getattr(jogo_tela, 'ordem_turnos', []):
                        if jogo_tela.eh_inimigo(ent) and getattr(ent, 'hp', 0) > 0:
                            nome_e = getattr(ent, 'nome', '').strip().lower()
                            tipo_e = getattr(ent, 'tipo', '').strip().lower()
                            if 'sukuna' in nome_e and (tipo_e == 'chefe' or nome_e == 'sukuna'):
                                boss_nome = 'Sukuna'
                                break
                            elif 'charlie' in nome_e and (tipo_e == 'chefe' or nome_e == 'charlie'):
                                boss_nome = 'Charlie'
                                break
                            elif 'estraga prazeres' in nome_e and (tipo_e == 'chefe' or 'estraga' in nome_e):
                                boss_nome = 'Estraga Prazeres'
                                break

                # Mapeamento do chefe respectivo para cada verso
                chefe_respectivo_por_verso = {
                    "feiticeiro": "Sukuna",
                    "sorcerer": "Sukuna",
                    "sobrevivente": "Charlie",
                    "survivor": "Charlie",
                    "agente": "Estraga Prazeres",
                    "agent": "Estraga Prazeres",
                }
                boss_esperado = chefe_respectivo_por_verso.get(str(verso_derrota).lower().strip(), "")

                # A cutscene de derrota so deve ser exibida caso morra para o respectivo boss
                morreu_para_boss_respectivo = bool(
                    boss_nome and (
                        (boss_esperado and boss_nome.lower() == boss_esperado.lower()) or
                        boss_nome in ("Sukuna", "Charlie", "Estraga Prazeres")
                    )
                )

                if morreu_para_boss_respectivo:
                    def ao_concluir_cutscene_game_over():
                        global estado
                        game_over_tela.pontos = registrar_pontos_partida()
                        game_over_tela.definir_verso(verso_derrota)
                        tocar_musica("GameOver.mp3")
                        estado = "game_over"

                    cutscene_tela.iniciar(boss_nome=boss_nome, verso=verso_derrota, callback_conclusao=ao_concluir_cutscene_game_over)
                    estado = "cutscene"
                else:
                    game_over_tela.pontos = pontos_finais
                    game_over_tela.definir_verso(verso_derrota)
                    tocar_musica("GameOver.mp3")
                    estado = "game_over"
        elif resultado_jogo == "vitoria":
            registrar_pontos_partida()
            tocar_musica("Menu.mp3")
            if getattr(jogo_tela, 'duas_pessoas', False) and getattr(jogo_tela, 'personagem2', None) is not None:
                pos_luta_tela.jogadores = [personagem, jogo_tela.personagem2]
            else:
                pos_luta_tela.jogadores = [personagem]
            if hasattr(jogo_tela, 'ultimo_resultado_batalha') and jogo_tela.ultimo_resultado_batalha:
                pos_luta_tela.definir_popup_notificacao(jogo_tela.ultimo_resultado_batalha)
            estado = "pos_luta"
        elif resultado_jogo == "fim_jogo":
            pontos_finais = registrar_pontos_partida()
            vitoria_tela.pontos = pontos_finais
            gerenciador_musica.parar()

            verso_batalha = getattr(jogo_tela, 'classe_atual', 'Feiticeiro')
            boss_nome = getattr(jogo_tela, 'ultimo_chefe_derrotado', None)
            if not boss_nome:
                if verso_batalha == 'Feiticeiro':
                    boss_nome = 'Sukuna'
                elif verso_batalha == 'Sobrevivente':
                    boss_nome = 'Charlie'
                else:
                    boss_nome = 'Estraga Prazeres'

            def ao_concluir_cutscene():
                global estado
                tocar_musica("Vitoria.mp3")
                vitoria_tela.pontos = registrar_pontos_partida()
                estado = "tela_vitoria"

            cutscene_tela.iniciar(boss_nome=boss_nome, verso=verso_batalha, callback_conclusao=ao_concluir_cutscene)
            estado = "cutscene"
        elif resultado_jogo == "fugiu":
            if getattr(jogo_tela, 'duas_pessoas', False) and getattr(jogo_tela, 'personagem2', None) is not None:
                pos_luta_tela.jogadores = [personagem, jogo_tela.personagem2]
            else:
                pos_luta_tela.jogadores = [personagem]
            if hasattr(jogo_tela, 'ultimo_resultado_batalha') and jogo_tela.ultimo_resultado_batalha:
                pos_luta_tela.definir_popup_notificacao(jogo_tela.ultimo_resultado_batalha)
            tocar_musica("Menu.mp3")
            estado = "pos_luta"
        elif resultado_jogo == "batalha_encerrada":
            estado = "selecao_cenario"
        return

    telas_atualizacao = {
        "intro": intro_tela,
        "menu": menu_tela,
        "classes": classes_tela,
        "verso": verso_tela,
        "conquistas": conquistas_tela,
        "config": config_tela,
        "sewer": sewer_tela,
        "cheats": cheats_tela,
        "game_over": game_over_tela,
        "tela_vitoria": vitoria_tela,
        "pos_luta": pos_luta_tela,
        "selecao_cenario": selecao_tela,
        "pos_dialogo": pos_dialogo_tela,
        "loja": loja_tela,
        "cutscene": cutscene_tela,
        "concluido": game_over_tela,
        "pausa": pausa_tela,
    }
    if tela_alvo := telas_atualizacao.get(estado):
        tela_alvo.atualizar(posicao_mouse, estado_clique_mouse)

def desenhar_estado_atual(posicao_mouse):
    telas_desenho = {
        "intro": intro_tela.desenhar,
        "menu": menu_tela.desenhar,
        "classes": classes_tela.desenhar,
        "verso": verso_tela.desenhar,
        "conquistas": conquistas_tela.desenhar,
        "config": config_tela.desenhar,
        "sewer": sewer_tela.desenhar,
        "cheats": cheats_tela.desenhar,
        "jogo": lambda: jogo_tela.desenhar(posicao_mouse),
        "pos_luta": lambda: pos_luta_tela.desenhar(posicao_mouse),
        "selecao_cenario": lambda: selecao_tela.desenhar(posicao_mouse),
        "dialogo": lambda: (selecao_tela.desenhar(posicao_mouse), dialogo_tela.desenhar()),
        "pos_dialogo": lambda: (selecao_tela.desenhar(posicao_mouse), pos_dialogo_tela.desenhar(posicao_mouse)),
        "loja": lambda: loja_tela.desenhar(posicao_mouse),
        "game_over": game_over_tela.desenhar,
        "cutscene": cutscene_tela.desenhar,
        "tela_vitoria": vitoria_tela.desenhar,
        "concluido": lambda: (game_over_tela.desenhar() if getattr(personagem, "hp", 1) <= 0 else vitoria_tela.desenhar()),
        "pausa": pausa_tela.desenhar,
    }
    tela.fill((0, 0, 0))
    if renderizador := telas_desenho.get(estado):
        renderizador()

def loop_principal():
    global rodando, estado, tela_real, tela, tela_cheia
    while rodando:
        gerenciador_musica.atualizar()
        posicao_mouse_real = pygame.mouse.get_pos()
        estado_clique_mouse = pygame.mouse.get_pressed()

        largura_real, altura_real = tela_real.get_size()
        escala = min(largura_real / LARGURA, altura_real / ALTURA) if LARGURA > 0 and ALTURA > 0 else 1
        nova_largura = int(LARGURA * escala)
        nova_altura = int(ALTURA * escala)
        deslocamento_x = (largura_real - nova_largura) // 2
        deslocamento_y = (altura_real - nova_altura) // 2

        if escala > 0:
            mx = int((posicao_mouse_real[0] - deslocamento_x) / escala)
            my = int((posicao_mouse_real[1] - deslocamento_y) / escala)
        else:
            mx, my = 0, 0
        posicao_mouse = (max(0, min(mx, LARGURA)), max(0, min(my, ALTURA)))

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_F11:
                    tela_cheia = not tela_cheia
                    sistema_config.definir_tela_cheia(tela_cheia)
                    sistema_config.salvar()
                    nova_tela = sistema_config.aplicar_video()
                    if nova_tela is not None:
                        tela_real = nova_tela
            if manipulador := DISTRIBUIDOR_EVENTOS.get(estado):
                novo_estado = manipulador(evento, posicao_mouse)
                if novo_estado:
                    estado = novo_estado

        atualizar_estado_atual(posicao_mouse, estado_clique_mouse)
        desenhar_estado_atual(posicao_mouse)

        sistema_conquistas.atualizar_notificacoes()
        if not esta_em_cutscene() and estado != "intro":
            sistema_conquistas.desenhar_notificacao(tela)

        tela_redimensionada = pygame.transform.scale(tela, (nova_largura, nova_altura))
        tela_real.fill((0, 0, 0))
        tela_real.blit(tela_redimensionada, (deslocamento_x, deslocamento_y))
        pygame.display.flip()
        relogio.tick(60)

    pygame.quit()

if __name__ == "__main__":
    loop_principal()
