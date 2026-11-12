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

Crie um arquivo `.env` baseado em `.env.example` e defina um `SECRET_KEY` aleatório. Os botões Google e Discord já estão ligados às rotas OAuth; eles ficam desabilitados até as credenciais correspondentes serem preenchidas.

### Google OAuth (Google Cloud Console)

1. Abra [Google Cloud Console](https://console.cloud.google.com/), crie ou selecione um projeto.
2. Configure a tela de consentimento OAuth (Audience/Branding) e adicione sua conta como usuário de teste se o app estiver em modo de teste.
3. Crie um OAuth Client ID do tipo **Web application**.
4. Em **Authorized JavaScript origins**, adicione `http://127.0.0.1:5000`.
5. Em **Authorized redirect URIs**, adicione exatamente `http://127.0.0.1:5000/auth/google/callback`.
6. Copie o Client ID e o Client Secret para `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET`.

### Discord OAuth

1. Abra o [Discord Developer Portal](https://discord.com/developers/applications) e crie uma Application.
2. Entre em **OAuth2** e adicione o redirect URI `http://127.0.0.1:5000/auth/discord/callback`.
3. Copie o Client ID e gere/copiei o Client Secret para `DISCORD_CLIENT_ID` e `DISCORD_CLIENT_SECRET`.
4. O login solicita os escopos `identify` e `email`; não precisa de bot nem permissões de servidor.

### Variáveis de ambiente

Preencha no seu `.env` local:

```dotenv
GOOGLE_CLIENT_ID=seu-client-id-google
GOOGLE_CLIENT_SECRET=seu-client-secret-google
DISCORD_CLIENT_ID=seu-client-id-discord
DISCORD_CLIENT_SECRET=seu-client-secret-discord
```

Reinicie o servidor depois de alterar o `.env`. Para produção, cadastre também os callbacks HTTPS com o domínio real, por exemplo `https://SEU-DOMINIO/auth/google/callback` e `https://SEU-DOMINIO/auth/discord/callback`, e defina `SESSION_COOKIE_SECURE=1`. O endereço cadastrado no provedor precisa corresponder exatamente ao endereço público usado pelo site.

**Segurança:** nunca envie Client Secret pelo chat, não o coloque no Git e não compartilhe seu arquivo `.env`. O app associa cada conta pelo ID imutável do provedor e não une contas automaticamente só porque os e-mails coincidem.

Execute `python app.py` e abra `http://127.0.0.1:5000`. Na primeira inicialização, o app cria as tabelas ausentes do banco local automaticamente. O método `create_all` não altera tabelas existentes; alterações futuras de esquema devem ser feitas com Flask-Migrate.

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
