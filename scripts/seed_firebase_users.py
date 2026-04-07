"""Seed script — creates Firebase Auth users for the 3 test users in seed_creds.py
and links them to the existing PostgreSQL users by firebase_uid.

Run AFTER seed_creds.py.

Usage:
    docker cp scripts/seed_firebase_users.py hermes_backend:/app/seed_firebase_users.py
    docker exec hermes_backend python seed_firebase_users.py

Re-runnable: existing Firebase users are skipped (matched by email).
After running, Step 1 in Postman (Firebase REST sign-in) will work.
"""

import os

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from sqlalchemy import create_engine, text

_DB_URL = os.environ["DATABASE_URL"].replace("+asyncpg", "+psycopg2")
_CREDS_PATH = os.environ.get("FIREBASE_CREDENTIALS_PATH", "/app/secrets/firebase-credentials.json")

_TEST_USER_PASS = "UserPass123!"  # pragma: allowlist secret

_TEST_USERS = [
    {"email": "user1@example.com", "password": _TEST_USER_PASS, "display_name": "Rahul Sharma"},
    {"email": "user2@example.com", "password": _TEST_USER_PASS, "display_name": "Priya Patel"},
    {"email": "user3@example.com", "password": _TEST_USER_PASS, "display_name": "Arun Kumar"},
]


def _init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(_CREDS_PATH)
        firebase_admin.initialize_app(cred)


def seed():
    _init_firebase()
    engine = create_engine(_DB_URL)

    inserted = 0
    skipped = 0

    with engine.connect() as conn:
        for user in _TEST_USERS:
            # Check if Firebase user already exists
            try:
                fb_user = firebase_auth.get_user_by_email(user["email"])
                print(f"  SKIP  (Firebase user exists): {user['email']}  uid={fb_user.uid}")
                skipped += 1
            except firebase_auth.UserNotFoundError:
                # Create in Firebase
                fb_user = firebase_auth.create_user(
                    email=user["email"],
                    password=user["password"],
                    display_name=user["display_name"],
                    email_verified=True,
                )
                print(f"  CREATE Firebase user: {user['email']}  uid={fb_user.uid}")
                inserted += 1

            # Link firebase_uid to PostgreSQL user
            result = conn.execute(
                text("UPDATE users SET firebase_uid = :uid WHERE email = :email RETURNING id"),
                {"uid": fb_user.uid, "email": user["email"]},
            )
            updated = result.rowcount
            if updated:
                print(f"    LINKED firebase_uid → users.email={user['email']}")
            else:
                print(f"    WARN: No PostgreSQL user found for {user['email']}")

        conn.commit()

    print(f"\nDone — {inserted} Firebase users created, {skipped} skipped.")
    print("\nPostman test flow:")
    print("  1. Set {{firebase_web_api_key}} in collection variables")
    print("  2. Run 'Step 1 — Get Firebase ID Token' with user1@example.com / UserPass123!")
    print("  3. Run 'Step 2 — Verify Firebase Token' → sets {{user_token}}")


if __name__ == "__main__":
    seed()
