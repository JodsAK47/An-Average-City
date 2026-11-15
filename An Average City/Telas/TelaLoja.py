import pygame
from Sistemas.Fontes import obter_fonte
from Sistemas.SistemaUI import Botao, TelaBase
from Sistemas.Inventario import inventario_global, carregar_sprite_item
from Entidades.Personagem import personagem


class GerenciadorLoja(TelaBase):
    def __init__(self, tela):
        super().__init__(tela, nome="loja")
        self.tela = tela
        self.largura = tela.get_width()
        self.altura = tela.get_height()

        self.fonte_titulo = obter_fonte(26)
        self.fonte_subtitulo = obter_fonte(14)
        self.fonte_item_nome = obter_fonte(15)
        self.fonte_desc = obter_fonte(12)
        self.fonte_preco = obter_fonte(13)
        self.fonte_status = obter_fonte(14)

        self.tipo_loja = "barista"  # "barista" ou "perigo"
        self.sucesso_evento = True
        self.mensagem_feedback = ""
        self.cor_feedback = (100, 255, 140)
        self.tempo_feedback = 0

        self.itens_catalogo = []
        self.botoes_compra = []
        self.botoes_venda = []
        self.aba_perigo = "comprar"  # "comprar" ou "vender"

        largura_sair = 240
        altura_sair = 46
        x_sair = (self.largura - largura_sair) // 2
        y_sair = self.altura - 75
        self.btn_sair = Botao(
            x_sair, y_sair, largura_sair, altura_sair,
            "SAIR DA LOJA",
            (70, 90, 115), (105, 130, 160),
            largura_sair, altura_sair,
            cor_texto=(255, 255, 255), fonte_tamanho=14
        )

        largura_aba = 350
        altura_aba = 34
        self.btn_aba_comprar = Botao(
            135, 100, largura_aba, altura_aba,
            "🛒 COMPRAR EQUIPAMENTOS & ITENS",
            (50, 65, 90), (75, 95, 130),
            largura_aba, altura_aba,
            cor_texto=(255, 255, 255), fonte_tamanho=13
        )
        self.btn_aba_vender = Botao(
            515, 100, largura_aba, altura_aba,
            "💰 VENDER EQUIPAMENTOS DO PERSONAGEM",
            (50, 65, 90), (75, 95, 130),
            largura_aba, altura_aba,
            cor_texto=(255, 255, 255), fonte_tamanho=13
        )

        self.configurar_loja("barista", sucesso=True)

    def configurar_loja(self, tipo_loja="barista", sucesso=True):
        self.tipo_loja = "perigo" if "perigo" in str(tipo_loja).lower() else "barista"
        self.sucesso_evento = bool(sucesso)
        self.mensagem_feedback = ""
        self.tempo_feedback = 0
        self.aba_perigo = "comprar"

        desconto = 1 if self.sucesso_evento else 0

        if self.tipo_loja == "barista":
            self.titulo_tela = "CAFÉ & PROVISÕES DO BARISTA ☕"
            self.subtitulo_tela = (
                "Visita segura ao balcão! Mantimentos e café de primeira qualidade garantidos."
            )
            self.cor_tema = (80, 195, 140)

            custo_marmita = max(1, 2 - desconto)
            custo_bilhete = max(1, 2 - desconto)
            custo_equip = max(1, 2 - desconto)

            self.itens_catalogo = [
                {
                    "id": "cafe",
                    "nome": "Café Expresso Revigorante",
                    "tag": "[CONSUMÍVEL]",
                    "desc": "Café quente e aromático. Restaura 35 HP e 10 MP.",
                    "custo_tipo": "materiais",
                    "custo": 1,
                    "limite": 3,
                    "comprados": 0,
                },
                {
                    "id": "pocao_vida",
                    "nome": "Poção de Vida Reforçada",
                    "tag": "[CONSUMÍVEL]",
                    "desc": "Tônico medicinal caseiro. Restaura 50 HP instantaneamente.",
                    "custo_tipo": "materiais",
                    "custo": 1,
                    "limite": 3,
                    "comprados": 0,
                },
                {
                    "id": "cha_mana",
                    "nome": "Chá de Mana Concentrado",
                    "tag": "[CONSUMÍVEL]",
                    "desc": "Infusão mística aromática. Restaura 20 MP no combate.",
                    "custo_tipo": "materiais",
                    "custo": 1,
                    "limite": 3,
                    "comprados": 0,
                },
                {
                    "id": "marmita",
                    "nome": "Marmita Nutritiva Especial",
                    "tag": "[ESPECIAL]",
                    "desc": "Refeição completa: cura 40 HP e concede +1 Con permanente!",
                    "custo_tipo": "materiais",
                    "custo": custo_marmita,
                    "limite": 1,
                    "comprados": 0,
                },
                {
                    "id": "bilhete",
                    "nome": "Bilhete do Dormitório",
                    "tag": "[SERVIÇO]",
                    "desc": "Passe seguro para dormir e se recuperar totalmente no alojamento.",
                    "custo_tipo": "materiais",
                    "custo": custo_bilhete,
                    "limite": 2,
                    "comprados": 0,
                },
                {
                    "id": "equip_barista",
                    "nome": "Peça de Proteção do Barista",
                    "tag": "[EQUIPAMENTO]",
                    "desc": "Equipamento defensivo para encarar os perigos da cidade.",
                    "custo_tipo": "materiais",
                    "custo": custo_equip,
                    "limite": 2,
                    "comprados": 0,
                },
            ]
        else:
            self.titulo_tela = "MERCADO CLANDESTINO DO PERIGO ☠️"
            self.subtitulo_tela = (
                "Você passou no teste! Compre armas, armaduras e equipamentos ou venda seus itens por Sucatas."
                if self.sucesso_evento
                else "Contrabando fora dos registros."
            )
            self.cor_tema = (225, 95, 95)

            custo_arma = max(2, 3 - desconto)
            custo_amuleto = max(1, 2 - desconto)
            custo_polidor = max(1, 2 - desconto)
            custo_forja = max(1, 2 - desconto)
            custo_equip = max(1, 2 - desconto)

            self.itens_catalogo = [
                {
                    "id": "arma_clandestina",
                    "nome": "Arma Contrabandeada",
                    "tag": "[ARMA RARA]",
                    "desc": "Arma modificada no mercado negro com bônus ofensivo superior (+3).",
                    "custo_tipo": "materiais",
                    "custo": custo_arma,
                    "limite": 2,
                    "comprados": 0,
                },
                {
                    "id": "amuleto_sombras",
                    "nome": "Amuleto das Sombras",
                    "tag": "[AMULETO]",
                    "desc": "Relíquia obscura que concede bônus místicos aleatórios.",
                    "custo_tipo": "materiais",
                    "custo": custo_amuleto,
                    "limite": 2,
                    "comprados": 0,
                },
                {
                    "id": "polidor",
                    "nome": "Polidor de Equipamentos",
                    "tag": "[ITEM]",
                    "desc": "Polidor para refinar e potencializar equipamentos equipados.",
                    "custo_tipo": "materiais",
                    "custo": custo_polidor,
                    "limite": 2,
                    "comprados": 0,
                },
                {
                    "id": "armadura_clandestina",
                    "nome": "Armadura Clandestina",
                    "tag": "[ARMADURA RARA]",
                    "desc": "Peça de armadura do mercado negro (Capacete, Peitoral, Calça ou Bota com bônus).",
                    "custo_tipo": "materiais",
                    "custo": custo_forja,
                    "limite": 2,
                    "comprados": 0,
                },
                {
                    "id": "pacto_sangue",
                    "nome": "Pacto de Sangue (+3 Sucatas)",
                    "tag": "[SACRIFÍCIO]",
                    "desc": "Sacrifique 15 HP da sua vida em troca de 3 Sucatas de metal!",
                    "custo_tipo": "hp",
                    "custo": 15,
                    "limite": 3,
                    "comprados": 0,
                },
                {
                    "id": "equip_perigo",
                    "nome": "Equipamento Misterioso Clandestino",
                    "tag": "[EQUIPAMENTO]",
                    "desc": "Equipamento aleatório de alto potencial de combate.",
                    "custo_tipo": "materiais",
                    "custo": custo_equip,
                    "limite": 2,
                    "comprados": 0,
                },
            ]

        self._gerar_botoes()
        self._gerar_botoes_venda()

    def _gerar_botoes(self):
        self.botoes_compra = []
        largura_card = 280
        altura_card = 210
        margem_x = 55
        espaco_x = 35
        margem_y = 195 if self.tipo_loja == "perigo" else 180
        espaco_y = 30

        for idx, item in enumerate(self.itens_catalogo):
            col = idx % 3
            row = idx // 3
            cx = margem_x + col * (largura_card + espaco_x)
            cy = margem_y + row * (altura_card + espaco_y)

            card_rect = pygame.Rect(cx, cy, largura_card, altura_card)
            btn_w = 200
            btn_h = 34
            btn_x = cx + (largura_card - btn_w) // 2
            btn_y = cy + altura_card - 44

            btn = Botao(
                btn_x, btn_y, btn_w, btn_h,
                "COMPRAR",
                (45, 110, 75), (65, 155, 105),
                btn_w, btn_h,
                cor_texto=(255, 255, 255), fonte_tamanho=12
            )
            self.botoes_compra.append({
                "item": item,
                "card_rect": card_rect,
                "botao": btn,
            })

    def _obter_equipamentos_vendiveis(self):
        lista = []
        # Equipamentos na mochila
        for eq in getattr(inventario_global, "equipamentos_inventario", []):
            valor = max(1, getattr(eq, "nivel", 1))
            lista.append({"eq": eq, "equipado": False, "dono": None, "valor": valor})
        # Equipamentos equipados por qualquer jogador (P1 ou P2)
        for eq in inventario_global.todos_equipamentos_equipados(incluir_todos=True):
            valor = max(1, getattr(eq, "nivel", 1))
            dono = inventario_global.obter_dono_equipamento(eq)
            lista.append({"eq": eq, "equipado": True, "dono": dono, "valor": valor})
        return lista

    def _gerar_botoes_venda(self):
        self.botoes_venda = []
        equipamentos = self._obter_equipamentos_vendiveis()

        largura_card = 280
        altura_card = 210
        margem_x = 55
        espaco_x = 35
        margem_y = 195
        espaco_y = 30

        for idx, item_venda in enumerate(equipamentos[:6]):
            col = idx % 3
            row = idx // 3
            cx = margem_x + col * (largura_card + espaco_x)
            cy = margem_y + row * (altura_card + espaco_y)

            card_rect = pygame.Rect(cx, cy, largura_card, altura_card)
            btn_w = 210
            btn_h = 34
            btn_x = cx + (largura_card - btn_w) // 2
            btn_y = cy + altura_card - 44

            val = item_venda["valor"]
            txt_btn = f"VENDER (+{val} SUCATA)" if val == 1 else f"VENDER (+{val} SUCATAS)"
            btn = Botao(
                btn_x, btn_y, btn_w, btn_h,
                txt_btn,
                (45, 115, 65), (65, 160, 95),
                btn_w, btn_h,
                cor_texto=(255, 255, 255), fonte_tamanho=12
            )
            self.botoes_venda.append({
                "item_venda": item_venda,
                "card_rect": card_rect,
                "botao": btn,
            })

    def _executar_compra(self, item):
        if item["comprados"] >= item["limite"]:
            self.mensagem_feedback = f"⚠️ {item['nome']} esgotado!"
            self.cor_feedback = (255, 180, 80)
            self.tempo_feedback = 120
            return False

        if item["custo_tipo"] == "materiais":
            custo = item["custo"]
            if inventario_global.materiais_totais() < custo:
                self.mensagem_feedback = f"❌ Sucatas insuficientes! Requer {custo} Sucatas."
                self.cor_feedback = (255, 95, 95)
                self.tempo_feedback = 120
                return False
            inventario_global.consumir_materiais(custo)
        elif item["custo_tipo"] == "hp":
            custo_hp = item["custo"]
            if personagem.hp <= custo_hp:
                self.mensagem_feedback = f"❌ Vida insuficiente para o sacrifício! (Precisa de mais que {custo_hp} HP)"
                self.cor_feedback = (255, 95, 95)
                self.tempo_feedback = 120
                return False
            personagem.hp -= custo_hp

        item_id = item["id"]
        mensagem_custom = None
        if item_id == "cafe":
            inventario_global.adicionar_consumivel("Café Expresso", "Restaura 35 HP e 10 MP.", 35, 10)
        elif item_id == "pocao_vida":
            inventario_global.adicionar_consumivel("Poção de Vida Reforçada", "Restaura 50 HP.", 50, 0)
        elif item_id == "cha_mana":
            inventario_global.adicionar_consumivel("Chá de Mana", "Restaura 20 MP.", 0, 20)
        elif item_id == "marmita":
            alvos = getattr(self, "jogadores", None) or [personagem]
            for jog in alvos:
                if jog is not None:
                    jog.hp = min(jog.max_hp, jog.hp + 40)
                    jog.atributos["Con"] = int(jog.atributos.get("Con", 1)) + 1
        elif item_id == "bilhete":
            inventario_global.adicionar_bilhete_dormitorio(1)
        elif item_id == "equip_barista":
            novo_eq = inventario_global.gerar_equipamento_aleatorio()
            inventario_global.adicionar_equipamento(novo_eq, auto_equipar=False)
        elif item_id == "arma_clandestina":
            novo_eq = inventario_global.gerar_equipamento_aleatorio(categoria="arma")
            for k in novo_eq.atributos_bonus:
                novo_eq.atributos_bonus[k] += 1
            inventario_global.adicionar_equipamento(novo_eq, auto_equipar=True)
            mensagem_custom = f"✓ Comprou {novo_eq.nome} (+{novo_eq.nivel-1}) com sucesso!"
        elif item_id == "armadura_clandestina":
            import random
            cat_armadura = random.choice(["capacete", "peitoral", "calca", "bota"])
            novo_eq = inventario_global.gerar_equipamento_aleatorio(categoria=cat_armadura)
            for k in novo_eq.atributos_bonus:
                novo_eq.atributos_bonus[k] += 1
            inventario_global.adicionar_equipamento(novo_eq, auto_equipar=True)
            mensagem_custom = f"✓ Comprou {novo_eq.nome} ({cat_armadura.upper()}) com sucesso!"
        elif item_id == "amuleto_sombras":
            novo_eq = inventario_global.gerar_equipamento_aleatorio(categoria="amuleto")
            for k in novo_eq.atributos_bonus:
                novo_eq.atributos_bonus[k] += 1
            inventario_global.adicionar_equipamento(novo_eq, auto_equipar=True)
            mensagem_custom = f"✓ Comprou {novo_eq.nome} com sucesso!"
        elif item_id == "polidor":
            inventario_global.adicionar_polidor_itens(1)
        elif item_id == "pacto_sangue":
            inventario_global.adicionar_sucata(3)
        elif item_id == "equip_perigo":
            novo_eq = inventario_global.gerar_equipamento_aleatorio()
            inventario_global.adicionar_equipamento(novo_eq, auto_equipar=True)
            mensagem_custom = f"✓ Comprou {novo_eq.nome} ({getattr(novo_eq, 'categoria', 'Item').upper()}) com sucesso!"

        item["comprados"] += 1
        self.mensagem_feedback = mensagem_custom or f"✓ Comprou {item['nome']} com sucesso!"
        self.cor_feedback = (100, 255, 140)
        self.tempo_feedback = 120
        self._gerar_botoes_venda()
        return True

    def _executar_venda(self, item_venda):
        eq = item_venda["eq"]
        valor = item_venda["valor"]

        if item_venda["equipado"]:
            inventario_global.desequipar(eq, jogador=item_venda.get("dono"))
            if eq in inventario_global.equipamentos_inventario:
                inventario_global.equipamentos_inventario.remove(eq)
        else:
            if eq in inventario_global.equipamentos_inventario:
                inventario_global.equipamentos_inventario.remove(eq)

        inventario_global.adicionar_sucata(valor)
        self.mensagem_feedback = f"✓ Vendeu {eq.nome} para o Perigo por +{valor} Sucatas!"
        self.cor_feedback = (100, 255, 140)
        self.tempo_feedback = 120
        self._gerar_botoes_venda()
        return True

    def atualizar_eventos(self, evento, posicao_mouse):
        if self.btn_sair.checar_clique(evento, posicao_mouse):
            return "continuar"

        if self.tipo_loja == "perigo":
            if self.btn_aba_comprar.checar_clique(evento, posicao_mouse):
                self.aba_perigo = "comprar"
                return None
            if self.btn_aba_vender.checar_clique(evento, posicao_mouse):
                self.aba_perigo = "vender"
                self._gerar_botoes_venda()
                return None

        if self.tipo_loja != "perigo" or self.aba_perigo == "comprar":
            for entrada in self.botoes_compra:
                if entrada["botao"].checar_clique(evento, posicao_mouse):
                    self._executar_compra(entrada["item"])
                    break
        else:
            for entrada in self.botoes_venda:
                if entrada["botao"].checar_clique(evento, posicao_mouse):
                    self._executar_venda(entrada["item_venda"])
                    break

        return None

    def atualizar(self, posicao_mouse, estado_clique_mouse):
        self.btn_sair.atualizar(posicao_mouse, estado_clique_mouse)
        if self.tempo_feedback > 0:
            self.tempo_feedback -= 1

        if self.tipo_loja == "perigo":
            if self.aba_perigo == "comprar":
                self.btn_aba_comprar.cor_normal = (70, 95, 140)
                self.btn_aba_comprar.cor_hover = (95, 125, 175)
                self.btn_aba_vender.cor_normal = (40, 48, 62)
                self.btn_aba_vender.cor_hover = (55, 68, 88)
            else:
                self.btn_aba_comprar.cor_normal = (40, 48, 62)
                self.btn_aba_comprar.cor_hover = (55, 68, 88)
                self.btn_aba_vender.cor_normal = (55, 125, 75)
                self.btn_aba_vender.cor_hover = (75, 165, 105)

            self.btn_aba_comprar.atualizar(posicao_mouse, estado_clique_mouse)
            self.btn_aba_vender.atualizar(posicao_mouse, estado_clique_mouse)

        if self.tipo_loja != "perigo" or self.aba_perigo == "comprar":
            for entrada in self.botoes_compra:
                item = entrada["item"]
                btn = entrada["botao"]
                esgotado = item["comprados"] >= item["limite"]
                if esgotado:
                    btn.definir_texto("ESGOTADO")
                    btn.definir_cores(cor_base=(55, 55, 65), cor_hover=(55, 55, 65))
                else:
                    custo = item["custo"]
                    tipo_c = item["custo_tipo"]
                    if tipo_c == "materiais":
                        pode = inventario_global.materiais_totais() >= custo
                        btn.definir_texto(f"COMPRAR ({custo} SUCATA)" if custo == 1 else f"COMPRAR ({custo} SUCATAS)")
                    else:
                        pode = personagem.hp > custo
                        btn.definir_texto(f"COMPRAR (-{custo} HP)")

                    if pode:
                        btn.definir_cores(cor_base=(45, 110, 75), cor_hover=(65, 155, 105))
                    else:
                        btn.definir_cores(cor_base=(95, 50, 50), cor_hover=(125, 65, 65))
                btn.atualizar(posicao_mouse, estado_clique_mouse)
        else:
            for entrada in self.botoes_venda:
                entrada["botao"].atualizar(posicao_mouse, estado_clique_mouse)

    def desenhar(self, posicao_mouse=None):
        self.tela.fill((16, 20, 28))

        # Cabeçalho da loja
        txt_tit = self.fonte_titulo.render(self.titulo_tela, True, self.cor_tema)
        self.tela.blit(txt_tit, (55, 25))

        txt_sub = self.fonte_subtitulo.render(self.subtitulo_tela, True, (185, 195, 215))
        self.tela.blit(txt_sub, (55, 65))

        # Abas na Loja do Perigo (Comprar / Vender)
        if self.tipo_loja == "perigo":
            self.btn_aba_comprar.desenhar(self.tela)
            self.btn_aba_vender.desenhar(self.tela)

        # Barra de status e moedas do jogador
        mats = inventario_global.materiais_totais()
        bilh = inventario_global.obter_bilhetes_dormitorio()
        poli = inventario_global.obter_polidores_itens()
        hp_max = getattr(personagem, "max_hp", 100)
        hp_atual = getattr(personagem, "hp", 100)
        mp_max = getattr(personagem, "max_mp", 10)
        mp_atual = getattr(personagem, "mp", 10)

        y_bar = 145 if self.tipo_loja == "perigo" else 105
        status_str = f"🔩 Sucatas: {mats}   |   ❤️ HP: {hp_atual}/{hp_max}   |   💧 MP: {mp_atual}/{mp_max}   |   🎫 Bilhetes: {bilh}   |   ✨ Polidores: {poli}"
        pygame.draw.rect(self.tela, (28, 35, 48), (55, y_bar, self.largura - 110, 32), border_radius=8)
        pygame.draw.rect(self.tela, (55, 70, 95), (55, y_bar, self.largura - 110, 32), width=1, border_radius=8)
        txt_st = self.fonte_status.render(status_str, True, (245, 235, 185))
        self.tela.blit(txt_st, txt_st.get_rect(center=(self.largura // 2, y_bar + 16)))

        # Mensagem de feedback
        if self.tempo_feedback > 0 and self.mensagem_feedback:
            y_fb = y_bar + 40
            txt_fb = self.fonte_subtitulo.render(self.mensagem_feedback, True, self.cor_feedback)
            self.tela.blit(txt_fb, txt_fb.get_rect(center=(self.largura // 2, y_fb)))

        # Conteúdo da aba Comprar
        if self.tipo_loja != "perigo" or self.aba_perigo == "comprar":
            for entrada in self.botoes_compra:
                item = entrada["item"]
                rect = entrada["card_rect"]
                esgotado = item["comprados"] >= item["limite"]

                fundo = (22, 28, 38) if not esgotado else (20, 22, 26)
                borda = self.cor_tema if not esgotado else (55, 60, 70)
                pygame.draw.rect(self.tela, fundo, rect, border_radius=10)
                pygame.draw.rect(self.tela, borda, rect, width=2, border_radius=10)

                tag_txt = self.fonte_desc.render(item["tag"], True, (130, 160, 210))
                self.tela.blit(tag_txt, (rect.x + 14, rect.y + 12))

                # Ícone do item no card da loja
                rect_icone = pygame.Rect(rect.right - 48, rect.y + 10, 36, 36)
                pygame.draw.rect(self.tela, (16, 20, 28), rect_icone, border_radius=6)
                pygame.draw.rect(self.tela, borda, rect_icone, width=1, border_radius=6)
                sprite_loja = carregar_sprite_item(item["nome"], tamanho=(30, 30))
                self.tela.blit(sprite_loja, (rect_icone.centerx - 15, rect_icone.centery - 15))

                nome_txt = self.fonte_item_nome.render(item["nome"], True, (255, 255, 255) if not esgotado else (130, 130, 130))
                self.tela.blit(nome_txt, (rect.x + 14, rect.y + 32))

                palavras = item["desc"].split()
                linhas = []
                curr = ""
                for p in palavras:
                    cand = f"{curr} {p}".strip()
                    if self.fonte_desc.size(cand)[0] > rect.width - 28:
                        linhas.append(curr)
                        curr = p
                    else:
                        curr = cand
                if curr:
                    linhas.append(curr)

                y_desc = rect.y + 58
                for l in linhas[:3]:
                    txt_l = self.fonte_desc.render(l, True, (190, 200, 215) if not esgotado else (110, 110, 110))
                    self.tela.blit(txt_l, (rect.x + 14, y_desc))
                    y_desc += 18

                if item["custo_tipo"] == "materiais":
                    preco_txt = f"Custo: {item['custo']} Sucata{'s' if item['custo'] > 1 else ''}"
                else:
                    preco_txt = f"Custo: {item['custo']} HP de Sangue"
                estoque_txt = f"Estoque: {item['limite'] - item['comprados']}/{item['limite']}"

                txt_pr = self.fonte_preco.render(preco_txt, True, (255, 220, 110) if not esgotado else (120, 120, 120))
                self.tela.blit(txt_pr, (rect.x + 14, rect.y + 128))
                txt_es = self.fonte_desc.render(estoque_txt, True, (140, 150, 170))
                self.tela.blit(txt_es, (rect.x + rect.width - txt_es.get_width() - 14, rect.y + 130))

                entrada["botao"].desenhar(self.tela)

        # Conteúdo da aba Vender (Loja do Perigo)
        else:
            if not self.botoes_venda:
                txt_vazio = self.fonte_subtitulo.render(
                    "Você não possui equipamentos na mochila ou equipados para vender ao receptador.",
                    True, (170, 180, 200)
                )
                self.tela.blit(txt_vazio, txt_vazio.get_rect(center=(self.largura // 2, 330)))
            else:
                for entrada in self.botoes_venda:
                    item_venda = entrada["item_venda"]
                    eq = item_venda["eq"]
                    rect = entrada["card_rect"]

                    pygame.draw.rect(self.tela, (24, 28, 38), rect, border_radius=10)
                    pygame.draw.rect(self.tela, (70, 130, 95), rect, width=2, border_radius=10)

                    tag_txt = "[EQUIPADO]" if item_venda["equipado"] else "[MOCHILA]"
                    cor_tag = (255, 215, 80) if item_venda["equipado"] else (110, 210, 255)
                    self.tela.blit(self.fonte_desc.render(tag_txt, True, cor_tag), (rect.x + 14, rect.y + 12))

                    rect_icone = pygame.Rect(rect.right - 48, rect.y + 10, 36, 36)
                    pygame.draw.rect(self.tela, (16, 20, 28), rect_icone, border_radius=6)
                    pygame.draw.rect(self.tela, (70, 130, 95), rect_icone, width=1, border_radius=6)
                    sprite_venda = carregar_sprite_item(eq, tamanho=(30, 30))
                    self.tela.blit(sprite_venda, (rect_icone.centerx - 15, rect_icone.centery - 15))

                    nome_txt = self.fonte_item_nome.render(eq.nome, True, (255, 255, 255))
                    self.tela.blit(nome_txt, (rect.x + 14, rect.y + 32))

                    cat_str = f"Categoria: {getattr(eq, 'categoria', 'Item').upper()}"
                    self.tela.blit(self.fonte_desc.render(cat_str, True, (160, 175, 195)), (rect.x + 14, rect.y + 58))

                    bonus_itens = [f"+{v} {k}" for k, v in getattr(eq, "atributos_bonus", {}).items() if v > 0]
                    bonus_str = ", ".join(bonus_itens) if bonus_itens else "Sem atributos extras"
                    self.tela.blit(self.fonte_desc.render(f"Bônus: {bonus_str}", True, (130, 220, 140)), (rect.x + 14, rect.y + 78))

                    nivel_str = f"Nível de Refino: +{getattr(eq, 'nivel', 1)-1}"
                    if getattr(eq, "polido", False):
                        nivel_str += " [Polido]"
                    self.tela.blit(self.fonte_desc.render(nivel_str, True, (255, 220, 120)), (rect.x + 14, rect.y + 98))

                    val_str = f"Valor do Perigo: +{item_venda['valor']} Sucatas"
                    self.tela.blit(self.fonte_preco.render(val_str, True, (255, 230, 100)), (rect.x + 14, rect.y + 128))

                    entrada["botao"].desenhar(self.tela)

        # Botão Sair
        self.btn_sair.desenhar(self.tela)


TelaLoja = GerenciadorLoja
