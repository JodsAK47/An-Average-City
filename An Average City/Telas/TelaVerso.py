import pygame
from Sistemas.SistemaUI import Botao, TelaBase, desenhar_painel_container
from Sistemas.Fontes import obter_fonte
from Sistemas.SaveSystem import save_global
from Sistemas.Conquistas import sistema_conquistas
from Entidades.Personagem import personagem
from Sistemas.Recursos import caminho_botao, caminho_dados

import json
import os

CAMINHO_DADOS = caminho_dados()

def carregar_arvores():
    try:
        with open(caminho_dados("arvores.json"), "r", encoding="utf-8") as f:
            dados = json.load(f)
            for verso, arvore in dados.items():
                for hab in arvore:
                    if isinstance(hab.get("pos"), list):
                        hab["pos"] = tuple(hab["pos"])
            return dados
    except FileNotFoundError:
        print("⚠️ Erro: arquivo arvores.json não encontrado.")
        return {"Sobrevivente": [], "Agente": [], "Feiticeiro": [], "Invocador": []}

ARVORE_POR_VERSO = carregar_arvores()

FUNDO = (25, 30, 42)
PAINEL = (38, 46, 62)
PAINEL_CLARO = (48, 57, 75)
BORDA = (91, 103, 126)
TEXTO = (235, 235, 235)
TEXTO_SECUNDARIO = (180, 190, 205)
AZUL_DESTAQUE = (76, 98, 122)

CORES_VERSO = {
    "Sobrevivente": (189, 118, 52),
    "Agente": (186, 52, 52),
    "Feiticeiro": (128, 78, 168),
}

SPRITES_POR_VERSO = {
    "Sobrevivente": "SURVIVORC.png",
    "Agente": "AGENTC.png",
    "Feiticeiro": "SOCERERC.png",
}

class GerenciadorVerso(TelaBase):
    def __init__(self, tela):
        super().__init__(tela, nome="verso")
        self.tela = tela

        self.fonte_titulo = obter_fonte(16)
        self.fonte_desc = obter_fonte(12)
        self.fonte_micro = obter_fonte(9)

        self.aviso = ""
        self.voltar_clicado = False

        self.pontos = save_global.obter_pontos()
        self.verso_atual = "Sobrevivente"
        self.verso_ativo = None
        self.modo = "menu"
        self.alvo_personagem = None
        self.habilidades_desbloqueadas = []
        self.habilidade_foco = None
        self.arvores_por_verso = {verso: arvore[:] for verso, arvore in ARVORE_POR_VERSO.items()}
        self.versos = ["Sobrevivente", "Agente", "Feiticeiro"]
        self.progresso_por_verso = {verso: list(save_global.obter_progresso_verso(verso)) for verso in self.versos}
        self.habilidades_desabilitadas = {verso: set(save_global.obter_habilidades_desabilitadas(verso)) for verso in self.versos}
        self.sincronizar_habilidades_ativas()

        self.botao_voltar = Botao(
            720, 700, 240, 50, "VOLTAR", (55, 62, 78), AZUL_DESTAQUE, 250, 55,
            cor_texto=TEXTO, fonte_tamanho=14,
            sprite_base_path="BACK.png", sprite_hover_path="BACK.png", sprite_clique_path="BACK.png",
        )

        self.botao_selecionar = Botao(
            720, 630, 240, 50, "ESCOLHER VERSO", AZUL_DESTAQUE, (95, 120, 145), 250, 55,
            cor_texto=TEXTO, fonte_tamanho=14,
            sprite_base_path="SELECT.png", sprite_hover_path="SELECT.png", sprite_clique_path="SELECT.png",
        )

        self.botao_confirmar = self.botao_selecionar
        self.botao_comprar = Botao(720, 560, 240, 50, "DESBLOQUEAR", (65, 75, 92), (95, 110, 130), 250, 55, cor_texto=TEXTO, fonte_tamanho=14)

        self.esferas_rects = {
            "Sobrevivente": pygame.Rect(70, 410, 80, 80),
            "Agente": pygame.Rect(190, 410, 80, 80),
            "Feiticeiro": pygame.Rect(130, 545, 80, 80),
        }
        self.imagens_por_verso = {
            nome: self._carregar_imagem_verso(nome)
            for nome in self.versos
        }

    def _carregar_imagem_verso(self, nome_verso):
        nome_arquivo = SPRITES_POR_VERSO.get(nome_verso, "SURVIVORC.png")
        try:
            imagem = pygame.image.load(caminho_botao(nome_arquivo)).convert_alpha()
            return imagem
        except (FileNotFoundError, pygame.error):
            return None

    def sincronizar_habilidades_ativas(self):
        self.pontos = save_global.obter_pontos()
        progresso_salvo = save_global.obter_progresso_versos()
        for v in self.versos:
            if v in progresso_salvo:
                self.progresso_por_verso[v] = list(progresso_salvo[v])
        self.progresso_por_verso.setdefault(self.verso_atual, [])
        self.habilidades_desbloqueadas = list(self.progresso_por_verso.get(self.verso_atual, []))

        desab_salvo = save_global.obter_habilidades_desabilitadas()
        for v in self.versos:
            if v in desab_salvo:
                self.habilidades_desabilitadas[v] = set(desab_salvo[v])
            else:
                self.habilidades_desabilitadas.setdefault(v, set())

        self.aplicar_talentos_ao_personagem()

    def aplicar_talentos_ao_personagem(self, personagem_alvo=None, verso=None):
        alvo = personagem_alvo if personagem_alvo is not None else personagem
        verso_alvo = verso if verso is not None else self.verso_atual
        talentos_verso = list(self.progresso_por_verso.get(verso_alvo, []))
        talentos_invocador = list(save_global.obter_progresso_verso("Invocador"))

        desab_verso = self.habilidades_desabilitadas.get(verso_alvo, set())
        desab_invocador = self.habilidades_desabilitadas.get("Invocador", set())
        desabilitadas = set(desab_verso) | set(desab_invocador)

        talentos_ativos = [t for t in (talentos_verso + talentos_invocador) if t not in desabilitadas]
        alvo.talentos = set(talentos_ativos)

        mapa_nodos = {"Sobrevivente": "S4", "Agente": "A4", "Feiticeiro": "F4"}
        if not hasattr(alvo, "ultimates_desbloqueadas"):
            alvo.ultimates_desbloqueadas = set()

        classes_todas = ["Físico", "Distância", "Magia", "Invocador"]
        nodo_ult = mapa_nodos.get(verso_alvo)
        if nodo_ult and nodo_ult in talentos_verso and nodo_ult not in desabilitadas:
            alvo.ultimates_desbloqueadas.add(verso_alvo)
            for c in classes_todas:
                alvo.ultimates_desbloqueadas.add((verso_alvo, c))
        else:
            alvo.ultimates_desbloqueadas.discard(verso_alvo)
            for c in classes_todas:
                alvo.ultimates_desbloqueadas.discard((verso_alvo, c))

        if "I4" in talentos_invocador and "I4" not in desabilitadas:
            alvo.ultimates_desbloqueadas.add("Invocador")
            for v in self.versos:
                alvo.ultimates_desbloqueadas.add((v, "Invocador"))

    def alternar_habilidade_foco(self):
        if not self.habilidade_foco:
            self.aviso = "Selecione uma habilidade na árvore!"
            return
        hab_id = self.habilidade_foco["id"]
        if hab_id not in self.habilidades_desbloqueadas:
            self.aviso = "Desbloqueie a habilidade antes de habilitar/desabilitar!"
            return

        desab_verso = self.habilidades_desabilitadas.setdefault(self.verso_atual, set())
        if hab_id in desab_verso:
            desab_verso.remove(hab_id)
            self.aviso = f"Habilidade '{self.habilidade_foco['nome']}' HABILITADA!"
        else:
            desab_verso.add(hab_id)
            self.aviso = f"Habilidade '{self.habilidade_foco['nome']}' DESABILITADA!"

        save_global.definir_habilidades_desabilitadas(self.verso_atual, list(desab_verso))
        save_global.salvar()
        self.aplicar_talentos_ao_personagem()

    def obter_arvore_ativa(self):
        return self.arvores_por_verso.get(self.verso_atual, self.arvores_por_verso["Sobrevivente"])

    def atualizar_eventos(self, evento, posicao_mouse):
        if self.botao_voltar.checar_clique(evento, posicao_mouse):
            save_global.salvar()
            self.voltar_clicado = True
            return None

        if self.botao_selecionar.checar_clique(evento, posicao_mouse):
            if self.modo == "visualizacao":
                alvo = getattr(self, "alvo_personagem", None)
                if alvo is not None:
                    self.aplicar_talentos_ao_personagem(alvo, verso=self.verso_atual)
                else:
                    self.aplicar_talentos_ao_personagem(personagem, verso=self.verso_atual)
                save_global.salvar()
                return self.verso_atual
            elif self.modo == "menu":
                self.alternar_habilidade_foco()
                return None

        if self.modo == "menu" and self.botao_comprar.checar_clique(evento, posicao_mouse):
            if self.habilidade_foco:
                if self.habilidade_foco["id"] not in self.habilidades_desbloqueadas:
                    pode_comprar = True
                    for req in self.habilidade_foco["req"]:
                        if req not in self.habilidades_desbloqueadas:
                            pode_comprar = False
                    if pode_comprar and self.pontos >= self.habilidade_foco["preco"]:
                        save_global.adicionar_pontos(-self.habilidade_foco["preco"])
                        self.pontos = save_global.obter_pontos()
                        self.habilidades_desbloqueadas.append(self.habilidade_foco["id"])
                        self.progresso_por_verso[self.verso_atual] = list(self.habilidades_desbloqueadas)
                        save_global.definir_progresso_verso(self.verso_atual, self.habilidades_desbloqueadas)
                        save_global.salvar()
                        self.aplicar_talentos_ao_personagem()
                        self.aviso = f"Desbloqueado: {self.habilidade_foco['nome']}!"

                        sistema_conquistas.desbloquear("primeiro_talento")

                        if self.habilidade_foco["id"] in {"S4", "A4", "F4"}:
                            self.aviso = f"Ultimate desbloqueada para {self.verso_atual}!"
                            sistema_conquistas.desbloquear("ultimate_desbloqueada")
            return None

        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            for nome, rect in self.esferas_rects.items():
                if rect.collidepoint(posicao_mouse):
                    self.verso_atual = nome
                    self.sincronizar_habilidades_ativas()
                    self.habilidade_foco = None
                    return None

            for hab in self.obter_arvore_ativa():
                x, y = hab["pos"]
                retangulo_habilidade = pygame.Rect(x - 35, y - 35, 70, 70)
                if retangulo_habilidade.collidepoint(posicao_mouse):
                    self.habilidade_foco = hab
                    return None

        return None

    def atualizar(self, posicao_mouse, estado_clique_mouse):
        self.botao_voltar.atualizar(posicao_mouse, estado_clique_mouse)
        if self.modo == "visualizacao":
            self.botao_selecionar.texto = "CONFIRMAR VERSO"
            self.botao_selecionar.cor_base = AZUL_DESTAQUE
            self.botao_selecionar.cor_hover = (95, 120, 145)
            self.botao_selecionar.cor_texto = TEXTO
        else:
            # Modo menu: botão vira HABILITAR / DESABILITAR
            if self.habilidade_foco:
                hab_id = self.habilidade_foco["id"]
                if hab_id in self.habilidades_desbloqueadas:
                    desab_verso = self.habilidades_desabilitadas.get(self.verso_atual, set())
                    if hab_id in desab_verso:
                        self.botao_selecionar.texto = "HABILITAR HABILIDADE"
                        self.botao_selecionar.cor_base = (35, 105, 55)
                        self.botao_selecionar.cor_hover = (48, 140, 75)
                        self.botao_selecionar.cor_texto = (210, 255, 220)
                    else:
                        self.botao_selecionar.texto = "DESABILITAR HABILIDADE"
                        self.botao_selecionar.cor_base = (130, 42, 45)
                        self.botao_selecionar.cor_hover = (170, 52, 58)
                        self.botao_selecionar.cor_texto = (255, 225, 225)
                else:
                    self.botao_selecionar.texto = "HABILITAR / DESABILITAR"
                    self.botao_selecionar.cor_base = (50, 58, 72)
                    self.botao_selecionar.cor_hover = (50, 58, 72)
                    self.botao_selecionar.cor_texto = (140, 150, 165)
            else:
                self.botao_selecionar.texto = "SELECIONE UMA HABILIDADE"
                self.botao_selecionar.cor_base = (50, 58, 72)
                self.botao_selecionar.cor_hover = (50, 58, 72)
                self.botao_selecionar.cor_texto = (140, 150, 165)

        self.botao_selecionar.atualizar(posicao_mouse, estado_clique_mouse)
        if self.modo == "menu":
            if self.habilidade_foco:
                hab_id = self.habilidade_foco["id"]
                if hab_id in self.habilidades_desbloqueadas:
                    self.botao_comprar.texto = "DESBLOQUEADA"
                    self.botao_comprar.cor_base = (45, 55, 70)
                    self.botao_comprar.cor_hover = (45, 55, 70)
                    self.botao_comprar.cor_texto = (130, 140, 155)
                else:
                    pode = all(req in self.habilidades_desbloqueadas for req in self.habilidade_foco.get("req", []))
                    if not pode:
                        self.botao_comprar.texto = "REQUER ANTERIOR"
                        self.botao_comprar.cor_base = (45, 55, 70)
                        self.botao_comprar.cor_hover = (45, 55, 70)
                        self.botao_comprar.cor_texto = (130, 140, 155)
                    elif self.pontos < self.habilidade_foco.get("preco", 0):
                        self.botao_comprar.texto = f"DESBLOQUEAR ({self.habilidade_foco.get('preco', 0)} PTS)"
                        self.botao_comprar.cor_base = (90, 75, 30)
                        self.botao_comprar.cor_hover = (110, 95, 40)
                        self.botao_comprar.cor_texto = (240, 215, 110)
                    else:
                        self.botao_comprar.texto = f"DESBLOQUEAR ({self.habilidade_foco.get('preco', 0)} PTS)"
                        self.botao_comprar.cor_base = (40, 105, 60)
                        self.botao_comprar.cor_hover = (55, 145, 80)
                        self.botao_comprar.cor_texto = (235, 255, 235)
            else:
                self.botao_comprar.texto = "DESBLOQUEAR"
                self.botao_comprar.cor_base = (45, 55, 70)
                self.botao_comprar.cor_hover = (45, 55, 70)
                self.botao_comprar.cor_texto = (130, 140, 155)

            self.botao_comprar.atualizar(posicao_mouse, estado_clique_mouse)

    def _quebrar_texto(self, texto, fonte, largura_maxima):
        linhas = []
        for paragrafo in texto.split("\n"):
            palavras = paragrafo.split()
            linha = ""
            for palavra in palavras:
                tentativa = f"{linha} {palavra}".strip()
                if fonte.size(tentativa)[0] <= largura_maxima:
                    linha = tentativa
                else:
                    if linha:
                        linhas.append(linha)
                    linha = palavra
            linhas.append(linha)
        return linhas

    def _desenhar_container_retorno(self):
        """
        Desenha um container estilizado na parte superior da árvore de habilidades
        para exibir mensagens de retorno, feedback e status em relação à skilltree.
        """
        rect_container = pygame.Rect(335, 55, 330, 125)
        desab_atual = self.habilidades_desabilitadas.get(self.verso_atual, set())

        tag_status = "ÁRVORE DE HABILIDADES"
        cor_borda = (80, 95, 120)
        cor_tag_bg = (32, 40, 56)
        cor_tag_txt = (175, 205, 235)
        cor_texto = TEXTO
        texto_principal = self.aviso

        if self.aviso:
            aviso_lower = self.aviso.lower()
            if any(term in aviso_lower for term in ["desbloqueado", "habilitada", "ultimate desbloqueada"]):
                tag_status = "SUCESSO"
                cor_borda = (42, 185, 95)
                cor_tag_bg = (20, 60, 35)
                cor_tag_txt = (130, 255, 180)
                cor_texto = (225, 255, 235)
            elif any(term in aviso_lower for term in ["desabilitada", "selecione", "desbloqueie"]):
                tag_status = "AVISO"
                cor_borda = (215, 75, 75)
                cor_tag_bg = (65, 25, 25)
                cor_tag_txt = (255, 175, 175)
                cor_texto = (255, 225, 225)
            elif "jogador" in aviso_lower:
                tag_status = "INSTRUÇÃO"
                cor_borda = (75, 160, 240)
                cor_tag_bg = (25, 45, 75)
                cor_tag_txt = (150, 215, 255)
                cor_texto = (230, 245, 255)
        elif self.habilidade_foco:
            hab = self.habilidade_foco
            hab_id = hab["id"]
            if hab_id in self.habilidades_desbloqueadas:
                if hab_id in desab_atual:
                    tag_status = "TALENTO DESABILITADO"
                    cor_borda = (205, 60, 60)
                    cor_tag_bg = (60, 25, 25)
                    cor_tag_txt = (255, 170, 170)
                    cor_texto = (255, 220, 220)
                    texto_principal = f"'{hab['nome']}' está inativo no momento."
                else:
                    tag_status = "TALENTO ATIVO"
                    cor_borda = (42, 175, 88)
                    cor_tag_bg = (20, 60, 35)
                    cor_tag_txt = (130, 255, 180)
                    cor_texto = (225, 255, 235)
                    texto_principal = f"'{hab['nome']}' está liberado e pronto para o combate."
            else:
                pode = all(req in self.habilidades_desbloqueadas for req in hab.get("req", []))
                if not pode:
                    tag_status = "TALENTO BLOQUEADO"
                    cor_borda = (80, 90, 108)
                    cor_tag_bg = (38, 44, 56)
                    cor_tag_txt = (160, 170, 185)
                    cor_texto = TEXTO_SECUNDARIO
                    texto_principal = "Requer o desbloqueio da habilidade anterior."
                elif self.pontos < hab.get("preco", 0):
                    tag_status = "PONTOS INSUFICIENTES"
                    cor_borda = (215, 175, 35)
                    cor_tag_bg = (60, 50, 18)
                    cor_tag_txt = (255, 220, 95)
                    cor_texto = (255, 245, 215)
                    texto_principal = f"Custo: {hab.get('preco', 0)} pts (você possui {self.pontos} pts)."
                else:
                    tag_status = "DISPONÍVEL"
                    cor_borda = (245, 205, 50)
                    cor_tag_bg = (65, 55, 20)
                    cor_tag_txt = (255, 235, 110)
                    cor_texto = (255, 255, 230)
                    texto_principal = f"Pronto para desbloquear por {hab.get('preco', 0)} pontos."
        else:
            tag_status = "ÁRVORE DE HABILIDADES"
            texto_principal = "Clique em um talento da árvore para inspecionar, desbloquear ou alternar status."

        # Caixa principal do container com sprite 8-bit
        desenhar_painel_container(self.tela, rect_container, "painel_retorno.png", fallback_cor=(22, 28, 38), borda_cor=cor_borda, margem=10)

        # Tag/Badge superior
        txt_tag = self.fonte_micro.render(tag_status, True, cor_tag_txt)
        largura_tag = txt_tag.get_width() + 16
        rect_tag = pygame.Rect(rect_container.centerx - largura_tag // 2, rect_container.y + 10, largura_tag, 20)
        pygame.draw.rect(self.tela, cor_tag_bg, rect_tag, border_radius=4)
        pygame.draw.rect(self.tela, cor_borda, rect_tag, width=1, border_radius=4)
        self.tela.blit(txt_tag, (rect_tag.centerx - txt_tag.get_width() // 2, rect_tag.centery - txt_tag.get_height() // 2))

        # Texto do retorno com quebra de linha
        linhas = self._quebrar_texto(texto_principal, self.fonte_desc, rect_container.width - 24)
        total_h = len(linhas) * 20
        y_ini = rect_tag.bottom + max(8, (rect_container.bottom - rect_tag.bottom - total_h) // 2)

        for i, linha in enumerate(linhas[:3]):
            txt_rend = self.fonte_desc.render(linha, True, cor_texto)
            self.tela.blit(txt_rend, (rect_container.centerx - txt_rend.get_width() // 2, y_ini + i * 20))

    def _desenhar_card_perfil_habilidade(self):
        """
        Desenha o container à direita como um card de perfil elegante,
        exibindo apenas o nome da habilidade, a moldura/imagem de perfil e a descrição.
        """
        rect_card = pygame.Rect(700, 40, 280, 465)
        desenhar_painel_container(self.tela, rect_card, "painel_detalhes.png", fallback_cor=PAINEL_CLARO, borda_cor=BORDA, margem=14)

        cor_verso = CORES_VERSO.get(self.verso_atual, AZUL_DESTAQUE)

        if self.habilidade_foco:
            hab = self.habilidade_foco
            nome_hab = hab["nome"].upper()
            desc_hab = hab.get("desc", "")
            hab_id = hab.get("id", "??")

            # 1. Nome da Habilidade
            linhas_nome = self._quebrar_texto(nome_hab, self.fonte_titulo, 250)
            y_nome = 56
            for l in linhas_nome[:2]:
                txt_l = self.fonte_titulo.render(l, True, TEXTO)
                self.tela.blit(txt_l, txt_l.get_rect(centerx=840, top=y_nome))
                y_nome += 22

            # Linha decorativa abaixo do nome
            pygame.draw.line(self.tela, cor_verso, (735, y_nome + 4), (945, y_nome + 4), 2)

            # 2. Imagem / Moldura estilo Card de Perfil
            rect_foto = pygame.Rect(740, y_nome + 12, 200, 150)
            desenhar_painel_container(self.tela, rect_foto, "painel_card.png", fallback_cor=(20, 26, 36), borda_cor=BORDA, margem=8)

            # Tenta carregar imagem real da habilidade se existir no disco
            imagem_carregada = None
            nomes_tentativas = [
                hab.get("arquivo_imagem"),
                hab.get("imagem"),
                f"{hab_id}.png",
                f"{hab['nome']}.png",
            ]
            for n_tentativa in nomes_tentativas:
                if n_tentativa:
                    try:
                        p = caminho_imagem(n_tentativa)
                        if os.path.exists(p) and os.path.isfile(p):
                            img_bruta = pygame.image.load(p).convert_alpha()
                            imagem_carregada = pygame.transform.smoothscale(img_bruta, (180, 130))
                            break
                    except Exception:
                        pass

            if imagem_carregada is not None:
                self.tela.blit(imagem_carregada, imagem_carregada.get_rect(center=rect_foto.center))
            else:
                # Placeholder visual estilo Card de Perfil (ainda não adicionada)
                pygame.draw.circle(self.tela, (30, 38, 52), rect_foto.center, 44)
                pygame.draw.circle(self.tela, cor_verso, rect_foto.center, 44, 3)
                pygame.draw.circle(self.tela, (45, 56, 75), rect_foto.center, 36)

                # ID do talento no centro do medalhão
                txt_id_card = self.fonte_titulo.render(hab_id, True, (245, 248, 252))
                self.tela.blit(txt_id_card, txt_id_card.get_rect(center=rect_foto.center))

                # Pequena tarja informativa na base da foto
                rect_tarja = pygame.Rect(rect_foto.x + 10, rect_foto.bottom - 24, rect_foto.width - 20, 18)
                pygame.draw.rect(self.tela, (28, 36, 48), rect_tarja, border_radius=4)
                pygame.draw.rect(self.tela, (60, 72, 92), rect_tarja, width=1, border_radius=4)
                txt_em_breve = self.fonte_micro.render("CARD DE HABILIDADE", True, (150, 165, 185))
                self.tela.blit(txt_em_breve, txt_em_breve.get_rect(center=rect_tarja.center))

            # 3. Descrição da Habilidade
            y_desc = rect_foto.bottom + 14
            txt_label_desc = self.fonte_micro.render("DESCRIÇÃO DA HABILIDADE", True, cor_verso)
            self.tela.blit(txt_label_desc, (735, y_desc))
            pygame.draw.line(self.tela, (60, 72, 92), (735 + txt_label_desc.get_width() + 8, y_desc + 7), (945, y_desc + 7), 1)

            deslocamento_y = y_desc + 18
            for linha in self._quebrar_texto(desc_hab, self.fonte_desc, 230):
                txt_desc = self.fonte_desc.render(linha, True, TEXTO_SECUNDARIO)
                self.tela.blit(txt_desc, (735, deslocamento_y))
                deslocamento_y += 20

        else:
            # Estado sem habilidade selecionada: exibe o card de perfil do próprio Verso
            nome_verso = self.verso_atual.upper()
            txt_nome = self.fonte_titulo.render(nome_verso, True, cor_verso)
            self.tela.blit(txt_nome, txt_nome.get_rect(centerx=840, top=58))

            pygame.draw.line(self.tela, cor_verso, (735, 84), (945, 84), 2)

            rect_foto = pygame.Rect(740, 96, 200, 150)
            desenhar_painel_container(self.tela, rect_foto, "painel_card.png", fallback_cor=(20, 26, 36), borda_cor=BORDA, margem=8)

            imagem_verso = self.imagens_por_verso.get(self.verso_atual)
            if imagem_verso is not None:
                sprite = pygame.transform.smoothscale(imagem_verso, (130, 130))
                self.tela.blit(sprite, sprite.get_rect(center=rect_foto.center))
            else:
                pygame.draw.circle(self.tela, cor_verso, rect_foto.center, 44)

            y_desc = rect_foto.bottom + 14
            txt_label_desc = self.fonte_micro.render("SOBRE O VERSO", True, cor_verso)
            self.tela.blit(txt_label_desc, (735, y_desc))
            pygame.draw.line(self.tela, (60, 72, 92), (735 + txt_label_desc.get_width() + 8, y_desc + 7), (945, y_desc + 7), 1)

            descricoes = {
                "Sobrevivente": "Resiliente e adaptável. Especialista em sobrevivência, defesa e resistência.",
                "Agente": "Ágil, preciso e letal. Focado em velocidade, ataques críticos e táticas avançadas.",
                "Feiticeiro": "Místico e destruidor. Canaliza energia arcana e conjura magias de alto impacto.",
            }
            desc = descricoes.get(self.verso_atual, "Selecione uma habilidade na árvore para ver seu perfil.")
            deslocamento_y = y_desc + 18
            for linha in self._quebrar_texto(desc, self.fonte_desc, 230):
                txt_desc = self.fonte_desc.render(linha, True, TEXTO_SECUNDARIO)
                self.tela.blit(txt_desc, (735, deslocamento_y))
                deslocamento_y += 20

            dica = "Clique nas orbes para inspecionar cada talento."
            txt_dica = self.fonte_micro.render(dica, True, (130, 150, 175))
            self.tela.blit(txt_dica, (735, deslocamento_y + 10))

    def desenhar(self):
        self.tela.fill(FUNDO)

        desenhar_painel_container(self.tela, (40, 40, 260, 260), "painel_detalhes.png", fallback_cor=PAINEL_CLARO, margem=12)
        txt_carac = self.fonte_desc.render("VERSO", True, TEXTO)
        self.tela.blit(txt_carac, (170 - txt_carac.get_width()//2, 50))

        imagem_central = self.imagens_por_verso.get(self.verso_atual)
        if imagem_central is not None:
            imagem_redimensionada = pygame.transform.smoothscale(imagem_central, (120, 120))
            rect_imagem = imagem_redimensionada.get_rect(center=(170, 180))
            self.tela.blit(imagem_redimensionada, rect_imagem)
            pygame.draw.circle(self.tela, (200, 255, 50), (170, 180), 60, 5)
        else:
            pygame.draw.circle(self.tela, CORES_VERSO.get(self.verso_atual, (100, 100, 100)), (170, 180), 60)
            pygame.draw.circle(self.tela, (200, 255, 50), (170, 180), 60, 5)

        nome_verso = self.verso_atual.upper()
        txt_nome_verso = self.fonte_desc.render(nome_verso, True, TEXTO)
        self.tela.blit(txt_nome_verso, (170 - txt_nome_verso.get_width()//2, 260))

        desenhar_painel_container(self.tela, (40, 320, 260, 440), "painel_base.png", fallback_cor=PAINEL_CLARO, margem=14)
        txt_arvores = self.fonte_desc.render("Arvores de Habilidades", True, TEXTO)
        self.tela.blit(txt_arvores, (170 - txt_arvores.get_width()//2, 340))

        destaque_por_verso = {
            "Sobrevivente": (255, 191, 122),
            "Agente": (255, 120, 120),
            "Feiticeiro": (196, 147, 255),
        }

        for nome, rect in self.esferas_rects.items():
            borda = 5 if nome == self.verso_atual else 0
            imagem_verso = self.imagens_por_verso.get(nome)
            if imagem_verso is not None:
                sprite = pygame.transform.smoothscale(imagem_verso, (rect.width, rect.height))
                self.tela.blit(sprite, rect.topleft)
            else:
                pygame.draw.circle(self.tela, CORES_VERSO.get(nome, (100, 100, 100)), rect.center, 40)
            if borda:
                pygame.draw.circle(self.tela, destaque_por_verso.get(nome, (255, 255, 255)), rect.center, 40, 5)

        desenhar_painel_container(self.tela, (320, 40, 360, 720), "painel_base.png", fallback_cor=PAINEL, borda_cor=BORDA, margem=16)

        self._desenhar_container_retorno()

        arvore_ativa = self.obter_arvore_ativa()
        desab_atual = self.habilidades_desabilitadas.get(self.verso_atual, set())

        # 1. Linhas conectando os nós
        for hab in arvore_ativa:
            for id_requisito in hab["req"]:
                for h in arvore_ativa:
                    if h["id"] == id_requisito:
                        hab_desbloq = hab["id"] in self.habilidades_desbloqueadas
                        req_desbloq = h["id"] in self.habilidades_desbloqueadas
                        if hab_desbloq:
                            cor_linha = (42, 175, 88) if hab["id"] not in desab_atual else (205, 50, 50)
                        elif req_desbloq:
                            cor_linha = (215, 175, 35)
                        else:
                            cor_linha = (70, 78, 92)
                        pygame.draw.line(self.tela, cor_linha, h["pos"], hab["pos"], 4)

        # 2. Orbes das habilidades
        for hab in arvore_ativa:
            hab_id = hab["id"]
            desbloqueada = hab_id in self.habilidades_desbloqueadas
            desabilitada = hab_id in desab_atual
            req_ok = all(req in self.habilidades_desbloqueadas for req in hab.get("req", []))

            if desbloqueada:
                if desabilitada:
                    # VERMELHO: se estiver desabilitada deixe a orbe vermelha
                    cor_orbe = (205, 50, 50)
                    cor_borda = (255, 95, 95)
                    cor_texto = (255, 230, 230)
                else:
                    # VERDE: Verde é liberado
                    cor_orbe = (42, 175, 88)
                    cor_borda = (85, 235, 135)
                    cor_texto = (235, 255, 240)
            else:
                if not req_ok:
                    # CINZA: cinza é desbloquear anterior
                    cor_orbe = (70, 78, 92)
                    cor_borda = (95, 105, 120)
                    cor_texto = (140, 150, 165)
                else:
                    if self.pontos < hab.get("preco", 0):
                        # AMARELO: Amarelo é Sem dinheiro o bastante
                        cor_orbe = (215, 175, 35)
                        cor_borda = (255, 215, 75)
                        cor_texto = (255, 250, 220)
                    else:
                        # Disponível para desbloquear (Amarelo Ouro / Pronto)
                        cor_orbe = (245, 205, 50)
                        cor_borda = (255, 235, 95)
                        cor_texto = (255, 255, 230)

            x, y = hab["pos"]
            pygame.draw.circle(self.tela, cor_orbe, (x, y), 35)
            pygame.draw.circle(self.tela, cor_borda, (x, y), 35, 3)

            txt_id = self.fonte_titulo.render(hab_id, True, cor_texto)
            self.tela.blit(txt_id, txt_id.get_rect(center=(x, y)))

            if self.habilidade_foco == hab:
                pygame.draw.circle(self.tela, (255, 255, 255), (x, y), 40, 3)



        self._desenhar_card_perfil_habilidade()

        if self.modo == "menu":
            rect_pontos = pygame.Rect(720, 514, 240, 36)
            desenhar_painel_container(self.tela, rect_pontos, "painel_topo.png", fallback_cor=FUNDO, borda_cor=BORDA, margem=8)
            txt_pontos = self.fonte_titulo.render(f"PONTOS: {self.pontos}", True, (255, 215, 60))
            self.tela.blit(txt_pontos, txt_pontos.get_rect(center=rect_pontos.center))
            self.botao_comprar.desenhar(self.tela)

        # Mini-painel de Legenda no rodapé da coluna esquerda
        rect_legenda = pygame.Rect(50, 642, 240, 110)
        desenhar_painel_container(self.tela, rect_legenda, "painel_card.png", fallback_cor=FUNDO, borda_cor=BORDA, margem=8)

        txt_leg_tit = self.fonte_desc.render("LEGENDA DAS ORBES:", True, TEXTO)
        self.tela.blit(txt_leg_tit, (58, 646))

        itens_legenda = [
            ((42, 175, 88), "Verde: Liberado"),
            ((205, 50, 50), "Vermelho: Desabilitado"),
            ((215, 175, 35), "Amarelo: Sem dinheiro"),
            ((70, 78, 92), "Cinza: Bloqueado anterior"),
        ]
        for idx, (cor_item, texto_item) in enumerate(itens_legenda):
            y_item = 667 + idx * 20
            pygame.draw.circle(self.tela, cor_item, (66, y_item + 6), 6)
            pygame.draw.circle(self.tela, TEXTO, (66, y_item + 6), 6, 1)
            txt_i = self.fonte_micro.render(texto_item, True, TEXTO_SECUNDARIO)
            self.tela.blit(txt_i, (78, y_item))

        self.botao_selecionar.desenhar(self.tela)
        self.botao_voltar.desenhar(self.tela)
