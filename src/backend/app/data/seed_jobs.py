"""Seed script — inserts realistic government job data for all 4 portal sections.

Sections seeded:
  - 10 latest_job entries (recruitment posts)
  - 9  admit_card entries (standalone admit card announcements)
  - 9  answer_key entries (standalone answer key announcements)
  - 9  result entries  (standalone result announcements)
  - Per-phase linked documents (job_admit_cards, job_answer_keys, job_results)

Usage (inside Docker):
    docker exec -w /app hermes_backend python -m app.data.seed_jobs

Re-runnable: existing slugs are skipped, phase docs deduplicated by title.
"""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import sync_engine
from app.models.admin_user import AdminUser
from app.models.entrance_exam import EntranceExam
from app.models.job_admit_card import JobAdmitCard
from app.models.job_answer_key import JobAnswerKey
from app.models.job_result import JobResult
from app.models.job_vacancy import JobVacancy

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slug_exists(session: Session, slug: str) -> bool:
    return session.execute(select(JobVacancy).where(JobVacancy.slug == slug)).scalar_one_or_none() is not None


def _get_job_id(session: Session, slug: str) -> uuid.UUID | None:
    row = session.execute(select(JobVacancy.id).where(JobVacancy.slug == slug)).scalar_one_or_none()
    return row


def _exam_slug_exists(session: Session, slug: str) -> bool:
    return session.execute(select(EntranceExam).where(EntranceExam.slug == slug)).scalar_one_or_none() is not None


def _get_exam_id(session: Session, slug: str) -> uuid.UUID | None:
    return session.execute(select(EntranceExam.id).where(EntranceExam.slug == slug)).scalar_one_or_none()


def _get_admin_id(session: Session) -> uuid.UUID | None:
    admin = session.execute(select(AdminUser).where(AdminUser.role == "admin").limit(1)).scalar_one_or_none()
    return admin.id if admin else None


# Old job_vacancies slugs to remove (restructured or duplicated)
SLUGS_TO_REPLACE = [
    "nta-neet-pg-2026-admit-card",  # Was incorrectly admit_card type
    "nta-neet-pg-2026",             # Was latest_job; now entrance_exam
    "nta-neet-pg-2026-hall-ticket", # Duplicates the admit card now linked via exam_id in job_admit_cards
]


# ---------------------------------------------------------------------------
# Job data
# ---------------------------------------------------------------------------

JOBS = [
    # ------------------------------------------------------------------
    # 1. SSC GD Constable 2025
    # ------------------------------------------------------------------
    {
        "job_title": "SSC GD Constable Recruitment 2025",
        "slug": "ssc-gd-constable-recruitment-2025",
        "organization": "Staff Selection Commission",
        "department": "SSC",
        "job_type": "latest_job",
        "employment_type": "permanent",
        "qualification_level": "10th",
        "total_vacancies": 25487,
        "vacancy_breakdown": {
            "by_category": {"UR": 10195, "OBC": 6872, "EWS": 2549, "SC": 3823, "ST": 2048, "PWD": 100},
            "by_post": [
                {"post_name": "Constable GD", "total": 20000, "qualification": "10th Pass", "age_limit": "18-23", "pay_scale": "₹21,700–₹69,100"},
                {"post_name": "Head Constable", "total": 5487, "qualification": "12th Pass", "age_limit": "21-27", "pay_scale": "₹25,500–₹81,100"},
            ],
            "by_state": [
                {"state": "Delhi", "vacancies": {"UR": 500, "OBC": 300, "SC": 150, "ST": 50}},
                {"state": "UP", "vacancies": {"UR": 2000, "OBC": 1200, "SC": 800, "ST": 400}},
                {"state": "Bihar", "vacancies": {"UR": 1500, "OBC": 900, "SC": 600, "ST": 300}},
            ],
        },
        "description": "<p>SSC has released <strong>25,487 vacancies</strong> for GD Constable posts in CAPF, NIA, SSF and Rifleman in Assam Rifles. This is one of the largest central government recruitment drives for 2025.</p>",
        "short_description": "SSC GD Constable 2025: Apply for 25,487 vacancies in CAPF, NIA, SSF & Assam Rifles. 10th pass eligible.",
        "eligibility": {
            "min_qualification": "10th",
            "qualification_details": "10th Pass from a recognized board",
            "age_limit": {
                "min": 18, "max": 23, "cutoff_date": "2026-01-01",
                "relaxation": {"OBC": 3, "SC": 5, "ST": 5, "PWD": 10, "Ex_Serviceman": 5},
            },
            "physical_standards": {
                "male": {
                    "general": {"height": 170, "chest": 80, "chest_expanded": 85},
                    "sc_st": {"height": 165, "chest": 78, "chest_expanded": 83},
                },
                "female": {"all": {"height": 157, "weight": 48}},
            },
            "medical_standards": {
                "vision": "6/6 in one eye, 6/9 in other",
                "color_blindness": "No color blindness",
                "other": "No flat foot, knock knee, squint eyes",
            },
        },
        "application_details": {
            "application_mode": "Online",
            "application_link": "https://ssc.nic.in/apply",
            "official_website": "https://ssc.nic.in",
            "notification_pdf": "https://ssc.nic.in/notification.pdf",
            "fee_payment_mode": "Online (Credit/Debit Card, Net Banking, UPI)",
            "important_links": [
                {"type": "apply_online", "text": "Apply Online", "url": "https://ssc.nic.in/apply"},
                {"type": "download_notification", "text": "Download Notification", "url": "https://ssc.nic.in/notification.pdf"},
                {"type": "syllabus", "text": "Download Syllabus", "url": "https://ssc.nic.in/syllabus.pdf"},
            ],
        },
        "documents": [
            {"name": "10th Certificate", "mandatory": True, "format": "PDF", "max_size_kb": 500},
            {"name": "Aadhar Card", "mandatory": True, "format": "PDF", "max_size_kb": 300},
            {"name": "Photo", "mandatory": True, "format": "JPG", "max_size_kb": 100},
            {"name": "Signature", "mandatory": True, "format": "JPG", "max_size_kb": 50},
            {"name": "Category Certificate", "mandatory": False, "format": "PDF", "max_size_kb": 300},
        ],
        "notification_date": date(2025, 12, 1),
        "application_start": date(2025, 12, 10),
        "application_end": date(2026, 1, 10),
        "exam_start": date(2026, 2, 15),
        "exam_end": date(2026, 3, 15),
        "result_date": date(2026, 4, 15),
        "exam_details": {
            "exam_pattern": [
                {"phase": "CBT", "subjects": [
                    {"name": "General Intelligence", "questions": 40, "marks": 40},
                    {"name": "General Awareness", "questions": 40, "marks": 40},
                    {"name": "Mathematics", "questions": 40, "marks": 40},
                    {"name": "English", "questions": 40, "marks": 40},
                ], "total_marks": 160, "duration_minutes": 120, "negative_marking": 0.25, "exam_mode": "Online"},
                {"phase": "PET", "tests": ["Race", "Long Jump", "High Jump"], "qualifying": True},
                {"phase": "PST", "qualifying": True},
            ],
            "exam_language": ["Hindi", "English"],
            "total_phases": 3,
        },
        "salary": {
            "pay_scale": "₹21,700–₹69,100", "pay_level": "Level-3", "grade_pay": "₹2,000",
            "allowances": ["DA", "HRA", "TA"], "other_benefits": "Medical, Pension, PF",
        },
        "salary_initial": 21700, "salary_max": 69100,
        "selection_process": [
            {"phase": 1, "name": "Computer Based Test (CBT)", "qualifying": False},
            {"phase": 2, "name": "Physical Efficiency Test (PET)", "qualifying": True},
            {"phase": 3, "name": "Physical Standard Test (PST)", "qualifying": True},
            {"phase": 4, "name": "Medical Examination", "qualifying": True},
            {"phase": 5, "name": "Document Verification", "qualifying": True},
        ],
        "fee_general": 100, "fee_obc": 100, "fee_sc_st": 0, "fee_ews": 100, "fee_female": 0,
        "status": "active", "is_featured": True, "is_urgent": False,
    },

    # ------------------------------------------------------------------
    # 2. UPSC Civil Services 2026
    # ------------------------------------------------------------------
    {
        "job_title": "UPSC Civil Services Examination 2026",
        "slug": "upsc-civil-services-examination-2026",
        "organization": "Union Public Service Commission",
        "department": "UPSC",
        "job_type": "latest_job",
        "employment_type": "permanent",
        "qualification_level": "graduate",
        "total_vacancies": 1105,
        "vacancy_breakdown": {
            "by_category": {"UR": 442, "OBC": 298, "EWS": 110, "SC": 166, "ST": 89},
            "by_post": [
                {"post_name": "IAS", "total": 180, "pay_scale": "₹56,100–₹2,50,000"},
                {"post_name": "IPS", "total": 200, "pay_scale": "₹56,100–₹2,25,000"},
                {"post_name": "IFS (Foreign)", "total": 34, "pay_scale": "₹56,100–₹1,87,500"},
                {"post_name": "Other Central Services (Group A & B)", "total": 691, "pay_scale": "₹56,100–₹1,77,500"},
            ],
        },
        "description": "<p>UPSC Civil Services Examination 2026 invites applications from graduates of any discipline. This is the most prestigious examination in India encompassing IAS, IPS, IFS and Central Services Group A & B.</p>",
        "short_description": "UPSC CSE 2026: Apply for 1105 IAS/IPS/IFS and allied service posts. Any graduate eligible.",
        "eligibility": {
            "min_qualification": "graduate",
            "qualification_details": "Bachelor's Degree from any recognised University",
            "age_limit": {
                "min": 21, "max": 32, "cutoff_date": "2026-08-01",
                "relaxation": {"OBC": 3, "SC": 5, "ST": 5, "PwBD": 10, "Ex_Serviceman": 5},
            },
            "attempts": {"general": 6, "OBC": 9, "SC_ST": "unlimited (till age limit)", "PwBD": 9},
        },
        "application_details": {
            "application_mode": "Online",
            "application_link": "https://upsconline.nic.in",
            "official_website": "https://upsc.gov.in",
            "notification_pdf": "https://upsc.gov.in/sites/default/files/notif-CSP-2026.pdf",
            "fee_payment_mode": "SBI Challan / Online",
            "important_links": [
                {"type": "apply_online", "text": "Apply Online", "url": "https://upsconline.nic.in"},
                {"type": "download_notification", "text": "Official Notification", "url": "https://upsc.gov.in/notification"},
                {"type": "syllabus", "text": "Syllabus", "url": "https://upsc.gov.in/syllabus"},
            ],
        },
        "documents": [
            {"name": "Degree Certificate", "mandatory": True, "format": "PDF", "max_size_kb": 500},
            {"name": "Photo", "mandatory": True, "format": "JPG", "max_size_kb": 300},
            {"name": "Signature", "mandatory": True, "format": "JPG", "max_size_kb": 100},
            {"name": "Category Certificate", "mandatory": False, "format": "PDF", "max_size_kb": 500},
        ],
        "notification_date": date(2026, 2, 12),
        "application_start": date(2026, 2, 12),
        "application_end": date(2026, 3, 4),
        "exam_start": date(2026, 5, 25),
        "result_date": date(2027, 4, 1),
        "exam_details": {
            "exam_pattern": [
                {"phase": "Prelims", "subjects": [
                    {"name": "General Studies Paper I", "questions": 100, "marks": 200},
                    {"name": "CSAT (Paper II)", "questions": 80, "marks": 200, "qualifying": True},
                ], "duration_minutes": 120, "negative_marking": 0.33},
                {"phase": "Mains", "papers": 9, "total_marks": 1750, "exam_mode": "Offline"},
                {"phase": "Personality Test / Interview", "marks": 275},
            ],
            "exam_language": ["Hindi", "English"],
            "total_phases": 3,
        },
        "salary": {
            "pay_level": "Level-10 to Level-13",
            "pay_scale": "₹56,100–₹2,50,000",
            "allowances": ["DA", "HRA", "TA", "Medical"],
            "other_benefits": "Government Accommodation, Pension, LTC",
        },
        "salary_initial": 56100, "salary_max": 250000,
        "selection_process": [
            {"phase": 1, "name": "Preliminary Examination (Objective)", "qualifying": True},
            {"phase": 2, "name": "Main Examination (Written)", "qualifying": False},
            {"phase": 3, "name": "Personality Test / Interview", "qualifying": False},
        ],
        "fee_general": 100, "fee_obc": 100, "fee_sc_st": 0, "fee_ews": 100, "fee_female": 0,
        "status": "active", "is_featured": True, "is_urgent": False,
    },

    # ------------------------------------------------------------------
    # 3. Railway RRB NTPC 2025
    # ------------------------------------------------------------------
    {
        "job_title": "RRB NTPC Graduate Level Recruitment 2025",
        "slug": "rrb-ntpc-graduate-level-recruitment-2025",
        "organization": "Railway Recruitment Board",
        "department": "Ministry of Railways",
        "job_type": "latest_job",
        "employment_type": "permanent",
        "qualification_level": "graduate",
        "total_vacancies": 11558,
        "vacancy_breakdown": {
            "by_category": {"UR": 4624, "OBC": 3120, "EWS": 1156, "SC": 1734, "ST": 924},
            "by_post": [
                {"post_name": "Junior Clerk cum Typist", "total": 990, "pay_level": "Level-2"},
                {"post_name": "Accounts Clerk cum Typist", "total": 361, "pay_level": "Level-2"},
                {"post_name": "Junior Time Keeper", "total": 17, "pay_level": "Level-2"},
                {"post_name": "Trains Clerk", "total": 544, "pay_level": "Level-2"},
                {"post_name": "Commercial cum Ticket Clerk", "total": 2022, "pay_level": "Level-3"},
                {"post_name": "Traffic Assistant", "total": 88, "pay_level": "Level-4"},
                {"post_name": "Goods Guard", "total": 3144, "pay_level": "Level-5"},
                {"post_name": "Senior Commercial cum Ticket Clerk", "total": 1736, "pay_level": "Level-5"},
                {"post_name": "Senior Clerk cum Typist", "total": 742, "pay_level": "Level-5"},
                {"post_name": "Junior Account Assistant cum Typist", "total": 1507, "pay_level": "Level-5"},
                {"post_name": "Senior Time Keeper", "total": 24, "pay_level": "Level-5"},
                {"post_name": "Station Master", "total": 994, "pay_level": "Level-6"},
                {"post_name": "Goods Guard", "total": 0, "pay_level": "Level-6"},
            ],
        },
        "description": "<p>Railway Recruitment Board invites online applications from eligible candidates for <strong>11,558 Non-Technical Popular Categories (NTPC) Graduate Level posts</strong> across Indian Railways zones. Candidates must hold a Graduate degree from a recognized university.</p>",
        "short_description": "RRB NTPC 2025: 11,558 vacancies for Graduate Level posts including Station Master, Goods Guard & more.",
        "eligibility": {
            "min_qualification": "graduate",
            "qualification_details": "Bachelor's Degree in any discipline from recognised University/Institute",
            "age_limit": {
                "min": 18, "max": 33, "cutoff_date": "2026-01-01",
                "relaxation": {"OBC": 3, "SC": 5, "ST": 5, "PwBD": 10},
            },
        },
        "application_details": {
            "application_mode": "Online",
            "application_link": "https://rrbonlinereg.co.in",
            "official_website": "https://indianrailways.gov.in",
            "notification_pdf": "https://rrbapply.gov.in/notification.pdf",
            "fee_payment_mode": "Online / SBI Challan",
            "important_links": [
                {"type": "apply_online", "text": "Apply Online", "url": "https://rrbonlinereg.co.in"},
                {"type": "download_notification", "text": "Official Notification", "url": "https://rrbapply.gov.in/notification.pdf"},
            ],
        },
        "documents": [
            {"name": "Degree Certificate", "mandatory": True, "format": "PDF", "max_size_kb": 500},
            {"name": "10th / Matriculation Certificate", "mandatory": True, "format": "PDF", "max_size_kb": 500},
            {"name": "Photo", "mandatory": True, "format": "JPG", "max_size_kb": 50},
            {"name": "Signature", "mandatory": True, "format": "JPG", "max_size_kb": 20},
            {"name": "Category Certificate", "mandatory": False, "format": "PDF", "max_size_kb": 300},
        ],
        "notification_date": date(2025, 9, 14),
        "application_start": date(2025, 9, 14),
        "application_end": date(2025, 10, 13),
        "exam_start": date(2026, 3, 1),
        "result_date": date(2026, 9, 1),
        "exam_details": {
            "exam_pattern": [
                {"phase": "CBT-1", "subjects": [
                    {"name": "Mathematics", "questions": 30, "marks": 30},
                    {"name": "General Intelligence & Reasoning", "questions": 30, "marks": 30},
                    {"name": "General Awareness", "questions": 40, "marks": 40},
                ], "total_marks": 100, "duration_minutes": 90, "negative_marking": 0.33, "qualifying": True},
                {"phase": "CBT-2", "subjects": [
                    {"name": "Mathematics", "questions": 35, "marks": 35},
                    {"name": "General Intelligence & Reasoning", "questions": 35, "marks": 35},
                    {"name": "General Awareness", "questions": 50, "marks": 50},
                ], "total_marks": 120, "duration_minutes": 90, "negative_marking": 0.33},
                {"phase": "Skill Test / Typing Test", "qualifying": True, "applicable_posts": ["Clerk", "Typist"]},
            ],
            "exam_language": ["Hindi", "English", "Regional Languages"],
            "total_phases": 3,
        },
        "salary": {
            "pay_scale": "₹19,900–₹63,200 (Level-2) to ₹35,400–₹1,12,400 (Level-6)",
            "allowances": ["DA", "HRA", "TA", "Night Duty Allowance"],
            "other_benefits": "Railway Pass, Medical, Pension, PF",
        },
        "salary_initial": 19900, "salary_max": 112400,
        "selection_process": [
            {"phase": 1, "name": "Computer Based Test – Stage 1 (CBT-1)", "qualifying": True},
            {"phase": 2, "name": "Computer Based Test – Stage 2 (CBT-2)", "qualifying": False},
            {"phase": 3, "name": "Skill Test / Typing Test", "qualifying": True},
            {"phase": 4, "name": "Document Verification & Medical", "qualifying": True},
        ],
        "fee_general": 500, "fee_obc": 500, "fee_sc_st": 250, "fee_ews": 500, "fee_female": 250,
        "status": "active", "is_featured": True, "is_urgent": False,
    },

    # ------------------------------------------------------------------
    # 4. IBPS PO 2025
    # ------------------------------------------------------------------
    {
        "job_title": "IBPS PO (Probationary Officer) Recruitment 2025",
        "slug": "ibps-po-recruitment-2025",
        "organization": "Institute of Banking Personnel Selection",
        "department": "IBPS",
        "job_type": "latest_job",
        "employment_type": "permanent",
        "qualification_level": "graduate",
        "total_vacancies": 4455,
        "vacancy_breakdown": {
            "by_category": {"UR": 1782, "OBC": 1202, "EWS": 446, "SC": 668, "ST": 357},
            "by_post": [
                {"post_name": "Probationary Officer / Management Trainee", "total": 4455, "pay_scale": "₹36,000–₹63,840"},
            ],
            "by_state": [
                {"state": "Maharashtra", "vacancies": 520},
                {"state": "Uttar Pradesh", "vacancies": 610},
                {"state": "Gujarat", "vacancies": 380},
                {"state": "Tamil Nadu", "vacancies": 290},
            ],
        },
        "description": "<p>IBPS PO 2025 recruitment for <strong>Probationary Officer / Management Trainee</strong> posts across 11 participating public sector banks including Punjab National Bank, Bank of Baroda, Canara Bank and others.</p>",
        "short_description": "IBPS PO 2025: 4,455 Probationary Officer vacancies across 11 public sector banks. Graduates eligible.",
        "eligibility": {
            "min_qualification": "graduate",
            "qualification_details": "Graduation in any discipline from recognised University",
            "age_limit": {
                "min": 20, "max": 30, "cutoff_date": "2025-11-01",
                "relaxation": {"OBC": 3, "SC": 5, "ST": 5, "PwBD": 10, "Ex_Serviceman": 5},
            },
        },
        "application_details": {
            "application_mode": "Online",
            "application_link": "https://ibps.in/apply",
            "official_website": "https://ibps.in",
            "notification_pdf": "https://ibps.in/wp-content/uploads/2025/08/CRP-PO-MT-XV-Notification.pdf",
            "fee_payment_mode": "Online (Debit/Credit Card, Net Banking, UPI)",
            "important_links": [
                {"type": "apply_online", "text": "Apply Online", "url": "https://ibps.in/apply"},
                {"type": "download_notification", "text": "Official Notification", "url": "https://ibps.in/notification"},
                {"type": "syllabus", "text": "Exam Pattern & Syllabus", "url": "https://ibps.in/syllabus"},
            ],
        },
        "documents": [
            {"name": "Degree Certificate", "mandatory": True, "format": "PDF", "max_size_kb": 500},
            {"name": "Photo", "mandatory": True, "format": "JPG", "max_size_kb": 50},
            {"name": "Signature", "mandatory": True, "format": "JPG", "max_size_kb": 20},
            {"name": "Left Thumb Impression", "mandatory": True, "format": "JPG", "max_size_kb": 20},
            {"name": "Hand-written Declaration", "mandatory": True, "format": "JPG", "max_size_kb": 50},
            {"name": "Category Certificate", "mandatory": False, "format": "PDF", "max_size_kb": 500},
        ],
        "notification_date": date(2025, 8, 5),
        "application_start": date(2025, 8, 5),
        "application_end": date(2025, 8, 26),
        "exam_start": date(2025, 10, 18),
        "result_date": date(2026, 2, 1),
        "exam_details": {
            "exam_pattern": [
                {"phase": "Prelims", "subjects": [
                    {"name": "English Language", "questions": 30, "marks": 30},
                    {"name": "Quantitative Aptitude", "questions": 35, "marks": 35},
                    {"name": "Reasoning Ability", "questions": 35, "marks": 35},
                ], "total_marks": 100, "duration_minutes": 60, "qualifying": True},
                {"phase": "Mains", "sections": [
                    {"name": "Reasoning & Computer Aptitude", "questions": 45, "marks": 60},
                    {"name": "English Language", "questions": 35, "marks": 40},
                    {"name": "Data Analysis & Interpretation", "questions": 35, "marks": 60},
                    {"name": "General Economy / Banking Awareness", "questions": 40, "marks": 40},
                    {"name": "English Language (Letter Writing & Essay)", "marks": 25},
                ], "total_marks": 225},
                {"phase": "Interview", "marks": 100},
            ],
            "exam_language": ["Hindi", "English"],
            "total_phases": 3,
        },
        "salary": {
            "pay_scale": "₹36,000–₹63,840",
            "allowances": ["DA", "HRA", "CCA", "Medical Aid", "LFC"],
            "other_benefits": "Pension, PF, Gratuity, Staff Loan at concessional rate",
        },
        "salary_initial": 36000, "salary_max": 63840,
        "selection_process": [
            {"phase": 1, "name": "Preliminary Examination (Online)", "qualifying": True},
            {"phase": 2, "name": "Main Examination (Online)", "qualifying": False},
            {"phase": 3, "name": "Interview", "qualifying": False},
            {"phase": 4, "name": "Document Verification", "qualifying": True},
        ],
        "fee_general": 850, "fee_obc": 850, "fee_sc_st": 175, "fee_ews": 850, "fee_female": 175,
        "status": "active", "is_featured": True, "is_urgent": False,
    },

    # ------------------------------------------------------------------
    # 5. SSC CGL 2025  (NEET PG moved to entrance_exams table)
    # Note: item 5 was NEET PG — now correctly in entrance_exams table
    # ------------------------------------------------------------------
    {
        "job_title": "SSC CGL (Combined Graduate Level) Examination 2025",
        "slug": "ssc-cgl-combined-graduate-level-2025",
        "organization": "Staff Selection Commission",
        "department": "SSC",
        "job_type": "latest_job",
        "employment_type": "permanent",
        "qualification_level": "graduate",
        "total_vacancies": 14582,
        "vacancy_breakdown": {
            "by_category": {"UR": 5833, "OBC": 3938, "EWS": 1458, "SC": 2187, "ST": 1166},
            "by_post": [
                {"post_name": "Assistant Audit Officer (AAO)", "total": 222, "pay_level": "Level-8"},
                {"post_name": "Income Tax Inspector", "total": 1508, "pay_level": "Level-7"},
                {"post_name": "Assistant Section Officer", "total": 633, "pay_level": "Level-7"},
                {"post_name": "Tax Assistant (CBDT)", "total": 5670, "pay_level": "Level-4"},
                {"post_name": "Tax Assistant (CBIC)", "total": 894, "pay_level": "Level-4"},
                {"post_name": "Sub-Inspector (CBI / NIA)", "total": 75, "pay_level": "Level-6"},
                {"post_name": "Statistical Investigator Gr. II", "total": 650, "pay_level": "Level-6"},
                {"post_name": "Other Posts", "total": 4930, "pay_level": "Level-3 to Level-8"},
            ],
        },
        "description": "<p>SSC CGL 2025 is a prestigious recruitment examination conducted for <strong>Group B and Group C posts</strong> in various Central Government Departments & Ministries. A total of <strong>14,582 vacancies</strong> have been released across multiple cadres including Income Tax Inspector, Tax Assistant and ASO.</p>",
        "short_description": "SSC CGL 2025: 14,582 Group B & C vacancies. Graduate candidates can apply for IT Inspector, Tax Assistant & more.",
        "eligibility": {
            "min_qualification": "graduate",
            "qualification_details": "Bachelor's degree from a recognised University",
            "age_limit": {
                "min": 18, "max": 32, "cutoff_date": "2026-01-01",
                "relaxation": {"OBC": 3, "SC": 5, "ST": 5, "PwBD": 10, "Ex_Serviceman": 3},
                "note": "Age limit varies by post (18–27 for some, 20–30 for others)",
            },
        },
        "application_details": {
            "application_mode": "Online",
            "application_link": "https://ssc.nic.in/portal/apply",
            "official_website": "https://ssc.nic.in",
            "notification_pdf": "https://ssc.nic.in/cgl2025-notification.pdf",
            "fee_payment_mode": "Online (SBI Net Banking, BHIM UPI, Debit/Credit Card)",
            "important_links": [
                {"type": "apply_online", "text": "Apply Online", "url": "https://ssc.nic.in/portal/apply"},
                {"type": "download_notification", "text": "Official Notification PDF", "url": "https://ssc.nic.in/cgl2025.pdf"},
                {"type": "previous_papers", "text": "Previous Year Papers", "url": "https://ssc.nic.in/papers"},
            ],
        },
        "documents": [
            {"name": "Graduation Degree", "mandatory": True, "format": "PDF", "max_size_kb": 500},
            {"name": "10th Certificate (DOB Proof)", "mandatory": True, "format": "PDF", "max_size_kb": 500},
            {"name": "Photo", "mandatory": True, "format": "JPG", "max_size_kb": 50},
            {"name": "Signature", "mandatory": True, "format": "JPG", "max_size_kb": 20},
            {"name": "Category / EWS Certificate", "mandatory": False, "format": "PDF", "max_size_kb": 300},
        ],
        "notification_date": date(2025, 10, 15),
        "application_start": date(2025, 10, 15),
        "application_end": date(2025, 11, 15),
        "exam_start": date(2026, 1, 5),
        "exam_end": date(2026, 2, 15),
        "result_date": date(2026, 6, 1),
        "exam_details": {
            "exam_pattern": [
                {"phase": "Tier-I", "subjects": [
                    {"name": "General Intelligence & Reasoning", "questions": 25, "marks": 50},
                    {"name": "General Awareness", "questions": 25, "marks": 50},
                    {"name": "Quantitative Aptitude", "questions": 25, "marks": 50},
                    {"name": "English Comprehension", "questions": 25, "marks": 50},
                ], "total_marks": 200, "duration_minutes": 60, "negative_marking": 0.5, "exam_mode": "Online CBT"},
                {"phase": "Tier-II", "papers": [
                    {"name": "Paper I (Compulsory)", "sections": ["Mathematical Abilities", "Reasoning & General Intelligence", "English Language & Comprehension", "General Awareness", "Computer Knowledge"], "total_marks": 390},
                    {"name": "Paper II (for JSO posts)", "subjects": ["Statistics"], "total_marks": 200},
                    {"name": "Paper III (for AAO posts)", "subjects": ["General Studies Finance & Economics"], "total_marks": 200},
                ], "exam_mode": "Online CBT"},
            ],
            "exam_language": ["Hindi", "English"],
            "total_phases": 2,
        },
        "salary": {
            "pay_scale": "₹25,500–₹81,100 (Level-4) to ₹47,600–₹1,51,100 (Level-8)",
            "allowances": ["DA", "HRA", "TA"],
            "other_benefits": "Medical, Pension, CGHS",
        },
        "salary_initial": 25500, "salary_max": 151100,
        "selection_process": [
            {"phase": 1, "name": "Tier-I (Online CBT)", "qualifying": True},
            {"phase": 2, "name": "Tier-II (Online CBT)", "qualifying": False},
            {"phase": 3, "name": "Document Verification & Medical", "qualifying": True},
        ],
        "fee_general": 100, "fee_obc": 100, "fee_sc_st": 0, "fee_ews": 100, "fee_female": 0,
        "status": "active", "is_featured": True, "is_urgent": False,
    },

    # ------------------------------------------------------------------
    # 7. Army Technical Entry Scheme 2026
    # ------------------------------------------------------------------
    {
        "job_title": "Indian Army Technical Entry Scheme (TES) 2026",
        "slug": "indian-army-tes-technical-entry-scheme-2026",
        "organization": "Indian Army",
        "department": "Ministry of Defence",
        "job_type": "latest_job",
        "employment_type": "permanent",
        "qualification_level": "10+2",
        "total_vacancies": 90,
        "vacancy_breakdown": {
            "by_category": {"UR": 90},
            "by_post": [{"post_name": "Technical Entry Scheme (Officer) – Engineering", "total": 90}],
            "note": "No reservation for TES (Open Merit)",
        },
        "description": "<p>Indian Army invites applications from <strong>unmarried male candidates</strong> who have passed 10+2 with Physics, Chemistry & Mathematics (PCM) for the Technical Entry Scheme (TES) 2026. Selected candidates will undergo 5-year B.Tech from MCEME/CME/MCTE followed by commissioning as Permanent Commission Officers.</p>",
        "short_description": "Indian Army TES 2026: 90 Officer vacancies for 10+2 (PCM) candidates. Lifetime career as Commissioned Officer.",
        "eligibility": {
            "min_qualification": "10+2",
            "qualification_details": "10+2 with Physics, Chemistry & Mathematics – minimum 70% aggregate",
            "age_limit": {
                "min": 16.5, "max": 19.5, "cutoff_date": "2026-07-01",
                "note": "Born between 02 Jan 2007 to 01 Jul 2010",
            },
            "gender": "Male only",
            "marital_status": "Unmarried",
            "jee_required": True,
            "jee_note": "Must have qualified JEE (Mains) 2026",
        },
        "application_details": {
            "application_mode": "Online",
            "application_link": "https://joinindianarmy.nic.in",
            "official_website": "https://joinindianarmy.nic.in",
            "notification_pdf": "https://joinindianarmy.nic.in/tes-2026-notification.pdf",
            "fee_payment_mode": "No application fee",
            "important_links": [
                {"type": "apply_online", "text": "Apply Online", "url": "https://joinindianarmy.nic.in"},
                {"type": "download_notification", "text": "Official Notification", "url": "https://joinindianarmy.nic.in/notification"},
            ],
        },
        "documents": [
            {"name": "10+2 Marksheet", "mandatory": True, "format": "PDF"},
            {"name": "10th Certificate (DOB Proof)", "mandatory": True, "format": "PDF"},
            {"name": "JEE Mains Scorecard", "mandatory": True, "format": "PDF"},
            {"name": "Photo", "mandatory": True, "format": "JPG", "max_size_kb": 100},
            {"name": "Signature", "mandatory": True, "format": "JPG", "max_size_kb": 50},
        ],
        "notification_date": date(2026, 1, 15),
        "application_start": date(2026, 1, 15),
        "application_end": date(2026, 2, 15),
        "exam_start": date(2026, 6, 1),
        "result_date": date(2026, 9, 1),
        "exam_details": {
            "exam_pattern": [
                {"phase": "SSB Interview", "description": "5-day Service Selection Board interview at Allahabad/Bhopal/Bangalore/Capthalla", "marks": 900},
                {"phase": "Medical Examination", "qualifying": True},
            ],
            "shortlisting": "Shortlisting based on JEE Mains score and 10+2 PCM marks",
            "total_phases": 2,
        },
        "salary": {
            "training": "₹56,100/month during training (stipend)",
            "commissioned_rank": "Lieutenant → Captain → Major",
            "pay_scale": "₹56,100–₹2,00,000 (Lieutenant to Major)",
            "allowances": ["MSP ₹15,500", "DA", "HRA/Accommodation", "Transport Allowance"],
            "other_benefits": "Free ration, Medical for self & family, Group Insurance, Canteen, Leave Travel Concession",
        },
        "salary_initial": 56100, "salary_max": 200000,
        "selection_process": [
            {"phase": 1, "name": "JEE Mains Shortlisting", "qualifying": True},
            {"phase": 2, "name": "SSB Interview (5-day)", "qualifying": False},
            {"phase": 3, "name": "Medical Examination", "qualifying": True},
            {"phase": 4, "name": "Merit List & Allotment", "qualifying": False},
        ],
        "fee_general": 0, "fee_obc": 0, "fee_sc_st": 0, "fee_ews": 0, "fee_female": 0,
        "status": "active", "is_featured": False, "is_urgent": False,
    },

    # ------------------------------------------------------------------
    # 8. MPSC State Services 2025
    # ------------------------------------------------------------------
    {
        "job_title": "MPSC Rajyaseva (State Services) Examination 2025",
        "slug": "mpsc-rajyaseva-state-services-examination-2025",
        "organization": "Maharashtra Public Service Commission",
        "department": "MPSC",
        "job_type": "latest_job",
        "employment_type": "permanent",
        "qualification_level": "graduate",
        "total_vacancies": 444,
        "vacancy_breakdown": {
            "by_category": {"UR": 155, "OBC": 72, "SC": 62, "ST": 44, "NT": 55, "SBC": 22, "EWS": 34},
            "by_post": [
                {"post_name": "Deputy Collector", "total": 22, "pay_level": "Group A"},
                {"post_name": "Deputy Superintendent of Police", "total": 16, "pay_level": "Group A"},
                {"post_name": "Assistant Commissioner Sales Tax", "total": 26, "pay_level": "Group A"},
                {"post_name": "Tehsildar", "total": 68, "pay_level": "Group B"},
                {"post_name": "Block Development Officer", "total": 45, "pay_level": "Group B"},
                {"post_name": "Other Group A & B Posts", "total": 267, "pay_level": "Group A & B"},
            ],
        },
        "description": "<p>MPSC Rajyaseva 2025 invites applications from graduates for <strong>444 Group A & B posts</strong> in Maharashtra government. This prestigious state civil service exam leads to positions like Deputy Collector, DSP, Tehsildar, BDO and other gazetted officer posts.</p>",
        "short_description": "MPSC Rajyaseva 2025: 444 Group A & B vacancies including Deputy Collector, DSP & Tehsildar for Maharashtra state.",
        "eligibility": {
            "min_qualification": "graduate",
            "qualification_details": "Bachelor's Degree from a recognised University",
            "age_limit": {
                "min": 19, "max": 38, "cutoff_date": "2026-01-01",
                "relaxation": {"OBC/NT/SBC": 3, "SC/ST": 5, "Ex_Serviceman": 5, "PwBD": 10},
            },
            "domicile": "Maharashtra domicile preferred for some posts",
            "marathi_language": "Knowledge of Marathi essential",
        },
        "application_details": {
            "application_mode": "Online",
            "application_link": "https://mpsconline.gov.in",
            "official_website": "https://mpsc.gov.in",
            "notification_pdf": "https://mpsc.gov.in/rajyaseva-2025-notification.pdf",
            "fee_payment_mode": "Online (Net Banking, Debit Card, Credit Card)",
            "important_links": [
                {"type": "apply_online", "text": "Apply Online", "url": "https://mpsconline.gov.in"},
                {"type": "download_notification", "text": "Official Notification", "url": "https://mpsc.gov.in/notification"},
            ],
        },
        "documents": [
            {"name": "Graduation Certificate", "mandatory": True, "format": "PDF"},
            {"name": "Maharashtra Domicile Certificate", "mandatory": True, "format": "PDF"},
            {"name": "Photo", "mandatory": True, "format": "JPG", "max_size_kb": 100},
            {"name": "Signature", "mandatory": True, "format": "JPG", "max_size_kb": 50},
            {"name": "Caste Certificate", "mandatory": False, "format": "PDF"},
        ],
        "notification_date": date(2025, 12, 20),
        "application_start": date(2025, 12, 20),
        "application_end": date(2026, 1, 20),
        "exam_start": date(2026, 4, 5),
        "result_date": date(2027, 2, 1),
        "exam_details": {
            "exam_pattern": [
                {"phase": "Prelims", "papers": [
                    {"name": "General Studies", "questions": 100, "marks": 200},
                    {"name": "CSAT", "questions": 80, "marks": 200, "qualifying": True},
                ], "duration_minutes": 120, "negative_marking": 0.25},
                {"phase": "Mains", "papers": 6, "total_marks": 800, "exam_mode": "Offline"},
                {"phase": "Interview", "marks": 100},
            ],
            "exam_language": ["Marathi", "English"],
            "total_phases": 3,
        },
        "salary": {
            "pay_scale": "₹15,600–₹39,100 (Grade Pay ₹5,400–₹6,600) for Group A",
            "allowances": ["DA", "HRA", "TA", "Medical Allowance"],
            "other_benefits": "Government Quarters, Medical, Pension, LTC",
        },
        "salary_initial": 56100, "salary_max": 177500,
        "selection_process": [
            {"phase": 1, "name": "Preliminary Examination", "qualifying": True},
            {"phase": 2, "name": "Main Examination (Written)", "qualifying": False},
            {"phase": 3, "name": "Interview / Personality Test", "qualifying": False},
            {"phase": 4, "name": "Document Verification & Medical", "qualifying": True},
        ],
        "fee_general": 524, "fee_obc": 324, "fee_sc_st": 324, "fee_ews": 524, "fee_female": 324,
        "status": "active", "is_featured": False, "is_urgent": False,
    },

    # ------------------------------------------------------------------
    # 9. DRDO Scientist 'B' 2025
    # ------------------------------------------------------------------
    {
        "job_title": "DRDO Scientist 'B' Recruitment through GATE 2025",
        "slug": "drdo-scientist-b-gate-2025",
        "organization": "Defence Research and Development Organisation",
        "department": "Ministry of Defence",
        "job_type": "latest_job",
        "employment_type": "permanent",
        "qualification_level": "graduate",
        "total_vacancies": 228,
        "vacancy_breakdown": {
            "by_category": {"UR": 92, "OBC": 61, "EWS": 23, "SC": 34, "ST": 18},
            "by_post": [
                {"post_name": "Scientist 'B' – Electronics Engineering", "total": 52, "pay_level": "Level-11"},
                {"post_name": "Scientist 'B' – Computer Science", "total": 48, "pay_level": "Level-11"},
                {"post_name": "Scientist 'B' – Mechanical Engineering", "total": 45, "pay_level": "Level-11"},
                {"post_name": "Scientist 'B' – Electrical Engineering", "total": 33, "pay_level": "Level-11"},
                {"post_name": "Scientist 'B' – Aeronautical Engineering", "total": 28, "pay_level": "Level-11"},
                {"post_name": "Scientist 'B' – Chemical Engineering", "total": 22, "pay_level": "Level-11"},
            ],
            "gate_disciplines": ["EC", "CS", "ME", "EE", "AE", "CH"],
        },
        "description": "<p>DRDO recruits <strong>228 Scientist 'B'</strong> posts through GATE 2025 score. Selected candidates will work on cutting-edge defence research and technology development at DRDO laboratories across India with an attractive pay package and career growth.</p>",
        "short_description": "DRDO Scientist B 2025: 228 vacancies via GATE score in Electronics, CS, Mechanical & other engineering disciplines.",
        "eligibility": {
            "min_qualification": "graduate",
            "qualification_details": "B.E./B.Tech in relevant engineering discipline from recognised University — minimum 60% marks (55% for SC/ST/PwBD)",
            "age_limit": {
                "min": 0, "max": 28, "cutoff_date": "2026-01-01",
                "relaxation": {"OBC": 3, "SC": 5, "ST": 5, "PwBD": 10, "Ex_Serviceman": 5},
            },
            "gate_requirement": "Valid GATE 2025 score in relevant paper",
        },
        "application_details": {
            "application_mode": "Online",
            "application_link": "https://rac.gov.in",
            "official_website": "https://drdo.gov.in",
            "notification_pdf": "https://rac.gov.in/drdo-scientist-b-2025.pdf",
            "fee_payment_mode": "Online",
            "important_links": [
                {"type": "apply_online", "text": "Apply Online (RAC Portal)", "url": "https://rac.gov.in"},
                {"type": "download_notification", "text": "Official Notification", "url": "https://rac.gov.in/notification"},
                {"type": "gate_portal", "text": "GATE 2025 Portal", "url": "https://gate2025.iitr.ac.in"},
            ],
        },
        "documents": [
            {"name": "B.E./B.Tech Degree Certificate", "mandatory": True, "format": "PDF"},
            {"name": "GATE 2025 Scorecard", "mandatory": True, "format": "PDF"},
            {"name": "Photo", "mandatory": True, "format": "JPG", "max_size_kb": 100},
            {"name": "Signature", "mandatory": True, "format": "JPG", "max_size_kb": 50},
            {"name": "Category Certificate", "mandatory": False, "format": "PDF"},
        ],
        "notification_date": date(2025, 11, 1),
        "application_start": date(2025, 11, 1),
        "application_end": date(2025, 11, 30),
        "exam_start": None,
        "result_date": date(2026, 5, 1),
        "exam_details": {
            "selection_basis": "GATE 2025 Score + Interview",
            "exam_pattern": [
                {"phase": "GATE Score Shortlisting", "qualifying": True, "note": "Based on GATE 2025 score in relevant discipline"},
                {"phase": "Interview", "marks": 100, "qualifying": False},
            ],
            "exam_language": ["English"],
            "total_phases": 2,
        },
        "salary": {
            "pay_level": "Level-11",
            "pay_scale": "₹67,700–₹2,08,700",
            "grade_pay": "₹6,600",
            "allowances": ["DA", "HRA", "TA", "Professional Update Allowance ₹5,000/year"],
            "other_benefits": "Medical, Pension, CGHS, Subsidised Canteen, Research Freedom",
        },
        "salary_initial": 67700, "salary_max": 208700,
        "selection_process": [
            {"phase": 1, "name": "GATE 2025 Score Shortlisting", "qualifying": True},
            {"phase": 2, "name": "Personal Interview", "qualifying": False},
            {"phase": 3, "name": "Medical Examination", "qualifying": True},
            {"phase": 4, "name": "Document Verification", "qualifying": True},
        ],
        "fee_general": 100, "fee_obc": 100, "fee_sc_st": 0, "fee_ews": 100, "fee_female": 0,
        "status": "active", "is_featured": False, "is_urgent": False,
    },

    # ------------------------------------------------------------------
    # 10. IBPS Clerk XV 2025
    # ------------------------------------------------------------------
    {
        "job_title": "IBPS Clerk (CRP Clerk XV) Recruitment 2025",
        "slug": "ibps-clerk-crp-xv-2025",
        "organization": "Institute of Banking Personnel Selection",
        "department": "IBPS",
        "job_type": "latest_job",
        "employment_type": "permanent",
        "qualification_level": "graduate",
        "total_vacancies": 6128,
        "vacancy_breakdown": {
            "by_category": {"UR": 2452, "OBC": 1655, "EWS": 613, "SC": 919, "ST": 489},
            "by_post": [{"post_name": "Clerical Cadre", "total": 6128, "pay_scale": "₹17,900–₹47,920"}],
        },
        "description": "<p>IBPS invites online applications for <strong>6,128 Clerical Cadre</strong> vacancies across 11 participating public sector banks. Selected candidates serve as Clerk / Single Window Operator at various bank branches across India.</p>",
        "short_description": "IBPS Clerk 2025: 6,128 vacancies in 11 public sector banks. Any graduate eligible. Prelims + Mains + LPT.",
        "eligibility": {
            "min_qualification": "graduate",
            "qualification_details": "Graduation in any discipline from a recognised University",
            "age_limit": {
                "min": 20, "max": 28, "cutoff_date": "2025-11-01",
                "relaxation": {"OBC": 3, "SC": 5, "ST": 5, "PwBD": 10, "Ex_Serviceman": 5},
            },
        },
        "application_details": {
            "application_mode": "Online",
            "application_link": "https://ibps.in/apply",
            "official_website": "https://ibps.in",
            "fee_payment_mode": "Online (Debit/Credit Card, Net Banking, UPI)",
        },
        "documents": [
            {"name": "Degree Certificate", "mandatory": True, "format": "PDF", "max_size_kb": 500},
            {"name": "Photo", "mandatory": True, "format": "JPG", "max_size_kb": 50},
            {"name": "Signature", "mandatory": True, "format": "JPG", "max_size_kb": 20},
        ],
        "notification_date": date(2025, 9, 12),
        "application_start": date(2025, 9, 12),
        "application_end": date(2025, 10, 2),
        "exam_start": date(2025, 11, 22),
        "result_date": date(2026, 4, 1),
        "exam_details": {
            "exam_pattern": [
                {"phase": "Prelims", "subjects": [
                    {"name": "English Language", "questions": 30, "marks": 30},
                    {"name": "Numerical Ability", "questions": 35, "marks": 35},
                    {"name": "Reasoning Ability", "questions": 35, "marks": 35},
                ], "total_marks": 100, "duration_minutes": 60, "qualifying": True},
                {"phase": "Mains", "subjects": [
                    {"name": "General/Financial Awareness", "questions": 50, "marks": 50},
                    {"name": "General English", "questions": 40, "marks": 40},
                    {"name": "Reasoning Ability & Computer Aptitude", "questions": 50, "marks": 60},
                    {"name": "Quantitative Aptitude", "questions": 50, "marks": 50},
                ], "total_marks": 200, "duration_minutes": 160},
            ],
            "exam_language": ["Hindi", "English"],
            "total_phases": 3,
        },
        "salary": {
            "pay_scale": "₹17,900–₹47,920",
            "allowances": ["DA", "HRA", "CCA", "Medical Aid"],
            "other_benefits": "Pension, PF, Staff Loan at concessional rate",
        },
        "salary_initial": 17900, "salary_max": 47920,
        "selection_process": [
            {"phase": 1, "name": "Preliminary Examination (Online)", "qualifying": True},
            {"phase": 2, "name": "Main Examination (Online)", "qualifying": False},
            {"phase": 3, "name": "Language Proficiency Test (LPT)", "qualifying": True},
        ],
        "fee_general": 850, "fee_obc": 850, "fee_sc_st": 175, "fee_ews": 850, "fee_female": 175,
        "status": "active", "is_featured": False, "is_urgent": False,
    },
]


# ---------------------------------------------------------------------------
# Entrance Exams (9 entries) — goes into entrance_exams table, NOT job_vacancies
# Covers NEET PG/UG, JEE, CLAT, CAT, CUET, NEET SS, CET etc.
# ---------------------------------------------------------------------------

ADMISSIONS = [
    {
        "slug": "nta-neet-pg-2026",
        "exam_name": "NTA NEET PG 2026 — Medical PG Entrance Examination",
        "conducting_body": "National Testing Agency",
        "counselling_body": "Medical Counselling Committee (MCC)",
        "exam_type": "pg",
        "stream": "medical",
        "short_description": "NEET PG 2026: National entrance for MD/MS/PG Diploma admissions. MBBS with completed internship eligible. 300 MCQs, 3.5 hrs.",
        "description": "<p>NTA conducts <strong>NEET PG 2026</strong> for admission to MD/MS/PG Diploma courses at 6,000+ medical colleges across India. MBBS doctors who have completed 12-month rotating internship by 31 March 2026 are eligible to apply.</p>",
        "eligibility": {
            "min_qualification": "MBBS",
            "qualification_details": "MBBS with 12-month rotating internship completed on or before 31 March 2026 from NMC-recognised institution",
            "registration": "Valid permanent/provisional NMC/MCI registration mandatory",
            "attempts_limit": "No attempt limit for NEET PG",
        },
        "exam_details": {
            "exam_pattern": [
                {"phase": "NEET PG CBT", "subjects": [
                    {"name": "Pre-Clinical (Anatomy, Physiology, Biochemistry)", "questions": 50, "marks": 200},
                    {"name": "Para-Clinical (Pathology, Pharmacology, Microbiology)", "questions": 100, "marks": 400},
                    {"name": "Clinical (Medicine, Surgery, OBG, Paediatrics)", "questions": 150, "marks": 600},
                ], "total_questions": 300, "total_marks": 1200, "duration_minutes": 210, "negative_marking": 1.0, "exam_mode": "Online CBT"},
            ],
            "exam_language": ["English"],
        },
        "selection_process": [
            {"phase": 1, "name": "NEET PG Written Test (CBT)", "qualifying": False},
            {"phase": 2, "name": "MCC Merit-Based Counselling (AIQ + State)", "qualifying": True},
        ],
        "seats_info": {"total_pg_seats": 52000, "aiq_seats": 50, "note": "50% All India Quota + 50% State Quota"},
        "application_start": date(2025, 11, 1),
        "application_end": date(2025, 11, 30),
        "exam_date": date(2026, 3, 9),
        "result_date": date(2026, 4, 15),
        "counselling_start": date(2026, 5, 1),
        "fee_general": 4250, "fee_obc": 4250, "fee_sc_st": 2625, "fee_ews": 4250, "fee_female": 4250,
        "source_url": "https://nta.ac.in/neet-pg",
        "status": "active", "is_featured": True,
    },
    {
        "slug": "nta-neet-ug-2026",
        "exam_name": "NTA NEET UG 2026 — Medical UG Entrance Examination",
        "conducting_body": "National Testing Agency",
        "counselling_body": "Medical Counselling Committee (MCC)",
        "exam_type": "ug",
        "stream": "medical",
        "short_description": "NEET UG 2026: National entrance for MBBS/BDS/BAMS/BHMS admissions. 12th (PCB) eligible. 720 marks, 3.5 hrs.",
        "eligibility": {
            "min_qualification": "12th",
            "qualification_details": "10+2 with Physics, Chemistry, Biology/Biotechnology — minimum 50% aggregate (40% for SC/ST/OBC/PwBD)",
            "age_limit": {"min": 17, "note": "Must be 17 on or before 31 December 2026"},
            "attempts_limit": "No limit on attempts",
        },
        "exam_details": {
            "exam_pattern": [
                {"phase": "NEET UG", "subjects": [
                    {"name": "Physics", "questions": 50, "marks": 180},
                    {"name": "Chemistry", "questions": 50, "marks": 180},
                    {"name": "Biology (Botany + Zoology)", "questions": 100, "marks": 360},
                ], "total_questions": 200, "total_marks": 720, "duration_minutes": 200, "negative_marking": 1.0, "exam_mode": "OMR (Offline)"},
            ],
            "exam_language": ["English", "Hindi", "Assamese", "Bengali", "Gujarati", "Kannada", "Malayalam", "Marathi", "Odia", "Punjabi", "Tamil", "Telugu", "Urdu"],
        },
        "selection_process": [
            {"phase": 1, "name": "NEET UG Written Exam (OMR)", "qualifying": False},
            {"phase": 2, "name": "MCC / State Counselling & Seat Allotment", "qualifying": True},
        ],
        "seats_info": {"total_mbbs_seats": 108000, "bds_seats": 28000, "aiq_seats": 15, "note": "15% AIQ + 85% State Quota for govt colleges"},
        "application_start": date(2025, 12, 1),
        "application_end": date(2026, 1, 10),
        "exam_date": date(2026, 5, 4),
        "result_date": date(2026, 6, 14),
        "counselling_start": date(2026, 7, 1),
        "fee_general": 1700, "fee_obc": 1600, "fee_sc_st": 1000, "fee_ews": 1600, "fee_female": 1600,
        "source_url": "https://nta.ac.in/neet",
        "status": "active", "is_featured": True,
    },
    {
        "slug": "jee-mains-2026",
        "exam_name": "JEE Main 2026 — Joint Entrance Examination",
        "conducting_body": "National Testing Agency",
        "counselling_body": "Joint Seat Allocation Authority (JoSAA)",
        "exam_type": "ug",
        "stream": "engineering",
        "short_description": "JEE Main 2026: Session 1 & 2 for B.Tech/B.Arch admissions in NITs, IIITs & CFTIs. 12th (PCM) eligible.",
        "eligibility": {
            "min_qualification": "12th",
            "qualification_details": "10+2 with Physics, Chemistry, Mathematics from any recognised board",
            "age_limit": {"note": "No upper age limit for JEE Main 2026"},
            "attempts_limit": "3 consecutive years",
        },
        "exam_details": {
            "exam_pattern": [
                {"phase": "Paper 1 (B.Tech)", "subjects": [
                    {"name": "Physics", "questions": 30, "marks": 100},
                    {"name": "Chemistry", "questions": 30, "marks": 100},
                    {"name": "Mathematics", "questions": 30, "marks": 100},
                ], "total_marks": 300, "duration_minutes": 180, "negative_marking": 1.0, "exam_mode": "CBT"},
            ],
            "sessions": "Session 1: Jan 2026; Session 2: Apr 2026",
        },
        "selection_process": [
            {"phase": 1, "name": "JEE Main (Qualifying for JEE Advanced)", "qualifying": True},
            {"phase": 2, "name": "JoSAA Counselling & Seat Allotment (NITs/IIITs/CFTIs)", "qualifying": True},
        ],
        "seats_info": {"nit_seats": 23000, "iiit_seats": 8000, "cfti_seats": 11000},
        "application_start": date(2025, 11, 1),
        "application_end": date(2025, 11, 30),
        "exam_date": date(2026, 1, 22),
        "result_date": date(2026, 2, 15),
        "counselling_start": date(2026, 7, 1),
        "fee_general": 1000, "fee_obc": 1000, "fee_sc_st": 500, "fee_ews": 1000, "fee_female": 800,
        "source_url": "https://jeemain.nta.ac.in",
        "status": "active", "is_featured": True,
    },
    {
        "slug": "jee-advanced-2026",
        "exam_name": "JEE Advanced 2026 — IIT Joint Entrance Examination",
        "conducting_body": "IIT Bombay (on behalf of IIT Council)",
        "counselling_body": "Joint Seat Allocation Authority (JoSAA)",
        "exam_type": "ug",
        "stream": "engineering",
        "short_description": "JEE Advanced 2026: Gateway to B.Tech at 23 IITs. Top 2.5 lakh JEE Main qualifiers eligible. 2 papers, 6 hrs.",
        "eligibility": {
            "min_qualification": "12th",
            "qualification_details": "Must qualify JEE Main 2026 (top 2.5 lakh rank). 12th with PCM, 75% aggregate (65% for SC/ST/PwD)",
            "attempts_limit": "Maximum 2 attempts in consecutive years",
        },
        "exam_details": {
            "exam_pattern": [
                {"phase": "Paper 1", "subjects": ["Physics", "Chemistry", "Mathematics"], "duration_minutes": 180, "marks": 186, "exam_mode": "CBT"},
                {"phase": "Paper 2", "subjects": ["Physics", "Chemistry", "Mathematics"], "duration_minutes": 180, "marks": 186, "exam_mode": "CBT"},
            ],
        },
        "selection_process": [
            {"phase": 1, "name": "Paper 1 & Paper 2 (same day)", "qualifying": False},
            {"phase": 2, "name": "JoSAA IIT Seat Allotment", "qualifying": True},
        ],
        "seats_info": {"iit_seats": 17385, "note": "23 IITs across India"},
        "exam_date": date(2026, 5, 25),
        "result_date": date(2026, 6, 9),
        "counselling_start": date(2026, 7, 1),
        "fee_general": 3200, "fee_obc": 3200, "fee_sc_st": 1600, "fee_ews": 3200, "fee_female": 1600,
        "source_url": "https://jeeadv.ac.in",
        "status": "active", "is_featured": True,
    },
    {
        "slug": "clat-2026",
        "exam_name": "CLAT 2026 — Common Law Admission Test",
        "conducting_body": "Consortium of NLUs",
        "counselling_body": "Consortium of NLUs",
        "exam_type": "ug",
        "stream": "law",
        "short_description": "CLAT 2026: Entrance for LLB (5-yr) at 24 NLUs. 12th pass eligible. 120 MCQs, 2 hrs. Score valid for all NLUs.",
        "eligibility": {
            "min_qualification": "12th",
            "qualification_details": "10+2 or equivalent — 45% marks (40% for SC/ST). No age limit from 2023.",
            "attempts_limit": "No limit",
        },
        "exam_details": {
            "exam_pattern": [
                {"phase": "CLAT UG", "subjects": [
                    {"name": "English Language", "questions": 28},
                    {"name": "Current Affairs & GK", "questions": 35},
                    {"name": "Legal Reasoning", "questions": 35},
                    {"name": "Logical Reasoning", "questions": 28},
                    {"name": "Quantitative Techniques", "questions": 14},
                ], "total_questions": 120, "total_marks": 120, "duration_minutes": 120, "negative_marking": 0.25, "exam_mode": "Offline (OMR)"},
            ],
        },
        "selection_process": [
            {"phase": 1, "name": "CLAT Written Exam", "qualifying": False},
            {"phase": 2, "name": "NLU Centralised Counselling & Seat Allotment", "qualifying": True},
        ],
        "seats_info": {"total_nlu_seats": 3660, "nlu_count": 24},
        "application_start": date(2025, 11, 1),
        "application_end": date(2025, 12, 31),
        "exam_date": date(2026, 12, 1),
        "result_date": date(2026, 12, 10),
        "fee_general": 4000, "fee_sc_st": 3500, "fee_obc": 4000, "fee_ews": 4000, "fee_female": 4000,
        "source_url": "https://consortiumofnlus.ac.in",
        "status": "active", "is_featured": False,
    },
    {
        "slug": "cat-2025",
        "exam_name": "CAT 2025 — Common Admission Test (IIM)",
        "conducting_body": "IIM Calcutta (on behalf of IIM consortium)",
        "counselling_body": "Individual IIMs",
        "exam_type": "pg",
        "stream": "management",
        "short_description": "CAT 2025: Gateway to PGP/MBA at 20 IIMs and 1,200+ B-schools. Any graduate eligible. 3 slots, CBT mode.",
        "eligibility": {
            "min_qualification": "graduate",
            "qualification_details": "Bachelor's Degree with 50% (45% for SC/ST/PwD) from any recognised university",
            "attempts_limit": "No limit",
        },
        "exam_details": {
            "exam_pattern": [
                {"phase": "CAT", "sections": [
                    {"name": "Verbal Ability & Reading Comprehension (VARC)", "questions": 24},
                    {"name": "Data Interpretation & Logical Reasoning (DILR)", "questions": 20},
                    {"name": "Quantitative Ability (QA)", "questions": 22},
                ], "total_questions": 66, "total_marks": 198, "duration_minutes": 120, "negative_marking": 1.0, "exam_mode": "CBT"},
            ],
        },
        "selection_process": [
            {"phase": 1, "name": "CAT Written Exam (CBT)", "qualifying": False},
            {"phase": 2, "name": "WAT + PI at IIMs / B-schools", "qualifying": False},
            {"phase": 3, "name": "Final Merit List & Admission Offer", "qualifying": True},
        ],
        "seats_info": {"iim_seats_approx": 4500, "participating_bschools": 1200},
        "application_start": date(2025, 8, 1),
        "application_end": date(2025, 9, 13),
        "exam_date": date(2025, 11, 23),
        "result_date": date(2026, 1, 5),
        "counselling_start": date(2026, 2, 1),
        "fee_general": 2400, "fee_obc": 2400, "fee_sc_st": 1200, "fee_ews": 2400, "fee_female": 1200,
        "source_url": "https://iimcat.ac.in",
        "status": "active", "is_featured": False,
    },
    {
        "slug": "cuet-ug-2026",
        "exam_name": "CUET UG 2026 — Common University Entrance Test",
        "conducting_body": "National Testing Agency",
        "counselling_body": "Individual Central Universities",
        "exam_type": "ug",
        "stream": "general",
        "short_description": "CUET UG 2026: Central admission test for 280+ universities including DU, BHU, JNU, Hyderabad. 12th pass eligible.",
        "eligibility": {
            "min_qualification": "12th",
            "qualification_details": "10+2 from any recognised board. Minimum percentage varies by university and course.",
        },
        "exam_details": {
            "exam_pattern": [
                {"section": "Section 1A: Language", "note": "13 languages", "questions_per_language": 50, "duration_minutes": 45},
                {"section": "Section 2: Domain", "note": "27 domain subjects, max 6 allowed", "questions": 45, "duration_minutes": 45},
                {"section": "Section 3: General Test", "questions": 60, "duration_minutes": 60},
            ],
            "exam_mode": "CBT",
        },
        "selection_process": [
            {"phase": 1, "name": "CUET UG Exam (CBT)", "qualifying": False},
            {"phase": 2, "name": "University-wise Counselling / Merit List", "qualifying": True},
        ],
        "seats_info": {"participating_universities": 280, "note": "Includes all Central Universities; DU alone has 70,000+ seats"},
        "application_start": date(2026, 2, 1),
        "application_end": date(2026, 3, 1),
        "exam_date": date(2026, 5, 8),
        "result_date": date(2026, 6, 30),
        "fee_general": 750, "fee_obc": 700, "fee_sc_st": 650, "fee_ews": 700, "fee_female": 650,
        "source_url": "https://cuet.nta.nic.in",
        "status": "upcoming", "is_featured": False,
    },
    {
        "slug": "neet-ss-2025",
        "exam_name": "NEET SS 2025 — Super Speciality Medical Entrance",
        "conducting_body": "National Board of Examinations in Medical Sciences (NBEMS)",
        "counselling_body": "Medical Counselling Committee (MCC)",
        "exam_type": "doctoral",
        "stream": "medical",
        "short_description": "NEET SS 2025: Entrance for DM/M.Ch (Super Speciality) courses. MD/MS in relevant speciality eligible.",
        "eligibility": {
            "min_qualification": "MD/MS",
            "qualification_details": "MD/MS degree in the relevant broad speciality from NMC-recognised institution",
        },
        "exam_details": {
            "exam_pattern": [
                {"phase": "NEET SS", "questions": 100, "marks": 100, "duration_minutes": 90, "negative_marking": 0.25, "exam_mode": "CBT"},
            ],
        },
        "selection_process": [
            {"phase": 1, "name": "NEET SS Written Exam", "qualifying": False},
            {"phase": 2, "name": "MCC DM/M.Ch Counselling", "qualifying": True},
        ],
        "application_start": date(2025, 7, 1),
        "application_end": date(2025, 7, 31),
        "exam_date": date(2025, 9, 1),
        "result_date": date(2025, 10, 1),
        "fee_general": 4000, "fee_sc_st": 2500,
        "source_url": "https://natboard.edu.in",
        "status": "active", "is_featured": False,
    },
    {
        "slug": "gate-2026",
        "exam_name": "GATE 2026 — Graduate Aptitude Test in Engineering",
        "conducting_body": "IIT Roorkee (on behalf of GATE Committee)",
        "counselling_body": "Individual IITs / IISc / PSUs for recruitment",
        "exam_type": "pg",
        "stream": "engineering",
        "short_description": "GATE 2026: M.Tech/Ph.D admissions at IITs/IISc + PSU recruitment. B.E./B.Tech or equivalent eligible. Score valid 3 years.",
        "eligibility": {
            "min_qualification": "graduate",
            "qualification_details": "B.E./B.Tech/B.Sc.(Research)/B.S. or 3rd year students of these programmes",
            "score_validity": "3 years from declaration of result",
        },
        "exam_details": {
            "exam_pattern": [
                {"phase": "GATE", "questions": 65, "marks": 100, "duration_minutes": 180,
                 "note": "29 papers; candidates appear in 1-2 papers", "exam_mode": "CBT"},
            ],
        },
        "selection_process": [
            {"phase": 1, "name": "GATE Written Exam (CBT)", "qualifying": False},
            {"phase": 2, "name": "Institute/PSU Admission Process (CCMT / individual)", "qualifying": True},
        ],
        "seats_info": {"note": "Score used by 900+ PG programmes + PSU direct recruitment (DRDO, IOCL, NTPC, ONGC etc.)"},
        "application_start": date(2025, 9, 1),
        "application_end": date(2025, 9, 26),
        "exam_date": date(2026, 2, 1),
        "result_date": date(2026, 3, 19),
        "fee_general": 1800, "fee_obc": 1800, "fee_sc_st": 900, "fee_ews": 1800, "fee_female": 900,
        "source_url": "https://gate2026.iitr.ac.in",
        "status": "active", "is_featured": False,
    },
]

# Per-phase linked documents for entrance_exams
EXAM_PHASE_DOCS = {
    "nta-neet-pg-2026": {
        "admit_cards": [
            {
                "phase_number": 1, "title": "NEET PG 2026 Admit Card",
                "download_url": "https://nta.ac.in/neet-pg/admit-card",
                "valid_from": date(2026, 3, 1), "valid_until": date(2026, 3, 9),
                "notes": "Carry printout + valid government-issued photo ID to exam centre.",
                "published_at": datetime(2026, 3, 1, tzinfo=timezone.utc),
            },
        ],
        "answer_keys": [
            {
                "phase_number": 1, "title": "NEET PG 2026 Provisional Answer Key",
                "answer_key_type": "provisional",
                "files": [{"label": "Answer Key PDF", "url": "https://nta.ac.in/neet-pg/ak.pdf"}],
                "objection_url": "https://nta.ac.in/neet-pg/objection",
                "objection_deadline": date(2026, 3, 20),
                "published_at": datetime(2026, 3, 15, tzinfo=timezone.utc),
            },
        ],
        "results": [
            {
                "phase_number": 1, "title": "NEET PG 2026 Result & Score Card",
                "result_type": "merit_list",
                "download_url": "https://nta.ac.in/neet-pg/result",
                "cutoff_marks": {"UR_50th_percentile": 350, "OBC_SC_ST_40th_percentile": 315, "PwBD_45th_percentile": 315},
                "notes": "Score card valid for MCC counselling rounds.",
                "published_at": datetime(2026, 4, 15, tzinfo=timezone.utc),
            },
        ],
    },
    "jee-mains-2026": {
        "admit_cards": [
            {
                "phase_number": 1, "title": "JEE Main 2026 Session 1 Admit Card",
                "download_url": "https://jeemain.nta.ac.in/admit-card",
                "valid_from": date(2026, 1, 14), "valid_until": date(2026, 1, 22),
                "notes": "Download from jeemain.nta.ac.in using Application No. & DOB.",
                "published_at": datetime(2026, 1, 14, tzinfo=timezone.utc),
            },
            {
                "phase_number": 2, "title": "JEE Main 2026 Session 2 Admit Card",
                "download_url": "https://jeemain.nta.ac.in/admit-card-s2",
                "valid_from": date(2026, 4, 1), "valid_until": date(2026, 4, 9),
                "notes": "Session 2 admit card — download using Application No. & DOB.",
                "published_at": datetime(2026, 4, 1, tzinfo=timezone.utc),
            },
        ],
        "answer_keys": [
            {
                "phase_number": 1, "title": "JEE Main Session 1 2026 Provisional Answer Key",
                "answer_key_type": "provisional",
                "files": [
                    {"label": "Paper 1 (B.Tech)", "url": "https://jeemain.nta.ac.in/ak-s1-paper1.pdf"},
                    {"label": "Paper 2A (B.Arch)", "url": "https://jeemain.nta.ac.in/ak-s1-paper2a.pdf"},
                ],
                "objection_url": "https://jeemain.nta.ac.in/objection",
                "objection_deadline": date(2026, 2, 1),
                "published_at": datetime(2026, 1, 28, tzinfo=timezone.utc),
            },
            {
                "phase_number": 1, "title": "JEE Main Session 1 2026 Final Answer Key",
                "answer_key_type": "final",
                "files": [
                    {"label": "Paper 1 Final Key", "url": "https://jeemain.nta.ac.in/fak-s1-paper1.pdf"},
                ],
                "published_at": datetime(2026, 2, 12, tzinfo=timezone.utc),
            },
            {
                "phase_number": 2, "title": "JEE Main Session 2 2026 Provisional Answer Key",
                "answer_key_type": "provisional",
                "files": [
                    {"label": "Paper 1 (B.Tech)", "url": "https://jeemain.nta.ac.in/ak-s2-paper1.pdf"},
                ],
                "objection_url": "https://jeemain.nta.ac.in/objection-s2",
                "objection_deadline": date(2026, 4, 16),
                "published_at": datetime(2026, 4, 12, tzinfo=timezone.utc),
            },
        ],
        "results": [
            {
                "phase_number": 1, "title": "JEE Main Session 1 2026 Result (NTA Score)",
                "result_type": "merit_list",
                "download_url": "https://jeemain.nta.ac.in/result-s1",
                "cutoff_marks": {"JEE_Advanced_Qualifying_percentile": 93.5, "NIT_General_approx_percentile": 88},
                "notes": "NTA Score (percentile) used for NIT/IIIT/CFTI allotment via JoSAA. Top 2.5L qualify for JEE Advanced.",
                "published_at": datetime(2026, 2, 15, tzinfo=timezone.utc),
            },
            {
                "phase_number": 2, "title": "JEE Main Session 2 2026 Result & Final Merit List",
                "result_type": "merit_list",
                "download_url": "https://jeemain.nta.ac.in/result-s2",
                "cutoff_marks": {"JEE_Advanced_Qualifying_percentile": 94.0, "NIT_General_approx_percentile": 89},
                "notes": "Best of Session 1 & Session 2 NTA Score considered for final rank list.",
                "published_at": datetime(2026, 4, 25, tzinfo=timezone.utc),
            },
        ],
    },

    "nta-neet-ug-2026": {
        "admit_cards": [
            {
                "phase_number": 1, "title": "NEET UG 2026 Admit Card",
                "download_url": "https://neet.nta.nic.in/admit-card",
                "valid_from": date(2026, 4, 20), "valid_until": date(2026, 5, 4),
                "notes": "Carry colour printout + valid Govt. photo ID. Report to centre 90 min before exam.",
                "published_at": datetime(2026, 4, 20, tzinfo=timezone.utc),
            },
        ],
        "answer_keys": [
            {
                "phase_number": 1, "title": "NEET UG 2026 Provisional Answer Key",
                "answer_key_type": "provisional",
                "files": [
                    {"label": "Physics", "url": "https://neet.nta.nic.in/ak/physics.pdf"},
                    {"label": "Chemistry", "url": "https://neet.nta.nic.in/ak/chemistry.pdf"},
                    {"label": "Biology", "url": "https://neet.nta.nic.in/ak/biology.pdf"},
                ],
                "objection_url": "https://neet.nta.nic.in/objection",
                "objection_deadline": date(2026, 5, 22),
                "published_at": datetime(2026, 5, 17, tzinfo=timezone.utc),
            },
            {
                "phase_number": 1, "title": "NEET UG 2026 Final Answer Key",
                "answer_key_type": "final",
                "files": [
                    {"label": "Final Answer Key (All Sets)", "url": "https://neet.nta.nic.in/fak/neet-ug-2026.pdf"},
                ],
                "published_at": datetime(2026, 6, 10, tzinfo=timezone.utc),
            },
        ],
        "results": [
            {
                "phase_number": 1, "title": "NEET UG 2026 Result & Score Card",
                "result_type": "merit_list",
                "download_url": "https://neet.nta.nic.in/result",
                "cutoff_marks": {
                    "UR_50th_percentile_marks": 720, "UR_cut_off": 138,
                    "OBC_SC_ST_40th_percentile": 108, "PwBD_45th_percentile": 122,
                },
                "notes": "Score card required for MCC / State counselling registration. Valid until NEET UG 2027.",
                "published_at": datetime(2026, 6, 14, tzinfo=timezone.utc),
            },
        ],
    },

    "jee-advanced-2026": {
        "admit_cards": [
            {
                "phase_number": 1, "title": "JEE Advanced 2026 Admit Card",
                "download_url": "https://jeeadv.ac.in/admit-card",
                "valid_from": date(2026, 5, 17), "valid_until": date(2026, 5, 25),
                "notes": "Download from jeeadv.ac.in. Carry printout + any one original Govt. photo ID.",
                "published_at": datetime(2026, 5, 17, tzinfo=timezone.utc),
            },
        ],
        "answer_keys": [
            {
                "phase_number": 1, "title": "JEE Advanced 2026 Provisional Answer Key",
                "answer_key_type": "provisional",
                "files": [
                    {"label": "Paper 1 — Physics", "url": "https://jeeadv.ac.in/ak/p1-physics.pdf"},
                    {"label": "Paper 1 — Chemistry", "url": "https://jeeadv.ac.in/ak/p1-chemistry.pdf"},
                    {"label": "Paper 1 — Mathematics", "url": "https://jeeadv.ac.in/ak/p1-maths.pdf"},
                    {"label": "Paper 2 — Physics", "url": "https://jeeadv.ac.in/ak/p2-physics.pdf"},
                    {"label": "Paper 2 — Chemistry", "url": "https://jeeadv.ac.in/ak/p2-chemistry.pdf"},
                    {"label": "Paper 2 — Mathematics", "url": "https://jeeadv.ac.in/ak/p2-maths.pdf"},
                ],
                "objection_url": "https://jeeadv.ac.in/objection",
                "objection_deadline": date(2026, 6, 2),
                "published_at": datetime(2026, 5, 29, tzinfo=timezone.utc),
            },
            {
                "phase_number": 1, "title": "JEE Advanced 2026 Final Answer Key",
                "answer_key_type": "final",
                "files": [
                    {"label": "Final Keys — Paper 1 & Paper 2", "url": "https://jeeadv.ac.in/fak/jee-adv-2026.pdf"},
                ],
                "published_at": datetime(2026, 6, 7, tzinfo=timezone.utc),
            },
        ],
        "results": [
            {
                "phase_number": 1, "title": "JEE Advanced 2026 Result — All India Rank (AIR)",
                "result_type": "merit_list",
                "download_url": "https://jeeadv.ac.in/result",
                "cutoff_marks": {
                    "CRL_min_marks_each_subject": 10, "CRL_aggregate_min": 90,
                    "OBC_NCL_aggregate": 81, "SC_aggregate": 45, "ST_aggregate": 45,
                },
                "notes": "AIR used for JoSAA IIT seat allotment. Architecture Aptitude Test (AAT) for B.Arch at IITs.",
                "total_qualified": 17400,
                "published_at": datetime(2026, 6, 9, tzinfo=timezone.utc),
            },
        ],
    },

    "clat-2026": {
        "admit_cards": [
            {
                "phase_number": 1, "title": "CLAT 2026 Admit Card",
                "download_url": "https://consortiumofnlus.ac.in/admit-card",
                "valid_from": date(2026, 11, 22), "valid_until": date(2026, 12, 1),
                "notes": "Download from consortiumofnlus.ac.in. Carry printout + Govt. photo ID + passport photo.",
                "published_at": datetime(2026, 11, 22, tzinfo=timezone.utc),
            },
        ],
        "answer_keys": [
            {
                "phase_number": 1, "title": "CLAT 2026 Provisional Answer Key",
                "answer_key_type": "provisional",
                "files": [
                    {"label": "CLAT UG 2026 Answer Key", "url": "https://consortiumofnlus.ac.in/ak/clat-ug-2026.pdf"},
                    {"label": "CLAT PG 2026 Answer Key", "url": "https://consortiumofnlus.ac.in/ak/clat-pg-2026.pdf"},
                ],
                "objection_url": "https://consortiumofnlus.ac.in/objection",
                "objection_deadline": date(2026, 12, 5),
                "published_at": datetime(2026, 12, 2, tzinfo=timezone.utc),
            },
            {
                "phase_number": 1, "title": "CLAT 2026 Final Answer Key",
                "answer_key_type": "final",
                "files": [
                    {"label": "Final Answer Key", "url": "https://consortiumofnlus.ac.in/fak/clat-2026.pdf"},
                ],
                "published_at": datetime(2026, 12, 8, tzinfo=timezone.utc),
            },
        ],
        "results": [
            {
                "phase_number": 1, "title": "CLAT 2026 Result & Merit List",
                "result_type": "merit_list",
                "download_url": "https://consortiumofnlus.ac.in/result",
                "cutoff_marks": {
                    "NLSIU_Bangalore_General_approx": 98.5,
                    "NLU_Delhi_General_approx": 97.8,
                    "NALSAR_Hyderabad_approx": 96.5,
                },
                "notes": "Merit list used for centralised NLU counselling. Candidates should register separately for preferred NLUs.",
                "published_at": datetime(2026, 12, 10, tzinfo=timezone.utc),
            },
        ],
    },

    "cat-2025": {
        "admit_cards": [
            {
                "phase_number": 1, "title": "CAT 2025 Admit Card",
                "download_url": "https://iimcat.ac.in/admit-card",
                "valid_from": date(2025, 11, 5), "valid_until": date(2025, 11, 23),
                "notes": "Download from iimcat.ac.in. Carry printout + any original Govt. photo ID. Slot pre-assigned.",
                "published_at": datetime(2025, 11, 5, tzinfo=timezone.utc),
            },
        ],
        "answer_keys": [
            {
                "phase_number": 1, "title": "CAT 2025 Answer Key & Question Paper",
                "answer_key_type": "provisional",
                "files": [
                    {"label": "Slot 1 Question Paper + Key", "url": "https://iimcat.ac.in/ak/cat2025-slot1.pdf"},
                    {"label": "Slot 2 Question Paper + Key", "url": "https://iimcat.ac.in/ak/cat2025-slot2.pdf"},
                    {"label": "Slot 3 Question Paper + Key", "url": "https://iimcat.ac.in/ak/cat2025-slot3.pdf"},
                ],
                "objection_url": "https://iimcat.ac.in/objection",
                "objection_deadline": date(2025, 12, 5),
                "published_at": datetime(2025, 11, 27, tzinfo=timezone.utc),
            },
        ],
        "results": [
            {
                "phase_number": 1, "title": "CAT 2025 Score Card & Result",
                "result_type": "merit_list",
                "download_url": "https://iimcat.ac.in/result",
                "cutoff_marks": {
                    "IIM_Ahmedabad_General_percentile": 99.0,
                    "IIM_Bangalore_General_percentile": 98.5,
                    "IIM_Calcutta_General_percentile": 98.5,
                    "Top6_IIMs_General_approx": 98.0,
                    "New_IIMs_General_approx": 90.0,
                },
                "notes": "CAT score valid for IIM WAT-PI shortlisting. Score card required for all participating B-school applications.",
                "published_at": datetime(2026, 1, 5, tzinfo=timezone.utc),
            },
        ],
    },

    "cuet-ug-2026": {
        "admit_cards": [
            {
                "phase_number": 1, "title": "CUET UG 2026 Admit Card — City Intimation Slip",
                "download_url": "https://cuet.nta.nic.in/city-intimation",
                "valid_from": date(2026, 4, 28), "valid_until": date(2026, 5, 8),
                "notes": "City Intimation Slip released first (approx 10 days before exam). Actual admit card released 4 days before exam.",
                "published_at": datetime(2026, 4, 28, tzinfo=timezone.utc),
            },
            {
                "phase_number": 1, "title": "CUET UG 2026 Admit Card",
                "download_url": "https://cuet.nta.nic.in/admit-card",
                "valid_from": date(2026, 5, 4), "valid_until": date(2026, 5, 8),
                "notes": "Download from cuet.nta.nic.in using Application No. & DOB. Carry with valid photo ID.",
                "published_at": datetime(2026, 5, 4, tzinfo=timezone.utc),
            },
        ],
        "answer_keys": [
            {
                "phase_number": 1, "title": "CUET UG 2026 Provisional Answer Key",
                "answer_key_type": "provisional",
                "files": [
                    {"label": "Domain Subject Keys", "url": "https://cuet.nta.nic.in/ak/domain-subjects.pdf"},
                    {"label": "General Test Key", "url": "https://cuet.nta.nic.in/ak/general-test.pdf"},
                    {"label": "Language Section Keys", "url": "https://cuet.nta.nic.in/ak/languages.pdf"},
                ],
                "objection_url": "https://cuet.nta.nic.in/objection",
                "objection_deadline": date(2026, 5, 20),
                "published_at": datetime(2026, 5, 14, tzinfo=timezone.utc),
            },
            {
                "phase_number": 1, "title": "CUET UG 2026 Final Answer Key",
                "answer_key_type": "final",
                "files": [
                    {"label": "Final Answer Key (All Subjects)", "url": "https://cuet.nta.nic.in/fak/cuet-ug-2026.pdf"},
                ],
                "published_at": datetime(2026, 6, 25, tzinfo=timezone.utc),
            },
        ],
        "results": [
            {
                "phase_number": 1, "title": "CUET UG 2026 Score Card",
                "result_type": "merit_list",
                "download_url": "https://cuet.nta.nic.in/result",
                "cutoff_marks": {
                    "DU_BCom_Hons_General_approx": 732,
                    "DU_BA_English_Hons_approx": 710,
                    "JNU_BA_Programme_approx": 685,
                },
                "notes": "CUET score valid for admission at all 280+ participating universities. Each university publishes its own cutoff merit list separately.",
                "published_at": datetime(2026, 6, 30, tzinfo=timezone.utc),
            },
        ],
    },

    "neet-ss-2025": {
        "admit_cards": [
            {
                "phase_number": 1, "title": "NEET SS 2025 Admit Card",
                "download_url": "https://natboard.edu.in/neet-ss/admit-card",
                "valid_from": date(2025, 8, 22), "valid_until": date(2025, 9, 1),
                "notes": "Download from natboard.edu.in. Carry printout + NMC registration certificate + Govt. photo ID.",
                "published_at": datetime(2025, 8, 22, tzinfo=timezone.utc),
            },
        ],
        "answer_keys": [
            {
                "phase_number": 1, "title": "NEET SS 2025 Provisional Answer Key",
                "answer_key_type": "provisional",
                "files": [
                    {"label": "NEET SS 2025 Answer Key (All Specialities)", "url": "https://natboard.edu.in/neet-ss/ak-2025.pdf"},
                ],
                "objection_url": "https://natboard.edu.in/neet-ss/objection",
                "objection_deadline": date(2025, 9, 12),
                "published_at": datetime(2025, 9, 7, tzinfo=timezone.utc),
            },
            {
                "phase_number": 1, "title": "NEET SS 2025 Final Answer Key",
                "answer_key_type": "final",
                "files": [
                    {"label": "Final Answer Key", "url": "https://natboard.edu.in/neet-ss/fak-2025.pdf"},
                ],
                "published_at": datetime(2025, 9, 25, tzinfo=timezone.utc),
            },
        ],
        "results": [
            {
                "phase_number": 1, "title": "NEET SS 2025 Result — Score Card & Merit List",
                "result_type": "merit_list",
                "download_url": "https://natboard.edu.in/neet-ss/result",
                "cutoff_marks": {
                    "General_qualifying_percentile": 50,
                    "SC_ST_OBC_PwBD_percentile": 40,
                },
                "notes": "Score card used for MCC DM/M.Ch counselling. AIQ: 50% seats; State Quota: 50% seats.",
                "published_at": datetime(2025, 10, 1, tzinfo=timezone.utc),
            },
        ],
    },

    "gate-2026": {
        "admit_cards": [
            {
                "phase_number": 1, "title": "GATE 2026 Admit Card",
                "download_url": "https://gate2026.iitr.ac.in/admit-card",
                "valid_from": date(2026, 1, 8), "valid_until": date(2026, 2, 15),
                "notes": "Download from GOAPS portal at gate2026.iitr.ac.in. Carry printout + original Govt. photo ID + passport photo.",
                "published_at": datetime(2026, 1, 8, tzinfo=timezone.utc),
            },
        ],
        "answer_keys": [
            {
                "phase_number": 1, "title": "GATE 2026 Provisional Answer Key",
                "answer_key_type": "provisional",
                "files": [
                    {"label": "CS — Computer Science & IT", "url": "https://gate2026.iitr.ac.in/ak/cs.pdf"},
                    {"label": "EC — Electronics & Communication", "url": "https://gate2026.iitr.ac.in/ak/ec.pdf"},
                    {"label": "ME — Mechanical Engineering", "url": "https://gate2026.iitr.ac.in/ak/me.pdf"},
                    {"label": "CE — Civil Engineering", "url": "https://gate2026.iitr.ac.in/ak/ce.pdf"},
                    {"label": "EE — Electrical Engineering", "url": "https://gate2026.iitr.ac.in/ak/ee.pdf"},
                    {"label": "CH — Chemical Engineering", "url": "https://gate2026.iitr.ac.in/ak/ch.pdf"},
                    {"label": "IN — Instrumentation Engineering", "url": "https://gate2026.iitr.ac.in/ak/in.pdf"},
                    {"label": "BT — Biotechnology", "url": "https://gate2026.iitr.ac.in/ak/bt.pdf"},
                    {"label": "Other Papers", "url": "https://gate2026.iitr.ac.in/ak/others.pdf"},
                ],
                "objection_url": "https://gate2026.iitr.ac.in/objection",
                "objection_deadline": date(2026, 2, 22),
                "published_at": datetime(2026, 2, 18, tzinfo=timezone.utc),
            },
            {
                "phase_number": 1, "title": "GATE 2026 Final Answer Key",
                "answer_key_type": "final",
                "files": [
                    {"label": "Final Answer Keys (All 29 Papers)", "url": "https://gate2026.iitr.ac.in/fak/all-papers.pdf"},
                ],
                "published_at": datetime(2026, 3, 15, tzinfo=timezone.utc),
            },
        ],
        "results": [
            {
                "phase_number": 1, "title": "GATE 2026 Score Card",
                "result_type": "merit_list",
                "download_url": "https://gate2026.iitr.ac.in/result",
                "cutoff_marks": {
                    "CS_General_qualifying_marks": 28.5,
                    "EC_General_qualifying_marks": 26.0,
                    "ME_General_qualifying_marks": 34.0,
                    "CE_General_qualifying_marks": 29.4,
                    "EE_General_qualifying_marks": 30.2,
                    "OBC_NCL_cutoff_fraction": 0.9,
                    "SC_ST_PwD_cutoff_fraction": 0.667,
                },
                "notes": "GATE 2026 score valid for 3 years. Used for M.Tech/Ph.D admissions (CCMT, individual IITs) and PSU direct recruitment (DRDO, ONGC, IOCL, NTPC, BHEL etc.).",
                "published_at": datetime(2026, 3, 19, tzinfo=timezone.utc),
            },
        ],
    },
}


# ---------------------------------------------------------------------------
# Section 2: Admit Card standalone posts (9 entries)
# These appear on the /admit-cards section page.
# Keep compact — just the essential fields for an admit card announcement.
# ---------------------------------------------------------------------------

ADMIT_CARD_POSTS = [
    {
        "job_title": "SSC CGL Tier-1 2025 Admit Card Released",
        "slug": "ssc-cgl-tier1-2025-admit-card",
        "organization": "Staff Selection Commission", "department": "SSC",
        "job_type": "admit_card",
        "short_description": "SSC CGL Tier-1 2025 admit card available for download. Carry printout to exam centre with valid photo ID.",
        "source_url": "https://ssc.nic.in/admit-card",
        "notification_date": date(2025, 12, 28),
        "exam_start": date(2026, 1, 5),
        "status": "active", "is_featured": False, "is_urgent": True,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
    {
        "job_title": "SSC GD Constable CBT 2025 Admit Card",
        "slug": "ssc-gd-cbt-2025-admit-card",
        "organization": "Staff Selection Commission", "department": "SSC",
        "job_type": "admit_card",
        "short_description": "SSC GD Constable CBT Admit Card 2025 released. Download from ssc.nic.in using registration number and DOB.",
        "source_url": "https://ssc.nic.in/admit-card",
        "notification_date": date(2026, 2, 1),
        "exam_start": date(2026, 2, 15),
        "status": "active", "is_featured": False, "is_urgent": True,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
    {
        "job_title": "RRB NTPC CBT-1 2026 Admit Card",
        "slug": "rrb-ntpc-cbt1-2026-admit-card",
        "organization": "Railway Recruitment Board", "department": "Ministry of Railways",
        "job_type": "admit_card",
        "short_description": "RRB NTPC CBT-1 2026 Admit Card released on RRB regional websites. Download using Registration No. & DOB.",
        "source_url": "https://rrbapply.gov.in/admit-card",
        "notification_date": date(2026, 2, 10),
        "exam_start": date(2026, 3, 1),
        "status": "active", "is_featured": False, "is_urgent": True,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
    {
        "job_title": "IBPS PO Prelims 2025 Admit Card",
        "slug": "ibps-po-prelims-2025-admit-card",
        "organization": "Institute of Banking Personnel Selection", "department": "IBPS",
        "job_type": "admit_card",
        "short_description": "IBPS PO Prelims 2025 Call Letter released. Download from ibps.in. Exam scheduled across multiple dates.",
        "source_url": "https://ibps.in/call-letter",
        "notification_date": date(2025, 10, 10),
        "exam_start": date(2025, 10, 18),
        "status": "active", "is_featured": False, "is_urgent": False,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
    {
        "job_title": "UPSC CSE Prelims 2026 Admit Card",
        "slug": "upsc-cse-prelims-2026-admit-card",
        "organization": "Union Public Service Commission", "department": "UPSC",
        "job_type": "admit_card",
        "short_description": "UPSC Civil Services Prelims 2026 e-Admit Card available on upsc.gov.in. Carry printout to IFoS exam hall.",
        "source_url": "https://upsc.gov.in/admit-card",
        "notification_date": date(2026, 5, 10),
        "exam_start": date(2026, 5, 25),
        "status": "active", "is_featured": False, "is_urgent": True,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
    {
        "job_title": "SSC CHSL Tier-1 2025 Admit Card Released",
        "slug": "ssc-chsl-tier1-2025-admit-card",
        "organization": "Staff Selection Commission", "department": "SSC",
        "job_type": "admit_card",
        "short_description": "SSC CHSL Tier-1 2025 Hall Ticket available. Download from ssc.nic.in. Exam for LDC/DEO/JSA posts.",
        "source_url": "https://ssc.nic.in/chsl-admit-card",
        "notification_date": date(2025, 11, 20),
        "exam_start": date(2025, 12, 1),
        "status": "active", "is_featured": False, "is_urgent": False,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
    {
        "job_title": "IBPS RRB PO Prelims 2025 Admit Card",
        "slug": "ibps-rrb-po-prelims-2025-admit-card",
        "organization": "Institute of Banking Personnel Selection", "department": "IBPS",
        "job_type": "admit_card",
        "short_description": "IBPS RRB Officer Scale-I Prelims 2025 Admit Card available on ibps.in. Download using Reg. No. & DOB.",
        "source_url": "https://ibps.in/rrb-call-letter",
        "notification_date": date(2025, 7, 25),
        "exam_start": date(2025, 8, 3),
        "status": "active", "is_featured": False, "is_urgent": False,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
    {
        "job_title": "NTA NEET PG 2026 Admit Card",
        "slug": "nta-neet-pg-2026-hall-ticket",
        "organization": "National Testing Agency", "department": "Ministry of Health & Family Welfare",
        "job_type": "admit_card",
        "short_description": "NEET PG 2026 Admit Card released on nta.ac.in. Candidates must carry printout with valid photo ID to exam centre.",
        "source_url": "https://nta.ac.in/neet-pg/admit-card",
        "notification_date": date(2026, 3, 1),
        "exam_start": date(2026, 3, 9),
        "status": "active", "is_featured": False, "is_urgent": True,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
    {
        "job_title": "CTET December 2025 Admit Card Released",
        "slug": "ctet-december-2025-admit-card",
        "organization": "Central Board of Secondary Education", "department": "CBSE",
        "job_type": "admit_card",
        "short_description": "CTET December 2025 Hall Ticket available on ctet.nic.in. Download using Application No. & DOB for Paper I & II.",
        "source_url": "https://ctet.nic.in/admit-card",
        "notification_date": date(2025, 12, 5),
        "exam_start": date(2025, 12, 14),
        "status": "active", "is_featured": False, "is_urgent": False,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
]


# ---------------------------------------------------------------------------
# Section 3: Answer Key standalone posts (9 entries)
# These appear on the /answer-keys section page.
# ---------------------------------------------------------------------------

ANSWER_KEY_POSTS = [
    {
        "job_title": "SSC CGL Tier-1 2025 Provisional Answer Key",
        "slug": "ssc-cgl-tier1-2025-answer-key-provisional",
        "organization": "Staff Selection Commission", "department": "SSC",
        "job_type": "answer_key",
        "short_description": "SSC CGL Tier-1 2025 Provisional Answer Key released. Check all sets (A/B/C/D). Raise objections by 18 Jan 2026.",
        "source_url": "https://ssc.nic.in/answer-key",
        "notification_date": date(2026, 1, 12),
        "exam_start": date(2026, 1, 5),
        "status": "active", "is_featured": False, "is_urgent": False,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
    {
        "job_title": "SSC CGL Tier-1 2025 Final Answer Key",
        "slug": "ssc-cgl-tier1-2025-answer-key-final",
        "organization": "Staff Selection Commission", "department": "SSC",
        "job_type": "answer_key",
        "short_description": "SSC CGL Tier-1 2025 Final Answer Key published after objection review. Download PDF from ssc.nic.in.",
        "source_url": "https://ssc.nic.in/answer-key-final",
        "notification_date": date(2026, 2, 5),
        "exam_start": date(2026, 1, 5),
        "status": "active", "is_featured": False, "is_urgent": False,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
    {
        "job_title": "RRB NTPC CBT-1 2025 Provisional Answer Key",
        "slug": "rrb-ntpc-cbt1-2025-answer-key",
        "organization": "Railway Recruitment Board", "department": "Ministry of Railways",
        "job_type": "answer_key",
        "short_description": "RRB NTPC CBT-1 2025 Provisional Answer Key available. Download question paper + answer key. Objections open till 5 Dec.",
        "source_url": "https://rrbapply.gov.in/answer-key",
        "notification_date": date(2025, 11, 25),
        "exam_start": date(2025, 11, 1),
        "status": "active", "is_featured": False, "is_urgent": False,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
    {
        "job_title": "IBPS PO Prelims 2025 Answer Key",
        "slug": "ibps-po-prelims-2025-answer-key",
        "organization": "Institute of Banking Personnel Selection", "department": "IBPS",
        "job_type": "answer_key",
        "short_description": "IBPS PO Prelims 2025 Answer Key with question paper available on ibps.in. Check your provisional score.",
        "source_url": "https://ibps.in/answer-key",
        "notification_date": date(2025, 10, 28),
        "exam_start": date(2025, 10, 18),
        "status": "active", "is_featured": False, "is_urgent": False,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
    {
        "job_title": "UPSC CAPF AC 2025 Provisional Answer Key",
        "slug": "upsc-capf-ac-2025-answer-key",
        "organization": "Union Public Service Commission", "department": "UPSC",
        "job_type": "answer_key",
        "short_description": "UPSC CAPF Assistant Commandant 2025 Provisional Answer Key for Paper I & II. Representation window open.",
        "source_url": "https://upsc.gov.in/answer-key",
        "notification_date": date(2025, 8, 15),
        "exam_start": date(2025, 8, 3),
        "status": "active", "is_featured": False, "is_urgent": False,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
    {
        "job_title": "NTA NEET UG 2025 Final Answer Key",
        "slug": "nta-neet-ug-2025-answer-key-final",
        "organization": "National Testing Agency", "department": "NTA",
        "job_type": "answer_key",
        "short_description": "NEET UG 2025 Final Answer Key released on nta.ac.in. All objections resolved. Result based on final key.",
        "source_url": "https://nta.ac.in/neet-ug/answer-key",
        "notification_date": date(2025, 6, 14),
        "exam_start": date(2025, 5, 4),
        "status": "active", "is_featured": False, "is_urgent": False,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
    {
        "job_title": "SSC CHSL Tier-1 2024 Final Answer Key",
        "slug": "ssc-chsl-tier1-2024-answer-key-final",
        "organization": "Staff Selection Commission", "department": "SSC",
        "job_type": "answer_key",
        "short_description": "SSC CHSL Tier-1 2024 Final Answer Key published. Download all shift PDFs from ssc.nic.in.",
        "source_url": "https://ssc.nic.in/chsl-answer-key",
        "notification_date": date(2024, 7, 15),
        "exam_start": date(2024, 7, 1),
        "status": "active", "is_featured": False, "is_urgent": False,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
    {
        "job_title": "IBPS RRB PO Prelims 2025 Answer Key",
        "slug": "ibps-rrb-po-prelims-2025-answer-key",
        "organization": "Institute of Banking Personnel Selection", "department": "IBPS",
        "job_type": "answer_key",
        "short_description": "IBPS RRB Officer Scale-I Prelims 2025 Answer Key released. Download question paper and answer key from ibps.in.",
        "source_url": "https://ibps.in/rrb-answer-key",
        "notification_date": date(2025, 8, 12),
        "exam_start": date(2025, 8, 3),
        "status": "active", "is_featured": False, "is_urgent": False,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
    {
        "job_title": "SSC MTS Tier-1 2024 Final Answer Key",
        "slug": "ssc-mts-tier1-2024-answer-key-final",
        "organization": "Staff Selection Commission", "department": "SSC",
        "job_type": "answer_key",
        "short_description": "SSC MTS & Havaldar Tier-1 2024 Final Answer Key published. All 20 shifts PDFs available on ssc.nic.in.",
        "source_url": "https://ssc.nic.in/mts-answer-key",
        "notification_date": date(2024, 10, 20),
        "exam_start": date(2024, 9, 30),
        "status": "active", "is_featured": False, "is_urgent": False,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
]


# ---------------------------------------------------------------------------
# Section 4: Result standalone posts (9 entries)
# These appear on the /results section page.
# ---------------------------------------------------------------------------

RESULT_POSTS = [
    {
        "job_title": "SSC CGL 2024 Final Result Declared",
        "slug": "ssc-cgl-2024-final-result",
        "organization": "Staff Selection Commission", "department": "SSC",
        "job_type": "result",
        "short_description": "SSC CGL 2024 Final Result declared. Check merit list, cut-off marks and post-wise allocation on ssc.nic.in.",
        "source_url": "https://ssc.nic.in/result",
        "notification_date": date(2025, 4, 1),
        "result_date": date(2025, 4, 1),
        "status": "active", "is_featured": False, "is_urgent": False,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
    {
        "job_title": "IBPS PO 2024 Final Result Announced",
        "slug": "ibps-po-2024-final-result",
        "organization": "Institute of Banking Personnel Selection", "department": "IBPS",
        "job_type": "result",
        "short_description": "IBPS PO 2024 Final Result released. Provisionally selected candidates called for document verification by participating banks.",
        "source_url": "https://ibps.in/result",
        "notification_date": date(2025, 2, 1),
        "result_date": date(2025, 2, 1),
        "status": "active", "is_featured": False, "is_urgent": False,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
    {
        "job_title": "RRB NTPC CBT-1 2025 Shortlist Result",
        "slug": "rrb-ntpc-cbt1-2025-result",
        "organization": "Railway Recruitment Board", "department": "Ministry of Railways",
        "job_type": "result",
        "short_description": "RRB NTPC CBT-1 2025 shortlisting result declared. Check category-wise cut-off and candidates shortlisted for CBT-2.",
        "source_url": "https://rrbapply.gov.in/result",
        "notification_date": date(2026, 1, 15),
        "result_date": date(2026, 1, 15),
        "status": "active", "is_featured": False, "is_urgent": False,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
    {
        "job_title": "UPSC Civil Services 2025 Final Result",
        "slug": "upsc-cse-2025-final-result",
        "organization": "Union Public Service Commission", "department": "UPSC",
        "job_type": "result",
        "short_description": "UPSC IAS/IPS 2025 Final Result declared. 1016 candidates recommended for various civil services. Check complete merit list.",
        "source_url": "https://upsc.gov.in/result",
        "notification_date": date(2026, 4, 25),
        "result_date": date(2026, 4, 25),
        "status": "active", "is_featured": True, "is_urgent": False,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
    {
        "job_title": "SSC CHSL 2024 Final Result Declared",
        "slug": "ssc-chsl-2024-final-result",
        "organization": "Staff Selection Commission", "department": "SSC",
        "job_type": "result",
        "short_description": "SSC CHSL 2024 Final Result for LDC/DEO/JSA posts declared. Cut-off marks and post-wise allocation available.",
        "source_url": "https://ssc.nic.in/chsl-result",
        "notification_date": date(2025, 6, 10),
        "result_date": date(2025, 6, 10),
        "status": "active", "is_featured": False, "is_urgent": False,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
    {
        "job_title": "NTA NEET PG 2025 Result Declared",
        "slug": "nta-neet-pg-2025-result",
        "organization": "National Testing Agency", "department": "Ministry of Health & Family Welfare",
        "job_type": "result",
        "short_description": "NEET PG 2025 Result and score card available on nta.ac.in. AIR-wise score and percentile published.",
        "source_url": "https://nta.ac.in/neet-pg/result",
        "notification_date": date(2025, 5, 1),
        "result_date": date(2025, 5, 1),
        "status": "active", "is_featured": False, "is_urgent": False,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
    {
        "job_title": "IBPS Clerk 2024 Prelims Result Out",
        "slug": "ibps-clerk-2024-prelims-result",
        "organization": "Institute of Banking Personnel Selection", "department": "IBPS",
        "job_type": "result",
        "short_description": "IBPS Clerk XIV Prelims 2024 Result declared. Shortlisted candidates proceed to Main Examination. Check ibps.in.",
        "source_url": "https://ibps.in/clerk-result",
        "notification_date": date(2025, 1, 10),
        "result_date": date(2025, 1, 10),
        "status": "active", "is_featured": False, "is_urgent": False,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
    {
        "job_title": "SSC GD Constable 2024 Final Result",
        "slug": "ssc-gd-constable-2024-final-result",
        "organization": "Staff Selection Commission", "department": "SSC",
        "job_type": "result",
        "short_description": "SSC GD Constable 2024 Final Result declared. Category-wise cut-off and merit list published on ssc.nic.in.",
        "source_url": "https://ssc.nic.in/gd-result",
        "notification_date": date(2025, 3, 20),
        "result_date": date(2025, 3, 20),
        "status": "active", "is_featured": False, "is_urgent": False,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
    {
        "job_title": "Railway ALP & Technician 2024 Final Result",
        "slug": "rrb-alp-technician-2024-final-result",
        "organization": "Railway Recruitment Board", "department": "Ministry of Railways",
        "job_type": "result",
        "short_description": "RRB ALP & Technician 2024 Final Result declared. Selected candidates called for document verification. Check rrb regional website.",
        "source_url": "https://rrbapply.gov.in/alp-result",
        "notification_date": date(2025, 2, 28),
        "result_date": date(2025, 2, 28),
        "status": "active", "is_featured": False, "is_urgent": False,
        "vacancy_breakdown": {}, "salary": {}, "eligibility": {}, "application_details": {}, "documents": [], "selection_process": [], "exam_details": {},
    },
]


# ---------------------------------------------------------------------------
# Per-phase linked documents for latest_job entries
# Keys are job slugs; values have lists for admit_cards, answer_keys, results.
# These populate job_admit_cards / job_answer_keys / job_results tables.
# phase_number maps to selection_process[?].phase in the parent job.
# ---------------------------------------------------------------------------

PHASE_DOCS = {
    "ssc-cgl-combined-graduate-level-2025": {
        "admit_cards": [
            {
                "phase_number": 1, "title": "SSC CGL Tier-1 2025 Admit Card",
                "download_url": "https://ssc.nic.in/admit-card/cgl-tier1",
                "valid_from": date(2025, 12, 28), "valid_until": date(2026, 1, 15),
                "notes": "Download from ssc.nic.in using Registration No. & DOB. Carry printout to exam.",
                "published_at": datetime(2025, 12, 28, tzinfo=timezone.utc),
            },
            {
                "phase_number": 2, "title": "SSC CGL Tier-2 2026 Admit Card",
                "download_url": "https://ssc.nic.in/admit-card/cgl-tier2",
                "valid_from": date(2026, 2, 20), "valid_until": date(2026, 3, 1),
                "notes": "Applicable only for candidates qualified in Tier-1.",
                "published_at": datetime(2026, 2, 20, tzinfo=timezone.utc),
            },
        ],
        "answer_keys": [
            {
                "phase_number": 1, "title": "SSC CGL Tier-1 2025 Provisional Answer Key",
                "answer_key_type": "provisional",
                "files": [
                    {"label": "Set A", "url": "https://ssc.nic.in/ak/cgl-t1-seta.pdf"},
                    {"label": "Set B", "url": "https://ssc.nic.in/ak/cgl-t1-setb.pdf"},
                    {"label": "Set C", "url": "https://ssc.nic.in/ak/cgl-t1-setc.pdf"},
                    {"label": "Set D", "url": "https://ssc.nic.in/ak/cgl-t1-setd.pdf"},
                ],
                "objection_url": "https://ssc.nic.in/objection",
                "objection_deadline": date(2026, 1, 18),
                "published_at": datetime(2026, 1, 12, tzinfo=timezone.utc),
            },
            {
                "phase_number": 1, "title": "SSC CGL Tier-1 2025 Final Answer Key",
                "answer_key_type": "final",
                "files": [
                    {"label": "Set A", "url": "https://ssc.nic.in/fak/cgl-t1-seta.pdf"},
                    {"label": "Set B", "url": "https://ssc.nic.in/fak/cgl-t1-setb.pdf"},
                    {"label": "Set C", "url": "https://ssc.nic.in/fak/cgl-t1-setc.pdf"},
                    {"label": "Set D", "url": "https://ssc.nic.in/fak/cgl-t1-setd.pdf"},
                ],
                "published_at": datetime(2026, 2, 5, tzinfo=timezone.utc),
            },
        ],
        "results": [
            {
                "phase_number": 1, "title": "SSC CGL Tier-1 2025 Result — Shortlist for Tier-2",
                "result_type": "shortlist",
                "download_url": "https://ssc.nic.in/result/cgl-tier1-2025",
                "cutoff_marks": {"UR": 148.75, "OBC": 143.25, "EWS": 141.50, "SC": 128.00, "ST": 119.50},
                "total_qualified": 175200,
                "notes": "Candidates scoring above cut-off in respective categories are shortlisted for Tier-2.",
                "published_at": datetime(2026, 3, 10, tzinfo=timezone.utc),
            },
        ],
    },

    "ibps-po-recruitment-2025": {
        "admit_cards": [
            {
                "phase_number": 1, "title": "IBPS PO Prelims 2025 Call Letter",
                "download_url": "https://ibps.in/call-letter/po-prelims",
                "valid_from": date(2025, 10, 10), "valid_until": date(2025, 10, 26),
                "notes": "Download using Registration No. & Password/DOB. Exam on multiple dates.",
                "published_at": datetime(2025, 10, 10, tzinfo=timezone.utc),
            },
            {
                "phase_number": 2, "title": "IBPS PO Mains 2025 Call Letter",
                "download_url": "https://ibps.in/call-letter/po-mains",
                "valid_from": date(2025, 11, 20), "valid_until": date(2025, 11, 30),
                "notes": "Only for candidates who cleared Prelims.",
                "published_at": datetime(2025, 11, 20, tzinfo=timezone.utc),
            },
        ],
        "answer_keys": [
            {
                "phase_number": 1, "title": "IBPS PO Prelims 2025 Answer Key",
                "answer_key_type": "provisional",
                "files": [
                    {"label": "English Language", "url": "https://ibps.in/ak/po-eng.pdf"},
                    {"label": "Quantitative Aptitude", "url": "https://ibps.in/ak/po-qa.pdf"},
                    {"label": "Reasoning Ability", "url": "https://ibps.in/ak/po-ra.pdf"},
                ],
                "published_at": datetime(2025, 10, 28, tzinfo=timezone.utc),
            },
        ],
        "results": [
            {
                "phase_number": 1, "title": "IBPS PO Prelims 2025 Result",
                "result_type": "shortlist",
                "download_url": "https://ibps.in/result/po-prelims",
                "cutoff_marks": {"UR": 64.25, "OBC": 60.50, "EWS": 61.75, "SC": 52.00, "ST": 48.75},
                "total_qualified": 41800,
                "published_at": datetime(2025, 11, 15, tzinfo=timezone.utc),
            },
        ],
    },

    "rrb-ntpc-graduate-level-recruitment-2025": {
        "admit_cards": [
            {
                "phase_number": 1, "title": "RRB NTPC CBT-1 2026 Admit Card",
                "download_url": "https://rrbapply.gov.in/admit-card",
                "valid_from": date(2026, 2, 10), "valid_until": date(2026, 3, 31),
                "notes": "Download from your respective RRB regional website using Registration No. & DOB.",
                "published_at": datetime(2026, 2, 10, tzinfo=timezone.utc),
            },
        ],
        "answer_keys": [
            {
                "phase_number": 1, "title": "RRB NTPC CBT-1 2026 Provisional Answer Key",
                "answer_key_type": "provisional",
                "files": [{"label": "Question Paper + Answer Key", "url": "https://rrbapply.gov.in/answer-key/ntpc-cbt1.pdf"}],
                "objection_url": "https://rrbapply.gov.in/objection",
                "objection_deadline": date(2026, 4, 10),
                "published_at": datetime(2026, 4, 1, tzinfo=timezone.utc),
            },
        ],
        "results": [
            {
                "phase_number": 1, "title": "RRB NTPC CBT-1 2026 Result — Shortlist for CBT-2",
                "result_type": "shortlist",
                "download_url": "https://rrbapply.gov.in/result/ntpc-cbt1",
                "cutoff_marks": {"UR": 72.50, "OBC": 68.00, "EWS": 70.25, "SC": 62.50, "ST": 58.00},
                "total_qualified": 115800,
                "notes": "Candidates shortlisted at 20× vacancy count in each category and post.",
                "published_at": datetime(2026, 5, 15, tzinfo=timezone.utc),
            },
        ],
    },

    # Note: nta-neet-pg-2026 phase docs are in EXAM_PHASE_DOCS (exam_id FK)
}


# ---------------------------------------------------------------------------
# Insert
# ---------------------------------------------------------------------------

def _make_job(data: dict, admin_id) -> JobVacancy:
    """Build a JobVacancy ORM object from a data dict."""
    return JobVacancy(
        id=uuid.uuid4(),
        job_title=data["job_title"],
        slug=data["slug"],
        organization=data["organization"],
        department=data.get("department"),
        job_type=data.get("job_type", "latest_job"),
        employment_type=data.get("employment_type", "permanent"),
        qualification_level=data.get("qualification_level"),
        total_vacancies=data.get("total_vacancies"),
        vacancy_breakdown=data.get("vacancy_breakdown", {}),
        description=data.get("description"),
        short_description=data.get("short_description"),
        eligibility=data.get("eligibility", {}),
        application_details=data.get("application_details", {}),
        documents=data.get("documents", []),
        source_url=data.get("source_url"),
        notification_date=data.get("notification_date"),
        application_start=data.get("application_start"),
        application_end=data.get("application_end"),
        exam_start=data.get("exam_start"),
        exam_end=data.get("exam_end"),
        result_date=data.get("result_date"),
        exam_details=data.get("exam_details", {}),
        salary_initial=data.get("salary_initial"),
        salary_max=data.get("salary_max"),
        salary=data.get("salary", {}),
        selection_process=data.get("selection_process", []),
        fee_general=data.get("fee_general"),
        fee_obc=data.get("fee_obc"),
        fee_sc_st=data.get("fee_sc_st"),
        fee_ews=data.get("fee_ews"),
        fee_female=data.get("fee_female"),
        status=data.get("status", "active"),
        is_featured=data.get("is_featured", False),
        is_urgent=data.get("is_urgent", False),
        views=0,
        applications_count=0,
        source="manual",
        created_by=admin_id,
        published_at=datetime.now(timezone.utc),
    )


def _insert_phase_docs(session, phase_docs_dict: dict, id_by_slug: dict, use_exam_id: bool = False):
    """Insert linked phase documents; returns count inserted."""
    count = 0
    for slug, docs in phase_docs_dict.items():
        parent_id = id_by_slug.get(slug)
        if not parent_id:
            print(f"  PHASE DOCS SKIP (parent not found): {slug}")
            continue
        kw_job = {} if use_exam_id else {}

        for ac in docs.get("admit_cards", []):
            kwargs = {"exam_id": parent_id} if use_exam_id else {"job_id": parent_id}
            exists = session.execute(
                select(JobAdmitCard).where(
                    JobAdmitCard.exam_id == parent_id if use_exam_id else JobAdmitCard.job_id == parent_id,
                    JobAdmitCard.title == ac["title"],
                )
            ).scalar_one_or_none()
            if not exists:
                session.add(JobAdmitCard(id=uuid.uuid4(), **kwargs, **ac))
                count += 1

        for ak in docs.get("answer_keys", []):
            kwargs = {"exam_id": parent_id} if use_exam_id else {"job_id": parent_id}
            exists = session.execute(
                select(JobAnswerKey).where(
                    JobAnswerKey.exam_id == parent_id if use_exam_id else JobAnswerKey.job_id == parent_id,
                    JobAnswerKey.title == ak["title"],
                )
            ).scalar_one_or_none()
            if not exists:
                session.add(JobAnswerKey(id=uuid.uuid4(), **kwargs, **ak))
                count += 1

        for res in docs.get("results", []):
            kwargs = {"exam_id": parent_id} if use_exam_id else {"job_id": parent_id}
            exists = session.execute(
                select(JobResult).where(
                    JobResult.exam_id == parent_id if use_exam_id else JobResult.job_id == parent_id,
                    JobResult.title == res["title"],
                )
            ).scalar_one_or_none()
            if not exists:
                session.add(JobResult(id=uuid.uuid4(), **kwargs, **res))
                count += 1
    return count


def seed():
    with Session(sync_engine) as session:
        admin_id = _get_admin_id(session)
        inserted = 0
        exam_inserted = 0
        skipped = 0
        docs_inserted = 0

        # ── Step 1: Remove restructured job_vacancies slugs ────────────
        for old_slug in SLUGS_TO_REPLACE:
            old = session.execute(
                select(JobVacancy).where(JobVacancy.slug == old_slug)
            ).scalar_one_or_none()
            if old:
                session.delete(old)
                print(f"  REMOVE (restructured): {old_slug}")
        session.flush()

        # ── Step 2: Insert job_vacancies (jobs + section posts) ────────
        all_jobs = JOBS + ADMIT_CARD_POSTS + ANSWER_KEY_POSTS + RESULT_POSTS
        job_id_by_slug: dict[str, uuid.UUID] = {}

        for data in all_jobs:
            existing = session.execute(
                select(JobVacancy).where(JobVacancy.slug == data["slug"])
            ).scalar_one_or_none()
            if existing:
                job_id_by_slug[data["slug"]] = existing.id
                skipped += 1
                print(f"  SKIP  (job exists): {data['slug']}")
                continue
            job = _make_job(data, admin_id)
            session.add(job)
            job_id_by_slug[data["slug"]] = job.id
            inserted += 1
            print(f"  INSERT job: {data['slug']}")

        session.flush()

        # ── Step 3: Insert entrance_exams ──────────────────────────────
        exam_id_by_slug: dict[str, uuid.UUID] = {}

        for data in ADMISSIONS:
            existing = session.execute(
                select(EntranceExam).where(EntranceExam.slug == data["slug"])
            ).scalar_one_or_none()
            if existing:
                exam_id_by_slug[data["slug"]] = existing.id
                skipped += 1
                print(f"  SKIP  (exam exists): {data['slug']}")
                continue
            exam = EntranceExam(
                id=uuid.uuid4(),
                published_at=datetime.now(timezone.utc),
                **{k: v for k, v in data.items()},
            )
            session.add(exam)
            exam_id_by_slug[data["slug"]] = exam.id
            exam_inserted += 1
            print(f"  INSERT exam: {data['slug']}")

        session.flush()

        # ── Step 4: Insert job phase docs (job_id) ────────────────────
        docs_inserted += _insert_phase_docs(session, PHASE_DOCS, job_id_by_slug, use_exam_id=False)

        # ── Step 5: Insert exam phase docs (exam_id) ──────────────────
        docs_inserted += _insert_phase_docs(session, EXAM_PHASE_DOCS, exam_id_by_slug, use_exam_id=True)

        session.commit()
        print(f"\nDone — {inserted} jobs + {exam_inserted} exams inserted, {docs_inserted} phase docs, {skipped} skipped.")


if __name__ == "__main__":
    seed()
