from datetime import datetime

from backend.database.db_init import db


class Thought(db.Model):
	__tablename__ = "thoughts"

	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
	text = db.Column(db.Text, nullable=False)
	results = db.Column(db.Text, nullable=False)
	created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

	def __repr__(self) -> str:
		return f"<Thought {self.id}>"
