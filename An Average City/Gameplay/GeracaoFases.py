import json
import os
import random
from Sistemas.Recursos import caminho_dados

CAMINHO_DADOS = caminho_dados()

class EventoNeutro:
    def __init__(self, nome, tipo, descricao, atributo_chave="For", dificuldade=10, vitoria=None, derrota=None):
        self.nome = nome
        self.tipo = tipo
        self.descricao = descricao
        self.atributo_chave = atributo_chave
        self.dificuldade = int(dificuldade)
        self.vitoria = dict(vitoria) if isinstance(vitoria, dict) else {}
        self.derrota = dict(derrota) if isinstance(derrota, dict) else {}
        self.sucesso = self.vitoria
        self.falha = self.derrota

    def para_dict(self):
        dados = {
            "nome": self.nome,
            "tipo": self.tipo,
            "descricao": self.descricao,
            "atributo-chave": self.atributo_chave,
            "dificuldade": self.dificuldade,
        }
        if self.vitoria:
            dados["vitoria"] = self.vitoria
        if self.derrota:
            dados["derrota"] = self.derrota
        return dados

class FaseAleatoria:
    def __init__(self, id_fase, nome, descricao, evento, inimigos):
        self.id_fase = id_fase
        self.nome = nome
        self.descricao = descricao
        self.evento = evento
        self.inimigos = inimigos

    def para_dict(self):
        return {
            "id": self.id_fase,
            "nome": self.nome,
            "descricao": self.descricao,
            "evento": self.evento.para_dict(),
            "inimigos": self.inimigos,
        }

def carregar_inimigos():
    try:
        arquivo = caminho_dados("inimigos.json")
        with open(arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ Erro: arquivo inimigos.json não encontrado.")
        return []

BANCO_INIMIGOS = carregar_inimigos()

def _criar_inimigo_a_partir_template(template, x=0, y=0, multiplicador=1.0):
    hp = max(12, int(template.get("max_hp", 20) * multiplicador + random.randint(0, 12)))
    xp = int(template.get("xp", 10) * multiplicador)

    atributos_base = template.get("atributos", {"For": 1, "Agi": 1, "Int": 1, "Sor": 1})
    atributos = {}
    for attr_nome, attr_val in atributos_base.items():
        passo = 2 if attr_nome == "Sor" else 3
        atributos[attr_nome] = max(1, int(attr_val + (multiplicador - 1) * passo))
    for padrao in ("For", "Agi", "Int", "Sor"):
        if padrao not in atributos:
            atributos[padrao] = 1

    max_mp_base = template.get("max_mp")
    max_mp_calc = int(max_mp_base * multiplicador) if max_mp_base is not None else None

    from Entidades.Inimigo import Inimigo
    return Inimigo(
        x,
        y,
        hp,
        template.get("arquivo_imagem", "Maldição 4.png"),
        template.get("nome", "Inimigo"),
        list(template.get("ataques", ["Soco"])),
        xp,
        atributos,
        max_mp=max_mp_calc,
        tipo=template.get("tipo", "comum"),
        classe=template.get("classe")
    )

def listar_inimigos_disponiveis(verso=None, incluir_chefes=False):
    inimigos = BANCO_INIMIGOS
    if verso:
        inimigos = [i for i in inimigos if i.get("verso") == verso]
    if not incluir_chefes:
        inimigos = [i for i in inimigos if i.get("tipo") != "chefe"]

    if not inimigos:
        inimigos = [i for i in BANCO_INIMIGOS if i.get("tipo") != "chefe"]

    return inimigos

def carregar_eventos():
    try:
        arquivo = caminho_dados("eventos.json")
        with open(arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return [{"nome": "Caminho normal", "tipo": "neutro", "descricao": "Nada de especial acontece.", "atributo-chave": "For", "dificuldade": 10}]

BANCO_EVENTOS = carregar_eventos()

def _criar_evento_de_dict(dados):
    vitoria = dados.get("vitoria") or dados.get("sucesso") or {}
    derrota = dados.get("derrota") or dados.get("falha") or {}
    return EventoNeutro(
        dados.get("nome", ""),
        dados.get("tipo", "neutro"),
        dados.get("descricao", ""),
        dados.get("atributo-chave", dados.get("atributo_chave", "For")),
        dados.get("dificuldade", 10),
        vitoria=vitoria,
        derrota=derrota,
    )

def _conceder_xp_jogador(jogador, quantidade_xp):
    jogador.xp = getattr(jogador, "xp", 0) + int(quantidade_xp)
    novo_nivel = (jogador.xp // 100) + 1
    if novo_nivel > getattr(jogador, "nivel", 1):
        niveis_ganhos = novo_nivel - getattr(jogador, "nivel", 1)
        jogador.pontos_atributo = getattr(jogador, "pontos_atributo", 0) + (3 * niveis_ganhos)
        jogador.nivel = novo_nivel

def obter_evento_por_nome(identificador):
    if isinstance(identificador, EventoNeutro):
        return identificador
    if isinstance(identificador, dict):
        return _criar_evento_de_dict(identificador)

    texto_id = str(identificador or "")
    candidatos = [texto_id]
    if ":" in texto_id:
        candidatos.append(texto_id.split(":")[-1])
        candidatos.append(texto_id.split(":", 1)[1])

    for candidato in candidatos:
        for item in BANCO_EVENTOS:
            if item.get("nome") == candidato:
                return _criar_evento_de_dict(item)

    prefixo_id = texto_id.split(":", 1)[0]
    if prefixo_id.startswith("evento_neutro_"):
        sufixo = prefixo_id.split("_")[-1]
        if sufixo.isdigit() and BANCO_EVENTOS:
            indice = (int(sufixo) - 1) % len(BANCO_EVENTOS)
            return _criar_evento_de_dict(BANCO_EVENTOS[indice])

    if BANCO_EVENTOS:
        return _criar_evento_de_dict(random.choice(BANCO_EVENTOS))
    return EventoNeutro("Caminho normal", "neutro", "Nada de especial acontece.", "For", 10)

def obter_dialogo_evento(identificador_evento):
    evento = obter_evento_por_nome(identificador_evento)
    nome = evento.nome
    descricao = evento.descricao
    atributo = evento.atributo_chave
    dificuldade = evento.dificuldade

    resumo_vitoria = ""
    resumo_derrota = ""
    if hasattr(evento, "vitoria") and isinstance(evento.vitoria, dict):
        resumo_vitoria = evento.vitoria.get("resumo", "")
    if hasattr(evento, "derrota") and isinstance(evento.derrota, dict):
        resumo_derrota = evento.derrota.get("resumo", "")

    if resumo_vitoria and resumo_derrota:
        texto_dialogo = (
            f"{descricao}\n"
            f"Teste de {atributo} (Dificuldade {dificuldade}):\n"
            f"• Sucesso: {resumo_vitoria}\n"
            f"• Falha: {resumo_derrota}"
        )
    else:
        resumos_eventos = {
            "Um Estranho te convida para beber": (
                f"{descricao}\n"
                f"Teste de {atributo} (Dificuldade {dificuldade}):\n"
                "• Sucesso: +35 HP, +15 MP, +1 Sab e +1 Con.\n"
                "• Falha: Bebida adulterada (-20 HP e -5 MP)."
            ),
            "A porta do achados e perdidos ficou aberta": (
                f"{descricao}\n"
                f"Teste de {atributo} (Dificuldade {dificuldade}):\n"
                "• Sucesso: +1 For, +2 Sucatas, +Poção de Vida, +Bilhete e +Polidor de Itens.\n"
                "• Falha: Alarme dispara (-15 HP e 3 inimigos fortalecidos)."
            ),
            "Comprar com o perigo": (
                f"{descricao}\n"
                f"Teste de {atributo} (Dificuldade {dificuldade}):\n"
                "• Sucesso: Negócio seguro! Acesso à Loja do Perigo para comprar e vender equipamentos.\n"
                "• Falha: Você é ROUBADO! Perde equipamentos/materiais e sofre emboscada (-20 HP)."
            ),
            "Alguem na entrada do bar te chama": (
                f"{descricao}\n"
                f"Teste de {atributo} (Dificuldade {dificuldade}):\n"
                "• Sucesso: +1 Ponto de Atributo, +1 For, +20 HP, +40 XP e atalho (1 inimigo).\n"
                "• Falha: Emboscada nas sombras (-15 HP, -5 MP e 3 inimigos)."
            ),
            "Duelar até cair": (
                f"{descricao}\n"
                f"Teste de {atributo} (Dificuldade {dificuldade}):\n"
                "• Sucesso: +1 For, +20 HP e Duelo 1x1 valendo o DOBRO de XP e Pontos!\n"
                "• Falha: Golpe baixo (-20 HP e duelo 1x1 mais difícil sem bônus)."
            ),
            "Uma Pausa para comprar mantimentos": (
                f"{descricao}\n"
                "Pausa segura no balcão do Barista (Sem chance de falha):\n"
                "• Mantimentos garantidos (+35 HP, +15 MP, +Equipamento, +Poção, +Sucata e +1 For) e acesso livre à Loja!"
            ),
        }

        texto_dialogo = resumos_eventos.get(
            nome,
            f"{descricao}\nTeste de {atributo} (Dificuldade {dificuldade}).",
        )

    return [
        {
            "nome": nome,
            "texto": texto_dialogo,
            "opcoes": [
                {"texto": f"Tentar (1d20 + {atributo} >= {dificuldade})", "retorno": f"evento_acao:tentar:{nome}"},
                {"texto": "Ignorar e ir para a próxima batalha", "retorno": "cancelar_evento"},
            ],
        }
    ]

def _executar_teste_evento_neutro(evento, lista_jogadores, inv, rolagem_forcada=None):
    jogador_principal = lista_jogadores[0]
    atributo_chave = getattr(evento, "atributo_chave", "For")
    dificuldade = int(getattr(evento, "dificuldade", 10))
    dado = int(rolagem_forcada) if rolagem_forcada is not None else random.randint(1, 20)
    dado = max(1, min(20, dado))
    valor_atributo = int(getattr(jogador_principal, "atributos", {}).get(atributo_chave, 1))
    total = dado + valor_atributo
    sucesso = total >= dificuldade
    nome = evento.nome
    if nome == "Uma Pausa para comprar mantimentos":
        sucesso = True
    placar = f"[1d20({dado}) + {atributo_chave}({valor_atributo}) = {total} vs Dif.{dificuldade}]"

    quantidade_inimigos = 2
    multiplicador_forca = 1.0
    multiplicador_recompensa = 1.0

    narrativa = ""
    efeitos = []
    mensagem = ""

    info_resultado = {}
    if hasattr(evento, "vitoria") and hasattr(evento, "derrota"):
        info_resultado = evento.vitoria if sucesso else evento.derrota

    if info_resultado:
        narrativa = info_resultado.get("narrativa", "")
        efeitos = list(info_resultado.get("efeitos", []))
        mensagem = info_resultado.get("mensagem", "")
        quantidade_inimigos = info_resultado.get("quantidade_inimigos", 2)
        multiplicador_forca = float(info_resultado.get("multiplicador_forca", 1.0))
        multiplicador_recompensa = float(info_resultado.get("multiplicador_recompensa", 1.0))

        hp_delta = info_resultado.get("hp", 0)
        if hp_delta > 0:
            for jog in lista_jogadores:
                jog.hp = min(jog.max_hp, jog.hp + hp_delta)
        elif hp_delta < 0:
            for jog in lista_jogadores:
                jog.hp = max(1, jog.hp + hp_delta)

        mp_delta = info_resultado.get("mp", 0)
        if mp_delta > 0:
            for jog in lista_jogadores:
                jog.mp = min(jog.max_mp, jog.mp + mp_delta)
        elif mp_delta < 0:
            for jog in lista_jogadores:
                jog.mp = max(0, jog.mp + mp_delta)

        atributos_dict = info_resultado.get("atributos", {})
        for attr, bonus in atributos_dict.items():
            attr_nome = atributo_chave if attr in ("{atributo_chave}", "atributo_chave") else attr
            for jog in lista_jogadores:
                if hasattr(jog, "atributos"):
                    jog.atributos[attr_nome] = jog.atributos.get(attr_nome, 1) + bonus

        pontos_attr = info_resultado.get("pontos_atributo", 0)
        if pontos_attr > 0:
            for jog in lista_jogadores:
                jog.pontos_atributo = getattr(jog, "pontos_atributo", 0) + pontos_attr

        xp_ganho = info_resultado.get("xp", 0)
        if xp_ganho > 0:
            for jog in lista_jogadores:
                _conceder_xp_jogador(jog, xp_ganho)

        if info_resultado.get("melhorar_equipamento", False) and inv.equipamento_slot is not None:
            inv.equipamento_slot.melhorar()

        bilhetes_ganhos = info_resultado.get("bilhetes_dormitorio", 0)
        if bilhetes_ganhos > 0:
            inv.adicionar_bilhete_dormitorio(bilhetes_ganhos)

        polidores_ganhos = info_resultado.get("polidores_itens", info_resultado.get("polidor_itens", 0))
        if polidores_ganhos > 0:
            inv.adicionar_polidor_itens(polidores_ganhos)

        equipamentos_aleatorios = int(info_resultado.get("equipamentos_aleatorios", 0))
        for _ in range(equipamentos_aleatorios):
            if hasattr(inv, "gerar_equipamento_aleatorio") and hasattr(inv, "adicionar_equipamento"):
                novo_eq = inv.gerar_equipamento_aleatorio()
                inv.adicionar_equipamento(novo_eq, auto_equipar=True)

        equipamentos_lista = info_resultado.get("equipamentos", [])
        for eq_info in equipamentos_lista:
            if isinstance(eq_info, dict) and hasattr(inv, "adicionar_equipamento"):
                from Sistemas.Inventario import Equipamento
                novo_eq = Equipamento(
                    eq_info.get("nome", "Capacete de Ferro"),
                    eq_info.get("atributos_bonus", {"Con": 2}),
                    categoria=eq_info.get("categoria"),
                )
                inv.adicionar_equipamento(novo_eq, auto_equipar=True)

        materiais_lista = info_resultado.get("materiais", [])
        for mat in materiais_lista:
            if isinstance(mat, dict):
                for _ in range(mat.get("quantidade", 1)):
                    inv.adicionar_material(mat.get("nome", "Sucata"), mat.get("descricao", "Melhora equips."))
            elif isinstance(mat, str):
                inv.adicionar_material(mat, "Melhora equips.")

        perder_mat = info_resultado.get("perder_materiais", 0)
        if perder_mat > 0 and inv.materiais_totais() > 0:
            inv.consumir_materiais(perder_mat)

        if not sucesso and nome == "Comprar com o perigo":
            item_roubado_nome = None
            if hasattr(inv, "equipamentos_inventario") and inv.equipamentos_inventario:
                roubado = inv.equipamentos_inventario.pop(0)
                item_roubado_nome = getattr(roubado, "nome", "Equipamento")
            elif hasattr(inv, "todos_equipamentos_equipados") and inv.todos_equipamentos_equipados():
                equips = inv.todos_equipamentos_equipados()
                alvo_roubo = next((e for e in equips if getattr(e, "categoria", "") != "arma"), equips[0])
                inv.desequipar(alvo_roubo)
                if alvo_roubo in inv.equipamentos_inventario:
                    inv.equipamentos_inventario.remove(alvo_roubo)
                item_roubado_nome = getattr(alvo_roubo, "nome", "Equipamento")

            if item_roubado_nome:
                efeitos = [
                    f"O Perigo te roubou! Levou seu {item_roubado_nome}",
                    "Sofreu ferimentos na emboscada (-20 HP)",
                    "Inimigos chegam fortalecidos e em alerta"
                ]
                mensagem = f"⚑ 🎲 FALHA! O Perigo te roubou o item {item_roubado_nome} e -20 HP!"
            else:
                if inv.materiais_totais() > 0:
                    inv.consumir_materiais(min(2, inv.materiais_totais()))
                efeitos = [
                    "O Perigo te roubou! Levou seus materiais da mochila",
                    "Sofreu ferimentos na emboscada (-20 HP)",
                    "Inimigos chegam fortalecidos e em alerta"
                ]
                mensagem = "⚑ 🎲 FALHA! O Perigo te roubou suas sucatas e -20 HP!"


        consumiveis_lista = info_resultado.get("consumiveis", [])
        for con in consumiveis_lista:
            if isinstance(con, dict):
                for _ in range(con.get("quantidade", 1)):
                    inv.adicionar_consumivel(
                        con.get("nome", "Poção de Vida"),
                        con.get("descricao", "Restaura 30 HP"),
                        con.get("hp", 30),
                        con.get("mp", 0),
                    )
    else:
        if nome == "Um Estranho te convida para beber":
            if sucesso:
                for jog in lista_jogadores:
                    jog.hp = min(jog.max_hp, jog.hp + 35)
                    jog.mp = min(jog.max_mp, jog.mp + 15)
                    if hasattr(jog, "atributos"):
                        jog.atributos["Sab"] = jog.atributos.get("Sab", 1) + 1
                        jog.atributos["Con"] = jog.atributos.get("Con", 1) + 1
                narrativa = "Você aceitou a bebida com cautela e soube conduzir a conversa. O estranho ficou impressionado, compartilhou conselhos valiosos e uma bebida revigorante."
                efeitos = ["Recuperou 35 de Vida e 15 de Mana", "Ganhou +1 de Sabedoria", "Ganhou +1 de Constituição"]
                mensagem = "⚑ 🎲 SUCESSO! Bebida revigorante: +35 HP, +15 MP, +1 Sab e +1 Con!"
            else:
                for jog in lista_jogadores:
                    jog.hp = max(1, jog.hp - 20)
                    jog.mp = max(0, jog.mp - 5)
                narrativa = "A bebida era forte demais e estava adulterada. Sua cabeça começou a rodar e seu corpo fraquejou antes do confronto."
                efeitos = ["Sofreu efeito tóxico (-20 HP)", "Perdeu energia mágica (-5 MP)"]
                mensagem = "⚑ 🎲 FALHA! A bebida estava adulterada: -20 HP e -5 MP!"

        elif nome == "A porta do achados e perdidos ficou aberta":
            if sucesso:
                for jog in lista_jogadores:
                    if hasattr(jog, "atributos"):
                        jog.atributos["For"] = jog.atributos.get("For", 1) + 1
                inv.adicionar_material("Sucata", "Melhora equips.")
                inv.adicionar_material("Sucata", "Melhora equips.")
                inv.adicionar_consumivel("Poção de Vida", "Restaura 30 HP", 30, 0)
                inv.adicionar_bilhete_dormitorio(1)
                inv.adicionar_polidor_itens(1)
                narrativa = "Com passos silenciosos e precisos, você entrou na sala e vasculhou as gavetas sem fazer alarde, encontrando suprimentos valiosos deixados para trás."
                efeitos = ["Ganhou +1 de Força", "Encontrou 2 Sucatas de metal", "Encontrou uma Poção de Vida", "Encontrou um Bilhete do Dormitório", "Encontrou um Polidor de Itens"]
                mensagem = "⚑ 🎲 SUCESSO! Cofre aberto: +1 For, +2 Sucatas, +Poção, +Bilhete e +Polidor de Itens!"
            else:
                for jog in lista_jogadores:
                    jog.hp = max(1, jog.hp - 15)
                quantidade_inimigos = 3
                multiplicador_forca = 1.15
                narrativa = "Ao tentar alcançar os pertences no fundo, uma prateleira de ferro desabou com estrondo. O alarme disparou e guardas extras vieram correndo!"
                efeitos = ["Sofreu ferimentos na confusão (-15 HP)", "Três guardas em alerta surgiram para a batalha"]
                mensagem = "⚑ 🎲 FALHA! O alarme disparou: -15 HP e 3 guardas alertados!"

        elif nome == "Comprar com o perigo":
            if sucesso:
                for jog in lista_jogadores:
                    if hasattr(jog, "atributos"):
                        jog.atributos["For"] = jog.atributos.get("For", 1) + 1
                        jog.atributos["Sor"] = jog.atributos.get("Sor", 1) + 1
                if inv.equipamento_slot is not None:
                    inv.equipamento_slot.melhorar()
                if hasattr(inv, "gerar_equipamento_aleatorio") and hasattr(inv, "adicionar_equipamento"):
                    inv.adicionar_equipamento(inv.gerar_equipamento_aleatorio(), auto_equipar=True)
                inv.adicionar_consumivel("Poção de Vida", "Restaura 30 HP", 30, 0)
                narrativa = "Você manteve a guarda alta e não caiu nas conversas do negociante. Impressionado com sua firmeza, ele te vendeu peças raras e um tônico restaurador."
                efeitos = ["Ganhou +1 de Força e +1 de Sorte", "Equipamento aprimorado em 1 nível", "Adquiriu um novo Equipamento na loja clandestina", "Recebeu uma Poção de Vida"]
                mensagem = "⚑ 🎲 SUCESSO! Negócio fechado: Equipamento melhorado, +Equipamento, +Poção, +1 For e +1 Sor!"
            else:
                for jog in lista_jogadores:
                    jog.hp = max(1, jog.hp - 20)
                if inv.materiais_totais() > 0:
                    inv.consumir_materiais(1)
                multiplicador_forca = 1.15
                narrativa = "O vendedor era um trapaceiro. Enquanto mostrava mercadorias falsas, seus comparsas surrupiaram seus pertences e armaram uma emboscada violenta."
                efeitos = ["Sofreu ferimentos no golpe (-20 HP)", "Perdeu materiais da mochila", "Inimigos chegam fortalecidos e em emboscada"]
                mensagem = "⚑ 🎲 FALHA! O vendedor te enganou: -20 HP e emboscada!"

        elif nome == "Alguem na entrada do bar te chama":
            if sucesso:
                for jog in lista_jogadores:
                    jog.pontos_atributo = getattr(jog, "pontos_atributo", 0) + 1
                    jog.hp = min(jog.max_hp, jog.hp + 20)
                    if hasattr(jog, "atributos"):
                        jog.atributos["For"] = jog.atributos.get("For", 1) + 1
                    _conceder_xp_jogador(jog, 40)
                quantidade_inimigos = 1
                narrativa = "A figura oculta nas sombras era um antigo veterano de guerra. Ele reconheceu seu potencial, ensinou técnicas secretas e indicou um atalho limpo."
                efeitos = ["Ganhou 1 Ponto de Atributo", "Ganhou +1 de Força", "Recuperou 20 de Vida", "Recebeu 40 de Experiência", "Enfrentará apenas 1 adversário"]
                mensagem = "⚑ 🎲 SUCESSO! Treino secreto: +1 Ponto Atributo, +1 For, +20 HP, +40 XP e atalho!"
            else:
                for jog in lista_jogadores:
                    jog.hp = max(1, jog.hp - 15)
                    jog.mp = max(0, jog.mp - 5)
                quantidade_inimigos = 3
                narrativa = "Era uma cilada covarde. Assim que você se aproximou da porta escura, agressores saltaram dos cantos do beco te espancando de surpresa!"
                efeitos = ["Sofreu agressão de surpresa (-15 HP e -5 MP)", "Cercado por 3 adversários hostis"]
                mensagem = "⚑ 🎲 FALHA! Era uma armadilha no beco: -15 HP, -5 MP e 3 inimigos!"

        elif nome == "Duelar até cair":
            quantidade_inimigos = 1
            if sucesso:
                for jog in lista_jogadores:
                    jog.hp = min(jog.max_hp, jog.hp + 20)
                    if hasattr(jog, "atributos"):
                        jog.atributos["For"] = jog.atributos.get("For", 1) + 1
                multiplicador_forca = 1.2
                multiplicador_recompensa = 2.0
                narrativa = "Você aceitou o duelo individual com bravura. Com um golpe magistral, você derrubou a guarda do rival, garantindo o dobro de recompensas pelo combate!"
                efeitos = ["Ganhou +1 de Força", "Recuperou 20 de Vida com o ímpeto da vitória", "Recompensas da batalha multiplicadas em dobro"]
                mensagem = "⚑ 🎲 SUCESSO! Duelo 1x1 com vantagem: +1 For, +20 HP e Recompensa em DOBRO!"
            else:
                for jog in lista_jogadores:
                    jog.hp = max(1, jog.hp - 20)
                multiplicador_forca = 1.35
                multiplicador_recompensa = 1.0
                narrativa = "O adversário não possuía qualquer honra. Antes que as regras fossem ditas, ele desferiu um golpe traiçoeiro na sua costela e avançou furioso!"
                efeitos = ["Sofreu um ataque covarde (-20 HP)", "Adversário parte para cima com ferocidade ampliada"]
                mensagem = "⚑ 🎲 FALHA! Golpe baixo antes do duelo: -20 HP e oponente feroz sem bônus!"

        else:
            if sucesso:
                for jog in lista_jogadores:
                    jog.hp = min(jog.max_hp, jog.hp + 35)
                    jog.mp = min(jog.max_mp, jog.mp + 15)
                    if hasattr(jog, "atributos"):
                        jog.atributos[atributo_chave] = jog.atributos.get(atributo_chave, 1) + 1
                inv.adicionar_consumivel("Poção de Vida", "Restaura 30 HP", 30, 0)
                inv.adicionar_material("Sucata", "Melhora equips.")
                if hasattr(inv, "gerar_equipamento_aleatorio") and hasattr(inv, "adicionar_equipamento"):
                    inv.adicionar_equipamento(inv.gerar_equipamento_aleatorio(), auto_equipar=True)
                narrativa = "O comerciante ofereceu provisões frescas e energéticas. Você se alimentou bem, recuperou o fôlego e reforçou sua preparação física para o próximo embate."
                efeitos = ["Recuperou 35 de Vida e 15 de Mana", f"Ganhou +1 de {atributo_chave}", "Adquiriu um Equipamento com o comerciante", "Recebeu uma Poção de Vida", "Recebeu Sucata para melhorias"]
                mensagem = f"⚑ 🎲 SUCESSO! Mantimentos obtidos: +35 HP, +15 MP, +Equipamento, +Poção, +Sucata e +1 {atributo_chave}!"
            else:
                for jog in lista_jogadores:
                    jog.hp = max(1, jog.hp - 15)
                narrativa = "Os suprimentos estavam estragados e a comida exalava cheiro azedo. Uma pontada forte no estômago te deixou debilitado antes da batalha."
                efeitos = ["Intoxicação alimentar (-15 HP)", "Sem bônus adicionais de mantimentos"]
                mensagem = "⚑ 🎲 FALHA! Mantimentos estragados: -15 HP antes da batalha!"

    return {
        "evento": evento,
        "nome_evento": nome,
        "sucesso": sucesso,
        "titulo_resultado": "SUCESSO!" if sucesso else "FALHA!",
        "narrativa": narrativa,
        "efeitos": efeitos,
        "rolagem_dado": dado,
        "valor_atributo": valor_atributo,
        "total_teste": total,
        "dificuldade": dificuldade,
        "atributo_chave": atributo_chave,
        "mensagem": mensagem,
        "quantidade_inimigos": quantidade_inimigos,
        "multiplicador_forca": multiplicador_forca,
        "multiplicador_recompensa": multiplicador_recompensa,
    }

def executar_efeito_evento(acao_ou_nome, jogo_tela=None, jogadores=None, inventario=None, rolagem_forcada=None):
    from Entidades.Personagem import personagem
    from Sistemas.Inventario import inventario_global

    inv = inventario if inventario is not None else inventario_global
    if jogadores is not None:
        lista_jogadores = list(jogadores)
    else:
        lista_jogadores = [personagem]
        if jogo_tela is not None and getattr(jogo_tela, "duas_pessoas", False) and getattr(jogo_tela, "personagem2", None) is not None:
            lista_jogadores.append(jogo_tela.personagem2)

    chave = str(acao_ou_nome or "")
    if chave.startswith("evento_acao:"):
        chave = chave.split(":", 1)[1]

    if chave.startswith("tentar:") or chave.startswith("evento_neutro_"):
        evento_alvo = obter_evento_por_nome(chave)
        return _executar_teste_evento_neutro(evento_alvo, lista_jogadores, inv, rolagem_forcada=rolagem_forcada)

    nomes_banco = {ev.get("nome") for ev in BANCO_EVENTOS}
    if chave in nomes_banco:
        evento_alvo = obter_evento_por_nome(chave)
        return _executar_teste_evento_neutro(evento_alvo, lista_jogadores, inv, rolagem_forcada=rolagem_forcada)

    if chave == "estranho_beber":
        return _executar_teste_evento_neutro(obter_evento_por_nome("Um Estranho te convida para beber"), lista_jogadores, inv, rolagem_forcada=rolagem_forcada or 20)

    if chave == "estranho_conversar":
        for jog in lista_jogadores:
            jog.mp = min(jog.max_mp, jog.mp + 15)
            _conceder_xp_jogador(jog, 40)
        return {
            "evento": obter_evento_por_nome("Um Estranho te convida para beber"),
            "sucesso": True,
            "mensagem": "⚑ 🍺 Conversa no bar: +15 MP e +40 XP adquiridos!",
            "quantidade_inimigos": 2,
            "multiplicador_forca": 1.0,
            "multiplicador_recompensa": 1.0,
        }

    if chave == "achados_invadir":
        return _executar_teste_evento_neutro(obter_evento_por_nome("A porta do achados e perdidos ficou aberta"), lista_jogadores, inv, rolagem_forcada=rolagem_forcada or 20)

    if chave == "achados_entrada":
        inv.adicionar_material("Sucata", "Melhora equips.")
        inv.adicionar_consumivel("Poção de Vida", "Restaura 30 HP", 30, 0)
        return {
            "evento": obter_evento_por_nome("A porta do achados e perdidos ficou aberta"),
            "sucesso": True,
            "mensagem": "⚑ 📦 Achados e perdidos: você coletou +1 Sucata e +1 Poção de Vida!",
            "quantidade_inimigos": 2,
            "multiplicador_forca": 1.0,
            "multiplicador_recompensa": 1.0,
        }

    if chave == "perigo_sangue":
        return _executar_teste_evento_neutro(obter_evento_por_nome("Comprar com o perigo"), lista_jogadores, inv, rolagem_forcada=rolagem_forcada or 20)

    if chave == "perigo_contrabando":
        if jogo_tela is not None and getattr(jogo_tela, "pontos_jogo", 0) >= 30:
            jogo_tela.pontos_jogo -= 30
        inv.adicionar_material("Sucata", "Melhora equips.")
        inv.adicionar_material("Sucata", "Melhora equips.")
        inv.adicionar_consumivel("Poção de Mana", "Restaura 10 MP", 0, 10)
        return {
            "evento": obter_evento_por_nome("Comprar com o perigo"),
            "sucesso": True,
            "mensagem": "⚑ 🕵️ Comprar com o perigo: +2 Sucatas e +1 Poção de Mana adquiridas!",
            "quantidade_inimigos": 2,
            "multiplicador_forca": 1.0,
            "multiplicador_recompensa": 1.0,
        }

    if chave == "bar_aproximar":
        return _executar_teste_evento_neutro(obter_evento_por_nome("Alguem na entrada do bar te chama"), lista_jogadores, inv, rolagem_forcada=rolagem_forcada or 20)

    if chave == "bar_distancia":
        inv.adicionar_bilhete_dormitorio(1)
        inv.adicionar_consumivel("Poção de Mana", "Restaura 10 MP", 0, 10)
        return {
            "evento": obter_evento_por_nome("Alguem na entrada do bar te chama"),
            "sucesso": True,
            "mensagem": "⚑ 👤 Sombra no bar: atalho revelou +1 Bilhete Dormitório, +1 Poção de Mana e rota limpa!",
            "quantidade_inimigos": 1,
            "multiplicador_forca": 1.0,
            "multiplicador_recompensa": 1.0,
        }

    if chave == "duelar_aceitar":
        return _executar_teste_evento_neutro(obter_evento_por_nome("Duelar até cair"), lista_jogadores, inv, rolagem_forcada=rolagem_forcada or 20)

    if chave == "mantimentos_refeicao":
        return _executar_teste_evento_neutro(obter_evento_por_nome("Uma Pausa para comprar mantimentos"), lista_jogadores, inv, rolagem_forcada=rolagem_forcada or 20)

    if chave == "mantimentos_pocoes":
        inv.adicionar_consumivel("Poção de Vida", "Restaura 30 HP", 30, 0)
        inv.adicionar_consumivel("Poção de Mana", "Restaura 10 MP", 0, 10)
        inv.adicionar_consumivel("Poção de Mana", "Restaura 10 MP", 0, 10)
        return {
            "evento": obter_evento_por_nome("Uma Pausa para comprar mantimentos"),
            "sucesso": True,
            "mensagem": "⚑ ☕ Pausa para mantimentos: +1 Poção de Vida e +2 Poções de Mana no inventário!",
            "quantidade_inimigos": 2,
            "multiplicador_forca": 1.0,
            "multiplicador_recompensa": 1.0,
        }

    if chave == "mantimentos_acampamento":
        inv.adicionar_material("Sucata", "Melhora equips.")
        inv.adicionar_material("Sucata", "Melhora equips.")
        inv.adicionar_bilhete_dormitorio(1)
        return {
            "evento": obter_evento_por_nome("Uma Pausa para comprar mantimentos"),
            "sucesso": True,
            "mensagem": "⚑ ☕ Pausa para mantimentos: +2 Sucatas e +1 Bilhete do Dormitório!",
            "quantidade_inimigos": 2,
            "multiplicador_forca": 1.0,
            "multiplicador_recompensa": 1.0,
        }

    evento_generico = obter_evento_por_nome(chave)
    return _executar_teste_evento_neutro(evento_generico, lista_jogadores, inv, rolagem_forcada=rolagem_forcada)

class GeradorFase:
    EVENTOS_NEUTROS = []

    def _carregar_eventos(self):
        if self.EVENTOS_NEUTROS:
            return
        self.EVENTOS_NEUTROS = [_criar_evento_de_dict(d) for d in carregar_eventos()]

    def __init__(self, fase_num=1):
        self.fase_num = fase_num
        self._carregar_eventos()

    def gerar_evento_neutro(self):
        evento = random.choice(self.EVENTOS_NEUTROS)
        return EventoNeutro(
            evento.nome,
            evento.tipo,
            evento.descricao,
            evento.atributo_chave,
            evento.dificuldade,
            vitoria=evento.vitoria,
            derrota=evento.derrota,
        )

    def gerar_inimigos_aleatorios(self, fase_num=None, quantidade=None, verso=None, multiplicador_extra=1.0):
        fase = self.fase_num if fase_num is None else fase_num
        if quantidade is None:
            quantidade = max(1, min(4, 1 + (fase // 2)))

        templates = listar_inimigos_disponiveis(verso=verso)
        inimigos = []

        for _ in range(quantidade):
            template = random.choice(templates)
            multiplicador = (1 + (fase * 0.22)) * multiplicador_extra
            inimigos.append(_criar_inimigo_a_partir_template(template, multiplicador=multiplicador))

        return inimigos

    def gerar_chefe_verso(self, verso):
        chefes = [i for i in BANCO_INIMIGOS if i.get("verso") == verso and i.get("tipo") == "chefe"]
        if not chefes:
            chefes = [i for i in BANCO_INIMIGOS if i.get("tipo") == "chefe"]
        template = random.choice(chefes)
        return _criar_inimigo_a_partir_template(template, multiplicador=1.5)

    def gerar_fase_aleatoria(self, fase_num=None, verso=None):
        fase = self.fase_num if fase_num is None else fase_num
        evento = self.gerar_evento_neutro()
        quantidade = 1 if evento.nome == "Duelar até cair" else max(1, min(4, 1 + (fase // 2)))
        mult_extra = 1.3 if evento.nome == "Duelar até cair" else 1.0
        inimigos = self.gerar_inimigos_aleatorios(fase, quantidade=quantidade, verso=verso, multiplicador_extra=mult_extra)
        return FaseAleatoria(
            f"fase_aleatoria_{fase}",
            f"Fase Aleatória {fase}",
            "Uma rota improvisada com inimigos e eventos inesperados.",
            evento,
            inimigos,
        )
