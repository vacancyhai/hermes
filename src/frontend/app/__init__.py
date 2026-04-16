"""Hermes User Frontend — Flask + Jinja2 + HTMX."""

import os
import secrets
import uuid as _uuid
from urllib.parse import urlparse

from flask import Blueprint, Flask, current_app, flash, redirect, render_template, request, send_from_directory, session

from app._flask_utils import _int_arg
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
_API_JOBS = "/jobs"
_API_ADMISSIONS = "/admissions"
_API_ADMIT_CARDS = "/admit-cards"
_API_ANSWER_KEYS = "/answer-keys"
_API_RESULTS = "/results"
_PATH_RECOMMENDED = "/recommended"


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
    "/users/me/phone",
    "/users/me/send-phone-otp",
    "/users/me/verify-phone-otp",
    "/users/me/set-password",
    "/users/me/change-password",
    "/users/me/link-email-password",
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


def _safe_back(fallback: str = "/") -> str:
    """Return the referrer URL only if it is same-origin, else return fallback.

    Prevents open-redirect attacks where an attacker sets Referer to an
    external URL.
    """
    referrer = request.referrer
    if referrer:
        ref = urlparse(referrer)
        own = urlparse(request.host_url)
        if ref.scheme == own.scheme and ref.netloc == own.netloc:
            return referrer
    return fallback


def _fetch_watched_ids():
    """Return (watched_job_ids, watched_admission_ids) sets for the current user.

    Uses _try_with_refresh so expired tokens are handled. Returns empty sets
    when the user is not logged in or the request fails.
    """
    w_resp, authed = _try_with_refresh(
        lambda t: current_app.api_client.get(_API_WATCHED, token=t)
    )
    if not authed or not w_resp or not w_resp.ok:
        return set(), set()
    data = w_resp.json()
    return (
        {str(j["id"]) for j in data.get("jobs", [])},
        {str(e["id"]) for e in data.get("admissions", [])},
    )



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
        return redirect("/")


def _not_found(e):
    return render_template(_TEMPLATE_404), 404


def _handle_unexpected_error(exc):
    current_app.logger.error("Unhandled exception: %s", exc, exc_info=True)
    return render_template(_TEMPLATE_404), 500


@bp.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "service": "hermes-frontend"}


# --- Watched Items Dashboard ---


@bp.route("/", methods=["GET"])
def dashboard():
    """Dashboard — latest 12 items per section + watched items for logged-in users."""
    _latest_params = {"limit": 12, "offset": 0}

    # Fetch latest 12 for each section (public, no auth needed)
    jobs_resp = current_app.api_client.get(_API_JOBS, params=_latest_params)
    latest_jobs = jobs_resp.json().get("data", []) if jobs_resp.ok else []

    admissions_resp = current_app.api_client.get(_API_ADMISSIONS, params=_latest_params)
    latest_admissions = admissions_resp.json().get("data", []) if admissions_resp.ok else []

    admit_cards_resp = current_app.api_client.get(_API_ADMIT_CARDS, params=_latest_params)
    latest_admit_cards = admit_cards_resp.json().get("data", []) if admit_cards_resp.ok else []

    answer_keys_resp = current_app.api_client.get(_API_ANSWER_KEYS, params=_latest_params)
    latest_answer_keys = answer_keys_resp.json().get("data", []) if answer_keys_resp.ok else []

    results_resp = current_app.api_client.get(_API_RESULTS, params=_latest_params)
    latest_results = results_resp.json().get("data", []) if results_resp.ok else []

    exam_resp = current_app.api_client.get("/exam-reminders")
    upcoming_exams = exam_resp.json().get("data", [])[:8] if exam_resp.ok else []

    token = session.get("token")
    if not token:
        return render_template(
            "dashboard/home.html",
            latest_jobs=latest_jobs,
            latest_admissions=latest_admissions,
            latest_admit_cards=latest_admit_cards,
            latest_answer_keys=latest_answer_keys,
            latest_results=latest_results,
            upcoming_exams=upcoming_exams,
            watched_jobs=[],
            watched_admissions=[],
            watched_job_ids=set(),
            watched_admission_ids=set(),
            total=0,
            logged_in=False,
            firebase_api_key=os.environ.get("FIREBASE_WEB_API_KEY", ""),
            firebase_auth_domain=os.environ.get("FIREBASE_AUTH_DOMAIN", ""),
            firebase_project_id=os.environ.get("FIREBASE_PROJECT_ID", ""),
        )

    resp, authed = _try_with_refresh(lambda t: current_app.api_client.get(_API_WATCHED, token=t))
    if not authed:
        return redirect(_URL_LOGIN)
    watched = resp.json() if resp.ok else {"jobs": [], "admissions": [], "total": 0}
    watched_job_ids = {str(j["id"]) for j in watched.get("jobs", [])}
    watched_admission_ids = {str(e["id"]) for e in watched.get("admissions", [])}


    return render_template(
        "dashboard/home.html",
        latest_jobs=latest_jobs,
        latest_admissions=latest_admissions,
        latest_admit_cards=latest_admit_cards,
        latest_answer_keys=latest_answer_keys,
        latest_results=latest_results,
        upcoming_exams=upcoming_exams,
        watched_jobs=watched.get("jobs", []),
        watched_admissions=watched.get("admissions", []),
        watched_job_ids=watched_job_ids,
        watched_admission_ids=watched_admission_ids,
        total=watched.get("total", 0),
        logged_in=True,
    )


# --- Notifications ---


@bp.route("/notifications", methods=["GET"])
def notifications():
    """Notifications page — requires login."""
    if not session.get("token"):
        return render_template(_TEMPLATE_LOGIN, next=_URL_NOTIFICATIONS,
            firebase_api_key=os.environ.get("FIREBASE_WEB_API_KEY", ""),
            firebase_auth_domain=os.environ.get("FIREBASE_AUTH_DOMAIN", ""),
            firebase_project_id=os.environ.get("FIREBASE_PROJECT_ID", ""),
        )

    params = {"limit": 20, "offset": 0}
    notif_resp, authed = _try_with_refresh(
        lambda t: current_app.api_client.get(_URL_NOTIFICATIONS, token=t, params=params)
    )
    if not authed:
        return redirect(_URL_LOGIN)
    notif_data = notif_resp.json() if notif_resp.ok else {"data": [], "pagination": {}}

    count_resp, _ = _try_with_refresh(
        lambda t: current_app.api_client.get(_API_NOTIFICATIONS_COUNT, token=t)
    )
    unread_count = count_resp.json().get("count", 0) if (count_resp and count_resp.ok) else 0

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
    resp = current_app.api_client.get(_API_JOBS, token=token, params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}
    recommended_jobs = []
    watched_job_ids = set()
    if token:
        rec_resp, authed = _try_with_refresh(
            lambda t: current_app.api_client.get(_API_JOBS + _PATH_RECOMMENDED, token=t, params={"limit": 20, "offset": 0})
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
    resp = current_app.api_client.get(_API_JOBS, token=token, params=params)
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


@bp.route("/jobs/<slug>", methods=["GET"])
def job_detail(slug):
    resp = current_app.api_client.get(f"/jobs/{slug}")
    if not resp.ok:
        return render_template(_TEMPLATE_404), 404
    job = resp.json()
    watching = False
    token = session.get("token")
    if token:
        w_resp = current_app.api_client.get(f"/jobs/{job['id']}/watch", token=token)
        if w_resp.ok:
            watching = w_resp.json().get("watching", False)
    return render_template("jobs/detail.html", job=job, watching=watching)


@bp.route("/jobs/<job_id>/watch", methods=["POST"])
def watch_job(job_id):
    try:
        _uuid.UUID(job_id)
    except ValueError:
        return render_template(_TEMPLATE_404), 404
    slug = request.form.get("slug")
    back = _safe_back(f"/jobs/{slug}" if slug else "/")
    resp, authed = _try_with_refresh(lambda t: current_app.api_client.post(f"/jobs/{job_id}/watch", token=t))
    if not authed:
        return redirect(f"/login?next={back}")
    if resp and not resp.ok and resp.status_code != 400:  # 400 = already watching, that's fine
        return render_template(_TEMPLATE_404), resp.status_code
    return redirect(back)


@bp.route("/jobs/<job_id>/unwatch", methods=["POST"])
def unwatch_job(job_id):
    try:
        _uuid.UUID(job_id)
    except ValueError:
        return render_template(_TEMPLATE_404), 404
    slug = request.form.get("slug")
    back = _safe_back(f"/jobs/{slug}" if slug else "/")
    _, authed = _try_with_refresh(lambda t: current_app.api_client.delete(f"/jobs/{job_id}/watch", token=t))
    if not authed:
        return redirect(f"/login?next={back}")
    return redirect(back)


# ─── Admit Cards Section ─────────────────────────────────────────────────


@bp.route("/admit-cards", methods=["GET"])
def admit_cards():
    params = {"limit": min(_int_arg("limit", 20), 100), "offset": _int_arg("offset", 0)}
    token = session.get("token")
    resp = current_app.api_client.get(_API_ADMIT_CARDS, params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}
    recommended_cards = []
    watched_job_ids, watched_admission_ids = _fetch_watched_ids()
    if token:
        rec_resp, authed = _try_with_refresh(
            lambda t: current_app.api_client.get(_API_ADMIT_CARDS + _PATH_RECOMMENDED, token=t, params={"limit": 20, "offset": 0})
        )
        if authed and rec_resp and rec_resp.ok:
            recommended_cards = rec_resp.json().get("data", [])
    return render_template(
        "admit_cards/list.html",
        cards=data.get("data", []),
        pagination=data.get("pagination", {}),
        recommended_cards=recommended_cards,
        watched_job_ids=watched_job_ids,
        watched_admission_ids=watched_admission_ids,
    )


@bp.route("/partials/admit-cards", methods=["GET"])
def admit_cards_partial():
    params = {"limit": min(_int_arg("limit", 20), 100), "offset": _int_arg("offset", 0)}
    resp = current_app.api_client.get(_API_ADMIT_CARDS, params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}
    pagination = data.get("pagination", {})
    has_more = pagination.get("has_more", False)
    next_offset = params["offset"] + params["limit"] if has_more else 0
    watched_job_ids, watched_admission_ids = _fetch_watched_ids()
    return render_template(
        "admit_cards/_cards.html",
        cards=data.get("data", []),
        has_more=has_more,
        next_offset=next_offset,
        watched_job_ids=watched_job_ids,
        watched_admission_ids=watched_admission_ids,
    )


@bp.route("/admit-cards/<slug>", methods=["GET"])
def admit_card_detail(slug):
    resp = current_app.api_client.get(f"/admit-cards/{slug}")
    if not resp.ok:
        return render_template(_TEMPLATE_404), 404
    card = resp.json()
    watching = False
    token = session.get("token")
    if token:
        if card.get("job"):
            w = current_app.api_client.get(f"/jobs/{card['job']['id']}/watch", token=token)
            watching = w.json().get("watching", False) if w.ok else False
        elif card.get("admission"):
            w = current_app.api_client.get(f"/admissions/{card['admission']['id']}/watch", token=token)
            watching = w.json().get("watching", False) if w.ok else False
    return render_template("admit_cards/detail.html", card=card, watching=watching)


# ─── Answer Keys Section ─────────────────────────────────────────────────


@bp.route("/answer-keys", methods=["GET"])
def answer_keys():
    params = {"limit": min(_int_arg("limit", 20), 100), "offset": _int_arg("offset", 0)}
    token = session.get("token")
    resp = current_app.api_client.get(_API_ANSWER_KEYS, params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}
    recommended_keys = []
    watched_job_ids, watched_admission_ids = _fetch_watched_ids()
    if token:
        rec_resp, authed = _try_with_refresh(
            lambda t: current_app.api_client.get(_API_ANSWER_KEYS + _PATH_RECOMMENDED, token=t, params={"limit": 20, "offset": 0})
        )
        if authed and rec_resp and rec_resp.ok:
            recommended_keys = rec_resp.json().get("data", [])
    return render_template(
        "answer_keys/list.html",
        keys=data.get("data", []),
        pagination=data.get("pagination", {}),
        recommended_keys=recommended_keys,
        watched_job_ids=watched_job_ids,
        watched_admission_ids=watched_admission_ids,
    )


@bp.route("/partials/answer-keys", methods=["GET"])
def answer_keys_partial():
    params = {"limit": min(_int_arg("limit", 20), 100), "offset": _int_arg("offset", 0)}
    resp = current_app.api_client.get(_API_ANSWER_KEYS, params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}
    pagination = data.get("pagination", {})
    has_more = pagination.get("has_more", False)
    next_offset = params["offset"] + params["limit"] if has_more else 0
    watched_job_ids, watched_admission_ids = _fetch_watched_ids()
    return render_template(
        "answer_keys/_cards.html",
        keys=data.get("data", []),
        has_more=has_more,
        next_offset=next_offset,
        watched_job_ids=watched_job_ids,
        watched_admission_ids=watched_admission_ids,
    )


@bp.route("/answer-keys/<slug>", methods=["GET"])
def answer_key_detail(slug):
    resp = current_app.api_client.get(f"/answer-keys/{slug}")
    if not resp.ok:
        return render_template(_TEMPLATE_404), 404
    key = resp.json()
    watching = False
    token = session.get("token")
    if token:
        if key.get("job"):
            w = current_app.api_client.get(f"/jobs/{key['job']['id']}/watch", token=token)
            watching = w.json().get("watching", False) if w.ok else False
        elif key.get("admission"):
            w = current_app.api_client.get(f"/admissions/{key['admission']['id']}/watch", token=token)
            watching = w.json().get("watching", False) if w.ok else False
    return render_template("answer_keys/detail.html", key=key, watching=watching)


# ─── Results Section ─────────────────────────────────────────────────────


@bp.route("/results", methods=["GET"])
def results():
    params = {"limit": min(_int_arg("limit", 20), 100), "offset": _int_arg("offset", 0)}
    token = session.get("token")
    resp = current_app.api_client.get(_API_RESULTS, params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}
    recommended_results = []
    watched_job_ids, watched_admission_ids = _fetch_watched_ids()
    if token:
        rec_resp, authed = _try_with_refresh(
            lambda t: current_app.api_client.get(_API_RESULTS + _PATH_RECOMMENDED, token=t, params={"limit": 20, "offset": 0})
        )
        if authed and rec_resp and rec_resp.ok:
            recommended_results = rec_resp.json().get("data", [])
    return render_template(
        "results/list.html",
        results=data.get("data", []),
        pagination=data.get("pagination", {}),
        recommended_results=recommended_results,
        watched_job_ids=watched_job_ids,
        watched_admission_ids=watched_admission_ids,
    )


@bp.route("/partials/results", methods=["GET"])
def results_partial():
    params = {"limit": min(_int_arg("limit", 20), 100), "offset": _int_arg("offset", 0)}
    resp = current_app.api_client.get(_API_RESULTS, params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}
    pagination = data.get("pagination", {})
    has_more = pagination.get("has_more", False)
    next_offset = params["offset"] + params["limit"] if has_more else 0
    watched_job_ids, watched_admission_ids = _fetch_watched_ids()
    return render_template(
        "results/_cards.html",
        results=data.get("data", []),
        has_more=has_more,
        next_offset=next_offset,
        watched_job_ids=watched_job_ids,
        watched_admission_ids=watched_admission_ids,
    )


@bp.route("/results/<slug>", methods=["GET"])
def result_detail(slug):
    resp = current_app.api_client.get(f"/results/{slug}")
    if not resp.ok:
        return render_template(_TEMPLATE_404), 404
    result = resp.json()
    watching = False
    token = session.get("token")
    if token:
        if result.get("job"):
            w = current_app.api_client.get(f"/jobs/{result['job']['id']}/watch", token=token)
            watching = w.json().get("watching", False) if w.ok else False
        elif result.get("admission"):
            w = current_app.api_client.get(f"/admissions/{result['admission']['id']}/watch", token=token)
            watching = w.json().get("watching", False) if w.ok else False
    return render_template("results/detail.html", result=result, watching=watching)


# ─── Admissions Section ──────────────────────────────────────────────────────


@bp.route("/admissions", methods=["GET"])
def admissions():
    params = {}
    for key in ("q", "stream", "admission_type"):
        val = request.args.get(key)
        if val:
            params[key] = val
    params["limit"] = min(_int_arg("limit", 20), 100)
    params["offset"] = _int_arg("offset", 0)
    token = session.get("token")
    resp = current_app.api_client.get(_API_ADMISSIONS, token=token, params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}
    recommended_admissions = []
    watched_job_ids, watched_admission_ids = _fetch_watched_ids()
    if token:
        rec_resp, authed = _try_with_refresh(
            lambda t: current_app.api_client.get(_API_ADMISSIONS + _PATH_RECOMMENDED, token=t, params={"limit": 20, "offset": 0})
        )
        if authed and rec_resp and rec_resp.ok:
            recommended_admissions = rec_resp.json().get("data", [])
    return render_template(
        "admissions/list.html",
        admissions=data.get("data", []),
        pagination=data.get("pagination", {}),
        recommended_admissions=recommended_admissions,
        watched_job_ids=watched_job_ids,
        watched_admission_ids=watched_admission_ids,
        q=request.args.get("q", ""),
        stream=request.args.get("stream", ""),
        admission_type=request.args.get("admission_type", ""),
    )


@bp.route("/partials/admissions", methods=["GET"])
def admissions_partial():
    params = {}
    for key in ("q", "stream", "admission_type"):
        val = request.args.get(key)
        if val:
            params[key] = val
    params["limit"] = min(_int_arg("limit", 20), 100)
    params["offset"] = _int_arg("offset", 0)
    resp = current_app.api_client.get(_API_ADMISSIONS, params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}
    pagination = data.get("pagination", {})
    has_more = pagination.get("has_more", False)
    next_offset = params["offset"] + params["limit"] if has_more else 0
    return render_template(
        "admissions/_cards.html",
        admissions=data.get("data", []),
        has_more=has_more,
        next_offset=next_offset,
        q=request.args.get("q", ""),
        stream=request.args.get("stream", ""),
        admission_type=request.args.get("admission_type", ""),
    )


@bp.route("/admissions/<slug>", methods=["GET"])
def admission_detail(slug):
    resp = current_app.api_client.get(f"/admissions/{slug}")
    if not resp.ok:
        return render_template(_TEMPLATE_404), 404
    admission = resp.json()
    watching = False
    token = session.get("token")
    if token:
        w_resp = current_app.api_client.get(f"/admissions/{admission['id']}/watch", token=token)
        if w_resp.ok:
            watching = w_resp.json().get("watching", False)
    return render_template("admissions/detail.html", admission=admission, watching=watching)


@bp.route("/admissions/<admission_id>/watch", methods=["POST"])
def watch_admission(admission_id):
    try:
        _uuid.UUID(admission_id)
    except ValueError:
        return render_template(_TEMPLATE_404), 404
    slug = request.form.get("slug")
    back = _safe_back(f"/admissions/{slug}" if slug else "/")
    resp, authed = _try_with_refresh(lambda t: current_app.api_client.post(f"/admissions/{admission_id}/watch", token=t))
    if not authed:
        return redirect(f"/login?next={back}")
    if resp and not resp.ok and resp.status_code != 400:
        return render_template(_TEMPLATE_404), resp.status_code
    return redirect(back)


@bp.route("/admissions/<admission_id>/unwatch", methods=["POST"])
def unwatch_admission(admission_id):
    try:
        _uuid.UUID(admission_id)
    except ValueError:
        return render_template(_TEMPLATE_404), 404
    slug = request.form.get("slug")
    back = _safe_back(f"/admissions/{slug}" if slug else "/")
    _resp, authed = _try_with_refresh(lambda t: current_app.api_client.delete(f"/admissions/{admission_id}/watch", token=t))
    if not authed:
        return redirect(f"/login?next={back}")
    return redirect(back)



_DEFAULT_SECRET_KEY = "dev-secret-key"  # pragma: allowlist secret


def create_app():
    app = Flask(__name__)  # NOSONAR
    app.secret_key = os.environ.get("SECRET_KEY", _DEFAULT_SECRET_KEY)
    if os.environ.get("FLASK_ENV") == "production" and app.secret_key == _DEFAULT_SECRET_KEY:
        raise RuntimeError("SECRET_KEY must be set to a secure value in production.")
    app.api_client = ApiClient(
        base_url=os.environ.get("BACKEND_API_URL", "http://localhost:8000/api/v1")
    )
    app.register_blueprint(bp)
    app.register_error_handler(404, _not_found)
    app.register_error_handler(Exception, _handle_unexpected_error)
    return app


# Flask CLI entry point
app = create_app()
