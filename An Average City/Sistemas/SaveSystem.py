import json
import os
from Sistemas.Recursos import caminho_dados, caminho_saves

CAMINHO_SAVES = caminho_saves()
ARQUIVO_SAVE = caminho_saves("save.json")


class GerenciadorSave:
    def __init__(self):
        self.pontos = 0
        self.total_pontos_acumulados = 0
        self.maior_pontuacao = 0
        self.conquistas = []
        self.member_card_coletado = False
        self.progresso_versos = {}
        self.habilidades_desabilitadas = {}
        self.carregar()

    def carregar(self):
        if not os.path.exists(ARQUIVO_SAVE):






            return

        try:
            with open(ARQUIVO_SAVE, "r", encoding="utf-8") as f:
                dados = json.load(f)
                self.pontos = max(0, int(dados.get("pontos", 0)))
                self.total_pontos_acumulados = max(0, int(dados.get("total_pontos_acumulados", self.pontos)))
                self.maior_pontuacao = max(0, int(dados.get("maior_pontuacao", 0)))
                self.conquistas = list(dados.get("conquistas", []))
                self.member_card_coletado = bool(dados.get("member_card_coletado", False))
                self.progresso_versos = dict(dados.get("progresso_versos", {}))
                self.habilidades_desabilitadas = {k: list(v) for k, v in dict(dados.get("habilidades_desabilitadas", {})).items()}
        except Exception as e:
            print(f"⚠️ Erro ao carregar save.json: {e}")

    def salvar(self):
        try:
            if not os.path.exists(CAMINHO_SAVES):
                os.makedirs(CAMINHO_SAVES, exist_ok=True)

            dados = {
                "pontos": int(self.pontos),
                "total_pontos_acumulados": int(self.total_pontos_acumulados),
                "maior_pontuacao": int(self.maior_pontuacao),
                "conquistas": list(self.conquistas),
                "member_card_coletado": bool(self.member_card_coletado),
                "progresso_versos": dict(self.progresso_versos),
                "habilidades_desabilitadas": {k: list(v) for k, v in self.habilidades_desabilitadas.items()},
            }

            with open(ARQUIVO_SAVE, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=4)

            try:
                from Sistemas.GerenciadorAudio import tocar_sfx
                tocar_sfx("Save.wav")
            except Exception:
                pass
        except Exception as e:
            print(f"⚠️ Erro ao salvar em save.json: {e}")

    def obter_progresso_versos(self):
        return dict(self.progresso_versos)

    def obter_progresso_verso(self, verso):
        return list(self.progresso_versos.get(verso, []))

    def definir_progresso_verso(self, verso, talentos):
        self.progresso_versos[verso] = list(talentos)

    def obter_habilidades_desabilitadas(self, verso=None):
        if verso is not None:
            return list(self.habilidades_desabilitadas.get(verso, []))
        return {k: list(v) for k, v in self.habilidades_desabilitadas.items()}

    def definir_habilidades_desabilitadas(self, verso, lista):
        self.habilidades_desabilitadas[verso] = list(lista)

    def esta_habilidade_desabilitada(self, verso, id_habilidade):
        return id_habilidade in self.habilidades_desabilitadas.get(verso, [])

    def obter_pontos(self):
        return self.pontos

    def definir_pontos(self, novos_pontos):
        self.pontos = max(0, int(novos_pontos))

    def adicionar_pontos(self, quantidade):
        qtd = int(quantidade)
        self.pontos = max(0, self.pontos + qtd)
        if qtd > 0:
            self.total_pontos_acumulados += qtd

    def registrar_partida(self, pontos_partida):
        pts = int(pontos_partida)
        if pts > self.maior_pontuacao:
            self.maior_pontuacao = pts
        self.adicionar_pontos(pts)

    def desbloquear_conquista(self, id_conquista):
        if id_conquista not in self.conquistas:
            self.conquistas.append(id_conquista)
            return True
        return False

    def esta_desbloqueada(self, id_conquista):
        return id_conquista in self.conquistas

    def tem_member_card(self):
        return bool(getattr(self, 'member_card_coletado', False))

    def coletar_member_card(self):
        self.member_card_coletado = True
        return True

    def definir_member_card(self, valor):
        self.member_card_coletado = bool(valor)

    def resetar_tudo(self):
        self.pontos = 0
        self.total_pontos_acumulados = 0
        self.maior_pontuacao = 0
        self.conquistas.clear()
        self.member_card_coletado = False
        self.progresso_versos.clear()
        self.habilidades_desabilitadas.clear()
        self.salvar()

save_global = GerenciadorSave()
