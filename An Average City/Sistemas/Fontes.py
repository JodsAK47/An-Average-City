import pygame
from Sistemas.Recursos import caminho_fonte

CAMINHO_FONTE = caminho_fonte("Minecraftia-Regular.ttf")
_CACHE_FONTES = {}


def obter_fonte(tamanho):
    chave = ("minecraftia", int(tamanho))
    if chave in _CACHE_FONTES:
        return _CACHE_FONTES[chave]
    if not pygame.font.get_init():
        pygame.font.init()
    try:
        fonte = pygame.font.Font(CAMINHO_FONTE, int(tamanho))
    except (pygame.error, FileNotFoundError):
        fonte = pygame.font.SysFont(["consolas", "courier"], int(tamanho), bold=True)
    _CACHE_FONTES[chave] = fonte
    return fonte


def obter_fonte_manga(tamanho):
    """Retorna a fonte Manga estilizada para títulos e introduções."""
    chave = ("manga", int(tamanho))
    if chave in _CACHE_FONTES:
        return _CACHE_FONTES[chave]
    if not pygame.font.get_init():
        pygame.font.init()
    try:
        fonte = pygame.font.Font(caminho_fonte("Manga.ttf"), int(tamanho))
    except (pygame.error, FileNotFoundError):
        fonte = pygame.font.SysFont(["consolas", "arial", "courier"], int(tamanho), bold=True)
    _CACHE_FONTES[chave] = fonte
    return fonte


def quebrar_texto(texto, fonte, largura_maxima):
    linhas = []
    for paragrafo in str(texto or "").split("\n"):
        palavras = paragrafo.split()
        if not palavras:
            linhas.append("")
            continue
        linha_atual = ""

        for palavra in palavras:
            candidata = (linha_atual + " " + palavra).strip() if linha_atual else palavra
            largura, _ = fonte.size(candidata)
            if largura <= largura_maxima:
                linha_atual = candidata
            else:
                if linha_atual:
                    linhas.append(linha_atual)
                if fonte.size(palavra)[0] > largura_maxima:
                    parte = ""
                    for ch in palavra:
                        if fonte.size(parte + ch)[0] <= largura_maxima:
                            parte += ch
                        else:
                            if parte:
                                linhas.append(parte)
                            parte = ch
                    linha_atual = parte
                else:
                    linha_atual = palavra

        if linha_atual:
            linhas.append(linha_atual)

    return linhas
