from datetime import datetime
from . import db

class Chat(db.Model):
    __tablename__ = "chats"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, default="New Chat")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    messages = db.relationship("Message", backref="chat", cascade="all, delete", lazy=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)