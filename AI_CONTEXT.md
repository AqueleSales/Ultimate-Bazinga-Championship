# AI_CONTEXT.md — Ultimate Bazinga Championship

> Documento de contexto e regras de trabalho para ChatGPT, Gemini, Copilot e outras IAs que contribuam com este repositório.
> Atualizado em 2026-11-10 com base nos arquivos existentes na branch `main`.

## 1. Missão do projeto

O **Ultimate Bazinga Championship (UBC)** é o módulo competitivo do ecossistema Bazinga Hub. A plataforma deve permitir organizar e acompanhar campeonatos individuais e por equipes, administrar fases e partidas, publicar resultados oficiais e preservar histórico, estatísticas e rankings.

A experiência deve transmitir energia de competição, espetáculo e identidade gamer. A interface não deve parecer um painel administrativo genérico.

## 2. Estado real do repositório

**Importante: diferencie sempre código existente, intenção documentada e funcionalidade futura.** O README descreve objetivos planejados; isso não significa que estejam implementados.

### Implementado na base atual

- Aplicação Flask com Application Factory em `bazinga.create_app`.
- Extensões SQLAlchemy, Flask-Migrate e Flask-SocketIO inicializadas separadamente.
- Configuração por variáveis de ambiente, carregadas com python-dotenv.
- Fallback local para SQLite e suporte configurável a PostgreSQL/Neon.
- Modelos SQLAlchemy para usuários, contas OAuth, participantes, torneios, equipes, inscrições, fases, partidas, slots e resultados.
- Blueprint HTTP principal com rota `/` e health check `/health`.
- Templates Jinja2 `base.html` e `championship.html`.
- CSS inicial responsivo com variáveis, Grid/Flexbox e suporte a `prefers-reduced-motion`.
- Fixtures e testes iniciais com Pytest e SQLite em memória.

### Ainda não implementado (não presumir que exista)

- Fluxos de login OAuth Google ou Discord. Authlib está nas dependências, mas não há fluxo de autenticação implementado nos arquivos analisados.
- Criação/edição/publicação de campeonatos por interface ou API.
- Inscrições, geração de chaveamento e progressão automática entre fases.
- Serviços de regras de torneio, rankings e estatísticas.
- Eventos Socket.IO de partidas/placares. A extensão é inicializada, mas não foram encontrados handlers de eventos.
- Dashboard real, páginas de perfil, feed, chat ou player de transmissão.
- Intro cinematográfica, carta, selo, fogo ou transição de entrada.

Não apresente itens planejados como prontos em textos, telas, documentação ou respostas.

## 3. Stack e arquitetura

### Backend

- Python
- Flask 3.1.0
- Flask-SQLAlchemy 3.1.1 / SQLAlchemy
- Flask-Migrate 4.1.0
- Flask-SocketIO 5.3.6
- psycopg2-binary
- Authlib (dependência disponível; integração OAuth ainda pendente)
- python-dotenv

### Frontend

- HTML5
- Jinja2
- CSS3 puro
- JavaScript Vanilla
- Fetch API quando houver necessidade de chamadas HTTP
- Socket.IO Client quando a camada de eventos for implementada

Não introduza React, Vue, Angular, Tailwind, Bootstrap ou bibliotecas de animação sem uma decisão explícita do responsável pelo projeto.

### Estrutura conhecida

```text
.
├── app.py
├── config.py
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .gitignore
├── bazinga/
│   ├── __init__.py
│   ├── extensions.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── participant.py
│   │   ├── tournament.py
│   │   └── match.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── main.py
│   ├── services/
│   │   └── __init__.py
│   ├── sockets/
│   │   └── __init__.py
│   ├── templates/
│   │   ├── base.html
│   │   └── championship.html
│   └── static/
│       └── css/
│           └── style.css
└── tests/
    ├── conftest.py
    └── test_health.py
```

Pastas de services e sockets possuem atualmente apenas arquivos de inicialização/documentação; não inventar módulos dentro delas como se já existissem.

## 4. Responsabilidade dos arquivos existentes

- `app.py`: importa `create_app`, obtém a aplicação e executa `socketio.run` em desenvolvimento.
- `config.py`: carrega .env e define SECRET_KEY, DEBUG, SQLALCHEMY_DATABASE_URI, opções do engine e fila opcional do Socket.IO.
- `bazinga/__init__.py`: Application Factory; valida SECRET_KEY, inicializa extensões, importa modelos e registra o blueprint principal.
- `bazinga/extensions.py`: instâncias compartilhadas de `db`, `migrate` e `socketio`.
- `bazinga/models/__init__.py`: importa e exporta os modelos para registro no SQLAlchemy.
- `bazinga/models/*.py`: entidades e relacionamentos do domínio (detalhes abaixo).
- `bazinga/routes/main.py`: blueprint `main`, rota da homepage e health check.
- `bazinga/templates/base.html`: estrutura global, header, main, footer e blocos Jinja.
- `bazinga/templates/championship.html`: homepage atual, estende base.html.
- `bazinga/static/css/style.css`: design inicial e responsividade.
- `tests/conftest.py`: app fixture e client fixture usando SQLite em memória.
- `tests/test_health.py`: health check, homepage e teste de participante inscrito em múltiplos torneios.

## 5. Modelo de domínio atual

### Usuário e identidade

- `User`: nome, email opcional, avatar, estado ativo e data de criação.
- `OAuthAccount`: vínculo de provedor externo com usuário; restrição única para `(provider, provider_user_id)`.
- Um usuário pode possuir várias contas OAuth.

### Participante

- `Participant`: identidade competitiva independente, com nome de exibição e avatar.
- `linked_user_id` é opcional: participante pode existir sem conta de usuário.
- Um participante pode ter inscrições em vários torneios.

### Torneio e organização

- `Tournament`: título, slug único, descrição, status, modalidade individual/equipe, visibilidade, organizador e datas.
- `TournamentAdmin`: vínculo de usuários administradores com função por torneio; unicidade por torneio/usuário.
- `TournamentStage`: fase ordenada dentro do torneio, com tipo, status, configurações JSON e datas.
- `Team`: equipe pertencente a um torneio, com nome, tag e seed.
- `TournamentRegistration`: inscrição de participante em torneio, opcionalmente associada a equipe; unicidade por torneio/participante.

### Partidas e resultados

- `Match`: pertence a uma fase; possui número, rodada, grupo, status, melhor-de, agenda e timestamps.
- `MatchSlot`: posição/competidor de uma partida; pode referenciar participante ou equipe, placar, seed e partida de origem.
- Há uma constraint garantindo que um slot não associe participante e equipe simultaneamente.
- `MatchResult`: resultado oficial 1:1 com partida, slot vencedor, usuário que registrou, placares finais JSON, notas e data de finalização.

**Cuidados de domínio:** respeitar as constraints e foreign keys existentes. Antes de alterar modelos, verificar impactos em relacionamentos, migrações e testes. Não presumir que toda regra de torneio já está validada apenas por existir uma coluna.

## 6. Direção visual e experiência

### Conceito principal

Criar uma identidade cinematográfica de campeonato, inspirada na sensação de revelação e impacto das apresentações de Super Smash Bros. Ultimate (2018), sem copiar assets, logos, personagens, efeitos proprietários ou composições exatas da Nintendo.

A sensação desejada:
- suspense antes da revelação;
- objeto/cartão de campeonato atravessando o escuro;
- desaceleração dramática no centro;
- selo/símbolo Bazinga recebendo um impacto visual;
- explosão de luz, partículas, fumaça e fogo estilizado;
- transição de chamas que revela a homepage/dashboard.

A intro deve ser uma criação original do UBC. O símbolo, lettering e arte do campeonato devem ser próprios.

### Fluxo de entrada pretendido

1. Tela escura com identidade sonora/visual opcional.
2. Cartão/convite entra em movimento e desacelera até o centro.
3. O selo Bazinga é destacado; a interação de entrada ou continuação aciona a revelação.
4. Explosão visual com flash controlado, partículas, faíscas e fogo.
5. Fire-wipe revela o conteúdo principal.
6. O usuário chega à aplicação e consegue navegar normalmente.

Não obrigar login enquanto o fluxo OAuth não existir. Não apresentar botões de login Google/Discord que não funcionem. A intro não deve bloquear conteúdo essencial nem reaparecer desnecessariamente em cada navegação. Definir claramente o comportamento de replay e persistência da intro.

### Regras de acessibilidade e performance da intro

- Disponibilizar ação visível de pular/reduzir a intro.
- Respeitar `prefers-reduced-motion: reduce`; oferecer uma entrada curta ou estática.
- Garantir navegação por teclado, foco visível e rótulos acessíveis.
- Evitar flashes intensos/repetidos e efeitos que possam causar desconforto.
- Não deixar áudio tocar automaticamente.
- Não usar vídeos enormes ou bibliotecas pesadas sem justificativa.
- Preferir CSS transforms/opacity para animações; evitar animar propriedades que provoquem layout contínuo.
- Limitar partículas e limpar timers/listeners/elementos temporários.
- Testar mobile, telas pequenas e dispositivos de menor desempenho.
- A intro deve falhar de forma segura: se JS/efeitos não carregarem, a homepage continua utilizável.

### Linguagem visual do site

O usuário quer uma estética gamer dramática e energética, não um dashboard corporativo genérico. O conteúdo interno deve equilibrar espetáculo com legibilidade: placares, partidas, confrontos, ranking e perfis precisam ser fáceis de consultar.

A paleta atual do CSS é roxo escuro:
- background `#121117`
- surface `#1b1923`
- surface raised `#24212f`
- border `#34303f`
- text `#f4f1fa`
- muted `#aaa4b8`
- primary `#9b70e8`
- primary strong `#8051d3`
- success `#55c58b`

A paleta Discord mencionada em brainstorm anterior não é requisito fixo. Não substituir automaticamente a identidade roxa atual por Discord Dark Mode. A decisão visual deve priorizar o conceito Smash-like original e manter consistência.

## 7. Funcionalidades de produto previstas

As metas descritas no README incluem:
- torneios individuais e por equipes;
- mata-mata simples/duplo;
- fase de grupos, pontos corridos e formatos híbridos;
- fases configuráveis;
- agenda e gerenciamento de partidas;
- placar em tempo real;
- resultados oficiais;
- perfis competitivos persistentes;
- histórico de participações e partidas;
- estatísticas individuais e por equipe;
- rankings e Hall da Fama;
- organizadores e administradores com permissões;
- inscrições;
- incorporação de transmissão externa e painel da partida.

Essas são metas, não funcionalidades concluídas. Implementar incrementalmente e documentar o que de fato ficar pronto.

## 8. Segurança e integridade

- Nunca inserir secrets, tokens, senhas ou credenciais em código, commits, logs ou documentação.
- Nunca ler, copiar ou publicar valores reais de .env.
- Usar `.env.example` apenas com placeholders.
- Validar no servidor toda operação que altera inscrições, permissões, partidas ou placares oficiais.
- O cliente Socket.IO nunca é autoridade para declarar vencedor ou resultado.
- Verificar identidade e autorização em endpoints e eventos.
- Usar transações para operações que alterem múltiplas entidades relacionadas.
- Não confiar em IDs, scores, roles ou status enviados pelo navegador sem validação.
- Evitar expor dados pessoais de usuários/participantes desnecessariamente.
- Não desabilitar CSRF ou controles de segurança para facilitar a interface.

## 9. Convenções de implementação

- Preservar Flask + Jinja2 + CSS puro + JavaScript Vanilla.
- Seguir a Application Factory; não criar uma segunda instância global de Flask em módulos internos.
- Importar extensões de `bazinga.extensions`.
- Manter modelos em `bazinga/models/`, rotas em blueprints, regras de negócio em `bazinga/services/` e handlers em `bazinga/sockets/`.
- Templates devem estender `base.html` quando fizer sentido e usar `url_for('static', filename=...)` para assets.
- Usar nomes claros e consistentes; evitar lógica de negócio complexa dentro de templates.
- Preferir CSS organizado com custom properties e componentes reutilizáveis.
- Isolar JavaScript por responsabilidade; não colocar scripts enormes inline em templates.
- Evitar dependências novas quando a plataforma nativa resolve bem.
- Manter responsividade, semântica HTML e acessibilidade como requisitos, não como acabamento opcional.
- Não quebrar rotas, nomes de endpoints, seletores ou contratos existentes sem atualizar todos os consumidores e testes.

## 10. Testes e execução

Instalação de desenvolvimento:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\\Scripts\\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements-dev.txt
```

Criar `.env` com base em `.env.example` e definir pelo menos `SECRET_KEY`. Não commitar `.env`.

Executar:

```bash
python app.py
```

Testes:

```bash
python -m pytest
```

Migrações (somente quando necessário e depois de revisar os modelos):

```bash
flask --app app db init
flask --app app db migrate -m "Describe schema change"
flask --app app db upgrade
```

Não executar `db init` novamente em ambiente que já possui migrations. Revisar os arquivos gerados antes de aplicar/commitar.

## 11. Protocolo obrigatório para IAs

Antes de alterar código:

1. Ler este arquivo e o README.
2. Inspecionar os arquivos diretamente relacionados à tarefa; não confiar apenas neste resumo.
3. Identificar o comportamento atual, dependências e pontos de integração.
4. Separar claramente fatos do código, hipóteses e propostas.
5. Apresentar um plano curto quando a alteração afetar arquitetura, banco, autenticação ou várias páginas.
6. Fazer mudanças pequenas e coerentes, preservando funcionalidades existentes.
7. Atualizar/adicionar testes para comportamento novo ou alterado.
8. Executar os testes disponíveis e informar exatamente o que foi executado e o resultado.
9. Atualizar este documento quando arquitetura, comandos, decisões ou estado real do projeto mudarem.

### Ao finalizar uma tarefa, informar

- arquivos criados/alterados;
- resumo do comportamento implementado;
- decisões técnicas e dependências novas;
- testes executados e resultado;
- limitações conhecidas e próximos passos;
- se houve alteração de banco, indicar migração necessária.

### Não fazer

- Não inventar endpoints, eventos, modelos, colunas ou telas que não existem.
- Não marcar funcionalidades planejadas como implementadas.
- Não substituir arquivos inteiros sem necessidade.
- Não alterar banco de dados sem avaliar migrações e compatibilidade.
- Não remover testes para fazer a suíte passar.
- Não introduzir credenciais ou dados reais.
- Não copiar assets protegidos de Super Smash Bros.; criar arte original inspirada apenas na sensação de espetáculo.
- Não deixar controles visuais sem ação real.

## 12. Próxima sequência recomendada

1. Consolidar a identidade visual e o fluxo da intro cinematográfica.
2. Implementar a intro como camada independente e integrada à homepage atual.
3. Criar testes/checagens para acessibilidade, fallback e navegação da intro.
4. Evoluir o dashboard com dados reais do backend, sem conteúdo falso apresentado como informação oficial.
5. Implementar autenticação e autorização antes de liberar ações administrativas.
6. Desenvolver serviços de torneio e progressão de partidas com testes de domínio.
7. Adicionar eventos Socket.IO após definir os contratos e validar autorização no servidor.

---

**Princípio central:** entender antes de alterar; preservar o que funciona; implementar somente o que pode ser testado; manter a experiência UBC cinematográfica, acessível e rápida.


## 13. Estado atualizado após a implementação da primeira intro (branch feature/cinematic-intro-dashboard)

A partir desta entrega, as informações abaixo substituem os itens antigos deste documento que descreviam a intro como inexistente.

### Implementado nesta branch

- `bazinga/templates/base.html`: overlay de intro, navegação principal, skip link e inclusão do JavaScript.
- `bazinga/templates/championship.html`: landing page com hero cinematográfico e cartões de módulos futuros em estado vazio.
- `bazinga/static/css/style.css`: identidade visual escura com acentos âmbar/fogo, layout responsivo e animações CSS.
- `bazinga/static/js/intro.js`: controle de primeira exibição por sessão, pular, rever, partículas leves, transição de revelação, foco e inert nos elementos de fundo.
- `tests/test_health.py`: teste de presença dos elementos essenciais da intro.
- `README.md`: estrutura e status atualizados.

### Comportamento da intro

- A intro aparece automaticamente uma vez por sessão do navegador, exceto quando o usuário solicita movimento reduzido.
- O cartão original do UBC entra em cena com desaceleração.
- A ação “Revelar campeonato” aciona impacto luminoso e wipe de fogo estilizado.
- “Pular introdução” fecha a camada imediatamente.
- “Rever intro” permite abrir a experiência novamente.
- O conteúdo de fundo recebe `inert` enquanto a intro está aberta; o foco vai para o botão principal e retorna ao elemento anterior ao fechar.
- Se JavaScript não executar, o overlay permanece oculto por padrão e o conteúdo principal continua acessível.
- Não há áudio automático nem dependência de assets protegidos de terceiros.

### Limites desta entrega

- Os cartões de partidas, ranking e Hall da Fama são placeholders explicitamente identificados; não há dados reais conectados.
- A transição de fogo é uma composição CSS original, não um vídeo ou simulação física de chamas.
- O teste adicionado valida a renderização dos elementos HTML, mas não substitui teste visual em navegador nem teste automatizado de interação.
- Os testes ainda precisam ser executados em ambiente Python com as dependências instaladas.

### Próximas tarefas recomendadas

1. Fazer revisão visual em desktop e mobile e ajustar timing/escala conforme o feedback.
2. Se necessário, criar arte original dedicada para o selo/cartão e efeitos de partículas mais ricos.
3. Integrar os cartões do dashboard a consultas reais quando rotas e regras de negócio existirem.
4. Implementar os módulos de torneios e partidas antes de apresentar números ou resultados como dados reais.
