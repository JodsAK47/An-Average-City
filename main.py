"""
Ponto de entrada principal padronizado para o jogo 'An Average City'.
Permite executar o jogo diretamente a partir da raiz do projeto:
    python main.py
    py main.py

Ou executar os testes automatizados:
    python main.py --test
    py main.py --test
"""

import os
import sys
from pathlib import Path

# Configuração e padronização do diretório de execução e importação
DIRETORIO_RAIZ_REPO = Path(__file__).resolve().parent
DIRETORIO_JOGO = DIRETORIO_RAIZ_REPO / "An Average City"

if not DIRETORIO_JOGO.exists():
    raise RuntimeError(f"Diretório do jogo não encontrado em: {DIRETORIO_JOGO}")

if str(DIRETORIO_JOGO) not in sys.path:
    sys.path.insert(0, str(DIRETORIO_JOGO))

# Garante que o diretório de trabalho seja a pasta do jogo
try:
    os.chdir(str(DIRETORIO_JOGO))
except Exception:
    pass


def executar_jogo():
    """Inicia o jogo através do loop principal do MotorJogo."""
    from Sistemas.MotorJogo import loop_principal
    loop_principal()


def executar_testes():
    """Executa a suíte de testes unitários automatizados."""
    import unittest
    pasta_testes = str(DIRETORIO_RAIZ_REPO / "tests")
    loader = unittest.TestLoader()
    suite = loader.discover(pasta_testes)
    runner = unittest.TextTestRunner(verbosity=2)
    resultado = runner.run(suite)
    sys.exit(0 if resultado.wasSuccessful() else 1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--test", "-t", "test"):
        executar_testes()
    else:
        executar_jogo()
