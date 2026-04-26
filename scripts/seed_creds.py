"""Seed script — creates admin users, test users with profiles, and Firebase Auth users.

Admins seeded (admin_users table):
  - admin@hermes.com    / Admin@123  (role: admin)
  - operator@hermes.com / Oper@123   (role: operator)

Test users seeded (users + user_profiles tables):
  - user1@hermes.com / User@123  (Graduate, General, Maharashtra)
  - user2@hermes.com / User@123  (Graduate, OBC, Delhi)
  - user3@hermes.com / User@123  (Post-graduate, SC, Tamil Nadu)

Firebase Auth users are also created for the 3 test users and their firebase_uid
is linked back to the PostgreSQL users row.

Usage:
    docker cp scripts/seed_creds.py hermes_backend:/app/seed_creds.py
    docker exec hermes_backend python seed_creds.py

Re-runnable: existing emails are skipped in both PostgreSQL and Firebase.
"""

import os
import uuid
from datetime import date, datetime, timezone

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from app.models.admin_user import AdminUser
from app.models.user import User
from app.models.user_profile import UserProfile
from passlib.context import CryptContext
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

_DB_URL = os.environ["DATABASE_URL"].replace("+asyncpg", "+psycopg2").replace(
    "pgbouncer:5432", "postgresql:5432"
)
_CREDS_PATH = os.environ.get("FIREBASE_CREDENTIALS_PATH", "/app/secrets/firebase-credentials.json")
_engine = create_engine(_DB_URL)

# ---------------------------------------------------------------------------
# Admin accounts
# ---------------------------------------------------------------------------

_USER_PASS = "User@123"  # pragma: allowlist secret

ADMINS = [
    {
        "email": "admin@hermes.com",
        "password": "Admin@123",  # pragma: allowlist secret
        "full_name": "Super Admin",
        "role": "admin",
        "department": "Platform",
        "phone": None,
    },
    {
        "email": "operator@hermes.com",
        "password": "Oper@123",  # pragma: allowlist secret
        "full_name": "Content Operator",
        "role": "operator",
        "department": "Content",
        "phone": None,
    },
]

# ---------------------------------------------------------------------------
# Test users
# ---------------------------------------------------------------------------

USERS = [
    {
        "email": "user1@hermes.com",
        "password": _USER_PASS,
        "full_name": "Rahul Sharma",
        "phone": None,
        "profile": {
            "date_of_birth": date(1998, 5, 15),
            "gender": "Male",
            "category": "General",
            "is_pwd": False,
            "is_ex_serviceman": False,
            "state": "Maharashtra",
            "city": "Pune",
            "pincode": "411001",
            "highest_qualification": "graduate",
            "education": {
                "degree": "B.Sc Computer Science",
                "university": "Pune University",
                "year": 2020,
                "percentage": 72.5,
            },
            "notification_preferences": {
                "email": True,
                "push": True,
                "whatsapp": False,
            },
            "preferred_states": ["Maharashtra", "Delhi", "Karnataka"],
            "preferred_categories": ["government", "psu"],
            "followed_organizations": ["SSC", "UPSC", "IBPS"],
        },
    },
    {
        "email": "user2@hermes.com",
        "password": _USER_PASS,
        "full_name": "Priya Patel",
        "phone": None,
        "profile": {
            "date_of_birth": date(2000, 9, 22),
            "gender": "Female",
            "category": "OBC",
            "is_pwd": False,
            "is_ex_serviceman": False,
            "state": "Delhi",
            "city": "New Delhi",
            "pincode": "110001",
            "highest_qualification": "graduate",
            "education": {
                "degree": "B.Com",
                "university": "Delhi University",
                "year": 2022,
                "percentage": 68.0,
            },
            "notification_preferences": {
                "email": True,
                "push": False,
                "whatsapp": False,
            },
            "preferred_states": ["Delhi", "Uttar Pradesh", "Haryana"],
            "preferred_categories": ["banking", "government"],
            "followed_organizations": ["IBPS", "RRB", "SSC"],
        },
    },
    {
        "email": "user3@hermes.com",
        "password": _USER_PASS,
        "full_name": "Arun Kumar",
        "phone": None,
        "profile": {
            "date_of_birth": date(1995, 3, 8),
            "gender": "Male",
            "category": "SC",
            "is_pwd": False,
            "is_ex_serviceman": False,
            "state": "Tamil Nadu",
            "city": "Chennai",
            "pincode": "600001",
            "highest_qualification": "post_graduate",
            "education": {
                "degree": "M.Sc Physics",
                "university": "University of Madras",
                "year": 2019,
                "percentage": 80.0,
            },
            "notification_preferences": {
                "email": True,
                "push": True,
                "whatsapp": False,
            },
            "preferred_states": ["Tamil Nadu", "Karnataka", "Andhra Pradesh"],
            "preferred_categories": ["research", "government", "psu"],
            "followed_organizations": ["DRDO", "UPSC", "ISRO"],
        },
    },
]


# ---------------------------------------------------------------------------
# Insert helpers
# ---------------------------------------------------------------------------


def _admin_exists(session: Session, email: str) -> bool:
    return (
        session.execute(
            select(AdminUser).where(AdminUser.email == email)
        ).scalar_one_or_none()
        is not None
    )


def _user_exists(session: Session, email: str) -> bool:
    return (
        session.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()
        is not None
    )


# ---------------------------------------------------------------------------
# Firebase helpers
# ---------------------------------------------------------------------------


def _init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(_CREDS_PATH)
        firebase_admin.initialize_app(cred)


def _seed_firebase_users():
    """Create Firebase Auth users for test users and link firebase_uid to PostgreSQL."""
    _init_firebase()
    inserted = 0
    skipped = 0

    with _engine.connect() as conn:
        for data in USERS:
            try:
                fb_user = firebase_auth.get_user_by_email(data["email"])
                print(f"  SKIP  (Firebase user exists): {data['email']}  uid={fb_user.uid}")
                skipped += 1
            except firebase_auth.UserNotFoundError:
                fb_user = firebase_auth.create_user(
                    email=data["email"],
                    password=data["password"],
                    display_name=data["full_name"],
                    email_verified=True,
                )
                print(f"  CREATE Firebase user: {data['email']}  uid={fb_user.uid}")
                inserted += 1

            result = conn.execute(
                text("UPDATE users SET firebase_uid = :uid WHERE email = :email RETURNING id"),
                {"uid": fb_user.uid, "email": data["email"]},
            )
            if result.rowcount:
                print(f"    LINKED firebase_uid → users.email={data['email']}")
            else:
                print(f"    WARN: No PostgreSQL user found for {data['email']}")

        conn.commit()

    print(f"\nFirebase — {inserted} users created, {skipped} skipped.")


def seed():
    admin_inserted = 0
    admin_skipped = 0
    user_inserted = 0
    user_skipped = 0

    with Session(_engine) as session:
        # --- Admins ---
        for data in ADMINS:
            if _admin_exists(session, data["email"]):
                print(f"  SKIP admin: {data['email']}")
                admin_skipped += 1
                continue
            admin = AdminUser(
                id=uuid.uuid4(),
                email=data["email"],
                password_hash=_pwd_ctx.hash(data["password"]),
                full_name=data["full_name"],
                role=data["role"],
                department=data.get("department"),
                phone=data.get("phone"),
                permissions={},
                status="active",
                is_email_verified=True,
            )
            session.add(admin)
            print(f"  INSERT admin: {data['email']}  (role={data['role']})")
            admin_inserted += 1

        session.flush()

        # --- Users + Profiles ---
        for data in USERS:
            if _user_exists(session, data["email"]):
                print(f"  SKIP user: {data['email']}")
                user_skipped += 1
                continue
            user_id = uuid.uuid4()
            user = User(
                id=user_id,
                email=data["email"],
                password_hash=_pwd_ctx.hash(data["password"]),
                full_name=data["full_name"],
                phone=data.get("phone"),
                firebase_uid=None,
                migration_status="native",
                status="active",
                is_verified=True,
                is_email_verified=True,
                is_phone_verified=False,
            )
            session.add(user)

            p = data["profile"]
            profile = UserProfile(
                id=uuid.uuid4(),
                user_id=user_id,
                date_of_birth=p.get("date_of_birth"),
                gender=p.get("gender"),
                category=p.get("category"),
                is_pwd=p.get("is_pwd", False),
                is_ex_serviceman=p.get("is_ex_serviceman", False),
                state=p.get("state"),
                city=p.get("city"),
                pincode=p.get("pincode"),
                highest_qualification=p.get("highest_qualification"),
                education=p.get("education", {}),
                notification_preferences=p.get("notification_preferences", {}),
                preferred_states=p.get("preferred_states", []),
                preferred_categories=p.get("preferred_categories", []),
                followed_organizations=p.get("followed_organizations", []),
                fcm_tokens=[],
            )
            session.add(profile)
            print(f"  INSERT user: {data['email']}  ({p['category']}, {p['state']})")
            user_inserted += 1

        session.commit()

    print(
        f"\nPostgreSQL — {admin_inserted} admins + {user_inserted} users inserted, "
        f"{admin_skipped + user_skipped} skipped."
    )

    # --- Firebase users ---
    print("\nSeeding Firebase Auth users...")
    _seed_firebase_users()

    print("\nCredentials:")
    print("  Admin:    admin@hermes.com    / Admin@123")
    print("  Operator: operator@hermes.com / Oper@123")
    print("  User 1:   user1@hermes.com    / User@123")
    print("  User 2:   user2@hermes.com    / User@123")
    print("  User 3:   user3@hermes.com    / User@123")
    print("\nPostman test flow:")
    print("  1. Set {{firebase_web_api_key}} in collection variables")
    print("  2. Run 'Step 1 — Get Firebase ID Token' with user1@hermes.com / User@123")
    print("  3. Run 'Step 2 — Verify Firebase Token' → sets {{user_token}}")


if __name__ == "__main__":
    seed()
