"""Eligibility checking engine — determines if a user is eligible for a job or admission.

check_job_eligibility(job, profile)       -> {"status": ..., "reasons": [...]}
check_admission_eligibility(adm, profile) -> {"status": ..., "reasons": [...]}

Status values:
  "eligible"           — all available criteria pass
  "partially_eligible" — at least one criterion passes, at least one fails
  "not_eligible"       — every checked criterion fails
  "unknown"            — profile has no data to evaluate against (prompt user to complete profile)
"""

from datetime import date

# Education level hierarchy (higher index = higher qualification)
EDUCATION_LEVELS = ["10th", "12th", "diploma", "graduate", "postgraduate", "phd"]


def _education_rank(level: str | None) -> int:
    if not level:
        return -1
    try:
        return EDUCATION_LEVELS.index(level.lower())
    except ValueError:
        return -1


def _user_age(dob: date | None) -> int | None:
    if not dob:
        return None
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _profile_complete(profile) -> bool:
    """Return True if the profile has enough data to evaluate eligibility."""
    if not profile:
        return False
    return bool(
        profile.highest_qualification
        or profile.category
        or profile.date_of_birth
        or profile.preferred_states
    )


def _resolve_status(passed: list[bool], failed: list[bool]) -> str:
    """Given lists of passed/failed criteria, return the eligibility status string."""
    n_pass = sum(passed)
    n_fail = sum(failed)
    if n_pass == 0 and n_fail == 0:
        return "unknown"
    if n_fail == 0:
        return "eligible"
    if n_pass == 0:
        return "not_eligible"
    return "partially_eligible"


def check_job_eligibility(job, profile) -> dict:
    """Check whether a user's profile meets the eligibility criteria for a job.

    Returns {"status": str, "reasons": list[str]}
    """
    if not _profile_complete(profile):
        return {
            "status": "unknown",
            "reasons": ["Complete your profile to check eligibility"],
        }

    reasons: list[str] = []
    passed: list[bool] = []
    failed: list[bool] = []

    eligibility = job.eligibility if isinstance(job.eligibility, dict) else {}

    # ── Education ────────────────────────────────────────────────────────────
    job_edu_rank = _education_rank(job.qualification_level)
    user_edu_rank = _education_rank(profile.highest_qualification if profile else None)
    if job_edu_rank >= 0:
        if user_edu_rank >= 0:
            if user_edu_rank >= job_edu_rank:
                passed.append(True)
                reasons.append(
                    f"Your qualification ({profile.highest_qualification})"
                    f" meets the requirement ({job.qualification_level})"
                )
            else:
                failed.append(True)
                reasons.append(
                    f"Required qualification: {job.qualification_level} — yours: {profile.highest_qualification}"
                )
        # if user edu unknown, skip criterion

    # ── Age ──────────────────────────────────────────────────────────────────
    age_min = eligibility.get("age_min")
    age_max = eligibility.get("age_max")
    user_age = _user_age(profile.date_of_birth if profile else None)
    if (age_min is not None or age_max is not None) and user_age is not None:
        age_ok = True
        msg_parts = []
        if age_min is not None and user_age < int(age_min):
            age_ok = False
            msg_parts.append(f"minimum age is {age_min}")
        if age_max is not None and user_age > int(age_max):
            age_ok = False
            msg_parts.append(f"maximum age is {age_max}")
        if age_ok:
            passed.append(True)
            reasons.append(f"Age {user_age} is within the eligible range")
        else:
            failed.append(True)
            reasons.append(
                f"Age {user_age} does not meet criteria: {', '.join(msg_parts)}"
            )

    # ── Category ─────────────────────────────────────────────────────────────
    job_cats: set[str] = set()
    if isinstance(job.vacancy_breakdown, dict):
        job_cats = {k.lower() for k in job.vacancy_breakdown}
    cat_val = eligibility.get("category")
    if isinstance(cat_val, list):
        job_cats.update(c.lower() for c in cat_val)
    elif isinstance(cat_val, str):
        job_cats.add(cat_val.lower())

    user_cat = profile.category.lower() if (profile and profile.category) else None
    if job_cats and user_cat:
        if user_cat in job_cats:
            passed.append(True)
            reasons.append(f"Your category ({profile.category}) is eligible")
        else:
            failed.append(True)
            reasons.append(
                f"Your category ({profile.category}) is not in the eligible list"
            )

    status = _resolve_status(passed, failed)
    return {"status": status, "reasons": reasons}


def check_admission_eligibility(admission, profile) -> dict:
    """Check whether a user's profile meets the eligibility criteria for an admission.

    Returns {"status": str, "reasons": list[str]}
    """
    if not _profile_complete(profile):
        return {
            "status": "unknown",
            "reasons": ["Complete your profile to check eligibility"],
        }

    reasons: list[str] = []
    passed: list[bool] = []
    failed: list[bool] = []

    eligibility = (
        admission.eligibility if isinstance(admission.eligibility, dict) else {}
    )

    # ── Education ────────────────────────────────────────────────────────────
    qual_req = eligibility.get("qualification") or eligibility.get("min_qualification")
    req_edu_rank = _education_rank(qual_req)
    user_edu_rank = _education_rank(profile.highest_qualification if profile else None)

    # Also use admission_type as a proxy: ug→12th, pg→graduate
    if req_edu_rank < 0 and admission.admission_type:
        type_map = {"ug": "12th", "pg": "graduate"}
        qual_req = type_map.get(admission.admission_type.lower())
        req_edu_rank = _education_rank(qual_req)

    if req_edu_rank >= 0 and user_edu_rank >= 0:
        if user_edu_rank >= req_edu_rank:
            passed.append(True)
            reasons.append(
                f"Your qualification ({profile.highest_qualification}) meets the requirement ({qual_req})"
            )
        else:
            failed.append(True)
            reasons.append(
                f"Required qualification: {qual_req} — yours: {profile.highest_qualification}"
            )

    # ── Age ──────────────────────────────────────────────────────────────────
    age_min = eligibility.get("age_min") or eligibility.get("min_age")
    age_max = eligibility.get("age_max") or eligibility.get("max_age")
    user_age = _user_age(profile.date_of_birth if profile else None)
    if (age_min is not None or age_max is not None) and user_age is not None:
        age_ok = True
        msg_parts = []
        if age_min is not None and user_age < int(age_min):
            age_ok = False
            msg_parts.append(f"minimum age is {age_min}")
        if age_max is not None and user_age > int(age_max):
            age_ok = False
            msg_parts.append(f"maximum age is {age_max}")
        if age_ok:
            passed.append(True)
            reasons.append(f"Age {user_age} is within the eligible range")
        else:
            failed.append(True)
            reasons.append(
                f"Age {user_age} does not meet criteria: {', '.join(msg_parts)}"
            )

    # ── Category ─────────────────────────────────────────────────────────────
    adm_cats: set[str] = set()
    cat_val = eligibility.get("category")
    if isinstance(cat_val, list):
        adm_cats = {c.lower() for c in cat_val}
    elif isinstance(cat_val, str):
        adm_cats.add(cat_val.lower())

    user_cat = profile.category.lower() if (profile and profile.category) else None
    if adm_cats and user_cat:
        if user_cat in adm_cats:
            passed.append(True)
            reasons.append(f"Your category ({profile.category}) is eligible")
        else:
            failed.append(True)
            reasons.append(
                f"Your category ({profile.category}) is not in the eligible list"
            )

    status = _resolve_status(passed, failed)
    return {"status": status, "reasons": reasons}
