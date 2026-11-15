import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pygame

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "An Average City"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

if not pygame.get_init():
    pygame.init()
pygame.display.set_mode((1000, 800))

from Entidades.Minion import Minion, criar_minion
from Entidades.Santuario import Santuario
from Gameplay.GeracaoFases import GeradorFase
from Gameplay.MinigameEsquiva import MinigameEsquiva
from Gameplay.MinigamesAtaque import GerenciadorMinigameAtaque
from Sistemas.Conquistas import sistema_conquistas
from Sistemas.Recursos import caminho_dados, caminho_vfx
from Telas.TelaCheats import GerenciadorCheatsTela
from Telas.TelaCombate import TelaCombate, personagem
from Telas.TelaConfiguracoes import GerenciadorConfiguracoesTela
from Telas.TelaLoja import GerenciadorLoja
from Telas.TelaPosDialogo import GerenciadorPosDialogo


class TestRegressaoLimpeza(unittest.TestCase):
    def test_arvores_sem_invocador_e_invocacao_funcional(self):
        with open(caminho_dados("arvores.json"), "r", encoding="utf-8") as f:
            arvores = json.load(f)
        self.assertNotIn("Invocador", arvores)
        self.assertEqual(set(arvores.keys()), {"Sobrevivente", "Agente", "Feiticeiro", "Cyberpunk"})

        minion = criar_minion("Lobo", dono=personagem)
        self.assertIsInstance(minion, Minion)
        self.assertTrue(minion.is_minion)

    def test_itens_json_economia_e_estrutura(self):
        with open(caminho_dados("itens.json"), "r", encoding="utf-8") as f:
            dados = json.load(f)

        self.assertNotIn("itens", dados)
        consumiveis = {item["id"]: item for item in dados.get("consumiveis", [])}
        self.assertEqual(consumiveis["pocao_mana"]["rec_mp"], 10)
        self.assertEqual(consumiveis["cha_mana"]["rec_mp"], 20)

        for grupo in ("consumiveis", "materiais", "especiais", "equipamentos"):
            for item in dados.get(grupo, []):
                if "preco_compra" in item and "preco_venda" in item:
                    self.assertGreaterEqual(
                        item["preco_compra"],
                        item["preco_venda"],
                        f"Exploit de compra/venda detectado em {item.get('nome')}",
                    )

    def test_conquistas_json_nao_sobrescrito_e_descricao_partida_10(self):
        caminho_conq = Path(caminho_dados("conquistas.json"))
        conteudo_antes = caminho_conq.read_text(encoding="utf-8")
        dados = json.loads(conteudo_antes)
        chefe = next(c for c in dados if c["id"] == "chefe_derrotado")
        self.assertIn("partida 10", chefe["como_liberar"].lower())

        with patch("Sistemas.SaveSystem.save_global.salvar"):
            sistema_conquistas.salvar()

        conteudo_depois = caminho_conq.read_text(encoding="utf-8")
        self.assertEqual(conteudo_antes, conteudo_depois)

    def test_eventos_tipo_padronizado_e_cache_classe(self):
        with open(caminho_dados("eventos.json"), "r", encoding="utf-8") as f:
            eventos = json.load(f)
        for ev in eventos:
            self.assertEqual(ev["tipo"], ev["tipo"].lower())

        g1 = GeradorFase(1)
        g2 = GeradorFase(2)
        self.assertTrue(len(GeradorFase.EVENTOS_NEUTROS) > 0)
        self.assertIs(g1.EVENTOS_NEUTROS, g2.EVENTOS_NEUTROS)

    def test_tela_pos_dialogo_desenha_e_separa_btn_loja(self):
        surf = pygame.Surface((1000, 800))
        tela = GerenciadorPosDialogo(surf)
        tela.configurar({
            "sucesso": True,
            "nome_evento": "Uma Pausa para comprar mantimentos",
            "narrativa": "Você encontrou o balcão seguro.",
            "efeitos": ["Acesso livre à Loja"],
        })
        self.assertTrue(tela.tem_loja)
        self.assertIsNotNone(tela.btn_loja)
        tela.desenhar((0, 0))
        self.assertLessEqual(tela.btn_loja.rect.right, tela.btn_continuar.rect.left)

    def test_minigame_ataque_lutador_estilo2_aceita_enter(self):
        surf = pygame.Surface((1000, 800))
        mg = GerenciadorMinigameAtaque(surf)

        class HabFake:
            nome = "Soco Carregado"
            tipo = "Físico"
            dano = 10
            custo_mp = 0
            precisao = 1.0
            estilo = 2

        mg.iniciar(HabFake(), alvo=None, jogador_ativo=personagem)
        self.assertEqual(mg.classe_normalizada, "Físico")
        self.assertEqual(mg.estilo, 2)

        teclas = {k: False for k in range(512)}
        teclas[pygame.K_RETURN] = True
        mg.atualizar((0, 0), (False, False, False), teclas_pressionadas=teclas)
        self.assertTrue(mg.forca_segurando)
        self.assertGreater(mg.forca_atual, 0.0)

    def test_santuario_ignora_dano_zero_ou_negativo(self):
        sant = Santuario(x=600, y=350)
        self.assertEqual(sant.golpes_restantes(), 4)
        self.assertEqual(sant.receber_dano(0), 0)
        self.assertEqual(sant.receber_dano(-10), 0)
        self.assertEqual(sant.golpes_restantes(), 4)
        self.assertGreater(sant.receber_dano(5), 0)
        self.assertEqual(sant.golpes_restantes(), 3)

    def test_minion_clamp_mp_zero_e_fallback_imagem(self):
        minion = Minion(
            100,
            100,
            nome="Teste",
            vida_maxima=20,
            nome_imagem="sprite_inexistente_teste.png",
            max_mp=0,
        )
        self.assertEqual(minion.max_mp, 0)
        self.assertEqual(minion.mp, 0)
        self.assertIsNotNone(minion.imagem_base)
        self.assertEqual(minion.curar_mp(5), 0)
        self.assertEqual(minion.mp, 0)
        dano = minion.receber_dano(3)
        self.assertEqual(dano, 3)
        self.assertEqual(minion.hp, 17)

    def test_caminho_vfx_nao_aponta_para_sfx(self):
        caminho = Path(caminho_vfx("Corte.png"))
        self.assertNotIn("SFX", caminho.parts)
        self.assertTrue(caminho.exists())

    def test_minigame_esquiva_evitou_tudo_exige_todas_rodadas(self):
        surf = pygame.Surface((1000, 800))
        mg = MinigameEsquiva(total_rodadas=3, tela=surf)
        mg.iniciar(velocidade_base=5.0, dano_pendente=20)
        mg.acertos = 0
        mg.acertos_centro = 2
        for b in mg.barras:
            b["ativa"] = False
        mg.timer_encerramento = 24
        res = mg.atualizar()
        self.assertIsNotNone(res)
        self.assertFalse(res["evitou_tudo"])

    def test_tela_combate_reiniciar_limpa_status_p1_e_p2(self):
        surf = pygame.Surface((1000, 800))
        combate = TelaCombate(surf)
        combate.duas_pessoas = True
        combate.reiniciar(forcar_novos_inimigos=True)
        self.assertIsNotNone(combate.personagem2)

        personagem.bloqueando = True
        personagem.focado = True
        combate.personagem2.bloqueando = True
        combate.personagem2.recuperando = True
        combate.personagem2.focado = True
        combate.personagem2.cego = True

        combate.reiniciar(forcar_novos_inimigos=False)
        self.assertFalse(personagem.bloqueando)
        self.assertFalse(personagem.focado)
        self.assertFalse(combate.personagem2.bloqueando)
        self.assertFalse(combate.personagem2.recuperando)
        self.assertFalse(combate.personagem2.focado)
        self.assertFalse(combate.personagem2.cego)

    def test_telas_definir_cores_config_cheats_e_loja(self):
        surf = pygame.Surface((1000, 800))

        cfg = GerenciadorConfiguracoesTela(surf)
        cfg._sincronizar_textos()
        cfg.atualizar((0, 0), (False, False, False))
        cfg.desenhar()

        cheats = GerenciadorCheatsTela(surf)
        cheats.atualizar((0, 0), (False, False, False))
        cheats.desenhar()
        cheats.modo = "seletor_batalha"
        cheats.atualizar((0, 0), (False, False, False))
        cheats.desenhar()

        loja = GerenciadorLoja(surf)
        loja.atualizar((0, 0), (False, False, False))
        loja.desenhar((0, 0))

    def test_conquistas_individuais_tres_chefes(self):
        sistema_conquistas.carregar()
        esperadas = {
            "Sukuna": "chefe_sukuna",
            "Charlie": "chefe_charlie",
            "Estraga Prazeres": "chefe_estraga_prazeres",
        }
        for id_conq in esperadas.values():
            self.assertIn(id_conq, sistema_conquistas.mapa_conquistas)
            conq = sistema_conquistas.mapa_conquistas[id_conq]
            icone = conq.obter_icone(desbloqueada=True, tamanho=(48, 48))
            self.assertEqual(icone.get_size(), (48, 48))

        from Entidades.Inimigo import Inimigo
        surf = pygame.Surface((1000, 800))
        sprites_chefe = {
            "Sukuna": "Sukuna.png",
            "Charlie": "Charlie.png",
            "Estraga Prazeres": "Killjoy.png",
        }
        for nome_chefe, id_esperado in esperadas.items():
            combate = TelaCombate(surf)
            personagem.hp = personagem.max_hp
            chefe = Inimigo(
                x=700,
                y=300,
                nome=nome_chefe,
                vida_maxima=100,
                nome_imagem=sprites_chefe[nome_chefe],
            )
            chefe.hp = 0
            combate.ordem_turnos = [personagem, chefe]
            combate.xp_calculado = False
            combate.estado = "combate"
            combate.partida_atual = 10
            combate.total_partidas = 10
            with patch.object(sistema_conquistas, "desbloquear") as mock_desb:
                combate.atualizar((0, 0), (False, False, False))
                chamadas = [call.args[0] for call in mock_desb.call_args_list]
                self.assertIn(id_esperado, chamadas)
                self.assertEqual(combate.ultimo_chefe_derrotado, nome_chefe)

    def test_equipamentos_diferenciados_entre_dois_jogadores(self):
        from Entidades.Personagem import Personagem
        from Sistemas.Inventario import Equipamento, inventario_global
        from Telas.TelaDescanso import TelaDescanso

        inventario_global.resetar()
        personagem.resetar(resetar_cheats=True)
        try:
            p2 = Personagem(150, 350, "pixil.png", nome="Jogador 2")
            p2.is_player = True

            espada_p1 = Equipamento("Espada P1", {"For": 7}, categoria="arma")
            colete_p1 = Equipamento("Colete P1", {"Con": 4, "Armadura": 5}, categoria="peitoral")
            cajado_p2 = Equipamento("Cajado P2", {"Int": 9, "Agi": 6}, categoria="arma")
            bota_p2 = Equipamento("Bota P2", {"Agi": 4, "Defesa": 3}, categoria="bota")

            inventario_global.equipar(espada_p1, jogador=personagem)
            inventario_global.equipar(colete_p1, jogador=personagem)
            inventario_global.equipar(cajado_p2, jogador=p2)
            inventario_global.equipar(bota_p2, jogador=p2)

            self.assertEqual(personagem.obter_bonus_equipamento("For"), 7)
            self.assertEqual(personagem.obter_bonus_equipamento("Int"), 0)
            self.assertEqual(p2.obter_bonus_equipamento("Int"), 9)
            self.assertEqual(p2.obter_bonus_equipamento("For"), 0)

            surf = pygame.Surface((1000, 800))
            combate = TelaCombate(surf)
            combate.duas_pessoas = True
            combate.personagem2 = p2
            self.assertGreater(
                combate.calcular_defesa_passiva(personagem),
                combate.calcular_defesa_passiva(p2),
            )
            self.assertLess(
                combate.velocidade_esquiva(p2),
                combate.velocidade_esquiva(personagem),
            )

            # Equipar um item já vestido por P1 em P2 remove de P1 automaticamente
            inventario_global.equipar(espada_p1, jogador=p2)
            self.assertIsNone(inventario_global.obter_slots_equipamento(jogador=personagem)[0][1])
            self.assertIs(inventario_global.obter_slots_equipamento(jogador=p2)[0][1], espada_p1)

            # TelaDescanso exibe/opera apenas os slots do jogador selecionado
            descanso = TelaDescanso(surf)
            descanso.jogadores = [personagem, p2]
            descanso.jogador_selecionado = 1
            descanso.atualizar((0, 0), (False, False, False))
            descanso.desenhar((0, 0))
            self.assertIs(inventario_global.obter_equipamento_alvo(jogador=descanso._jogador_atual()), espada_p1)

            # TelaLoja lista e vende itens equipados de ambos os jogadores
            loja = GerenciadorLoja(surf)
            loja.tipo_loja = "perigo"
            vendiveis = loja._obter_equipamentos_vendiveis()
            donos = {id(v["eq"]): v["dono"] for v in vendiveis if v["equipado"]}
            self.assertIs(donos[id(colete_p1)], personagem)
            self.assertIs(donos[id(espada_p1)], p2)
            loja._executar_venda(next(v for v in vendiveis if v["eq"] is espada_p1))
            self.assertIsNone(inventario_global.obter_slots_equipamento(jogador=p2)[0][1])
        finally:
            inventario_global.resetar()
            personagem.resetar(resetar_cheats=True)

    def test_verso_cyberpunk_edgerunners_completo(self):
        from Gameplay.GeracaoFases import BANCO_INIMIGOS, GeradorFase
        from Gameplay.Habilidades import banco_habilidades, obter_ultimate
        from Sistemas.Constantes import Verso, obter_equipamento_inicial
        from Telas.TelaVerso import GerenciadorVerso, SPRITES_POR_VERSO

        self.assertEqual(Verso.normalizar("edgerunners"), Verso.CYBERPUNK)
        self.assertEqual(SPRITES_POR_VERSO["Cyberpunk"], "CYBERC.png")

        surf = pygame.Surface((1000, 800))
        with patch("Telas.TelaVerso.save_global.conquistas", [
            "chefe_sukuna", "chefe_charlie", "chefe_estraga_prazeres",
        ]):
            tela_verso = GerenciadorVerso(surf)
        self.assertIn("Cyberpunk", tela_verso.versos)
        self.assertIn("Cyberpunk", tela_verso.esferas_rects)
        self.assertIsNotNone(tela_verso.imagens_por_verso["Cyberpunk"])

        arvore = tela_verso.arvores_por_verso["Cyberpunk"]
        self.assertEqual([n["id"] for n in arvore], ["C1", "C2", "C3", "C4"])
        self.assertEqual(sum(n["preco"] for n in arvore), 180)

        for classe in ("Físico", "Distância", "Magia", "Invocador"):
            normais = [h for h in banco_habilidades.values() if h.verso == "Cyberpunk" and h.tipo == classe]
            self.assertGreaterEqual(len(normais), 2)
            ult = obter_ultimate("Cyberpunk", classe)
            self.assertIsNotNone(ult)
            eq_nome, _ = obter_equipamento_inicial("Cyberpunk", classe)
            self.assertNotEqual(eq_nome, "Equipamento Padrão")

        inimigos_cyber = [i for i in BANCO_INIMIGOS if i.get("verso") == "Cyberpunk"]
        self.assertGreaterEqual(len(inimigos_cyber), 4)
        chefe = GeradorFase().gerar_chefe_verso("Cyberpunk")
        self.assertEqual(chefe.nome, "Adam Smasher")

        from Sistemas.Constantes import obter_musica_combate
        self.assertEqual(obter_musica_combate("Cyberpunk", eh_chefe=False), "Cyber Combate.mp3")
        self.assertEqual(obter_musica_combate("Cyberpunk", eh_chefe=True), "Cyber Boss.mp3")

        combate = TelaCombate(surf)
        personagem.resetar(resetar_cheats=True)
        vel_sem_c1 = combate.velocidade_esquiva(personagem)
        personagem.talentos = {"C1"}
        vel_com_c1 = combate.velocidade_esquiva(personagem)
        self.assertAlmostEqual(vel_com_c1, max(2.4, vel_sem_c1 * 0.80), places=5)

        # Verifica C1: aumenta o valor da esquiva (parry 20%, esquiva 10%)
        from Gameplay.MinigameEsquiva import MinigameEsquiva
        minigame_sem_c1 = MinigameEsquiva(total_rodadas=1, tela=surf)
        personagem.talentos = set()
        minigame_sem_c1.iniciar(velocidade_base=3.0, dano_pendente=100, alvo=personagem, tela=surf)
        minigame_sem_c1.barras[0]["x"] = 200.0
        minigame_sem_c1.atualizar(clicou=True)
        self.assertAlmostEqual(minigame_sem_c1.reducao, 0.10, places=5)

        minigame_com_c1 = MinigameEsquiva(total_rodadas=1, tela=surf)
        personagem.talentos = {"C1"}
        minigame_com_c1.iniciar(velocidade_base=3.0, dano_pendente=100, alvo=personagem, tela=surf)
        minigame_com_c1.barras[0]["x"] = 200.0
        minigame_com_c1.atualizar(clicou=True)
        self.assertAlmostEqual(minigame_com_c1.reducao, 0.20, places=5)

        minigame_esquiva_c1 = MinigameEsquiva(total_rodadas=1, tela=surf)
        minigame_esquiva_c1.iniciar(velocidade_base=3.0, dano_pendente=100, alvo=personagem, tela=surf)
        minigame_esquiva_c1.barras[0]["x"] = 250.0
        minigame_esquiva_c1.atualizar(clicou=True)
        self.assertAlmostEqual(minigame_esquiva_c1.reducao, 0.10, places=5)

        personagem.talentos = {"C1", "C2", "C3", "C4"}
        combate.configurar_classe("Cyberpunk", "Físico")
        self.assertIn("Sandevistan: Corte Zero", personagem.ataques)
        self.assertIn("Corte Mantis", personagem.ataques)

        # Verifica C2: +20% de dano e chance extra de Eletrocutar mesmo em ataque sem efeito nativo
        from Gameplay.Habilidades import Habilidade
        inimigo_teste = GeradorFase().gerar_chefe_verso("Cyberpunk")
        inimigo_teste.hp = 500
        inimigo_teste.max_hp = 500
        combate.ordem_turnos = [personagem, inimigo_teste]
        combate.indice_turno = 0
        hab_sem_efeito = Habilidade("Corte Teste", "Físico", 10, 0, 1.0, "Teste", efeito=None, chance_efeito=0.0)
        with patch("Telas.TelaCombate.random.random", return_value=0.05):
            combate.executar_ataque_jogador(hab_sem_efeito, inimigo_teste)
        self.assertTrue(getattr(inimigo_teste, "eletrocutado", False))

        # Verifica C3: 2 ações por turno e 10% de chance de ficar atordoado no começo do turno
        personagem.talentos = {"C3"}
        personagem.atordoado = False
        combate.cooldown_feedback = 0
        combate.acao_pos_feedback = None
        combate.turno_jogador_iniciado = False
        combate.timer_inimigo = 0
        combate.indice_turno = 0
        with patch("Telas.TelaCombate.random.random", return_value=0.50):
            combate.atualizar((0, 0), False)
        self.assertFalse(getattr(personagem, "atordoado", False))
        self.assertEqual(combate.acoes_restantes_jogador, 2)

        combate.finalizar_acao_jogador()
        self.assertEqual(combate.indice_turno, 0)
        self.assertEqual(combate.acoes_restantes_jogador, 1)

        combate.finalizar_acao_jogador()
        self.assertEqual(combate.indice_turno, 1)

        # Verifica C3: 10% de chance de atordoar no começo do turno
        personagem.atordoado = False
        combate.cooldown_feedback = 0
        combate.acao_pos_feedback = None
        combate.turno_jogador_iniciado = False
        combate.timer_inimigo = 0
        combate.indice_turno = 0
        with patch("Telas.TelaCombate.random.random", return_value=0.05):
            combate.atualizar((0, 0), False)
        self.assertTrue(getattr(personagem, "atordoado", False))

        # Verifica que C3 não concede mais +1 PM ao abater inimigo
        personagem.atordoado = False
        inimigo_teste.hp = 1
        personagem.mp = 0
        personagem.max_mp = 10
        with patch("Telas.TelaCombate.random.random", return_value=0.50):
            combate.executar_ataque_jogador(hab_sem_efeito, inimigo_teste)
        self.assertEqual(personagem.mp, 0)

        personagem.resetar(resetar_cheats=True)
        from Sistemas.Inventario import inventario_global
        inventario_global.resetar()


if __name__ == "__main__":
    unittest.main()
