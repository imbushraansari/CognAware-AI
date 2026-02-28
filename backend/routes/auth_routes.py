from urllib.parse import urljoin, urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from backend.database.db_init import db
from backend.models.user import User

auth_bp = Blueprint("auth", __name__)


def _is_safe_next_url(target: str) -> bool:
	if not target:
		return False
	ref_url = urlparse(request.host_url)
	test_url = urlparse(urljoin(request.host_url, target))
	return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


@auth_bp.route("/")
def home_redirect():
	if current_user.is_authenticated:
		return redirect(url_for("analysis.dashboard"))
	return render_template("home.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
	if current_user.is_authenticated:
		return redirect(url_for("analysis.dashboard"))

	if request.method == "POST":
		name = request.form.get("name", "").strip()
		email = request.form.get("email", "").strip().lower()
		password = request.form.get("password", "")

		if not name or not email or not password:
			flash("Please fill out all fields.", "warning")
			return render_template("register.html")

		existing_user = User.query.filter_by(email=email).first()
		if existing_user:
			flash("An account with this email already exists.", "danger")
			return render_template("register.html")

		user = User(name=name, email=email)
		user.set_password(password)
		db.session.add(user)
		db.session.commit()
		login_user(user)

		flash("Registration successful. You are now logged in.", "success")
		return redirect(url_for("analysis.dashboard"))

	return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
	if current_user.is_authenticated:
		return redirect(url_for("analysis.dashboard"))

	if request.method == "POST":
		email = request.form.get("email", "").strip().lower()
		password = request.form.get("password", "")

		if not email or not password:
			flash("Email and password are required.", "warning")
			return render_template("login.html")

		user = User.query.filter_by(email=email).first()
		if not user or not user.check_password(password):
			flash("Invalid email or password.", "danger")
			return render_template("login.html")

		login_user(user)
		flash("You are now logged in.", "success")

		next_url = request.args.get("next")
		if next_url and _is_safe_next_url(next_url):
			return redirect(next_url)
		return redirect(url_for("analysis.dashboard"))

	return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
	logout_user()
	flash("You have been logged out.", "info")
	return redirect(url_for("auth.home_redirect"))
