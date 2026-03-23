# Frontend ↔ Backend Audit Report

> Generated: 2026-03-23 | Scope: User Frontend, Admin Frontend vs Backend API

---

## Summary

| Category | Count |
|----------|-------|
| ✅ Bugs (all fixed) | 1 fixed |
| 🟡 Backend endpoints unused by any frontend | 4 |
| ✅ Endpoints correctly wired | 38+ |

---

## ✅ Fixed Bug — `GET /users/me` → `GET /users/profile`

**File:** `src/frontend/app/__init__.py` — `firebase_callback()` (line 372)

**Status: Fixed** — `/users/me` replaced with `/users/profile`.

```python
# FIXED: was /users/me (non-existent), now correctly calls /users/profile
me_resp = current_app.api_client.get("/users/profile", token=session["token"])
session["user_name"] = me_resp.json().get("full_name", "") if me_resp.ok else ""
```

**Impact before fix:** After Firebase login, `session["user_name"]` always stayed `""` because `/users/me` doesn't exist. Fixed in `firebase_callback()`.

**Regression guard:** `test_firebase_callback_success` in `src/frontend/tests/integration/test_routes.py` now asserts `mock_api.get.assert_called_once_with("/users/profile", token="jwt-access")`.

---

## 🟡 Backend Endpoints — Not Called by Any Frontend

These endpoints exist in the backend and are documented in `API.md` but no frontend currently calls them. They are intentional — either planned for future use or handled differently.

| Endpoint | Reason |
|----------|--------|
| `POST /users/me/fcm-token` | FCM token registration for push notifications. Requires JS service worker to call this after Firebase messaging setup. Not implemented in the Flask frontend yet (planned for Phase 9 / PWA enhancement). |
| `DELETE /users/me/fcm-token` | Same — part of push notification teardown on logout. |
| `GET /auth/csrf-token` | Admin frontend generates CSRF tokens locally in Flask session (`secrets.token_hex(16)`), so it never fetches from the backend. This is intentional design — the backend endpoint is available for non-Flask clients (e.g. mobile, third-party). |
| `GET /applications/{id}` | Single application detail endpoint. The dashboard shows an inline list + inline edit without navigating to a dedicated detail page, so this endpoint is never triggered. Can be used when a detail view is added. |

---

## ✅ Fully Wired Endpoints (No Gaps)

### User Frontend (`src/frontend`)

| Endpoint | Usage |
|----------|-------|
| `POST /auth/verify-token` | `/auth/firebase-callback` relay |
| `POST /auth/logout` | `/logout` route |
| `POST /auth/refresh` | `_try_refresh()` on 401 |
| `GET /jobs` | Homepage + HTMX load-more |
| `GET /jobs/recommended` | Recommended tab (requires token) |
| `GET /jobs/{slug}` | Job detail page |
| `GET /applications` | Dashboard listing |
| `GET /applications/stats` | Dashboard stats cards |
| `POST /applications` | Track application form submit |
| `PUT /applications/{id}` | Inline application update |
| `DELETE /applications/{id}` | Remove from tracker |
| `GET /notifications` | Notifications page + HTMX load-more |
| `GET /notifications/count` | Badge count (HTMX polling) |
| `PUT /notifications/{id}/read` | Mark single read |
| `PUT /notifications/read-all` | Mark all read |
| `DELETE /notifications/{id}` | Delete notification |
| `GET /users/profile` | Profile page |
| `PUT /users/profile` | Update profile fields |
| `PUT /users/profile/phone` | Update phone number |
| `GET /users/me/following` | Following list on profile page |
| `POST /organizations/{name}/follow` | Follow org button |
| `DELETE /organizations/{name}/follow` | Unfollow org button |
| `PUT /users/me/notification-preferences` | Notification settings form |

### Admin Frontend (`src/frontend-admin`)

| Endpoint | Usage |
|----------|-------|
| `POST /auth/admin/login` | Admin login form |
| `POST /auth/admin/logout` | Admin logout |
| `POST /auth/admin/refresh` | `_try_refresh()` on 401 |
| `GET /admin/stats` | Dashboard stats cards |
| `GET /admin/analytics` | Dashboard analytics (admin role only) |
| `GET /admin/jobs` | Job list + HTMX load-more |
| `GET /admin/jobs/{id}` | Draft review page (GET) |
| `POST /admin/jobs` | Create new job form |
| `POST /admin/jobs/upload-pdf` | PDF upload form |
| `PUT /admin/jobs/{id}` | Edit job (review form POST) |
| `PUT /admin/jobs/{id}/approve` | Approve draft button |
| `DELETE /admin/jobs/{id}` | Delete job (admin only) |
| `GET /admin/users` | User list + HTMX load-more |
| `GET /admin/users/{id}` | User detail page |
| `PUT /admin/users/{id}/status` | Suspend/activate user |
| `PUT /admin/users/{id}/role` | Change role (admin only) |
| `GET /admin/logs` | Audit logs + HTMX load-more |

---

## Recommendations

1. ~~**Fix immediately:** Change `/users/me` → `/users/profile` in `firebase_callback()`~~ — **Done.**
2. **Future (Phase 9 / PWA):** Wire `POST /users/me/fcm-token` and `DELETE /users/me/fcm-token` from the service worker to enable full push notification support.
3. **Future:** Add a `/dashboard/applications/{id}` detail page in the user frontend to make use of the existing `GET /applications/{id}` backend endpoint.
