# Email Template Usage Documentation

## Active Templates (Used in Production)

### 1. `deadline_reminder.html`
**Used by:** `app/tasks/notifications.py`
**Purpose:** Sends deadline reminders for job applications (7/3/1 day before)
**Status:** ✅ Active

### 2. `new_job_alert.html`
**Used by:** `app/tasks/notifications.py`
**Purpose:** Notifies users about new job postings matching their preferences
**Status:** ✅ Active

### 3. `otp.html`
**Used by:** `app/routers/auth.py`
**Purpose:** Sends OTP codes for phone verification
**Status:** ✅ Active

### 4. `welcome.html`
**Used by:** `app/routers/auth.py`
**Purpose:** Welcome email after successful registration
**Status:** ✅ Active

### 5. `email_linked.html`
**Used by:** `app/routers/auth.py`
**Purpose:** Confirmation when email is linked to existing phone-only account
**Status:** ✅ Active

---

## Phone Verification Templates

### 6. `phone_added.html`
**Used by:** `app/routers/users.py`
**Purpose:** Notification when a phone number is added to account
**Status:** ✅ Active

### 7. `phone_verified.html`
**Used by:** `app/routers/users.py`
**Purpose:** Confirmation after phone number verification
**Status:** ✅ Active

---

## Firebase Auth Templates (Reference Only)

These templates exist for potential future use or legacy compatibility, but primary auth is handled by Firebase:

### 8. `verification.html`
**Purpose:** Email verification link (Firebase handles this via their UI)
**Status:** ⚠️ Standby - Firebase currently manages email verification
**Note:** Keep for potential custom email verification flow

### 9. `password_reset.html`
**Purpose:** Password reset link (Firebase handles this via their UI)
**Status:** ⚠️ Standby - Firebase currently manages password reset
**Note:** Keep for potential custom password reset flow

### 10. `password_set.html`
**Purpose:** Password set confirmation (Firebase handles this)
**Status:** ⚠️ Standby - Firebase currently manages password operations
**Note:** Keep for potential custom password management

### 11. `password_changed.html`
**Used by:** `app/routers/users.py`
**Purpose:** Security notification when password is changed
**Status:** ✅ Active - Security notification even though Firebase manages auth

---

## Base Template

### 12. `base.html`
**Purpose:** Base layout template extended by all other email templates
**Status:** ✅ Active - Used by all templates

---

## Summary

- **Active Templates:** 8 (base, deadline_reminder, new_job_alert, otp, welcome, email_linked, phone_added, phone_verified, password_changed)
- **Standby Templates:** 3 (verification, password_reset, password_set) - Firebase handles these but templates kept for flexibility
- **Total:** 12 templates

## Recommendation

**Keep all templates.** The Firebase-managed auth templates (verification, password_reset, password_set) provide flexibility for future custom flows or migration away from Firebase if needed. They add minimal overhead.
