import hmac
import re
import unicodedata
from datetime import datetime, timezone
from functools import wraps

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, session, url_for

from ..extensions import db
from ..models import (
    Match, MatchResult, Participant, Team, Tournament,
    TournamentAdmin, TournamentRegistration, User,
)

main_bp = Blueprint("main", __name__)


def get_current_user():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id) if user_id else None
    return user if user and user.is_active else None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not get_current_user():
            return redirect(url_for("main.championship_home", screen="auth"))
        return view(*args, **kwargs)
    return wrapped


def valid_csrf():
    expected = session.get("_csrf_token", "")
    supplied = request.form.get("csrf_token", "") or request.headers.get("X-CSRF-Token", "")
    return bool(expected and supplied and hmac.compare_digest(expected, supplied))


def slugify(value):
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return slug[:180] or "torneio"


MODULES = {
    "competitions": {"eyebrow":"CENTRAL DE TORNEIOS / 01","title":"CAMPEONATOS","subtitle":"Encontre sua próxima disputa.","description":"Torneios oficiais, inscrições e calendário.","empty_title":"Nenhum campeonato aberto no momento.","empty_description":"Volte em breve para encontrar a próxima disputa.","icon":"♜","status":"SEM TORNEIOS ABERTOS"},
    "matches": {"eyebrow":"CENTRAL DE PARTIDAS / 02","title":"PARTIDAS","subtitle":"Cada confronto escreve uma história.","description":"Acompanhe partidas agendadas e resultados confirmados.","empty_title":"Nenhum confronto agendado.","empty_description":"As partidas aparecerão aqui quando forem criadas pelos organizadores.","icon":"⚔","status":"SEM PARTIDAS"},
    "ranking": {"eyebrow":"CLASSIFICAÇÃO GLOBAL / 03","title":"RANKING","subtitle":"O topo não se conquista sozinho.","description":"Classificações oficiais por temporada e modalidade.","empty_title":"A corrida pelo topo ainda não começou.","empty_description":"As posições serão calculadas a partir dos resultados oficiais.","icon":"♛","status":"RANKING EM PREPARAÇÃO"},
    "achievements": {"eyebrow":"LEGADO DOS COMPETIDORES / 04","title":"CONQUISTAS","subtitle":"Grandes momentos merecem ser lembrados.","description":"Títulos, marcos, recordes e reconhecimentos.","empty_title":"Seu mural de conquistas está vazio.","empty_description":"As conquistas serão registradas conforme os resultados forem homologados.","icon":"✧","status":"EM BREVE"},
    "community": {"eyebrow":"BAZINGA HUB / 05","title":"COMUNIDADE","subtitle":"Rivais hoje. Lendas amanhã.","description":"Conheça outros competidores e encontre equipes.","empty_title":"A comunidade está se reunindo.","empty_description":"Perfis públicos e recursos sociais serão liberados em breve.","icon":"♧","status":"EM PREPARAÇÃO"},
}


@main_bp.get("/")
def championship_home():
    return render_template("championship.html")


@main_bp.get("/hub")
@login_required
def hub():
    return redirect(url_for("main.championship_home"))


@main_bp.get("/competitions")
def competitions():
    tournaments = db.session.scalars(
        db.select(Tournament)
        .where(Tournament.visibility == "public", Tournament.status.in_(("registration_open", "open", "published")))
        .order_by(Tournament.starts_at.asc().nullslast(), Tournament.created_at.desc())
    ).all()
    user = get_current_user()
    participant = db.session.scalar(db.select(Participant).where(Participant.linked_user_id == user.id)) if user else None
    registered_ids = set()
    if participant:
        registered_ids = set(db.session.scalars(
            db.select(TournamentRegistration.tournament_id).where(
                TournamentRegistration.participant_id == participant.id,
                TournamentRegistration.status.in_(("registered", "confirmed")),
            )
        ).all())
    return render_template("competitions.html", tournaments=tournaments, registered_ids=registered_ids)


@main_bp.get("/competitions/<int:tournament_id>")
def competition_detail(tournament_id):
    tournament = db.get_or_404(Tournament, tournament_id)
    user = get_current_user()
    if tournament.visibility != "public" and (not user or tournament.organizer_id != user.id):
        abort(404)
    registrations = db.session.scalars(
        db.select(TournamentRegistration)
        .where(TournamentRegistration.tournament_id == tournament.id)
        .order_by(TournamentRegistration.registered_at.asc())
    ).all()
    user_registration = None
    if user:
        participant = db.session.scalar(
            db.select(Participant).where(Participant.linked_user_id == user.id)
        )
        if participant:
            user_registration = db.session.scalar(
                db.select(TournamentRegistration).where(
                    TournamentRegistration.tournament_id == tournament.id,
                    TournamentRegistration.participant_id == participant.id,
                    TournamentRegistration.status.in_(("registered", "confirmed")),
                )
            )
    return render_template(
        "competition_detail.html",
        tournament=tournament,
        registrations=registrations,
        user_registration=user_registration,
    )


@main_bp.post("/competitions/<int:tournament_id>/register")
@login_required
def register_competition(tournament_id):
    if not valid_csrf():
        abort(400, description="Token de segurança inválido.")
    tournament = db.get_or_404(Tournament, tournament_id)
    if tournament.status not in ("registration_open", "open"):
        flash("As inscrições deste campeonato não estão abertas.", "error")
        return redirect(url_for("main.competition_detail", tournament_id=tournament.id))
    user = get_current_user()
    participant = db.session.scalar(db.select(Participant).where(Participant.linked_user_id == user.id))
    if participant is None:
        participant = Participant(linked_user_id=user.id, display_name=user.name, avatar_url=user.avatar_url)
        db.session.add(participant)
        db.session.flush()
    existing = db.session.scalar(db.select(TournamentRegistration).where(
        TournamentRegistration.tournament_id == tournament.id,
        TournamentRegistration.participant_id == participant.id,
    ))
    if existing:
        flash("Você já está inscrito neste campeonato.", "info")
    else:
        db.session.add(TournamentRegistration(tournament_id=tournament.id, participant_id=participant.id))
        db.session.commit()
        flash("Inscrição realizada! Você está na lista de competidores.", "success")
    return redirect(url_for("main.competition_detail", tournament_id=tournament.id))


@main_bp.post("/competitions/<int:tournament_id>/cancel")
@login_required
def cancel_registration(tournament_id):
    if not valid_csrf():
        abort(400, description="Token de segurança inválido.")
    tournament = db.get_or_404(Tournament, tournament_id)
    user = get_current_user()
    participant = db.session.scalar(db.select(Participant).where(Participant.linked_user_id == user.id))
    if participant:
        registration = db.session.scalar(db.select(TournamentRegistration).where(
            TournamentRegistration.tournament_id == tournament.id,
            TournamentRegistration.participant_id == participant.id,
            TournamentRegistration.status == "registered",
        ))
        if registration:
            db.session.delete(registration)
            db.session.commit()
            flash("Sua inscrição foi cancelada.", "success")
    return redirect(url_for("main.competition_detail", tournament_id=tournament.id))


@main_bp.post("/competitions/create")
@login_required
def create_competition():
    if not valid_csrf():
        abort(400, description="Token de segurança inválido.")
    user = get_current_user()
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    mode = request.form.get("competition_mode", "individual")
    if not title or len(title) > 180 or mode not in ("individual", "team"):
        flash("Informe um título válido e uma modalidade válida.", "error")
        return redirect(url_for("main.competitions"))
    base = slugify(title)
    slug = base
    suffix = 2
    while db.session.scalar(db.select(Tournament.id).where(Tournament.slug == slug)):
        slug = f"{base}-{suffix}"
        suffix += 1
    tournament = Tournament(
        title=title, slug=slug, description=description[:5000],
        status="registration_open", competition_mode=mode,
        visibility="public", organizer_id=user.id,
    )
    db.session.add(tournament)
    db.session.flush()
    db.session.add(TournamentAdmin(tournament_id=tournament.id, user_id=user.id, role="owner"))
    db.session.commit()
    flash("Campeonato criado e inscrições abertas.", "success")
    return redirect(url_for("main.competition_detail", tournament_id=tournament.id))


@main_bp.get("/<module>")
def module_page(module):
    data = MODULES.get(module)
    if not data:
        abort(404)
    if module == "competitions":
        return redirect(url_for("main.competitions"))
    return render_template("module.html", module=data, module_key=module)


@main_bp.get("/health")
def health_check():
    return jsonify({"status": "ok", "service": "ultimate-bazinga-championship"})
