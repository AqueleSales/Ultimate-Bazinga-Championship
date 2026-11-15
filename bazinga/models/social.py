from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Index

from ..extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class TournamentDetails(db.Model):
    __tablename__ = "tournament_details"

    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey("tournaments.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    game_title = db.Column(db.String(180), nullable=True)
    image_url = db.Column(db.String(1000), nullable=True)
    max_participants = db.Column(db.Integer, nullable=True)
    venue = db.Column(db.String(180), nullable=True)
    rules = db.Column(db.Text, nullable=True)
    stream_url = db.Column(db.String(1000), nullable=True)
    tournament = db.relationship("Tournament", backref=db.backref("details", uselist=False, cascade="all, delete-orphan"))


class DirectMessage(db.Model):
    __tablename__ = "direct_messages"
    __table_args__ = (
        Index("ix_dm_conversation_created", "sender_id", "recipient_id", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    read_at = db.Column(db.DateTime(timezone=True), nullable=True)
    sender = db.relationship("User", foreign_keys=[sender_id])
    recipient = db.relationship("User", foreign_keys=[recipient_id])


class Achievement(db.Model):
    __tablename__ = "achievements"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    awarded_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    image_url = db.Column(db.String(1000), nullable=True)
    animation_url = db.Column(db.String(1000), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    user = db.relationship("User", foreign_keys=[user_id])
    awarded_by = db.relationship("User", foreign_keys=[awarded_by_id])


class Clip(db.Model):
    __tablename__ = "clips"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    awarded_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title = db.Column(db.String(140), nullable=False)
    url = db.Column(db.String(1000), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    user = db.relationship("User", foreign_keys=[user_id])
    awarded_by = db.relationship("User", foreign_keys=[awarded_by_id])


class CommunityPost(db.Model):
    __tablename__ = "community_posts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    body = db.Column(db.String(2000), nullable=False)
    clip_url = db.Column(db.String(1000), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    user = db.relationship("User")
