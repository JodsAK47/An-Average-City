import pygame
from Sistemas.SistemaUI import Botao, TelaBase
from Sistemas.Fontes import obter_fonte
from Sistemas.Recursos import caminho_imagem
from Sistemas.SaveSystem import save_global
from Sistemas.Conquistas import sistema_conquistas
from Entidades.Personagem import personagem
from Gameplay.GeracaoFases import BANCO_INIMIGOS

FUNDO = (14, 18, 22)
PAINEL = (22, 28, 36)
PAINEL_CARD = (30, 38, 48)
VERDE_NEON = (0, 255, 140)
VERDE_ESCURO = (15, 60, 35)
CIANO = (50, 220, 255)
ROXO_NEON = (180, 80, 255)
VERMELHO_ALERTA = (255, 70, 70)
AMARELO_OURO = (255, 215, 60)
TEXTO_CLARO = (240, 245, 250)
TEXTO_CINZA = (150, 165, 180)
BORDA_PAINEL = (45, 60, 75)

CORES_VERSO = {
    "Feiticeiro": (180, 80, 255),
    "Sobrevivente": (0, 255, 140),
    "Agente": (50, 220, 255),
}

class GerenciadorCheatsTela(TelaBase):
    def __init__(self, tela):
        super().__init__(tela, nome="cheats")
        self.tela = tela
        self.fonte_titulo = obter_fonte(18)
        self.fonte_sub = obter_fonte(12)
        self.fonte_botao = obter_fonte(13)
        self.fonte_status = obter_fonte(12)
        self.fonte_mini = obter_fonte(10)
        self.fonte_micro = obter_fonte(9)

        self.modo = "cheats"  # "cheats" ou "seletor_batalha"
        self.voltar_clicado = False
        self.mensagem_feedback = "Terminal de Cheats pronto. Selecione uma função."
        self.cor_feedback = VERDE_NEON

        # === BOTÕES DO MODO CHEATS ===
        self.btn_pontos = Botao(
            60, 138, 390, 38, "+999.999 PONTOS INFINITOS",
            (25, 55, 45), (35, 85, 65), 395, 40,
            cor_texto=VERDE_NEON, fonte_tamanho=12
        )

        self.btn_godmode = Botao(
            60, 182, 390, 38, "GOD MODE: DESATIVADO",
            (50, 30, 60), (75, 40, 95), 395, 40,
            cor_texto=ROXO_NEON, fonte_tamanho=12
        )

        self.btn_conquistas = Botao(
            60, 226, 390, 38, "DESBLOQUEAR TODAS CONQUISTAS",
            (60, 50, 20), (95, 80, 25), 395, 40,
            cor_texto=AMARELO_OURO, fonte_tamanho=12
        )

        self.btn_restaurar = Botao(
            60, 270, 390, 38, "DESATIVAR CHEATS / RESTAURAR",
            (45, 30, 30), (70, 40, 40), 395, 40,
            cor_texto=VERMELHO_ALERTA, fonte_tamanho=12
        )

        self.btn_batalha_custom = Botao(
            60, 332, 390, 44, "⚔️ BATALHA PERSONALIZADA (1-4 INIMIGOS)",
            (20, 60, 75), (35, 105, 130), 395, 46,
            cor_texto=CIANO, fonte_tamanho=12
        )

        self.btn_confinamento = Botao(
            60, 384, 390, 34, "BATALHAR: CONFINAMENTO (ESPECIAL)",
            (50, 45, 20), (90, 80, 30), 395, 36,
            cor_texto=AMARELO_OURO, fonte_tamanho=11
        )

        self.btn_sukuna_boss = Botao(
            60, 424, 390, 34, "BATALHAR: SUKUNA (CHEFE)",
            (60, 20, 30), (105, 30, 45), 395, 36,
            cor_texto=(255, 140, 140), fonte_tamanho=11
        )

        self.btn_killjoy_boss = Botao(
            60, 464, 390, 34, "BATALHAR: ESTRAGA PRAZERES (CHEFE)",
            (20, 45, 60), (30, 80, 105), 395, 36,
            cor_texto=(140, 230, 255), fonte_tamanho=11
        )

        self.btn_voltar = Botao(
            720, 715, 220, 48, "VOLTAR AO MENU",
            (40, 50, 65), (60, 75, 95), 226, 52,
            cor_texto=TEXTO_CLARO, fonte_tamanho=14,
            sprite_base_path="BACK.png", sprite_hover_path="BACK.png", sprite_clique_path="BACK.png"
        )

        # === BOTÕES E ESTADOS DO SELETOR DE BATALHA ===
        self.equipe_selecionada = []  # Lista de templates (máx 4)
        self.filtro_verso = "TODOS"

        self.btn_voltar_seletor = Botao(
            740, 24, 215, 38, "← VOLTAR AOS CHEATS",
            (45, 55, 70), (70, 85, 105), 218, 40,
            cor_texto=TEXTO_CLARO, fonte_tamanho=12
        )

        self.btn_iniciar_batalha_custom = Botao(
            650, 96, 195, 46, "⚔️ INICIAR (0/4)",
            (25, 70, 45), (40, 120, 75), 198, 48,
            cor_texto=VERDE_NEON, fonte_tamanho=13
        )

        self.btn_limpar_equipe = Botao(
            855, 96, 95, 46, "LIMPAR",
            (65, 30, 35), (105, 40, 48), 98, 48,
            cor_texto=VERMELHO_ALERTA, fonte_tamanho=12
        )

        self.botoes_filtros = {
            "TODOS": Botao(50, 196, 175, 28, "TODOS (12)", (30, 38, 48), (45, 60, 75), 178, 30, cor_texto=TEXTO_CLARO, fonte_tamanho=11),
            "Feiticeiro": Botao(235, 196, 140, 28, "FEITICEIRO (4)", (45, 25, 55), (75, 35, 95), 143, 30, cor_texto=ROXO_NEON, fonte_tamanho=11),
            "Sobrevivente": Botao(385, 196, 150, 28, "SOBREVIVENTE (4)", (20, 50, 35), (35, 85, 55), 153, 30, cor_texto=VERDE_NEON, fonte_tamanho=11),
            "Agente": Botao(545, 196, 130, 28, "AGENTE (4)", (20, 45, 60), (30, 80, 105), 133, 30, cor_texto=CIANO, fonte_tamanho=11),
        }

        self.presets_batalha = [
            {"nome": "4x Confinamento", "equipe": ["Confinamento"] * 4},
            {"nome": "3 Chefes", "equipe": ["Sukuna", "Charlie", "Estraga Prazeres"]},
            {"nome": "Trio Agente", "equipe": ["Confinamento", "Torreta", "MaxBot"]},
            {"nome": "Trio Maldições", "equipe": ["Maldição Grau 4", "Maldição Grau 2", "Maldição Grau Especial"]},
        ]
        self.botoes_presets = []
        for idx, pr in enumerate(self.presets_batalha):
            x_pr = 215 + idx * 115
            btn_pr = Botao(x_pr, 154, 108, 24, pr["nome"], (25, 35, 45), (40, 58, 75), 110, 25, cor_texto=CIANO, fonte_tamanho=10)
            self.botoes_presets.append({"dados": pr, "btn": btn_pr})

        # Miniaturas de skins
        self.catalogo_skins = [
            {"nome": "Pixil Clássico", "arquivo": "pixil.png", "desc": "Visual tradicional"},
            {"nome": "Campeão Dourado", "arquivo": "pixil_ouro.png", "desc": "Armadura de Ouro puro"},
            {"nome": "Agente Cibernético", "arquivo": "Cyborg Skin.png", "desc": "Tecnologia de ponta neon"},
            {"nome": "Guerreiro Sombrio", "arquivo": "pixil_sombra.png", "desc": "Energia do Vazio"},
            {"nome": "Sukuna (Chefe)", "arquivo": "Sukuna.png", "desc": "O Rei das Maldições"},
            {"nome": "Maldição Espiritual", "arquivo": "Maldição 4.png", "desc": "Espírito amaldiçoado"},
        ]
        self.miniaturas_skins = {}
        self._carregar_miniaturas_skins()

        # Miniaturas de inimigos
        self.miniaturas_inimigos = {}
        self._carregar_miniaturas_inimigos()

    def resetar(self):
        """Restaura o menu de cheats e todos os seus estados/trapaças para os padrões iniciais."""
        self.modo = "cheats"
        self.voltar_clicado = False
        self.mensagem_feedback = "Terminal de Cheats pronto. Selecione uma função."
        self.cor_feedback = VERDE_NEON
        self.filtro_verso = "TODOS"
        self.equipe_selecionada.clear()

        self.btn_godmode.texto = "GOD MODE: DESATIVADO"
        self.btn_godmode.cor_texto = ROXO_NEON

        self.btn_iniciar_batalha_custom.texto = "⚔️ INICIAR (0/4)"
        self.btn_iniciar_batalha_custom.cor_texto = TEXTO_CINZA
        self.btn_iniciar_batalha_custom.cor_fundo = (35, 45, 55)
        self.btn_iniciar_batalha_custom.cor_hover = (45, 55, 65)

        # Desativa cheats no personagem e restaura skin original
        personagem.resetar(resetar_cheats=True)
        personagem.trocar_skin("pixil.png")

    def _carregar_miniaturas_skins(self):
        for s in self.catalogo_skins:
            try:
                img = pygame.image.load(caminho_imagem(s["arquivo"])).convert_alpha()
                mini = pygame.transform.scale(img, (60, 70))
                grande = pygame.transform.scale(img, (110, 130))
                self.miniaturas_skins[s["arquivo"]] = {"mini": mini, "grande": grande}
            except Exception as e:
                print(f"⚠️ Erro ao carregar miniatura {s['arquivo']}: {e}")

    def _carregar_miniaturas_inimigos(self):
        for tmpl in BANCO_INIMIGOS:
            img_arq = tmpl.get("arquivo_imagem", "Maldição 4.png")
            if img_arq not in self.miniaturas_inimigos:
                try:
                    img = pygame.image.load(caminho_imagem(img_arq)).convert_alpha()
                    mini_card = pygame.transform.scale(img, (42, 46))
                    mini_slot = pygame.transform.scale(img, (32, 34))
                    self.miniaturas_inimigos[img_arq] = {"card": mini_card, "slot": mini_slot}
                except Exception as e:
                    print(f"⚠️ Erro ao carregar miniatura do inimigo {img_arq}: {e}")

    def atualizar_eventos(self, evento, posicao_mouse):
        if self.modo == "cheats":
            return self._atualizar_eventos_cheats(evento, posicao_mouse)
        elif self.modo == "seletor_batalha":
            return self._atualizar_eventos_seletor(evento, posicao_mouse)
        return None

    def _atualizar_eventos_cheats(self, evento, posicao_mouse):
        if self.btn_voltar.checar_clique(evento, posicao_mouse):
            self.voltar_clicado = True
            return "menu"

        if self.btn_batalha_custom.checar_clique(evento, posicao_mouse):
            self.modo = "seletor_batalha"
            self.mensagem_feedback = "Selecione de 1 a 4 inimigos no catálogo para montar sua batalha!"
            self.cor_feedback = CIANO
            return None

        if self.btn_pontos.checar_clique(evento, posicao_mouse):
            save_global.adicionar_pontos(999999)
            self.mensagem_feedback = "✓ +999.999 Pontos adicionados com sucesso ao Save!"
            self.cor_feedback = VERDE_NEON

        if self.btn_godmode.checar_clique(evento, posicao_mouse):
            personagem.god_mode = not getattr(personagem, 'god_mode', False)
            if personagem.god_mode:
                personagem.max_hp = 999
                personagem.hp = 999
                personagem.max_mp = 99
                personagem.mp = 99
                self.btn_godmode.texto = "GOD MODE: ATIVADO (ON)"
                self.btn_godmode.cor_texto = VERDE_NEON
                self.mensagem_feedback = "⚡ MODO DEUS ATIVADO! (Invencível + 999 HP + Mana Infinita)"
                self.cor_feedback = VERDE_NEON
            else:
                personagem.max_hp = 100
                personagem.hp = 100
                personagem.max_mp = 10
                personagem.mp = 0
                self.btn_godmode.texto = "GOD MODE: DESATIVADO"
                self.btn_godmode.cor_texto = ROXO_NEON
                self.mensagem_feedback = "Modo Deus desativado. Vida e mana normalizadas."
                self.cor_feedback = TEXTO_CINZA

        if self.btn_conquistas.checar_clique(evento, posicao_mouse):
            for c in sistema_conquistas.conquistas:
                c.desbloqueada = True
                save_global.desbloquear_conquista(c.id)
            sistema_conquistas.salvar()
            self.mensagem_feedback = "🏆 Todas as 14 conquistas foram desbloqueadas e salvas!"
            self.cor_feedback = AMARELO_OURO

        if self.btn_sukuna_boss.checar_clique(evento, posicao_mouse):
            return ("batalhar_custom", ["Sukuna"])

        if self.btn_killjoy_boss.checar_clique(evento, posicao_mouse):
            return ("batalhar_custom", ["Estraga Prazeres"])

        if self.btn_confinamento.checar_clique(evento, posicao_mouse):
            return ("batalhar_custom", ["Confinamento"])

        if self.btn_restaurar.checar_clique(evento, posicao_mouse):
            self.resetar()
            self.mensagem_feedback = "Padrões restaurados (God Mode desativado e skin padrão aplicada)."
            self.cor_feedback = TEXTO_CLARO

        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            x_ini = 510
            y_ini = 270
            for idx, s in enumerate(self.catalogo_skins):
                col = idx % 2
                lin = idx // 2
                rect_skin = pygame.Rect(x_ini + col * 220, y_ini + lin * 110, 205, 95)
                if rect_skin.collidepoint(posicao_mouse):
                    personagem.trocar_skin(s["arquivo"])
                    from Sistemas.Conquistas import sistema_conquistas
                    sistema_conquistas.desbloquear("moda_em_primeiro_lugar")
                    self.mensagem_feedback = f"🎭 Skin '{s['nome']}' equipada com sucesso!"
                    self.cor_feedback = CIANO

        return None

    def _atualizar_eventos_seletor(self, evento, posicao_mouse):
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                self.modo = "cheats"
                return None
            if evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.equipe_selecionada:
                    nomes = [t["nome"] for t in self.equipe_selecionada]
                    return ("batalhar_custom", nomes)
                else:
                    self.mensagem_feedback = "⚠️ Adicione pelo menos 1 inimigo antes de iniciar a batalha!"
                    self.cor_feedback = VERMELHO_ALERTA
                    return None

        if self.btn_voltar_seletor.checar_clique(evento, posicao_mouse):
            self.modo = "cheats"
            return None

        if self.btn_limpar_equipe.checar_clique(evento, posicao_mouse):
            self.equipe_selecionada.clear()
            self.mensagem_feedback = "Equipe limpa. Selecione de 1 a 4 inimigos abaixo."
            self.cor_feedback = TEXTO_CINZA
            return None

        if self.btn_iniciar_batalha_custom.checar_clique(evento, posicao_mouse):
            if not self.equipe_selecionada:
                self.mensagem_feedback = "⚠️ Adicione pelo menos 1 inimigo à equipe para iniciar a batalha!"
                self.cor_feedback = VERMELHO_ALERTA
                return None
            nomes = [t["nome"] for t in self.equipe_selecionada]
            return ("batalhar_custom", nomes)

        # Filtros
        for chave_filtro, btn_f in self.botoes_filtros.items():
            if btn_f.checar_clique(evento, posicao_mouse):
                self.filtro_verso = chave_filtro
                self.mensagem_feedback = f"Filtro aplicado: {chave_filtro}"
                self.cor_feedback = CIANO
                return None

        # Presets
        for pr_item in self.botoes_presets:
            if pr_item["btn"].checar_clique(evento, posicao_mouse):
                nomes_pr = pr_item["dados"]["equipe"]
                self.equipe_selecionada.clear()
                for n in nomes_pr:
                    tmpl = next((t for t in BANCO_INIMIGOS if t.get("nome") == n), None)
                    if tmpl and len(self.equipe_selecionada) < 4:
                        self.equipe_selecionada.append(tmpl)
                self.mensagem_feedback = f"Preset '{pr_item['dados']['nome']}' carregado com sucesso!"
                self.cor_feedback = VERDE_NEON
                return None

        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            # Checar clique nos slots para remover
            x_ini_slots = 50
            w_slot = 142
            h_slot = 52
            y_slot = 94
            for idx in range(len(self.equipe_selecionada)):
                rect_slot = pygame.Rect(x_ini_slots + idx * (w_slot + 8), y_slot, w_slot, h_slot)
                if rect_slot.collidepoint(posicao_mouse):
                    removido = self.equipe_selecionada.pop(idx)
                    self.mensagem_feedback = f"Inimigo '{removido['nome']}' removido da equipe. ({len(self.equipe_selecionada)}/4)"
                    self.cor_feedback = CIANO
                    return None

            # Checar clique nos cards de inimigos do catálogo
            lista_visivel = BANCO_INIMIGOS
            if self.filtro_verso != "TODOS":
                lista_visivel = [i for i in BANCO_INIMIGOS if i.get("verso") == self.filtro_verso]

            col_w = 220
            row_h = 146
            gap_x = 10
            gap_y = 10
            x_ini = 50
            y_ini = 236

            for idx, tmpl in enumerate(lista_visivel):
                col = idx % 4
                lin = idx // 4
                rect_card = pygame.Rect(x_ini + col * (col_w + gap_x), y_ini + lin * (row_h + gap_y), col_w, row_h)

                if rect_card.collidepoint(posicao_mouse):
                    if len(self.equipe_selecionada) < 4:
                        self.equipe_selecionada.append(tmpl)
                        self.mensagem_feedback = f"✓ '{tmpl['nome']}' adicionado à equipe! ({len(self.equipe_selecionada)}/4 vagas)"
                        self.cor_feedback = VERDE_NEON
                    else:
                        self.mensagem_feedback = "⚠️ Limite máximo de 4 inimigos atingido! Remova um ou inicie a batalha."
                        self.cor_feedback = AMARELO_OURO
                    return None

        return None

    def atualizar(self, posicao_mouse, estado_clique_mouse):
        if self.modo == "cheats":
            self.btn_pontos.atualizar(posicao_mouse, estado_clique_mouse)
            self.btn_godmode.atualizar(posicao_mouse, estado_clique_mouse)
            self.btn_conquistas.atualizar(posicao_mouse, estado_clique_mouse)
            self.btn_restaurar.atualizar(posicao_mouse, estado_clique_mouse)
            self.btn_batalha_custom.atualizar(posicao_mouse, estado_clique_mouse)
            self.btn_confinamento.atualizar(posicao_mouse, estado_clique_mouse)
            self.btn_sukuna_boss.atualizar(posicao_mouse, estado_clique_mouse)
            self.btn_killjoy_boss.atualizar(posicao_mouse, estado_clique_mouse)
            self.btn_voltar.atualizar(posicao_mouse, estado_clique_mouse)

            if getattr(personagem, 'god_mode', False):
                self.btn_godmode.texto = "GOD MODE: ATIVADO (ON)"
                self.btn_godmode.cor_texto = VERDE_NEON
            else:
                self.btn_godmode.texto = "GOD MODE: DESATIVADO"
                self.btn_godmode.cor_texto = ROXO_NEON

        elif self.modo == "seletor_batalha":
            self.btn_voltar_seletor.atualizar(posicao_mouse, estado_clique_mouse)
            self.btn_limpar_equipe.atualizar(posicao_mouse, estado_clique_mouse)

            qtd = len(self.equipe_selecionada)
            self.btn_iniciar_batalha_custom.texto = f"⚔️ INICIAR ({qtd}/4)"
            if qtd > 0:
                self.btn_iniciar_batalha_custom.cor_texto = VERDE_NEON
                self.btn_iniciar_batalha_custom.cor_fundo = (25, 75, 50)
                self.btn_iniciar_batalha_custom.cor_hover = (40, 130, 80)
            else:
                self.btn_iniciar_batalha_custom.cor_texto = TEXTO_CINZA
                self.btn_iniciar_batalha_custom.cor_fundo = (35, 45, 55)
                self.btn_iniciar_batalha_custom.cor_hover = (45, 55, 65)

            self.btn_iniciar_batalha_custom.atualizar(posicao_mouse, estado_clique_mouse)

            for btn_f in self.botoes_filtros.values():
                btn_f.atualizar(posicao_mouse, estado_clique_mouse)

            for pr_item in self.botoes_presets:
                pr_item["btn"].atualizar(posicao_mouse, estado_clique_mouse)

    def desenhar(self):
        self.tela.fill(FUNDO)
        if self.modo == "cheats":
            self._desenhar_cheats()
        elif self.modo == "seletor_batalha":
            self._desenhar_seletor_batalha()

    def _desenhar_cheats(self):
        # Cabeçalho
        pygame.draw.rect(self.tela, PAINEL, (40, 20, 920, 60), border_radius=8)
        pygame.draw.rect(self.tela, VERDE_NEON, (40, 20, 920, 60), width=2, border_radius=8)

        txt_tit = self.fonte_titulo.render("SEWER ACCESS // CONSOLE DE CHEATS", True, VERDE_NEON)
        txt_sub = self.fonte_mini.render("MODELO DE TESTE // PAINEL DE CONTROLE", True, CIANO)
        self.tela.blit(txt_tit, (60, 28))
        self.tela.blit(txt_sub, (60, 56))

        # Painel Esquerdo
        rect_painel_esq = pygame.Rect(40, 100, 430, 595)
        pygame.draw.rect(self.tela, PAINEL, rect_painel_esq, border_radius=8)
        pygame.draw.rect(self.tela, BORDA_PAINEL, rect_painel_esq, width=2, border_radius=8)

        lbl_sec1 = self.fonte_status.render("TRAPAÇAS GERAIS", True, VERDE_NEON)
        self.tela.blit(lbl_sec1, (60, 115))

        self.btn_pontos.desenhar(self.tela)
        self.btn_godmode.desenhar(self.tela)
        self.btn_conquistas.desenhar(self.tela)
        self.btn_restaurar.desenhar(self.tela)

        lbl_sec_arena = self.fonte_status.render("ARENA & BATALHAS PERSONALIZADAS", True, CIANO)
        self.tela.blit(lbl_sec_arena, (60, 314))

        self.btn_batalha_custom.desenhar(self.tela)
        self.btn_confinamento.desenhar(self.tela)
        self.btn_sukuna_boss.desenhar(self.tela)
        self.btn_killjoy_boss.desenhar(self.tela)

        # Caixa de status do sistema
        retangulo_caixa_status = pygame.Rect(60, 506, 390, 174)
        pygame.draw.rect(self.tela, (18, 22, 28), retangulo_caixa_status, border_radius=6)
        pygame.draw.rect(self.tela, BORDA_PAINEL, retangulo_caixa_status, width=1, border_radius=6)

        lbl_stats = self.fonte_sub.render("STATUS ATUAL DO SISTEMA:", True, CIANO)
        self.tela.blit(lbl_stats, (75, 514))

        gm_ativo = getattr(personagem, 'god_mode', False)
        txt_gm = "ATIVADO (Imortal)" if gm_ativo else "Desativado"
        cor_gm = VERDE_NEON if gm_ativo else TEXTO_CINZA

        linhas_info = [
            (f"• Pontos Salvos: {save_global.obter_pontos()}", VERDE_NEON),
            (f"• Conquistas: {sistema_conquistas.total_desbloqueadas()}/{sistema_conquistas.total_conquistas()}", AMARELO_OURO),
            (f"• Vida Atual: {personagem.hp}/{personagem.max_hp}", VERMELHO_ALERTA if not gm_ativo else VERDE_NEON),
            (f"• Mana Atual: {personagem.mp}/{personagem.max_mp}", CIANO),
            (f"• Modo Deus: {txt_gm}", cor_gm),
            (f"• Member Card: {'Ativo' if save_global.tem_member_card() else 'Indisponível'}", VERDE_NEON if save_global.tem_member_card() else VERMELHO_ALERTA),
            (f"• Skin Equipada: {getattr(personagem, 'nome_imagem', 'pixil.png')}", ROXO_NEON),
        ]

        y_lin = 534
        for texto, cor in linhas_info:
            surf_info = self.fonte_mini.render(texto, True, cor)
            self.tela.blit(surf_info, (75, y_lin))
            y_lin += 20

        # Painel Direito (Skins)
        rect_painel_dir = pygame.Rect(490, 100, 470, 595)
        pygame.draw.rect(self.tela, PAINEL, rect_painel_dir, border_radius=8)
        pygame.draw.rect(self.tela, BORDA_PAINEL, rect_painel_dir, width=2, border_radius=8)

        lbl_sec2 = self.fonte_status.render("ARMÁRIO DE SKINS DO PERSONAGEM", True, CIANO)
        self.tela.blit(lbl_sec2, (510, 115))

        quadro_previo = pygame.Rect(510, 145, 100, 110)
        pygame.draw.rect(self.tela, (18, 22, 28), quadro_previo, border_radius=8)
        pygame.draw.rect(self.tela, CIANO, quadro_previo, width=2, border_radius=8)

        skin_atual = getattr(personagem, 'nome_imagem', 'pixil.png')
        if skin_atual in self.miniaturas_skins:
            superficie_previa = self.miniaturas_skins[skin_atual]["grande"]
            superficie_previa_pequena = pygame.transform.scale(superficie_previa, (80, 95))
            self.tela.blit(superficie_previa_pequena, (quadro_previo.x + 10, quadro_previo.y + 7))

        txt_previa_nome = self.fonte_status.render("EQUIPADA AGORA:", True, TEXTO_CINZA)
        self.tela.blit(txt_previa_nome, (625, 160))
        nome_skin_amigavel = skin_atual
        for s in self.catalogo_skins:
            if s["arquivo"] == skin_atual:
                nome_skin_amigavel = s["nome"]
                break
        txt_skin_lbl = self.fonte_botao.render(nome_skin_amigavel, True, VERDE_NEON)
        self.tela.blit(txt_skin_lbl, (625, 185))
        txt_dica_skin = self.fonte_mini.render("Clique em qualquer skin abaixo para vestir:", True, TEXTO_CINZA)
        self.tela.blit(txt_dica_skin, (625, 218))

        x_ini = 510
        y_ini = 270
        for idx, s in enumerate(self.catalogo_skins):
            col = idx % 2
            lin = idx // 2
            rect_skin = pygame.Rect(x_ini + col * 225, y_ini + lin * 115, 215, 102)

            esta_equipada = (skin_atual == s["arquivo"])
            cor_bg = (30, 42, 54) if esta_equipada else (20, 25, 34)
            cor_borda = VERDE_NEON if esta_equipada else BORDA_PAINEL
            largura_b = 2 if esta_equipada else 1

            pygame.draw.rect(self.tela, cor_bg, rect_skin, border_radius=8)
            pygame.draw.rect(self.tela, cor_borda, rect_skin, width=largura_b, border_radius=8)

            if s["arquivo"] in self.miniaturas_skins:
                mini = self.miniaturas_skins[s["arquivo"]]["mini"]
                self.tela.blit(mini, (rect_skin.x + 8, rect_skin.y + 16))

            cor_titulo_s = VERDE_NEON if esta_equipada else TEXTO_CLARO
            txt_n = self.fonte_sub.render(s["nome"], True, cor_titulo_s)
            self.tela.blit(txt_n, (rect_skin.x + 72, rect_skin.y + 16))

            txt_d = self.fonte_mini.render(s["desc"], True, TEXTO_CINZA)
            self.tela.blit(txt_d, (rect_skin.x + 72, rect_skin.y + 40))

            if esta_equipada:
                txt_eq = self.fonte_mini.render("● EM USO", True, VERDE_NEON)
                self.tela.blit(txt_eq, (rect_skin.x + 72, rect_skin.y + 68))
            else:
                txt_eq = self.fonte_mini.render("[ USAR ]", True, CIANO)
                self.tela.blit(txt_eq, (rect_skin.x + 72, rect_skin.y + 68))

        # Barra inferior
        pygame.draw.rect(self.tela, (18, 24, 32), (40, 710, 660, 58), border_radius=6)
        pygame.draw.rect(self.tela, BORDA_PAINEL, (40, 710, 660, 58), width=1, border_radius=6)

        txt_prompt = self.fonte_mini.render("> CONSOLE:", True, CIANO)
        self.tela.blit(txt_prompt, (55, 718))

        surf_fb = self.fonte_sub.render(self.mensagem_feedback, True, self.cor_feedback)
        self.tela.blit(surf_fb, (55, 738))

        self.btn_voltar.desenhar(self.tela)

    def _desenhar_seletor_batalha(self):
        # 1. Cabeçalho Superior
        pygame.draw.rect(self.tela, PAINEL, (40, 15, 920, 56), border_radius=8)
        pygame.draw.rect(self.tela, CIANO, (40, 15, 920, 56), width=2, border_radius=8)

        txt_tit = self.fonte_titulo.render("SIMULADOR DE COMBATE // ARENA PERSONALIZADA", True, CIANO)
        txt_sub = self.fonte_mini.render("Escolha qualquer inimigo do jogo e monte equipes de 1 a 4 oponentes simultâneos!", True, TEXTO_CINZA)
        self.tela.blit(txt_tit, (55, 23))
        self.tela.blit(txt_sub, (55, 48))

        self.btn_voltar_seletor.desenhar(self.tela)

        # 2. Painel da Equipe Selecionada (Topo)
        rect_painel_equipe = pygame.Rect(40, 78, 920, 108)
        pygame.draw.rect(self.tela, PAINEL, rect_painel_equipe, border_radius=8)
        pygame.draw.rect(self.tela, BORDA_PAINEL, rect_painel_equipe, width=1, border_radius=8)

        txt_lbl_eq = self.fonte_status.render(f"EQUIPE INIMIGA SELECIONADA: {len(self.equipe_selecionada)} / 4 VAGAS", True, VERDE_NEON)
        self.tela.blit(txt_lbl_eq, (55, 82))

        # 4 Slots de Equipe
        x_ini_slots = 50
        w_slot = 142
        h_slot = 52
        y_slot = 98

        for i in range(4):
            rect_s = pygame.Rect(x_ini_slots + i * (w_slot + 8), y_slot, w_slot, h_slot)
            if i < len(self.equipe_selecionada):
                tmpl = self.equipe_selecionada[i]
                verso = tmpl.get("verso", "Agente")
                cor_v = CORES_VERSO.get(verso, CIANO)

                pygame.draw.rect(self.tela, (26, 34, 46), rect_s, border_radius=6)
                pygame.draw.rect(self.tela, cor_v, rect_s, width=2, border_radius=6)

                img_arq = tmpl.get("arquivo_imagem", "Maldição 4.png")
                if img_arq in self.miniaturas_inimigos:
                    mini = self.miniaturas_inimigos[img_arq]["slot"]
                    self.tela.blit(mini, (rect_s.x + 5, rect_s.y + 8))

                txt_n = self.fonte_mini.render(tmpl["nome"][:12], True, TEXTO_CLARO)
                self.tela.blit(txt_n, (rect_s.x + 40, rect_s.y + 6))

                txt_hp = self.fonte_micro.render(f"HP: {tmpl.get('max_hp', 30)}", True, AMARELO_OURO)
                self.tela.blit(txt_hp, (rect_s.x + 40, rect_s.y + 22))

                txt_v = self.fonte_micro.render(verso[:9], True, cor_v)
                self.tela.blit(txt_v, (rect_s.x + 40, rect_s.y + 36))

                # Ícone de remover [X]
                txt_x = self.fonte_micro.render("✕", True, VERMELHO_ALERTA)
                self.tela.blit(txt_x, (rect_s.right - 12, rect_s.top + 4))
            else:
                pygame.draw.rect(self.tela, (18, 24, 32), rect_s, border_radius=6)
                pygame.draw.rect(self.tela, (40, 50, 65), rect_s, width=1, border_radius=6)
                txt_vazio = self.fonte_mini.render(f"+ Vago #{i+1}", True, (90, 105, 125))
                self.tela.blit(txt_vazio, (rect_s.x + (w_slot - txt_vazio.get_width()) // 2, rect_s.y + 18))

        # Ações da equipe (Iniciar / Limpar)
        self.btn_iniciar_batalha_custom.desenhar(self.tela)
        self.btn_limpar_equipe.desenhar(self.tela)

        # Linha de presets rápidos
        txt_presets_lbl = self.fonte_micro.render("PRESETS RÁPIDOS:", True, TEXTO_CINZA)
        self.tela.blit(txt_presets_lbl, (55, 159))

        for pr_item in self.botoes_presets:
            pr_item["btn"].desenhar(self.tela)

        # 3. Barra de Filtros
        pygame.draw.rect(self.tela, (18, 22, 28), (40, 192, 920, 36), border_radius=6)
        pygame.draw.rect(self.tela, BORDA_PAINEL, (40, 192, 920, 36), width=1, border_radius=6)

        for chave_f, btn_f in self.botoes_filtros.items():
            if self.filtro_verso == chave_f:
                btn_f.cor_texto = AMARELO_OURO
                btn_f.cor_borda = AMARELO_OURO
            else:
                btn_f.cor_texto = TEXTO_CLARO
                btn_f.cor_borda = None
            btn_f.desenhar(self.tela)

        txt_dica_adicionar = self.fonte_mini.render("Dica: Clique no card do inimigo para adicioná-lo à equipe (máx 4).", True, CIANO)
        self.tela.blit(txt_dica_adicionar, (685, 202))

        # 4. Grade de Inimigos (Roster de 12 templates)
        lista_visivel = BANCO_INIMIGOS
        if self.filtro_verso != "TODOS":
            lista_visivel = [i for i in BANCO_INIMIGOS if i.get("verso") == self.filtro_verso]

        col_w = 220
        row_h = 146
        gap_x = 10
        gap_y = 10
        x_ini = 50
        y_ini = 236

        pos_mouse = pygame.mouse.get_pos()

        for idx, tmpl in enumerate(lista_visivel):
            col = idx % 4
            lin = idx // 4
            rx = x_ini + col * (col_w + gap_x)
            ry = y_ini + lin * (row_h + gap_y)
            rect_card = pygame.Rect(rx, ry, col_w, row_h)

            verso = tmpl.get("verso", "Agente")
            cor_v = CORES_VERSO.get(verso, CIANO)
            tipo = tmpl.get("tipo", "comum").capitalize()

            hover = rect_card.collidepoint(pos_mouse)
            cor_bg = (32, 42, 56) if hover else (22, 28, 38)
            cor_borda = cor_v if hover else (50, 65, 80)
            esp_borda = 2 if hover else 1

            pygame.draw.rect(self.tela, cor_bg, rect_card, border_radius=8)
            pygame.draw.rect(self.tela, cor_borda, rect_card, width=esp_borda, border_radius=8)

            # Miniatura
            img_arq = tmpl.get("arquivo_imagem", "Maldição 4.png")
            if img_arq in self.miniaturas_inimigos:
                mini = self.miniaturas_inimigos[img_arq]["card"]
                self.tela.blit(mini, (rect_card.x + 8, rect_card.y + 10))

            # Nome
            cor_nome = AMARELO_OURO if tmpl.get("tipo") == "chefe" else TEXTO_CLARO
            txt_n = self.fonte_sub.render(tmpl["nome"], True, cor_nome)
            self.tela.blit(txt_n, (rect_card.x + 56, rect_card.y + 8))

            # Verso e Tipo
            txt_tag = self.fonte_micro.render(f"{verso} • {tipo}", True, cor_v)
            self.tela.blit(txt_tag, (rect_card.x + 56, rect_card.y + 26))

            # Atributos principais
            attrs = tmpl.get("atributos", {})
            agi = attrs.get("Agi", 1)
            forca = attrs.get("For", 1)
            hp_txt = f"HP: {tmpl.get('max_hp', 20)} | MP: {tmpl.get('max_mp', 0)} | Agi: {agi}"
            txt_stats = self.fonte_micro.render(hp_txt, True, TEXTO_CINZA)
            self.tela.blit(txt_stats, (rect_card.x + 10, rect_card.y + 60))

            # Habilidade de destaque
            ataques = tmpl.get("ataques", ["Soco"])
            atk_preview = ", ".join(ataques[:2])
            txt_atks = self.fonte_micro.render(f"Golpes: {atk_preview[:28]}", True, (130, 145, 160))
            self.tela.blit(txt_atks, (rect_card.x + 10, rect_card.y + 78))

            # Badge especial
            if tmpl.get("nome") == "Confinamento":
                pygame.draw.rect(self.tela, (70, 50, 15), (rect_card.x + 10, rect_card.y + 96, 200, 16), border_radius=3)
                txt_esp = self.fonte_micro.render("⚡ Stun em Área após 5 rodadas", True, AMARELO_OURO)
                self.tela.blit(txt_esp, (rect_card.x + 16, rect_card.y + 97))
            elif tmpl.get("tipo") == "chefe":
                pygame.draw.rect(self.tela, (65, 20, 25), (rect_card.x + 10, rect_card.y + 96, 200, 16), border_radius=3)
                txt_esp = self.fonte_micro.render("👑 Chefe Supremo com Mecânica de Fase", True, (255, 140, 140))
                self.tela.blit(txt_esp, (rect_card.x + 16, rect_card.y + 97))
            else:
                pygame.draw.rect(self.tela, (20, 30, 42), (rect_card.x + 10, rect_card.y + 96, 200, 16), border_radius=3)
                txt_esp = self.fonte_micro.render(f"XP Concedido: {tmpl.get('xp', 20)} pts", True, CIANO)
                self.tela.blit(txt_esp, (rect_card.x + 16, rect_card.y + 97))

            # Botão adicionar no rodapé do card
            equipe_cheia = len(self.equipe_selecionada) >= 4
            btn_add_rect = pygame.Rect(rect_card.x + 10, rect_card.y + 118, 200, 22)
            cor_btn_add = (35, 45, 55) if equipe_cheia else ((30, 85, 55) if hover else (22, 55, 38))
            cor_txt_add = TEXTO_CINZA if equipe_cheia else VERDE_NEON

            pygame.draw.rect(self.tela, cor_btn_add, btn_add_rect, border_radius=4)
            pygame.draw.rect(self.tela, (45, 75, 60) if not equipe_cheia else BORDA_PAINEL, btn_add_rect, width=1, border_radius=4)

            lbl_btn_add = "+ ADICIONAR À EQUIPE" if not equipe_cheia else "EQUIPE CHEIA (4/4)"
            txt_btn_add = self.fonte_micro.render(lbl_btn_add, True, cor_txt_add)
            self.tela.blit(txt_btn_add, (btn_add_rect.x + (200 - txt_btn_add.get_width()) // 2, btn_add_rect.y + 4))

        # 5. Barra Inferior de Feedback e Atalhos
        pygame.draw.rect(self.tela, (18, 24, 32), (40, 710, 920, 58), border_radius=6)
        pygame.draw.rect(self.tela, BORDA_PAINEL, (40, 710, 920, 58), width=1, border_radius=6)

        txt_prompt = self.fonte_mini.render("> CONSOLE:", True, CIANO)
        self.tela.blit(txt_prompt, (55, 718))

        surf_fb = self.fonte_sub.render(self.mensagem_feedback, True, self.cor_feedback)
        self.tela.blit(surf_fb, (55, 738))

        txt_atalhos = self.fonte_mini.render("[ENTER] Iniciar Batalha  •  [ESC] Voltar aos Cheats", True, TEXTO_CINZA)
        self.tela.blit(txt_atalhos, (640, 728))
