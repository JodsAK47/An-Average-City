"""
Gerenciador de Áudio e Músicas (OSTs) para o jogo An Average City.
Controla reprodução contínua, seleção de trilhas por Verso e transições
suaves com Fade-In e Fade-Out entre estados e cenários.
"""

import enum
import sys
import time
from pathlib import Path
from typing import Optional, Dict

import pygame

from .Configuracoes import sistema_config
from .Constantes import Verso, obter_musica_combate
from .Recursos import caminho_musica, caminho_sfx


def _log_seguro(msg: str):
    """Imprime mensagens sem risco de falha de codificação em terminais legados (como cp1252)."""
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            print(msg.encode(sys.stdout.encoding or "ascii", errors="replace").decode(sys.stdout.encoding or "ascii"))
        except Exception:
            pass


class EstadoMusica(enum.Enum):
    PARADO = 0
    TOCANDO = 1
    FADING_OUT = 2
    FADING_IN = 3


class GerenciadorMusica:
    """
    Gerenciador com suporte a interpolação suave (Fade-in / Fade-out)
    sem bloqueio de frames no loop principal.
    """

    def __init__(self):
        self.estado: EstadoMusica = EstadoMusica.PARADO
        self.musica_atual: Optional[str] = None
        self.proxima_musica: Optional[str] = None

        self.volume_atual: float = 0.0
        self.volume_inicio_fade_out: float = 0.0
        self.tempo_fade_out: float = 0.0
        self.duracao_fade_out: float = 0.6  # segundos

        self.volume_inicio_fade_in: float = 0.0
        self.tempo_fade_in: float = 0.0
        self.duracao_fade_in: float = 0.8  # segundos
        self.duracao_fade_in_proxima: float = 0.8

        self._ultimo_timestamp: float = time.time()
        self.verso_atual: str = Verso.SOBREVIVENTE.value

    def definir_verso(self, verso: Optional[str]):
        """Atualiza o verso atual para determinar trilhas de combate/chefe."""
        if verso:
            self.verso_atual = Verso.normalizar(verso).value

    def obter_musica_combate(self, eh_chefe: bool = False, verso: Optional[str] = None) -> str:
        """Retorna a OST de combate ou chefe correspondente ao verso."""
        v = verso or self.verso_atual
        return obter_musica_combate(v, eh_chefe=eh_chefe)

    def resolver_nome_musica(self, nome_arquivo: str, verso: Optional[str] = None) -> str:
        """
        Converte referências genéricas antigas ('Combate.mp3', 'Boss.mp3')
        para as trilhas específicas do verso correspondente.
        """
        if not nome_arquivo:
            return ""
        v = verso or self.verso_atual
        if nome_arquivo in ("Combate.mp3", "combate.mp3", "Combate"):
            return obter_musica_combate(v, eh_chefe=False)
        if nome_arquivo in ("Boss.mp3", "boss.mp3", "Boss"):
            return obter_musica_combate(v, eh_chefe=True)
        return nome_arquivo

    def _obter_volume_alvo(self) -> float:
        """Consulta o volume de música efetivo do sistema de configurações."""
        try:
            return sistema_config.obter_volume_musica_efetivo()
        except Exception:
            return 0.5

    def _aplicar_volume_mixer(self, vol: float):
        """Aplica o volume com clamp seguro [0.0, 1.0]."""
        self.volume_atual = max(0.0, min(1.0, float(vol)))
        if pygame.mixer.get_init():
            try:
                pygame.mixer.music.set_volume(self.volume_atual)
            except Exception:
                pass

    def tocar(
        self,
        nome_arquivo: str,
        fade_out_ms: int = 600,
        fade_in_ms: int = 800,
        verso: Optional[str] = None,
        reiniciar_se_mesma: bool = False,
    ):
        """
        Inicia ou transiciona para uma nova música usando fade out e fade in.
        Se a música solicitada já estiver tocando, a reprodução é mantida sem interrupção.
        """
        if verso:
            self.definir_verso(verso)

        nome_resolvido = self.resolver_nome_musica(nome_arquivo, verso=verso)
        if not nome_resolvido:
            return

        # Se for a mesma música que já está em reprodução contínua
        if self.musica_atual == nome_resolvido and not reiniciar_se_mesma:
            if self.estado == EstadoMusica.TOCANDO or self.estado == EstadoMusica.FADING_IN:
                # Mantém fluxo sem reiniciar
                return
            elif self.estado == EstadoMusica.FADING_OUT:
                # Cancelar fade out e retornar suavemente para fade in
                self.proxima_musica = None
                self.estado = EstadoMusica.FADING_IN
                self.duracao_fade_in = max(0.05, fade_in_ms / 1000.0)
                self.tempo_fade_in = 0.0
                self.volume_inicio_fade_in = self.volume_atual
                return

        if not pygame.mixer.get_init():
            return

        em_reproducao = self.estado in (EstadoMusica.TOCANDO, EstadoMusica.FADING_IN, EstadoMusica.FADING_OUT)
        if em_reproducao:
            try:
                if not pygame.mixer.music.get_busy() and self.volume_atual <= 0.01:
                    em_reproducao = False
            except Exception:
                em_reproducao = False

        if em_reproducao and fade_out_ms > 0:
            # Transição: inicia Fade-Out da música atual
            self.proxima_musica = nome_resolvido
            self.duracao_fade_out = max(0.05, fade_out_ms / 1000.0)
            self.tempo_fade_out = self.duracao_fade_out
            self.volume_inicio_fade_out = self.volume_atual
            self.duracao_fade_in_proxima = max(0.05, fade_in_ms / 1000.0)
            self.estado = EstadoMusica.FADING_OUT
        else:
            # Sem transição de saída: carrega imediatamente com Fade-In
            self._iniciar_reproducao(nome_resolvido, fade_in_ms=fade_in_ms)

    def _iniciar_reproducao(self, nome_arquivo: str, fade_in_ms: int = 800):
        """Carrega e começa a tocar a trilha sonora."""
        if not pygame.mixer.get_init():
            return

        caminho_completo = caminho_musica(nome_arquivo)
        if not Path(caminho_completo).exists():
            _log_seguro(f"[Aviso] Arquivo de OST nao encontrado: '{nome_arquivo}'")
            self.estado = EstadoMusica.PARADO
            self.musica_atual = None
            return

        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(caminho_completo)
            self.musica_atual = nome_arquivo
            self.proxima_musica = None

            vol_alvo = self._obter_volume_alvo()
            duracao_fade_in_seg = max(0.05, fade_in_ms / 1000.0)

            if fade_in_ms > 0 and vol_alvo > 0.0:
                self._aplicar_volume_mixer(0.0)
                pygame.mixer.music.play(-1)
                self.estado = EstadoMusica.FADING_IN
                self.duracao_fade_in = duracao_fade_in_seg
                self.tempo_fade_in = 0.0
                self.volume_inicio_fade_in = 0.0
            else:
                self._aplicar_volume_mixer(vol_alvo)
                pygame.mixer.music.play(-1)
                self.estado = EstadoMusica.TOCANDO
        except Exception as e:
            _log_seguro(f"[Aviso] Nao foi possivel reproduzir '{nome_arquivo}': {e}")
            self.estado = EstadoMusica.PARADO
            self.musica_atual = None

    def parar(self, fade_out_ms: int = 600):
        """Para a música atual, opcionalmente com fade out."""
        if not pygame.mixer.get_init() or self.estado == EstadoMusica.PARADO:
            return

        if fade_out_ms <= 0:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            self.estado = EstadoMusica.PARADO
            self.musica_atual = None
            self.proxima_musica = None
            self.volume_atual = 0.0
        else:
            self.proxima_musica = None
            self.duracao_fade_out = max(0.05, fade_out_ms / 1000.0)
            self.tempo_fade_out = self.duracao_fade_out
            self.volume_inicio_fade_out = self.volume_atual
            self.estado = EstadoMusica.FADING_OUT

    def atualizar(self, dt: Optional[float] = None):
        """
        Atualiza o estado de fade in / fade out a cada quadro do jogo.
        Pode ser chamado sem parâmetros; calcula automaticamente o tempo decorrido.
        """
        agora = time.time()
        if dt is None:
            dt = agora - self._ultimo_timestamp
            # Limita dt para evitar saltos bruscos se o jogo congelar ou minimizar
            dt = max(0.0, min(0.2, float(dt)))
        else:
            dt = max(0.0, float(dt))
        self._ultimo_timestamp = agora

        if not pygame.mixer.get_init():
            return

        vol_alvo = self._obter_volume_alvo()

        if self.estado == EstadoMusica.FADING_OUT:
            self.tempo_fade_out -= dt
            if self.tempo_fade_out <= 0.0:
                self.tempo_fade_out = 0.0
                self._aplicar_volume_mixer(0.0)
                try:
                    pygame.mixer.music.stop()
                except Exception:
                    pass

                proxima = self.proxima_musica
                self.proxima_musica = None

                if proxima:
                    duracao_fade_in = int(self.duracao_fade_in_proxima * 1000.0)
                    self._iniciar_reproducao(proxima, fade_in_ms=duracao_fade_in)
                else:
                    self.estado = EstadoMusica.PARADO
                    self.musica_atual = None
            else:
                progresso = 1.0 - (self.tempo_fade_out / self.duracao_fade_out)
                vol = max(0.0, self.volume_inicio_fade_out * (1.0 - progresso))
                self._aplicar_volume_mixer(vol)

        elif self.estado == EstadoMusica.FADING_IN:
            self.tempo_fade_in += dt
            if self.tempo_fade_in >= self.duracao_fade_in:
                self.tempo_fade_in = self.duracao_fade_in
                self._aplicar_volume_mixer(vol_alvo)
                self.estado = EstadoMusica.TOCANDO
            else:
                progresso = self.tempo_fade_in / self.duracao_fade_in
                vol = self.volume_inicio_fade_in + (vol_alvo - self.volume_inicio_fade_in) * progresso
                self._aplicar_volume_mixer(vol)

        elif self.estado == EstadoMusica.TOCANDO:
            # Sincroniza com eventuais ajustes de volume feitos pelo jogador nas configurações
            if abs(self.volume_atual - vol_alvo) > 0.02:
                self._aplicar_volume_mixer(vol_alvo)


# Instância global do gerenciador de música
gerenciador_musica = GerenciadorMusica()


class GerenciadorSFX:
    """
    Gerenciador global para carregamento e reprodução de efeitos sonoros (SFX).
    Realiza cache de objetos pygame.mixer.Sound e aplica o volume de SFX
    definido nas configurações do sistema.
    """

    def __init__(self):
        self._sons: Dict[str, pygame.mixer.Sound] = {}

    def obter_som(self, nome_arquivo: str) -> Optional[pygame.mixer.Sound]:
        """Carrega e armazena em cache o efeito sonoro."""
        if not pygame.mixer.get_init():
            return None
        nome_chave = Path(nome_arquivo).name.lower()
        if nome_chave in self._sons:
            return self._sons[nome_chave]

        caminho = caminho_sfx(nome_arquivo)
        if Path(caminho).exists():
            try:
                snd = pygame.mixer.Sound(caminho)
                self._sons[nome_chave] = snd
                return snd
            except Exception as e:
                _log_seguro(f"[Aviso] Nao foi possivel carregar SFX '{nome_arquivo}': {e}")
                return None
        return None

    def tocar(self, nome_arquivo: str, volume_relativo: float = 1.0) -> Optional[pygame.mixer.Channel]:
        """
        Reproduz um efeito sonoro com o volume configurado para SFX.
        Retorna o canal de reprodução ou None se desativado/mudo.
        """
        if not pygame.mixer.get_init():
            return None
        try:
            if sistema_config.esta_mutado():
                return None
            vol_base = sistema_config.obter_volume_sfx_efetivo()
            vol = max(0.0, min(1.0, float(vol_base * volume_relativo)))
            if vol <= 0.0:
                return None
        except Exception:
            return None

        snd = self.obter_som(nome_arquivo)
        if snd is not None:
            try:
                snd.set_volume(vol)
                return snd.play()
            except Exception as e:
                _log_seguro(f"[Aviso] Erro ao reproduzir SFX '{nome_arquivo}': {e}")
                return None
        return None

    def limpar_cache(self):
        """Limpa o cache de sons carregados."""
        self._sons.clear()


# Instância global do gerenciador de efeitos sonoros (SFX)
gerenciador_sfx = GerenciadorSFX()
tocar_sfx = gerenciador_sfx.tocar
