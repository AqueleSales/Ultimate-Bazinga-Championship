def test_health_endpoint_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json == {
        "status": "ok",
        "service": "ultimate-bazinga-championship",
    }


def test_homepage_loads(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Ultimate Bazinga" in response.data


def test_homepage_includes_accessible_cinematic_intro(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b'id="cinematic-intro"' in response.data
    assert b'id="intro-skip"' in response.data
    assert b'id="replay-intro"' in response.data
    assert b"prefers-reduced-motion" not in response.data


def test_participant_can_join_multiple_tournaments(app):
    from sqlalchemy.orm import configure_mappers

    from bazinga.extensions import db
    from bazinga.models import Participant, Tournament, TournamentRegistration, User

    configure_mappers()

    with app.app_context():
        organizer = User(name="Organizer")
        participant = Participant(display_name="Player One")
        db.session.add_all([organizer, participant])
        db.session.flush()

        first = Tournament(
            title="Bazinga Open",
            slug="bazinga-open",
            organizer_id=organizer.id,
        )
        second = Tournament(
            title="Bazinga Winter Cup",
            slug="bazinga-winter-cup",
            organizer_id=organizer.id,
        )
        db.session.add_all([first, second])
        db.session.flush()

        db.session.add_all(
            [
                TournamentRegistration(
                    tournament_id=first.id,
                    participant_id=participant.id,
                ),
                TournamentRegistration(
                    tournament_id=second.id,
                    participant_id=participant.id,
                ),
            ]
        )
        db.session.commit()

        assert len(participant.registrations) == 2
