import json
import os
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent / "An Average City"
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.init()
pygame.display.set_mode((1024, 768))

from Sistemas.Recursos import caminho_imagem, caminho_dados
from Entidades.Minion import BANCO_MINIONS, Minion, criar_minion


class TestMinionsSprites(unittest.TestCase):
    def test_todos_minions_possuem_sprites_existentes(self):
        """Verifica se todos os minions do minions.json possuem arquivo_imagem válido e existente no disco."""
        caminho_minions = Path(caminho_dados("minions.json"))
        self.assertTrue(caminho_minions.exists(), "minions.json não encontrado")

        with open(caminho_minions, "r", encoding="utf-8") as f:
            minions = json.load(f)

        self.assertGreater(len(minions), 0, "minions.json está vazio")

        for nome, dados in minions.items():
            img = dados.get("arquivo_imagem")
            self.assertTrue(bool(img), f"Minion '{nome}' não possui arquivo_imagem definido")
            caminho_resolvido = caminho_imagem(img)
            self.assertTrue(
                os.path.exists(caminho_resolvido),
                f"Sprite '{img}' do minion '{nome}' não encontrada em {caminho_resolvido}"
            )

    def test_sprites_especificas_dos_minions(self):
        """Verifica a atribuição correta das sprites de cada minion, especialmente as novas."""
        caminho_minions = Path(caminho_dados("minions.json"))
        with open(caminho_minions, "r", encoding="utf-8") as f:
            minions = json.load(f)

        # Cão Divino deve usar Cachorro.png
        self.assertEqual(minions["Cão Divino"]["arquivo_imagem"], "Cachorro.png")
        self.assertFalse(minions["Cão Divino"]["inverter_horizontal"])

        # Nue deve usar Nue.png
        self.assertEqual(minions["Nue"]["arquivo_imagem"], "Nue.png")
        self.assertFalse(minions["Nue"]["inverter_horizontal"])

        # Mahoraga deve usar Mahoraga.png
        self.assertEqual(minions["Mahoraga"]["arquivo_imagem"], "Mahoraga.png")

        # Pequeno Santuário deve usar Santuario.png
        self.assertIn(minions["Pequeno Santuário"]["arquivo_imagem"].lower(), ["santuario.png"])

        # Sobrevivente: Abelha e Pássaro Olhudo
        self.assertEqual(minions["Abelha Soldado"]["arquivo_imagem"], "Abelha.png")
        self.assertEqual(minions["Pássaro Olhudo"]["arquivo_imagem"], "Passaro_Olhudo.png")

        # Agente: Torreta Sentinela e Drone Caçador
        self.assertEqual(minions["Torreta Sentinela"]["arquivo_imagem"], "Torreta.png")
        self.assertEqual(minions["Drone Caçador"]["arquivo_imagem"], "Drone.png")
        self.assertTrue(minions["Drone Caçador"]["inverter_horizontal"])

    def test_instanciacao_criar_minion_carrega_imagem(self):
        """Verifica se criar_minion instancia cada minion carregando a imagem com dimensões válidas."""
        for nome_minion in BANCO_MINIONS:
            minion = criar_minion(nome_minion)
            self.assertIsNotNone(minion.imagem, f"Minion '{nome_minion}' não possui surface de imagem")
            w, h = minion.imagem.get_size()
            self.assertGreater(w, 0, f"Minion '{nome_minion}' possui largura inválida")
            self.assertEqual(h, 82, f"Minion '{nome_minion}' possui altura diferente de 82px")

    def test_respeito_ao_inverter_horizontal(self):
        """Verifica se inverter_horizontal é respeitado na criação do minion."""
        m_normal = Minion(nome="TesteNormal", nome_imagem="Cachorro.png", inverter_horizontal=False)
        m_invertido = Minion(nome="TesteInvertido", nome_imagem="Cachorro.png", inverter_horizontal=True)

        w, h = m_normal.imagem.get_size()
        # Ao inverter horizontalmente, o pixel da esquerda vai para a direita
        pixels_normal = [m_normal.imagem.get_at((x, h // 2)) for x in range(w)]
        pixels_invertido = [m_invertido.imagem.get_at((x, h // 2)) for x in range(w)]
        self.assertEqual(pixels_normal, list(reversed(pixels_invertido)))

    def test_sprite_cartao_do_clube_na_pasta_de_itens(self):
        """Verifica se o jogo localiza o sprite do cartão do clube (MemberCard.png) na pasta de itens/inventário."""
        from Sistemas.Recursos import caminho_item
        from Sistemas.Inventario import obter_arquivo_imagem_item

        caminho_card = caminho_item("MemberCard.png")
        self.assertTrue(os.path.exists(caminho_card), f"MemberCard.png não encontrado em {caminho_card}")
        self.assertIn("inventario", caminho_card.lower().replace("\\", "/"))

        # Verifica mapeamento no inventário
        self.assertEqual(obter_arquivo_imagem_item("cartão do clube"), "MemberCard.png")
        self.assertEqual(obter_arquivo_imagem_item("cartao do clube"), "MemberCard.png")
        self.assertEqual(obter_arquivo_imagem_item("member card"), "MemberCard.png")


if __name__ == "__main__":
    unittest.main()
