"""Hermes User Frontend — Flask + Jinja2 + HTMX."""

import os
import secrets

from flask import Blueprint, Flask, current_app, flash, redirect, render_template, request, send_from_directory, session

from app.api_client import ApiClient

_TEMPLATE_404 = "shared/404.html"
_API_USERS_PROFILE = "/users/profile"
_API_WATCHED = "/users/me/watched"
_TEMPLATE_LOGIN = "auth/login.html"
_URL_LOGIN = "/login"
_URL_NOTIFICATIONS = "/notifications"
_API_NOTIFICATIONS_COUNT = "/notifications/count"
_CONTENT_TYPE_JSON = "application/json"
_ERR_MISSING_FIELDS = "Missing fields"
_ERR_AUTH_REQUIRED = "Authentication required"


bp = Blueprint("frontend", __name__)

_CSRF_EXEMPT = {
    "/auth/firebase-callback",
    "/auth/send-email-otp",
    "/auth/verify-email-otp",
    "/auth/complete-registration",
    "/auth/check-user-providers",
    "/auth/add-password",
    "/auth/check-phone-availability",
}


def _try_refresh():
    """Refresh access token using stored refresh token. Updates session. Returns new token or None."""
    refresh_token = session.get("refresh_token")
    if not refresh_token:
        session.clear()
        return None
    r = current_app.api_client.post("/auth/refresh", json={"refresh_token": refresh_token})
    if not r.ok:
        session.clear()
        return None
    data = r.json()
    session["token"] = data.get("access_token")
    session["refresh_token"] = data.get("refresh_token", refresh_token)
    return session["token"]


def _get_csrf_token():
    """Generate or retrieve a per-session CSRF token."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


def _try_with_refresh(api_fn):
    """Call api_fn(token) -> resp. On 401, refresh the token and retry once.

    Returns (resp, authenticated). If authenticated=False the caller should
    redirect to /login.
    """
    token = session.get("token")
    if not token:
        return None, False
    resp = api_fn(token)
    if resp.status_code == 401:
        token = _try_refresh()
        if not token:
            return None, False
        resp = api_fn(token)
    return resp, True


def _int_arg(name: str, default: int) -> int:
    """Parse an integer query parameter safely."""
    try:
        return int(request.args.get(name, default))
    except (ValueError, TypeError):
        return default


def _handle_profile_update(token: str, form) -> None:
    """Build and submit a profile update payload from POST form data."""
    update = {}
    for f in ("gender", "state", "city", "pincode"):
        val = form.get(f, "").strip()
        update[f] = val or None
    for f in ("is_pwd", "is_ex_serviceman"):
        update[f] = form.get(f) == "on"
    qual = form.get("highest_qualification", "").strip()
    update["highest_qualification"] = qual or None
    update["preferred_states"] = [s.strip() for s in form.get("preferred_states", "").split(",") if s.strip()]
    update["preferred_categories"] = form.getlist("preferred_categories")
    current_app.api_client.put(_API_USERS_PROFILE, token=token, json=update)
    phone = form.get("phone", "").strip()
    if phone:
        current_app.api_client.put("/users/profile/phone", token=token, json={"phone": phone})
    flash("Profile updated.", "success")


def _handle_notification_prefs(token: str, form) -> None:
    """Submit notification preference updates from POST form data."""
    prefs = {
        "email": form.get("email_notif") == "on",
        "push": form.get("push_notif") == "on",
    }
    current_app.api_client.put("/users/me/notification-preferences", token=token, json=prefs)
    flash("Notification preferences saved.", "success")



@bp.app_context_processor
def inject_csrf():
    return {"csrf_token": _get_csrf_token()}


@bp.before_app_request
def validate_csrf():
    if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
        return
    if request.path in _CSRF_EXEMPT:
        return
    form_token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token", "")
    if not form_token or form_token != session.get("csrf_token"):
        flash("Invalid or expired form submission. Please try again.", "error")
        return redirect(request.referrer or "/")


def _not_found(e):
    return render_template(_TEMPLATE_404), 404


def _handle_unexpected_error(exc):
    current_app.logger.error("Unhandled exception: %s", exc, exc_info=True)
    return render_template(_TEMPLATE_404), 500


@bp.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "service": "hermes-frontend"}


@bp.route("/", methods=["GET"])
def index():
    return redirect("/dashboard")


# --- Watched Items Dashboard ---


@bp.route("/dashboard", methods=["GET"])
def dashboard():
    """Watched items dashboard — shows jobs and exams the user is watching."""
    token = session.get("token")
    if not token:
        return render_template(_TEMPLATE_LOGIN, next="/dashboard")

    resp, authed = _try_with_refresh(lambda t: current_app.api_client.get(_API_WATCHED, token=t))
    if not authed:
        return redirect(_URL_LOGIN)
    watched = resp.json() if resp.ok else {"jobs": [], "exams": [], "total": 0}

    return render_template(
        "dashboard/dashboard.html",
        watched_jobs=watched.get("jobs", []),
        watched_exams=watched.get("exams", []),
        total=watched.get("total", 0),
    )


# --- Notifications ---


@bp.route("/notifications", methods=["GET"])
def notifications():
    """Notifications page — requires login."""
    token = session.get("token")
    if not token:
        return render_template(_TEMPLATE_LOGIN, next=_URL_NOTIFICATIONS)

    # Fetch unread count (refresh token on 401)
    count_resp = current_app.api_client.get(_API_NOTIFICATIONS_COUNT, token=token)
    if count_resp.status_code == 401:
        token = _try_refresh()
        if not token:
            return redirect(_URL_LOGIN)
        count_resp = current_app.api_client.get(_API_NOTIFICATIONS_COUNT, token=token)
    unread_count = count_resp.json().get("count", 0) if count_resp.ok else 0

    # Fetch notifications
    params = {"limit": 20, "offset": 0}
    notif_resp = current_app.api_client.get(_URL_NOTIFICATIONS, token=token, params=params)
    notif_data = notif_resp.json() if notif_resp.ok else {"data": [], "pagination": {}}

    return render_template(
        "notifications/notifications.html",
        notifications=notif_data["data"],
        pagination=notif_data.get("pagination", {}),
        unread_count=unread_count,
    )


@bp.route("/notifications/list", methods=["GET"])
def notifications_list_partial():
    """HTMX partial — returns notification rows for load-more."""
    token = session.get("token")
    if not token:
        return "", 401

    params = {"limit": 20, "offset": _int_arg("offset", 0)}
    notif_resp = current_app.api_client.get(_URL_NOTIFICATIONS, token=token, params=params)
    notif_data = notif_resp.json() if notif_resp.ok else {"data": [], "pagination": {}}

    pagination = notif_data.get("pagination", {})
    has_more = pagination.get("has_more", False)
    next_offset = params["offset"] + params["limit"] if has_more else 0

    return render_template(
        "notifications/_notif_items.html",
        notifications=notif_data["data"],
        has_more=has_more,
        next_offset=next_offset,
    )


@bp.route("/notifications/unread-count", methods=["GET"])
def notifications_unread_count():
    """HTMX partial — returns just the unread count number for the badge."""
    token = session.get("token")
    if not token:
        return ""

    resp = current_app.api_client.get(_API_NOTIFICATIONS_COUNT, token=token)
    count = resp.json().get("count", 0) if resp.ok else 0

    if count > 0:
        return str(count)
    return ""


@bp.route("/notifications/<notification_id>/read", methods=["POST"])
def mark_notification_read(notification_id):
    """Mark a notification as read (proxies to backend PUT)."""
    _, authed = _try_with_refresh(lambda t: current_app.api_client.put(f"/notifications/{notification_id}/read", token=t))
    if not authed:
        return redirect(_URL_LOGIN)
    return redirect(_URL_NOTIFICATIONS)


@bp.route("/notifications/read-all", methods=["POST"])
def mark_all_notifications_read():
    """Mark all notifications as read (proxies to backend PUT)."""
    _, authed = _try_with_refresh(lambda t: current_app.api_client.put("/notifications/read-all", token=t))
    if not authed:
        return redirect(_URL_LOGIN)
    return redirect(_URL_NOTIFICATIONS)


@bp.route("/notifications/<notification_id>/delete", methods=["POST"])
def delete_notification(notification_id):
    """Delete a notification (proxies to backend DELETE)."""
    _, authed = _try_with_refresh(lambda t: current_app.api_client.delete(f"/notifications/{notification_id}", token=t))
    if not authed:
        return redirect(_URL_LOGIN)
    return redirect(_URL_NOTIFICATIONS)


@bp.route("/offline", methods=["GET"])
def offline():
    return render_template("shared/offline.html")


# --- Profile ---


@bp.route("/profile", methods=["GET", "POST"])  # NOSONAR
def profile():
    """User profile — view and update preferences, phone, notification settings."""
    token = session.get("token")
    if not token:
        return redirect("/login?next=/profile")

    if request.method == "POST":
        action = request.form.get("action", "profile")
        if action == "profile":
            _handle_profile_update(token, request.form)
        elif action == "notification_prefs":
            _handle_notification_prefs(token, request.form)
        return redirect("/profile")

    resp = current_app.api_client.get(_API_USERS_PROFILE, token=token)
    if resp.status_code == 401:
        token = _try_refresh()
        if not token:
            return redirect(_URL_LOGIN)
        resp = current_app.api_client.get(_API_USERS_PROFILE, token=token)

    user_data = resp.json() if resp.ok else {}
    return render_template("auth/profile.html",
        user=user_data,
        profile=user_data.get("profile", {}),
        firebase_api_key=os.environ.get("FIREBASE_WEB_API_KEY", ""),
        firebase_auth_domain=os.environ.get("FIREBASE_AUTH_DOMAIN", ""),
        firebase_project_id=os.environ.get("FIREBASE_PROJECT_ID", "")
    )


# --- Auth Flows (Firebase) ---


@bp.route("/auth/send-email-otp", methods=["POST"])
def send_email_otp():
    """Proxy: generate and send a 6-digit OTP to the user's email."""
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    full_name = data.get("full_name", "")
    if not email or not full_name:
        return {"error": "Missing email or name"}, 400
    resp = current_app.api_client.post("/auth/send-email-otp", json={"email": email, "full_name": full_name})
    if not resp.ok:
        detail = "Failed to send OTP"
        if resp.headers.get("content-type", "").startswith(_CONTENT_TYPE_JSON):
            detail = resp.json().get("detail", detail)
        return {"error": detail}, resp.status_code
    return {"message": "OTP sent to your email"}, 200


@bp.route("/auth/verify-email-otp", methods=["POST"])
def verify_email_otp():
    """Proxy: verify the 6-digit OTP and return verification token."""
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    otp = data.get("otp", "")
    if not email or not otp:
        return {"error": _ERR_MISSING_FIELDS}, 400
    resp = current_app.api_client.post("/auth/verify-email-otp", json={"email": email, "otp": otp})
    if not resp.ok:
        detail = "Invalid OTP"
        if resp.headers.get("content-type", "").startswith(_CONTENT_TYPE_JSON):
            detail = resp.json().get("detail", detail)
        return {"error": detail}, resp.status_code
    return resp.json(), 200


@bp.route("/auth/complete-registration", methods=["POST"])
def complete_registration():
    """Proxy: complete email/password registration via Firebase Admin SDK."""
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    password = data.get("password", "")
    verification_token = data.get("verification_token", "")
    if not email or not password or not verification_token:
        return {"error": _ERR_MISSING_FIELDS}, 400
    resp = current_app.api_client.post(
        "/auth/complete-registration",
        json={"email": email, "password": password, "verification_token": verification_token},
    )
    if not resp.ok:
        detail = "Registration failed"
        if resp.headers.get("content-type", "").startswith(_CONTENT_TYPE_JSON):
            detail = resp.json().get("detail", detail)
        return {"error": detail}, resp.status_code
    return resp.json(), 200


@bp.route("/auth/check-user-providers", methods=["POST"])
def check_user_providers():
    """Proxy: check which authentication providers a user has."""
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    if not email:
        return {"error": "Email required"}, 400
    resp = current_app.api_client.post("/auth/check-user-providers", json={"email": email})
    if not resp.ok:
        return {"error": "Failed to check providers"}, resp.status_code
    return resp.json(), 200


@bp.route("/auth/add-password", methods=["POST"])
def add_password():
    """Proxy: add password to existing social auth account."""
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    password = data.get("password", "")
    verification_token = data.get("verification_token", "")
    if not email or not password or not verification_token:
        return {"error": _ERR_MISSING_FIELDS}, 400
    resp = current_app.api_client.post(
        "/auth/add-password",
        json={"email": email, "password": password, "verification_token": verification_token},
    )
    if not resp.ok:
        detail = "Failed to add password"
        if resp.headers.get("content-type", "").startswith(_CONTENT_TYPE_JSON):
            detail = resp.json().get("detail", detail)
        return {"error": detail}, resp.status_code
    return resp.json(), 200


@bp.route("/auth/check-phone-availability", methods=["POST"])
def check_phone_availability():
    """Proxy: check if phone number is already registered."""
    data = request.get_json(silent=True) or {}
    phone = data.get("phone", "")
    if not phone:
        return {"error": "Phone number required"}, 400
    resp = current_app.api_client.post("/auth/check-phone-availability", json={"phone": phone})
    if not resp.ok:
        return {"error": "Failed to check phone availability"}, resp.status_code
    return resp.json(), 200


@bp.route("/users/me/profile", methods=["GET"])
def get_user_profile():
    """Proxy: get user profile with phone verification status."""
    resp, ok = _try_with_refresh(lambda token: current_app.api_client.get(_API_USERS_PROFILE, token=token))
    if not ok:
        return redirect(_URL_LOGIN)
    if not resp.ok:
        return {"error": "Failed to fetch profile"}, resp.status_code
    return resp.json(), 200


@bp.route("/users/me/phone", methods=["PUT"])
def update_user_phone():
    """Proxy: update user phone number."""
    data = request.get_json(silent=True) or {}
    phone = data.get("phone", "")
    if not phone:
        return {"error": "Phone number required"}, 400
    resp, ok = _try_with_refresh(lambda token: current_app.api_client.put("/users/profile/phone", token=token, json={"phone": phone}))
    if not ok:
        return {"error": _ERR_AUTH_REQUIRED}, 401
    if not resp.ok:
        detail = "Failed to update phone"
        if resp.headers.get("content-type", "").startswith(_CONTENT_TYPE_JSON):
            detail = resp.json().get("detail", detail)
        return {"error": detail}, resp.status_code
    return resp.json(), 200


@bp.route("/users/me/send-phone-otp", methods=["POST"])
def send_phone_otp():
    """Proxy: trigger phone OTP send."""
    resp, ok = _try_with_refresh(lambda token: current_app.api_client.post("/users/me/send-phone-otp", token=token))
    if not ok:
        return {"error": _ERR_AUTH_REQUIRED}, 401
    if not resp.ok:
        detail = "Failed to send OTP"
        if resp.headers.get("content-type", "").startswith(_CONTENT_TYPE_JSON):
            detail = resp.json().get("detail", detail)
        return {"error": detail}, resp.status_code
    return resp.json(), 200


@bp.route("/users/me/verify-phone-otp", methods=["POST"])
def verify_phone_otp():
    """Proxy: verify phone OTP."""
    data = request.get_json(silent=True) or {}
    otp = data.get("otp", "")
    if not otp:
        return {"error": "OTP required"}, 400
    resp, ok = _try_with_refresh(lambda token: current_app.api_client.post("/users/me/verify-phone-otp", token=token, json={"otp": otp}))
    if not ok:
        return {"error": _ERR_AUTH_REQUIRED}, 401
    if not resp.ok:
        detail = "Invalid OTP"
        if resp.headers.get("content-type", "").startswith(_CONTENT_TYPE_JSON):
            detail = resp.json().get("detail", detail)
        return {"error": detail}, resp.status_code
    return resp.json(), 200


@bp.route("/users/me/set-password", methods=["POST"])
def set_password():
    """Proxy: set password for Google OAuth users."""
    data = request.get_json(silent=True) or {}
    new_password = data.get("new_password", "")
    if not new_password or len(new_password) < 8:
        return {"error": "Password must be at least 8 characters"}, 400
    resp, ok = _try_with_refresh(lambda token: current_app.api_client.post("/users/me/set-password", token=token, json={"new_password": new_password}))
    if not ok:
        return {"error": _ERR_AUTH_REQUIRED}, 401
    if not resp.ok:
        detail = "Failed to set password"
        if resp.headers.get("content-type", "").startswith(_CONTENT_TYPE_JSON):
            detail = resp.json().get("detail", detail)
        return {"error": detail}, resp.status_code
    return resp.json(), 200


@bp.route("/users/me/change-password", methods=["POST"])
def change_password():
    """Proxy: change password for users with existing password."""
    data = request.get_json(silent=True) or {}
    new_password = data.get("new_password", "")
    if not new_password:
        return {"error": "New password required"}, 400
    if len(new_password) < 8:
        return {"error": "New password must be at least 8 characters"}, 400
    resp, ok = _try_with_refresh(lambda token: current_app.api_client.post("/users/me/change-password", token=token, json={"new_password": new_password}))
    if not ok:
        return {"error": _ERR_AUTH_REQUIRED}, 401
    if not resp.ok:
        detail = "Failed to change password"
        if resp.headers.get("content-type", "").startswith(_CONTENT_TYPE_JSON):
            detail = resp.json().get("detail", detail)
        return {"error": detail}, resp.status_code
    return resp.json(), 200


@bp.route("/users/me/link-email-password", methods=["POST"])
def link_email_password():
    """Proxy: link email+password to phone-only account."""
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    password = data.get("password", "")
    if not email or not password:
        return {"error": "Email and password required"}, 400
    if len(password) < 8:
        return {"error": "Password must be at least 8 characters"}, 400
    resp, ok = _try_with_refresh(lambda token: current_app.api_client.post("/users/me/link-email-password", token=token, json={"email": email, "password": password}))
    if not ok:
        return {"error": _ERR_AUTH_REQUIRED}, 401
    if not resp.ok:
        detail = "Failed to link email and password"
        if resp.headers.get("content-type", "").startswith(_CONTENT_TYPE_JSON):
            detail = resp.json().get("detail", detail)
        return {"error": detail}, resp.status_code
    return resp.json(), 200


@bp.route("/auth/firebase-callback", methods=["POST"])
def firebase_callback():
    """Receive Firebase ID token from JS, verify via backend, store JWT in session."""
    data = request.get_json(silent=True) or {}
    id_token = data.get("id_token", "")
    full_name = data.get("full_name")
    if not id_token:
        return {"error": "Missing token"}, 400

    resp = current_app.api_client.post("/auth/verify-token", json={"id_token": id_token, "full_name": full_name})
    if not resp.ok:
        detail = "Authentication failed"
        if resp.headers.get("content-type", "").startswith(_CONTENT_TYPE_JSON):
            detail = resp.json().get("detail", detail)
        return {"error": detail}, resp.status_code

    tokens = resp.json()
    session["token"] = tokens.get("access_token")
    session["refresh_token"] = tokens.get("refresh_token")
    me_resp = current_app.api_client.get(_API_USERS_PROFILE, token=session["token"])
    session["user_name"] = me_resp.json().get("full_name", "") if me_resp.ok else ""
    return {"redirect": "/"}, 200


@bp.route("/login", methods=["GET"])
def login():
    """Render Firebase-powered login page."""
    return render_template(_TEMPLATE_LOGIN,
        next=request.args.get("next", "/"),
        firebase_api_key=os.environ.get("FIREBASE_WEB_API_KEY", ""),
        firebase_auth_domain=os.environ.get("FIREBASE_AUTH_DOMAIN", ""),
        firebase_project_id=os.environ.get("FIREBASE_PROJECT_ID", ""),
    )


@bp.route("/logout", methods=["GET"])
def logout():
    token = session.get("token")
    if token:
        current_app.api_client.post("/auth/logout", token=token)
    session.clear()
    return redirect("/")


@bp.route("/favicon.ico", methods=["GET"])
def favicon():
    """Serve favicon or return 204 if not found."""
    favicon_path = os.path.join(current_app.root_path, "static", "favicon.ico")
    if os.path.exists(favicon_path):
        return send_from_directory(os.path.join(current_app.root_path, "static"), "favicon.ico")
    return "", 204


# ─── Jobs Section ────────────────────────────────────────────────────────


@bp.route("/jobs", methods=["GET"])
def jobs():
    params = {}
    for key in ("q", "qualification_level", "organization"):
        val = request.args.get(key)
        if val:
            params[key] = val
    params["limit"] = min(_int_arg("limit", 20), 100)
    params["offset"] = _int_arg("offset", 0)
    token = session.get("token")
    resp = current_app.api_client.get("/jobs", token=token, params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}
    recommended_jobs = []
    watched_job_ids = set()
    if token:
        rec_resp, authed = _try_with_refresh(
            lambda t: current_app.api_client.get("/jobs/recommended", token=t, params={"limit": 20, "offset": 0})
        )
        if authed and rec_resp and rec_resp.ok:
            recommended_jobs = rec_resp.json().get("data", [])
        w_resp = current_app.api_client.get(_API_WATCHED, token=session.get("token"))
        if w_resp.ok:
            watched_job_ids = {str(j["id"]) for j in w_resp.json().get("jobs", [])}
    return render_template(
        "jobs/list.html",
        jobs=data.get("data", []),
        pagination=data.get("pagination", {}),
        recommended_jobs=recommended_jobs,
        watched_job_ids=watched_job_ids,
        q=request.args.get("q", ""),
        qualification_level=request.args.get("qualification_level", ""),
        organization=request.args.get("organization", ""),
    )


@bp.route("/partials/jobs", methods=["GET"])
def jobs_partial():
    params = {}
    for key in ("q", "qualification_level", "organization"):
        val = request.args.get(key)
        if val:
            params[key] = val
    params["limit"] = min(_int_arg("limit", 20), 100)
    params["offset"] = _int_arg("offset", 0)
    token = session.get("token")
    resp = current_app.api_client.get("/jobs", token=token, params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}
    pagination = data.get("pagination", {})
    has_more = pagination.get("has_more", False)
    next_offset = params["offset"] + params["limit"] if has_more else 0
    return render_template(
        "jobs/_cards.html",
        jobs=data.get("data", []),
        has_more=has_more,
        next_offset=next_offset,
        q=request.args.get("q", ""),
        qualification_level=request.args.get("qualification_level", ""),
        organization=request.args.get("organization", ""),
    )


@bp.route("/jobs/<job_id>", methods=["GET"])
def job_detail(job_id):
    resp = current_app.api_client.get(f"/jobs/{job_id}")
    if not resp.ok:
        return render_template(_TEMPLATE_404), 404
    job = resp.json()
    watching = False
    token = session.get("token")
    if token:
        w_resp = current_app.api_client.get(_API_WATCHED, token=token)
        if w_resp.ok:
            watching = any(str(j["id"]) == job_id for j in w_resp.json().get("jobs", []))
    return render_template("jobs/detail.html", job=job, watching=watching)


@bp.route("/jobs/<job_id>/watch", methods=["POST"])
def watch_job(job_id):
    _, authed = _try_with_refresh(lambda t: current_app.api_client.post(f"/jobs/{job_id}/watch", token=t))
    if not authed:
        return redirect(f"/login?next=/jobs/{job_id}")
    return redirect(request.form.get("next") or request.referrer or f"/jobs/{job_id}")


@bp.route("/jobs/<job_id>/unwatch", methods=["POST"])
def unwatch_job(job_id):
    _, authed = _try_with_refresh(lambda t: current_app.api_client.delete(f"/jobs/{job_id}/watch", token=t))
    if not authed:
        return redirect(f"/login?next=/jobs/{job_id}")
    return redirect(request.form.get("next") or request.referrer or f"/jobs/{job_id}")


# ─── Admit Cards Section ─────────────────────────────────────────────────


@bp.route("/admit-cards", methods=["GET"])
def admit_cards():
    params = {"limit": min(_int_arg("limit", 20), 100), "offset": _int_arg("offset", 0)}
    token = session.get("token")
    resp = current_app.api_client.get("/admit-cards", params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}
    recommended_cards = []
    if token:
        rec_resp, authed = _try_with_refresh(
            lambda t: current_app.api_client.get("/admit-cards/recommended", token=t, params={"limit": 20, "offset": 0})
        )
        if authed and rec_resp and rec_resp.ok:
            recommended_cards = rec_resp.json().get("data", [])
    return render_template(
        "admit_cards/list.html",
        cards=data.get("data", []),
        pagination=data.get("pagination", {}),
        recommended_cards=recommended_cards,
    )


@bp.route("/partials/admit-cards", methods=["GET"])
def admit_cards_partial():
    params = {"limit": min(_int_arg("limit", 20), 100), "offset": _int_arg("offset", 0)}
    resp = current_app.api_client.get("/admit-cards", params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}
    pagination = data.get("pagination", {})
    has_more = pagination.get("has_more", False)
    next_offset = params["offset"] + params["limit"] if has_more else 0
    return render_template(
        "admit_cards/_cards.html",
        cards=data.get("data", []),
        has_more=has_more,
        next_offset=next_offset,
    )


@bp.route("/admit-cards/<card_id>", methods=["GET"])
def admit_card_detail(card_id):
    resp = current_app.api_client.get(f"/admit-cards/{card_id}")
    if not resp.ok:
        return render_template(_TEMPLATE_404), 404
    return render_template("admit_cards/detail.html", card=resp.json())


# ─── Answer Keys Section ─────────────────────────────────────────────────


@bp.route("/answer-keys", methods=["GET"])
def answer_keys():
    params = {"limit": min(_int_arg("limit", 20), 100), "offset": _int_arg("offset", 0)}
    token = session.get("token")
    resp = current_app.api_client.get("/answer-keys", params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}
    recommended_keys = []
    if token:
        rec_resp, authed = _try_with_refresh(
            lambda t: current_app.api_client.get("/answer-keys/recommended", token=t, params={"limit": 20, "offset": 0})
        )
        if authed and rec_resp and rec_resp.ok:
            recommended_keys = rec_resp.json().get("data", [])
    return render_template(
        "answer_keys/list.html",
        keys=data.get("data", []),
        pagination=data.get("pagination", {}),
        recommended_keys=recommended_keys,
    )


@bp.route("/partials/answer-keys", methods=["GET"])
def answer_keys_partial():
    params = {"limit": min(_int_arg("limit", 20), 100), "offset": _int_arg("offset", 0)}
    resp = current_app.api_client.get("/answer-keys", params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}
    pagination = data.get("pagination", {})
    has_more = pagination.get("has_more", False)
    next_offset = params["offset"] + params["limit"] if has_more else 0
    return render_template(
        "answer_keys/_cards.html",
        keys=data.get("data", []),
        has_more=has_more,
        next_offset=next_offset,
    )


@bp.route("/answer-keys/<key_id>", methods=["GET"])
def answer_key_detail(key_id):
    resp = current_app.api_client.get(f"/answer-keys/{key_id}")
    if not resp.ok:
        return render_template(_TEMPLATE_404), 404
    return render_template("answer_keys/detail.html", key=resp.json())


# ─── Results Section ─────────────────────────────────────────────────────


@bp.route("/results", methods=["GET"])
def results():
    params = {"limit": min(_int_arg("limit", 20), 100), "offset": _int_arg("offset", 0)}
    token = session.get("token")
    resp = current_app.api_client.get("/results", params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}
    recommended_results = []
    if token:
        rec_resp, authed = _try_with_refresh(
            lambda t: current_app.api_client.get("/results/recommended", token=t, params={"limit": 20, "offset": 0})
        )
        if authed and rec_resp and rec_resp.ok:
            recommended_results = rec_resp.json().get("data", [])
    return render_template(
        "results/list.html",
        results=data.get("data", []),
        pagination=data.get("pagination", {}),
        recommended_results=recommended_results,
    )


@bp.route("/partials/results", methods=["GET"])
def results_partial():
    params = {"limit": min(_int_arg("limit", 20), 100), "offset": _int_arg("offset", 0)}
    resp = current_app.api_client.get("/results", params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}
    pagination = data.get("pagination", {})
    has_more = pagination.get("has_more", False)
    next_offset = params["offset"] + params["limit"] if has_more else 0
    return render_template(
        "results/_cards.html",
        results=data.get("data", []),
        has_more=has_more,
        next_offset=next_offset,
    )


@bp.route("/results/<result_id>", methods=["GET"])
def result_detail(result_id):
    resp = current_app.api_client.get(f"/results/{result_id}")
    if not resp.ok:
        return render_template(_TEMPLATE_404), 404
    return render_template("results/detail.html", result=resp.json())


# ─── Entrance Exams Section ──────────────────────────────────────────────


@bp.route("/entrance-exams", methods=["GET"])
def entrance_exams():
    params = {}
    for key in ("q", "stream", "exam_type"):
        val = request.args.get(key)
        if val:
            params[key] = val
    params["limit"] = min(_int_arg("limit", 20), 100)
    params["offset"] = _int_arg("offset", 0)
    token = session.get("token")
    resp = current_app.api_client.get("/entrance-exams", token=token, params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}
    recommended_exams = []
    watched_exam_ids = set()
    if token:
        rec_resp, authed = _try_with_refresh(
            lambda t: current_app.api_client.get("/entrance-exams/recommended", token=t, params={"limit": 20, "offset": 0})
        )
        if authed and rec_resp and rec_resp.ok:
            recommended_exams = rec_resp.json().get("data", [])
        w_resp = current_app.api_client.get(_API_WATCHED, token=session.get("token"))
        if w_resp.ok:
            watched_exam_ids = {str(e["id"]) for e in w_resp.json().get("exams", [])}
    return render_template(
        "entrance_exams/list.html",
        exams=data.get("data", []),
        pagination=data.get("pagination", {}),
        recommended_exams=recommended_exams,
        watched_exam_ids=watched_exam_ids,
        q=request.args.get("q", ""),
        stream=request.args.get("stream", ""),
        exam_type=request.args.get("exam_type", ""),
    )


@bp.route("/partials/entrance-exams", methods=["GET"])
def entrance_exams_partial():
    params = {}
    for key in ("q", "stream", "exam_type"):
        val = request.args.get(key)
        if val:
            params[key] = val
    params["limit"] = min(_int_arg("limit", 20), 100)
    params["offset"] = _int_arg("offset", 0)
    resp = current_app.api_client.get("/entrance-exams", params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}
    pagination = data.get("pagination", {})
    has_more = pagination.get("has_more", False)
    next_offset = params["offset"] + params["limit"] if has_more else 0
    return render_template(
        "entrance_exams/_cards.html",
        exams=data.get("data", []),
        has_more=has_more,
        next_offset=next_offset,
        q=request.args.get("q", ""),
        stream=request.args.get("stream", ""),
        exam_type=request.args.get("exam_type", ""),
    )


@bp.route("/entrance-exams/<exam_id>", methods=["GET"])
def entrance_exam_detail(exam_id):
    resp = current_app.api_client.get(f"/entrance-exams/{exam_id}")
    if not resp.ok:
        return render_template(_TEMPLATE_404), 404
    exam = resp.json()
    watching = False
    token = session.get("token")
    if token:
        w_resp = current_app.api_client.get(_API_WATCHED, token=token)
        if w_resp.ok:
            watching = any(str(e["id"]) == exam_id for e in w_resp.json().get("exams", []))
    return render_template("entrance_exams/detail.html", exam=exam, watching=watching)


@bp.route("/entrance-exams/<exam_id>/watch", methods=["POST"])
def watch_exam(exam_id):
    _, authed = _try_with_refresh(lambda t: current_app.api_client.post(f"/entrance-exams/{exam_id}/watch", token=t))
    if not authed:
        return redirect(f"/login?next=/entrance-exams/{exam_id}")
    return redirect(request.form.get("next") or request.referrer or f"/entrance-exams/{exam_id}")


@bp.route("/entrance-exams/<exam_id>/unwatch", methods=["POST"])
def unwatch_exam(exam_id):
    _, authed = _try_with_refresh(lambda t: current_app.api_client.delete(f"/entrance-exams/{exam_id}/watch", token=t))
    if not authed:
        return redirect(f"/login?next=/entrance-exams/{exam_id}")
    return redirect(request.form.get("next") or request.referrer or f"/entrance-exams/{exam_id}")


def create_app():
    app = Flask(__name__)  # NOSONAR
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")
    app.api_client = ApiClient(
        base_url=os.environ.get("BACKEND_API_URL", "http://localhost:8000/api/v1")
    )
    app.register_blueprint(bp)
    app.register_error_handler(404, _not_found)
    app.register_error_handler(Exception, _handle_unexpected_error)
    return app


# Flask CLI entry point
app = create_app()
