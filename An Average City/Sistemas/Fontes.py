import pygame
from Sistemas.Recursos import caminho_fonte

CAMINHO_FONTE = caminho_fonte("Minecraftia-Regular.ttf")

def obter_fonte(tamanho):
    if not pygame.font.get_init():
        pygame.font.init()
    try:
        return pygame.font.Font(CAMINHO_FONTE, tamanho)
    except (pygame.error, FileNotFoundError):
        return pygame.font.SysFont(["consolas", "courier"], tamanho, bold=True)

def obter_fonte_manga(tamanho):
    """Retorna a fonte Manga estilizada para títulos e introduções."""
    if not pygame.font.get_init():
        pygame.font.init()
    try:
        return pygame.font.Font(caminho_fonte("Manga.ttf"), tamanho)
    except (pygame.error, FileNotFoundError):
        return pygame.font.SysFont(["consolas", "arial", "courier"], tamanho, bold=True)

def quebrar_texto(texto, fonte, largura_maxima):
    palavras = texto.split()
    linhas = []
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
                if parte:
                    linha_atual = parte
                else:
                    linha_atual = ""
            else:
                linha_atual = palavra

    if linha_atual:
        linhas.append(linha_atual)

    return linhas
