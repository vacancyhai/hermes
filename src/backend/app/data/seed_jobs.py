"""Seed script — inserts 9 realistic government job vacancies into the database.

Usage (inside Docker):
    docker exec -w /app hermes_backend python -m app.data.seed_jobs
"""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import sync_engine
from app.models.admin_user import AdminUser
from app.models.job_vacancy import JobVacancy

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slug_exists(session: Session, slug: str) -> bool:
    return session.execute(select(JobVacancy).where(JobVacancy.slug == slug)).scalar_one_or_none() is not None


def _get_admin_id(session: Session) -> uuid.UUID | None:
    admin = session.execute(select(AdminUser).where(AdminUser.role == "admin").limit(1)).scalar_one_or_none()
    return admin.id if admin else None


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
    # 5. NEET PG Admit Card 2026
    # ------------------------------------------------------------------
    {
        "job_title": "NTA NEET PG 2026 Admit Card Released",
        "slug": "nta-neet-pg-2026-admit-card",
        "organization": "National Testing Agency",
        "department": "Ministry of Health & Family Welfare",
        "job_type": "admit_card",
        "employment_type": "contract",
        "qualification_level": "post-graduate",
        "total_vacancies": None,
        "vacancy_breakdown": {},
        "description": "<p>NTA has released the <strong>NEET PG 2026 Admit Card</strong>. Candidates can download their hall ticket from the official website using their application number and date of birth.</p>",
        "short_description": "NEET PG 2026 Admit Card released. Download your hall ticket from nta.ac.in using Application No. & DOB.",
        "eligibility": {
            "min_qualification": "MBBS",
            "qualification_details": "MBBS degree or equivalent from a recognized university with 12-month Internship completed",
            "age_limit": {"min": 0, "max": 0, "note": "No upper age limit"},
        },
        "application_details": {
            "application_mode": "Online",
            "application_link": "https://nta.ac.in/neet-pg",
            "official_website": "https://nta.ac.in",
            "important_links": [
                {"type": "admit_card", "text": "Download Admit Card", "url": "https://nta.ac.in/neet-pg/admit-card"},
                {"type": "official_website", "text": "Official Website", "url": "https://nta.ac.in"},
            ],
        },
        "documents": [
            {"name": "Admit Card (Print)", "mandatory": True, "format": "PDF"},
            {"name": "Government Photo ID", "mandatory": True, "format": "Original"},
        ],
        "notification_date": date(2026, 2, 10),
        "application_start": date(2025, 11, 1),
        "application_end": date(2025, 11, 30),
        "exam_start": date(2026, 3, 9),
        "result_date": date(2026, 4, 15),
        "exam_details": {
            "exam_pattern": [
                {"phase": "NEET PG", "subjects": [
                    {"name": "Pre-Clinical Subjects", "questions": 50, "marks": 200},
                    {"name": "Para-Clinical Subjects", "questions": 100, "marks": 400},
                    {"name": "Clinical Subjects", "questions": 150, "marks": 600},
                ], "total_questions": 300, "total_marks": 1200, "duration_minutes": 210, "negative_marking": 1.0, "exam_mode": "Online CBT"},
            ],
            "exam_language": ["English"],
            "total_phases": 1,
        },
        "salary": {},
        "salary_initial": None, "salary_max": None,
        "selection_process": [
            {"phase": 1, "name": "NEET PG Written Test", "qualifying": False},
            {"phase": 2, "name": "Merit-Based Counselling", "qualifying": True},
        ],
        "fee_general": 4250, "fee_obc": 4250, "fee_sc_st": 2625, "fee_ews": 4250, "fee_female": 4250,
        "status": "active", "is_featured": False, "is_urgent": True,
    },

    # ------------------------------------------------------------------
    # 6. SSC CGL 2025
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
]


# ---------------------------------------------------------------------------
# Insert
# ---------------------------------------------------------------------------

def seed():
    with Session(sync_engine) as session:
        admin_id = _get_admin_id(session)
        inserted = 0
        skipped = 0

        for data in JOBS:
            if _slug_exists(session, data["slug"]):
                print(f"  SKIP  (already exists): {data['slug']}")
                skipped += 1
                continue

            job = JobVacancy(
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
            session.add(job)
            print(f"  INSERT: {data['slug']}")
            inserted += 1

        session.commit()
        print(f"\nDone — {inserted} inserted, {skipped} skipped.")


if __name__ == "__main__":
    seed()
