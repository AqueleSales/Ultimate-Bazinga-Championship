# 🏆 Ultimate Bazinga Championship

> Plataforma web para organizar, gerenciar e acompanhar as competições do ecossistema Bazinga.

O **Ultimate Bazinga Championship** é o módulo competitivo do Bazinga Hub. A plataforma foi planejada para administrar campeonatos individuais e por equipes, acompanhar partidas em tempo real e preservar o histórico competitivo dos participantes.

## 🎯 Objetivos

- Centralizar a organização de campeonatos.
- Permitir diferentes formatos de competição sem alterar o código.
- Gerenciar participantes, equipes, fases e partidas.
- Atualizar placares em tempo real.
- Manter histórico, estatísticas, rankings e retrospectivas.
- Oferecer uma interface responsiva com identidade visual própria.

## 🧩 Funcionalidades planejadas

### Campeonatos
- Competições individuais e por equipes.
- Mata-mata simples e duplo.
- Fase de grupos.
- Pontos corridos.
- Formatos híbridos, como grupos seguidos de eliminatórias.
- Fases configuráveis pelo organizador.

### Partidas
- Chaveamento e confrontos.
- Gerenciamento de partidas e horários.
- Placar atualizado em tempo real.
- Registro de resultados oficiais.

### Participantes e histórico
- Perfil competitivo permanente.
- Participação em vários campeonatos, inclusive edições antigas.
- Histórico de partidas e resultados.
- Estatísticas individuais e por equipe.
- Rankings com critérios configuráveis.
- Retrospectivas e Hall da Fama.

### Administração
- Organizador e administradores por campeonato.
- Permissões específicas por função.
- Gerenciamento de inscrições, fases e resultados.

### Transmissão
- Área para incorporar transmissões externas.
- Painel com informações da partida em destaque.

## 🛠️ Stack

### Backend
- Python
- Flask
- Flask-SQLAlchemy / SQLAlchemy
- Flask-Migrate
- Flask-SocketIO

### Frontend
- HTML5 com Jinja2
- CSS3 puro, com variáveis, Flexbox e Grid
- JavaScript Vanilla
- Fetch API
- Socket.IO Client

### Banco de dados
- PostgreSQL
- Neon PostgreSQL
- SQLite como alternativa local para desenvolvimento inicial

### Autenticação planejada
- Google OAuth2
- Discord OAuth2

## 🏗️ Estrutura atual

```text
.
├── app.py
├── config.py
├── requirements.txt
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
│   │   └── main.py
│   ├── services/
│   ├── sockets/
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

A aplicação utiliza o padrão **Application Factory**. Rotas, modelos, serviços e eventos em tempo real ficam separados para evitar concentrar toda a lógica em um único arquivo.

## 💻 Executar localmente

### 1. Clonar o repositório

```bash
git clone https://github.com/AqueleSales/Ultimate-Bazinga-Championship.git
cd Ultimate-Bazinga-Championship
```

### 2. Criar e ativar um ambiente virtual

Windows:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente

Crie um arquivo local chamado `.env`, usando `.env.example` como referência.

- `SECRET_KEY`: chave secreta da aplicação.
- `DATABASE_URL`: conexão PostgreSQL do Neon. Se omitida, a aplicação usa SQLite local.
- Credenciais OAuth: serão necessárias quando a autenticação for implementada.

Nunca envie o arquivo `.env` ao GitHub.

### 5. Executar

```bash
python app.py
```

A aplicação ficará disponível em `http://127.0.0.1:5000`.

## 🗃️ Migrações do banco

Depois de configurar o banco de dados:

```bash
flask --app app db init
flask --app app db migrate -m "Initial database schema"
flask --app app db upgrade
```

As migrações geradas devem ser versionadas no Git. Em ambientes já inicializados, não execute novamente `db init`.

## 🧪 Testes

```bash
python -m pytest
```

Os testes utilizam SQLite em memória e não precisam acessar o banco de produção.

## 🔐 Segurança

- Segredos ficam em variáveis de ambiente.
- O arquivo `.env` é ignorado pelo Git.
- A chave secreta não possui valor padrão inseguro.
- Operações administrativas e alterações oficiais de placar devem ser validadas no servidor.
- O cliente Socket.IO não será autoridade sobre resultados oficiais.

## 📌 Status

O projeto está em fase inicial de estruturação. A aplicação Flask, a organização modular, os primeiros modelos e a página inicial estão sendo preparados. Autenticação, regras de torneio, gerenciamento administrativo, rankings e eventos de placar ainda serão implementados e testados.

## 👥 Projeto

- **Nome:** Ultimate Bazinga Championship
- **Ecossistema:** Bazinga Hub
- **Categoria:** Plataforma web de gerenciamento de competições

---

*Bazinga — Mais do que acompanhar uma competição, fazer parte dela.*
