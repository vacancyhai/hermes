"""Eligibility checking engine — determines if a user is eligible for a job or admission.

check_job_eligibility(job, profile)       -> {"status": ..., "reasons": [...]}
check_admission_eligibility(adm, profile) -> {"status": ..., "reasons": [...]}

Status values:
  "eligible"           — all available criteria pass
  "partially_eligible" — at least one criterion passes, at least one fails
  "not_eligible"       — every checked criterion fails
  "unknown"            — profile has no data to evaluate against (prompt user to complete profile)

Job criteria  (eligibility JSONB keys: age_min, age_max, age_relaxation, qualification):
  1. Education     — profile.highest_qualification vs job.qualification_level (structured level)
  2. Age           — profile.date_of_birth vs eligibility.age_min / age_max
                     + relaxation from eligibility.age_relaxation
                     (DB keys: OBC, SC_ST, PwBD, PwD_UR, Ex_Serviceman)
  3. Category      — profile.category vs vacancy_breakdown.total_vacancy keys (SC/ST/OBC/EWS/UR)
  4. Domicile      — profile.state vs eligibility.domicile_required

Admission criteria  (eligibility JSONB keys: qualification, age_limit, min_percentage):
  1. Education     — admission_type proxy (ug→12th, pg→graduate) vs profile.highest_qualification
  2. Age           — profile.date_of_birth vs eligibility.age_limit.{min,max}  (0 = no limit)
                     NO age_relaxation dict on admissions — relaxation is in notes text only
  3. Min %         — profile.education.percentage vs eligibility.min_percentage (skip if 0)
  4. Domicile      — profile.state vs eligibility.domicile_required
"""

from datetime import date

# Education level hierarchy (higher index = higher qualification)
EDUCATION_LEVELS = ["10th", "12th", "diploma", "graduate", "postgraduate", "phd"]

# Map profile.category values → age_relaxation dict keys used in real DB data
_CATEGORY_TO_RELAX_KEY: dict[str, str] = {
    "obc": "OBC",
    "sc": "SC_ST",
    "st": "SC_ST",
    "ews": "EWS",
    "ebc": "OBC",
    "general": "UR",
}


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


def _age_relaxation(profile, eligibility: dict) -> int:
    """Return age relaxation years for this user from eligibility.age_relaxation.

    DB key format: {"OBC": 3, "SC_ST": 5, "PwBD": 10, "Ex_Serviceman": 3}
    Maps profile.category → the matching key, picks PwBD if is_pwd=True.
    Returns 0 if no age_relaxation dict on the job.
    """
    job_relax: dict = eligibility.get("age_relaxation") or {}
    if not job_relax:
        return 0
    relaxation = 0
    user_cat = profile.category.lower() if (profile and profile.category) else None
    if user_cat:
        relax_key = _CATEGORY_TO_RELAX_KEY.get(user_cat)
        if relax_key and relax_key in job_relax:
            relaxation = int(job_relax[relax_key])
    if getattr(profile, "is_pwd", False):
        pwd_extra = int(job_relax.get("PwBD", job_relax.get("PwD_UR", 0)))
        relaxation = max(relaxation, pwd_extra)
    if getattr(profile, "is_ex_serviceman", False):
        esm_extra = int(job_relax.get("Ex_Serviceman", 0))
        relaxation = max(relaxation, esm_extra)
    return relaxation


def _check_age(
    age_min,
    age_max,
    user_age: int | None,
    passed: list,
    failed: list,
    reasons: list,
    relaxation: int = 0,
) -> None:
    if user_age is None or (age_min is None and age_max is None):
        return
    effective_max = (int(age_max) + relaxation) if age_max is not None else None
    msg_parts = []
    if age_min is not None and user_age < int(age_min):
        msg_parts.append(f"minimum age is {age_min}")
    if effective_max is not None and user_age > effective_max:
        relax_note = f" (including {relaxation}yr relaxation)" if relaxation else ""
        msg_parts.append(f"maximum age is {effective_max}{relax_note}")
    if not msg_parts:
        relax_note = f" (with {relaxation}yr relaxation)" if relaxation else ""
        passed.append(True)
        reasons.append(f"Age {user_age} is within the eligible range{relax_note}")
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


def _check_domicile(
    eligibility: dict,
    profile,
    passed: list,
    failed: list,
    reasons: list,
    label: str = "vacancy",
) -> None:
    domicile_required = eligibility.get("domicile_required")
    if not domicile_required:
        return
    user_state = getattr(profile, "state", None)
    if not user_state:
        return
    if user_state.lower() == domicile_required.lower():
        passed.append(True)
        reasons.append(f"Your state ({user_state}) matches the required domicile")
    else:
        failed.append(True)
        reasons.append(
            f"This {label} requires domicile of {domicile_required} — yours: {user_state}"
        )


# Vacancy breakdown keys that represent reservation categories
_VACANCY_CAT_KEYS = {"sc", "st", "obc", "ews", "ebc", "ur", "general", "pwd"}


def _cats_from_eligibility(
    eligibility: dict, vacancy_breakdown: dict | None = None
) -> set[str]:
    """Build a set of lowercase category strings from eligibility + vacancy_breakdown.

    vacancy_breakdown real structure: {"total_vacancy": {"SC": n, "ST": n, "OBC": n, ...}, ...}
    Maps UR → general so it matches profile.category == "General".
    """
    cats: set[str] = set()
    cat_val = eligibility.get("category")
    if isinstance(cat_val, list):
        cats = {c.lower() for c in cat_val}
    elif isinstance(cat_val, str):
        cats.add(cat_val.lower())
    if isinstance(vacancy_breakdown, dict):
        total_vac = vacancy_breakdown.get("total_vacancy") or {}
        for k, v in total_vac.items():
            key = k.lower()
            if key in _VACANCY_CAT_KEYS and isinstance(v, int) and v > 0:
                cats.add("general" if key == "ur" else key)
    return cats


def _check_min_percentage(
    eligibility: dict,
    profile,
    passed: list,
    failed: list,
    reasons: list,
) -> None:
    """Check profile education percentage against eligibility.min_percentage (0 = skip)."""
    min_pct = eligibility.get("min_percentage") or 0
    if min_pct <= 0:
        return
    user_pct = None
    if isinstance(profile.education, dict):
        user_pct = profile.education.get("percentage")
    if user_pct is None:
        return
    if float(user_pct) >= float(min_pct):
        passed.append(True)
        reasons.append(f"Your percentage ({user_pct}%) meets the minimum ({min_pct}%)")
    else:
        failed.append(True)
        reasons.append(f"Minimum percentage required: {min_pct}% — yours: {user_pct}%")


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
        relaxation=_age_relaxation(profile, eligibility),
    )
    _check_category(
        _cats_from_eligibility(eligibility, job.vacancy_breakdown),
        profile.category,
        passed,
        failed,
        reasons,
    )
    _check_domicile(eligibility, profile, passed, failed, reasons, label="vacancy")

    return {"status": _resolve_status(passed, failed), "reasons": reasons}


def check_admission_eligibility(admission, profile) -> dict:
    """Check whether a user's profile meets the eligibility criteria for an admission.

    Returns {"status": str, "reasons": list[str]}

    Admission eligibility DB structure:
      eligibility.qualification    — free-text string (e.g. "B.E./B.Tech...")
      eligibility.age_limit.min/max — integers, 0 means no limit
      eligibility.min_percentage   — integer, 0 means no requirement
      admission.admission_type     — "ug" or "pg" used as education proxy
    """
    if not _profile_complete(profile):
        return _UNKNOWN_PROFILE

    reasons: list[str] = []
    passed: list[bool] = []
    failed: list[bool] = []

    eligibility = (
        admission.eligibility if isinstance(admission.eligibility, dict) else {}
    )

    # ── Education — use admission_type as structured proxy (qualification is free-text) ──
    type_map = {"ug": "12th", "pg": "graduate"}
    req_level = type_map.get((admission.admission_type or "").lower())
    _check_education(req_level, profile.highest_qualification, passed, failed, reasons)

    # ── Age — eligibility.age_limit.{min,max}, 0 means no limit ─────────────────────────
    age_limit = eligibility.get("age_limit") or {}
    age_min = age_limit.get("min") if isinstance(age_limit, dict) else None
    age_max = age_limit.get("max") if isinstance(age_limit, dict) else None
    if age_min == 0:
        age_min = None
    if age_max == 0:
        age_max = None
    # admissions have no structured age_relaxation dict — skip relaxation
    _check_age(
        age_min,
        age_max,
        _user_age(profile.date_of_birth),
        passed,
        failed,
        reasons,
    )

    # ── Min percentage — eligibility.min_percentage, 0 means no requirement ─────────────
    _check_min_percentage(eligibility, profile, passed, failed, reasons)

    # ── Domicile ─────────────────────────────────────────────────────────────────────────
    _check_domicile(eligibility, profile, passed, failed, reasons, label="admission")

    return {"status": _resolve_status(passed, failed), "reasons": reasons}
