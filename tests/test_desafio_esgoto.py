import os
import sys
import unittest
from itertools import combinations
from unittest.mock import patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "An Average City"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import pygame

if not pygame.get_init():
    pygame.init()
pygame.display.set_mode((1000, 800))

from Entidades.Personagem import personagem
from Gameplay.ChefeDavid import criar_david
from Gameplay.DesafioEsgoto import GerenciadorDesafioEsgoto
from Gameplay.GeracaoFases import GeradorFase, listar_inimigos_disponiveis
from Sistemas.Conquistas import sistema_conquistas
from Sistemas.GerenciadorAudio import gerenciador_musica
from Sistemas.Inventario import Equipamento, SistemaInventario, inventario_global
from Sistemas.Recursos import caminho_cenario
from Sistemas.SaveSystem import save_global
from Telas.TelaSewer import GerenciadorSewerTela


CONQUISTAS_CHEFES = ("chefe_sukuna", "chefe_charlie", "chefe_estraga_prazeres")


class TestDesafioEsgoto(unittest.TestCase):
    def setUp(self):
        self.estado_personagem = dict(personagem.__dict__)
        self.estado_inventario = dict(inventario_global.__dict__)
        self.addCleanup(self.restaurar_estado)
        self.enterContext(patch.multiple(
            save_global,
            conquistas=list(CONQUISTAS_CHEFES),
            progresso_versos={},
            habilidades_desabilitadas={},
        ))
        self.enterContext(patch.object(save_global, "salvar"))
        self.enterContext(patch.object(sistema_conquistas, "desbloquear"))
        self.musica = self.enterContext(patch.object(gerenciador_musica, "tocar"))
        self.enterContext(patch.object(gerenciador_musica, "definir_verso"))
        self.enterContext(patch.multiple(
            gerenciador_musica,
            musica_atual="Menu.mp3",
            proxima_musica=None,
            verso_atual="Sobrevivente",
        ))
        personagem.resetar(resetar_cheats=True)
        SistemaInventario.__init__(inventario_global)
        self.superficie = pygame.Surface((1000, 800))

    def restaurar_estado(self):
        personagem.__dict__.clear()
        personagem.__dict__.update(self.estado_personagem)
        inventario_global.__dict__.clear()
        inventario_global.__dict__.update(self.estado_inventario)

    def novo_desafio(self):
        return GerenciadorDesafioEsgoto(self.superficie)

    def clicar(self, tela, posicao):
        tela.atualizar_eventos(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1), posicao)
        return tela.atualizar_eventos(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1), posicao)

    def preparar(self, verso="Feiticeiro", classe="Magia"):
        desafio = self.novo_desafio()
        self.assertTrue(desafio.iniciar())
        desafio.verso = verso
        self.assertTrue(desafio.confirmar_classe(classe))
        return desafio

    def test_entrada_exige_as_tres_conquistas_sem_modificar_jogador_bloqueado(self):
        tela_esgoto = GerenciadorSewerTela(self.superficie)
        for quantidade in range(4):
            for conquistas in combinations(CONQUISTAS_CHEFES, quantidade):
                with self.subTest(conquistas=conquistas):
                    save_global.conquistas[:] = ["chefe_derrotado", "vitoria_cyberpunk", *conquistas]
                    atributos_antes = personagem.atributos
                    consumiveis_antes = inventario_global.consumiveis
                    desafio = self.novo_desafio()
                    self.assertEqual(desafio.iniciar(), quantidade == 3)
                    resultado_clique = self.clicar(tela_esgoto, tela_esgoto.rect_porta_restrita.center)
                    if quantidade == 3:
                        self.assertEqual(resultado_clique, "desafio_david")
                        self.assertEqual(desafio.etapa, "verso")
                        desafio.encerrar()
                    else:
                        self.assertIsNone(resultado_clique)
                        self.assertIs(personagem.atributos, atributos_antes)
                        self.assertIs(inventario_global.consumiveis, consumiveis_antes)

    def test_escolha_de_verso_e_classe_precede_preparacao_nivel_dez(self):
        desafio = self.novo_desafio()
        self.assertTrue(desafio.iniciar())
        self.assertFalse(desafio.iniciar_combate())
        self.assertFalse(desafio.confirmar_classe("Magia"))
        self.clicar(desafio, desafio.verso_tela.esferas_rects["Feiticeiro"].center)
        self.clicar(desafio, desafio.verso_tela.botao_selecionar.rect.center)
        self.assertEqual(desafio.etapa, "classe")
        self.assertEqual(desafio.verso, "Feiticeiro")
        self.clicar(desafio, desafio.classes_tela.rects["Magia"].center)
        self.clicar(desafio, desafio.classes_tela.botao_selecionar.rect.center)
        self.assertEqual(desafio.etapa, "preparacao")
        self.assertEqual(desafio.classe, "Magia")
        self.assertEqual((personagem.nivel, personagem.xp, personagem.pontos_atributo), (10, 900, 27))
        self.assertEqual((personagem.hp, personagem.mp), (personagem.max_hp, personagem.max_mp))
        self.assertTrue(personagem.ataques)
        self.assertEqual(inventario_global.materiais_totais(), 12)
        self.assertGreaterEqual(sum(item.quantidade for item in inventario_global.consumiveis), 7)
        self.assertGreaterEqual(len(inventario_global.todos_equipamentos_equipados()), 3)
        desafio.desenhar()

    def test_loja_e_inventario_retornam_sem_repor_compras_ou_perder_distribuicao(self):
        desafio = self.preparar()
        self.clicar(desafio, desafio.preparacao.botoes["loja"].rect.center)
        self.assertEqual(desafio.etapa, "loja")
        item = next(item for item in desafio.loja.itens_catalogo if item["id"] == "pocao_vida")
        self.assertTrue(desafio.loja._executar_compra(item))
        quantidade_comprada = sum(consumivel.quantidade for consumivel in inventario_global.consumiveis)
        sucata_apos_compra = inventario_global.materiais_totais()
        self.clicar(desafio, desafio.loja.btn_sair.rect.center)
        self.assertEqual(desafio.etapa, "preparacao")
        self.clicar(desafio, desafio.preparacao.botoes["inventario"].rect.center)
        self.assertEqual(desafio.etapa, "inventario")
        botao_con = next(botao for botao, atributo in desafio.inventario.botoes_up if atributo == "Con")
        vida_antes = personagem.max_hp
        self.clicar(desafio, botao_con.rect.center)
        self.assertEqual(personagem.max_hp, vida_antes + 10)
        self.assertEqual(personagem.pontos_atributo, 26)
        self.clicar(desafio, desafio.inventario.btn_continuar.rect.center)
        self.assertEqual(desafio.etapa, "preparacao")
        self.clicar(desafio, desafio.preparacao.botoes["loja"].rect.center)
        self.assertEqual(item["comprados"], 1)
        self.assertEqual(inventario_global.materiais_totais(), sucata_apos_compra)
        self.assertEqual(sum(consumivel.quantidade for consumivel in inventario_global.consumiveis), quantidade_comprada)

    def test_david_e_exclusivo_e_combate_usa_cenario_e_musica_do_esgoto(self):
        david = criar_david()
        self.assertEqual((david.nome, david.tipo, david.especial), ("David Martins", "chefe", True))
        self.assertEqual(david.mp, david.max_mp)
        self.assertTrue(any(david.obter_habilidade(nome).custo_mp == 0 for nome in david.ataques))
        self.assertNotIn("David Martins", [dados["nome"] for dados in listar_inimigos_disponiveis(incluir_chefes=True)])
        self.assertEqual(GeradorFase().gerar_chefe_verso("Cyberpunk").nome, "Adam Smasher")
        desafio = self.preparar("Cyberpunk", "Distância")
        self.assertTrue(desafio.iniciar_combate())
        self.assertEqual(desafio.etapa, "combate")
        inimigos = [entidade for entidade in desafio.combate.ordem_turnos if desafio.combate.eh_inimigo(entidade)]
        self.assertEqual([inimigo.nome for inimigo in inimigos], ["David Martins"])
        self.assertEqual(desafio.combate.musica_luta, "Batalha Esgoto.mp3")
        self.musica.assert_called_with("Batalha Esgoto.mp3")
        esperado = pygame.image.load(caminho_cenario("Batalha Esgotos.png")).convert()
        self.assertEqual(pygame.image.tobytes(desafio.combate.fundo_luta, "RGB"), pygame.image.tobytes(esperado, "RGB"))
        self.assertEqual(desafio.combate.total_partidas, 1)
        desafio.desenhar()

    def test_resultados_retornam_a_preparacao_e_repeticao_preserva_progresso(self):
        desafio = self.preparar("Agente", "Invocador")
        atributos_originais = dict(personagem.atributos)
        consumiveis_originais = [(item.nome, item.quantidade) for item in inventario_global.consumiveis]
        for resultado, mensagem in (("fim_jogo", "vitoria"), ("vitoria", "vitoria"), ("game_over", "derrota"), ("fugiu", "fugiu")):
            with self.subTest(resultado=resultado):
                self.assertTrue(desafio.iniciar_combate())
                personagem.aplicar_status("Veneno")
                with patch.object(desafio.combate, "atualizar", return_value=resultado):
                    desafio.atualizar((0, 0), (False, False, False))
                self.assertEqual(desafio.etapa, "preparacao")
                self.assertEqual(desafio.preparacao.resultado, mensagem)
                self.assertFalse(personagem.envenenado)
                self.assertEqual(personagem.minions, [])
                self.assertEqual(personagem.nivel, 10)
                self.assertEqual(personagem.atributos, atributos_originais)
                self.assertEqual([(item.nome, item.quantidade) for item in inventario_global.consumiveis], consumiveis_originais)

    def test_pausa_na_loja_retorna_ao_mesmo_estado_e_saida_restaura_partida(self):
        personagem.nivel = 4
        personagem.xp = 300
        personagem.hp = 71
        personagem.mp = 6
        personagem.talentos = {"S1"}
        arma = Equipamento("Arma anterior", {"For": 7}, categoria="arma")
        inventario_global.equipar(arma)
        inventario_global.adicionar_consumivel("Provisão anterior", "Item anterior", 35, 0)
        atributos_originais = personagem.atributos
        talentos_originais = personagem.talentos
        consumiveis_originais = inventario_global.consumiveis
        desafio = self.preparar()
        self.clicar(desafio, desafio.preparacao.botoes["loja"].rect.center)
        tecla_escape = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        desafio.atualizar_eventos(tecla_escape, (0, 0))
        self.assertEqual(desafio.etapa, "pausa")
        desafio.atualizar_eventos(tecla_escape, (0, 0))
        self.assertEqual(desafio.etapa, "loja")
        self.assertEqual(desafio.encerrar(), "sewer")
        self.assertIsNone(desafio.etapa)
        self.assertIs(personagem.atributos, atributos_originais)
        self.assertIs(personagem.talentos, talentos_originais)
        self.assertEqual((personagem.nivel, personagem.xp, personagem.hp, personagem.mp), (4, 300, 71, 6))
        self.assertIs(inventario_global.equipamento_slot, arma)
        self.assertIs(inventario_global.consumiveis, consumiveis_originais)
        self.assertEqual([(item.nome, item.quantidade) for item in consumiveis_originais], [("Provisão anterior", 1)])
        self.assertEqual(arma.atributos_bonus, {"For": 7})

    def test_reconfigurar_classe_nao_acumula_bonus_ou_niveis(self):
        desafio = self.preparar("Feiticeiro", "Magia")
        atributos_magia = dict(personagem.atributos)
        self.assertTrue(desafio.confirmar_classe("Magia"))
        self.assertEqual(personagem.atributos, atributos_magia)
        self.assertTrue(desafio.confirmar_classe("Físico"))
        self.assertGreater(personagem.atributos["For"], personagem.atributos["Int"])
        self.assertTrue(desafio.confirmar_classe("Magia"))
        self.assertEqual(personagem.atributos, atributos_magia)
        self.assertEqual((personagem.nivel, personagem.xp, personagem.pontos_atributo), (10, 900, 27))


if __name__ == "__main__":
    unittest.main()
