from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, UniqueConstraint

from ..extensions import db


class Match(db.Model):
    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("stage_id", "match_number", name="uq_match_number_per_stage"),
    )

    id = db.Column(db.Integer, primary_key=True)
    stage_id = db.Column(
        db.Integer,
        db.ForeignKey("tournament_stages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    round_number = db.Column(db.Integer, nullable=True)
    match_number = db.Column(db.Integer, nullable=False)
    group_name = db.Column(db.String(80), nullable=True)
    status = db.Column(db.String(24), nullable=False, default="scheduled")
    best_of = db.Column(db.Integer, nullable=True)
    scheduled_at = db.Column(db.DateTime(timezone=True), nullable=True)
    started_at = db.Column(db.DateTime(timezone=True), nullable=True)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    stage = db.relationship("TournamentStage", back_populates="matches")
    slots = db.relationship(
        "MatchSlot",
        back_populates="match",
        cascade="all, delete-orphan",
        order_by="MatchSlot.slot_number",
        foreign_keys="MatchSlot.match_id",
    )
    result = db.relationship(
        "MatchResult",
        back_populates="match",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="MatchResult.match_id",
    )


class MatchSlot(db.Model):
    __tablename__ = "match_slots"
    __table_args__ = (
        UniqueConstraint("match_id", "slot_number", name="uq_match_slot_number"),
        CheckConstraint(
            "participant_id IS NULL OR team_id IS NULL",
            name="ck_match_slot_single_competitor_type",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(
        db.Integer,
        db.ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slot_number = db.Column(db.SmallInteger, nullable=False)
    participant_id = db.Column(
        db.Integer,
        db.ForeignKey("participants.id", ondelete="RESTRICT"),
        nullable=True,
    )
    team_id = db.Column(
        db.Integer,
        db.ForeignKey("teams.id", ondelete="RESTRICT"),
        nullable=True,
    )
    score = db.Column(db.Integer, nullable=False, default=0)
    seed = db.Column(db.Integer, nullable=True)
    source_match_id = db.Column(
        db.Integer,
        db.ForeignKey("matches.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_outcome = db.Column(db.String(12), nullable=True)

    match = db.relationship(
        "Match",
        back_populates="slots",
        foreign_keys=[match_id],
    )
    participant = db.relationship("Participant")
    team = db.relationship("Team")
    source_match = db.relationship("Match", foreign_keys=[source_match_id])


class MatchResult(db.Model):
    __tablename__ = "match_results"

    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(
        db.Integer,
        db.ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    winner_slot_id = db.Column(
        db.Integer,
        db.ForeignKey("match_slots.id", ondelete="RESTRICT"),
        nullable=False,
    )
    recorded_by_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    notes = db.Column(db.Text, nullable=True)
    final_scores = db.Column(db.JSON, nullable=False, default=dict)
    finalized_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    match = db.relationship(
        "Match",
        back_populates="result",
        foreign_keys=[match_id],
    )
    winner_slot = db.relationship("MatchSlot", foreign_keys=[winner_slot_id])
    recorded_by = db.relationship("User")
