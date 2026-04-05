# Email Notifications

Hermes automatically sends email notifications for various user account actions to keep users informed of security-related changes.

## Email Templates

All email templates are located in `src/backend/app/templates/email/` and extend the base template for consistent branding.

### Authentication & Registration

| Template | Trigger | Variables |
|----------|---------|-----------|
| `welcome.html` | User completes registration OR Google OAuth user signs in for first time | `name`, `base_url` |
| `otp.html` | User requests email OTP during registration | `name`, `otp`, `expires_minutes` |
| `verification.html` | Email verification required | `name`, `verification_url` |

### Password Management

| Template | Trigger | Variables |
|----------|---------|-----------|
| `password_set.html` | Google OAuth user sets password for first time | `name`, `timestamp`, `base_url` |
| `password_changed.html` | User changes their password | `name`, `timestamp`, `base_url` |

### Phone Management

| Template | Trigger | Variables |
|----------|---------|-----------|
| `phone_added.html` | User adds/updates phone number | `name`, `phone`, `timestamp`, `base_url` |
| `phone_verified.html` | User successfully verifies phone number with OTP | `name`, `phone`, `timestamp`, `base_url` |

### Account Linking

| Template | Trigger | Variables |
|----------|---------|-----------|
| `email_linked.html` | Phone-only user links email+password to account | `name`, `email`, `phone`, `timestamp`, `base_url` |

## Email Notification Flow

Email notifications are sent asynchronously using Celery tasks:

```python
from app.tasks.notifications import send_email_notification

send_email_notification.delay(
    email_address,
    subject,
    template_path,
    context_vars
)
```

### Configuration

Email settings are configured in `.env`:

```env
MAIL_ENABLED=true
MAIL_SERVER=mailpit           # Use mailpit for development
MAIL_PORT=1025
MAIL_USE_TLS=false
MAIL_DEFAULT_SENDER=noreply@hermes.example.com
```

**Development:** Emails are captured by Mailpit (web UI at `http://localhost:8025`)
**Production:** Configure SMTP server with TLS enabled

## Security Features

1. **No Sensitive Data:** Emails never include passwords or OTPs (except in dedicated OTP email)
2. **Timestamp Tracking:** All security-related emails include UTC timestamp
3. **Action Confirmation:** Users are notified of all account changes
4. **Base URL:** Links point to configured `FRONTEND_URL` environment variable

## Password Requirements

All password-related operations enforce these requirements:
- **Minimum 8 characters**
- **At least 1 uppercase letter**
- **At least 1 special character** (!@#$%^&*(),.?":{}|<>)

Validation is performed both client-side (JavaScript) and server-side (Pydantic schema).

## Testing

Email notifications can be tested in development:

1. **Mailpit UI:** Visit `http://localhost:8025` to see all sent emails
2. **Unit Tests:** Mock `send_email_notification.delay()` in tests
3. **Integration Tests:** Use test database to trigger actual email sends (captured by Mailpit)

## Email Notification Events

### User Actions

| Action | Email Sent | Additional Actions |
|--------|------------|-------------------|
| Complete registration (email/password) | Welcome email | Creates user account |
| Google OAuth first login | Welcome email | Creates user account |
| Request email OTP | OTP email | Stores OTP in Redis (10 min expiry) |
| Set password (Google user) | Password set confirmation | Updates Firebase auth |
| Change password | Password changed confirmation | Updates Firebase auth |
| Add/update phone number | Phone added notification | Marks phone as unverified |
| Verify phone with OTP | Phone verified confirmation | Sets `is_phone_verified = true` |
| Link email to phone account | Email linked confirmation | Updates Firebase auth, links email |

### Admin Actions

Admin panel actions do not trigger email notifications to the affected user (to prevent spam from bulk operations).

## Rate Limiting

Email sending is indirectly rate-limited through:
- **Endpoint rate limits** (e.g., 5/minute for password change)
- **Redis OTP limits** (10-minute expiry prevents rapid OTP requests)
- **Celery task queuing** (prevents email server overload)

## Future Enhancements

Planned email notification improvements:
- [ ] Account suspension/reactivation notifications
- [ ] Job application status updates
- [ ] Weekly digest of new jobs from followed organizations
- [ ] Deadline reminders for applied jobs
- [ ] Password reset confirmation emails
