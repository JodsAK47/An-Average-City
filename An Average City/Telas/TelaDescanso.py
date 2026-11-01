import pygame
from Sistemas.SistemaUI import Botao, TelaBase, desenhar_painel_container
from Entidades.Personagem import personagem
from Sistemas.Fontes import obter_fonte
from Sistemas.Inventario import inventario_global, carregar_sprite_item, eh_arte_placeholder, obter_arquivo_imagem_item
from Sistemas.Conquistas import sistema_conquistas

class TelaDescanso(TelaBase):
    def __init__(self, tela):
        super().__init__(tela, nome="descanso")
        self.tela = tela
        self.largura = tela.get_width()
        self.altura = tela.get_height()
        self.jogadores = [personagem]
        self.jogador_selecionado = 0
        self.slot_selecionado = None
        self.mensagem = "Selecione um espaco."

        self.fonte_titulo = obter_fonte(28)
        self.fonte_secao = obter_fonte(16)
        self.fonte_texto = obter_fonte(14)
        self.fonte_menor = obter_fonte(10)

        botoes = []
        for indice, atributo in enumerate(("For", "Agi", "Con", "Sab", "Int", "Sor")):
            botao = Botao(890, 195 + indice * 44, 36, 32, "+",
                          (35, 125, 75), (65, 190, 105), 36, 32,
                          cor_texto=(255, 255, 255), fonte_tamanho=14)
            botoes.append((botao, atributo))
        self.botoes_up = botoes
        self.btn_continuar = Botao(self.largura - 260, 715, 220, 48, "CONTINUAR",
                                   (70, 90, 115), (105, 130, 160), 220, 48,
                                   cor_texto=(255, 255, 255), fonte_tamanho=14)

        self.btn_melhorar_equip = Botao(68, 235, 205, 54, "MELHORAR",
                                        (59, 68, 88), (82, 94, 115), 205, 54,
                                        cor_texto=(255, 255, 255), fonte_tamanho=14)

        self.btn_pausa = Botao(self.largura - 175, 35, 125, 38, "⏸ MENU", (48, 57, 75), (70, 85, 110), 125, 38, cor_texto=(235, 240, 250), fonte_tamanho=12)
        self.abas_jogadores = []
        self.notificacao_popup = None
        self.notificacao_visivel = False
        self.btn_fechar_popup = None
        self.posicao_mouse = (0, 0)
        self.ultimo_slot_clicado = None
        self.tempo_ultimo_clique = 0
        self.intervalo_duplo_clique = 400

    def definir_popup_notificacao(self, dados_resultado):
        if not dados_resultado:
            self.notificacao_popup = None
            self.notificacao_visivel = False
            return

        cura = dados_resultado.get("cura", {})
        itens = dados_resultado.get("itens", [])
        mensagem = dados_resultado.get("mensagem", "Batalha encerrada.")

        contagem_itens = {}
        for item in itens:
            contagem_itens[item] = contagem_itens.get(item, 0) + 1

        lista_itens_formatada = []
        for nome_item, qtd in contagem_itens.items():
            if qtd > 1:
                lista_itens_formatada.append(f"{nome_item} x{qtd}")
            else:
                lista_itens_formatada.append(nome_item)

        hp_curado = cura.get("hp", 0)
        mp_curado = cura.get("mp", 0)

        if hp_curado > 0 or mp_curado > 0:
            texto_cura = f"+{hp_curado} HP  |  +{mp_curado} PM"
        else:
            texto_cura = "+30% HP  |  +3 PM (HP Máximo)"

        self.notificacao_popup = {
            "texto_cura": texto_cura,
            "itens": lista_itens_formatada,
            "hp_curado": hp_curado,
            "mp_curado": mp_curado,
            "mensagem": mensagem,
        }
        self.notificacao_visivel = True

    def _retangulos_slots(self):
        inventario = [pygame.Rect(345 + coluna * 68, 220 + linha * 60, 60, 48)
                      for linha in range(4) for coluna in range(4)]
        equipamentos = [pygame.Rect(688 + coluna * 62, 535 + linha * 62, 52, 48)
                        for linha in range(2) for coluna in range(4)]
        return inventario, equipamentos

    def atualizar_eventos(self, evento, posicao_mouse):
        if evento.type == pygame.KEYDOWN and evento.key in (pygame.K_ESCAPE, pygame.K_p):
            return "pausa"

        if self.btn_pausa.checar_clique(evento, posicao_mouse):
            return "pausa"

        if self.notificacao_visivel and self.btn_fechar_popup and evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            if self.btn_fechar_popup.collidepoint(posicao_mouse):
                self.notificacao_visivel = False
                return None

        if self.btn_continuar.checar_clique(evento, posicao_mouse):
            self.notificacao_visivel = False
            return "continuar"

        if self.btn_melhorar_equip.checar_clique(evento, posicao_mouse):
            alvo_eq = inventario_global.obter_equipamento_alvo()
            custo = inventario_global.custo_melhoria(alvo_eq)
            if alvo_eq and inventario_global.materiais_totais() >= custo:
                inventario_global.consumir_materiais(custo)
                alvo_eq.melhorar()
                self.mensagem = f"{alvo_eq.nome} melhorado!"
                sistema_conquistas.desbloquear("ferreiro")
            else:
                self.mensagem = "Materiais insuficientes!"
            return None


        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            for indice, aba in enumerate(self.abas_jogadores):
                if aba.collidepoint(posicao_mouse):
                    self.jogador_selecionado = indice
                    self.slot_selecionado = None
                    self.ultimo_slot_clicado = None
                    self.mensagem = "Jogador selecionado."
                    return None

            inventario, equipamentos = self._retangulos_slots()
            itens_do_inventario = inventario_global.itens_do_inventario()
            agora = pygame.time.get_ticks()

            for indice, slot in enumerate(inventario + equipamentos):
                if slot.collidepoint(posicao_mouse):
                    eh_duplo_clique = (
                        self.ultimo_slot_clicado == indice
                        and (agora - self.tempo_ultimo_clique) <= self.intervalo_duplo_clique
                    )
                    self.tempo_ultimo_clique = agora
                    self.ultimo_slot_clicado = indice if not eh_duplo_clique else None
                    self.slot_selecionado = indice

                    # Slot da Mochila (Inventário)
                    if indice < len(inventario):
                        if indice >= len(itens_do_inventario):
                            self.mensagem = "Espaço vazio na mochila."
                            return None

                        item = itens_do_inventario[indice]
                        jogador = self.jogadores[self.jogador_selecionado] if self.jogadores else personagem
                        tipo_item = getattr(item, "tipo", None)

                        # 1 CLIQUE: Apenas seleciona e exibe a descrição
                        if not eh_duplo_clique:
                            if tipo_item == "equipamento":
                                inventario_global.equipamento_selecionado = item
                                bonus_str = ", ".join(f"+{v} {k}" for k, v in item.atributos_bonus.items() if v > 0)
                                polido_str = " [Polido]" if getattr(item, "polido", False) else ""
                                cat = getattr(item, "categoria", "arma").capitalize()
                                desc_str = f": {bonus_str}" if bonus_str else ""
                                self.mensagem = f"{item.nome} (+{item.nivel - 1}){polido_str} [{cat}]{desc_str} (2 cliques para equipar)"
                            elif tipo_item == "material":
                                self.mensagem = f"{item.nome}: {item.descricao} (Usado no painel de Criação)"
                            elif tipo_item == "bilhete" or getattr(item, "nome", "") == "Bilhete do Dormitório":
                                self.mensagem = f"Bilhete do Dormitório: possui {item.quantidade}. Gasta 1 para descansar e curar na seleção de caminhos."
                            elif tipo_item == "polidor" or getattr(item, "nome", "") == "Polidor de Itens":
                                self.mensagem = f"Polidor de Itens: possui {item.quantidade}. (2 cliques para usar no equipamento selecionado)"
                            else:
                                # Consumível
                                desc = getattr(item, "descricao", "")
                                efeitos = []
                                rec_hp = getattr(item, "rec_hp", 0)
                                rec_mp = getattr(item, "rec_mp", 0)
                                if rec_hp > 0:
                                    efeitos.append(f"+{rec_hp} HP")
                                if rec_mp > 0:
                                    efeitos.append(f"+{rec_mp} PM")
                                ef_txt = f" ({', '.join(efeitos)})" if efeitos else ""
                                self.mensagem = f"{item.nome}{ef_txt}: {desc} (2 cliques para consumir)"
                            return None

                        # 2 CLIQUES: Equipa ou consome o item
                        if tipo_item == "equipamento":
                            if inventario_global.equipar(item):
                                self.mensagem = f"✓ Equipou {item.nome}!"
                            else:
                                self.mensagem = f"Não é possível equipar {item.nome} (máx. 3 amuletos sem repetir)!"
                        elif tipo_item == "polidor" or getattr(item, "nome", "") == "Polidor de Itens":
                            alvo_eq = inventario_global.obter_equipamento_alvo()
                            if inventario_global.usar_polidor_itens(alvo_eq):
                                nome_alvo = alvo_eq.nome if alvo_eq else "equipamento"
                                self.mensagem = f"✓ Usou {item.nome}! Efeito de {nome_alvo} dobrado!"
                            else:
                                self.mensagem = "Nenhum equipamento selecionado para polir!"
                        elif tipo_item == "material":
                            self.mensagem = f"{item.nome}: Guardado no inventário. Use o botão 'MELHORAR' para aprimorar equipamentos."
                        elif tipo_item == "bilhete" or getattr(item, "nome", "") == "Bilhete do Dormitório":
                            self.mensagem = f"Bilhete do Dormitório: Usado ao escolher 'Dormitório' na seleção de caminhos."
                        elif getattr(item, "quantidade", 0) > 0:
                            item.usar(jogador)
                            self.mensagem = f"✓ Usou {item.nome}!"
                            if item.quantidade <= 0 and item in inventario_global.consumiveis:
                                inventario_global.consumiveis.remove(item)
                        return None

                    # Slot de Equipamento Equipado
                    else:
                        eq_idx = indice - len(inventario)
                        slots_eq = inventario_global.obter_slots_equipamento()
                        if 0 <= eq_idx < len(slots_eq):
                            rotulo_slot, eq = slots_eq[eq_idx]
                            if eq is None:
                                self.mensagem = f"Slot {rotulo_slot} vazio."
                                return None

                            # 1 CLIQUE: Seleciona e exibe descrição
                            if not eh_duplo_clique:
                                inventario_global.equipamento_selecionado = eq
                                bonus_str = ", ".join(f"+{v} {k}" for k, v in eq.atributos_bonus.items() if v > 0)
                                polido_str = " [Polido]" if getattr(eq, "polido", False) else ""
                                cat = getattr(eq, "categoria", "arma").capitalize()
                                desc_str = f": {bonus_str}" if bonus_str else ""
                                self.mensagem = f"{eq.nome} (+{eq.nivel - 1}){polido_str} [Equipado - {cat}]{desc_str} (2 cliques para desequipar)"
                                return None

                            # 2 CLIQUES: Desequipa o item
                            nome_eq = eq.nome
                            if inventario_global.desequipar(eq):
                                self.mensagem = f"✓ Desequipou {nome_eq}!"
                                self.slot_selecionado = None
                            else:
                                self.mensagem = f"Não foi possível desequipar {nome_eq}."
                        return None

        if self.jogador_selecionado >= len(self.jogadores):
            self.jogador_selecionado = 0

        jogador = self.jogadores[self.jogador_selecionado] if self.jogadores else personagem
        if getattr(jogador, 'pontos_atributo', 0) > 0:
            for botao_atributo, atributo in self.botoes_up:
                if botao_atributo.checar_clique(evento, posicao_mouse):
                    jogador.atributos[atributo] += 1
                    jogador.pontos_atributo -= 1

                    if atributo == "Con":
                        jogador.max_hp += 10
                        jogador.hp += 10
                    elif atributo == "Sab":
                        jogador.max_mp += 2
                        jogador.mp += 2
                    self.mensagem = f"{atributo} aumentado."
        return None

    def atualizar(self, posicao_mouse, estado_clique_mouse):
        self.posicao_mouse = posicao_mouse
        self.btn_pausa.atualizar(posicao_mouse, estado_clique_mouse)
        self.btn_continuar.atualizar(posicao_mouse, estado_clique_mouse)
        self.btn_melhorar_equip.atualizar(posicao_mouse, estado_clique_mouse)
        for botao_atributo, atributo in self.botoes_up:
            botao_atributo.atualizar(posicao_mouse, estado_clique_mouse)

    def desenhar(self, posicao_mouse=None):
        self.tela.fill((25, 30, 42))
        desenhar_painel_container(self.tela, (24, 24, self.largura - 48, self.altura - 48), "painel_base.png", fallback_cor=(38, 46, 62), margem=16)
        self.tela.blit(self.fonte_titulo.render("DESCANSO", True, (240, 220, 150)), (48, 42))

        self.btn_pausa.desenhar(self.tela)
        self.abas_jogadores = []
        for indice, jogador in enumerate(self.jogadores):
            rect = pygame.Rect(300 + indice * 135, 38, 120, 34)
            self.abas_jogadores.append(rect)
            cor = (75, 110, 145) if indice == self.jogador_selecionado else (55, 62, 78)
            pygame.draw.rect(self.tela, cor, rect)
            texto = self.fonte_menor.render(f"JOGADOR {indice + 1}", True, (235, 235, 235))
            self.tela.blit(texto, texto.get_rect(center=rect.center))

        paineis = (pygame.Rect(48, 110, 245, 565), pygame.Rect(315, 110, 335, 565), pygame.Rect(672, 110, 280, 565))
        sprites_paineis = ("painel_detalhes.png", "painel_base.png", "painel_detalhes.png")
        for painel, sprite_p in zip(paineis, sprites_paineis):
            desenhar_painel_container(self.tela, painel, sprite_p, fallback_cor=(48, 57, 75), borda_cor=(91, 103, 126), margem=14)

        self.tela.blit(self.fonte_secao.render("CRIACAO", True, (235, 220, 170)), (68, 132))
        self.tela.blit(self.fonte_menor.render("Receitas e materiais", True, (170, 180, 195)), (68, 163))
        if self.jogador_selecionado >= len(self.jogadores):
            self.jogador_selecionado = 0
        jogador = self.jogadores[self.jogador_selecionado] if self.jogadores else personagem
        self.tela.blit(self.fonte_secao.render("STATUS", True, (235, 220, 170)), (68, 188))
        self.tela.blit(self.fonte_menor.render(
            f"HP: {int(jogador.hp)}/{int(jogador.max_hp)}    PM: {int(jogador.mp)}/{int(jogador.max_mp)}",
            True, (170, 220, 255)), (68, 210))
        eq_alvo = inventario_global.obter_equipamento_alvo()
        custo = inventario_global.custo_melhoria(eq_alvo)
        mats = inventario_global.materiais_totais()

        pos_mouse = posicao_mouse if posicao_mouse is not None else self.posicao_mouse
        item_hovered = None

        y_attr = 320
        if eq_alvo:
            self.btn_melhorar_equip.texto = f"MELHORAR ({custo} MAT)"
            self.btn_melhorar_equip.desenhar(self.tela)
            sufixo_polido = " [Polido]" if getattr(eq_alvo, "polido", False) else ""

            # Card com sprite do equipamento alvo
            card_eq = pygame.Rect(68, 296, 205, 46)
            desenhar_painel_container(self.tela, card_eq, "painel_ouro.png", fallback_cor=(34, 42, 58), borda_cor=(255, 215, 60), margem=8)

            sprite_alvo = carregar_sprite_item(eq_alvo, tamanho=(36, 36))
            self.tela.blit(sprite_alvo, (card_eq.x + 5, card_eq.y + 5))

            nome_curto = eq_alvo.nome if len(eq_alvo.nome) <= 12 else eq_alvo.nome[:11] + "..."
            self.tela.blit(self.fonte_menor.render(f"{nome_curto} +{eq_alvo.nivel-1}{sufixo_polido}", True, (255, 215, 0)), (card_eq.x + 46, card_eq.y + 6))
            cat_alvo = getattr(eq_alvo, "categoria", "arma").capitalize()
            self.tela.blit(self.fonte_menor.render(f"Tipo: {cat_alvo}", True, (160, 180, 205)), (card_eq.x + 46, card_eq.y + 24))

            y_attr = 352
            for k, v in eq_alvo.atributos_bonus.items():
                if v > 0:
                    self.tela.blit(self.fonte_menor.render(f"+{v} {k}", True, (150, 255, 150)), (68, y_attr))
                    y_attr += 18
        self.tela.blit(self.fonte_menor.render(f"Materiais disp.: {mats}", True, (200, 200, 200)), (68, y_attr + 12 if eq_alvo else 300))

        self.tela.blit(self.fonte_secao.render("INVENTARIO", True, (235, 220, 170)), (338, 132))
        self.tela.blit(self.fonte_menor.render("Itens carregados", True, (170, 180, 195)), (338, 163))
        inventario, equipamentos = self._retangulos_slots()
        itens_do_inventario = inventario_global.itens_do_inventario()

        for indice, slot in enumerate(inventario):
            selecionado = (self.slot_selecionado == indice)
            hover = slot.collidepoint(pos_mouse)

            if selecionado:
                cor_fundo = (58, 75, 102)
                cor_borda = (255, 215, 60)
                borda_w = 2
            elif hover:
                cor_fundo = (46, 56, 76)
                cor_borda = (145, 175, 215)
                borda_w = 2
            else:
                cor_fundo = (34, 40, 54)
                cor_borda = (65, 78, 102)
                borda_w = 1

            sprite_slot = "painel_ouro.png" if selecionado else "painel_card.png"
            desenhar_painel_container(self.tela, slot, sprite_slot, fallback_cor=cor_fundo, borda_cor=cor_borda, margem=6)
            if hover and not selecionado:
                pygame.draw.rect(self.tela, (145, 175, 215), slot, width=1, border_radius=4)

            if indice < len(itens_do_inventario):
                item = itens_do_inventario[indice]
                if hover:
                    item_hovered = item

                # Renderiza sprite do item ou placeholder
                sprite = carregar_sprite_item(item, tamanho=(34, 34))
                self.tela.blit(sprite, (slot.centerx - 17, slot.centery - 17))

                # Quantidade de itens empilháveis
                qtd = getattr(item, "quantidade", 1)
                if qtd > 1:
                    txt_qtd = f"x{qtd}"
                    surf_sombra = self.fonte_menor.render(txt_qtd, True, (0, 0, 0))
                    surf_qtd = self.fonte_menor.render(txt_qtd, True, (255, 240, 200))
                    qx = slot.right - surf_qtd.get_width() - 3
                    qy = slot.bottom - surf_qtd.get_height() - 2
                    self.tela.blit(surf_sombra, (qx + 1, qy + 1))
                    self.tela.blit(surf_qtd, (qx, qy))
                elif getattr(item, "tipo", None) == "equipamento":
                    lvl = getattr(item, "nivel", 1) - 1
                    if lvl > 0:
                        txt_lvl = f"+{lvl}"
                        surf_s = self.fonte_menor.render(txt_lvl, True, (0, 0, 0))
                        surf_lvl = self.fonte_menor.render(txt_lvl, True, (130, 255, 140))
                        lx = slot.right - surf_lvl.get_width() - 3
                        ly = slot.bottom - surf_lvl.get_height() - 2
                        self.tela.blit(surf_s, (lx + 1, ly + 1))
                        self.tela.blit(surf_lvl, (lx, ly))

        self.tela.blit(self.fonte_menor.render(self.mensagem, True, (170, 180, 195)), (338, 505))
        bilhetes = inventario_global.obter_bilhetes_dormitorio()
        self.tela.blit(self.fonte_menor.render(f"Bilhetes de Dormitório: {bilhetes}", True, (255, 215, 120)), (338, 535))

        if self.jogador_selecionado >= len(self.jogadores):
            self.jogador_selecionado = 0
        self.tela.blit(self.fonte_secao.render("ATRIBUTOS", True, (235, 220, 170)), (696, 132))
        self.tela.blit(self.fonte_menor.render(f"Nivel {getattr(jogador, 'nivel', 1)}", True, (180, 190, 205)), (696, 163))
        chaves = ["For", "Agi", "Con", "Sab", "Int", "Sor"]
        nomes = ["Forca", "Agilidade", "Constituicao", "Sabedoria", "Intelecto", "Sorte"]
        for indice, (chave, nome) in enumerate(zip(chaves, nomes)):
            y = 195 + indice * 44
            pygame.draw.rect(self.tela, (59, 68, 88), (696, y, 185, 32))
            valor_base = jogador.atributos.get(chave, 1)
            bonus_eq = inventario_global.obter_bonus_atributo(chave)
            texto_attr = f"{nome}: {valor_base + bonus_eq}" + (f" (+{bonus_eq})" if bonus_eq > 0 else "")
            self.tela.blit(self.fonte_menor.render(texto_attr, True, (235, 235, 235)), (708, y + 9))
            if getattr(jogador, 'pontos_atributo', 0) > 0:
                self.botoes_up[indice][0].desenhar(self.tela)
        pontos = getattr(jogador, 'pontos_atributo', 0)
        self.tela.blit(self.fonte_menor.render(f"Pontos disponiveis: {pontos}", True, (130, 230, 155)), (696, 468))
        self.tela.blit(self.fonte_secao.render("EQUIPAMENTOS", True, (235, 220, 170)), (696, 512))
        slots_eq = inventario_global.obter_slots_equipamento()

        for indice, slot in enumerate(equipamentos):
            slot_indice = len(inventario) + indice
            selecionado = (self.slot_selecionado == slot_indice)
            hover = slot.collidepoint(pos_mouse)

            if selecionado:
                cor_fundo = (58, 75, 102)
                cor_borda = (255, 215, 60)
                borda_w = 2
            elif hover:
                cor_fundo = (46, 56, 76)
                cor_borda = (145, 175, 215)
                borda_w = 2
            else:
                cor_fundo = (34, 40, 54)
                cor_borda = (65, 78, 102)
                borda_w = 1

            sprite_slot = "painel_ouro.png" if selecionado else "painel_card.png"
            desenhar_painel_container(self.tela, slot, sprite_slot, fallback_cor=cor_fundo, borda_cor=cor_borda, margem=6)
            if hover and not selecionado:
                pygame.draw.rect(self.tela, (145, 175, 215), slot, width=1, border_radius=4)

            if indice < len(slots_eq):
                rotulo_slot, eq = slots_eq[indice]
                if eq is not None:
                    if hover:
                        item_hovered = eq

                    # Sprite do equipamento
                    sprite_eq = carregar_sprite_item(eq, tamanho=(34, 34))
                    self.tela.blit(sprite_eq, (slot.centerx - 17, slot.centery - 17))

                    # Nível
                    lvl = getattr(eq, "nivel", 1) - 1
                    if lvl > 0:
                        txt_lvl = f"+{lvl}"
                        surf_s = self.fonte_menor.render(txt_lvl, True, (0, 0, 0))
                        surf_lvl = self.fonte_menor.render(txt_lvl, True, (130, 255, 140))
                        lx = slot.right - surf_lvl.get_width() - 3
                        ly = slot.bottom - surf_lvl.get_height() - 2
                        self.tela.blit(surf_s, (lx + 1, ly + 1))
                        self.tela.blit(surf_lvl, (lx, ly))

                    if getattr(eq, "polido", False):
                        surf_star = self.fonte_menor.render("★", True, (255, 220, 60))
                        self.tela.blit(surf_star, (slot.x + 3, slot.y + 1))
                else:
                    rot_abrev = rotulo_slot[:3].upper() if len(rotulo_slot) > 3 else rotulo_slot.upper()
                    surf_rot = self.fonte_menor.render(rot_abrev, True, (80, 95, 118))
                    self.tela.blit(surf_rot, surf_rot.get_rect(center=slot.center))

        self.btn_continuar.desenhar(self.tela)

        # Renderização do tooltip do item sob o mouse
        if item_hovered and not getattr(self, "notificacao_visivel", False):
            self._desenhar_tooltip_item(item_hovered, pos_mouse)

        if self.notificacao_visivel and self.notificacao_popup:
            self._desenhar_overlay_notificacao()

    def _desenhar_tooltip_item(self, item, posicao_mouse):
        if not item:
            return

        nome = getattr(item, "nome", "Item")
        eh_ph = eh_arte_placeholder(item)
        categoria = getattr(item, "categoria", getattr(item, "tipo", "Item")).capitalize()

        linhas = []
        if getattr(item, "tipo", None) == "equipamento":
            bonus = getattr(item, "atributos_bonus", {})
            bonus_str = ", ".join(f"+{v} {k}" for k, v in bonus.items() if v > 0)
            if bonus_str:
                linhas.append(f"Bonus: {bonus_str}")
            lvl = getattr(item, "nivel", 1) - 1
            if lvl > 0:
                linhas.append(f"Melhoria: +{lvl}")
            if getattr(item, "polido", False):
                linhas.append("Polido: Dobro de efeito")
        elif getattr(item, "tipo", None) == "consumivel" or hasattr(item, "rec_hp"):
            rec_hp = getattr(item, "rec_hp", 0)
            rec_mp = getattr(item, "rec_mp", 0)
            if rec_hp > 0:
                linhas.append(f"Recupera: +{rec_hp} HP")
            if rec_mp > 0:
                linhas.append(f"Recupera: +{rec_mp} PM")

        desc = getattr(item, "descricao", "")
        if desc and desc != "Selecione um espaco.":
            palavras = desc.split()
            atual = ""
            for p in palavras:
                cand = f"{atual} {p}".strip()
                if len(cand) > 28:
                    linhas.append(atual)
                    atual = p
                else:
                    atual = cand
            if atual:
                linhas.append(atual)

        # Dica de duplo clique
        if getattr(item, "tipo", None) == "equipamento":
            esta_equipado = any(item is eq for _, eq in inventario_global.obter_slots_equipamento())
            dica_txt = "Dica: 2 cliques para desequipar" if esta_equipado else "Dica: 2 cliques para equipar"
            linhas.append(dica_txt)
        elif getattr(item, "tipo", None) == "consumivel" or hasattr(item, "rec_hp"):
            linhas.append("Dica: 2 cliques para consumir")

        tag_arte = "Arte: [Oficial]" if not eh_ph else "Arte: [Provisória (Placeholder)]"
        cor_arte = (100, 230, 140) if not eh_ph else (255, 180, 80)

        largura_tt = 220
        altura_tt = 48 + (len(linhas) * 16) + 18
        mx, my = posicao_mouse
        x_tt = mx + 16
        y_tt = my + 16
        if x_tt + largura_tt > self.largura - 10:
            x_tt = mx - largura_tt - 12
        if y_tt + altura_tt > self.altura - 10:
            y_tt = my - altura_tt - 12

        surf_tt = pygame.Surface((largura_tt, altura_tt), pygame.SRCALPHA)
        surf_tt.fill((20, 26, 38, 245))
        pygame.draw.rect(surf_tt, (70, 95, 135), (0, 0, largura_tt, altura_tt), width=1, border_radius=6)

        sprite_tt = carregar_sprite_item(item, tamanho=(26, 26))
        surf_tt.blit(sprite_tt, (8, 8))

        txt_nome = self.fonte_menor.render(nome[:18], True, (255, 220, 110))
        surf_tt.blit(txt_nome, (38, 7))
        txt_cat = self.fonte_menor.render(f"Tipo: {categoria}", True, (160, 180, 205))
        surf_tt.blit(txt_cat, (38, 23))

        y_l = 42
        for l in linhas:
            txt_l = self.fonte_menor.render(l, True, (220, 225, 235))
            surf_tt.blit(txt_l, (8, y_l))
            y_l += 16

        txt_art = self.fonte_menor.render(tag_arte, True, cor_arte)
        surf_tt.blit(txt_art, (8, y_l + 2))

        self.tela.blit(surf_tt, (x_tt, y_tt))

    def _desenhar_overlay_notificacao(self):
        dados = self.notificacao_popup
        if not dados:
            return

        itens = dados.get("itens", [])
        num_linhas_itens = max(1, len(itens))

        largura_popup = 285
        altura_popup = 74 + (num_linhas_itens * 18)

        x = self.largura - largura_popup - 24
        y = 16

        desenhar_painel_container(self.tela, (x, y, largura_popup, altura_popup), "painel_retorno.png", fallback_cor=(22, 28, 42), borda_cor=(76, 175, 120), margem=10)
        pygame.draw.rect(self.tela, (40, 85, 60), (x + 4, y + 4, largura_popup - 8, 20), border_radius=4)

        txt_titulo = self.fonte_menor.render("FIM DA BATALHA", True, (255, 220, 130))
        self.tela.blit(txt_titulo, (x + 10, y + 6))

        self.btn_fechar_popup = pygame.Rect(x + largura_popup - 22, y + 4, 18, 18)
        txt_x = self.fonte_menor.render("x", True, (210, 210, 210))
        self.tela.blit(txt_x, (self.btn_fechar_popup.x + 4, self.btn_fechar_popup.y + 1))

        msg_texto = dados.get("mensagem", "Batalha encerrada.")
        txt_msg = self.fonte_menor.render(msg_texto, True, (255, 235, 160))
        self.tela.blit(txt_msg, (x + 10, y + 28))

        txt_cura_label = self.fonte_menor.render("Cura obtida:", True, (160, 220, 180))
        self.tela.blit(txt_cura_label, (x + 10, y + 48))
        txt_cura_val = self.fonte_menor.render(dados.get("texto_cura", "+30% HP / +3 PM"), True, (130, 255, 160))
        self.tela.blit(txt_cura_val, (x + 100, y + 48))

        txt_itens_label = self.fonte_menor.render("Itens obtidos:", True, (255, 215, 120))
        self.tela.blit(txt_itens_label, (x + 10, y + 68))

        y_item = y + 86
        if itens:
            for item in itens:
                nome_limpo = item.split(" x")[0] if " x" in item else item
                sprite_drop = carregar_sprite_item(nome_limpo, tamanho=(16, 16))
                self.tela.blit(sprite_drop, (x + 16, y_item))
                txt_item = self.fonte_menor.render(f"{item}", True, (240, 240, 240))
                self.tela.blit(txt_item, (x + 36, y_item))
                y_item += 18
        else:
            txt_vazio = self.fonte_menor.render("- Nenhum item obtido", True, (170, 180, 195))
            self.tela.blit(txt_vazio, (x + 20, y_item))

GerenciadorPosLuta = TelaDescanso
