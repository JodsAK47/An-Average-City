from .TelaMenu import GerenciadorMenu
from .TelaIntro import GerenciadorIntro
from .TelaCombate import GerenciadorJogo
from .TelaGameOver import GerenciadorGameOver
from .TelaClasses import GerenciadorClasses
from .TelaVerso import GerenciadorVerso
from .TelaVitoria import GerenciadorVitoria
from .TelaConquistas import GerenciadorConquistasTela
from .TelaCheats import GerenciadorCheatsTela
from .TelaSewer import GerenciadorSewerTela
from .TelaCenarios import GerenciadorSelecao
from .TelaDescanso import TelaDescanso, GerenciadorPosLuta
from .TelaDialogo import GerenciadorDialogo
from .TelaCutscene import GerenciadorCutscene

from .TelaConfiguracoes import GerenciadorConfiguracoesTela
from .TelaPosDialogo import GerenciadorPosDialogo
from .TelaLoja import GerenciadorLoja, TelaLoja
from .TelaPausa import GerenciadorPausa, TelaPausa

TelaConfiguracoes = GerenciadorConfiguracoesTela

__all__ = [
    "GerenciadorMenu",
    "GerenciadorIntro",
    "GerenciadorJogo",
    "GerenciadorGameOver",
    "GerenciadorClasses",
    "GerenciadorVerso",
    "GerenciadorVitoria",
    "GerenciadorConquistasTela",
    "GerenciadorCheatsTela",
    "GerenciadorSewerTela",
    "GerenciadorSelecao",
    "GerenciadorPosLuta",
    "GerenciadorDialogo",
    "GerenciadorCutscene",
    "TelaDescanso",
    "GerenciadorConfiguracoesTela",
    "TelaConfiguracoes",
    "GerenciadorPosDialogo",
    "GerenciadorLoja",
    "TelaLoja",
    "GerenciadorPausa",
    "TelaPausa",
]
