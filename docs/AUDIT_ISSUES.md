# Hermes Project — Audit Issues (Hinglish)

> **Audit Date:** April 19, 2026
> Yeh document un saare gaps ko cover karta hai jo project ke full audit mein mile.
> Har issue mein: **Kya problem hai → Kyun hua → Kaise fix karein → Fix ke baad kya hoga**

---

## 🔴 Critical Issues (Abhi Fix Karni Chahiye)

---

### Issue #1 — `jobs` Table ka `links` Field Model/Schema Mein Nahi Hai

**Kya problem hai?**
Database ke `jobs` table mein ek `links JSONB` column exist karta hai (migration mein add hua tha), lekin:
- `Job` SQLAlchemy model mein yeh field nahi hai
- `JobCreateRequest` schema mein nahi hai — matlab admin job banate waqt links set nahi kar sakta
- `JobResponse` mein nahi hai — API response mein links kabhi return nahi hote
- Frontend/Admin templates mein bhi missing hai

**Kyun hua?**
Schema changes migrate karte waqt DB column add kar diya gaya tha, lekin corresponding Python model aur Pydantic schema update karna bhool gaya.

**Kaise fix karein?**
```python
# src/backend/app/models/job.py mein add karo:
links: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
```
```python
# src/backend/app/schemas/jobs.py mein add karo:
# JobCreateRequest, JobUpdateRequest, JobResponse teeno mein:
links: list = Field(default_factory=list)   # Create/Update mein
links: list                                  # Response mein
```

**Fix ke baad kya hoga?**
- Admin portal se job create/edit karte waqt links add kar sakenge
- Public API `GET /jobs/{slug}` response mein links dikhenge
- Frontend job detail page pe links render ho sakenge (application portal, notice PDF, etc.)

---

### Issue #2 — `answer_keys` Table Pe `published_at` Index Missing

**Kya problem hai?**
`answer_keys` table pe `published_at` column pe koi index nahi hai.
Admin list endpoint `_admin_list_docs` ORDER BY `published_at DESC` use karta hai — bina index ke large data pe **full table scan** hogi, query slow ho jayegi.

Compare karo:
- `admit_cards` → `idx_admit_cards_pub` ✅ exists
- `results` → `idx_results_pub` ✅ exists
- `answer_keys` → `idx_answer_keys_pub` ❌ **missing**

**Kyun hua?**
Migration consolidation ke waqt `admit_cards` aur `results` ke pub indexes copy ho gaye lekin `answer_keys` ka index accidentally skip ho gaya.

**Kaise fix karein?**
Naya migration ya existing migration mein add karo:
```sql
CREATE INDEX idx_answer_keys_pub ON answer_keys(published_at);
```
Ya Alembic migration mein:
```python
op.create_index("idx_answer_keys_pub", "answer_keys", ["published_at"])
```

**Fix ke baad kya hoga?**
- Admin `GET /admin/answer-keys` query fast ho jayegi
- Jab answer keys badhenge (thousands), ORDER BY `published_at` instantly execute hogi

---

### Issue #3 — `user_watches_*` DB Index/Constraint Names Rename Nahi Hue

**Kya problem hai?**
Table `user_watches` ko rename karke `user_tracks` kiya gaya tha, lekin DB ke andar indexes aur constraints ke naam abhi bhi purane hain:
```
user_watches_pkey          ← should be: user_tracks_pkey
ix_user_watches_user_id    ← should be: ix_user_tracks_user_id
ix_user_watches_entity     ← should be: ix_user_tracks_entity
ck_user_watches_entity_type ← should be: ck_user_tracks_entity_type
user_watches_user_id_fkey  ← FK constraint bhi purana naam
```

**Kyun hua?**
Migration mein sirf `ALTER TABLE user_watches RENAME TO user_tracks` kiya gaya, lekin index/constraint rename statements (`ALTER INDEX`, `ALTER TABLE ... RENAME CONSTRAINT`) nahi likhe gaye.

**Kaise fix karein?**
Ek naya migration banao:
```python
op.execute("ALTER INDEX user_watches_pkey RENAME TO user_tracks_pkey")
op.execute("ALTER INDEX ix_user_watches_user_id RENAME TO ix_user_tracks_user_id")
op.execute("ALTER INDEX ix_user_watches_entity RENAME TO ix_user_tracks_entity")
op.execute("ALTER TABLE user_tracks RENAME CONSTRAINT ck_user_watches_entity_type TO ck_user_tracks_entity_type")
op.execute("ALTER TABLE user_tracks RENAME CONSTRAINT user_watches_user_id_fkey TO user_tracks_user_id_fkey")
```

**Fix ke baad kya hoga?**
- DB schema properly clean ho jayega
- Future developers confuse nahi honge "watch" aur "track" ke beech
- `\d user_tracks` clean output dikhayega

---

## 🟡 Functional Stubs (Incomplete Features)

---

### Issue #4 — `send_new_job_notifications` Kuch Karta Hi Nahi

**Kya problem hai?**
Celery task `send_new_job_notifications(job_id)` registered hai lekin body sirf `pass` hai:
```python
@celery.task(name="app.tasks.notifications.send_new_job_notifications")
def send_new_job_notifications(job_id: str):
    """Notify users who follow the job's organization when a new job is posted."""
    pass   # ← kuch nahi hota!
```
Email template `new_job_alert.html` exist karta hai. Docs mein bhi yeh feature documented hai. Lekin actually **koi user ko notification nahi milti** jab naya job post hota hai.

**Kyun hua?**
Feature design tha — `followed_organizations` field `user_profiles` mein hai — lekin implementation puri nahi ki gayi. Placeholder chhod diya gaya.

**Kaise fix karein?**
```python
def send_new_job_notifications(job_id: str):
    with Session(sync_engine) as session:
        row = session.execute(
            text("SELECT job_title, organization, slug FROM jobs WHERE id = :id"),
            {"id": job_id}
        ).fetchone()
        if not row:
            return
        job_title, org, slug = row
        # Users jinhone yeh org follow kiya hai
        users = session.execute(
            text("""
                SELECT u.id, u.email FROM users u
                JOIN user_profiles p ON p.user_id = u.id
                WHERE p.followed_organizations @> :org_json
                  AND u.status = 'active'
            """),
            {"org_json": json.dumps([org])}
        ).fetchall()
        for user_id, _ in users:
            smart_notify.delay(
                user_id=str(user_id),
                title=f"New Job: {job_title}",
                message=f"{org} ne ek nayi vacancy post ki hai.",
                notification_type="new_job_from_followed_org",
                entity_type="job", entity_id=job_id,
                action_url=f"/jobs/{slug}",
                email_template="new_job_alert.html",
                email_context={"job_title": job_title, "organization": org, "url": f"/jobs/{slug}"},
            )
```
Phir `admin.py` mein job create hone ke baad `send_new_job_notifications.delay(str(job.id))` call karo.

**Fix ke baad kya hoga?**
- Jab admin naya job create karega, uss organization ke followers ko turant notification milegi
- `new_job_alert.html` email bhi jayegi
- "Follow Organization" feature actually useful ban jayega

---

### Issue #5 — `notify_priority_subscribers` Bhi Sirf `pass` Hai

**Kya problem hai?**
Same problem — registered Celery task, body sirf `pass`.

**Kyun hua?**
Feature scope mein tha ("priority subscribers" jo kisi job ke updates pe alert chahte hain), lekin implement nahi kiya gaya.

**Kaise fix karein?**
Ya toh implement karo (similar to `send_new_job_notifications`) ya phir task ko codebase se remove karo taaki confusion na ho. Koi bhi isko call nahi karta abhi — dead code hai.

**Fix ke baad kya hoga?**
- Agar implement karein: users priority alerts pe subscribe kar sakte hain
- Agar remove karein: codebase clean hogi, maintenance burden kam hoga

---

### Issue #6 — WhatsApp Delivery Sirf Placeholder Hai

**Kya problem hai?**
`_send_whatsapp_message()` method code mein hai lekin actually kuch nahi bhejta:
- `WHATSAPP_API_TOKEN` set nahi hoga toh function return ho jata hai silently
- Log mein `whatsapp_skipped` aata hai
- User ke notification preferences mein `whatsapp: true` ho phir bhi koi message nahi milta

**Kyun hua?**
WhatsApp Business API integration expensive/complex thi. Placeholder rakha gaya "future use" ke liye.

**Kaise fix karein?**
Do options hain:
1. **WhatsApp Business API integrate karo** (Meta Cloud API ya Twilio) — `WHATSAPP_API_TOKEN` aur `WHATSAPP_PHONE_ID` env vars mein rakho
2. **Ya notification preferences mein `whatsapp` option hide karo** frontend pe taaki users enable na kar sakein jab tak ready na ho

**Fix ke baad kya hoga?**
- Users ko real WhatsApp messages milenge job deadline reminders ke liye
- Notification preferences ka `whatsapp` toggle actually kaam karega

---

## 🟠 Test Coverage Gaps

---

### Issue #7 — New Doc Schema Fields Ke Liye Koi Test Nahi

**Kya problem hai?**
`admit_cards`, `answer_keys`, `results` ke create/update/read endpoints naye fields use karte hain (`slug`, `links`, `exam_start`/`exam_end`, `start_date`/`end_date`), lekin integration tests mein yeh fields test nahi hote. Purane test cases (agar hain) shayad purane fields check karte hain.

**Kyun hua?**
Schema refactor ke saath tests update karna miss ho gaya.

**Kaise fix karein?**
`tests/integration/test_content.py` mein test cases add karo:
```python
def test_create_admit_card_with_links(admin_client, job):
    resp = admin_client.post("/api/v1/admin/admit-cards", json={
        "job_id": str(job.id),
        "slug": "test-admit-card",
        "title": "Test Admit Card",
        "links": [{"label": "Download", "url": "https://example.com"}],
        "exam_start": "2026-05-01",
        "exam_end": "2026-05-15",
    })
    assert resp.status_code == 201
    assert resp.json()["slug"] == "test-admit-card"
    assert len(resp.json()["links"]) == 1
```

**Fix ke baad kya hoga?**
- Schema regression catch hogi agar koi future mein fields change kare
- CI mein confidence badhi rahegi

---

### Issue #8 — `GET /exam-reminders` Endpoint Ka Koi Test Nahi

**Kya problem hai?**
`/api/v1/exam-reminders` endpoint exist karta hai aur frontend pe use hota hai (dashboard page), lekin backend tests mein iska koi test case nahi hai.

**Kyun hua?**
Naya endpoint add hua, test likhna reh gaya.

**Kaise fix karein?**
```python
def test_exam_reminders_empty(client):
    resp = client.get("/api/v1/exam-reminders")
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "total" in resp.json()
```

**Fix ke baad kya hoga?**
- Endpoint ka basic contract verified rahega
- Agar koi future mein logic todega, CI fail karega

---

### Issue #9 — Track Status Endpoints (`GET /jobs/{id}/track`) Ka Test Nahi

**Kya problem hai?**
Track karna (`POST /track`) aur untrack karna (`DELETE /track`) ke tests hain shayad, lekin **status check** (`GET /jobs/{id}/track` → `{"tracking": true/false}`) ka koi test nahi.

**Kaise fix karein?**
```python
def test_track_status_not_tracking(user_client, job):
    resp = user_client.get(f"/api/v1/jobs/{job.id}/track")
    assert resp.status_code == 200
    assert resp.json()["tracking"] == False

def test_track_status_after_tracking(user_client, job):
    user_client.post(f"/api/v1/jobs/{job.id}/track")
    resp = user_client.get(f"/api/v1/jobs/{job.id}/track")
    assert resp.json()["tracking"] == True
```

---

## 🟠 Admin UI / Frontend Gaps

---

### Issue #10 — Admin Doc Form Mein `published_at` Field Nahi Hai

**Kya problem hai?**
Jab admin job ya admission ke liye admit card, answer key, ya result add karta hai, form mein `published_at` date field nahi hai. Isliye:
- Naye docs hamesha `published_at = NULL` ke saath create hote hain
- `_admin_list_docs` ORDER BY `published_at DESC NULLS LAST` karta hai — null wale items hamesha list ke **end** mein aate hain
- Public endpoints bhi published_at se order karte hain — naye docs public listing mein neeche dikhte hain

**Kyun hua?**
Form HTML mein `published_at` input field add karna bhool gaye.

**Kaise fix karein?**
`src/frontend-admin/app/templates/jobs/job_edit.html` aur `admissions/admission_edit.html` ke add-doc forms mein:
```html
<label>Published At (optional)</label>
<input type="datetime-local" name="published_at">
```
Aur `__init__.py` mein `_add_doc()` helper mein:
```python
payload["published_at"] = form.get("published_at") or None
```

**Fix ke baad kya hoga?**
- Admin newly created docs ko "published" mark kar sakenge
- Docs sahi order mein listing pe dikhenge — latest published pehle

---

### Issue #11 — Public Frontend Pe Admit Card/Answer Key/Result Detail Pages Nahi Hain

**Kya problem hai?**
Backend pe ye public endpoints exist karte hain:
- `GET /api/v1/admit-cards/{slug}`
- `GET /api/v1/answer-keys/{slug}`
- `GET /api/v1/results/{slug}`

Lekin `src/frontend/app/__init__.py` mein koi route nahi hai in slugs ko render karne ke liye. User kisi admit card ke detail page pe ja hi nahi sakta directly.

**Kyun hua?**
Backend API ready hai, lekin frontend routes aur templates banana reh gaya.

**Kaise fix karein?**
`src/frontend/app/__init__.py` mein:
```python
@bp.route("/admit-cards/<slug>")
def admit_card_detail(slug):
    resp = current_app.api_client.get(f"/admit-cards/{slug}")
    if not resp.ok:
        abort(404)
    return render_template("admit_cards/detail.html", card=resp.json())
```
Similarly answer keys aur results ke liye.

**Fix ke baad kya hoga?**
- Users direct URL se admit card detail dekh sakenge
- Share button aur SEO ke liye proper URLs ban sakenge
- Notifications mein `action_url` actually kisi useful page pe le jayega

---

## 🟡 Docs Gaps (Minor)

---

### Issue #12 — `DESIGN.md` Status Line Purana Hai

**Kya problem hai?**
`DESIGN.md` line 3 pe:
> "Phase 8 (OCI deployment) next"

Yeh status ab accurate nahi hai — rename/refactor aur multiple phases already complete ho chuki hain.

**Kaise fix karein?**
Update karo to reflect current state aur pending items.

---

### Issue #13 — `DIAGRAMS.md` ERD Mein `USER_TRACKS` Label Galat Spacing

**Kya problem hai?**
ERD mein `USER_TRACKS entity` section mein `entity_type = 'admission'` ke baad extra spaces hain — cosmetic issue.

---

## 📋 Priority Order (Kya Pehle Fix Karein)

| Priority | Issue | Effort | Impact |
|----------|-------|--------|--------|
| 🔴 P1 | #1 — `jobs.links` model/schema mein add karo | Low (30 min) | High — field completely missing |
| 🔴 P1 | #2 — `answer_keys` published_at index | Low (10 min) | Medium — performance |
| 🔴 P1 | #3 — DB index names rename | Low (15 min) | Medium — cleanliness |
| 🟡 P2 | #10 — Admin form mein `published_at` add karo | Low (20 min) | High — docs order broken |
| 🟡 P2 | #4 — `send_new_job_notifications` implement karo | Medium (2 hrs) | High — follow org feature broken |
| 🟡 P2 | #11 — Frontend detail page routes | Medium (2 hrs) | High — UX gap |
| 🟠 P3 | #7, #8, #9 — Test coverage add karo | Medium (3 hrs) | Medium — CI confidence |
| 🟠 P3 | #5 — Stub task remove ya implement karo | Low (30 min) | Low — dead code |
| 🟠 P3 | #6 — WhatsApp ya hide karo | High (1 day) | Low (optional feature) |
| 🟡 P4 | #12, #13 — Docs update | Low (15 min) | Low |

---

## 🔧 Quick Wins (< 1 hour mein fix)

Yeh 4 issues ek saath fix kar sakte ho ek single PR mein:

1. `jobs.links` model + schema mein add karo
2. `answer_keys` published_at migration/index add karo
3. `user_tracks` DB indexes rename karo
4. Admin add-doc form mein `published_at` field add karo
