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


def _check_education(
    req_level: str | None,
    user_level: str | None,
    passed: list,
    failed: list,
    reasons: list,
) -> None:
    req_rank = _education_rank(req_level)
    user_rank = _education_rank(user_level)
    if req_rank < 0 or user_rank < 0:
        return
    if user_rank >= req_rank:
        passed.append(True)
        reasons.append(
            f"Your qualification ({user_level}) meets the requirement ({req_level})"
        )
    else:
        failed.append(True)
        reasons.append(f"Required qualification: {req_level} — yours: {user_level}")


def _check_age(
    age_min,
    age_max,
    user_age: int | None,
    passed: list,
    failed: list,
    reasons: list,
) -> None:
    if user_age is None or (age_min is None and age_max is None):
        return
    msg_parts = []
    if age_min is not None and user_age < int(age_min):
        msg_parts.append(f"minimum age is {age_min}")
    if age_max is not None and user_age > int(age_max):
        msg_parts.append(f"maximum age is {age_max}")
    if not msg_parts:
        passed.append(True)
        reasons.append(f"Age {user_age} is within the eligible range")
    else:
        failed.append(True)
        reasons.append(f"Age {user_age} does not meet criteria: {', '.join(msg_parts)}")


def _check_category(
    allowed_cats: set[str],
    user_category: str | None,
    passed: list,
    failed: list,
    reasons: list,
) -> None:
    if not allowed_cats or not user_category:
        return
    user_cat = user_category.lower()
    if user_cat in allowed_cats:
        passed.append(True)
        reasons.append(f"Your category ({user_category}) is eligible")
    else:
        failed.append(True)
        reasons.append(f"Your category ({user_category}) is not in the eligible list")


def _cats_from_eligibility(eligibility: dict, extra: dict | None = None) -> set[str]:
    """Build a set of lowercase category strings from eligibility and optional extra dict."""
    cats: set[str] = set()
    cat_val = eligibility.get("category")
    if isinstance(cat_val, list):
        cats = {c.lower() for c in cat_val}
    elif isinstance(cat_val, str):
        cats.add(cat_val.lower())
    if isinstance(extra, dict):
        cats.update(k.lower() for k in extra)
    return cats


_UNKNOWN_PROFILE = {
    "status": "unknown",
    "reasons": ["Complete your profile to check eligibility"],
}


def check_job_eligibility(job, profile) -> dict:
    """Check whether a user's profile meets the eligibility criteria for a job.

    Returns {"status": str, "reasons": list[str]}
    """
    if not _profile_complete(profile):
        return _UNKNOWN_PROFILE

    reasons: list[str] = []
    passed: list[bool] = []
    failed: list[bool] = []

    eligibility = job.eligibility if isinstance(job.eligibility, dict) else {}

    _check_education(
        job.qualification_level,
        profile.highest_qualification,
        passed,
        failed,
        reasons,
    )
    _check_age(
        eligibility.get("age_min"),
        eligibility.get("age_max"),
        _user_age(profile.date_of_birth),
        passed,
        failed,
        reasons,
    )
    _check_category(
        _cats_from_eligibility(eligibility, job.vacancy_breakdown),
        profile.category,
        passed,
        failed,
        reasons,
    )

    return {"status": _resolve_status(passed, failed), "reasons": reasons}


def check_admission_eligibility(admission, profile) -> dict:
    """Check whether a user's profile meets the eligibility criteria for an admission.

    Returns {"status": str, "reasons": list[str]}
    """
    if not _profile_complete(profile):
        return _UNKNOWN_PROFILE

    reasons: list[str] = []
    passed: list[bool] = []
    failed: list[bool] = []

    eligibility = (
        admission.eligibility if isinstance(admission.eligibility, dict) else {}
    )

    # Resolve required qualification: explicit field or infer from admission_type
    qual_req = eligibility.get("qualification") or eligibility.get("min_qualification")
    if not qual_req and admission.admission_type:
        qual_req = {"ug": "12th", "pg": "graduate"}.get(
            admission.admission_type.lower()
        )

    _check_education(qual_req, profile.highest_qualification, passed, failed, reasons)
    _check_age(
        eligibility.get("age_min") or eligibility.get("min_age"),
        eligibility.get("age_max") or eligibility.get("max_age"),
        _user_age(profile.date_of_birth),
        passed,
        failed,
        reasons,
    )
    _check_category(
        _cats_from_eligibility(eligibility),
        profile.category,
        passed,
        failed,
        reasons,
    )

    return {"status": _resolve_status(passed, failed), "reasons": reasons}
