import hmac

from authlib.integrations.base_client.errors import OAuthError
from flask import Blueprint, abort, current_app, flash, redirect, request, session, url_for

from ..extensions import db, oauth
from ..models import OAuthAccount, User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _provider(name):
    client = getattr(oauth, name)
    if not current_app.config.get(f"{name.upper()}_CLIENT_ID") or not current_app.config.get(f"{name.upper()}_CLIENT_SECRET"):
        abort(503, description=f"Login com {name.title()} ainda não foi configurado.")
    return client


@auth_bp.get("/google")
def google_login():
    client = _provider("google")
    callback = url_for("auth.google_callback", _external=True)
    # Ask Google to show the account chooser instead of silently reusing a session.
    try:
        return client.authorize_redirect(callback, prompt="select_account")
    except Exception:
        current_app.logger.exception("Falha ao iniciar OAuth do Google")
        flash("Não foi possível iniciar o Google Login. Confira as credenciais e o terminal do servidor.", "error")
        return redirect(url_for("main.championship_home", screen="auth"))


@auth_bp.get("/google/callback")
def google_callback():
    client = _provider("google")
    try:
        token = client.authorize_access_token()
        profile = token.get("userinfo") or client.userinfo()
    except Exception:
        current_app.logger.exception("Falha no callback OAuth do Google")
        flash("O Google não conseguiu concluir a autenticação. Confira o terminal do servidor para ver o erro técnico.", "error")
        return redirect(url_for("main.championship_home", screen="auth"))

    provider_id = str(profile.get("sub") or "")
    if not provider_id:
        abort(400, description="O Google não retornou um identificador de usuário válido.")
    return _sign_in("google", provider_id, profile.get("name") or "Competidor", profile.get("email"), profile.get("picture"))


@auth_bp.get("/discord")
def discord_login():
    client = _provider("discord")
    callback = url_for("auth.discord_callback", _external=True)
    try:
        return client.authorize_redirect(callback)
    except Exception:
        current_app.logger.exception("Falha ao iniciar OAuth do Discord")
        flash("Não foi possível iniciar o Discord Login. Confira as credenciais e o terminal do servidor.", "error")
        return redirect(url_for("main.championship_home", screen="auth"))


@auth_bp.get("/discord/callback")
def discord_callback():
    client = _provider("discord")
    try:
        token = client.authorize_access_token()
        profile = client.get("users/@me", token=token).json()
    except Exception:
        current_app.logger.exception("Falha no callback OAuth do Discord")
        flash("O Discord não conseguiu concluir a autenticação. Confira o terminal do servidor para ver o erro técnico.", "error")
        return redirect(url_for("main.championship_home", screen="auth"))

    provider_id = str(profile.get("id") or "")
    if not provider_id:
        abort(400, description="O Discord não retornou um identificador de usuário válido.")
    avatar = profile.get("avatar")
    avatar_url = f"https://cdn.discordapp.com/avatars/{provider_id}/{avatar}.png" if avatar else None
    return _sign_in("discord", provider_id, profile.get("global_name") or profile.get("username") or "Competidor", profile.get("email"), avatar_url)


def _sign_in(provider, provider_id, name, email, avatar_url):
    account = db.session.scalar(
        db.select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == provider_id,
        )
    )
    if account:
        user = account.user
        if not user.is_active:
            abort(403, description="Esta conta está desativada.")
        # Refresh public profile fields from the provider on each successful login.
        user.name = (name or user.name or "Competidor")[:120]
        user.email = email or user.email
        user.avatar_url = avatar_url or user.avatar_url
    else:
        # Do not auto-link identities by email: only the provider's immutable ID
        # proves ownership of this OAuth identity.
        user = User(name=(name or "Competidor")[:120], email=email, avatar_url=avatar_url)
        account = OAuthAccount(
            provider=provider,
            provider_user_id=provider_id,
            email=email,
            user=user,
        )
        db.session.add(user)
        db.session.add(account)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Falha ao salvar a conta local após OAuth com %s", provider)
        flash("A autenticação foi aceita pelo provedor, mas não foi possível salvar sua conta. Confira o terminal do servidor.", "error")
        return redirect(url_for("main.championship_home", screen="auth"))

    # Rotate the session after authentication to avoid session fixation.
    session.clear()
    session["user_id"] = user.id
    session["auth_provider"] = provider
    session.permanent = True
    return redirect(url_for("main.championship_home", screen="hub"))


@auth_bp.post("/logout")
def logout():
    expected = session.get('_csrf_token', '')
    supplied = request.form.get('csrf_token', '')
    if not expected or not hmac.compare_digest(expected, supplied):
        abort(400, description='Token de segurança inválido.')
    session.clear()
    return redirect(url_for("main.championship_home", screen="auth"))
