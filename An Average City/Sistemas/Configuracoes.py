import json
import os
from typing import Tuple, List, Optional
import pygame
from Sistemas.Constantes import NOME_JOGO
from Sistemas.Recursos import caminho_saves, caminho_dados

ARQUIVO_CONFIG = caminho_saves("config.json")
ARQUIVO_LEGADO_CONFIG = caminho_dados("config.json")

RESOLUCOES_DISPONIVEIS: List[Tuple[int, int, str]] = [
    (800, 600, "4:3 SVGA"),
    (1000, 800, "5:4 Padrão"),
    (1024, 768, "4:3 XGA"),
    (1280, 720, "16:9 HD"),
    (1280, 800, "16:10 WXGA"),
    (1366, 768, "16:9 Laptop"),
    (1600, 900, "16:9 HD+"),
    (1920, 1080, "16:9 FHD"),
]

PADRAO_LARGURA = 1000
PADRAO_ALTURA = 800
PADRAO_TELA_CHEIA = False
PADRAO_VOLUME_GERAL = 1.0
PADRAO_VOLUME_MUSICA = 0.5
PADRAO_VOLUME_SFX = 0.7
PADRAO_MUTADO = False

class GerenciadorConfiguracoes:

    def __init__(self):
        self.resolucoes = RESOLUCOES_DISPONIVEIS
        self.largura = PADRAO_LARGURA
        self.altura = PADRAO_ALTURA
        self.tela_cheia = PADRAO_TELA_CHEIA
        self.volume_geral = PADRAO_VOLUME_GERAL
        self.volume_musica = PADRAO_VOLUME_MUSICA
        self.volume_sfx = PADRAO_VOLUME_SFX
        self.mutado = PADRAO_MUTADO

        self.carregar()

    def carregar(self):
        arquivo_para_ler = None
        if os.path.exists(ARQUIVO_CONFIG):
            arquivo_para_ler = ARQUIVO_CONFIG
        elif os.path.exists(ARQUIVO_LEGADO_CONFIG):
            arquivo_para_ler = ARQUIVO_LEGADO_CONFIG

        if not arquivo_para_ler:
            return

        try:
            with open(arquivo_para_ler, "r", encoding="utf-8") as f:
                dados = json.load(f)

            largura = int(dados.get("largura", PADRAO_LARGURA))
            altura = int(dados.get("altura", PADRAO_ALTURA))
            if any(r[0] == largura and r[1] == altura for r in self.resolucoes):
                self.largura = largura
                self.altura = altura
            else:
                self.largura = PADRAO_LARGURA
                self.altura = PADRAO_ALTURA

            self.tela_cheia = bool(dados.get("tela_cheia", PADRAO_TELA_CHEIA))

            self.volume_geral = max(0.0, min(1.0, float(dados.get("volume_geral", PADRAO_VOLUME_GERAL))))
            self.volume_musica = max(0.0, min(1.0, float(dados.get("volume_musica", PADRAO_VOLUME_MUSICA))))
            self.volume_sfx = max(0.0, min(1.0, float(dados.get("volume_sfx", PADRAO_VOLUME_SFX))))
            self.mutado = bool(dados.get("mutado", PADRAO_MUTADO))

        except Exception as e:
            print(f"⚠️ Erro ao carregar config.json: {e}")

    def salvar(self):
        try:
            diretorio_saves = os.path.dirname(ARQUIVO_CONFIG)
            if not os.path.exists(diretorio_saves):
                os.makedirs(diretorio_saves, exist_ok=True)

            dados = {
                "largura": int(self.largura),
                "altura": int(self.altura),
                "tela_cheia": bool(self.tela_cheia),
                "volume_geral": round(float(self.volume_geral), 2),
                "volume_musica": round(float(self.volume_musica), 2),
                "volume_sfx": round(float(self.volume_sfx), 2),
                "mutado": bool(self.mutado),
            }

            with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"⚠️ Erro ao salvar config.json: {e}")
            return False

    def restaurar_padroes(self):
        self.largura = PADRAO_LARGURA
        self.altura = PADRAO_ALTURA
        self.tela_cheia = PADRAO_TELA_CHEIA
        self.volume_geral = PADRAO_VOLUME_GERAL
        self.volume_musica = PADRAO_VOLUME_MUSICA
        self.volume_sfx = PADRAO_VOLUME_SFX
        self.mutado = PADRAO_MUTADO
        self.salvar()
        self.aplicar_audio()

    def obter_resolucao(self) -> Tuple[int, int]:
        return (self.largura, self.altura)

    def obter_indice_resolucao(self) -> int:
        for i, (l, a, _) in enumerate(self.resolucoes):
            if l == self.largura and a == self.altura:
                return i
        return 1

    def definir_resolucao(self, largura: int, altura: int):
        self.largura = int(largura)
        self.altura = int(altura)

    def proxima_resolucao(self) -> Tuple[int, int]:
        idx = (self.obter_indice_resolucao() + 1) % len(self.resolucoes)
        self.largura = self.resolucoes[idx][0]
        self.altura = self.resolucoes[idx][1]
        return self.obter_resolucao()

    def resolucao_anterior(self) -> Tuple[int, int]:
        idx = (self.obter_indice_resolucao() - 1) % len(self.resolucoes)
        self.largura = self.resolucoes[idx][0]
        self.altura = self.resolucoes[idx][1]
        return self.obter_resolucao()

    def obter_texto_resolucao_atual(self) -> str:
        idx = self.obter_indice_resolucao()
        l, a, rotulo = self.resolucoes[idx]
        return f"{l} x {a}  [{rotulo}]"

    def obter_tela_cheia(self) -> bool:
        return self.tela_cheia

    def definir_tela_cheia(self, ativo: bool):
        self.tela_cheia = bool(ativo)

    def alternar_tela_cheia(self) -> bool:
        self.tela_cheia = not self.tela_cheia
        return self.tela_cheia

    def aplicar_video(self) -> Optional[pygame.Surface]:
        if not pygame.display.get_init():
            return None

        flags = pygame.FULLSCREEN if self.tela_cheia else pygame.RESIZABLE
        tamanho = (0, 0) if self.tela_cheia else (self.largura, self.altura)
        nova_superficie = pygame.display.set_mode(tamanho, flags)
        pygame.display.set_caption(NOME_JOGO)
        return nova_superficie

    def obter_volume_geral(self) -> float:
        return self.volume_geral

    def definir_volume_geral(self, valor: float):
        self.volume_geral = max(0.0, min(1.0, round(float(valor), 2)))
        self.aplicar_audio()

    def alterar_volume_geral(self, delta: float):
        self.definir_volume_geral(self.volume_geral + delta)

    def obter_volume_musica(self) -> float:
        return self.volume_musica

    def definir_volume_musica(self, valor: float):
        self.volume_musica = max(0.0, min(1.0, round(float(valor), 2)))
        self.aplicar_audio()

    def alterar_volume_musica(self, delta: float):
        self.definir_volume_musica(self.volume_musica + delta)

    def obter_volume_sfx(self) -> float:
        return self.volume_sfx

    def definir_volume_sfx(self, valor: float):
        self.volume_sfx = max(0.0, min(1.0, round(float(valor), 2)))

    def alterar_volume_sfx(self, delta: float):
        self.definir_volume_sfx(self.volume_sfx + delta)

    def esta_mutado(self) -> bool:
        return self.mutado

    def definir_mudo(self, valor: bool):
        self.mutado = bool(valor)
        self.aplicar_audio()

    def alternar_mudo(self) -> bool:
        self.mutado = not self.mutado
        self.aplicar_audio()
        return self.mutado

    def obter_volume_musica_efetivo(self) -> float:
        if self.mutado:
            return 0.0
        return max(0.0, min(1.0, round(self.volume_geral * self.volume_musica, 2)))

    def obter_volume_sfx_efetivo(self) -> float:
        if self.mutado:
            return 0.0
        return max(0.0, min(1.0, round(self.volume_geral * self.volume_sfx, 2)))

    def aplicar_audio(self):
        if pygame.mixer.get_init():
            try:
                pygame.mixer.music.set_volume(self.obter_volume_musica_efetivo())
            except Exception as e:
                try:
                    print(f"[Aviso] Erro ao aplicar volume da musica: {e}")
                except Exception:
                    pass

sistema_config = GerenciadorConfiguracoes()
