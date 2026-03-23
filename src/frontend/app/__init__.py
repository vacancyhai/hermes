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

    @app.route("/health")
    def health():
        return {"status": "ok", "service": "hermes-frontend"}

    @app.route("/")
    def index():
        """Landing page — full page with initial job listing."""
        params = _job_params()
        token = session.get("token")
        if params.get("recommended") and token:
            resp = current_app.api_client.get("/jobs/recommended", token=token, params={"limit": params.get("limit", 20), "offset": params.get("offset", 0)})
        else:
            params.pop("recommended", None)
            resp = current_app.api_client.get("/jobs", params=params)
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}
        return render_template("index.html", jobs=data["data"], pagination=data.get("pagination", {}), params=params)

    @app.route("/jobs")
    def job_list_partial():
        """HTMX partial — returns only the job card rows + load-more button."""
        params = _job_params()
        token = session.get("token")
        if params.get("recommended") and token:
            resp = current_app.api_client.get("/jobs/recommended", token=token, params={"limit": params.get("limit", 20), "offset": params.get("offset", 0)})
        else:
            params.pop("recommended", None)
            resp = current_app.api_client.get("/jobs", params=params)
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}
        return render_template("_job_cards.html", jobs=data["data"], pagination=data.get("pagination", {}), params=params)

    @app.route("/jobs/<slug>")
    def job_detail(slug):
        """Job detail page."""
        resp = current_app.api_client.get(f"/jobs/{slug}")
        if not resp.ok:
            return render_template("404.html"), 404
        job = resp.json()
        return render_template("job_detail.html", job=job)

    # --- Application Dashboard ---

    @app.route("/dashboard")
    def dashboard():
        """Application tracking dashboard — requires login."""
        token = session.get("token")
        if not token:
            return render_template("login.html", next="/dashboard")

        # Fetch stats (refresh token on 401)
        stats_resp = current_app.api_client.get("/applications/stats", token=token)
        if stats_resp.status_code == 401:
            token = _try_refresh()
            if not token:
                return redirect("/login")
            stats_resp = current_app.api_client.get("/applications/stats", token=token)
        stats = stats_resp.json() if stats_resp.ok else {"total": 0}

        # Fetch applications
        params = {"limit": 20, "offset": 0}
        status_filter = request.args.get("status")
        if status_filter:
            params["status"] = status_filter

        apps_resp = current_app.api_client.get("/applications", token=token, params=params)
        apps_data = apps_resp.json() if apps_resp.ok else {"data": [], "pagination": {}}

        return render_template(
            "dashboard.html",
            stats=stats,
            applications=apps_data["data"],
            pagination=apps_data.get("pagination", {}),
            current_status=status_filter,
        )

    @app.route("/dashboard/track", methods=["POST"])
    def track_application():
        """Track a job application."""
        token = session.get("token")
        if not token:
            return redirect("/login")
        job_id = request.form.get("job_id", "")
        notes = request.form.get("notes", "").strip()
        is_priority = request.form.get("is_priority") == "on"
        resp = current_app.api_client.post("/applications", token=token, json={
            "job_id": job_id, "notes": notes or None, "is_priority": is_priority
        })
        if resp.ok:
            flash("Job added to your tracker!", "success")
        elif resp.status_code == 409:
            flash("Already tracking this job.", "info")
        else:
            flash("Could not track this job. Please try again.", "error")
        return redirect(request.form.get("next", "/dashboard"))

    @app.route("/dashboard/applications/<app_id>/update", methods=["POST"])
    def update_application(app_id):
        """Update application status, notes, priority, app number."""
        token = session.get("token")
        if not token:
            return "", 401
        update = {}
        status_val = request.form.get("status", "").strip()
        if status_val:
            update["status"] = status_val
        notes_val = request.form.get("notes", "").strip()
        update["notes"] = notes_val or None
        app_num = request.form.get("application_number", "").strip()
        update["application_number"] = app_num or None
        update["is_priority"] = request.form.get("is_priority") == "on"
        current_app.api_client.put(f"/applications/{app_id}", token=token, json=update)
        return redirect("/dashboard")

    @app.route("/dashboard/applications/<app_id>/delete", methods=["POST"])
    def delete_application(app_id):
        """Remove an application from the tracker."""
        token = session.get("token")
        if not token:
            return "", 401
        current_app.api_client.delete(f"/applications/{app_id}", token=token)
        return redirect("/dashboard")

    @app.route("/dashboard/applications")
    def dashboard_applications_partial():
        """HTMX partial — returns application rows for the dashboard."""
        token = session.get("token")
        if not token:
            return "", 401

        params = {"limit": 20, "offset": _int_arg("offset", 0)}
        status_filter = request.args.get("status")
        if status_filter:
            params["status"] = status_filter

        apps_resp = current_app.api_client.get("/applications", token=token, params=params)
        apps_data = apps_resp.json() if apps_resp.ok else {"data": [], "pagination": {}}

        return render_template(
            "_application_rows.html",
            applications=apps_data["data"],
            pagination=apps_data.get("pagination", {}),
            current_status=status_filter,
        )

    # --- Notifications ---

    @app.route("/notifications")
    def notifications():
        """Notifications page — requires login."""
        token = session.get("token")
        if not token:
            return render_template("login.html", next="/notifications")

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
            "notifications.html",
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
            "_notif_items.html",
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
        token = session.get("token")
        if not token:
            return redirect("/login")

        current_app.api_client.put(f"/notifications/{notification_id}/read", token=token)
        return redirect("/notifications")

    @app.route("/notifications/read-all", methods=["POST"])
    def mark_all_notifications_read():
        """Mark all notifications as read (proxies to backend PUT)."""
        token = session.get("token")
        if not token:
            return redirect("/login")

        current_app.api_client.put("/notifications/read-all", token=token)
        return redirect("/notifications")

    @app.route("/notifications/<notification_id>/delete", methods=["POST"])
    def delete_notification(notification_id):
        """Delete a notification (proxies to backend DELETE)."""
        token = session.get("token")
        if not token:
            return redirect("/login")

        current_app.api_client.delete(f"/notifications/{notification_id}", token=token)
        return redirect("/notifications")

    @app.route("/offline")
    def offline():
        return render_template("offline.html")

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
        following_resp = current_app.api_client.get("/users/me/following", token=token)
        following = following_resp.json().get("followed_organizations", []) if following_resp.ok else []
        return render_template("profile.html", user=user_data, profile=user_data.get("profile", {}), following=following)

    @app.route("/profile/follow", methods=["POST"])
    def follow_org():
        """Follow an organization."""
        token = session.get("token")
        if not token:
            return redirect("/login")
        org_name = request.form.get("org_name", "").strip()
        if org_name:
            current_app.api_client.post(f"/organizations/{org_name}/follow", token=token)
        return redirect(request.form.get("next", "/profile"))

    @app.route("/profile/unfollow", methods=["POST"])
    def unfollow_org():
        """Unfollow an organization."""
        token = session.get("token")
        if not token:
            return redirect("/login")
        org_name = request.form.get("org_name", "").strip()
        if org_name:
            current_app.api_client.delete(f"/organizations/{org_name}/follow", token=token)
        return redirect(request.form.get("next", "/profile"))

    # --- Auth Flows ---

    @app.route("/register", methods=["GET", "POST"])
    def register():
        """User registration form."""
        if request.method == "GET":
            csrf_token = secrets.token_hex(16)
            session["csrf_token"] = csrf_token
            return render_template("register.html", csrf_token=csrf_token)

        form_csrf = request.form.get("csrf_token", "")
        if not form_csrf or form_csrf != session.pop("csrf_token", None):
            flash("Invalid request. Please try again.", "error")
            return redirect("/register")

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        full_name = request.form.get("full_name", "").strip()
        resp = current_app.api_client.post("/auth/register", json={"email": email, "password": password, "full_name": full_name})
        if resp.ok:
            flash("Registration successful! Please check your email to verify your account.", "success")
            return redirect("/login")
        detail = resp.json().get("detail", "Registration failed") if resp.headers.get("content-type", "").startswith("application/json") else "Registration failed"
        flash(detail, "error")
        return redirect("/register")

    @app.route("/forgot-password", methods=["GET", "POST"])
    def forgot_password():
        """Request a password reset email."""
        if request.method == "GET":
            csrf_token = secrets.token_hex(16)
            session["csrf_token"] = csrf_token
            return render_template("forgot_password.html", csrf_token=csrf_token)

        form_csrf = request.form.get("csrf_token", "")
        if not form_csrf or form_csrf != session.pop("csrf_token", None):
            flash("Invalid request. Please try again.", "error")
            return redirect("/forgot-password")

        email = request.form.get("email", "").strip()
        current_app.api_client.post("/auth/forgot-password", json={"email": email})
        # Always show success to avoid email enumeration
        flash("If that email is registered, you'll receive a reset link shortly.", "success")
        return redirect("/login")

    @app.route("/reset-password", methods=["GET", "POST"])
    def reset_password():
        """Reset password using token from email link."""
        token = request.args.get("token", "") or request.form.get("token", "")
        if not token:
            flash("Invalid or missing reset token.", "error")
            return redirect("/login")

        if request.method == "GET":
            csrf_token = secrets.token_hex(16)
            session["csrf_token"] = csrf_token
            return render_template("reset_password.html", csrf_token=csrf_token, token=token)

        form_csrf = request.form.get("csrf_token", "")
        if not form_csrf or form_csrf != session.pop("csrf_token", None):
            flash("Invalid request. Please try again.", "error")
            return redirect(f"/reset-password?token={token}")

        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        if new_password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(f"/reset-password?token={token}")

        resp = current_app.api_client.post("/auth/reset-password", json={"token": token, "new_password": new_password})
        if resp.ok:
            flash("Password reset successful! Please sign in.", "success")
            return redirect("/login")
        detail = resp.json().get("detail", "Reset failed. Token may be expired.") if resp.headers.get("content-type", "").startswith("application/json") else "Reset failed."
        flash(detail, "error")
        return redirect(f"/reset-password?token={token}")

    @app.route("/verify-email/<token>")
    def verify_email(token):
        """Handle email verification link."""
        resp = current_app.api_client.get(f"/auth/verify-email/{token}")
        if resp.ok:
            flash("Email verified! You can now sign in.", "success")
        else:
            detail = resp.json().get("detail", "Verification failed. Link may be expired.") if resp.headers.get("content-type", "").startswith("application/json") else "Verification failed."
            flash(detail, "error")
        return redirect("/login")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        """Simple login form — stores JWT in session."""
        if request.method == "GET":
            csrf_token = secrets.token_hex(16)
            session["csrf_token"] = csrf_token
            return render_template("login.html", next=request.args.get("next", "/dashboard"), csrf_token=csrf_token)

        # Validate CSRF token
        form_csrf = request.form.get("csrf_token", "")
        if not form_csrf or form_csrf != session.pop("csrf_token", None):
            flash("Invalid request. Please try again.", "error")
            return redirect("/login")

        email = request.form.get("email", "")
        password = request.form.get("password", "")
        resp = current_app.api_client.post("/auth/login", json={"email": email, "password": password})
        if resp.ok:
            data = resp.json()
            session["token"] = data.get("access_token")
            session["refresh_token"] = data.get("refresh_token")
            # Fetch user's full name from /users/me
            me_resp = current_app.api_client.get("/users/me", token=session["token"])
            session["user_name"] = me_resp.json().get("full_name", email) if me_resp.ok else email
            next_url = request.form.get("next", "/dashboard")
            return redirect(next_url)
        flash("Invalid email or password", "error")
        return redirect("/login")

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
        for key in ("q", "job_type", "qualification_level", "organization", "department", "recommended"):
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

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc):
        app.logger.error("Unhandled exception: %s", exc, exc_info=True)
        return render_template("404.html"), 500

    return app


# Flask CLI entry point
app = create_app()
