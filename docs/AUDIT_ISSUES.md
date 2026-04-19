# Hermes Project — Audit Issues (Hinglish)

> **Audit Date:** April 19, 2026
> Yeh document un saare gaps ko cover karta hai jo project ke full audit mein mile.
> Har issue mein: **Kya problem hai → Kyun hua → Kaise fix karein → Fix ke baad kya hoga**
>
> **Fixed so far:** #1 (jobs.links), #2 (answer_keys index), #3 (user_tracks rename), #4 (send_new_job_notifications implemented), #5 (notify_priority_subscribers dead code removed), #10 (published_at form), #11 (detail pages already existed), #12 (DESIGN.md status line)
> **Skipped:** #7/#8/#9 (tests — deferred), #6 (WhatsApp — silently skips already), #13 (cosmetic spacing — already aligned)

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

##  Docs Gaps (Minor)

---

### Issue #13 — `DIAGRAMS.md` ERD Mein `USER_TRACKS` Label Galat Spacing

**Kya problem hai?**
ERD mein `USER_TRACKS entity` section mein `entity_type = 'admission'` ke baad extra spaces hain — cosmetic issue.

---

## 📋 Priority Order (Remaining Issues)

| Priority | Issue | Effort | Impact |
|----------|-------|--------|--------|
| 🟡 P1 | #4 — `send_new_job_notifications` implement karo | Medium (2 hrs) | High — follow org feature broken |
| 🟠 P2 | #7, #8, #9 — Test coverage add karo | Medium (3 hrs) | Medium — CI confidence |
| 🟠 P2 | #5 — Stub task remove ya implement karo | Low (30 min) | Low — dead code |
| 🟠 P2 | #6 — WhatsApp ya hide karo | High (1 day) | Low (optional feature) |
| 🟡 P3 | #13 — `DIAGRAMS.md` spacing fix | Low (5 min) | Low |
