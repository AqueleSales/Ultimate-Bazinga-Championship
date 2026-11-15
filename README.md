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

## Hub privado da turma
O UBC é pensado para um grupo de amigos, não como uma rede social aberta. As áreas internas exigem autenticação Google ou Discord.

- **Campeonatos:** catálogo em grid 2×N com jogo, arte, horário, vagas, local, regras, link de transmissão e inscrição com limite de participantes.
- **Partidas:** chave eliminatória com rodadas, BYEs e avanço automático dos vencedores. Partidas ao vivo ficam em destaque e a tela consulta atualizações a cada 15 segundos.
- **Ranking:** lista de jogadores, vitórias registradas, top 3 de MVPs e equipes cadastradas.
- **Conquistas:** organizadores podem entregar reconhecimentos com imagem e GIF/URL de animação.
- **Clips:** cada pessoa pode salvar seus próprios links; organizadores também podem entregar clips a outros competidores.
- **DMs:** conversas privadas entre contas autenticadas.
- **Comunidade:** mural interno para avisos, publicações e links de clips.

Nesta fase, todo usuário autenticado tem permissão temporária para criar e gerenciar eventos, registrar resultados, entregar conquistas/clips e publicar no mural. Os quatro administradores permanentes ainda não foram definidos no sistema; quando os nomes/contas forem definidos, será necessário introduzir papéis permanentes e restringir essas ações.

**Privacidade:** as páginas internas exigem login, mas o fluxo OAuth ainda permite que uma conta nova seja criada por qualquer pessoa que consiga autenticar com Google/Discord. Para tornar o acesso realmente exclusivo aos amigos, configure uma lista de membros aprovados ou um código de convite antes de disponibilizar o endereço publicamente.

## Autenticação
Google usa OpenID Connect; Discord usa OAuth2. O sistema cria/recupera a conta local pelo ID imutável do provedor e não vincula contas automaticamente por e-mail. O estado OAuth é gerenciado pelo Authlib. Cookies de sessão usam HttpOnly e SameSite=Lax; em produção HTTPS, defina `SESSION_COOKIE_SECURE=1`.

A autenticação requer credenciais próprias do mantenedor. Não existem credenciais incluídas no repositório.

## Dados e inicialização
As tabelas novas `tournament_details`, `direct_messages`, `achievements`, `clips` e `community_posts` são criadas por `db.create_all()` na inicialização, sem alterar as tabelas antigas. Em produção, faça backup do banco antes de atualizar o código. O avanço de chaves e os resultados são validados no servidor.

## Limitações conhecidas
- A atualização de partidas ao vivo usa polling HTTP de 15 segundos, não WebSockets em tempo real.
- O ranking de MVP é baseado em vitórias individuais registradas; regras avançadas de pontuação, desempate, MVP por partida e estatísticas por jogo ainda precisam ser definidas.
- O gerador atual implementa mata-mata simples; grupos, dupla eliminação e formatos híbridos ainda não estão disponíveis.
- Links de imagem, GIF e clips são externos; o sistema salva URLs, não faz upload nem transcodifica arquivos.
- A experiência visual precisa de validação manual em navegadores desktop e mobile após o deploy.
