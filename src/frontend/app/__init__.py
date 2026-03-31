"""Hermes User Frontend — Flask + Jinja2 + HTMX."""

import os
import secrets

from flask import Flask, current_app, render_template, request, session, redirect, flash

from app.api_client import ApiClient


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

    app.api_client = ApiClient(
        base_url=os.environ.get("BACKEND_API_URL", "http://localhost:8000/api/v1")
    )

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

    _api_with_auth = _try_with_refresh

    @app.context_processor
    def inject_csrf():
        return {"csrf_token": _get_csrf_token()}

    _CSRF_EXEMPT = {"/auth/firebase-callback", "/auth/send-email-otp", "/auth/verify-email-otp", "/auth/complete-registration", "/auth/check-user-providers", "/auth/add-password", "/auth/check-phone-availability"}

    @app.before_request
    def validate_csrf():
        if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
            return
        if request.path in _CSRF_EXEMPT:
            return
        form_token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token", "")
        if not form_token or form_token != session.get("csrf_token"):
            flash("Invalid or expired form submission. Please try again.", "error")
            return redirect(request.referrer or "/")

    @app.route("/health")
    def health():
        return {"status": "ok", "service": "hermes-frontend"}

    @app.route("/")
    def index():
        """Landing page — job vacancies only."""
        params = _job_params()
        token = session.get("token")
        if params.get("recommended") and token:
            resp = current_app.api_client.get("/jobs/recommended", token=token, params={"limit": params.get("limit", 20), "offset": params.get("offset", 0)})
        else:
            params.pop("recommended", None)
            resp = current_app.api_client.get("/jobs", params=params)
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}
        return render_template("jobs/index.html", jobs=data["data"], pagination=data.get("pagination", {}), params=params, card_type="latest_job")

    @app.route("/jobs")
    def job_list_partial():
        """HTMX partial — returns job card rows + load-more button."""
        params = _job_params()
        token = session.get("token")
        if params.get("recommended") and token:
            resp = current_app.api_client.get("/jobs/recommended", token=token, params={"limit": params.get("limit", 20), "offset": params.get("offset", 0)})
        else:
            params.pop("recommended", None)
            resp = current_app.api_client.get("/jobs", params=params)
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}
        return render_template("jobs/_job_cards.html", jobs=data["data"], pagination=data.get("pagination", {}), params=params, card_type="latest_job")

    @app.route("/admit-cards")
    def admit_cards():
        """Browse admit cards."""
        token = session.get("token")
        params = {"limit": 20, "offset": request.args.get("offset", 0, type=int)}
        if request.args.get("q"):
            params["q"] = request.args.get("q")
        if request.args.get("organization"):
            params["organization"] = request.args.get("organization")
        
        if request.args.get("recommended") and token:
            resp = current_app.api_client.get("/admit-cards/recommended", token=token, params={"limit": params.get("limit", 20), "offset": params.get("offset", 0)})
        else:
            resp = current_app.api_client.get("/admit-cards", params=params)
        
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}
        return render_template("admit_cards/admit_cards.html", cards=data["data"], pagination=data.get("pagination", {}), params=request.args)

    @app.route("/answer-keys")
    def answer_keys():
        """Answer keys section page."""
        token = session.get("token")
        params = {"limit": 20, "offset": request.args.get("offset", 0, type=int)}
        if request.args.get("q"):
            params["q"] = request.args.get("q")
        if request.args.get("organization"):
            params["organization"] = request.args.get("organization")
        
        if request.args.get("recommended") and token:
            resp = current_app.api_client.get("/answer-keys/recommended", token=token, params={"limit": params.get("limit", 20), "offset": params.get("offset", 0)})
        else:
            resp = current_app.api_client.get("/answer-keys", params=params)
        
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}
        return render_template("answer_keys/answer_keys.html", keys=data["data"], pagination=data.get("pagination", {}), params=request.args)

    @app.route("/results")
    def results():
        """Results section page."""
        token = session.get("token")
        params = {"limit": 20, "offset": request.args.get("offset", 0, type=int)}
        if request.args.get("q"):
            params["q"] = request.args.get("q")
        if request.args.get("organization"):
            params["organization"] = request.args.get("organization")
        
        if request.args.get("recommended") and token:
            resp = current_app.api_client.get("/results/recommended", token=token, params={"limit": params.get("limit", 20), "offset": params.get("offset", 0)})
        else:
            resp = current_app.api_client.get("/results", params=params)
        
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}
        return render_template("results/results.html", results=data["data"], pagination=data.get("pagination", {}), params=request.args)

    @app.route("/admit-cards/<card_id>")
    def admit_card_detail(card_id):
        """Admit card detail page."""
        resp = current_app.api_client.get(f"/admit-cards/{card_id}")
        if not resp.ok:
            return render_template("shared/404.html"), 404
        card = resp.json()
        return render_template("admit_cards/admit_card_detail.html", card=card)

    @app.route("/answer-keys/<key_id>")
    def answer_key_detail(key_id):
        """Answer key detail page."""
        resp = current_app.api_client.get(f"/answer-keys/{key_id}")
        if not resp.ok:
            return render_template("shared/404.html"), 404
        key = resp.json()
        return render_template("answer_keys/answer_key_detail.html", key=key)

    @app.route("/results/<result_id>")
    def result_detail(result_id):
        """Result detail page."""
        resp = current_app.api_client.get(f"/results/{result_id}")
        if not resp.ok:
            return render_template("shared/404.html"), 404
        result = resp.json()
        return render_template("results/result_detail.html", result=result)

    @app.route("/jobs/<slug>")
    def job_detail(slug):
        """Job detail page."""
        resp = current_app.api_client.get(f"/jobs/{slug}")
        if not resp.ok:
            return render_template("shared/404.html"), 404
        job = resp.json()
        return render_template("jobs/job_detail.html", job=job)


    @app.route("/entrance-exams")
    def entrance_exams():
        """Entrance exams section page."""
        token = session.get("token")
        params = {}
        for key in ("q", "stream", "exam_type"):
            val = request.args.get(key)
            if val:
                params[key] = val
        params["limit"] = min(_int_arg("limit", 20), 100)
        params["offset"] = _int_arg("offset", 0)
        
        if request.args.get("recommended") and token:
            resp = current_app.api_client.get("/entrance-exams/recommended", token=token, params={"limit": params.get("limit", 20), "offset": params.get("offset", 0)})
        else:
            resp = current_app.api_client.get("/entrance-exams", params=params)
        
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}
        return render_template("entrance_exams/entrance_exams.html", exams=data["data"], pagination=data.get("pagination", {}), params=request.args)

    @app.route("/entrance-exams/partial")
    def entrance_exams_partial():
        """HTMX partial for entrance exams load-more — returns card rows only."""
        params = {}
        for key in ("q", "stream", "exam_type"):
            val = request.args.get(key)
            if val:
                params[key] = val
        params["limit"] = 20
        params["offset"] = _int_arg("offset", 0)
        resp = current_app.api_client.get("/entrance-exams", params=params)
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}
        return render_template("entrance_exams/_exam_cards.html", exams=data["data"], pagination=data.get("pagination", {}), params=params)

    @app.route("/entrance-exams/<slug>")
    def entrance_exam_detail(slug):
        """Entrance exam detail page."""
        resp = current_app.api_client.get(f"/entrance-exams/{slug}")
        if not resp.ok:
            return render_template("shared/404.html"), 404
        exam = resp.json()
        return render_template("entrance_exams/entrance_exam_detail.html", exam=exam)


    # --- Watched Items Dashboard ---

    @app.route("/dashboard")
    def dashboard():
        """Watched items dashboard — shows jobs and exams the user is watching."""
        token = session.get("token")
        if not token:
            return render_template("auth/login.html", next="/dashboard")

        resp, authed = _try_with_refresh(lambda t: current_app.api_client.get("/users/me/watched", token=t))
        if not authed:
            return redirect("/login")
        watched = resp.json() if resp.ok else {"jobs": [], "exams": [], "total": 0}

        return render_template(
            "dashboard/dashboard.html",
            watched_jobs=watched.get("jobs", []),
            watched_exams=watched.get("exams", []),
            total=watched.get("total", 0),
        )

    # --- Notifications ---

    @app.route("/notifications")
    def notifications():
        """Notifications page — requires login."""
        token = session.get("token")
        if not token:
            return render_template("auth/login.html", next="/notifications")

        # Fetch unread count (refresh token on 401)
        count_resp = current_app.api_client.get("/notifications/count", token=token)
        if count_resp.status_code == 401:
            token = _try_refresh()
            if not token:
                return redirect("/login")
            count_resp = current_app.api_client.get("/notifications/count", token=token)
        unread_count = count_resp.json().get("count", 0) if count_resp.ok else 0

        # Fetch notifications
        params = {"limit": 20, "offset": 0}
        notif_resp = current_app.api_client.get("/notifications", token=token, params=params)
        notif_data = notif_resp.json() if notif_resp.ok else {"data": [], "pagination": {}}

        return render_template(
            "notifications/notifications.html",
            notifications=notif_data["data"],
            pagination=notif_data.get("pagination", {}),
            unread_count=unread_count,
        )

    @app.route("/notifications/list")
    def notifications_list_partial():
        """HTMX partial — returns notification rows for load-more."""
        token = session.get("token")
        if not token:
            return "", 401

        params = {"limit": 20, "offset": _int_arg("offset", 0)}
        notif_resp = current_app.api_client.get("/notifications", token=token, params=params)
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

    @app.route("/notifications/unread-count")
    def notifications_unread_count():
        """HTMX partial — returns just the unread count number for the badge."""
        token = session.get("token")
        if not token:
            return ""

        resp = current_app.api_client.get("/notifications/count", token=token)
        count = resp.json().get("count", 0) if resp.ok else 0

        if count > 0:
            return str(count)
        return ""

    @app.route("/notifications/<notification_id>/read", methods=["POST"])
    def mark_notification_read(notification_id):
        """Mark a notification as read (proxies to backend PUT)."""
        _, authed = _try_with_refresh(lambda t: current_app.api_client.put(f"/notifications/{notification_id}/read", token=t))
        if not authed:
            return redirect("/login")
        return redirect("/notifications")

    @app.route("/notifications/read-all", methods=["POST"])
    def mark_all_notifications_read():
        """Mark all notifications as read (proxies to backend PUT)."""
        _, authed = _try_with_refresh(lambda t: current_app.api_client.put("/notifications/read-all", token=t))
        if not authed:
            return redirect("/login")
        return redirect("/notifications")

    @app.route("/notifications/<notification_id>/delete", methods=["POST"])
    def delete_notification(notification_id):
        """Delete a notification (proxies to backend DELETE)."""
        _, authed = _try_with_refresh(lambda t: current_app.api_client.delete(f"/notifications/{notification_id}", token=t))
        if not authed:
            return redirect("/login")
        return redirect("/notifications")

    @app.route("/offline")
    def offline():
        return render_template("shared/offline.html")

    # --- Profile (Phase 10b + 10c + 10f) ---

    @app.route("/profile", methods=["GET", "POST"])
    def profile():
        """User profile — view and update preferences, phone, notification settings."""
        token = session.get("token")
        if not token:
            return redirect("/login?next=/profile")

        if request.method == "POST":
            action = request.form.get("action", "profile")

            if action == "profile":
                update = {}
                for f in ("gender", "state", "city", "pincode"):
                    val = request.form.get(f, "").strip()
                    update[f] = val or None
                for f in ("is_pwd", "is_ex_serviceman"):
                    update[f] = request.form.get(f) == "on"
                qual = request.form.get("highest_qualification", "").strip()
                update["highest_qualification"] = qual or None
                states = [s.strip() for s in request.form.get("preferred_states", "").split(",") if s.strip()]
                update["preferred_states"] = states
                cats = request.form.getlist("preferred_categories")
                update["preferred_categories"] = cats
                current_app.api_client.put("/users/profile", token=token, json=update)
                phone = request.form.get("phone", "").strip()
                if phone:
                    current_app.api_client.put("/users/profile/phone", token=token, json={"phone": phone})
                flash("Profile updated.", "success")

            elif action == "notification_prefs":
                prefs = {
                    "email": request.form.get("email_notif") == "on",
                    "push": request.form.get("push_notif") == "on",
                }
                current_app.api_client.put("/users/me/notification-preferences", token=token, json=prefs)
                flash("Notification preferences saved.", "success")

            return redirect("/profile")

        resp = current_app.api_client.get("/users/profile", token=token)
        if resp.status_code == 401:
            token = _try_refresh()
            if not token:
                return redirect("/login")
            resp = current_app.api_client.get("/users/profile", token=token)

        user_data = resp.json() if resp.ok else {}
        return render_template("auth/profile.html",
            user=user_data,
            profile=user_data.get("profile", {}),
            firebase_api_key=os.environ.get("FIREBASE_WEB_API_KEY", ""),
            firebase_auth_domain=os.environ.get("FIREBASE_AUTH_DOMAIN", ""),
            firebase_project_id=os.environ.get("FIREBASE_PROJECT_ID", "")
        )

    # --- Auth Flows (Firebase) ---

    @app.route("/auth/send-email-otp", methods=["POST"])
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
            if resp.headers.get("content-type", "").startswith("application/json"):
                detail = resp.json().get("detail", detail)
            return {"error": detail}, resp.status_code
        return {"message": "OTP sent to your email"}, 200

    @app.route("/auth/verify-email-otp", methods=["POST"])
    def verify_email_otp():
        """Proxy: verify the 6-digit OTP and return verification token."""
        data = request.get_json(silent=True) or {}
        email = data.get("email", "")
        otp = data.get("otp", "")
        if not email or not otp:
            return {"error": "Missing fields"}, 400
        resp = current_app.api_client.post("/auth/verify-email-otp", json={"email": email, "otp": otp})
        if not resp.ok:
            detail = "Invalid OTP"
            if resp.headers.get("content-type", "").startswith("application/json"):
                detail = resp.json().get("detail", detail)
            return {"error": detail}, resp.status_code
        return resp.json(), 200

    @app.route("/auth/complete-registration", methods=["POST"])
    def complete_registration():
        """Proxy: complete email/password registration via Firebase Admin SDK."""
        data = request.get_json(silent=True) or {}
        email = data.get("email", "")
        password = data.get("password", "")
        verification_token = data.get("verification_token", "")
        if not email or not password or not verification_token:
            return {"error": "Missing fields"}, 400
        resp = current_app.api_client.post(
            "/auth/complete-registration",
            json={"email": email, "password": password, "verification_token": verification_token},
        )
        if not resp.ok:
            detail = "Registration failed"
            if resp.headers.get("content-type", "").startswith("application/json"):
                detail = resp.json().get("detail", detail)
            return {"error": detail}, resp.status_code
        return resp.json(), 200

    @app.route("/auth/check-user-providers", methods=["POST"])
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

    @app.route("/auth/add-password", methods=["POST"])
    def add_password():
        """Proxy: add password to existing social auth account."""
        data = request.get_json(silent=True) or {}
        email = data.get("email", "")
        password = data.get("password", "")
        verification_token = data.get("verification_token", "")
        if not email or not password or not verification_token:
            return {"error": "Missing fields"}, 400
        resp = current_app.api_client.post(
            "/auth/add-password",
            json={"email": email, "password": password, "verification_token": verification_token},
        )
        if not resp.ok:
            detail = "Failed to add password"
            if resp.headers.get("content-type", "").startswith("application/json"):
                detail = resp.json().get("detail", detail)
            return {"error": detail}, resp.status_code
        return resp.json(), 200

    @app.route("/auth/check-phone-availability", methods=["POST"])
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

    @app.route("/users/me/profile", methods=["GET"])
    def get_user_profile():
        """Proxy: get user profile with phone verification status."""
        resp, ok = _api_with_auth(lambda token: current_app.api_client.get("/users/profile", token=token))
        if not ok:
            return redirect("/login")
        if not resp.ok:
            return {"error": "Failed to fetch profile"}, resp.status_code
        return resp.json(), 200

    @app.route("/users/me/phone", methods=["PUT"])
    def update_user_phone():
        """Proxy: update user phone number."""
        data = request.get_json(silent=True) or {}
        phone = data.get("phone", "")
        if not phone:
            return {"error": "Phone number required"}, 400
        resp, ok = _api_with_auth(lambda token: current_app.api_client.put("/users/profile/phone", token=token, json={"phone": phone}))
        if not ok:
            return {"error": "Authentication required"}, 401
        if not resp.ok:
            detail = "Failed to update phone"
            if resp.headers.get("content-type", "").startswith("application/json"):
                detail = resp.json().get("detail", detail)
            return {"error": detail}, resp.status_code
        return resp.json(), 200

    @app.route("/users/me/send-phone-otp", methods=["POST"])
    def send_phone_otp():
        """Proxy: trigger phone OTP send."""
        resp, ok = _api_with_auth(lambda token: current_app.api_client.post("/users/me/send-phone-otp", token=token))
        if not ok:
            return {"error": "Authentication required"}, 401
        if not resp.ok:
            detail = "Failed to send OTP"
            if resp.headers.get("content-type", "").startswith("application/json"):
                detail = resp.json().get("detail", detail)
            return {"error": detail}, resp.status_code
        return resp.json(), 200

    @app.route("/users/me/verify-phone-otp", methods=["POST"])
    def verify_phone_otp():
        """Proxy: verify phone OTP."""
        data = request.get_json(silent=True) or {}
        otp = data.get("otp", "")
        if not otp:
            return {"error": "OTP required"}, 400
        resp, ok = _api_with_auth(lambda token: current_app.api_client.post("/users/me/verify-phone-otp", token=token, json={"otp": otp}))
        if not ok:
            return {"error": "Authentication required"}, 401
        if not resp.ok:
            detail = "Invalid OTP"
            if resp.headers.get("content-type", "").startswith("application/json"):
                detail = resp.json().get("detail", detail)
            return {"error": detail}, resp.status_code
        return resp.json(), 200

    @app.route("/users/me/set-password", methods=["POST"])
    def set_password():
        """Proxy: set password for Google OAuth users."""
        data = request.get_json(silent=True) or {}
        new_password = data.get("new_password", "")
        if not new_password or len(new_password) < 8:
            return {"error": "Password must be at least 8 characters"}, 400
        resp, ok = _api_with_auth(lambda token: current_app.api_client.post("/users/me/set-password", token=token, json={"new_password": new_password}))
        if not ok:
            return {"error": "Authentication required"}, 401
        if not resp.ok:
            detail = "Failed to set password"
            if resp.headers.get("content-type", "").startswith("application/json"):
                detail = resp.json().get("detail", detail)
            return {"error": detail}, resp.status_code
        return resp.json(), 200

    @app.route("/users/me/change-password", methods=["POST"])
    def change_password():
        """Proxy: change password for users with existing password."""
        data = request.get_json(silent=True) or {}
        current_password = data.get("current_password", "")
        new_password = data.get("new_password", "")
        if not current_password or not new_password:
            return {"error": "Both current and new passwords required"}, 400
        if len(new_password) < 8:
            return {"error": "New password must be at least 8 characters"}, 400
        resp, ok = _api_with_auth(lambda token: current_app.api_client.post("/users/me/change-password", token=token, json={"current_password": current_password, "new_password": new_password}))
        if not ok:
            return {"error": "Authentication required"}, 401
        if not resp.ok:
            detail = "Failed to change password"
            if resp.headers.get("content-type", "").startswith("application/json"):
                detail = resp.json().get("detail", detail)
            return {"error": detail}, resp.status_code
        return resp.json(), 200

    @app.route("/users/me/link-email-password", methods=["POST"])
    def link_email_password():
        """Proxy: link email+password to phone-only account."""
        data = request.get_json(silent=True) or {}
        email = data.get("email", "")
        password = data.get("password", "")
        if not email or not password:
            return {"error": "Email and password required"}, 400
        if len(password) < 8:
            return {"error": "Password must be at least 8 characters"}, 400
        resp, ok = _api_with_auth(lambda token: current_app.api_client.post("/users/me/link-email-password", token=token, json={"email": email, "password": password}))
        if not ok:
            return {"error": "Authentication required"}, 401
        if not resp.ok:
            detail = "Failed to link email and password"
            if resp.headers.get("content-type", "").startswith("application/json"):
                detail = resp.json().get("detail", detail)
            return {"error": detail}, resp.status_code
        return resp.json(), 200

    @app.route("/auth/firebase-callback", methods=["POST"])
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
            if resp.headers.get("content-type", "").startswith("application/json"):
                detail = resp.json().get("detail", detail)
            return {"error": detail}, resp.status_code

        tokens = resp.json()
        session["token"] = tokens.get("access_token")
        session["refresh_token"] = tokens.get("refresh_token")
        me_resp = current_app.api_client.get("/users/profile", token=session["token"])
        session["user_name"] = me_resp.json().get("full_name", "") if me_resp.ok else ""
        return {"redirect": "/"}, 200

    @app.route("/login")
    def login():
        """Render Firebase-powered login page."""
        return render_template("auth/login.html",
            next=request.args.get("next", "/"),
            firebase_api_key=os.environ.get("FIREBASE_WEB_API_KEY", ""),
            firebase_auth_domain=os.environ.get("FIREBASE_AUTH_DOMAIN", ""),
            firebase_project_id=os.environ.get("FIREBASE_PROJECT_ID", ""),
        )

    @app.route("/logout")
    def logout():
        token = session.get("token")
        if token:
            current_app.api_client.post("/auth/logout", token=token)
        session.clear()
        return redirect("/")

    def _job_params() -> dict:
        """Build query params from request args."""
        params: dict = {}
        for key in ("q", "qualification_level", "organization", "department", "recommended"):
            val = request.args.get(key)
            if val:
                params[key] = val
        params["limit"] = min(_int_arg("limit", 20), 100)
        params["offset"] = _int_arg("offset", 0)
        return params

    def _int_arg(name: str, default: int) -> int:
        """Parse an integer query parameter safely."""
        try:
            return int(request.args.get(name, default))
        except (ValueError, TypeError):
            return default

    @app.route("/favicon.ico")
    def favicon():
        """Serve favicon or return 204 if not found."""
        from flask import send_from_directory
        import os
        favicon_path = os.path.join(app.root_path, "static", "favicon.ico")
        if os.path.exists(favicon_path):
            return send_from_directory(os.path.join(app.root_path, "static"), "favicon.ico")
        return "", 204

    @app.errorhandler(404)
    def not_found(e):
        return render_template("shared/404.html"), 404

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc):
        app.logger.error("Unhandled exception: %s", exc, exc_info=True)
        return render_template("shared/404.html"), 500

    return app


# Flask CLI entry point
app = create_app()
