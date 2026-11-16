"""Fluxo do desafio de David, com preparação independente da campanha."""

import pygame

from Entidades.Personagem import personagem
from Gameplay.ChefeDavid import criar_david
from Sistemas.GerenciadorAudio import gerenciador_musica
from Sistemas.Inventario import SistemaInventario, inventario_global
from Sistemas.Recursos import caminho_cenario
from Sistemas.SaveSystem import save_global
from Sistemas.SistemaUI import TelaBase
from Telas.TelaClasses import GerenciadorClasses
from Telas.TelaCombate import GerenciadorJogo
from Telas.TelaDescanso import TelaDescanso
from Telas.TelaLoja import GerenciadorLoja
from Telas.TelaPausa import GerenciadorPausa
from Telas.TelaPreparacaoEsgoto import GerenciadorPreparacaoEsgoto
from Telas.TelaVerso import GerenciadorVerso


MUSICA_DESAFIO = "Batalha Esgoto.mp3"
CENARIO_DESAFIO = "Batalha Esgotos.png"


class GerenciadorDesafioEsgoto(TelaBase):
    def __init__(self, tela):
        super().__init__(tela, nome="desafio_esgoto")
        self.etapa = None
        self._estado_anterior = None
        self.verso = None
        self.classe = None
        self.combate = None

    def iniciar(self):
        if not save_global.derrotou_chefes_iniciais():
            return False
        if self._estado_anterior is not None:
            self.encerrar()

        # Substituir os recipientes preserva os objetos da partida anterior.
        self._estado_anterior = (
            dict(personagem.__dict__),
            dict(inventario_global.__dict__),
            gerenciador_musica.proxima_musica or gerenciador_musica.musica_atual or "Menu.mp3",
            gerenciador_musica.verso_atual,
        )
        try:
            personagem.resetar(resetar_cheats=True)
            SistemaInventario.__init__(inventario_global)
            self.verso = None
            self.classe = None
            self.combate = None
            self.verso_tela = GerenciadorVerso(self.tela)
            self.verso_tela.modo = "visualizacao"
            self.verso_tela.alvo_personagem = personagem
            self.verso_tela.aviso = "Escolha seu Verso para enfrentar David Martinez"
            self.classes_tela = GerenciadorClasses(self.tela)
            self.preparacao = GerenciadorPreparacaoEsgoto(self.tela)
            self.loja = GerenciadorLoja(self.tela)
            self.inventario = TelaDescanso(self.tela)
            self.pausa = GerenciadorPausa(self.tela)
            self.pausa.btn_menu.definir_texto("VOLTAR AO ESGOTO")
            self.etapa = "verso"
        except Exception:
            self.encerrar()
            raise
        return True

    def confirmar_classe(self, classe):
        if self._estado_anterior is None or self.verso not in self.verso_tela.versos:
            return False
        if classe not in self.classes_tela.opcoes:
            return False

        personagem.resetar(resetar_cheats=True)
        inventario_global.resetar()
        self.classe = classe
        self.combate = GerenciadorJogo(self.tela)
        self.combate.modo_campanha = False
        self.combate.configurar_classe(self.verso, classe)
        self.verso_tela.aplicar_talentos_ao_personagem(personagem, verso=self.verso)
        self.combate.fase_numero = 10
        self.combate.aplicar_progressao_atributos_fase(10)
        personagem.nivel = 10
        personagem.xp = 900
        personagem.pontos_atributo = 27
        personagem.max_hp = 250
        personagem.max_mp = 35
        personagem.hp = personagem.max_hp
        personagem.mp = personagem.max_mp

        for item_id, quantidade in (
            ("pocao_vida_reforcada", 3),
            ("cha_mana", 3),
            ("cafe_expresso", 1),
            ("capacete_de_ferro", 1),
            ("botas_velozes", 1),
            ("polidor_itens", 1),
        ):
            inventario_global.adicionar_item_por_id(item_id, quantidade)
        inventario_global.adicionar_sucata(12)
        inventario_global.item_bilhete.quantidade = 0
        for equipamento in list(inventario_global.equipamentos_inventario):
            inventario_global.equipar(equipamento, jogador=personagem)

        self.loja.configurar_loja("barista", sucesso=True)
        self.loja.titulo_tela = "SUPRIMENTOS DOS ESGOTOS"
        self.loja.subtitulo_tela = "Troque sucatas por provisões e equipamentos antes de enfrentar David Martinez."
        self.loja.btn_sair.definir_texto("VOLTAR À PREPARAÇÃO")
        self.inventario.jogadores = [personagem]
        self.inventario.btn_continuar.definir_texto("VOLTAR À PREPARAÇÃO")
        self.inventario.mensagem = "Distribua seus 27 pontos e prepare seus equipamentos."
        self.preparacao.configurar(self.verso, classe)
        self.etapa = "preparacao"
        return True

    def iniciar_combate(self):
        if self.combate is None or self.etapa != "preparacao":
            return False
        personagem.hp = personagem.max_hp
        personagem.mp = personagem.max_mp
        personagem.limpar_status()
        self.combate.partida_atual = 1
        self.combate.total_partidas = 1
        self.combate.fase_numero = 10
        self.combate.ordem_turnos = [personagem, criar_david()]
        self.combate.evento_neutro = None
        self.combate.pontos_jogo = 0
        self.combate.rodada_numero = 1
        self.combate.clique_anterior = False
        self.combate.reiniciar()
        self.combate.fundo_luta = pygame.image.load(caminho_cenario(CENARIO_DESAFIO)).convert()
        self.combate.fundo_luta_redimensionado = None
        self.combate.fundo_luta_tamanho = None
        self.combate.musica_luta = MUSICA_DESAFIO
        self.combate.mensagem_log = "David Martinez aguarda nas profundezas dos esgotos!"
        gerenciador_musica.tocar(MUSICA_DESAFIO)
        self.etapa = "combate"
        return True

    def encerrar(self):
        if self._estado_anterior is not None:
            estado_personagem, estado_inventario, musica, verso = self._estado_anterior
            personagem.__dict__.clear()
            personagem.__dict__.update(estado_personagem)
            inventario_global.__dict__.clear()
            inventario_global.__dict__.update(estado_inventario)
            gerenciador_musica.definir_verso(verso)
            gerenciador_musica.tocar(musica)
            self._estado_anterior = None
        self.etapa = None
        return "sewer"

    def _abrir_pausa(self):
        self.pausa.abrir(self.etapa)
        self.etapa = "pausa"

    def atualizar_eventos(self, evento, posicao_mouse):
        if self.etapa is None:
            return None
        if self.etapa == "verso":
            resultado = self.verso_tela.atualizar_eventos(evento, posicao_mouse)
            if self.verso_tela.voltar_clicado:
                self.verso_tela.voltar_clicado = False
                return self.encerrar()
            if resultado in self.verso_tela.versos:
                self.verso = resultado
                self.classes_tela.aviso = f"{resultado} | Escolha sua classe para enfrentar David Martinez"
                self.etapa = "classe"
        elif self.etapa == "classe":
            resultado = self.classes_tela.atualizar_eventos(evento, posicao_mouse)
            if self.classes_tela.voltar_clicado:
                self.classes_tela.voltar_clicado = False
                self.etapa = "verso"
            elif resultado:
                self.confirmar_classe(resultado)
        elif self.etapa == "preparacao":
            resultado = self.preparacao.atualizar_eventos(evento, posicao_mouse)
            if resultado == "lutar":
                self.iniciar_combate()
            elif resultado in ("loja", "inventario"):
                self.etapa = resultado
            elif resultado == "voltar":
                return self.encerrar()
        elif self.etapa in ("loja", "inventario"):
            if evento.type == pygame.KEYDOWN and evento.key in (pygame.K_ESCAPE, pygame.K_p):
                self._abrir_pausa()
                return None
            resultado = self._tela_atual().atualizar_eventos(evento, posicao_mouse)
            if resultado in ("continuar", "voltar"):
                self.etapa = "preparacao"
            elif resultado == "pausa":
                self._abrir_pausa()
        elif self.etapa == "combate":
            if evento.type == pygame.KEYDOWN and evento.key in (pygame.K_ESCAPE, pygame.K_p):
                self._abrir_pausa()
            else:
                self.combate.processar_evento(evento, posicao_mouse)
        elif self.etapa == "pausa":
            resultado = self.pausa.atualizar_eventos(evento, posicao_mouse)
            if resultado == "continuar":
                self.etapa = self.pausa.estado_anterior
                self.pausa.fechar()
                if self.etapa == "combate":
                    self.combate.clique_anterior = False
            elif resultado == "menu":
                return self.encerrar()
            elif resultado == "config":
                return "config"
        return None

    def _tela_atual(self):
        return {
            "verso": self.verso_tela,
            "classe": self.classes_tela,
            "preparacao": self.preparacao,
            "loja": self.loja,
            "inventario": self.inventario,
            "combate": self.combate,
            "pausa": self.pausa,
        }.get(self.etapa)

    def atualizar(self, posicao_mouse, estado_clique_mouse):
        if self.etapa is None:
            return
        resultado = self._tela_atual().atualizar(posicao_mouse, estado_clique_mouse)
        if self.etapa == "combate":
            if resultado == "pausa":
                self._abrir_pausa()
            elif resultado in ("fim_jogo", "vitoria", "game_over", "fugiu", "batalha_encerrada"):
                resultado = {
                    "fim_jogo": "vitoria", "game_over": "derrota", "batalha_encerrada": "fugiu",
                }.get(resultado, resultado)
                personagem.limpar_status()
                personagem.minions.clear()
                personagem.hp = personagem.max_hp
                personagem.mp = personagem.max_mp
                self.preparacao.definir_resultado(resultado)
                self.etapa = "preparacao"
                gerenciador_musica.tocar("Menu.mp3")

    def desenhar(self):
        if self.etapa is not None:
            self._tela_atual().desenhar()
