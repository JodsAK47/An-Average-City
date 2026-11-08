import os
import sys
import math
import unittest
import pygame

# Inicialização headless do Pygame para testes
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

# Assegura que o diretório raiz esteja no sys.path
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
DIRETORIO_RAIZ = os.path.abspath(os.path.join(DIRETORIO_ATUAL, ".."))
if DIRETORIO_RAIZ not in sys.path:
    sys.path.insert(0, DIRETORIO_RAIZ)
DIRETORIO_PROJETO = os.path.join(DIRETORIO_RAIZ, "An Average City")
if DIRETORIO_PROJETO not in sys.path:
    sys.path.insert(0, DIRETORIO_PROJETO)

pygame.init()
pygame.display.set_mode((1000, 768))

from Entidades.Personagem import personagem
from Sistemas.Inventario import inventario_global, Consumivel
from Telas.TelaCombate import TelaCombate


class TestCombateHUDItensEAgir(unittest.TestCase):
    def setUp(self):
        # Reset de atributos do jogador
        personagem.hp = 50
        personagem.max_hp = 100
        personagem.mp = 10
        personagem.max_mp = 20
        personagem.bloqueando = False
        personagem.recuperando = False
        personagem.focado = False
        personagem.ataques = ["Golpe Rápido", "Impacto Pesado"]

        # Reset do inventário consumíveis
        inventario_global.consumiveis = []

        # Instanciação da tela de combate
        self.tela = pygame.display.get_surface()
        self.jogo = TelaCombate(self.tela)
        self.jogo.menu_acoes_estado = "principal"
        self.jogo.cooldown_feedback = 0

    def test_botoes_menu_principal_estrutura(self):
        """Verifica se o botão AGIR substituiu o de ataque e ITEM substituiu BLOQ no menu principal."""
        self.assertEqual(self.jogo.btn_agir.texto, "AGIR")
        self.assertEqual(self.jogo.btn_ataque, self.jogo.btn_agir)
        self.assertEqual(self.jogo.btn_item.texto, "ITEM")
        self.assertIsNotNone(self.jogo.btn_bloquear)
        self.assertEqual(self.jogo.btn_bloquear.texto, "BLOQUEAR")

    def test_transicao_principal_para_agir(self):
        """Testa clique no botão AGIR transicionando para o submenu 'agir'."""
        self.jogo.menu_acoes_estado = "principal"
        pos = (self.jogo.btn_agir.rect.centerx, self.jogo.btn_agir.rect.centery)
        self.jogo._processar_menu_principal(personagem, pos, (False, False, False), clicou=True)
        self.assertEqual(self.jogo.menu_acoes_estado, "agir")

    def test_submenu_agir_voltar(self):
        """Testa botão VOLTAR no submenu 'agir' retornando para o menu principal."""
        self.jogo.menu_acoes_estado = "agir"
        pos = (self.jogo.btn_agir_voltar.rect.centerx, self.jogo.btn_agir_voltar.rect.centery)
        self.jogo._processar_menu_agir(personagem, pos, (False, False, False), clicou=True)
        self.assertEqual(self.jogo.menu_acoes_estado, "principal")

    def test_submenu_agir_atacar_abre_ataques(self):
        """Testa botão ATACAR dentro de 'agir' abrindo a lista de ataques."""
        self.jogo.menu_acoes_estado = "agir"
        pos = (self.jogo.btn_agir_atacar.rect.centerx, self.jogo.btn_agir_atacar.rect.centery)
        self.jogo._processar_menu_agir(personagem, pos, (False, False, False), clicou=True)
        self.assertEqual(self.jogo.menu_acoes_estado, "ataques")
        self.assertGreater(len(self.jogo.botoes_habilidades_dinamicos), 0)

        # Voltar do menu de ataques deve retornar para 'agir'
        pos_voltar = (self.jogo.btn_voltar.rect.centerx, self.jogo.btn_voltar.rect.centery)
        self.jogo._processar_menu_ataques(personagem, pos_voltar, (False, False, False), clicou=True)
        self.assertEqual(self.jogo.menu_acoes_estado, "agir")

    def test_submenu_agir_bloquear(self):
        """Testa botão BLOQUEAR dentro de 'agir' ativando bloqueio e avançando turno."""
        self.jogo.menu_acoes_estado = "agir"
        personagem.bloqueando = False
        pos = (self.jogo.btn_agir_bloquear.rect.centerx, self.jogo.btn_agir_bloquear.rect.centery)
        self.jogo._processar_menu_agir(personagem, pos, (False, False, False), clicou=True)
        self.assertTrue(personagem.bloqueando)
        self.assertIn("BLOQUEAR", self.jogo.mensagem_log)
        self.assertEqual(self.jogo.menu_acoes_estado, "principal")
        self.assertGreater(self.jogo.cooldown_feedback, 0)

    def test_transicao_principal_para_itens(self):
        """Testa clique no botão ITEM abrindo o submenu de itens."""
        inventario_global.consumiveis = [
            Consumivel("Poção de Vida", "Restaura 30 HP", rec_hp=30, rec_mp=0)
        ]
        self.jogo.menu_acoes_estado = "principal"
        pos = (self.jogo.btn_item.rect.centerx, self.jogo.btn_item.rect.centery)
        self.jogo._processar_menu_principal(personagem, pos, (False, False, False), clicou=True)
        self.assertEqual(self.jogo.menu_acoes_estado, "itens")
        self.assertEqual(len(self.jogo.botoes_itens_dinamicos), 1)

    def test_submenu_itens_voltar(self):
        """Testa botão VOLTAR no submenu de itens retornando para o menu principal."""
        self.jogo.menu_acoes_estado = "itens"
        self.jogo.gerar_botoes_itens(personagem)
        pos = (self.jogo.btn_voltar_itens.rect.centerx, self.jogo.btn_voltar_itens.rect.centery)
        self.jogo._processar_menu_itens(personagem, pos, (False, False, False), clicou=True)
        self.assertEqual(self.jogo.menu_acoes_estado, "principal")

    def test_uso_de_item_em_combate(self):
        """Testa o uso efetivo de um item consumível durante o combate."""
        pocao = Consumivel("Poção de Vida", "Restaura 30 HP", rec_hp=30, rec_mp=0)
        pocao.quantidade = 2
        inventario_global.consumiveis = [pocao]

        personagem.hp = 40
        personagem.max_hp = 100

        self.jogo.menu_acoes_estado = "itens"
        self.jogo.gerar_botoes_itens(personagem)

        # Clica no botão da Poção de Vida
        btn_pocao = self.jogo.botoes_itens_dinamicos[0]["botao"]
        pos = (btn_pocao.rect.centerx, btn_pocao.rect.centery)
        self.jogo._processar_menu_itens(personagem, pos, (False, False, False), clicou=True)

        # Vida aumentada em 30, quantidade diminuída para 1, cooldown ativado
        self.assertEqual(personagem.hp, 70)
        self.assertEqual(pocao.quantidade, 1)
        self.assertIn("usou Poção de Vida", self.jogo.mensagem_log)
        self.assertEqual(self.jogo.menu_acoes_estado, "principal")
        self.assertGreater(self.jogo.cooldown_feedback, 0)

    def test_expansao_vertical_hud_subindo_topo(self):
        """
        Testa o requisito crítico:
        'se houverem mais itens do que espaço na hud faça que ela fique maior verticalmente fazendo o topo dela subir'.
        A base inferior deve permanecer sempre em 702 (acima dos cartões dos jogadores em 716),
        enquanto a coordenada y diminui (o topo sobe) e a altura aumenta proporcionalmente.
        """
        base_inferior_esperada = 702

        # 1. Estado principal (padrão)
        self.jogo.menu_acoes_estado = "principal"
        rect_padrao = self.jogo.obter_rect_hud_acoes()
        self.assertEqual(rect_padrao.y, 596)
        self.assertEqual(rect_padrao.height, 106)
        self.assertEqual(rect_padrao.bottom, base_inferior_esperada)

        # 2. Estado itens com até 3 itens (1 linha)
        inventario_global.consumiveis = [
            Consumivel(f"Item {i}", "Desc", rec_hp=10) for i in range(3)
        ]
        self.jogo.menu_acoes_estado = "itens"
        rect_1_linha = self.jogo.obter_rect_hud_acoes()
        self.assertEqual(rect_1_linha.y, 596)
        self.assertEqual(rect_1_linha.height, 106)
        self.assertEqual(rect_1_linha.bottom, base_inferior_esperada)

        # 3. Estado itens com 5 itens (requer 2 linhas: 5 itens + 1 voltar = 6 slots)
        inventario_global.consumiveis = [
            Consumivel(f"Item {i}", "Desc", rec_hp=10) for i in range(5)
        ]
        rect_2_linhas = self.jogo.obter_rect_hud_acoes()
        self.assertLess(rect_2_linhas.y, 596, "O topo da HUD deve subir (y menor)!")
        self.assertEqual(rect_2_linhas.y, 540)
        self.assertEqual(rect_2_linhas.height, 162)
        self.assertEqual(rect_2_linhas.bottom, base_inferior_esperada, "A base inferior da HUD deve permanecer fixa em 702!")

        # 4. Estado itens com 9 itens (requer 3 linhas: 9 itens + 1 voltar = 10 slots)
        inventario_global.consumiveis = [
            Consumivel(f"Item {i}", "Desc", rec_hp=10) for i in range(9)
        ]
        rect_3_linhas = self.jogo.obter_rect_hud_acoes()
        self.assertLess(rect_3_linhas.y, rect_2_linhas.y, "Com 3 linhas, o topo da HUD deve subir ainda mais!")
        self.assertEqual(rect_3_linhas.y, 484)
        self.assertEqual(rect_3_linhas.height, 218)
        self.assertEqual(rect_3_linhas.bottom, base_inferior_esperada, "A base inferior continua fixa em 702!")

    def test_renderizacao_desenhar_sem_erros(self):
        """Verifica se o método desenhar() roda sem exceções em todos os menus (principal, agir, itens, ataques, minions)."""
        inventario_global.consumiveis = [
            Consumivel(f"Item {i}", "Desc", rec_hp=10) for i in range(6)
        ]

        estados_para_testar = ["principal", "agir", "itens", "ataques", "minions"]
        for est in estados_para_testar:
            self.jogo.menu_acoes_estado = est
            if est == "itens":
                self.jogo.gerar_botoes_itens(personagem)
            elif est == "ataques":
                self.jogo.gerar_botoes_ataque(personagem)
            elif est == "minions":
                self.jogo.gerar_botoes_minions(personagem)
            self.jogo.desenhar()

    def test_invocador_botao_minions_ciano(self):
        """Verifica se ao clicar em atacar como Invocador, surge o botão MINIONS na cor ciano da classe."""
        self.jogo.configurar_classe("Sobrevivente", "Invocador")
        self.jogo.menu_acoes_estado = "agir"

        # Clica em ATACAR
        pos_atacar = (self.jogo.btn_agir_atacar.rect.centerx, self.jogo.btn_agir_atacar.rect.centery)
        self.jogo._processar_menu_agir(personagem, pos_atacar, (False, False, False), clicou=True)
        self.assertEqual(self.jogo.menu_acoes_estado, "ataques")

        # Procura o botão MINIONS
        nomes = [item["nome"] for item in self.jogo.botoes_habilidades_dinamicos]
        self.assertIn("MINIONS", nomes)

        item_minions = next(item for item in self.jogo.botoes_habilidades_dinamicos if item["nome"] == "MINIONS")
        self.assertEqual(item_minions.get("tipo"), "minions")
        # Cor base ciano da classe Invocador (52, 168, 148)
        self.assertEqual(item_minions["botao"].cor_base, (52, 168, 148))

    def test_invocador_clique_minions_abre_summons_e_volta(self):
        """Verifica se clicar no botão MINIONS abre o submenu com os summons dele e se VOLTAR retorna para ataques."""
        self.jogo.configurar_classe("Sobrevivente", "Invocador")
        self.jogo.gerar_botoes_ataque(personagem)
        self.jogo.menu_acoes_estado = "ataques"

        item_minions = next(item for item in self.jogo.botoes_habilidades_dinamicos if item["nome"] == "MINIONS")
        pos_minions = (item_minions["botao"].rect.centerx, item_minions["botao"].rect.centery)
        self.jogo._processar_menu_ataques(personagem, pos_minions, (False, False, False), clicou=True)

        # Transiciona para 'minions'
        self.assertEqual(self.jogo.menu_acoes_estado, "minions")
        self.assertGreater(len(self.jogo.botoes_minions_dinamicos), 0)

        # Verifica se os summons do Invocador estão presentes
        nomes_summons = [m["nome"] for m in self.jogo.botoes_minions_dinamicos]
        self.assertIn("Invocar Abelha", nomes_summons)
        self.assertIn("Invocar Pássaro Olhudo", nomes_summons)

        # Clicar em VOLTAR no submenu de minions retorna para o menu de ataques
        pos_voltar = (self.jogo.btn_voltar_minions.rect.centerx, self.jogo.btn_voltar_minions.rect.centery)
        self.jogo._processar_menu_minions(personagem, pos_voltar, (False, False, False), clicou=True)
        self.assertEqual(self.jogo.menu_acoes_estado, "ataques")

    def test_classe_nao_invocador_sem_botao_minions(self):
        """Verifica se classes sem minions (ex: Físico) mostram diretamente seus ataques sem o botão MINIONS."""
        self.jogo.configurar_classe("Sobrevivente", "Físico")
        self.jogo.gerar_botoes_ataque(personagem)
        nomes = [item["nome"] for item in self.jogo.botoes_habilidades_dinamicos]
        self.assertNotIn("MINIONS", nomes)
        self.assertGreater(len(nomes), 0)

    def test_expansao_vertical_hud_minions_subindo_topo(self):
        """Verifica se quando houver mais de 3 summons, a HUD de minions expande verticalmente subindo o topo."""
        base_inferior_esperada = 702
        self.jogo.configurar_classe("Sobrevivente", "Invocador")

        # Invocador com até 3 summons (linhas = 1)
        self.jogo.menu_acoes_estado = "minions"
        rect_1_linha = self.jogo.obter_rect_hud_acoes()
        self.assertEqual(rect_1_linha.y, 596)
        self.assertEqual(rect_1_linha.height, 106)
        self.assertEqual(rect_1_linha.bottom, base_inferior_esperada)

        # Simula Invocador com 5 summons
        personagem.ataques = [
            "Invocar Abelha", "Invocar Pássaro Olhudo", "Cães Divinos", "Invocar Nue", "Implantar Torreta"
        ]
        rect_2_linhas = self.jogo.obter_rect_hud_acoes()
        self.assertEqual(rect_2_linhas.y, 540)
        self.assertEqual(rect_2_linhas.height, 162)
        self.assertEqual(rect_2_linhas.bottom, base_inferior_esperada)

    def test_limite_summons_nao_cura_nem_reforca(self):
        """Verifica que ao atingir o limite de summons, invocar NÃO cura os summons existentes e retorna None."""
        self.jogo.configurar_classe("Sobrevivente", "Invocador")
        limite = self.jogo.limite_minions(personagem)
        self.assertEqual(limite, 2)

        # Invoca minions até atingir o limite (2 minions)
        m1 = self.jogo.invocar_minion("Abelha Soldado", dono=personagem)
        m2 = self.jogo.invocar_minion("Pássaro Olhudo", dono=personagem)
        self.assertIsNotNone(m1)
        self.assertIsNotNone(m2)
        self.assertEqual(len(self.jogo.obter_minions_vivos(personagem)), 2)

        # Reduz HP do minion 1 para testar se ele seria indevidamente curado
        m1.hp = 10
        hp_anterior = m1.hp

        # Tenta invocar novamente com o limite já atingido
        resultado = self.jogo.invocar_minion("Abelha Soldado", dono=personagem)

        # Não deve invocar novo minion nem curar o existente
        self.assertIsNone(resultado, "Com o limite atingido, invocar_minion deve retornar None.")
        self.assertEqual(m1.hp, hp_anterior, "Minion NÃO deve ser curado ao atingir o limite!")
        self.assertEqual(len(self.jogo.obter_minions_vivos(personagem)), 2)

        # Teste via interface do menu 'minions'
        self.jogo.menu_acoes_estado = "minions"
        self.jogo.gerar_botoes_minions(personagem)
        btn_abelha = self.jogo.botoes_minions_dinamicos[0]["botao"]
        pos = (btn_abelha.rect.centerx, btn_abelha.rect.centery)
        self.jogo._processar_menu_minions(personagem, pos, (False, False, False), clicou=True)

        self.assertIn("Limite de summons atingido", self.jogo.mensagem_log)
        self.assertEqual(m1.hp, hp_anterior, "Minion continua sem cura indevida.")

    def test_botao_comandos_aparece_ao_lado_de_minions_para_invocador(self):
        """Verifica se o botão COMANDOS surge ao lado do botão MINIONS no menu de ataque do Invocador."""
        self.jogo.configurar_classe("Sobrevivente", "Invocador")
        self.jogo.gerar_botoes_ataque(personagem)
        nomes = [item["nome"] for item in self.jogo.botoes_habilidades_dinamicos]
        self.assertIn("MINIONS", nomes)
        self.assertIn("COMANDOS", nomes)

        idx_minions = nomes.index("MINIONS")
        idx_comandos = nomes.index("COMANDOS")
        self.assertEqual(idx_comandos, idx_minions + 1, "O botão COMANDOS deve estar logo ao lado de MINIONS")

    def test_transicao_para_submenu_comandos_e_voltar(self):
        """Testa clique em COMANDOS abrindo o menu de comandos e botão VOLTAR retornando para ataques."""
        self.jogo.configurar_classe("Sobrevivente", "Invocador")
        self.jogo.gerar_botoes_ataque(personagem)
        self.jogo.menu_acoes_estado = "ataques"

        # Localiza o botão COMANDOS
        btn_cmd = next(item["botao"] for item in self.jogo.botoes_habilidades_dinamicos if item["nome"] == "COMANDOS")
        pos = (btn_cmd.rect.centerx, btn_cmd.rect.centery)
        self.jogo._processar_menu_ataques(personagem, pos, (False, False, False), clicou=True)
        self.assertEqual(self.jogo.menu_acoes_estado, "comandos")

        # Verifica botões do menu de comandos
        self.assertEqual(self.jogo.btn_cmd_atingir.texto, "ATINGIR")
        self.assertEqual(self.jogo.btn_cmd_defender.texto, "DEFENDER")
        self.assertEqual(self.jogo.btn_cmd_descansar.texto, "DESCANSAR")
        self.assertEqual(self.jogo.btn_cmd_voltar.texto, "VOLTAR")

        # Clica em VOLTAR
        pos_voltar = (self.jogo.btn_cmd_voltar.rect.centerx, self.jogo.btn_cmd_voltar.rect.centery)
        self.jogo._processar_menu_comandos(personagem, pos_voltar, (False, False, False), clicou=True)
        self.assertEqual(self.jogo.menu_acoes_estado, "ataques")

    def test_comando_atingir_define_alvo_prioritario_summons(self):
        """Testa comando ATINGIR selecionando um inimigo alvo prioritário para os summons."""
        self.jogo.configurar_classe("Sobrevivente", "Invocador")
        minion = self.jogo.invocar_minion("Abelha Soldado", dono=personagem)
        self.assertIsNotNone(minion)

        # Configura inimigos no combate
        from Entidades.Inimigo import Inimigo
        inimigo1 = Inimigo(x=550, y=360, nome="Inimigo Alfa", vida_maxima=80, nome_imagem="Inimigo1.png")
        inimigo2 = Inimigo(x=650, y=360, nome="Inimigo Beta", vida_maxima=80, nome_imagem="Inimigo1.png")
        self.jogo.ordem_turnos = [personagem, minion, inimigo1, inimigo2]

        self.jogo.menu_acoes_estado = "comandos"
        pos_atingir = (self.jogo.btn_cmd_atingir.rect.centerx, self.jogo.btn_cmd_atingir.rect.centery)
        self.jogo._processar_menu_comandos(personagem, pos_atingir, (False, False, False), clicou=True)
        self.assertEqual(self.jogo.menu_acoes_estado, "selecionar_alvo_comando_atingir")

        # Jogador clica no Inimigo Beta na arena
        pos_alvo = (inimigo2.rect.centerx, inimigo2.rect.centery)
        self.jogo._processar_selecao_alvo_atingir(personagem, pos_alvo, (False, False, False), clicou=True, inimigos_vivos=[inimigo1, inimigo2])
        self.assertEqual(self.jogo.alvo_prioritario_minions, inimigo2)
        self.assertEqual(minion.alvo_prioritario, inimigo2)
        self.assertIn("focam em Inimigo Beta", self.jogo.mensagem_log)

        # Ao executar o turno do minion com golpe de alvo único, ele ataca o Inimigo Beta
        minion.escolher_ataque = lambda: "Ferrão Veloz"
        hp_beta_antes = inimigo2.hp
        hp_alfa_antes = inimigo1.hp
        self.jogo.executar_turno_minion(minion)
        self.assertLess(inimigo2.hp, hp_beta_antes, "Minion deve focar no alvo prioritário Beta!")
        self.assertEqual(inimigo1.hp, hp_alfa_antes, "Inimigo Alfa não deve ser atacado se Beta era o prioritário!")

    def test_comando_defender_faz_inimigos_focarem_minion_e_minion_nao_ataca(self):
        """Testa comando DEFENDER: jogador mira no minion, que entra em defesa, não ataca, e atrai ataques inimigos."""
        self.jogo.configurar_classe("Sobrevivente", "Invocador")
        minion = self.jogo.invocar_minion("Abelha Soldado", dono=personagem)
        self.assertIsNotNone(minion)

        from Entidades.Inimigo import Inimigo
        inimigo = Inimigo(x=550, y=360, nome="Inimigo Alfa", vida_maxima=80, nome_imagem="Inimigo1.png")
        self.jogo.ordem_turnos = [personagem, minion, inimigo]

        # Entra em comandos e clica em DEFENDER
        self.jogo.menu_acoes_estado = "comandos"
        pos_def = (self.jogo.btn_cmd_defender.rect.centerx, self.jogo.btn_cmd_defender.rect.centery)
        self.jogo._processar_menu_comandos(personagem, pos_def, (False, False, False), clicou=True)
        self.assertEqual(self.jogo.menu_acoes_estado, "selecionar_minion_comando_defender")

        # Clica no minion como alvo
        pos_minion = (minion.rect.centerx, minion.rect.centery)
        self.jogo._processar_selecao_minion_defender(personagem, pos_minion, (False, False, False), clicou=True)
        self.assertTrue(minion.defendendo)
        self.assertIn("defenderá a equipe", self.jogo.mensagem_log)

        # Minion defendendo NÃO ataca no seu turno
        hp_inimigo_antes = inimigo.hp
        msg = self.jogo.executar_turno_minion(minion)
        self.assertIn("está defendendo e não ataca neste turno", msg)
        self.assertEqual(inimigo.hp, hp_inimigo_antes, "Minion em defesa não deve causar dano!")

        # Turno do inimigo: inimigos focam 100% no minion defensor ao invés do jogador
        minions_defendendo = [m for m in self.jogo.obter_minions_vivos() if getattr(m, "defendendo", False)]
        self.assertIn(minion, minions_defendendo)

    def test_comando_descansar_cura_10_porcento_e_minion_dorme_sem_atacar(self):
        """Testa comando DESCANSAR: jogador mira no minion, cura 10% da vida máxima, e minion dorme sem atacar."""
        self.jogo.configurar_classe("Sobrevivente", "Invocador")
        minion = self.jogo.invocar_minion("Abelha Soldado", dono=personagem)
        self.assertIsNotNone(minion)
        minion.max_hp = 50
        minion.hp = 20  # Ferido

        from Entidades.Inimigo import Inimigo
        inimigo = Inimigo(x=550, y=360, nome="Inimigo Alfa", vida_maxima=80, nome_imagem="Inimigo1.png")
        self.jogo.ordem_turnos = [personagem, minion, inimigo]

        # Entra em comandos e clica em DESCANSAR
        self.jogo.menu_acoes_estado = "comandos"
        pos_desc = (self.jogo.btn_cmd_descansar.rect.centerx, self.jogo.btn_cmd_descansar.rect.centery)
        self.jogo._processar_menu_comandos(personagem, pos_desc, (False, False, False), clicou=True)
        self.assertEqual(self.jogo.menu_acoes_estado, "selecionar_minion_comando_descansar")

        # Clica no minion como alvo
        cura_esperada = max(1, int(minion.max_hp * 0.10))  # 10% de 50 = 5
        self.assertEqual(cura_esperada, 5)

        pos_minion = (minion.rect.centerx, minion.rect.centery)
        self.jogo._processar_selecao_minion_descansar(personagem, pos_minion, (False, False, False), clicou=True)
        self.assertEqual(minion.hp, 25, "Minion deve ser curado em 10% do HP máximo (20 + 5 = 25)!")
        self.assertTrue(minion.dormindo)
        self.assertIn("descansou (+5 HP)", self.jogo.mensagem_log)

        # Minion dormindo NÃO ataca no seu turno e acorda após o turno
        hp_inimigo_antes = inimigo.hp
        msg = self.jogo.executar_turno_minion(minion)
        self.assertIn("descansando/dormindo e não ataca neste turno", msg)
        self.assertEqual(inimigo.hp, hp_inimigo_antes, "Minion dormindo não ataca!")
        self.assertFalse(minion.dormindo, "Após o turno de descanso, o minion deve acordar!")


if __name__ == "__main__":
    unittest.main()
