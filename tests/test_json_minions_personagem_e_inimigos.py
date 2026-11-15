import os
import sys
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "An Average City"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
if not pygame.get_init():
    pygame.init()
pygame.display.set_mode((100, 100))

from Sistemas.Recursos import caminho_dados, caminho_imagem
from Entidades.Minion import (
    BANCO_HABILIDADES_MINIONS,
    BANCO_MINIONS,
    BANCO_MINIONS_PERSONAGEM,
    BANCO_MINIONS_INIMIGOS,
    carregar_minions_personagem,
    criar_minion,
    Minion
)
from Entidades.Personagem import Personagem
from Entidades.Inimigo import Inimigo


class TestJsonMinionsPersonagemEInimigos(unittest.TestCase):
    def test_arquivo_minions_personagem_valido(self):
        """Verifica se minions_personagem.json existe e contém todos os minions do jogador com dados válidos."""
        p_path = caminho_dados("minions_personagem.json")
        self.assertTrue(os.path.exists(p_path), f"Arquivo não encontrado: {p_path}")

        with open(p_path, "r", encoding="utf-8") as f:
            minions_p = json.load(f)
        self.assertEqual(carregar_minions_personagem(), minions_p)
        self.assertEqual(BANCO_MINIONS_PERSONAGEM, minions_p)

        esperados = [
            "Abelha Soldado",
            "Pássaro Olhudo",
            "Torreta Sentinela",
            "Drone Caçador",
            "Cão Divino",
            "Nue",
            "Mahoraga",
            "Drone Netrunner",
            "Unidade Militech"
        ]
        for nome in esperados:
            self.assertIn(nome, minions_p, f"Minion de personagem '{nome}' ausente em minions_personagem.json")
            dados = minions_p[nome]
            self.assertEqual(dados.get("nome"), nome)
            for campo in ("max_hp", "max_mp", "atributos"):
                self.assertIn(campo, dados)
            self.assertGreater(dados["max_hp"], 0)
            self.assertGreaterEqual(dados["max_mp"], 0)
            self.assertEqual(set(dados["atributos"]), {"For", "Agi", "Con", "Sab", "Int", "Sor"})
            self.assertIn("ataques", dados)
            self.assertGreater(len(dados["ataques"]), 0)

            # Verifica existência do sprite
            img = dados.get("arquivo_imagem")
            self.assertTrue(bool(img))
            caminho_res = caminho_imagem(img)
            self.assertTrue(os.path.exists(caminho_res), f"Sprite '{img}' não encontrado em {caminho_res}")

    def test_arquivo_minions_inimigos_valido(self):
        """Verifica se minions_inimigos.json existe e contém minions de inimigos com dados válidos."""
        i_path = caminho_dados("minions_inimigos.json")
        self.assertTrue(os.path.exists(i_path), f"Arquivo não encontrado: {i_path}")

        with open(i_path, "r", encoding="utf-8") as f:
            minions_i = json.load(f)

        esperados = [
            "Pequeno Santuário",
            "Fera do Breu",
            "Mãos das Sombras",
            "Tentáculos das Trevas",
            "Enxame Noturno",
            "Torreta Inimiga",
            "Pássaro Sombrio"
        ]
        for nome in esperados:
            self.assertIn(nome, minions_i, f"Minion inimigo '{nome}' ausente em minions_inimigos.json")
            dados = minions_i[nome]
            self.assertEqual(dados.get("nome"), nome)
            self.assertIn("max_hp", dados)
            self.assertIn("max_mp", dados)
            self.assertIn("atributos", dados)
            self.assertIn("ataques", dados)
            self.assertGreater(len(dados["ataques"]), 0)

            # Verifica existência do sprite
            img = dados.get("arquivo_imagem")
            self.assertTrue(bool(img))
            caminho_res = caminho_imagem(img)
            self.assertTrue(os.path.exists(caminho_res), f"Sprite '{img}' não encontrado em {caminho_res}")

    def test_bancos_carregados_no_minion(self):
        """Verifica se Minion.py carrega e expõe BANCO_MINIONS_PERSONAGEM e BANCO_MINIONS_INIMIGOS separadamente."""
        self.assertGreaterEqual(len(BANCO_MINIONS_PERSONAGEM), 7)
        self.assertGreaterEqual(len(BANCO_MINIONS_INIMIGOS), 7)

        # Cão Divino é do jogador
        self.assertIn("Cão Divino", BANCO_MINIONS_PERSONAGEM)
        # Pequeno Santuário e Fera do Breu são de inimigos
        self.assertIn("Pequeno Santuário", BANCO_MINIONS_INIMIGOS)
        self.assertIn("Fera do Breu", BANCO_MINIONS_INIMIGOS)

        # BANCO_MINIONS geral unifica ambos
        self.assertIn("Cão Divino", BANCO_MINIONS)
        self.assertIn("Pequeno Santuário", BANCO_MINIONS)
        self.assertIn("Fera do Breu", BANCO_MINIONS)

    def test_ataques_referenciam_catalogo_de_habilidades(self):
        """Os dois catálogos guardam nomes de habilidades que existem no arquivo separado."""
        with open(caminho_dados("habilidades_minions.json"), "r", encoding="utf-8") as f:
            habilidades = json.load(f)
        self.assertTrue(habilidades)
        self.assertEqual(BANCO_HABILIDADES_MINIONS, habilidades)

        for arquivo in ("minions_personagem.json", "minions_inimigos.json"):
            with open(caminho_dados(arquivo), "r", encoding="utf-8") as f:
                minions = json.load(f)
            for nome_minion, dados in minions.items():
                with self.subTest(arquivo=arquivo, minion=nome_minion):
                    self.assertTrue(dados["ataques"])
                    for nome_ataque in dados["ataques"]:
                        self.assertIsInstance(nome_ataque, str)
                        self.assertIn(nome_ataque, habilidades)
                        self.assertEqual(habilidades[nome_ataque]["nome"], nome_ataque)

    def test_criar_minions_resolve_habilidades_do_catalogo(self):
        """Invocações de ambos os lados recebem os valores e efeitos configurados para cada ataque."""
        campos = (
            "nome", "tipo", "dano", "custo_mp", "precisao", "descricao",
            "efeito", "chance_efeito", "em_area",
        )
        for banco, jogador in ((BANCO_MINIONS_PERSONAGEM, True), (BANCO_MINIONS_INIMIGOS, False)):
            dono = SimpleNamespace(is_player=jogador)
            for nome_minion, dados in banco.items():
                with self.subTest(minion=nome_minion, jogador=jogador):
                    minion = criar_minion(nome_minion, dono=dono)
                    self.assertEqual(minion.ataques, dados["ataques"])
                    self.assertEqual(set(minion.habilidades), set(dados["ataques"]))
                    for nome_ataque in dados["ataques"]:
                        habilidade = minion.obter_habilidade(nome_ataque)
                        esperado = BANCO_HABILIDADES_MINIONS[nome_ataque]
                        for campo in campos:
                            self.assertEqual(getattr(habilidade, campo), esperado[campo], campo)
                        self.assertEqual(habilidade.verso, dados["verso"])

                    minion.mp = 0
                    habilidade = minion.obter_habilidade(minion.escolher_ataque())
                    self.assertEqual(habilidade.custo_mp, 0)

    def test_habilidades_nao_sao_compartilhadas_entre_minions(self):
        primeiro = criar_minion("Nue")
        segundo = criar_minion("Nue")
        nome_ataque = primeiro.ataques[0]
        habilidade = primeiro.obter_habilidade(nome_ataque)
        outra_habilidade = segundo.obter_habilidade(nome_ataque)

        self.assertIsNot(habilidade, outra_habilidade)
        dano_original = BANCO_HABILIDADES_MINIONS[nome_ataque]["dano"]
        habilidade.dano += 10
        self.assertEqual(outra_habilidade.dano, dano_original)
        self.assertEqual(BANCO_HABILIDADES_MINIONS[nome_ataque]["dano"], dano_original)

    def test_ataque_usa_valores_exclusivamente_do_catalogo(self):
        dados = dict(BANCO_HABILIDADES_MINIONS["Ferrão Veloz"])
        dados.update(dano=23, custo_mp=4, efeito="Veneno", chance_efeito=1.0)
        with patch.dict(BANCO_HABILIDADES_MINIONS, {"Ferrão Veloz": dados}):
            minion = criar_minion("Abelha Soldado")
        habilidade = minion.obter_habilidade("Ferrão Veloz")
        self.assertEqual(habilidade.dano, 23)
        self.assertEqual(habilidade.custo_mp, 4)
        self.assertEqual(habilidade.efeito, "Veneno")
        self.assertEqual(habilidade.chance_efeito, 1.0)

    def test_atributos_embutidos_preservam_estatisticas_dos_minions(self):
        with open(caminho_dados("minions_personagem.json"), "r", encoding="utf-8") as f:
            minions = json.load(f)
        dono = SimpleNamespace(is_player=True, atributos={"Sab": 1})
        for nome, dados in minions.items():
            with self.subTest(minion=nome):
                minion = criar_minion(nome, dono=dono)
                self.assertEqual(minion.max_hp, dados["max_hp"])
                self.assertEqual(minion.hp, dados["max_hp"])
                self.assertEqual(minion.max_mp, dados["max_mp"])
                self.assertEqual(minion.mp, dados["max_mp"])
                self.assertEqual(minion.atributos, dados["atributos"])

    def test_fortalecer_minion_nao_altera_atributos_do_catalogo_ou_de_outro_minion(self):
        primeiro = criar_minion("Nue")
        segundo = criar_minion("Nue")
        atributos_originais = dict(BANCO_MINIONS_PERSONAGEM["Nue"]["atributos"])
        primeiro.curar_e_fortalecer()

        self.assertGreater(primeiro.atributos["Sab"], atributos_originais["Sab"])
        self.assertEqual(segundo.atributos, atributos_originais)
        self.assertEqual(BANCO_MINIONS_PERSONAGEM["Nue"]["atributos"], atributos_originais)
        self.assertEqual(BANCO_MINIONS["Nue"]["atributos"], atributos_originais)

    def test_ataques_nao_aceitam_valores_embutidos(self):
        with self.assertRaisesRegex(TypeError, "somente nomes"):
            Minion(ataques_dados=[{"nome": "Ferrão Veloz", "dano": 999}])
        with self.assertRaisesRegex(ValueError, "habilidades_minions.json"):
            Minion(ataques_dados=["Ataque inexistente"])

    def test_ataque_padrao_tambem_usa_catalogo(self):
        dados = dict(BANCO_HABILIDADES_MINIONS["Investida Espiritual"])
        dados["dano"] = 19
        with patch.dict(BANCO_HABILIDADES_MINIONS, {"Investida Espiritual": dados}):
            minion = Minion()
        self.assertEqual(minion.ataques, ["Investida Espiritual"])
        self.assertEqual(minion.obter_habilidade("Investida Espiritual").dano, 19)

    def test_santuario_usa_habilidade_do_catalogo_de_minions(self):
        from Entidades.Santuario import Santuario

        dados = dict(BANCO_HABILIDADES_MINIONS["Cortes Malevolentes"])
        dados.update(dano=23, efeito="Queimar", chance_efeito=0.75)
        with patch.dict(BANCO_HABILIDADES_MINIONS, {"Cortes Malevolentes": dados}):
            santuario = Santuario()
            habilidade = santuario.obter_habilidade("Cortes Malevolentes")

        self.assertEqual(habilidade.nome, "Cortes Malevolentes")
        self.assertEqual(habilidade.dano, 23)
        self.assertEqual(habilidade.efeito, "Queimar")
        self.assertEqual(habilidade.chance_efeito, 0.75)
        self.assertTrue(habilidade.em_area)
        self.assertEqual(habilidade.verso, santuario.verso)

    def test_criar_minion_com_dono_jogador_e_inimigo(self):
        """Verifica se criar_minion associa corretamente o lado do dono ao minion."""
        from Entidades.Personagem import personagem
        inimigo = Inimigo(700, 300, 100, "Inimigo1.png", nome="Boss")

        minion_p = criar_minion("Cão Divino", dono=personagem)
        self.assertEqual(minion_p.lado, "jogador")
        self.assertTrue(minion_p.eh_do_jogador)
        self.assertFalse(minion_p.eh_do_inimigo)

        minion_i = criar_minion("Fera do Breu", dono=inimigo)
        self.assertEqual(minion_i.lado, "inimigo")
        self.assertFalse(minion_i.eh_do_jogador)
        self.assertTrue(minion_i.eh_do_inimigo)


if __name__ == "__main__":
    unittest.main()
