import json
import os
import pygame
from Sistemas.Fontes import obter_fonte
from Sistemas.Recursos import caminho_imagem, caminho_botao, caminho_dados, caminho_conquista

ARQUIVO_CONQUISTAS = caminho_dados("conquistas.json")

def converter_para_cinza(surface):
    try:
        return pygame.transform.grayscale(surface)
    except (AttributeError, pygame.error):
        copia = surface.copy()
        w, h = copia.get_size()
        for x in range(w):
            for y in range(h):
                r, g, b, a = copia.get_at((x, y))
                if a > 0:
                    cinza = int(0.299 * r + 0.587 * g + 0.114 * b)
                    copia.set_at((x, y), (cinza, cinza, cinza, a))
        return copia

class Conquista:
    def __init__(self, id_conquista, nome, como_liberar, icone_arquivo, desbloqueada=False, oculta=False):
        self.id = id_conquista
        self.nome = nome
        self.como_liberar = como_liberar
        self.icone_arquivo = icone_arquivo
        self.desbloqueada = desbloqueada
        self.oculta = bool(oculta)
        self._superficie_colorida = None
        self._superficie_cinza = None

    def carregar_icones(self):
        if self._superficie_colorida is not None:
            return

        surf = None
        for tentativa in (
            caminho_conquista(self.icone_arquivo),
            caminho_imagem(self.icone_arquivo),
            caminho_botao(self.icone_arquivo),
        ):
            if os.path.exists(tentativa):
                try:
                    surf = pygame.image.load(tentativa).convert_alpha()
                except pygame.error:
                    surf = pygame.image.load(tentativa)
                break

        if surf is None:
            surf = pygame.Surface((64, 64), pygame.SRCALPHA)
            surf.fill((100, 100, 120))
            pygame.draw.rect(surf, (255, 215, 0), (2, 2, 60, 60), width=3)

        self._superficie_colorida = surf
        self._superficie_cinza = converter_para_cinza(surf)

    def obter_icone(self, desbloqueada=None, tamanho=(48, 48)):
        self.carregar_icones()
        esta_ativa = self.desbloqueada if desbloqueada is None else desbloqueada
        base = self._superficie_colorida if esta_ativa else self._superficie_cinza
        return pygame.transform.smoothscale(base, tamanho)

class SistemaConquistas:
    def __init__(self):
        self.conquistas = []
        self.mapa_conquistas = {}
        self.notificacoes = []
        self.fonte_notificacao = None
        self.fonte_sub = None
        self.carregar()

    def carregar(self):
        self.conquistas.clear()
        self.mapa_conquistas.clear()
        self.notificacoes.clear()
        if not os.path.exists(ARQUIVO_CONQUISTAS):
            return

        try:
            from Sistemas.SaveSystem import save_global
            with open(ARQUIVO_CONQUISTAS, "r", encoding="utf-8") as f:
                dados = json.load(f)
                for item in dados:
                    id_c = item["id"]
                    ja_desbloqueada = save_global.esta_desbloqueada(id_c)
                    c = Conquista(
                        id_conquista=id_c,
                        nome=item["nome"],
                        como_liberar=item["como_liberar"],
                        icone_arquivo=item.get("icone", "SELECT.png"),
                        desbloqueada=ja_desbloqueada,
                        oculta=item.get("oculta", False),
                    )
                    self.conquistas.append(c)
                    self.mapa_conquistas[c.id] = c
            self.verificar_conquistas_especiais()
        except Exception as e:
            print(f"[Aviso] Erro ao carregar conquistas: {e}")

    def salvar(self):
        try:
            from Sistemas.SaveSystem import save_global
            for c in self.conquistas:
                if c.desbloqueada:
                    save_global.desbloquear_conquista(c.id)
            self.verificar_conquistas_especiais(salvar=False)
            save_global.salvar()
        except Exception as e:
            print(f"[Aviso] Erro ao salvar conquistas: {e}")

    def esta_desbloqueada(self, id_conquista):
        c = self.mapa_conquistas.get(id_conquista)
        return bool(c and c.desbloqueada)

    def desbloquear(self, id_conquista):
        if id_conquista == "easter_egg" and not self._requisitos_easter_egg():
            return False
        if id_conquista == "platina" and not self._requisitos_platina():
            return False
        desbloqueada = self._desbloquear(id_conquista)
        especiais = self.verificar_conquistas_especiais(salvar=False)
        if desbloqueada or especiais:
            from Sistemas.SaveSystem import save_global
            save_global.salvar()
        return desbloqueada

    def _desbloquear(self, id_conquista):
        c = self.mapa_conquistas.get(id_conquista)
        if c and not c.desbloqueada:
            c.desbloqueada = True
            from Sistemas.SaveSystem import save_global
            save_global.desbloquear_conquista(id_conquista)
            self.notificacoes.append({
                "nome": c.nome,
                "icone": c.obter_icone(desbloqueada=True, tamanho=(40, 40)),
                "tempo": 220,
                "y_anim": -70,
                **({"progresso": 100} if id_conquista == "easter_egg" else {}),
            })
            return True
        return False

    def _etapas_easter_egg(self):
        from Sistemas.SaveSystem import save_global
        versos = set(save_global.versos_concluidos)
        return (
            {"Sobrevivente", "Agente", "Feiticeiro"}.issubset(versos),
            bool(save_global.david_martins_derrotado),
            "Cyberpunk" in versos,
        )

    def _requisitos_easter_egg(self):
        return all(self._etapas_easter_egg())

    def obter_progresso_easter_egg(self):
        if self.esta_desbloqueada("easter_egg"):
            return 100
        return round(sum(self._etapas_easter_egg()) * 100 / 3)

    def _notificar_progresso_easter_egg(self, progresso_anterior):
        progresso = self.obter_progresso_easter_egg()
        conquista = self.mapa_conquistas.get("easter_egg")
        if conquista and progresso_anterior < progresso < 100:
            self.notificacoes.append({
                "nome": conquista.nome,
                "titulo": "PROGRESSO DE CONQUISTA",
                "progresso": progresso,
                "icone": conquista.obter_icone(desbloqueada=True, tamanho=(40, 40)),
                "tempo": 220,
                "y_anim": -70,
            })

    def _requisitos_platina(self):
        outras = [c for c in self.conquistas if c.id != "platina"]
        return bool(outras) and all(c.desbloqueada for c in outras)

    def verificar_conquistas_especiais(self, salvar=True):
        alterada = False
        if self._requisitos_easter_egg():
            alterada = self._desbloquear("easter_egg") or alterada
        if self._requisitos_platina():
            alterada = self._desbloquear("platina") or alterada
        if alterada and salvar:
            from Sistemas.SaveSystem import save_global
            save_global.salvar()
        return alterada

    def registrar_vitoria_campanha(self, verso):
        from Sistemas.Constantes import Verso
        from Sistemas.SaveSystem import save_global
        verso_normalizado = Verso.normalizar(verso, estrito=True)
        if verso_normalizado is None:
            return False
        verso = verso_normalizado.value
        progresso_anterior = self.obter_progresso_easter_egg()
        alterada = verso not in save_global.versos_concluidos
        if alterada:
            save_global.versos_concluidos.append(verso)
            self._notificar_progresso_easter_egg(progresso_anterior)
        especiais = self.verificar_conquistas_especiais(salvar=False)
        if alterada or especiais:
            save_global.salvar()
        return alterada

    def registrar_vitoria_david(self):
        from Sistemas.SaveSystem import save_global
        progresso_anterior = self.obter_progresso_easter_egg()
        alterada = not save_global.david_martins_derrotado
        save_global.david_martins_derrotado = True
        if alterada:
            self._notificar_progresso_easter_egg(progresso_anterior)
        especiais = self.verificar_conquistas_especiais(salvar=False)
        if alterada or especiais:
            save_global.salvar()
        return alterada

    def esta_platinado(self):
        return self.esta_desbloqueada("platina") and self._requisitos_platina()

    def obter_conquistas_visiveis(self):
        return [
            c for c in self.conquistas
            if not c.oculta or c.desbloqueada
            or (c.id == "easter_egg" and self.obter_progresso_easter_egg() > 0)
        ]

    def total_desbloqueadas(self):
        return sum(1 for c in self.conquistas if c.desbloqueada)

    def total_conquistas(self):
        return len(self.conquistas)

    def resetar_todas(self):
        for c in self.conquistas:
            c.desbloqueada = False
        try:
            from Sistemas.SaveSystem import save_global
            save_global.conquistas.clear()
            save_global.versos_concluidos.clear()
            save_global.david_martins_derrotado = False
        except Exception:
            pass
        self.notificacoes.clear()
        self.salvar()

    def atualizar_notificacoes(self):
        for notif in self.notificacoes[:3]:
            notif["tempo"] -= 1
            if notif["y_anim"] < 20:
                notif["y_anim"] += 5
            if notif["tempo"] <= 0:
                self.notificacoes.remove(notif)

    def desenhar_notificacao(self, tela):
        if not self.notificacoes:
            return

        if self.fonte_notificacao is None:
            self.fonte_notificacao = obter_fonte(14)
            self.fonte_sub = obter_fonte(11)

        for indice, notif in enumerate(self.notificacoes[:3]):
            y = notif["y_anim"] + indice * 64
            x = (tela.get_width() - 360) // 2
            rect_banner = pygame.Rect(x, y, 360, 56)

            pygame.draw.rect(tela, (15, 15, 20), (rect_banner.x + 3, rect_banner.y + 3, rect_banner.width, rect_banner.height), border_radius=10)
            pygame.draw.rect(tela, (30, 36, 50), rect_banner, border_radius=10)
            pygame.draw.rect(tela, (230, 190, 60), rect_banner, width=2, border_radius=10)

            icone = notif.get("icone")
            if icone:
                tela.blit(icone, (rect_banner.x + 10, rect_banner.y + 8))

            titulo = notif.get("titulo", "🏆 CONQUISTA DESBLOQUEADA!")
            nome = notif["nome"]
            if "progresso" in notif:
                nome = f"{nome}: {notif['progresso']}%"
            txt_topo = self.fonte_sub.render(titulo, True, (255, 215, 0))
            txt_nome = self.fonte_notificacao.render(nome, True, (255, 255, 255))
            tela.blit(txt_topo, (rect_banner.x + 60, rect_banner.y + 8))
            tela.blit(txt_nome, (rect_banner.x + 60, rect_banner.y + 28))

sistema_conquistas = SistemaConquistas()
