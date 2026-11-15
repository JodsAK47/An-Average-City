import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

BASE_DIR = Path(__file__).resolve().parent.parent / "An Average City"
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pygame

if not pygame.get_init():
    pygame.init()
pygame.display.set_mode((1000, 800))

from Entidades.Inimigo import Inimigo
from Entidades.Personagem import Personagem, personagem
from Gameplay.DesafioEsgoto import GerenciadorDesafioEsgoto
from Sistemas.Conquistas import SistemaConquistas
from Sistemas.GerenciadorAudio import gerenciador_musica
from Sistemas.Inventario import SistemaInventario, inventario_global
from Sistemas.SaveSystem import GerenciadorSave, save_global
from Telas.TelaCombate import TelaCombate
from Telas.TelaConquistas import GerenciadorConquistasTela


VERSOS = ("Sobrevivente", "Agente", "Feiticeiro", "Cyberpunk")


class TestConquistasEspeciais(unittest.TestCase):
    def setUp(self):
        self.estado_personagem = dict(personagem.__dict__)
        self.estado_inventario = dict(inventario_global.__dict__)
        self.addCleanup(self.restaurar_estado)
        temporario = self.enterContext(tempfile.TemporaryDirectory())
        self.arquivo_save = Path(temporario) / "save.json"
        self.enterContext(patch("Sistemas.SaveSystem.ARQUIVO_SAVE", str(self.arquivo_save)))
        self.enterContext(patch("Sistemas.SaveSystem.CAMINHO_SAVES", temporario))
        self.enterContext(patch.multiple(
            save_global,
            conquistas=[],
            versos_concluidos=[],
            david_martins_derrotado=False,
            progresso_versos={},
            habilidades_desabilitadas={},
        ))
        self.enterContext(patch.object(gerenciador_musica, "tocar"))
        self.enterContext(patch.object(gerenciador_musica, "definir_verso"))
        self.enterContext(patch("Sistemas.GerenciadorAudio.tocar_sfx"))
        personagem.resetar(resetar_cheats=True)
        SistemaInventario.__init__(inventario_global)
        self.sistema = SistemaConquistas()
        self.enterContext(patch("Sistemas.Conquistas.sistema_conquistas", self.sistema))
        self.enterContext(patch("Telas.TelaConquistas.sistema_conquistas", self.sistema))
        self.superficie = pygame.Surface((1000, 800))

    def restaurar_estado(self):
        personagem.__dict__.clear()
        personagem.__dict__.update(self.estado_personagem)
        inventario_global.__dict__.clear()
        inventario_global.__dict__.update(self.estado_inventario)

    def completar_requisitos(self):
        for verso in VERSOS:
            self.sistema.registrar_vitoria_campanha(verso)
        self.sistema.registrar_vitoria_david()

    def notificacoes_easter_egg(self, sistema=None):
        sistema = sistema or self.sistema
        return [notificacao for notificacao in sistema.notificacoes if notificacao["nome"] == "Easter Egg"]

    def obter_platina(self):
        for conquista in self.sistema.conquistas:
            if conquista.id not in ("easter_egg", "platina"):
                self.sistema.desbloquear(conquista.id)
        self.completar_requisitos()

    def preparar_vitoria(self, verso="Cyberpunk", partida=10, total=10, campanha=True, nome_chefe="Adam Smasher"):
        combate = TelaCombate(self.superficie)
        combate.classe_atual = verso
        combate.partida_atual = partida
        combate.total_partidas = total
        combate.modo_campanha = campanha
        chefe = Inimigo(700, 300, 100, "pixil_cyber.png", nome=nome_chefe, tipo="chefe")
        chefe.hp = 0
        personagem.hp = personagem.max_hp
        combate.ordem_turnos = [personagem, chefe]
        return combate

    def test_requisitos_completam_em_ordens_diferentes_e_somente_no_ultimo(self):
        ordens = (
            ("David", *VERSOS),
            (*VERSOS, "David"),
            ("Cyberpunk", "David", "Feiticeiro", "Sobrevivente", "Agente"),
        )
        for ordem in ordens:
            with self.subTest(ordem=ordem):
                self.sistema.resetar_todas()
                for indice, requisito in enumerate(ordem):
                    if requisito == "David":
                        self.sistema.registrar_vitoria_david()
                    else:
                        self.sistema.registrar_vitoria_campanha(requisito)
                    self.assertEqual(self.sistema.esta_desbloqueada("easter_egg"), indice == len(ordem) - 1)
                self.assertEqual([n["progresso"] for n in self.notificacoes_easter_egg()], [33, 67, 100])

    def test_vitorias_de_batalha_e_conquistas_dos_chefes_nao_substituem_campanhas(self):
        for identificador in (
            "vitoria_sobrevivente", "vitoria_agente", "vitoria_feiticeiro", "vitoria_cyberpunk",
            "chefe_sukuna", "chefe_charlie", "chefe_estraga_prazeres", "chefe_derrotado",
        ):
            self.sistema.desbloquear(identificador)
        self.sistema.registrar_vitoria_david()
        self.assertEqual(save_global.versos_concluidos, [])
        self.assertFalse(self.sistema.esta_desbloqueada("easter_egg"))
        self.assertFalse(self.sistema.desbloquear("easter_egg"))

    def test_easter_egg_so_aparece_apos_completar_um_requisito_inteiro(self):
        self.assertNotIn("easter_egg", [c.id for c in self.sistema.obter_conquistas_visiveis()])
        self.assertIn("platina", [c.id for c in self.sistema.obter_conquistas_visiveis()])
        self.assertEqual(self.sistema.obter_progresso_easter_egg(), 0)
        for verso in VERSOS[:2]:
            self.sistema.registrar_vitoria_campanha(verso)
            self.assertEqual(self.sistema.obter_progresso_easter_egg(), 0)
            self.assertNotIn("easter_egg", [c.id for c in self.sistema.obter_conquistas_visiveis()])
            self.assertEqual(self.notificacoes_easter_egg(), [])
        self.sistema.registrar_vitoria_campanha(VERSOS[2])
        self.assertEqual(self.sistema.obter_progresso_easter_egg(), 33)
        self.assertIn("easter_egg", [c.id for c in self.sistema.obter_conquistas_visiveis()])
        self.assertFalse(self.sistema.esta_desbloqueada("easter_egg"))

        for primeiro_requisito in ("David", "Cyberpunk"):
            with self.subTest(primeiro_requisito=primeiro_requisito):
                self.sistema.resetar_todas()
                if primeiro_requisito == "David":
                    self.sistema.registrar_vitoria_david()
                else:
                    self.sistema.registrar_vitoria_campanha(primeiro_requisito)
                self.assertEqual(self.sistema.obter_progresso_easter_egg(), 33)
                self.assertIn("easter_egg", [c.id for c in self.sistema.obter_conquistas_visiveis()])
                self.assertFalse(self.sistema.esta_desbloqueada("easter_egg"))
                self.assertEqual([n["progresso"] for n in self.notificacoes_easter_egg()], [33])

    def test_progresso_notifica_cada_requisito_uma_vez_e_conclui_sem_duplicata(self):
        self.completar_requisitos()
        self.assertIn("easter_egg", [c.id for c in self.sistema.obter_conquistas_visiveis()])
        self.assertEqual(self.sistema.obter_progresso_easter_egg(), 100)
        self.assertTrue(self.sistema.esta_desbloqueada("easter_egg"))
        for _ in range(3):
            self.completar_requisitos()
            self.sistema.verificar_conquistas_especiais()
            self.sistema.salvar()
        self.assertEqual([n["progresso"] for n in self.notificacoes_easter_egg()], [33, 67, 100])
        self.assertEqual(len(save_global.versos_concluidos), 4)
        self.sistema.desenhar_notificacao(self.superficie)

    def test_descricao_nao_revela_os_requisitos(self):
        descricao = self.sistema.mapa_conquistas["easter_egg"].como_liberar.lower()
        self.assertTrue(descricao)
        for pista in ("sobrevivente", "agente", "feiticeiro", "cyberpunk", "david", "martins", "zere", "zerar"):
            self.assertNotIn(pista, descricao)

    def test_platina_exige_todas_as_outras_incluindo_easter_egg(self):
        for conquista in self.sistema.conquistas:
            if conquista.id not in ("easter_egg", "platina"):
                self.sistema.desbloquear(conquista.id)
        self.assertFalse(self.sistema.esta_platinado())
        self.assertFalse(self.sistema.desbloquear("platina"))
        self.completar_requisitos()
        self.assertTrue(self.sistema.esta_platinado())
        self.assertEqual(self.sistema.total_desbloqueadas(), self.sistema.total_conquistas())
        self.sistema.salvar()
        self.sistema.verificar_conquistas_especiais()
        self.assertEqual([n["nome"] for n in self.sistema.notificacoes].count("Platina"), 1)

    def test_progresso_parcial_e_conquistas_persistem_apos_recarregar(self):
        self.sistema.registrar_vitoria_campanha("Sobrevivente")
        self.sistema.registrar_vitoria_david()
        novo_save = GerenciadorSave()
        self.assertEqual(novo_save.versos_concluidos, ["Sobrevivente"])
        self.assertTrue(novo_save.david_martins_derrotado)
        self.assertEqual(self.sistema.obter_progresso_easter_egg(), 33)
        with patch("Sistemas.SaveSystem.save_global", novo_save):
            novo_sistema = SistemaConquistas()
            self.assertEqual(novo_sistema.obter_progresso_easter_egg(), 33)
            self.assertIn("easter_egg", [c.id for c in novo_sistema.obter_conquistas_visiveis()])
            self.assertEqual(self.notificacoes_easter_egg(novo_sistema), [])
            novo_sistema.registrar_vitoria_david()
            novo_sistema.registrar_vitoria_campanha("Sobrevivente")
            novo_sistema.verificar_conquistas_especiais()
            novo_sistema.salvar()
            self.assertEqual(self.notificacoes_easter_egg(novo_sistema), [])
            for verso in VERSOS[1:]:
                novo_sistema.registrar_vitoria_campanha(verso)
            self.assertTrue(novo_sistema.esta_desbloqueada("easter_egg"))
            self.assertEqual([n["progresso"] for n in self.notificacoes_easter_egg(novo_sistema)], [67, 100])
            recarregado = GerenciadorSave()
            self.assertIn("easter_egg", recarregado.conquistas)
            self.assertEqual(set(recarregado.versos_concluidos), set(VERSOS))
            with patch("Sistemas.SaveSystem.save_global", recarregado):
                sistema_recarregado = SistemaConquistas()
                self.assertEqual(sistema_recarregado.obter_progresso_easter_egg(), 100)
                self.assertEqual(self.notificacoes_easter_egg(sistema_recarregado), [])

    def test_save_antigo_nao_inventa_zeramentos_e_reset_limpa_tudo(self):
        self.arquivo_save.write_text(json.dumps({
            "conquistas": ["chefe_sukuna", "vitoria_cyberpunk"],
        }), encoding="utf-8")
        antigo = GerenciadorSave()
        self.assertEqual(antigo.versos_concluidos, [])
        self.assertFalse(antigo.david_martins_derrotado)
        self.obter_platina()
        self.sistema.resetar_todas()
        self.assertFalse(self.sistema.esta_platinado())
        self.assertFalse(save_global.david_martins_derrotado)
        self.assertEqual(save_global.versos_concluidos, [])
        self.assertEqual(save_global.conquistas, [])
        self.assertEqual(self.sistema.notificacoes, [])
        self.assertEqual(self.sistema.obter_progresso_easter_egg(), 0)
        self.assertNotIn("easter_egg", [c.id for c in self.sistema.obter_conquistas_visiveis()])
        novo_save = GerenciadorSave()
        self.assertEqual(novo_save.versos_concluidos, [])
        self.assertFalse(novo_save.david_martins_derrotado)

    def test_campanha_so_registra_no_final_em_modo_campanha(self):
        for partida, total, campanha in ((1, 10, True), (1, 1, True), (10, 10, False)):
            with self.subTest(partida=partida, total=total, campanha=campanha):
                combate = self.preparar_vitoria(partida=partida, total=total, campanha=campanha)
                combate.atualizar((0, 0), (False, False, False))
                self.assertEqual(save_global.versos_concluidos, [])
        combate = self.preparar_vitoria()
        combate.atualizar((0, 0), (False, False, False))
        self.assertEqual(save_global.versos_concluidos, ["Cyberpunk"])

    def test_zeramento_cooperativo_registra_os_dois_versos_participantes(self):
        combate = self.preparar_vitoria(verso="Sobrevivente", nome_chefe="Charlie")
        segundo = Personagem(150, 350, nome="Jogador 2")
        combate.duas_pessoas = True
        combate.personagem2 = segundo
        combate.classe_jogador2 = "Cyberpunk"
        combate.ordem_turnos.insert(1, segundo)
        combate.atualizar((0, 0), (False, False, False))
        self.assertEqual(set(save_global.versos_concluidos), {"Sobrevivente", "Cyberpunk"})

    def test_david_conta_imediatamente_na_vitoria_mas_nao_na_derrota_simultanea(self):
        derrota = self.preparar_vitoria(partida=1, total=1, campanha=False, nome_chefe="David Martins")
        personagem.hp = 0
        derrota.atualizar((0, 0), (False, False, False))
        self.assertFalse(save_global.david_martins_derrotado)
        vitoria = self.preparar_vitoria(partida=1, total=1, campanha=False, nome_chefe="David Martins")
        vitoria.atualizar((0, 0), (False, False, False))
        self.assertTrue(save_global.david_martins_derrotado)
        self.assertEqual(save_global.versos_concluidos, [])
        self.assertGreater(vitoria.cooldown_feedback, 0)

    def test_sair_do_desafio_restaura_personagem_sem_desfazer_conquista(self):
        save_global.conquistas[:] = ["chefe_sukuna", "chefe_charlie", "chefe_estraga_prazeres"]
        save_global.versos_concluidos[:] = VERSOS
        atributos_anteriores = personagem.atributos
        desafio = GerenciadorDesafioEsgoto(self.superficie)
        self.assertTrue(desafio.iniciar())
        desafio.verso = "Cyberpunk"
        self.assertTrue(desafio.confirmar_classe("Magia"))
        self.assertTrue(desafio.iniciar_combate())
        for inimigo in desafio.combate.ordem_turnos:
            if desafio.combate.eh_inimigo(inimigo):
                inimigo.hp = 0
        desafio.atualizar((0, 0), (False, False, False))
        self.assertTrue(save_global.david_martins_derrotado)
        self.assertTrue(self.sistema.esta_desbloqueada("easter_egg"))
        desafio.encerrar()
        self.assertIs(personagem.atributos, atributos_anteriores)
        self.assertTrue(save_global.david_martins_derrotado)
        self.assertIn("easter_egg", GerenciadorSave().conquistas)

    def test_menu_seleciona_conquista_revelada_e_remove_selecao_apos_reset(self):
        tela = GerenciadorConquistasTela(self.superficie)
        self.sistema.registrar_vitoria_david()
        self.assertEqual(self.sistema.obter_progresso_easter_egg(), 33)
        self.assertFalse(self.sistema.esta_desbloqueada("easter_egg"))
        visiveis = self.sistema.obter_conquistas_visiveis()
        indice = next(i for i, conquista in enumerate(visiveis) if conquista.id == "easter_egg")
        tela.scroll_y = max(0, len(visiveis) * 86 + 20 - tela.rect_lista.height)
        y = tela.rect_lista.y + 10 + indice * 86 - int(tela.scroll_y) + 38
        tela.atualizar_eventos(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1), (tela.rect_lista.centerx, y))
        self.assertEqual(tela.conquista_selecionada.id, "easter_egg")
        tela.desenhar()
        self.sistema.resetar_todas()
        tela.atualizar((0, 0), (False, False, False))
        self.assertNotEqual(tela.conquista_selecionada.id, "easter_egg")
        tela.desenhar()

    def test_tema_dourado_e_brilhos_somente_com_platina(self):
        tela = GerenciadorConquistasTela(self.superficie)
        tela.atualizar((0, 0), (False, False, False))
        self.assertFalse(tela.platinado)
        self.assertEqual(tela.brilhos, [])
        self.obter_platina()
        for _ in range(180):
            tela.atualizar((0, 0), (False, False, False))
        self.assertTrue(tela.platinado)
        self.assertGreater(len(tela.brilhos), 0)
        self.assertLessEqual(len(tela.brilhos), 36)
        tela.desenhar()
        self.sistema.resetar_todas()
        tela.atualizar((0, 0), (False, False, False))
        self.assertFalse(tela.platinado)
        self.assertEqual(tela.brilhos, [])
        tela.desenhar()


if __name__ == "__main__":
    unittest.main()
