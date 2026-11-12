# 🏆 Ultimate Bazinga Championship

Plataforma web para organizar, gerenciar e acompanhar as competições do ecossistema Bazinga.

## Stack
- Python / Flask com Application Factory
- Flask-SQLAlchemy, Flask-Migrate e Flask-SocketIO
- Authlib para OAuth 2.0 / OpenID Connect
- Jinja2, CSS e JavaScript ES Modules
- PostgreSQL/Neon ou SQLite local

## Executar localmente

```bash
git clone https://github.com/AqueleSales/Ultimate-Bazinga-Championship.git
cd Ultimate-Bazinga-Championship
python -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install -r requirements-dev.txt
```

Crie um arquivo `.env` baseado em `.env.example` e defina um `SECRET_KEY` aleatório. Para ativar os logins, configure aplicações OAuth no Google Cloud Console e no Discord Developer Portal e cadastre os callbacks:

- Google: `http://127.0.0.1:5000/auth/google/callback`
- Discord: `http://127.0.0.1:5000/auth/discord/callback`

Preencha `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `DISCORD_CLIENT_ID` e `DISCORD_CLIENT_SECRET`. Sem credenciais, os provedores aparecem desabilitados e a entrada de visitante continua disponível. Nunca compartilhe nem versione o arquivo `.env`.

Execute `python app.py` e abra `http://127.0.0.1:5000`.

## Testes

```bash
python -m pytest
```

## Experiência visual
- Abertura cinematográfica com envelope 3D Three.js, partículas, iluminação e selo.
- Revelação tipográfica, cortinas e controle para pular a abertura.
- Fallback 2D se WebGL ou o CDN Three.js não estiver disponível.
- Respeito a `prefers-reduced-motion`.
- Tela de entrada, transição de fogo e hub gamer responsivo.
- Cartões de torneios, partidas, ranking e Hall da Fama permanecem placeholders até integração com dados reais.

## Autenticação
Google usa OpenID Connect; Discord usa OAuth2. O sistema cria/recupera a conta local pelo ID imutável do provedor e não vincula contas automaticamente por e-mail. O estado OAuth é gerenciado pelo Authlib. Cookies de sessão usam HttpOnly e SameSite=Lax; em produção HTTPS, defina `SESSION_COOKIE_SECURE=1`.

A autenticação requer credenciais próprias do mantenedor. Não existem credenciais incluídas no repositório.

## Próximos módulos
Torneios, inscrições, equipes, chaveamentos, partidas, resultados, rankings, perfis e atualizações em tempo real ainda precisam de implementação e integração com os modelos existentes.
