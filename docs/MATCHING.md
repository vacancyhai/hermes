# Eligibility Matching

Hermes checks whether a user's profile meets the criteria for a job or admission. This document covers how eligibility is determined, what data is used, and how results are returned.

## Overview

Eligibility is evaluated lazily — the jobs/admissions list loads first, then each card fires an HTMX request to fetch its eligibility badge.

When a user opens `/jobs`, the list is fetched from `GET /api/v1/jobs` with no eligibility filtering. As each card scrolls into view, an HTMX `revealed` trigger fires `GET /partials/jobs/<slug>/eligibility` on the frontend, which in turn calls `GET /api/v1/jobs/eligibility/<slug>` on the backend and returns an inline badge. The backend returns `{"status": ..., "reasons": [...]}`.

The same pattern applies to `/admissions`.

---

## Status Values

| Status | Meaning |
|--------|---------|
| `eligible` | All evaluated criteria passed |
| `partially_eligible` | At least one criterion passed, at least one failed |
| `not_eligible` | Every evaluated criterion failed |
| `unknown` | Profile has no usable data — user is prompted to complete profile |

A criterion is **skipped** (not counted) when the required data is absent from either the job/admission record or the user profile.

---

## Job Eligibility

**Source:** `src/backend/app/services/matching.py` → `check_job_eligibility(job, profile)`

**Endpoint:** `GET /api/v1/jobs/eligibility/{slug}`

### Criteria

| # | Criterion | Job field | Profile field |
|---|-----------|-----------|---------------|
| 1 | Education | `job.qualification_level` | `profile.highest_qualification` |
| 2 | Age | `eligibility.age_min`, `eligibility.age_max` | `profile.date_of_birth` |
| 3 | Category | `vacancy_breakdown.total_vacancy` keys | `profile.category` |
| 4 | Domicile | `eligibility.domicile_required` | `profile.state` |

### Age Relaxation

Age relaxation is read from `eligibility.age_relaxation` (a JSONB dict on the job). It uses the **actual DB key format** — not lowercase:

| DB key | Applies to |
|--------|-----------|
| `OBC` | profile.category = OBC or EBC |
| `SC_ST` | profile.category = SC or ST |
| `EWS` | profile.category = EWS |
| `PwBD` / `PwD_UR` | profile.is_pwd = true |
| `Ex_Serviceman` | profile.is_ex_serviceman = true |

For example: `{"OBC": 3, "SC_ST": 5, "PwBD": 10, "Ex_Serviceman": 3}`.

The effective age max becomes `age_max + relaxation`. If no `age_relaxation` dict exists on the job, no relaxation is applied (no hardcoded defaults).

### Category Matching

Job categories are derived from `vacancy_breakdown.total_vacancy`, which holds keys like `SC`, `ST`, `OBC`, `EWS`, `UR`, `PWD` with integer vacancy counts. `UR` is mapped to `general` to match `profile.category = "General"`. Only keys with `> 0` vacancies are considered eligible categories.

---

## Admission Eligibility

**Source:** `src/backend/app/services/matching.py` → `check_admission_eligibility(admission, profile)`

**Endpoint:** `GET /api/v1/admissions/eligibility/{slug}`

### Criteria

| # | Criterion | Admission field | Profile field |
|---|-----------|-----------------|---------------|
| 1 | Education | `admission.admission_type` (proxy) | `profile.highest_qualification` |
| 2 | Age | `eligibility.age_limit.min` / `.max` | `profile.date_of_birth` |
| 3 | Min % | `eligibility.min_percentage` | `profile.education.percentage` |
| 4 | Domicile | `eligibility.domicile_required` | `profile.state` |

### Education Proxy

`eligibility.qualification` is a free-text string (e.g. `"B.E./B.Tech or equivalent..."`), so it cannot be compared structurally. Instead, `admission_type` is used as a proxy:

| admission_type | Required level |
|----------------|---------------|
| `ug` | `12th` |
| `pg` | `graduate` |

### Age — No Relaxation

Admissions use `eligibility.age_limit.{min, max}` (integers, `0` = no limit). Age relaxation for admissions is mentioned only in the `eligibility.notes` free-text field and is **not applied programmatically**.

### Min Percentage

`eligibility.min_percentage` is an integer (`0` = no requirement). When set, it is compared against `profile.education.percentage`. The check is skipped if either value is missing.

---

## Profile Completeness Check

Before any criteria are evaluated, the profile is checked for minimum usable data. A profile is considered complete if **any** of the following are set:

- `highest_qualification`
- `category`
- `date_of_birth`
- `preferred_states`

If none are set, the response status is `unknown` with a message prompting the user to complete their profile.

---

## Frontend Rendering

Eligibility badges are defined in `src/frontend/app/__init__.py` (`_ELIGIBILITY_BADGE` dict) and rendered inline on each job/admission card via HTMX. Each card has a placeholder span with `hx-get` pointing to the eligibility partial and `hx-trigger="revealed"`, so the badge loads only when the card scrolls into view.

The badge is only shown when the user is logged in **and** the profile is marked complete (checked server-side via `/users/profile`). Otherwise a static "Check Eligibility" link to `/profile` is shown.

---

## Adding New Criteria

To add a new criterion to job eligibility:

1. Add a new `_check_*` helper function in `matching.py` following the existing pattern (`passed`, `failed`, `reasons` lists).
2. Call it inside `check_job_eligibility` after the existing checks.
3. Ensure the corresponding field exists on `UserProfile` and is exposed in `ProfileResponse`.
4. If it requires a new `eligibility` JSONB key, document the key name and format here.
