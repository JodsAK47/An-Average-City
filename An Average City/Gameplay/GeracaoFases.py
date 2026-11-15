import json
import random
from Sistemas.Recursos import caminho_dados

TOTAL_FASES_NORMAIS = 9
TOTAL_PARTIDAS_JOGO = 10  # 9 fases normais + 1 combate contra o chefe (partida 10)


def carregar_limite_pontos_arvore(arquivo=None):
    """Retorna o custo total necessário para desbloquear uma trilha completa da árvore de habilidades."""
    caminho = arquivo or caminho_dados("arvores.json")
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            arvores = json.load(f)
        totais = [
            sum(int(hab.get("preco", 0)) for hab in trilhas)
            for trilhas in arvores.values()
            if isinstance(trilhas, list) and trilhas
        ]
        if totais:
            return max(1, max(totais))
    except Exception:
        pass
    return 180


LIMITE_PONTOS_JOGO = carregar_limite_pontos_arvore()


def calcular_pontos_fase_passada(partida_atual, total_fases=TOTAL_PARTIDAS_JOGO, limite_pontos=None):
    """Divide o limite total de pontos da árvore igualmente por fase passada (não por inimigo morto)."""
    limite = LIMITE_PONTOS_JOGO if limite_pontos is None else max(0, int(limite_pontos))
    total = max(1, int(total_fases or TOTAL_PARTIDAS_JOGO))
    partida = max(1, min(total, int(partida_atual or 1)))
    acumulado_atual = int(round((partida / total) * limite))
    acumulado_anterior = int(round(((partida - 1) / total) * limite))
    return max(0, acumulado_atual - acumulado_anterior)

MAPA_CATEGORIAS_INIMIGO = {
    "fraco": "pequeno",
    "fraca": "pequeno",
    "pequeno": "pequeno",
    "pequena": "pequeno",
    "menor": "pequeno",
    "comum": "pequeno",
    "medio": "medio",
    "médio": "medio",
    "media": "medio",
    "média": "medio",
    "grande": "grande",
    "elite": "grande",
    "chefe": "chefe",
    "boss": "chefe",
}


def normalizar_categoria_inimigo(tipo_ou_template):
    """Normaliza o tipo/tamanho de um inimigo para 'pequeno', 'medio', 'grande' ou 'chefe'."""
    if isinstance(tipo_ou_template, dict):
        valor = tipo_ou_template.get("tamanho") or tipo_ou_template.get("tipo", "medio")
    else:
        valor = tipo_ou_template
    chave = str(valor or "medio").strip().lower()
    return MAPA_CATEGORIAS_INIMIGO.get(chave, "medio")


def obter_regras_fase(fase_num, duas_pessoas=False):
    """Retorna (min_inimigos, max_inimigos, pesos_por_categoria) conforme a faixa da fase e modo."""
    fase = max(1, int(fase_num or 1))
    if duas_pessoas:
        if fase <= 3:
            return 2, 4, {"pequeno": 60, "medio": 40}
        if fase <= 6:
            return 3, 4, {"medio": 55, "pequeno": 25, "grande": 20}
        return 3, 4, {"medio": 60, "grande": 40}
    if fase <= 3:
        return 1, 4, {"pequeno": 70, "medio": 30}
    if fase <= 6:
        return 2, 4, {"medio": 55, "pequeno": 30, "grande": 15}
    return 2, 4, {"medio": 68, "grande": 32}

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

def carregar_inimigos():
    try:
        arquivo = caminho_dados("inimigos.json")
        with open(arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ Erro: arquivo inimigos.json não encontrado.")
        return []

BANCO_INIMIGOS = carregar_inimigos()

FATOR_BONUS_PROGRESSIVO_CATEGORIA = {
    "pequeno": 1.60,
    "medio": 1.20,
    "grande": 0.85,
    "chefe": 0.65,
}


def calcular_bonus_progressivo_inimigo(fase_num, categoria):
    """Calcula bônus progressivo de fase para inimigos; quanto mais fraco o porte, maior o bônus."""
    fase = max(1, int(fase_num or 1))
    cat = normalizar_categoria_inimigo(categoria)
    fator = FATOR_BONUS_PROGRESSIVO_CATEGORIA.get(cat, 1.0)
    if fase <= 1:
        return {"For": 0, "Agi": 0, "Int": 0, "Sor": 0, "mult_hp_extra": 0.0}

    soma_base = 0.0
    for f in range(2, fase + 1):
        passo = 1.0 if f <= 3 else (2.0 if f <= 6 else 3.0)
        soma_base += passo

    bonus_principal = max(1, int(round(soma_base * fator)))
    bonus_sorte = max(1, int(round(soma_base * fator * 0.5)))

    extra_por_fase = {"pequeno": 0.08, "medio": 0.05, "grande": 0.02, "chefe": 0.02}.get(cat, 0.04)
    mult_hp_extra = (fase - 1) * extra_por_fase

    return {
        "For": bonus_principal,
        "Agi": bonus_principal,
        "Int": bonus_principal,
        "Sor": bonus_sorte,
        "mult_hp_extra": mult_hp_extra,
    }


def _criar_inimigo_a_partir_template(
    template,
    x=0,
    y=0,
    multiplicador=1.0,
    multiplicador_hp=None,
    multiplicador_atributos=None,
    multiplicador_mp=None,
    fase_num=None,
):
    categoria = normalizar_categoria_inimigo(template)
    bonus_prog = calcular_bonus_progressivo_inimigo(fase_num, categoria) if fase_num is not None else None

    mult_hp = multiplicador if multiplicador_hp is None else multiplicador_hp
    if bonus_prog:
        mult_hp += bonus_prog["mult_hp_extra"]
    mult_attr = multiplicador if multiplicador_atributos is None else multiplicador_atributos
    mult_mp = multiplicador if multiplicador_mp is None else multiplicador_mp

    hp = max(12, int(template.get("max_hp", 20) * mult_hp + random.randint(0, 12)))
    xp = int(template.get("xp", 10) * multiplicador)

    atributos_base = template.get("atributos", {"For": 1, "Agi": 1, "Int": 1, "Sor": 1})
    atributos = {}
    for attr_nome, attr_val in atributos_base.items():
        passo = 2 if attr_nome == "Sor" else 3
        val = int(attr_val + (mult_attr - 1) * passo)
        if bonus_prog:
            val += bonus_prog.get(attr_nome, 0)
        atributos[attr_nome] = max(1, val)
    for padrao in ("For", "Agi", "Int", "Sor"):
        if padrao not in atributos:
            extra_p = bonus_prog.get(padrao, 0) if bonus_prog else 0
            atributos[padrao] = max(1, 1 + extra_p)

    max_mp_base = template.get("max_mp")
    max_mp_calc = int(max_mp_base * mult_mp) if max_mp_base is not None else None

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
    inimigos = [i for i in BANCO_INIMIGOS if not i.get("especial", False)]
    if verso:
        inimigos = [i for i in inimigos if i.get("verso") == verso]
    if not incluir_chefes:
        inimigos = [i for i in inimigos if i.get("tipo") != "chefe"]

    if not inimigos:
        inimigos = [i for i in BANCO_INIMIGOS if i.get("tipo") != "chefe" and not i.get("especial", False)]

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
        texto_dialogo = f"{descricao}\nTeste de {atributo} (Dificuldade {dificuldade})."

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

    quantidade_inimigos = None
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
        quantidade_inimigos = info_resultado.get("quantidade_inimigos", None)
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

        if not sucesso and info_resultado.get("roubar_equipamento", False):
            item_roubado_nome = None
            if hasattr(inv, "equipamentos_inventario") and inv.equipamentos_inventario:
                roubado = inv.equipamentos_inventario.pop(0)
                item_roubado_nome = getattr(roubado, "nome", "Equipamento")
            elif hasattr(inv, "todos_equipamentos_equipados") and inv.todos_equipamentos_equipados(incluir_todos=True):
                equips = inv.todos_equipamentos_equipados(incluir_todos=True)
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
        if sucesso:
            narrativa = getattr(evento, "descricao", "Você superou o desafio com habilidade.")
            efeitos = ["Avançou pelo caminho sem contratempos"]
            mensagem = f"⚑ 🎲 SUCESSO! Desafio '{nome}' superado!"
        else:
            for jog in lista_jogadores:
                jog.hp = max(1, jog.hp - 15)
            narrativa = "O contratempo no trajeto deixou sua equipe em alerta antes do combate."
            efeitos = ["Sofreu ferimentos leves (-15 HP)"]
            mensagem = f"⚑ 🎲 FALHA! Contratempo em '{nome}': -15 HP."

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
            "quantidade_inimigos": None,
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
            "quantidade_inimigos": None,
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
            "quantidade_inimigos": None,
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
            "quantidade_inimigos": None,
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
            "quantidade_inimigos": None,
            "multiplicador_forca": 1.0,
            "multiplicador_recompensa": 1.0,
        }

    evento_generico = obter_evento_por_nome(chave)
    return _executar_teste_evento_neutro(evento_generico, lista_jogadores, inv, rolagem_forcada=rolagem_forcada)

class GeradorFase:
    EVENTOS_NEUTROS = []

    def _carregar_eventos(self):
        if GeradorFase.EVENTOS_NEUTROS:
            return
        GeradorFase.EVENTOS_NEUTROS = [_criar_evento_de_dict(d) for d in carregar_eventos()]

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

    def _sortear_template_por_fase(self, templates, pesos_categorias):
        """Sorteia primeiro a categoria com os pesos da fase e depois um template da categoria."""
        por_categoria = {}
        for tmpl in templates:
            cat = normalizar_categoria_inimigo(tmpl)
            if cat in pesos_categorias:
                por_categoria.setdefault(cat, []).append(tmpl)

        if not por_categoria:
            globais = listar_inimigos_disponiveis(verso=None)
            for tmpl in globais:
                cat = normalizar_categoria_inimigo(tmpl)
                if cat in pesos_categorias:
                    por_categoria.setdefault(cat, []).append(tmpl)

        if por_categoria:
            categorias_disp = list(por_categoria.keys())
            pesos_disp = [pesos_categorias[c] for c in categorias_disp]
            cat_escolhida = random.choices(categorias_disp, weights=pesos_disp, k=1)[0]
            return random.choice(por_categoria[cat_escolhida])

        return random.choice(templates)

    def gerar_inimigos_aleatorios(self, fase_num=None, quantidade=None, verso=None, multiplicador_extra=1.0, duas_pessoas=False):
        fase = max(1, int((self.fase_num if fase_num is None else fase_num) or 1))
        min_qtd, max_qtd, pesos_categorias = obter_regras_fase(fase, duas_pessoas=duas_pessoas)
        if quantidade is None:
            quantidade = random.randint(min_qtd, max_qtd)
        else:
            quantidade = max(1, int(quantidade))

        templates = listar_inimigos_disponiveis(verso=verso)
        inimigos = []

        for _ in range(quantidade):
            template = self._sortear_template_por_fase(templates, pesos_categorias)
            multiplicador = (1 + (fase * 0.22)) * multiplicador_extra
            if duas_pessoas:
                inimigos.append(
                    _criar_inimigo_a_partir_template(
                        template,
                        multiplicador=multiplicador,
                        multiplicador_hp=multiplicador * 1.35,
                        multiplicador_atributos=multiplicador * 1.15,
                        fase_num=fase,
                    )
                )
            else:
                inimigos.append(_criar_inimigo_a_partir_template(template, multiplicador=multiplicador, fase_num=fase))

        return inimigos

    def gerar_chefe_verso(self, verso, duas_pessoas=False):
        chefes = [i for i in BANCO_INIMIGOS if i.get("verso") == verso and i.get("tipo") == "chefe" and not i.get("especial", False)]
        if not chefes:
            chefes = [i for i in BANCO_INIMIGOS if i.get("tipo") == "chefe" and not i.get("especial", False)]
        template = random.choice(chefes)
        if duas_pessoas:
            return _criar_inimigo_a_partir_template(
                template,
                multiplicador=1.5,
                multiplicador_hp=2.2,
                multiplicador_atributos=1.25 * 1.5,
                multiplicador_mp=1.8,
                fase_num=TOTAL_PARTIDAS_JOGO,
            )
        return _criar_inimigo_a_partir_template(template, multiplicador=1.5, fase_num=TOTAL_PARTIDAS_JOGO)
