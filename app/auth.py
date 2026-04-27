import os

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from . import db
from .models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/login")
def login():
    return render_template("auth/login.html")


@auth_bp.post("/login")
def login_post():
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        flash("Invalid email or password.", "danger")
        return redirect(url_for("auth.login"))

    login_user(user)
    return redirect(url_for("site.dashboard_posts"))


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("site.home"))


@auth_bp.get("/bootstrap-admin")
def bootstrap_admin():
    """
    One-time helper for local/dev only.
    Set env:
      BOOTSTRAP_ADMIN_TOKEN
      ADMIN_EMAIL
      ADMIN_PASSWORD
    Then visit:
      /auth/bootstrap-admin?token=...
    """
    token = request.args.get("token")
    expected = (os.environ.get("BOOTSTRAP_ADMIN_TOKEN") or "").strip()
    if not expected or token != expected:
        return ("Not found", 404)

    email = (os.environ.get("ADMIN_EMAIL") or "").strip().lower()
    password = os.environ.get("ADMIN_PASSWORD") or ""
    if not email or not password:
        return ("Missing ADMIN_EMAIL / ADMIN_PASSWORD", 400)

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, is_admin=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return ("Admin created.", 201)

    user.is_admin = True
    user.set_password(password)
    db.session.commit()
    return ("Admin updated.", 200)

