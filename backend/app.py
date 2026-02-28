import os
import sys

if __package__ is None or __package__ == "":
	project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
	if project_root not in sys.path:
		sys.path.insert(0, project_root)

from flask import Flask
from flask_login import LoginManager

from backend.database.db_init import db
from backend.models.user import User
from backend.models.thought import Thought
from backend.routes.analysis_routes import analysis_bp
from backend.routes.auth_routes import auth_bp


def create_app() -> Flask:
	app = Flask(
		__name__,
		template_folder="../frontend/templates",
		static_folder="../frontend/static",
	)

	base_dir = os.path.abspath(os.path.dirname(__file__))
	db_path = os.path.join(base_dir, "cognaware.db")

	app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-in-production")
	app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
	app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

	db.init_app(app)

	login_manager = LoginManager()
	login_manager.login_view = "auth.login"
	login_manager.login_message = "Please log in to access this page."
	login_manager.login_message_category = "warning"
	login_manager.init_app(app)

	@login_manager.user_loader
	def load_user(user_id: str):
		return db.session.get(User, int(user_id))

	app.register_blueprint(auth_bp)
	app.register_blueprint(analysis_bp)

	with app.app_context():
		db.create_all()

	return app


app = create_app()


if __name__ == "__main__":
	app.run(debug=True)
