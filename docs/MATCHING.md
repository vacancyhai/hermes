# Eligibility Matching

Hermes checks whether a user's profile meets the criteria for a job or admission.

**Source:** `src/backend/app/services/matching.py`

---

## Overview

Eligibility is evaluated in two ways:

1. **Pre-computed (cache-first):** When a user updates their profile, or when a job/admission is created/updated, Celery tasks asynchronously compute and upsert eligibility results into the `job_eligibility` and `admission_eligibility` tables.
2. **Live fallback:** If no pre-computed row exists (e.g. new user, task not yet run), the endpoint calls the matching functions directly and returns a live result.

**Endpoints:**
- `GET /api/v1/jobs/eligibility/{slug}` — checks `job_eligibility` cache first, then live
- `GET /api/v1/admissions/eligibility/{slug}` — checks `admission_eligibility` cache first, then live

Both require a user JWT.

---

## Status Values

| Status | Meaning |
|--------|---------|
| `eligible` | All evaluated criteria passed (no failures) |
| `partially_eligible` | At least one criterion passed AND at least one failed |
| `not_eligible` | Every evaluated criterion failed (zero passes) |
| `unknown` | Profile has no usable data — user is prompted to complete their profile |

A criterion is **skipped** (not counted as pass or fail) when the required data is absent from either the job/admission record or the user profile.

---

## Profile Completeness Check

Before any criteria are evaluated, a profile is considered usable if **any** of the following are set:
- `highest_qualification`
- `category`
- `date_of_birth`
- `preferred_states`

If none are set, the response is `{"status": "unknown", "reasons": ["Complete your profile to check eligibility"]}`.

---

## Job Eligibility

**Function:** `check_job_eligibility(job, profile)` → `{"status": str, "reasons": list[str]}`

### Criteria (evaluated in order)

| # | Criterion | Job data source | Profile field |
|---|-----------|----------------|---------------|
| 1 | Education | `job.qualification_level` | `profile.highest_qualification` |
| 2 | Age | `job.eligibility.age_min`, `.age_max` | `profile.date_of_birth` |
| 3 | Category | `job.vacancy_breakdown.total_vacancy` keys | `profile.category` |
| 4 | Domicile | `job.eligibility.domicile_required` | `profile.state` |

### Education Check

Compares using a fixed level hierarchy:
```
10th < 12th < diploma < graduate < postgraduate < phd
```
Pass if `user_rank >= required_rank`. Skipped if either value is missing or unrecognised.

### Age Check

Age is computed from `profile.date_of_birth` relative to today's date. Age relaxation is added to `age_max` before comparison.

**Age relaxation** is read from `job.eligibility.age_relaxation` (JSONB dict — actual DB key format):

| DB key | Applies when |
|--------|-------------|
| `OBC` | `profile.category` is `obc` or `ebc` |
| `SC_ST` | `profile.category` is `sc` or `st` |
| `EWS` | `profile.category` is `ews` |
| `PwBD` / `PwD_UR` | `profile.is_pwd = true` |
| `Ex_Serviceman` | `profile.is_ex_serviceman = true` |

For `is_pwd` and `is_ex_serviceman`, `max(category_relaxation, special_relaxation)` is used.
If no `age_relaxation` key exists on the job, relaxation is 0.

Example: `{"OBC": 3, "SC_ST": 5, "PwBD": 10, "Ex_Serviceman": 3}`

### Category Check

Categories are derived from `job.vacancy_breakdown.total_vacancy` keys (e.g. `SC`, `ST`, `OBC`, `EWS`, `UR`, `PWD`). Only keys with `> 0` vacancy count are included. `UR` is mapped to `general` to match `profile.category`.

The `job.eligibility.category` key is also checked if present (can be a list or string).

### Domicile Check

If `job.eligibility.domicile_required` is set, `profile.state` must match (case-insensitive). Skipped if either is absent.

---

## Admission Eligibility

**Function:** `check_admission_eligibility(admission, profile)` → `{"status": str, "reasons": list[str]}`

### Criteria (evaluated in order)

| # | Criterion | Admission data source | Profile field |
|---|-----------|----------------------|---------------|
| 1 | Education | `admission.admission_type` (proxy) | `profile.highest_qualification` |
| 2 | Age | `admission.eligibility.age_limit.{min, max}` | `profile.date_of_birth` |
| 3 | Min % | `admission.eligibility.min_percentage` | `profile.education.percentage` |
| 4 | Domicile | `admission.eligibility.domicile_required` | `profile.state` |

### Education Proxy

`eligibility.qualification` is free-text and cannot be compared structurally. `admission_type` is used as a structured proxy:

| `admission_type` | Required level |
|-----------------|----------------|
| `ug` | `12th` |
| `pg` | `graduate` |
| `doctoral`, `lateral`, other | Skipped (no proxy mapping) |

### Age — No Relaxation

Admissions use `eligibility.age_limit.{min, max}` (integers; `0` = no limit). **No age relaxation dict** is applied for admissions — any relaxation info is free-text in `eligibility.notes` and is not evaluated programmatically.

### Min Percentage

`eligibility.min_percentage` (integer; `0` or absent = skip). Compared against `profile.education.percentage` (from the JSONB `education` field). Skipped if either value is absent.

---

## Pre-Computation (Celery Tasks)

Three tasks in `app/tasks/eligibility.py`:

| Task | Triggered when | Action |
|------|---------------|--------|
| `recompute_eligibility_for_user(user_id)` | User updates profile | Runs against all `active`/`upcoming` jobs + admissions; upserts into `job_eligibility` + `admission_eligibility` |
| `recompute_eligibility_for_job(job_id)` | Job created or updated | Runs against all users who have a profile; upserts into `job_eligibility`. If job status is not `active`/`upcoming`, **purges** all rows for that job instead |
| `recompute_eligibility_for_admission(admission_id)` | Admission created or updated | Same pattern as job task but for `admission_eligibility` |

Upserts use PostgreSQL `ON CONFLICT DO UPDATE` on the unique constraints `uq_job_elig_user_job` and `uq_adm_elig_user_admission`.

---

## Adding New Criteria

1. Add a new `_check_*` helper function in `matching.py` following the existing pattern (appends to `passed`, `failed`, `reasons` lists; skips silently when data is absent).
2. Call it inside `check_job_eligibility` (or `check_admission_eligibility`) after the existing checks.
3. Ensure the corresponding field exists on `UserProfile` (and is exposed in `ProfileUpdateRequest` / `ProfileResponse`).
4. If it requires a new `eligibility` JSONB key, document the key name and expected format in this file.
