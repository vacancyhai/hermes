"""Eligibility checking engine — determines if a user is eligible for a job or admission.

check_job_eligibility(job, profile)       -> {"status": ..., "reasons": [...]}
check_admission_eligibility(adm, profile) -> {"status": ..., "reasons": [...]}

Status values:
  "eligible"           — all available criteria pass
  "partially_eligible" — at least one criterion passes, at least one fails
  "not_eligible"       — every checked criterion fails
  "unknown"            — profile has no data to evaluate against (prompt user to complete profile)

Criteria checked (job):
  1. Education     — profile.highest_qualification vs job.qualification_level
  2. Age           — profile.date_of_birth vs eligibility.age_min/age_max
                     with category-based relaxation from eligibility.age_relaxation
  3. Category      — profile.category vs job.vacancy_breakdown keys + eligibility.category
  4. PWD           — profile.is_pwd vs eligibility.pwd_eligible
  5. Ex-serviceman — profile.is_ex_serviceman vs eligibility.ex_serviceman_eligible
  6. Domicile      — profile.state vs eligibility.domicile_required
"""

from datetime import date

# Education level hierarchy (higher index = higher qualification)
EDUCATION_LEVELS = ["10th", "12th", "diploma", "graduate", "postgraduate", "phd"]

# Default age relaxation (years) by category — standard govt job rules
_DEFAULT_AGE_RELAXATION: dict[str, int] = {
    "obc": 3,
    "sc": 5,
    "st": 5,
    "ews": 0,
    "ebc": 3,
    "pwd": 10,
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
    """Return age relaxation years for this user.

    Uses eligibility.age_relaxation dict for job-specific overrides,
    falls back to _DEFAULT_AGE_RELAXATION by category.
    PWD relaxation applies if profile.is_pwd is True.
    """
    relaxation = 0
    user_cat = profile.category.lower() if (profile and profile.category) else None
    job_relax: dict = eligibility.get("age_relaxation") or {}
    if user_cat:
        if isinstance(job_relax, dict) and user_cat in job_relax:
            relaxation = int(job_relax[user_cat])
        else:
            relaxation = _DEFAULT_AGE_RELAXATION.get(user_cat, 0)
    if profile and getattr(profile, "is_pwd", False):
        pwd_extra = (
            int(job_relax.get("pwd", _DEFAULT_AGE_RELAXATION["pwd"]))
            if isinstance(job_relax, dict)
            else _DEFAULT_AGE_RELAXATION["pwd"]
        )
        relaxation = max(relaxation, pwd_extra)
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


def _check_pwd(
    eligibility: dict,
    profile,
    passed: list,
    failed: list,
    reasons: list,
    label: str = "vacancy",
) -> None:
    pwd_eligible = eligibility.get("pwd_eligible")
    if pwd_eligible is None:
        return
    user_is_pwd = getattr(profile, "is_pwd", False)
    if pwd_eligible:
        if user_is_pwd:
            passed.append(True)
            reasons.append(f"PWD candidates are eligible for this {label}")
    else:
        if user_is_pwd:
            failed.append(True)
            reasons.append(f"This {label} does not have PWD reservation")


def _check_ex_serviceman(
    eligibility: dict,
    profile,
    passed: list,
    failed: list,
    reasons: list,
    label: str = "vacancy",
) -> None:
    esm_eligible = eligibility.get("ex_serviceman_eligible")
    if esm_eligible is None:
        return
    user_is_esm = getattr(profile, "is_ex_serviceman", False)
    if esm_eligible:
        if user_is_esm:
            passed.append(True)
            reasons.append(f"Ex-serviceman candidates are eligible for this {label}")
    else:
        if user_is_esm:
            failed.append(True)
            reasons.append(f"This {label} does not have ex-serviceman reservation")


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
        relaxation=_age_relaxation(profile, eligibility),
    )
    _check_category(
        _cats_from_eligibility(eligibility, job.vacancy_breakdown),
        profile.category,
        passed,
        failed,
        reasons,
    )
    _check_pwd(eligibility, profile, passed, failed, reasons, label="vacancy")
    _check_ex_serviceman(eligibility, profile, passed, failed, reasons, label="vacancy")
    _check_domicile(eligibility, profile, passed, failed, reasons, label="vacancy")

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
        relaxation=_age_relaxation(profile, eligibility),
    )
    _check_category(
        _cats_from_eligibility(eligibility),
        profile.category,
        passed,
        failed,
        reasons,
    )
    _check_pwd(eligibility, profile, passed, failed, reasons, label="admission")
    _check_ex_serviceman(
        eligibility, profile, passed, failed, reasons, label="admission"
    )
    _check_domicile(eligibility, profile, passed, failed, reasons, label="admission")

    return {"status": _resolve_status(passed, failed), "reasons": reasons}
