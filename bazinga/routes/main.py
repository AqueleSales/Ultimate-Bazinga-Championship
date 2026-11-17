import hmac
import re
import unicodedata
from datetime import datetime, timezone
from functools import wraps
from urllib.parse import urlparse

from sqlalchemy import or_, func
from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, session, url_for

from ..extensions import db
from ..storage import StorageError, StorageNotConfigured, is_storage_reference, signed_media_url, upload_media
from ..models import (
    Achievement, Clip, CommunityPost, DirectMessage, Match, MatchResult,
    MatchSlot, Participant, Team, Tournament, TournamentAdmin,
    TournamentDetails, TournamentRegistration, TournamentStage, User,
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


def organizer_required(view):
    """Temporary UBC policy: every authenticated friend can organize everything."""
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        return view(*args, **kwargs)
    return wrapped


def valid_csrf():
    expected = session.get("_csrf_token", "")
    supplied = request.form.get("csrf_token", "") or request.headers.get("X-CSRF-Token", "")
    return bool(expected and supplied and hmac.compare_digest(expected, supplied))


def require_csrf():
    if not valid_csrf():
        abort(400, description="Token de segurança inválido.")


def safe_url(value):
    value = (value or "").strip()
    if not value:
        return None
    parsed = urlparse(value)
    return value[:1000] if parsed.scheme in ("http", "https") and parsed.netloc else None


def slugify(value):
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return slug[:180] or "torneio"


MODULES = {
    "competitions": {"eyebrow":"CENTRAL DE TORNEIOS / 01","title":"CAMPEONATOS","subtitle":"Os eventos da nossa arena.","description":"Veja quais jogos estão chegando, horários, vagas e regras." ,"icon":"♜"},
    "matches": {"eyebrow":"CHAVES OFICIAIS / 02","title":"PARTIDAS","subtitle":"Cada confronto escreve uma história.","description":"Acompanhe o ao vivo, as próximas partidas e os resultados." ,"icon":"⚔"},
    "ranking": {"eyebrow":"PLACAR DA TURMA / 03","title":"RANKING","subtitle":"Quem está no topo da arena?","description":"Jogadores, equipes e MVPs. Os números vêm dos resultados registrados." ,"icon":"♛"},
    "achievements": {"eyebrow":"LEGADO DOS COMPETIDORES / 04","title":"CONQUISTAS","subtitle":"Momentos que merecem ficar para sempre.","description":"Medalhas, reconhecimentos especiais e clips da nossa história." ,"icon":"✧"},
    "community": {"eyebrow":"BAZINGA HUB / 05","title":"COMUNIDADE","subtitle":"A resenha continua fora da partida.","description":"Mural privado para avisos, comentários e clips dos amigos." ,"icon":"♧"},
    "dm": {"eyebrow":"MENSAGENS PRIVADAS / 06","title":"MENSAGENS","subtitle":"Fale diretamente com alguém da turma.","description":"Conversas privadas entre os participantes do UBC." ,"icon":"✉"},
}


@main_bp.get("/")
def championship_home():
    return render_template("championship.html")


@main_bp.get("/hub")
@login_required
def hub():
    return redirect(url_for("main.championship_home"))


@main_bp.get("/competitions")
@login_required
def competitions():
    search_query = (request.args.get("q") or "").strip()[:100]
    statement = db.select(Tournament).where(
        Tournament.status.in_(("registration_open", "open", "published", "live", "completed")),
    )
    if search_query:
        pattern = f"%{search_query}%"
        statement = statement.where(or_(Tournament.title.ilike(pattern), Tournament.description.ilike(pattern)))
    tournaments = db.session.scalars(statement.order_by(Tournament.starts_at.asc().nullslast(), Tournament.created_at.desc())).all()
    user = get_current_user()
    participant = db.session.scalar(db.select(Participant).where(Participant.linked_user_id == user.id)) if user else None
    registered_ids = set()
    if participant:
        registered_ids = set(db.session.scalars(db.select(TournamentRegistration.tournament_id).where(
            TournamentRegistration.participant_id == participant.id,
            TournamentRegistration.status.in_(("registered", "confirmed")),
        )).all())
    tournament_images = {t.id: signed_media_url(t.details.image_url) for t in tournaments if t.details and t.details.image_url}
    return render_template("competitions.html", tournaments=tournaments, registered_ids=registered_ids, search_query=search_query, tournament_images=tournament_images)


@main_bp.get("/competitions/<int:tournament_id>")
@login_required
def competition_detail(tournament_id):
    tournament = db.get_or_404(Tournament, tournament_id)
    user = get_current_user()
    registrations = db.session.scalars(db.select(TournamentRegistration).where(
        TournamentRegistration.tournament_id == tournament.id
    ).order_by(TournamentRegistration.registered_at.asc())).all()
    participant = db.session.scalar(db.select(Participant).where(Participant.linked_user_id == user.id)) if user else None
    user_registration = db.session.scalar(db.select(TournamentRegistration).where(
        TournamentRegistration.tournament_id == tournament.id,
        TournamentRegistration.participant_id == participant.id,
        TournamentRegistration.status.in_(("registered", "confirmed")),
    )) if participant else None
    matches = db.session.scalars(
        db.select(Match).join(TournamentStage).where(TournamentStage.tournament_id == tournament.id)
        .order_by(Match.round_number, Match.match_number)
    ).all()
    tournament_image_url = signed_media_url(tournament.details.image_url) if tournament.details and tournament.details.image_url else None
    return render_template("competition_detail.html", tournament=tournament, registrations=registrations, user_registration=user_registration, matches=matches, tournament_image_url=tournament_image_url)


@main_bp.post("/competitions/<int:tournament_id>/register")
@login_required
def register_competition(tournament_id):
    require_csrf()
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
    details = db.session.scalar(db.select(TournamentDetails).where(TournamentDetails.tournament_id == tournament.id))
    count = db.session.scalar(db.select(func.count(TournamentRegistration.id)).where(
        TournamentRegistration.tournament_id == tournament.id,
        TournamentRegistration.status.in_(("registered", "confirmed")),
    )) or 0
    if existing:
        flash("Você já está inscrito neste campeonato.", "info")
    elif details and details.max_participants and count >= details.max_participants:
        flash("As vagas deste campeonato já foram preenchidas.", "error")
    else:
        db.session.add(TournamentRegistration(tournament_id=tournament.id, participant_id=participant.id))
        db.session.commit()
        flash("Inscrição realizada! Você está na lista de competidores.", "success")
    return redirect(url_for("main.competition_detail", tournament_id=tournament.id))


@main_bp.post("/competitions/<int:tournament_id>/cancel")
@login_required
def cancel_registration(tournament_id):
    require_csrf()
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


@main_bp.post("/media/upload")
@login_required
def upload_media_file():
    require_csrf()
    uploaded = request.files.get("file")
    kind = (request.form.get("kind") or "tournaments").strip()
    if kind not in ("tournaments", "achievements"):
        return jsonify(error="Categoria de mídia inválida."), 400
    if uploaded is None or not uploaded.filename:
        return jsonify(error="Selecione um arquivo para enviar."), 400
    try:
        return jsonify(reference=upload_media(uploaded, kind=kind)), 201
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except StorageNotConfigured:
        return jsonify(error="O armazenamento do Supabase ainda não foi configurado no servidor."), 503
    except StorageError:
        current_app.logger.exception("Supabase Storage upload failed")
        return jsonify(error="Não foi possível enviar o arquivo ao Supabase. Tente novamente."), 502


@main_bp.post("/competitions/create")
@organizer_required
def create_competition():
    require_csrf()
    user = get_current_user()
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    mode = request.form.get("competition_mode", "individual")
    if not title or len(title) > 180 or mode not in ("individual", "team"):
        flash("Informe um título válido e uma modalidade válida.", "error")
        return redirect(url_for("main.competitions"))
    base, slug, suffix = slugify(title), slugify(title), 2
    while db.session.scalar(db.select(Tournament.id).where(Tournament.slug == slug)):
        slug, suffix = f"{base}-{suffix}", suffix + 1
    tournament = Tournament(title=title, slug=slug, description=description[:5000],
        status="registration_open", competition_mode=mode, visibility="public", organizer_id=user.id,
        starts_at=_parse_datetime(request.form.get("starts_at")))
    db.session.add(tournament)
    db.session.flush()
    details = TournamentDetails(tournament_id=tournament.id,
        game_title=(request.form.get("game_title") or title).strip()[:180],
        image_url=(request.form.get("image_url") or "").strip()[:1000] if is_storage_reference(request.form.get("image_url")) else safe_url(request.form.get("image_url")),
        max_participants=_positive_int(request.form.get("max_participants")),
        venue=(request.form.get("venue") or "").strip()[:180] or None,
        rules=(request.form.get("rules") or "").strip()[:5000] or None,
        stream_url=safe_url(request.form.get("stream_url")))
    db.session.add(details)
    db.session.add(TournamentAdmin(tournament_id=tournament.id, user_id=user.id, role="owner"))
    db.session.commit()
    flash("Evento criado! Todos os participantes autenticados podem organizar o UBC nesta fase.", "success")
    return redirect(url_for("main.competition_detail", tournament_id=tournament.id))


def _parse_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _positive_int(value):
    try:
        number = int(value)
        return number if number > 0 else None
    except (TypeError, ValueError):
        return None


def _auto_resolve_bye(match, recorder_id):
    slots = match.slots
    unresolved = [
        slot for slot in slots
        if slot.source_match_id and slot.source_match.status not in ("completed", "bye")
    ]
    if unresolved or match.result:
        return
    filled = [slot for slot in slots if slot.participant_id or slot.team_id]
    if len(filled) == 2:
        if match.status == "bye":
            match.status = "scheduled"
        return
    if len(filled) == 1:
        winner = filled[0]
        match.status = "completed"
        match.completed_at = datetime.now(timezone.utc)
        db.session.add(MatchResult(match_id=match.id, winner_slot_id=winner.id, recorded_by_id=recorder_id))
        _propagate_winner(match, winner, recorder_id)
    elif len(filled) == 0:
        match.status = "bye"
        match.completed_at = datetime.now(timezone.utc)
        _propagate_winner(match, None, recorder_id)


def _propagate_winner(match, winner, recorder_id):
    parent_slots = db.session.scalars(db.select(MatchSlot).where(MatchSlot.source_match_id == match.id)).all()
    for parent_slot in parent_slots:
        if winner:
            parent_slot.participant_id = winner.participant_id
            parent_slot.team_id = winner.team_id
            parent_slot.seed = winner.seed
        parent_match = parent_slot.match
        if parent_match.status not in ("completed", "bye"):
            _auto_resolve_bye(parent_match, recorder_id)


@main_bp.post("/competitions/<int:tournament_id>/bracket")
@organizer_required
def create_bracket(tournament_id):
    require_csrf()
    tournament = db.get_or_404(Tournament, tournament_id)
    if db.session.scalar(db.select(TournamentStage.id).where(TournamentStage.tournament_id == tournament.id)):
        flash("Este campeonato já possui uma chave criada.", "info")
        return redirect(url_for("main.competition_detail", tournament_id=tournament.id))
    registrations = db.session.scalars(db.select(TournamentRegistration).where(
        TournamentRegistration.tournament_id == tournament.id,
        TournamentRegistration.status.in_(("registered", "confirmed")),
    ).order_by(TournamentRegistration.registered_at.asc())).all()
    if len(registrations) < 2:
        flash("São necessários pelo menos dois competidores inscritos para gerar a chave.", "error")
        return redirect(url_for("main.competition_detail", tournament_id=tournament.id))

    size = 1
    while size < len(registrations):
        size *= 2
    stage = TournamentStage(tournament_id=tournament.id, name="Chave principal",
                            stage_type="single_elimination", order_index=1, status="in_progress")
    db.session.add(stage)
    db.session.flush()

    rounds = {}
    first_round = []
    global_match_number = 1
    total_rounds = size.bit_length() - 1
    for round_number in range(1, total_rounds + 1):
        match_count = size // (2 ** round_number)
        rounds[round_number] = []
        for local_match_number in range(1, match_count + 1):
            match = Match(stage_id=stage.id, round_number=round_number,
                          match_number=global_match_number, status="scheduled")
            global_match_number += 1
            db.session.add(match)
            db.session.flush()
            rounds[round_number].append(match)
            if round_number == 1:
                first_round.append(match)
                first_index = (local_match_number - 1) * 2
                for slot_number in (1, 2):
                    registration = registrations[first_index + slot_number - 1] if first_index + slot_number - 1 < len(registrations) else None
                    db.session.add(MatchSlot(
                        match_id=match.id, slot_number=slot_number,
                        participant_id=(registration.participant_id if registration and not registration.team_id else None),
                        team_id=(registration.team_id if registration else None),
                        seed=(registration.seed if registration else None),
                    ))
            else:
                previous = rounds[round_number - 1]
                child_index = (local_match_number - 1) * 2
                for slot_number, child in enumerate(previous[child_index:child_index + 2], start=1):
                    db.session.add(MatchSlot(match_id=match.id, slot_number=slot_number,
                                              source_match_id=child.id, source_outcome="winner"))

    db.session.flush()
    for match in first_round:
        _auto_resolve_bye(match, get_current_user().id)
    db.session.commit()
    flash("Chave eliminatória criada! Os vencedores avançam automaticamente para a próxima rodada.", "success")
    return redirect(url_for("main.competition_detail", tournament_id=tournament.id))


@main_bp.post("/matches/<int:match_id>/live")
@organizer_required
def set_match_live(match_id):
    require_csrf()
    match = db.get_or_404(Match, match_id)
    if match.status != "scheduled":
        abort(409, description="Somente partidas agendadas podem ser iniciadas.")
    match.status = "live"
    match.started_at = match.started_at or datetime.now(timezone.utc)
    db.session.commit()
    flash("Partida marcada como AO VIVO.", "success")
    return redirect(url_for("main.module_page", module="matches"))


@main_bp.post("/matches/<int:match_id>/result")
@organizer_required
def record_match_result(match_id):
    require_csrf()
    match = db.get_or_404(Match, match_id)
    if match.status not in ("scheduled", "live"):
        abort(409, description="Esta partida já foi encerrada ou não está disponível.")
    winner_id = _positive_int(request.form.get("winner_slot_id"))
    winner = db.session.scalar(db.select(MatchSlot).where(MatchSlot.id == winner_id, MatchSlot.match_id == match.id)) if winner_id else None
    if not winner or not winner.participant_id and not winner.team_id:
        abort(400, description="Selecione um competidor válido para vencer.")
    existing = match.result
    if existing:
        existing.winner_slot_id = winner.id
        existing.recorded_by_id = get_current_user().id
        existing.finalized_at = datetime.now(timezone.utc)
    else:
        db.session.add(MatchResult(match_id=match.id, winner_slot_id=winner.id, recorded_by_id=get_current_user().id))
    match.status = "completed"
    match.completed_at = datetime.now(timezone.utc)
    match.status = "completed"
    match.completed_at = datetime.now(timezone.utc)
    db.session.flush()
    _propagate_winner(match, winner, get_current_user().id)
    db.session.commit()
    flash("Resultado oficial registrado e chave atualizada.", "success")
    return redirect(url_for("main.module_page", module="matches"))


@main_bp.get("/<module>")
@login_required
def module_page(module):
    data = MODULES.get(module)
    if not data:
        abort(404)
    context = {"module": data, "module_key": module}
    if module == "matches":
        context["live_matches"] = db.session.scalars(db.select(Match).where(Match.status == "live").order_by(Match.started_at.desc())).all()
        context["other_matches"] = db.session.scalars(db.select(Match).where(Match.status != "live").order_by(Match.scheduled_at.asc().nullslast(), Match.id.desc()).limit(80)).all()
    elif module == "ranking":
        context["participants"] = db.session.scalars(db.select(Participant).order_by(Participant.display_name.asc())).all()
        wins = {}
        for result in db.session.scalars(db.select(MatchResult).order_by(MatchResult.finalized_at.desc())).all():
            slot = result.winner_slot
            if slot and slot.participant_id:
                wins[slot.participant_id] = wins.get(slot.participant_id, 0) + 1
        context["wins"] = wins
        context["mvp"] = sorted(context["participants"], key=lambda p: wins.get(p.id, 0), reverse=True)[:3]
        context["teams"] = db.session.scalars(db.select(Team).order_by(Team.name.asc())).all()
    elif module == "achievements":
        context["achievements"] = db.session.scalars(db.select(Achievement).order_by(Achievement.created_at.desc()).limit(100)).all()
        context["achievement_media"] = {
            item.id: {
                "image": signed_media_url(item.image_url) if item.image_url else None,
                "animation": signed_media_url(item.animation_url) if item.animation_url else None,
            } for item in context["achievements"]
        }
        context["clips"] = db.session.scalars(db.select(Clip).order_by(Clip.created_at.desc()).limit(100)).all()
        context["users"] = db.session.scalars(db.select(User).where(User.is_active.is_(True)).order_by(User.name.asc())).all()
    elif module == "community":
        context["posts"] = db.session.scalars(db.select(CommunityPost).order_by(CommunityPost.created_at.desc()).limit(100)).all()
    elif module == "dm":
        user = get_current_user()
        context["users"] = db.session.scalars(db.select(User).where(User.is_active.is_(True), User.id != user.id).order_by(User.name.asc())).all() if user else []
        context["conversations"] = _conversations(user) if user else []
    return render_template("module.html", **context)


def _conversations(user):
    sent = db.session.scalars(db.select(DirectMessage.recipient_id).where(DirectMessage.sender_id == user.id)).all()
    received = db.session.scalars(db.select(DirectMessage.sender_id).where(DirectMessage.recipient_id == user.id)).all()
    ids = set(sent + received)
    if not ids:
        return []
    users = db.session.scalars(db.select(User).where(User.id.in_(ids), User.is_active.is_(True))).all()
    latest = []
    for other in users:
        message = db.session.scalar(db.select(DirectMessage).where(
            or_((DirectMessage.sender_id == user.id) & (DirectMessage.recipient_id == other.id),
                (DirectMessage.sender_id == other.id) & (DirectMessage.recipient_id == user.id))
        ).order_by(DirectMessage.created_at.desc()).limit(1))
        if message:
            latest.append((other, message))
    return sorted(latest, key=lambda item: item[1].created_at, reverse=True)


@main_bp.get("/dm/<int:user_id>")
@login_required
def direct_message(user_id):
    user = get_current_user()
    other = db.get_or_404(User, user_id)
    if other.id == user.id or not other.is_active:
        abort(404)
    messages = db.session.scalars(db.select(DirectMessage).where(
        or_((DirectMessage.sender_id == user.id) & (DirectMessage.recipient_id == other.id),
            (DirectMessage.sender_id == other.id) & (DirectMessage.recipient_id == user.id))
    ).order_by(DirectMessage.created_at.asc()).limit(300)).all()
    now = datetime.now(timezone.utc)
    for message in messages:
        if message.recipient_id == user.id and message.read_at is None:
            message.read_at = now
    db.session.commit()
    return render_template("dm_conversation.html", other_user=other, messages=messages)


@main_bp.post("/dm/<int:user_id>")
@login_required
def send_direct_message(user_id):
    require_csrf()
    user = get_current_user()
    other = db.get_or_404(User, user_id)
    body = (request.form.get("body") or "").strip()
    if other.id == user.id or not other.is_active:
        abort(404)
    if not body or len(body) > 4000:
        flash("A mensagem deve ter entre 1 e 4.000 caracteres.", "error")
    else:
        db.session.add(DirectMessage(sender_id=user.id, recipient_id=other.id, body=body))
        db.session.commit()
    return redirect(url_for("main.direct_message", user_id=other.id))


@main_bp.post("/community")
@login_required
def create_community_post():
    require_csrf()
    body = (request.form.get("body") or "").strip()
    clip_url = safe_url(request.form.get("clip_url"))
    if not body or len(body) > 2000:
        flash("Escreva uma publicação de até 2.000 caracteres.", "error")
    else:
        db.session.add(CommunityPost(user_id=get_current_user().id, body=body, clip_url=clip_url))
        db.session.commit()
        flash("Publicado no mural da turma.", "success")
    return redirect(url_for("main.module_page", module="community"))


@main_bp.post("/achievements")
@organizer_required
def award_achievement():
    require_csrf()
    user_id = _positive_int(request.form.get("user_id"))
    recipient = db.session.get(User, user_id) if user_id else None
    title = (request.form.get("title") or "").strip()
    if not recipient or not recipient.is_active or not title or len(title) > 120:
        flash("Escolha um competidor e informe um título válido.", "error")
    else:
        db.session.add(Achievement(user_id=recipient.id, awarded_by_id=get_current_user().id,
            title=title, description=(request.form.get("description") or "").strip()[:500] or None,
            image_url=(request.form.get("image_url") or "").strip()[:1000] if is_storage_reference(request.form.get("image_url")) else safe_url(request.form.get("image_url")),
            animation_url=(request.form.get("animation_url") or "").strip()[:1000] if is_storage_reference(request.form.get("animation_url")) else safe_url(request.form.get("animation_url"))))
        db.session.commit()
        flash("Conquista personalizada entregue!", "success")
    return redirect(url_for("main.module_page", module="achievements"))


@main_bp.post("/clips")
@login_required
def save_clip():
    require_csrf()
    title = (request.form.get("title") or "").strip()
    clip_url = safe_url(request.form.get("url"))
    if not title or len(title) > 140 or not clip_url:
        flash("Informe um título e um link de clip válido (http/https).", "error")
    else:
        db.session.add(Clip(user_id=get_current_user().id, title=title, url=clip_url,
            description=(request.form.get("description") or "").strip()[:500] or None))
        db.session.commit()
        flash("Clip salvo na sua coleção.", "success")
    return redirect(url_for("main.module_page", module="achievements"))


@main_bp.post("/clips/award")
@organizer_required
def award_clip():
    require_csrf()
    user_id = _positive_int(request.form.get("user_id"))
    recipient = db.session.get(User, user_id) if user_id else None
    title = (request.form.get("title") or "").strip()
    clip_url = safe_url(request.form.get("url"))
    if not recipient or not recipient.is_active or not title or len(title) > 140 or not clip_url:
        flash("Escolha um competidor e informe título e link válidos para o clip.", "error")
    else:
        db.session.add(Clip(user_id=recipient.id, awarded_by_id=get_current_user().id,
            title=title, url=clip_url, description=(request.form.get("description") or "").strip()[:500] or None))
        db.session.commit()
        flash("Clip entregue ao competidor!", "success")
    return redirect(url_for("main.module_page", module="achievements"))


@main_bp.get("/health")
def health_check():
    return {"status": "ok", "service": "ultimate-bazinga-championship"}


@main_bp.get("/admin")
@organizer_required
def admin_control_room():
    tournaments = db.session.scalars(db.select(Tournament).order_by(Tournament.created_at.desc())).all()
    users = db.session.scalars(db.select(User).where(User.is_active.is_(True)).order_by(User.name.asc())).all()
    registrations = db.session.scalars(db.select(TournamentRegistration).order_by(TournamentRegistration.registered_at.desc()).limit(100)).all()
    return render_template("admin.html", tournaments=tournaments, users=users, registrations=registrations)


@main_bp.get("/admin/tournaments/new")
@organizer_required
def admin_new_tournament():
    return render_template("admin_tournament_form.html", tournament=None)


@main_bp.get("/admin/tournaments/<int:tournament_id>/edit")
@organizer_required
def admin_edit_tournament(tournament_id):
    return render_template("admin_tournament_form.html", tournament=db.get_or_404(Tournament, tournament_id))


@main_bp.post("/admin/tournaments/<int:tournament_id>/edit")
@organizer_required
def admin_update_tournament(tournament_id):
    require_csrf()
    tournament = db.get_or_404(Tournament, tournament_id)
    title = (request.form.get("title") or "").strip()
    mode = request.form.get("competition_mode", "individual")
    if not title or len(title) > 180 or mode not in ("individual", "team"):
        flash("Confira o título e a modalidade do campeonato.", "error")
        return redirect(url_for("main.admin_edit_tournament", tournament_id=tournament.id))
    tournament.title = title
    tournament.description = (request.form.get("description") or "").strip()[:5000]
    tournament.competition_mode = mode
    tournament.status = request.form.get("status", tournament.status)
    tournament.starts_at = _parse_datetime(request.form.get("starts_at"))
    details = tournament.details or TournamentDetails(tournament_id=tournament.id)
    db.session.add(details)
    details.game_title = (request.form.get("game_title") or title).strip()[:180]
    image_ref = (request.form.get("image_url") or "").strip()
    details.image_url = image_ref[:1000] if is_storage_reference(image_ref) else safe_url(image_ref)
    details.max_participants = _positive_int(request.form.get("max_participants"))
    details.venue = (request.form.get("venue") or "").strip()[:180] or None
    details.rules = (request.form.get("rules") or "").strip()[:5000] or None
    details.stream_url = safe_url(request.form.get("stream_url"))
    db.session.commit()
    flash("Configurações do campeonato atualizadas.", "success")
    return redirect(url_for("main.admin_control_room"))


@main_bp.get("/admin/achievements/new")
@organizer_required
def admin_new_achievement():
    users = db.session.scalars(db.select(User).where(User.is_active.is_(True)).order_by(User.name.asc())).all()
    return render_template("admin_achievement_form.html", users=users)

@main_bp.get("/admin/matches")
@organizer_required
def admin_matches():
    matches = db.session.scalars(db.select(Match).order_by(Match.started_at.desc().nullslast(), Match.id.desc()).limit(200)).all()
    return render_template("admin_matches.html", matches=matches)
