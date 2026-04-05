"""Firebase Admin SDK — shared initialization for Auth + FCM."""

import firebase_admin
from app.config import settings
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials


def init_firebase() -> bool:
    """Initialize Firebase Admin SDK once. Returns True if ready."""
    if firebase_admin._apps:
        return True
    if not settings.FIREBASE_CREDENTIALS_PATH:
        return False
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)
    return True


def verify_id_token(id_token: str) -> dict:
    """Verify a Firebase ID token. Returns decoded claims dict.

    Raises ValueError if Firebase is not configured.
    Raises firebase_admin.auth.InvalidIdTokenError if token is invalid/expired.
    """
    if not init_firebase():
        raise ValueError("Firebase not configured")
    return firebase_auth.verify_id_token(id_token)
