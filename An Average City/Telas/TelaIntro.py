"""
Tela de Introdução (Intro) para o jogo An Average City.
Exibida antes do menu principal:
- Fundo totalmente preto
- Linhas de diálogo carregadas de Dados/intro.json
- Cada linha surge separadamente no estilo máquina de escrever com som de diálogo (Dialogo.wav)
- Transição com Fade-Out entre cada linha individual
- Ao final, exibe o diálogo completo na tela
- Música ambiente Intro.mp3 (OSTs)
- Fonte Manga (Manga.ttf)
- Opção de pular (Skip) via botão ou teclado
"""

import os
import json
from typing import Optional, List, Tuple
import pygame

from Sistemas.SistemaUI import TelaBase, Botao
from Sistemas.Fontes import obter_fonte, obter_fonte_manga, quebrar_texto
from Sistemas.GerenciadorAudio import gerenciador_musica, tocar_sfx
from Sistemas.Recursos import caminho_dados

LINHAS_INTRO_FALLBACK = [
    "Nas profundezas de uma cidade aparentemente comum...",
    "Sob o asfalto cinzento e os arranha-céus que tocam a névoa,",
    "antigos mistérios e forças ocultas despertam.",
    "Sobreviventes buscam recursos em becos esquecidos.",
    "Agentes operam nas sombras da conspiração.",
    "Feiticeiros manipulam energias além da compreensão humana.",
    "Três caminhos distintos. Um único destino.",
    "Bem-vindo a An Average City."
]


def carregar_linhas_intro_json() -> List[str]:
    """Carrega as linhas de diálogo a partir de Dados/intro.json com fallback seguro."""
    caminho = caminho_dados("intro.json")
    if os.path.exists(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                dados = json.load(f)
                if isinstance(dados, dict) and "linhas" in dados:
                    linhas = [str(linha).strip() for linha in dados["linhas"] if str(linha).strip()]
                    if linhas:
                        return linhas
                elif isinstance(dados, list):
                    linhas = [str(linha).strip() for linha in dados if str(linha).strip()]
                    if linhas:
                        return linhas
        except Exception as e:
            print(f"[Aviso] Erro ao carregar Dados/intro.json: {e}")
    return list(LINHAS_INTRO_FALLBACK)


class GerenciadorIntro(TelaBase):
    """Controla a apresentação cinematográfica de introdução com máquina de escrever e fade-out entre linhas."""

    # Fases de exibição
    FASE_DIGITANDO = 0
    FASE_ESPERA = 1
    FASE_FADEOUT = 2
    FASE_COMPLETO = 3

    def __init__(self, tela: pygame.Surface, linhas_intro: Optional[List[str]] = None):
        super().__init__(tela, nome="intro")
        self.tela = tela
        self.largura = tela.get_width()
        self.altura = tela.get_height()

        self.cor_fundo = (0, 0, 0)
        self.linhas: List[str] = list(linhas_intro) if linhas_intro is not None else carregar_linhas_intro_json()

        # Configurações de fonte
        self.tamanho_fonte = 22
        self.tamanho_fonte_destaque = 26
        self.fonte_manga = obter_fonte_manga(self.tamanho_fonte)
        self.fonte_manga_destaque = obter_fonte_manga(self.tamanho_fonte_destaque)
        self.fonte_dica = obter_fonte(14)

        # Estado da sequência
        self.indice_linha = 0
        self.fase_atual = self.FASE_DIGITANDO

        # Máquina de escrever da linha atual
        self.caractere_atual = 0
        self.pausa_pontuacao = 0
        self.frame_contador = 0

        # Fade out da linha individual
        self.alpha_linha = 255
        self.duracao_espera_linha = 55   # frames que a linha fica parada antes do fade-out (~0.9s)
        self.duracao_fadeout_linha = 22  # frames de fade out (~0.35s)
        self.timer_fase = 0

        # Fase final completa
        self.alpha_completo = 0
        self.duracao_fadein_completo = 30
        self.timer_espera_pos_conclusao = 0
        self.duracao_espera_auto = 360  # ~6 segundos a 60 FPS antes de ir pro menu sozinho

        # Botão Pular / Skip
        self.botao_pular = Botao(
            x=self.largura - 140,
            y=25,
            largura=115,
            altura=36,
            texto="PULAR >>",
            cor_base=(25, 25, 30),
            cor_hover=(60, 60, 75),
            cor_texto=(230, 230, 230),
            fonte_tamanho=14,
            borda_raio=8,
            id_botao="btn_skip"
        )
        self.adicionar_botao(self.botao_pular)

    @property
    def concluido(self) -> bool:
        """Indica se a sequência alcançou a tela final com o diálogo completo."""
        return self.fase_atual == self.FASE_COMPLETO

    @property
    def texto_completo(self) -> str:
        """Retorna o texto de todas as linhas unidas por quebras de linha."""
        return "\n\n".join(self.linhas)

    def iniciar(self, tocar_trilha: bool = True):
        """Reinicia a máquina de escrever do início e inicia a trilha Intro.mp3."""
        self.indice_linha = 0
        self.fase_atual = self.FASE_DIGITANDO
        self.caractere_atual = 0
        self.pausa_pontuacao = 0
        self.frame_contador = 0
        self.timer_fase = 0
        self.alpha_linha = 255
        self.alpha_completo = 0
        self.timer_espera_pos_conclusao = 0

        if tocar_trilha:
            try:
                gerenciador_musica.tocar("Intro.mp3", fade_out_ms=0, fade_in_ms=800)
            except Exception:
                pass

    def avancar_proxima_linha(self):
        """Avança para a próxima linha ou para a exibição final completa."""
        self.indice_linha += 1
        if self.indice_linha < len(self.linhas):
            self.fase_atual = self.FASE_DIGITANDO
            self.caractere_atual = 0
            self.pausa_pontuacao = 0
            self.timer_fase = 0
            self.alpha_linha = 255
        else:
            self.fase_atual = self.FASE_COMPLETO
            self.alpha_completo = 0
            self.timer_fase = 0

    def pular_ou_concluir(self) -> str:
        """
        Atalho rápido de avanço:
        - Se está digitando ou apresentando linhas: salta imediatamente para o diálogo completo no final.
        - Se já está no diálogo completo: avança para o menu.
        """
        if self.fase_atual != self.FASE_COMPLETO:
            self.fase_atual = self.FASE_COMPLETO
            self.alpha_completo = 255
            self.indice_linha = len(self.linhas)
            return ""
        return "menu"

    def atualizar_eventos(self, evento: pygame.event.Event, posicao_mouse: Tuple[int, int]) -> Optional[str]:
        """Processa eventos de teclado e mouse para skip e avanço entre linhas."""
        # Clique no botão PULAR vai direto para o menu
        if self.botao_pular.checar_clique(evento, posicao_mouse):
            return "menu"

        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                return "menu"
            if evento.key in (pygame.K_SPACE, pygame.K_RETURN):
                if self.fase_atual == self.FASE_DIGITANDO:
                    # Revela a linha atual inteira
                    linha_txt = self.linhas[self.indice_linha] if self.indice_linha < len(self.linhas) else ""
                    self.caractere_atual = len(linha_txt)
                    self.fase_atual = self.FASE_ESPERA
                    self.timer_fase = 0
                    return None
                elif self.fase_atual in (self.FASE_ESPERA, self.FASE_FADEOUT):
                    # Avança logo para a próxima linha
                    self.avancar_proxima_linha()
                    return None
                elif self.fase_atual == self.FASE_COMPLETO:
                    # Conclui e vai para o menu
                    return "menu"

        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            if not self.botao_pular.rect.collidepoint(posicao_mouse):
                if self.fase_atual == self.FASE_DIGITANDO:
                    linha_txt = self.linhas[self.indice_linha] if self.indice_linha < len(self.linhas) else ""
                    self.caractere_atual = len(linha_txt)
                    self.fase_atual = self.FASE_ESPERA
                    self.timer_fase = 0
                    return None
                elif self.fase_atual in (self.FASE_ESPERA, self.FASE_FADEOUT):
                    self.avancar_proxima_linha()
                    return None
                elif self.fase_atual == self.FASE_COMPLETO:
                    return "menu"

        return None

    def atualizar(self, posicao_mouse: Tuple[int, int], estado_clique_mouse: Tuple[bool, ...]) -> Optional[str]:
        """Avança o tempo, máquina de escrever e fade-outs."""
        self.frame_contador += 1
        self.botao_pular.atualizar(posicao_mouse, estado_clique_mouse)

        if self.fase_atual == self.FASE_DIGITANDO:
            if self.pausa_pontuacao > 0:
                self.pausa_pontuacao -= 1
                return None

            linha_atual = self.linhas[self.indice_linha] if self.indice_linha < len(self.linhas) else ""
            tam_linha = len(linha_atual)

            # Avança caractere a cada 4 quadros (~15 caracteres/segundo)
            if self.frame_contador % 4 == 0:
                if self.caractere_atual < tam_linha:
                    char_atual = linha_atual[self.caractere_atual]
                    self.caractere_atual += 1

                    if char_atual not in (" ", "\n", "\t"):
                        tocar_sfx("Dialogo.wav", volume_relativo=0.6)

                    # Pausas expressivas
                    if char_atual in (".", "!", "?"):
                        self.pausa_pontuacao = 14
                    elif char_atual in (",", ";", ":"):
                        self.pausa_pontuacao = 7
                else:
                    self.fase_atual = self.FASE_ESPERA
                    self.timer_fase = 0

        elif self.fase_atual == self.FASE_ESPERA:
            self.timer_fase += 1
            if self.timer_fase >= self.duracao_espera_linha:
                self.fase_atual = self.FASE_FADEOUT
                self.timer_fase = 0

        elif self.fase_atual == self.FASE_FADEOUT:
            self.timer_fase += 1
            progresso = min(1.0, self.timer_fase / float(self.duracao_fadeout_linha))
            self.alpha_linha = max(0, int(255 * (1.0 - progresso)))
            if self.timer_fase >= self.duracao_fadeout_linha:
                self.avancar_proxima_linha()

        elif self.fase_atual == self.FASE_COMPLETO:
            if self.alpha_completo < 255:
                self.alpha_completo = min(255, self.alpha_completo + int(255 / self.duracao_fadein_completo))

            self.timer_espera_pos_conclusao += 1
            if self.timer_espera_pos_conclusao >= self.duracao_espera_auto:
                return "menu"

        return None

    def desenhar(self):
        """Renderiza a linha individual com fade-out ou o diálogo completo final."""
        self.tela.fill(self.cor_fundo)
        largura_maxima = int(self.largura * 0.85)

        # 1. Exibição de Linha Individual (Digitando / Espera / Fade-out)
        if self.fase_atual in (self.FASE_DIGITANDO, self.FASE_ESPERA, self.FASE_FADEOUT):
            if self.indice_linha < len(self.linhas):
                linha_cheia = self.linhas[self.indice_linha]
                texto_parcial = linha_cheia[:self.caractere_atual]

                # Cursor piscante durante a digitação
                if self.fase_atual == self.FASE_DIGITANDO and (self.frame_contador // 18) % 2 == 0:
                    texto_parcial += "_"

                linhas_quebradas = quebrar_texto(texto_parcial, self.fonte_manga_destaque, largura_maxima)
                altura_linha = self.fonte_manga_destaque.get_linesize()
                altura_bloco = len(linhas_quebradas) * (altura_linha + 6)
                y_base = (self.altura - altura_bloco) // 2

                for i, l in enumerate(linhas_quebradas):
                    if not l:
                        continue
                    surf_txt = self.fonte_manga_destaque.render(l, True, (255, 255, 255))
                    if self.alpha_linha < 255:
                        surf_txt.set_alpha(self.alpha_linha)
                    x_linha = (self.largura - surf_txt.get_width()) // 2
                    self.tela.blit(surf_txt, (x_linha, y_base + i * (altura_linha + 6)))

        # 2. Exibição do Diálogo Completo no Final
        elif self.fase_atual == self.FASE_COMPLETO:
            linhas_renderizar = []
            for linha in self.linhas:
                sublinhas = quebrar_texto(linha, self.fonte_manga, largura_maxima)
                linhas_renderizar.extend(sublinhas)
                linhas_renderizar.append("")  # Espaçamento entre parágrafos

            if linhas_renderizar and linhas_renderizar[-1] == "":
                linhas_renderizar.pop()

            altura_linha = self.fonte_manga.get_linesize()
            espacamento_extra = 4
            espacamento_paragrafo = 12

            altura_total = 0
            for l in linhas_renderizar:
                altura_total += espacamento_paragrafo if l == "" else (altura_linha + espacamento_extra)

            y_atual = max(90, (self.altura - altura_total) // 2)

            for l in linhas_renderizar:
                if l == "":
                    y_atual += espacamento_paragrafo
                    continue
                surf_l = self.fonte_manga.render(l, True, (255, 255, 255))
                if self.alpha_completo < 255:
                    surf_l.set_alpha(self.alpha_completo)
                x_l = (self.largura - surf_l.get_width()) // 2
                self.tela.blit(surf_l, (x_l, y_atual))
                y_atual += altura_linha + espacamento_extra

            # Dica pulsante no rodapé
            alfa_pulsante = int(170 + 75 * ((self.frame_contador % 60) / 60.0))
            alfa_efetivo = min(self.alpha_completo, alfa_pulsante)
            surf_dica = self.fonte_dica.render("[ Clique ou pressione ESPAÇO / ENTER para continuar ]", True, (alfa_efetivo, alfa_efetivo, alfa_efetivo))
            x_dica = (self.largura - surf_dica.get_width()) // 2
            y_dica = self.altura - 50
            self.tela.blit(surf_dica, (x_dica, y_dica))

        # Botão Pular / Skip
        self.botao_pular.desenhar(self.tela)
