from datetime import datetime, timezone

from ..extensions import db


class Participant(db.Model):
    __tablename__ = "participants"

    id = db.Column(db.Integer, primary_key=True)
    linked_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    display_name = db.Column(db.String(120), nullable=False, index=True)
    avatar_url = db.Column(db.String(512), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    linked_user = db.relationship("User")
    registrations = db.relationship(
        "TournamentRegistration",
        back_populates="participant",
    )
