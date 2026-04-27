from collections import defaultdict
from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from . import db
from .models import Event, PmcAchievement, Post, User
from .storage import upload_cover_to_supabase, upload_pmc_pdf_to_supabase
from .utils import slugify

site_bp = Blueprint("site", __name__)


@site_bp.get("/")
def home():
    latest = (
        Post.query.filter_by(is_published=True)
        .order_by(Post.published_at.desc())
        .limit(6)
        .all()
    )
    return render_template("home.html", latest=latest)


@site_bp.get("/about")
def about():
    return render_template("about.html")


@site_bp.get("/contact")
def contact():
    return render_template("contact.html")


@site_bp.get("/events")
def events():
    items = (
        Event.query.filter_by(is_published=True)
        .order_by(
            Event.starts_at.desc().nullslast(),  # type: ignore[attr-defined]
            Event.published_at.desc(),
        )
        .all()
    )
    return render_template("events/index.html", items=items)


@site_bp.get("/events/<slug>")
def events_detail(slug: str):
    item = Event.query.filter_by(slug=slug, is_published=True).first()
    if not item:
        abort(404)
    return render_template("events/detail.html", item=item)


@site_bp.get("/centers/research")
def center_research():
    return render_template("centers/research.html")


@site_bp.get("/centers/education")
def center_education():
    return render_template("centers/education.html")


@site_bp.get("/centers/content-provider")
def center_content_provider():
    return render_template("centers/content_provider.html")


@site_bp.get("/centers/publishing")
def center_publishing():
    return render_template("centers/publishing.html")


@site_bp.get("/pmc")
def pmc():
    rows = (
        PmcAchievement.query.filter_by(is_published=True)
        .order_by(PmcAchievement.fiscal_year.desc(), PmcAchievement.published_at.desc())
        .all()
    )
    by_year = defaultdict(list)
    for row in rows:
        by_year[row.fiscal_year].append(row)
    years_desc = sorted(by_year.keys(), reverse=True)
    return render_template(
        "pmc.html",
        pmc_by_year=dict(by_year),
        pmc_years=years_desc,
    )


@site_bp.get("/projects")
def projects():
    return render_template("projects_archive.html")


@site_bp.get("/news")
def news():
    posts = (
        Post.query.filter_by(is_published=True)
        .order_by(Post.published_at.desc())
        .all()
    )
    return render_template("news/index.html", posts=posts)


@site_bp.get("/news/<slug>")
def news_detail(slug: str):
    post = Post.query.filter_by(slug=slug, is_published=True).first()
    if not post:
        abort(404)
    return render_template("news/detail.html", post=post)


def _require_admin():
    if not current_user.is_authenticated:
        abort(401)
    if not getattr(current_user, "is_admin", False):
        abort(403)


def _can_edit_post(post: Post) -> bool:
    if not current_user.is_authenticated:
        return False
    if getattr(current_user, "is_admin", False):
        return True
    return post.author_id == current_user.id


def _can_edit_pmc(item: PmcAchievement) -> bool:
    if not current_user.is_authenticated:
        return False
    if getattr(current_user, "is_admin", False):
        return True
    return item.author_id == current_user.id


def _can_edit_event(item: Event) -> bool:
    if not current_user.is_authenticated:
        return False
    if getattr(current_user, "is_admin", False):
        return True
    return item.author_id == current_user.id


@site_bp.get("/dashboard/events")
@login_required
def dashboard_events():
    if getattr(current_user, "is_admin", False):
        items = (
            Event.query.order_by(
                Event.starts_at.desc().nullslast(),  # type: ignore[attr-defined]
                Event.published_at.desc(),
            ).all()
        )
    else:
        items = (
            Event.query.filter_by(author_id=current_user.id)
            .order_by(
                Event.starts_at.desc().nullslast(),  # type: ignore[attr-defined]
                Event.published_at.desc(),
            )
            .all()
        )
    return render_template("admin/events.html", items=items)


@site_bp.get("/dashboard/events/new")
@login_required
def dashboard_events_new():
    return render_template("admin/event_form.html", item=None)


@site_bp.post("/dashboard/events/new")
@login_required
def dashboard_events_new_post():
    title = (request.form.get("title") or "").strip()
    summary = (request.form.get("summary") or "").strip() or None
    body = (request.form.get("body") or "").strip()
    cover_image = (request.form.get("cover_image") or "").strip() or None
    cover_file = request.files.get("cover_file")
    is_published = request.form.get("is_published") == "on"

    starts_at_raw = (request.form.get("starts_at") or "").strip()
    ends_at_raw = (request.form.get("ends_at") or "").strip()
    location = (request.form.get("location") or "").strip() or None
    registration_url = (request.form.get("registration_url") or "").strip() or None

    starts_at = None
    ends_at = None
    if starts_at_raw:
        try:
            starts_at = datetime.fromisoformat(starts_at_raw)
        except ValueError:
            starts_at = None
    if ends_at_raw:
        try:
            ends_at = datetime.fromisoformat(ends_at_raw)
        except ValueError:
            ends_at = None

    if not title or not body:
        flash("Title and details are required.", "danger")
        return redirect(url_for("site.dashboard_events_new"))

    if starts_at_raw and not starts_at:
        flash("Start date/time must be valid.", "danger")
        return redirect(url_for("site.dashboard_events_new"))
    if ends_at_raw and not ends_at:
        flash("End date/time must be valid.", "danger")
        return redirect(url_for("site.dashboard_events_new"))
    if starts_at and ends_at and ends_at < starts_at:
        flash("End date/time must be after start.", "danger")
        return redirect(url_for("site.dashboard_events_new"))

    uploaded_url = upload_cover_to_supabase(cover_file)
    if uploaded_url:
        cover_image = uploaded_url

    base_slug = slugify(title)
    slug = base_slug
    n = 2
    while Event.query.filter_by(slug=slug).first():
        slug = f"{base_slug}-{n}"
        n += 1

    item = Event(
        title=title,
        slug=slug,
        summary=summary,
        body=body,
        starts_at=starts_at,
        ends_at=ends_at,
        location=location,
        registration_url=registration_url,
        cover_image=cover_image,
        is_published=is_published,
        published_at=datetime.utcnow(),
        author_id=current_user.id,
    )
    db.session.add(item)
    db.session.commit()
    flash("Event created.", "success")
    return redirect(url_for("site.dashboard_events"))


@site_bp.get("/dashboard/events/<int:item_id>/edit")
@login_required
def dashboard_events_edit(item_id: int):
    item = db.session.get(Event, item_id)
    if not item:
        abort(404)
    if not _can_edit_event(item):
        abort(403)
    return render_template("admin/event_form.html", item=item)


@site_bp.post("/dashboard/events/<int:item_id>/edit")
@login_required
def dashboard_events_edit_post(item_id: int):
    item = db.session.get(Event, item_id)
    if not item:
        abort(404)
    if not _can_edit_event(item):
        abort(403)

    title = (request.form.get("title") or "").strip()
    summary = (request.form.get("summary") or "").strip() or None
    body = (request.form.get("body") or "").strip()
    cover_image = (request.form.get("cover_image") or "").strip() or None
    cover_file = request.files.get("cover_file")
    is_published = request.form.get("is_published") == "on"

    starts_at_raw = (request.form.get("starts_at") or "").strip()
    ends_at_raw = (request.form.get("ends_at") or "").strip()
    location = (request.form.get("location") or "").strip() or None
    registration_url = (request.form.get("registration_url") or "").strip() or None

    starts_at = None
    ends_at = None
    if starts_at_raw:
        try:
            starts_at = datetime.fromisoformat(starts_at_raw)
        except ValueError:
            starts_at = None
    if ends_at_raw:
        try:
            ends_at = datetime.fromisoformat(ends_at_raw)
        except ValueError:
            ends_at = None

    if not title or not body:
        flash("Title and details are required.", "danger")
        return redirect(url_for("site.dashboard_events_edit", item_id=item_id))

    if starts_at_raw and not starts_at:
        flash("Start date/time must be valid.", "danger")
        return redirect(url_for("site.dashboard_events_edit", item_id=item_id))
    if ends_at_raw and not ends_at:
        flash("End date/time must be valid.", "danger")
        return redirect(url_for("site.dashboard_events_edit", item_id=item_id))
    if starts_at and ends_at and ends_at < starts_at:
        flash("End date/time must be after start.", "danger")
        return redirect(url_for("site.dashboard_events_edit", item_id=item_id))

    uploaded_url = upload_cover_to_supabase(cover_file)
    if uploaded_url:
        cover_image = uploaded_url

    item.title = title
    item.summary = summary
    item.body = body
    item.starts_at = starts_at
    item.ends_at = ends_at
    item.location = location
    item.registration_url = registration_url
    item.cover_image = cover_image
    item.is_published = is_published
    db.session.commit()
    flash("Event updated.", "success")
    return redirect(url_for("site.dashboard_events"))


@site_bp.post("/dashboard/events/<int:item_id>/delete")
@login_required
def dashboard_events_delete(item_id: int):
    _require_admin()
    item = db.session.get(Event, item_id)
    if not item:
        abort(404)
    db.session.delete(item)
    db.session.commit()
    flash("Event deleted.", "warning")
    return redirect(url_for("site.dashboard_events"))


@site_bp.get("/dashboard/pmc-achievements")
@login_required
def dashboard_pmc_achievements():
    if getattr(current_user, "is_admin", False):
        items = (
            PmcAchievement.query.order_by(
                PmcAchievement.fiscal_year.desc(), PmcAchievement.published_at.desc()
            ).all()
        )
    else:
        items = (
            PmcAchievement.query.filter_by(author_id=current_user.id)
            .order_by(
                PmcAchievement.fiscal_year.desc(), PmcAchievement.published_at.desc()
            )
            .all()
        )
    return render_template("admin/pmc_achievements.html", items=items)


@site_bp.get("/dashboard/pmc-achievements/new")
@login_required
def dashboard_pmc_achievements_new():
    return render_template("admin/pmc_achievement_form.html", item=None)


@site_bp.post("/dashboard/pmc-achievements/new")
@login_required
def dashboard_pmc_achievements_new_post():
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip() or None
    year_raw = (request.form.get("fiscal_year") or "").strip()
    is_published = request.form.get("is_published") == "on"
    pdf_file = request.files.get("pdf_file")

    try:
        fiscal_year = int(year_raw)
    except ValueError:
        fiscal_year = 0

    if not title or fiscal_year < 2019 or fiscal_year > 2025:
        flash("Title and a valid year (2019–2025) are required.", "danger")
        return redirect(url_for("site.dashboard_pmc_achievements_new"))

    pdf_url = upload_pmc_pdf_to_supabase(pdf_file)
    if not pdf_url:
        flash("A PDF file is required (Supabase Storage must be configured for uploads).", "danger")
        return redirect(url_for("site.dashboard_pmc_achievements_new"))

    item = PmcAchievement(
        fiscal_year=fiscal_year,
        title=title,
        description=description,
        pdf_url=pdf_url,
        is_published=is_published,
        published_at=datetime.utcnow(),
        author_id=current_user.id,
    )
    db.session.add(item)
    db.session.commit()
    flash("Achievement added.", "success")
    return redirect(url_for("site.dashboard_pmc_achievements"))


@site_bp.get("/dashboard/pmc-achievements/<int:item_id>/edit")
@login_required
def dashboard_pmc_achievements_edit(item_id: int):
    item = db.session.get(PmcAchievement, item_id)
    if not item:
        abort(404)
    if not _can_edit_pmc(item):
        abort(403)
    return render_template("admin/pmc_achievement_form.html", item=item)


@site_bp.post("/dashboard/pmc-achievements/<int:item_id>/edit")
@login_required
def dashboard_pmc_achievements_edit_post(item_id: int):
    item = db.session.get(PmcAchievement, item_id)
    if not item:
        abort(404)
    if not _can_edit_pmc(item):
        abort(403)

    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip() or None
    year_raw = (request.form.get("fiscal_year") or "").strip()
    is_published = request.form.get("is_published") == "on"
    pdf_file = request.files.get("pdf_file")

    try:
        fiscal_year = int(year_raw)
    except ValueError:
        fiscal_year = 0

    if not title or fiscal_year < 2019 or fiscal_year > 2025:
        flash("Title and a valid year (2019–2025) are required.", "danger")
        return redirect(url_for("site.dashboard_pmc_achievements_edit", item_id=item_id))

    new_pdf = upload_pmc_pdf_to_supabase(pdf_file)
    if new_pdf:
        item.pdf_url = new_pdf

    if not item.pdf_url:
        flash("A PDF is required. Upload a PDF file.", "danger")
        return redirect(url_for("site.dashboard_pmc_achievements_edit", item_id=item_id))

    item.fiscal_year = fiscal_year
    item.title = title
    item.description = description
    item.is_published = is_published
    db.session.commit()
    flash("Achievement updated.", "success")
    return redirect(url_for("site.dashboard_pmc_achievements"))


@site_bp.post("/dashboard/pmc-achievements/<int:item_id>/delete")
@login_required
def dashboard_pmc_achievements_delete(item_id: int):
    _require_admin()
    item = db.session.get(PmcAchievement, item_id)
    if not item:
        abort(404)
    db.session.delete(item)
    db.session.commit()
    flash("Achievement deleted.", "warning")
    return redirect(url_for("site.dashboard_pmc_achievements"))


@site_bp.get("/admin/posts")
@login_required
def admin_posts_redirect():
    return redirect(url_for("site.dashboard_posts"))


@site_bp.get("/dashboard/posts")
@login_required
def dashboard_posts():
    if getattr(current_user, "is_admin", False):
        posts = Post.query.order_by(Post.published_at.desc()).all()
    else:
        posts = (
            Post.query.filter_by(author_id=current_user.id)
            .order_by(Post.published_at.desc())
            .all()
        )
    return render_template("admin/posts.html", posts=posts)


@site_bp.get("/dashboard/posts/new")
@login_required
def dashboard_posts_new():
    return render_template("admin/post_form.html", post=None)


@site_bp.post("/dashboard/posts/new")
@login_required
def dashboard_posts_new_post():
    title = (request.form.get("title") or "").strip()
    summary = (request.form.get("summary") or "").strip() or None
    body = (request.form.get("body") or "").strip()
    cover_image = (request.form.get("cover_image") or "").strip() or None
    cover_file = request.files.get("cover_file")
    is_published = request.form.get("is_published") == "on"

    if not title or not body:
        flash("Title and body are required.", "danger")
        return redirect(url_for("site.dashboard_posts_new"))

    uploaded_url = upload_cover_to_supabase(cover_file)
    if uploaded_url:
        cover_image = uploaded_url

    base_slug = slugify(title)
    slug = base_slug
    n = 2
    while Post.query.filter_by(slug=slug).first():
        slug = f"{base_slug}-{n}"
        n += 1

    post = Post(
        title=title,
        slug=slug,
        summary=summary,
        body=body,
        cover_image=cover_image,
        is_published=is_published,
        published_at=datetime.utcnow(),
        author_id=current_user.id,
    )
    db.session.add(post)
    db.session.commit()
    flash("Post created.", "success")
    return redirect(url_for("site.dashboard_posts"))


@site_bp.get("/dashboard/posts/<int:post_id>/edit")
@login_required
def dashboard_posts_edit(post_id: int):
    post = db.session.get(Post, post_id)
    if not post:
        abort(404)
    if not _can_edit_post(post):
        abort(403)
    return render_template("admin/post_form.html", post=post)


@site_bp.post("/dashboard/posts/<int:post_id>/edit")
@login_required
def dashboard_posts_edit_post(post_id: int):
    post = db.session.get(Post, post_id)
    if not post:
        abort(404)
    if not _can_edit_post(post):
        abort(403)

    title = (request.form.get("title") or "").strip()
    summary = (request.form.get("summary") or "").strip() or None
    body = (request.form.get("body") or "").strip()
    cover_image = (request.form.get("cover_image") or "").strip() or None
    cover_file = request.files.get("cover_file")
    is_published = request.form.get("is_published") == "on"

    if not title or not body:
        flash("Title and body are required.", "danger")
        return redirect(url_for("site.dashboard_posts_edit", post_id=post_id))

    uploaded_url = upload_cover_to_supabase(cover_file)
    if uploaded_url:
        cover_image = uploaded_url

    post.title = title
    post.summary = summary
    post.body = body
    post.cover_image = cover_image
    post.is_published = is_published
    db.session.commit()
    flash("Post updated.", "success")
    return redirect(url_for("site.dashboard_posts"))


@site_bp.post("/dashboard/posts/<int:post_id>/delete")
@login_required
def dashboard_posts_delete(post_id: int):
    _require_admin()
    post = db.session.get(Post, post_id)
    if not post:
        abort(404)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted.", "warning")
    return redirect(url_for("site.dashboard_posts"))


@site_bp.get("/admin/users")
@login_required
def admin_users():
    _require_admin()
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users)


@site_bp.get("/admin/users/new")
@login_required
def admin_users_new():
    _require_admin()
    return render_template("admin/user_form.html", user=None)


@site_bp.post("/admin/users/new")
@login_required
def admin_users_new_post():
    _require_admin()
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    is_admin = request.form.get("is_admin") == "on"

    if not email or not password:
        flash("Email and password are required.", "danger")
        return redirect(url_for("site.admin_users_new"))
    if User.query.filter_by(email=email).first():
        flash("Email already exists.", "danger")
        return redirect(url_for("site.admin_users_new"))

    user = User(email=email, is_admin=is_admin)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash("User created.", "success")
    return redirect(url_for("site.admin_users"))


@site_bp.get("/admin/users/<int:user_id>/edit")
@login_required
def admin_users_edit(user_id: int):
    _require_admin()
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    return render_template("admin/user_form.html", user=user)


@site_bp.post("/admin/users/<int:user_id>/edit")
@login_required
def admin_users_edit_post(user_id: int):
    _require_admin()
    user = db.session.get(User, user_id)
    if not user:
        abort(404)

    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    is_admin = request.form.get("is_admin") == "on"

    if not email:
        flash("Email is required.", "danger")
        return redirect(url_for("site.admin_users_edit", user_id=user_id))
    existing = User.query.filter_by(email=email).first()
    if existing and existing.id != user.id:
        flash("Email already exists.", "danger")
        return redirect(url_for("site.admin_users_edit", user_id=user_id))

    user.email = email
    user.is_admin = is_admin
    if password:
        user.set_password(password)
    db.session.commit()
    flash("User updated.", "success")
    return redirect(url_for("site.admin_users"))


@site_bp.post("/admin/users/<int:user_id>/delete")
@login_required
def admin_users_delete(user_id: int):
    _require_admin()
    if user_id == current_user.id:
        flash("You can’t delete your own account.", "danger")
        return redirect(url_for("site.admin_users"))

    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted.", "warning")
    return redirect(url_for("site.admin_users"))


