import json
import os
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent / "An Average City"
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from Sistemas.Recursos import caminho_dados, caminho_imagem


class TestInimigosSprites(unittest.TestCase):
    def test_todos_inimigos_possuem_sprites_existentes(self):
        with open(caminho_dados("inimigos.json"), "r", encoding="utf-8") as arquivo:
            inimigos = json.load(arquivo)

        self.assertGreater(len(inimigos), 0, "inimigos.json está vazio")

        for inimigo in inimigos:
            nome = inimigo["nome"]
            imagem = inimigo.get("arquivo_imagem")
            self.assertTrue(imagem, f"Inimigo '{nome}' não possui arquivo_imagem")
            caminho = caminho_imagem(imagem)
            self.assertTrue(
                os.path.isfile(caminho),
                f"Sprite '{imagem}' do inimigo '{nome}' não encontrada em {caminho}",
            )


if __name__ == "__main__":
    unittest.main()
