from datetime import datetime, timezone

from sqlalchemy import UniqueConstraint

from ..extensions import db


class Tournament(db.Model):
    __tablename__ = "tournaments"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    slug = db.Column(db.String(200), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(24), nullable=False, default="draft")
    competition_mode = db.Column(db.String(20), nullable=False, default="individual")
    visibility = db.Column(db.String(20), nullable=False, default="public")
    organizer_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    starts_at = db.Column(db.DateTime(timezone=True), nullable=True)
    ends_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    organizer = db.relationship("User")
    stages = db.relationship(
        "TournamentStage",
        back_populates="tournament",
        cascade="all, delete-orphan",
        order_by="TournamentStage.order_index",
    )
    registrations = db.relationship(
        "TournamentRegistration",
        back_populates="tournament",
        cascade="all, delete-orphan",
    )
    teams = db.relationship(
        "Team",
        back_populates="tournament",
        cascade="all, delete-orphan",
    )
    administrators = db.relationship(
        "TournamentAdmin",
        back_populates="tournament",
        cascade="all, delete-orphan",
    )


class TournamentAdmin(db.Model):
    __tablename__ = "tournament_admins"
    __table_args__ = (
        UniqueConstraint("tournament_id", "user_id", name="uq_tournament_admin_user"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(
        db.Integer,
        db.ForeignKey("tournaments.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role = db.Column(db.String(24), nullable=False, default="admin")
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    tournament = db.relationship("Tournament", back_populates="administrators")
    user = db.relationship("User")


class TournamentStage(db.Model):
    __tablename__ = "tournament_stages"
    __table_args__ = (
        UniqueConstraint("tournament_id", "order_index", name="uq_tournament_stage_order"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(
        db.Integer,
        db.ForeignKey("tournaments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(120), nullable=False)
    stage_type = db.Column(db.String(32), nullable=False)
    order_index = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(24), nullable=False, default="pending")
    settings = db.Column(db.JSON, nullable=False, default=dict)
    starts_at = db.Column(db.DateTime(timezone=True), nullable=True)
    ends_at = db.Column(db.DateTime(timezone=True), nullable=True)

    tournament = db.relationship("Tournament", back_populates="stages")
    matches = db.relationship(
        "Match",
        back_populates="stage",
        cascade="all, delete-orphan",
    )


class Team(db.Model):
    __tablename__ = "teams"
    __table_args__ = (
        UniqueConstraint("tournament_id", "name", name="uq_team_name_per_tournament"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(
        db.Integer,
        db.ForeignKey("tournaments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(120), nullable=False)
    tag = db.Column(db.String(16), nullable=True)
    seed = db.Column(db.Integer, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    tournament = db.relationship("Tournament", back_populates="teams")
    registrations = db.relationship(
        "TournamentRegistration",
        back_populates="team",
    )


class TournamentRegistration(db.Model):
    __tablename__ = "tournament_registrations"
    __table_args__ = (
        UniqueConstraint(
            "tournament_id",
            "participant_id",
            name="uq_participant_registration_per_tournament",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(
        db.Integer,
        db.ForeignKey("tournaments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    participant_id = db.Column(
        db.Integer,
        db.ForeignKey("participants.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    team_id = db.Column(
        db.Integer,
        db.ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status = db.Column(db.String(24), nullable=False, default="registered")
    seed = db.Column(db.Integer, nullable=True)
    registered_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    tournament = db.relationship("Tournament", back_populates="registrations")
    participant = db.relationship("Participant", back_populates="registrations")
    team = db.relationship("Team", back_populates="registrations")
