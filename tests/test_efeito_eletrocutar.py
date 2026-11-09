import os
import sys
import unittest
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "An Average City"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import pygame
if not pygame.get_init():
    pygame.init()

from Entidades.Personagem import Personagem
from Entidades.Inimigo import Inimigo
from Entidades.Minion import Minion
from Telas.TelaCombate import TelaCombate, personagem
from Sistemas.SistemaEfeitos import obter_efeitos_ativos, carregar_icone_efeito, CONFIG_EFEITOS


class TestEfeitoEletrocutar(unittest.TestCase):
    def setUp(self):
        self.superficie = pygame.Surface((1000, 700))
        self.combate = TelaCombate(self.superficie)
        self.personagem = personagem

    def test_config_efeito_e_sprite_choque(self):
        """Verifica se o efeito eletrocutar está configurado com Choque.png."""
        self.assertIn("eletrocutar", CONFIG_EFEITOS)
        cfg = CONFIG_EFEITOS["eletrocutar"]
        self.assertEqual(cfg["arquivo"], "Choque.png")
        self.assertEqual(cfg["tipo"], "debuff")

        # Testar carregamento do ícone
        icone = carregar_icone_efeito("eletrocutar", 20)
        self.assertIsNotNone(icone)
        self.assertEqual(icone.get_size(), (20, 20))

    def test_aplicar_status_eletrocutar_na_entidade(self):
        """Aplicar status eletrocutar deve durar 2 rodadas e atordoar por 1 rodada."""
        inimigo = Inimigo(700, 300, 100, "Inimigo1.png", nome="Alvo")
        self.assertFalse(inimigo.eletrocutado)
        self.assertFalse(inimigo.atordoado)

        inimigo.aplicar_status("Eletrocutar")
        self.assertTrue(inimigo.eletrocutado)
        self.assertEqual(inimigo.turnos_eletrocutado, 2)
        self.assertTrue(inimigo.atordoado)

    def test_obter_efeitos_ativos_retorna_choque(self):
        """obter_efeitos_ativos deve retornar o ícone de Choque com a duração correta."""
        inimigo = Inimigo(700, 300, 100, "Inimigo1.png", nome="Alvo")
        inimigo.aplicar_status("Eletrocutar")

        efeitos = obter_efeitos_ativos(inimigo)
        nomes = [e["nome"] for e in efeitos]
        self.assertIn("Eletrocutado", nomes)

        # Como está eletrocutado, o ícone de Choque já representa o status de CC elétrico
        efeito_choque = next(e for e in efeitos if e["nome"] == "Eletrocutado")
        self.assertEqual(efeito_choque["arquivo"], "Choque.png")
        self.assertIn("2 rodadas", efeito_choque.get("duracao_texto", ""))

    def test_combate_aplicar_eletrocutar_e_controle(self):
        """TelaCombate deve aplicar o efeito e obter controle 'Eletrocutar'."""
        inimigo = Inimigo(700, 300, 100, "Inimigo1.png", nome="Alvo")
        msg = self.combate.aplicar_efeito_controle(inimigo, "Eletrocutar")
        self.assertEqual(msg, "ELETROCUTOU!")
        self.assertTrue(inimigo.eletrocutado)
        self.assertEqual(inimigo.turnos_eletrocutado, 2)
        self.assertTrue(inimigo.atordoado)

        # Durante o primeiro turno atordoado
        controle = self.combate.obter_efeito_controle(inimigo)
        self.assertEqual(controle, "Eletrocutar")

        # Limpar controle de grupo ao passar o turno
        self.combate.limpar_efeitos_controle(inimigo)
        self.assertFalse(inimigo.atordoado)
        # Permanece eletrocutado para a 2ª rodada
        self.assertTrue(inimigo.eletrocutado)
        self.assertIsNone(self.combate.obter_efeito_controle(inimigo))

    def test_dano_continuo_eletrico_semelhante_a_fogo(self):
        """Eletrocutar deve causar 5% de dano por rodada durante 2 rodadas completas."""
        inimigo = Inimigo(700, 300, 100, "Inimigo1.png", nome="Alvo")
        inimigo.hp = 100
        self.combate.ordem_turnos = [inimigo]

        self.combate.aplicar_efeito_controle(inimigo, "Eletrocutar")
        self.assertEqual(inimigo.turnos_eletrocutado, 2)

        # Fim da Rodada 1
        self.combate.processar_fim_rodada()
        self.assertEqual(inimigo.hp, 95)  # 5% de 100 = 5 de dano
        self.assertEqual(inimigo.turnos_eletrocutado, 1)
        self.assertTrue(inimigo.eletrocutado)

        # Fim da Rodada 2
        self.combate.processar_fim_rodada()
        self.assertEqual(inimigo.hp, 90)  # mais 5 de dano
        self.assertEqual(inimigo.turnos_eletrocutado, 0)
        self.assertFalse(inimigo.eletrocutado)

    def test_ataques_nue_possuem_efeito_eletrocutar(self):
        """Todos os ataques do Nue em minions_personagem.json devem possuir efeito Eletrocutar."""
        p_minions = os.path.join(BASE_DIR, "Dados", "minions_personagem.json")
        with open(p_minions, "r", encoding="utf-8") as f:
            minions = json.load(f)

        self.assertIn("Nue", minions)
        ataques_nue = minions["Nue"]["ataques"]
        self.assertTrue(len(ataques_nue) >= 2)
        for atk in ataques_nue:
            self.assertEqual(atk["efeito"], "Eletrocutar", f"Ataque {atk['nome']} do Nue deveria ter efeito Eletrocutar")
            self.assertGreater(atk["chance_efeito"], 0.0)

    def test_torreta_possui_novo_ataque_eletrocutar(self):
        """Tanto a Torreta inimiga quanto a Torreta Sentinela devem possuir ataque de choque."""
        # 1. Inimigo Torreta
        p_inimigos = os.path.join(BASE_DIR, "Dados", "inimigos.json")
        with open(p_inimigos, "r", encoding="utf-8") as f:
            inis = json.load(f)
        torreta = next((i for i in inis if i["nome"] == "Torreta"), None)
        self.assertIsNotNone(torreta)
        self.assertIn("Descarga Elétrica", torreta["ataques"])

        # 2. Habilidade em habilidades_inimigos.json
        p_habs = os.path.join(BASE_DIR, "Dados", "habilidades_inimigos.json")
        with open(p_habs, "r", encoding="utf-8") as f:
            habs = json.load(f)
        self.assertIn("Descarga Elétrica", habs)
        self.assertEqual(habs["Descarga Elétrica"]["efeito"], "Eletrocutar")

        # 3. Minion Torreta Sentinela
        p_minions = os.path.join(BASE_DIR, "Dados", "minions_personagem.json")
        with open(p_minions, "r", encoding="utf-8") as f:
            minions = json.load(f)
        self.assertIn("Torreta Sentinela", minions)
        atks_sentinela = minions["Torreta Sentinela"]["ataques"]
        nomes_atks = [a["nome"] for a in atks_sentinela]
        self.assertIn("Descarga Elétrica", nomes_atks)
        descarga_sentinela = next(a for a in atks_sentinela if a["nome"] == "Descarga Elétrica")
        self.assertEqual(descarga_sentinela["efeito"], "Eletrocutar")


if __name__ == "__main__":
    unittest.main()
