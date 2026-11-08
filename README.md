# An Average City

Jogo de RPG em Python com Pygame, desenvolvido como projeto de estudo em lógica, orientação a objetos e desenvolvimento de jogos 2D.

Status atual: em desenvolvimento ativo, com mecânicas principais já implementadas e diversas features de sistema, progressão e interface funcionando.

## Visão geral

O projeto é um RPG por turnos com foco em combate, seleção de classes, árvore de habilidades, progresso de personagem, inventário, loja, conquistas e múltiplas telas de fluxo do jogo.

A estrutura atual do projeto está organizada em módulos e telas, com a lógica principal localizada em:

- [An Average City/Sistemas/MotorJogo.py](An%20Average%20City/Sistemas/MotorJogo.py)
- [An Average City/Telas](An%20Average%20City/Telas)
- [An Average City/Sistemas](An%20Average%20City/Sistemas)
- [An Average City/Entidades](An%20Average%20City/Entidades)
- [An Average City/Gameplay](An%20Average%20City/Gameplay)

## ✅ O que já foi implementado

### Sistema de jogo

- Menu principal com navegação entre telas
- Seleção de classes e seleção de verso
- Fluxo principal do jogo em estados
- Combate por turnos com ordem de ação dinâmica
- Sistema de esquiva interativa durante o ataque inimigo
- Fases e geração de inimigos por template
- Várias telas do jogo: menu, combate, descanso, loja, conquistas, configurações, game over e vitória

### Progressão e RPG

- Sistema de XP e níveis
- Pontos de atributo distribuídos ao subir de nível
- Atributos principais: Força, Agilidade, Constituição, Sabedoria, Intelecto e Sorte
- Árvore de habilidades por verso
- Talentos e ultimates desbloqueáveis
- Minions/invocações e elementos de suporte no combate

### Inventário e economia

- Inventário com consumíveis, materiais e equipamentos
- Equipamentos por categoria: arma, capacete, peitoral, calça, bota e amuleto
- Melhoria e polimento de itens
- Loja com compra e venda
- Loja segura e loja clandestina
- Materiais e recompensas relacionadas ao progresso

### Persistência

- Save em JSON
- Progresso de versos salvo
- Conquistas com notificações
- Configurações de vídeo e áudio salvas
- Reset do save e reinicialização do jogo

### Conteúdo extra

- Modo cooperativo de 2 jogadores
- Acesso restrito por Member Card
- Eventos neutros com testes de atributo e recompensas/penalidades
- Sistema de conquistas e feedback visual

## 🔄 O que está em andamento / em expansão

- Refinamento da árvore de talentos e balanceamento de habilidades
- Expansão de conteúdo de fases e inimigos
- Melhorias no sistema de loja e recompensas
- Ajustes no balanceamento de equipamentos e itens
- Polimento visual e de UX das telas
- Aprimoramento de efeitos sonoros e feedback de combate
- Expansão da narrativa e eventos do mundo

## ⚠️ O que ainda pode faltar

- Animações mais elaboradas para habilidades e ataques
- SFX mais completos e mais consistentes no combate
- Melhor acabamento visual em cenas, fundos e elementos de interface
- Mais conteúdo de exploração e mundo aberto/semiexploração
- Mais fases, bosses e variedade narrativa
- Refino final de balanceamento e acessibilidade

## 🧭 Status por área

### Concluído

- [x] Base de jogo e fluxo principal
- [x] Sistema de batalha por turnos
- [x] Progressão por nível e atributos
- [x] Inventário e equipamentos
- [x] Loja
- [x] Save e configurações
- [x] Conquistas
- [x] Versos/talentos/ultimates

### Em desenvolvimento

- [ ] Melhorias visuais e animações
- [ ] Sons e efeitos sonoros de ataques
- [ ] Expansão narrativa/mundo
- [ ] Balanceamento final
- [ ] Mais conteúdo de fases e inimigos

## ▶️ Como executar

### Pré-requisitos

- Python 3.10+ (Recomendado 3.13)
- Dependências listadas em requirements.txt

### Instalação de dependências

```bash
pip install -r requirements.txt
```

### Execução Padronizada (Direto da Raiz)

O jogo conta com um ponto de entrada padronizado (`main.py`) que configura caminhos e diretórios automaticamente:

```bash
python main.py
# ou
py main.py
```

### Execução dos Testes Automatizados

```bash
python main.py --test
# ou
py -m unittest discover tests
```

### Execução Alternativa (Subpasta)

Também é possível executar diretamente a partir da subpasta do jogo:

```bash
cd "An Average City"
python Sistemas/MotorJogo.py
```

## 📁 Estrutura principal

```text
An-Avarage-City/
├── README.md
├── README(Start).md
├── main.py
├── An Average City/
│   ├── Entidades/
│   ├── Gameplay/
│   ├── Sistemas/
│   │   ├── MotorJogo.py
│   ├── Telas/
│   ├── Saves/
│   ├── Dados/
│   └── Sprites/
└── OSTs/
```

## 📝 Observação

Este README foi atualizado para refletir o estado real do projeto conforme a implementação atual no código. O arquivo anterior estava desatualizado e descrevia uma versão mais antiga do jogo.

---

## 👥 Autores & Equipe do Projeto

Desenvolvido para a disciplina de **Programação Orientada a Objetos** no **IFRN Campus Caicó**:
- **Jusfran Medeiros do Nascimento** (*JodsAK47*)
- **Luis Felipe Torres Josué** (*Gold*)
- **Martiniano Dantas**

---

## 📄 Licença

Este projeto é desenvolvido para fins educacionais e estudo de desenvolvimento de jogos 2D, lógica de programação e arquitetura de software orientada a objetos.

Projeto desenvolvido como estudo de programação orientada a objetos, lógica de jogos e desenvolvimento com Python e Pygame.
