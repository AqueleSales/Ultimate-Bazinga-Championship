from bazinga.extensions import db
from bazinga.models import (
    Achievement, Clip, CommunityPost, DirectMessage, Match, MatchResult,
    Participant, Tournament, TournamentDetails, TournamentRegistration, User,
)


def signed_in_client(app, client, name="Amigo"):
    with app.app_context():
        user = User(name=name, email=f"{name.lower()}@example.test")
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    client.get("/")
    with client.session_transaction() as session:
        session["user_id"] = user_id
        token = session["_csrf_token"]
    return user_id, token


def test_hub_modules_and_competitions_are_private_to_authenticated_friends(client):
    for path in ("/competitions", "/matches", "/ranking", "/achievements", "/community", "/dm"):
        response = client.get(path)
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/?screen=auth")


def test_authenticated_user_can_open_private_hub_modules(app, client):
    signed_in_client(app, client)
    for path, heading in (
        ("/competitions", b"CAMPEONATOS"),
        ("/matches", b"PARTIDAS"),
        ("/ranking", b"RANKING"),
        ("/achievements", b"CONQUISTAS"),
        ("/community", b"COMUNIDADE"),
        ("/dm", b"MENSAGENS"),
    ):
        response = client.get(path)
        assert response.status_code == 200
        assert heading in response.data


def test_every_authenticated_friend_can_create_event_and_generate_bracket(app, client):
    user_id, token = signed_in_client(app, client, "Organizador")
    with app.app_context():
        people = [Participant(display_name="Player One"), Participant(display_name="Player Two")]
        db.session.add_all(people)
        db.session.flush()
        tournament = Tournament(
            title="UBC Smash Night", slug="ubc-smash-night", description="Noite de Smash",
            status="registration_open", competition_mode="individual",
            visibility="public", organizer_id=user_id,
        )
        db.session.add(tournament)
        db.session.flush()
        db.session.add(TournamentDetails(
            tournament_id=tournament.id, game_title="Super Smash Bros. Ultimate",
            max_participants=8, venue="Discord",
        ))
        for person in people:
            db.session.add(TournamentRegistration(tournament_id=tournament.id, participant_id=person.id))
        db.session.commit()
        tournament_id = tournament.id

    response = client.post(f"/competitions/{tournament_id}/bracket", data={"csrf_token": token})
    assert response.status_code == 302
    with app.app_context():
        match = db.session.scalar(db.select(Match))
        assert match is not None
        assert len(match.slots) == 2


def test_dm_is_created_between_two_authenticated_users(app, client):
    sender_id, token = signed_in_client(app, client, "Remetente")
    with app.app_context():
        recipient = User(name="Destinatário", email="destinatario@example.test")
        db.session.add(recipient)
        db.session.commit()
        recipient_id = recipient.id

    response = client.post(f"/dm/{recipient_id}", data={"csrf_token": token, "body": "Bora jogar hoje?"})
    assert response.status_code == 302
    response = client.get(f"/dm/{recipient_id}")
    assert response.status_code == 200
    assert "Bora jogar hoje?".encode() in response.data
    with app.app_context():
        message = db.session.scalar(db.select(DirectMessage))
        assert message.sender_id == sender_id
        assert message.recipient_id == recipient_id


def test_community_post_and_clip_are_saved_for_the_private_group(app, client):
    user_id, token = signed_in_client(app, client, "Clipper")
    response = client.post("/community", data={
        "csrf_token": token, "body": "Olha esse momento!", "clip_url": "https://example.com/clip",
    })
    assert response.status_code == 302
    response = client.post("/clips", data={
        "csrf_token": token, "title": "Combo absurdo", "url": "https://example.com/video",
    })
    assert response.status_code == 302
    with app.app_context():
        assert db.session.scalar(db.select(CommunityPost)).user_id == user_id
        assert db.session.scalar(db.select(Clip)).user_id == user_id


def test_organizer_can_award_custom_achievement_with_art(app, client):
    organizer_id, token = signed_in_client(app, client, "Organizador")
    with app.app_context():
        recipient = User(name="MVP", email="mvp@example.test")
        db.session.add(recipient)
        db.session.commit()
        recipient_id = recipient.id

    response = client.post("/achievements", data={
        "csrf_token": token, "user_id": recipient_id, "title": "Rei do comeback",
        "description": "Virou a final", "image_url": "https://example.com/medal.png",
        "animation_url": "https://example.com/medal.gif",
    })
    assert response.status_code == 302
    with app.app_context():
        achievement = db.session.scalar(db.select(Achievement))
        assert achievement.user_id == recipient_id
        assert achievement.awarded_by_id == organizer_id
        assert achievement.animation_url.endswith(".gif")


def test_external_clip_urls_reject_unsafe_schemes(app, client):
    _, token = signed_in_client(app, client)
    response = client.post("/clips", data={
        "csrf_token": token, "title": "Link inválido", "url": "javascript:alert(1)",
    })
    assert response.status_code == 302
    with app.app_context():
        assert db.session.scalar(db.select(Clip)) is None


def test_elimination_bracket_auto_advances_bye_and_winner(app, client):
    organizer_id, token = signed_in_client(app, client, "Chaveiro")
    with app.app_context():
        players = [Participant(display_name=f"Player {index}") for index in range(1, 4)]
        db.session.add_all(players)
        db.session.flush()
        tournament = Tournament(
            title="Copa de três", slug="copa-de-tres", status="registration_open",
            competition_mode="individual", visibility="public", organizer_id=organizer_id,
        )
        db.session.add(tournament)
        db.session.flush()
        for player in players:
            db.session.add(TournamentRegistration(tournament_id=tournament.id, participant_id=player.id))
        db.session.commit()
        tournament_id = tournament.id

    client.post(f"/competitions/{tournament_id}/bracket", data={"csrf_token": token})
    with app.app_context():
        matches = db.session.scalars(db.select(Match).order_by(Match.round_number, Match.match_number)).all()
        assert len(matches) == 3
        assert matches[1].status == "completed"  # bye
        final_match = matches[2]
        assert any(slot.participant_id is not None for slot in final_match.slots)

    with app.app_context():
        first_match = db.session.scalar(db.select(Match).where(Match.round_number == 1, Match.match_number == 1))
        winner_slot_id = first_match.slots[0].id
        first_match_id = first_match.id
    response = client.post(f"/matches/{first_match_id}/result", data={
        "csrf_token": token, "winner_slot_id": winner_slot_id,
    })
    assert response.status_code == 302
    with app.app_context():
        final_match = db.session.scalar(db.select(Match).where(Match.round_number == 2))
        assert final_match.status == "scheduled"
        assert all(slot.participant_id for slot in final_match.slots)


def test_organizer_can_award_clip_to_competitor(app, client):
    organizer_id, token = signed_in_client(app, client, "Organizador")
    with app.app_context():
        recipient = User(name="Jogador", email="clip-award@example.test")
        db.session.add(recipient)
        db.session.commit()
        recipient_id = recipient.id
    response = client.post("/clips/award", data={
        "csrf_token": token, "user_id": recipient_id, "title": "Clip da vitória",
        "url": "https://example.com/clip-awarded",
    })
    assert response.status_code == 302
    with app.app_context():
        clip = db.session.scalar(db.select(Clip))
        assert clip.user_id == recipient_id
        assert clip.awarded_by_id == organizer_id


def test_configured_invite_code_is_required_before_new_oauth_accounts(app):
    from bazinga import create_app

    class InviteConfig:
        TESTING = True
        SECRET_KEY = "invite-test-secret"
        SQLALCHEMY_DATABASE_URI = "sqlite://"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        SQLALCHEMY_ENGINE_OPTIONS = {}
        UBC_INVITE_CODE = "friends-only-code"

    invite_app = create_app(InviteConfig)
    client = invite_app.test_client()
    page = client.get("/")
    assert b"CÓDIGO DE CONVITE DA BAZINGA" in page.data
    with client.session_transaction() as session:
        csrf = session["_csrf_token"]

    rejected = client.post("/auth/invite", data={"csrf_token": csrf, "invite_code": "wrong"})
    assert rejected.status_code == 302
    with client.session_transaction() as session:
        assert not session.get("ubc_invite_verified")

    accepted = client.post("/auth/invite", data={"csrf_token": csrf, "invite_code": "friends-only-code"})
    assert accepted.status_code == 302
    with client.session_transaction() as session:
        assert session.get("ubc_invite_verified")
