import random
import pygame
from Sistemas.Fontes import obter_fonte, quebrar_texto
from Gameplay.GeracaoFases import BANCO_EVENTOS
from Sistemas.SistemaUI import Botao, TelaBase
from Sistemas.Inventario import inventario_global

class GerenciadorSelecao(TelaBase):
    def __init__(self, tela):
        super().__init__(tela, nome="selecao_cenario")
        self.tela = tela
        self.largura_tela = self.tela.get_width()
        self.retangulos = []
        self.clique_anterior = False

        self.fonte_titulo = obter_fonte(25)
        self.txt_titulo = self.fonte_titulo.render("ESCOLHA SEU PRÓXIMO DESAFIO", True, (255, 255, 255))
        self.fonte_cartao = obter_fonte(14)
        self.mensagem = ""

        largura_btn = 260
        altura_btn = 46
        x_btn = (self.largura_tela - largura_btn) // 2
        y_btn = max(630, self.tela.get_height() - 105)
        self.btn_dormir = Botao(x_btn, y_btn, largura_btn, altura_btn, "DORMIR",
                                (80, 110, 70), (110, 150, 90), largura_btn, altura_btn,
                                cor_texto=(255, 255, 255), fonte_tamanho=14)

        self.cenarios_disponiveis = []
        for indice, ev in enumerate(BANCO_EVENTOS, 1):
            tipo_str = str(ev.get("tipo", "neutro")).strip().lower()
            tag = "[AJUDA]" if tipo_str == "ajuda" else "[EVENTO NEUTRO]"
            attr_chave = ev.get("atributo-chave", "For")
            dificuldade = ev.get("dificuldade", 10)
            identificador = f"evento_neutro_{indice}:{ev['nome']}"
            rotulo = f"{tag}\n\n{ev['nome'].upper()}\n\n{ev['descricao']}\n\nTeste: {attr_chave} (Dif. {dificuldade})"
            self.cenarios_disponiveis.append((identificador, rotulo))

        self.recarregar_opcoes()

    def recarregar_opcoes(self):
        self.mensagem = ""
        self.retangulos.clear()
        self.largura_tela = self.tela.get_width()

        largura_btn = 260
        altura_btn = 46
        x_btn = (self.largura_tela - largura_btn) // 2
        y_btn = max(630, self.tela.get_height() - 105)
        self.btn_dormir.rect = pygame.Rect(x_btn, y_btn, largura_btn, altura_btn)

        quantidade_opcoes = 3
        espacamento = max(12, self.largura_tela // 50)
        margem = max(20, self.largura_tela // 20)
        largura_rect = (self.largura_tela - (margem * 2) - (espacamento * (quantidade_opcoes - 1))) // quantidade_opcoes
        altura_rect = min(360, max(220, self.tela.get_height() - 300))
        y_rect = max(170, (self.tela.get_height() - altura_rect) // 2 + 10)
        x_inicial = (self.largura_tela - ((largura_rect * quantidade_opcoes) + (espacamento * (quantidade_opcoes - 1)))) // 2

        qtd_escolha = min(quantidade_opcoes, len(self.cenarios_disponiveis))
        escolhidos = random.sample(self.cenarios_disponiveis, qtd_escolha)

        for indice_opcao, (nome, rotulo) in enumerate(escolhidos):
            x = x_inicial + indice_opcao * (largura_rect + espacamento)
            rect = pygame.Rect(x, y_rect, largura_rect, altura_rect)
            self.retangulos.append({
                "rect": rect,
                "nome": nome,
                "rotulo": rotulo,
            })

    def atualizar_eventos(self, evento, posicao_mouse):
        bilhetes = inventario_global.obter_bilhetes_dormitorio()
        if self.btn_dormir.checar_clique(evento, posicao_mouse):
            if bilhetes > 0:
                return "dormir"
            self.mensagem = "Você precisa de 1 Bilhete do Dormitório para poder dormir!"
            return None

        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            for retangulo in self.retangulos:
                if retangulo["rect"].collidepoint(posicao_mouse):
                    return retangulo["nome"]
        return None

    def atualizar(self, posicao_mouse, estado_clique_mouse):
        clique_agora = estado_clique_mouse[0]
        clicou = clique_agora and not self.clique_anterior
        self.clique_anterior = clique_agora

        bilhetes = inventario_global.obter_bilhetes_dormitorio()
        self.btn_dormir.definir_texto(f"DORMIR ({bilhetes})")
        self.btn_dormir.atualizar(posicao_mouse, estado_clique_mouse)

    def desenhar(self, posicao_mouse):
        self.tela.fill((15, 15, 20))

        self.tela.blit(self.txt_titulo, self.txt_titulo.get_rect(centerx=self.largura_tela // 2, top=70))

        fonte = self.fonte_cartao

        for retangulo in self.retangulos:
            rect = retangulo["rect"]
            em_foco = rect.collidepoint(posicao_mouse)

            cor_fundo = (60, 60, 80) if em_foco else (35, 35, 45)
            cor_borda = (255, 220, 0) if em_foco else (150, 150, 170)
            largura_borda = 4 if em_foco else 2

            pygame.draw.rect(self.tela, cor_fundo, rect, border_radius=10)
            pygame.draw.rect(self.tela, cor_borda, rect, width=largura_borda, border_radius=10)

            linhas = quebrar_texto(retangulo["rotulo"], fonte, rect.width - 24)

            altura_texto = len(linhas) * fonte.get_linesize()
            y_texto = rect.centery - altura_texto // 2
            for indice_linha, linha in enumerate(linhas):
                cor_txt = (255, 220, 0) if em_foco else (255, 255, 255)
                texto_surf = fonte.render(linha, True, cor_txt)
                x_txt = rect.x + (rect.width - texto_surf.get_width()) // 2
                y_txt = y_texto + (indice_linha * fonte.get_linesize())
                self.tela.blit(texto_surf, (x_txt, y_txt))

        bilhetes = inventario_global.obter_bilhetes_dormitorio()
        self.btn_dormir.definir_texto(f"DORMIR ({bilhetes})")
        self.btn_dormir.desenhar(self.tela)

        if self.mensagem:
            txt_msg = self.fonte_cartao.render(self.mensagem, True, (255, 120, 120))
            self.tela.blit(txt_msg, txt_msg.get_rect(centerx=self.largura_tela // 2, top=self.btn_dormir.rect.bottom + 6))
        else:
            txt_dica = self.fonte_cartao.render("Dormir pula a escolha de cenário e restaura Vida/Mana", True, (160, 160, 180))
            self.tela.blit(txt_dica, txt_dica.get_rect(centerx=self.largura_tela // 2, top=self.btn_dormir.rect.bottom + 6))

