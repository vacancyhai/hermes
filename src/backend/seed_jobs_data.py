"""
Seed data for 5 government job vacancies
Run this script to populate the database with sample job postings
Usage: docker compose exec backend python seed_jobs_data.py
"""

import os
import logging
from datetime import datetime

# Disable SQLAlchemy logging to avoid request_id errors
logging.basicConfig(level=logging.WARNING)
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)

from app import create_app
from app.models.job import JobVacancy
from app.extensions import db
import json


def parse_date(date_str):
    """Parse date string in YYYY-MM-DD format"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        return None


def create_seed_jobs():
    """Create 5 sample job postings"""
    
    app = create_app()
    with app.app_context():
        
        jobs_data = [
            # Job 1: SSC GD Constable
            {
                "job_title": "SSC GD Constable Recruitment 2025",
                "slug": "ssc-gd-constable-recruitment-2025",
                "organization": "Staff Selection Commission",
                "department": "SSC",
                "post_code": "SSC-GD-2025",
                "job_type": "latest_job",
                "employment_type": "permanent",
                "qualification_level": "10th",
                "total_vacancies": 25487,
                "vacancy_breakdown": {
                    "by_category": {
                        "UR": 10195,
                        "OBC": 6872,
                        "EWS": 2549,
                        "SC": 3823,
                        "ST": 2048,
                        "PWD": 100
                    },
                    "by_post": [
                        {
                            "post_name": "Constable GD",
                            "post_code": "GD-01",
                            "total": 20000,
                            "qualification": "10th Pass",
                            "age_limit": "18-23",
                            "pay_scale": "₹21,700 - ₹69,100"
                        },
                        {
                            "post_name": "Head Constable",
                            "post_code": "HC-01",
                            "total": 5487,
                            "qualification": "12th Pass",
                            "age_limit": "21-27",
                            "pay_scale": "₹25,500 - ₹81,100"
                        }
                    ],
                    "by_state": [
                        {"state": "Delhi", "vacancies": {"UR": 500, "OBC": 300, "SC": 150, "ST": 50}},
                        {"state": "UP", "vacancies": {"UR": 2000, "OBC": 1200, "SC": 800, "ST": 400}},
                        {"state": "Bihar", "vacancies": {"UR": 1500, "OBC": 900, "SC": 600, "ST": 300}}
                    ]
                },
                "description": "<h2>SSC GD Constable Recruitment 2025</h2><p>Staff Selection Commission has released notification for recruitment of 25,487 Constable (GD) posts in various forces including BSF, CRPF, CISF, ITBP, and SSB. Candidates with 10th qualification can apply online.</p>",
                "short_description": "SSC has released 25487 GD Constable vacancies. 10th pass candidates can apply online till 10 Jan 2026.",
                "eligibility": {
                    "min_qualification": "10th",
                    "required_stream": None,
                    "qualification_details": "10th Pass from recognized board",
                    "age_limit": {
                        "min": 18,
                        "max": 23,
                        "cutoff_date": "2026-01-01",
                        "relaxation": {
                            "OBC": 3,
                            "SC": 5,
                            "ST": 5,
                            "PWD": 10,
                            "Ex_Serviceman": 5
                        }
                    },
                    "physical_standards": {
                        "male": {
                            "general": {"height": 170, "chest": 80, "chest_expanded": 85},
                            "sc_st": {"height": 165, "chest": 78, "chest_expanded": 83}
                        },
                        "female": {
                            "all": {"height": 157, "weight": 48}
                        }
                    }
                },
                "application_details": {
                    "application_mode": "Online",
                    "application_link": "https://ssc.nic.in/apply",
                    "official_website": "https://ssc.nic.in",
                    "notification_pdf": "https://ssc.nic.in/notification.pdf",
                    "application_fee": {
                        "General": 100,
                        "OBC": 100,
                        "SC": 0,
                        "ST": 0,
                        "Female": 0,
                        "PWD": 0
                    }
                },
                "important_dates": {
                    "notification_date": "2025-12-01",
                    "application_start": "2025-12-10",
                    "application_end": "2026-01-10",
                    "admit_card_release": "2026-02-01",
                    "exam_start": "2026-02-15",
                    "result_date": "2026-04-15"
                },
                "salary": {
                    "pay_scale": "₹21,700 - ₹69,100",
                    "pay_level": "Level-3",
                    "initial_salary": 21700,
                    "max_salary": 69100
                },
                "status": "active",
                "is_featured": True,
                "priority": 5
            },
            
            # Job 2: Railway RRB Group D
            {
                "job_title": "Railway RRB Group D Recruitment 2026",
                "slug": "railway-rrb-group-d-recruitment-2026",
                "organization": "Railway Recruitment Board",
                "department": "Indian Railways",
                "post_code": "RRB-GD-2026",
                "job_type": "latest_job",
                "employment_type": "permanent",
                "qualification_level": "10th",
                "total_vacancies": 62907,
                "vacancy_breakdown": {
                    "by_category": {
                        "UR": 31453,
                        "OBC": 16982,
                        "SC": 9437,
                        "ST": 4718,
                        "EWS": 6291
                    },
                    "by_post": [
                        {
                            "post_name": "Track Maintainer Grade-IV",
                            "post_code": "TM-IV",
                            "total": 35000,
                            "qualification": "10th + ITI",
                            "age_limit": "18-33",
                            "pay_scale": "₹18,000 - ₹56,900"
                        },
                        {
                            "post_name": "Helper/Assistant",
                            "post_code": "HLP-01",
                            "total": 15000,
                            "qualification": "10th Pass",
                            "age_limit": "18-33",
                            "pay_scale": "₹18,000 - ₹56,900"
                        },
                        {
                            "post_name": "Assistant Pointsman",
                            "post_code": "AP-01",
                            "total": 12907,
                            "qualification": "10th Pass",
                            "age_limit": "18-33",
                            "pay_scale": "₹18,000 - ₹56,900"
                        }
                    ],
                    "by_state": [
                        {"state": "UP", "vacancies": {"UR": 8000, "OBC": 4500, "SC": 2500, "ST": 1200}},
                        {"state": "Bihar", "vacancies": {"UR": 6000, "OBC": 3500, "SC": 2000, "ST": 1000}},
                        {"state": "Maharashtra", "vacancies": {"UR": 5000, "OBC": 2800, "SC": 1500, "ST": 800}}
                    ],
                    "by_trade": [
                        {"trade": "Fitter", "total": 8500},
                        {"trade": "Welder", "total": 6200},
                        {"trade": "Electrician", "total": 7800},
                        {"trade": "Carpenter", "total": 3400}
                    ]
                },
                "description": "<h2>Railway RRB Group D Recruitment 2026</h2><p>Railway Recruitment Board has announced 62,907 vacancies for Group D posts across all Indian Railway zones. This is one of the largest railway recruitments. 10th pass candidates with/without ITI can apply.</p>",
                "short_description": "RRB announced 62,907 Group D vacancies. 10th pass candidates can apply. Age limit 18-33 years.",
                "eligibility": {
                    "min_qualification": "10th",
                    "required_stream": None,
                    "qualification_details": "10th Pass or ITI from recognized institution",
                    "age_limit": {
                        "min": 18,
                        "max": 33,
                        "cutoff_date": "2026-01-01",
                        "relaxation": {
                            "OBC": 3,
                            "SC": 5,
                            "ST": 5,
                            "PWD": 10,
                            "Ex_Serviceman": 5
                        }
                    },
                    "physical_standards": {
                        "male": {
                            "general": {"height": 157, "weight": 50},
                            "st": {"height": 152, "weight": 47}
                        },
                        "female": {
                            "all": {"height": 152, "weight": 45}
                        }
                    }
                },
                "application_details": {
                    "application_mode": "Online",
                    "application_link": "https://rrbapply.gov.in",
                    "official_website": "https://rrbcdg.gov.in",
                    "notification_pdf": "https://rrbcdg.gov.in/notification_2026.pdf",
                    "application_fee": {
                        "General": 500,
                        "OBC": 500,
                        "SC": 250,
                        "ST": 250,
                        "Female": 250,
                        "PWD": 0
                    },
                    "important_links": [
                        {"type": "apply_online", "text": "Apply Online", "url": "https://rrbapply.gov.in"},
                        {"type": "download_notification", "text": "Download Notification", "url": "https://rrbcdg.gov.in/notification_2026.pdf"},
                        {"type": "syllabus", "text": "Exam Syllabus", "url": "https://rrbcdg.gov.in/syllabus.pdf"}
                    ]
                },
                "important_dates": {
                    "notification_date": "2026-01-05",
                    "application_start": "2026-01-20",
                    "application_end": "2026-02-20",
                    "correction_start": "2026-02-25",
                    "correction_end": "2026-03-05",
                    "admit_card_release": "2026-04-01",
                    "exam_start": "2026-04-15",
                    "result_date": "2026-06-30"
                },
                "exam_details": {
                    "exam_pattern": [
                        {
                            "phase": "CBT",
                            "subjects": [
                                {"name": "Mathematics", "questions": 25, "marks": 25},
                                {"name": "General Intelligence", "questions": 30, "marks": 30},
                                {"name": "General Science", "questions": 25, "marks": 25},
                                {"name": "General Awareness", "questions": 20, "marks": 20}
                            ],
                            "total_marks": 100,
                            "duration_minutes": 90,
                            "negative_marking": 0.33,
                            "exam_mode": "Online"
                        },
                        {
                            "phase": "PET",
                            "tests": ["Physical Efficiency Test"],
                            "qualifying": True
                        },
                        {
                            "phase": "Document Verification",
                            "qualifying": True
                        }
                    ],
                    "syllabus_link": "https://rrbcdg.gov.in/syllabus.pdf",
                    "exam_language": ["Hindi", "English", "Regional Languages"],
                    "total_phases": 3
                },
                "salary": {
                    "pay_scale": "₹18,000 - ₹56,900",
                    "pay_level": "Level-1",
                    "initial_salary": 18000,
                    "max_salary": 56900,
                    "allowances": ["DA", "HRA", "TA"],
                    "other_benefits": "Free Railway Pass, Medical, Pension, PF"
                },
                "selection_process": [
                    {"phase": 1, "name": "Computer Based Test (CBT)", "qualifying": False},
                    {"phase": 2, "name": "Physical Efficiency Test (PET)", "qualifying": True},
                    {"phase": 3, "name": "Document Verification", "qualifying": True},
                    {"phase": 4, "name": "Medical Examination", "qualifying": True}
                ],
                "status": "active",
                "is_featured": True,
                "is_trending": True,
                "priority": 5
            },
            
            # Job 3: UPSC Civil Services Examination
            {
                "job_title": "UPSC Civil Services Examination 2026",
                "slug": "upsc-civil-services-examination-2026",
                "organization": "Union Public Service Commission",
                "department": "UPSC",
                "post_code": "UPSC-CSE-2026",
                "job_type": "latest_job",
                "employment_type": "permanent",
                "qualification_level": "graduation",
                "total_vacancies": 1056,
                "vacancy_breakdown": {
                    "by_category": {
                        "UR": 529,
                        "OBC": 285,
                        "SC": 159,
                        "ST": 79,
                        "EWS": 106
                    },
                    "by_post": [
                        {
                            "post_name": "IAS (Indian Administrative Service)",
                            "post_code": "IAS",
                            "total": 180,
                            "qualification": "Graduation",
                            "age_limit": "21-32",
                            "pay_scale": "₹56,100 - ₹2,50,000"
                        },
                        {
                            "post_name": "IPS (Indian Police Service)",
                            "post_code": "IPS",
                            "total": 150,
                            "qualification": "Graduation",
                            "age_limit": "21-32",
                            "pay_scale": "₹56,100 - ₹2,25,000"
                        },
                        {
                            "post_name": "IFS (Indian Foreign Service)",
                            "post_code": "IFS",
                            "total": 50,
                            "qualification": "Graduation",
                            "age_limit": "21-32",
                            "pay_scale": "₹56,100 - ₹2,50,000"
                        },
                        {
                            "post_name": "IRS (Indian Revenue Service)",
                            "post_code": "IRS",
                            "total": 150,
                            "qualification": "Graduation",
                            "age_limit": "21-32",
                            "pay_scale": "₹56,100 - ₹2,05,400"
                        },
                        {
                            "post_name": "Other Services (IDAS, IRTS, IRPS, etc)",
                            "post_code": "OTH",
                            "total": 526,
                            "qualification": "Graduation",
                            "age_limit": "21-32",
                            "pay_scale": "₹44,900 - ₹1,42,400"
                        }
                    ]
                },
                "description": "<h2>UPSC Civil Services Examination 2026</h2><p>Union Public Service Commission conducts the prestigious Civil Services Examination for recruitment to All India Services (IAS, IPS, IFS) and Group A and Group B Central Services. This exam is known as one of the toughest competitive exams in India.</p><p>The examination is conducted in three stages: Preliminary (Objective), Mains (Descriptive), and Interview (Personality Test).</p>",
                "short_description": "UPSC CSE 2026 notification for 1056 posts including IAS, IPS, IFS. Graduation required. Age 21-32 years.",
                "eligibility": {
                    "min_qualification": "graduation",
                    "required_stream": None,
                    "qualification_details": "Bachelor's Degree from recognized university in any discipline",
                    "age_limit": {
                        "min": 21,
                        "max": 32,
                        "cutoff_date": "2026-08-01",
                        "relaxation": {
                            "OBC": 3,
                            "SC": 5,
                            "ST": 5,
                            "PWD": 10,
                            "Ex_Serviceman": 5,
                            "J&K_Domicile": 5
                        },
                        "is_post_wise": False
                    },
                    "medical_standards": {
                        "vision": "For IAS/IFS - 6/6 or 6/9, For IPS - 6/6 or 6/9 (corrected)",
                        "color_blindness": "Should not be color blind (critical for IPS)",
                        "other": "Sound health, no major physical disabilities"
                    }
                },
                "application_details": {
                    "application_mode": "Online",
                    "application_link": "https://upsconline.nic.in",
                    "official_website": "https://upsc.gov.in",
                    "notification_pdf": "https://upsc.gov.in/CSE_2026_notification.pdf",
                    "application_fee": {
                        "General": 100,
                        "OBC": 100,
                        "SC": 0,
                        "ST": 0,
                        "Female": 0,
                        "PWD": 0
                    },
                    "important_links": [
                        {"type": "apply_online", "text": "Apply Online", "url": "https://upsconline.nic.in"},
                        {"type": "download_notification", "text": "Download Notification", "url": "https://upsc.gov.in/CSE_2026_notification.pdf"},
                        {"type": "syllabus", "text": "Detailed Syllabus", "url": "https://upsc.gov.in/syllabus/cse.pdf"},
                        {"type": "previous_papers", "text": "Previous Year Papers", "url": "https://upsc.gov.in/previous_papers"}
                    ]
                },
                "important_dates": {
                    "notification_date": "2026-02-05",
                    "application_start": "2026-02-12",
                    "application_end": "2026-03-05",
                    "prelims_exam": "2026-05-31",
                    "prelims_result": "2026-07-15",
                    "mains_exam_start": "2026-09-18",
                    "mains_exam_end": "2026-09-27",
                    "mains_result": "2027-01-10",
                    "interview_start": "2027-02-01",
                    "final_result": "2027-04-30"
                },
                "exam_details": {
                    "exam_pattern": [
                        {
                            "phase": "Preliminary",
                            "subjects": [
                                {"name": "General Studies Paper I", "questions": 100, "marks": 200},
                                {"name": "CSAT Paper II", "questions": 80, "marks": 200}
                            ],
                            "total_marks": 400,
                            "duration_minutes": 120,
                            "negative_marking": 0.33,
                            "exam_mode": "Offline",
                            "qualifying": True
                        },
                        {
                            "phase": "Mains",
                            "subjects": [
                                {"name": "Essay", "marks": 250},
                                {"name": "General Studies I", "marks": 250},
                                {"name": "General Studies II", "marks": 250},
                                {"name": "General Studies III", "marks": 250},
                                {"name": "General Studies IV (Ethics)", "marks": 250},
                                {"name": "Optional Subject Paper I", "marks": 250},
                                {"name": "Optional Subject Paper II", "marks": 250}
                            ],
                            "total_marks": 1750,
                            "exam_mode": "Offline"
                        },
                        {
                            "phase": "Interview",
                            "total_marks": 275,
                            "qualifying": False
                        }
                    ],
                    "syllabus_link": "https://upsc.gov.in/syllabus/cse.pdf",
                    "exam_language": ["Hindi", "English"],
                    "total_phases": 3
                },
                "salary": {
                    "pay_scale": "₹56,100 - ₹2,50,000",
                    "pay_level": "Level-10 to Level-17",
                    "initial_salary": 56100,
                    "max_salary": 250000,
                    "allowances": ["DA", "HRA", "TA", "Special Allowances"],
                    "other_benefits": "Government accommodation, Vehicle, Medical, Pension, LTC"
                },
                "selection_process": [
                    {"phase": 1, "name": "Preliminary Examination (Objective)", "qualifying": True},
                    {"phase": 2, "name": "Mains Examination (Descriptive)", "qualifying": False},
                    {"phase": 3, "name": "Personality Test (Interview)", "qualifying": False},
                    {"phase": 4, "name": "Document Verification", "qualifying": True},
                    {"phase": 5, "name": "Medical Examination", "qualifying": True}
                ],
                "status": "active",
                "is_featured": True,
                "is_urgent": True,
                "priority": 10
            },
            
            # Job 4: IBPS Bank PO
            {
                "job_title": "IBPS PO (Probationary Officer) Recruitment 2026",
                "slug": "ibps-po-recruitment-2026",
                "organization": "Institute of Banking Personnel Selection",
                "department": "Banking",
                "post_code": "IBPS-PO-2026",
                "job_type": "latest_job",
                "employment_type": "permanent",
                "qualification_level": "graduation",
                "total_vacancies": 4455,
                "vacancy_breakdown": {
                    "by_category": {
                        "UR": 2228,
                        "OBC": 1201,
                        "SC": 669,
                        "ST": 334,
                        "EWS": 446
                    },
                    "by_post": [
                        {
                            "post_name": "Probationary Officer",
                            "post_code": "PO-01",
                            "total": 4455,
                            "qualification": "Graduation (60% for Gen/OBC, 55% for SC/ST/PWD)",
                            "age_limit": "20-30",
                            "pay_scale": "₹23,700 - ₹42,020"
                        }
                    ],
                    "by_bank": [
                        {"bank": "Bank of Baroda", "vacancies": 350},
                        {"bank": "Canara Bank", "vacancies": 450},
                        {"bank": "Indian Bank", "vacancies": 350},
                        {"bank": "Punjab National Bank", "vacancies": 550},
                        {"bank": "Union Bank of India", "vacancies": 450},
                        {"bank": "Bank of India", "vacancies": 400},
                        {"bank": "Central Bank of India", "vacancies": 350},
                        {"bank": "Indian Overseas Bank", "vacancies": 300},
                        {"bank": "UCO Bank", "vacancies": 255},
                        {"bank": "Bank of Maharashtra", "vacancies": 250},
                        {"bank": "Punjab & Sind Bank", "vacancies": 150},
                        {"bank": "Other Banks", "vacancies": 850}
                    ]
                },
                "description": "<h2>IBPS PO Recruitment 2026</h2><p>Institute of Banking Personnel Selection (IBPS) has released notification for recruitment of 4,455 Probationary Officers (PO) in 11 participating public sector banks. Graduates with 60% marks can apply.</p><p>After selection, candidates will undergo 2 years of training and will be appointed as Assistant Manager in participating banks.</p>",
                "short_description": "IBPS PO 2026 notification released for 4,455 posts in 11 PSU banks. Graduate with 60% can apply. Age 20-30.",
                "eligibility": {
                    "min_qualification": "graduation",
                    "required_stream": None,
                    "qualification_details": "Bachelor's Degree in any discipline with minimum 60% (55% for SC/ST/PWD) from recognized university",
                    "age_limit": {
                        "min": 20,
                        "max": 30,
                        "cutoff_date": "2026-07-01",
                        "relaxation": {
                            "OBC": 3,
                            "SC": 5,
                            "ST": 5,
                            "PWD": 10,
                            "Ex_Serviceman": 5
                        },
                        "is_post_wise": False
                    },
                    "medical_standards": {
                        "vision": "Normal vision",
                        "other": "Should be physically and mentally fit for banking duties"
                    }
                },
                "application_details": {
                    "application_mode": "Online",
                    "application_link": "https://ibpsonline.ibps.in",
                    "official_website": "https://ibps.in",
                    "notification_pdf": "https://ibps.in/CWE-PO-XII-notification.pdf",
                    "application_fee": {
                        "General": 850,
                        "OBC": 850,
                        "EWS": 850,
                        "SC": 175,
                        "ST": 175,
                        "PWD": 175
                    },
                    "fee_payment_mode": "Online (Debit Card, Credit Card, Net Banking, UPI)",
                    "important_links": [
                        {"type": "apply_online", "text": "Apply Online", "url": "https://ibpsonline.ibps.in"},
                        {"type": "download_notification", "text": "Official Notification", "url": "https://ibps.in/CWE-PO-XII-notification.pdf"},
                        {"type": "syllabus", "text": "Exam Syllabus", "url": "https://ibps.in/syllabus-po.pdf"}
                    ]
                },
                "important_dates": {
                    "notification_date": "2026-07-01",
                    "application_start": "2026-07-08",
                    "application_end": "2026-07-28",
                    "prelims_admit_card": "2026-09-01",
                    "prelims_exam": "2026-09-20",
                    "prelims_result": "2026-10-15",
                    "mains_admit_card": "2026-11-01",
                    "mains_exam": "2026-11-21",
                    "mains_result": "2027-01-10",
                    "interview_call_letter": "2027-02-01",
                    "interview_dates": "2027-02-15",
                    "final_result": "2027-03-30"
                },
                "exam_details": {
                    "exam_pattern": [
                        {
                            "phase": "Preliminary Examination",
                            "subjects": [
                                {"name": "English Language", "questions": 30, "marks": 30},
                                {"name": "Quantitative Aptitude", "questions": 35, "marks": 35},
                                {"name": "Reasoning Ability", "questions": 35, "marks": 35}
                            ],
                            "total_marks": 100,
                            "duration_minutes": 60,
                            "negative_marking": 0.25,
                            "exam_mode": "Online",
                            "qualifying": True
                        },
                        {
                            "phase": "Mains Examination",
                            "subjects": [
                                {"name": "Reasoning & Computer Aptitude", "questions": 45, "marks": 60},
                                {"name": "English Language", "questions": 35, "marks": 40},
                                {"name": "Data Analysis & Interpretation", "questions": 35, "marks": 60},
                                {"name": "General/Economy/Banking Awareness", "questions": 40, "marks": 40},
                                {"name": "English (Letter Writing & Essay)", "questions": 2, "marks": 25}
                            ],
                            "total_marks": 225,
                            "duration_minutes": 180,
                            "negative_marking": 0.25,
                            "exam_mode": "Online"
                        },
                        {
                            "phase": "Interview",
                            "total_marks": 100,
                            "qualifying": False
                        }
                    ],
                    "syllabus_link": "https://ibps.in/syllabus-po.pdf",
                    "exam_language": ["Hindi", "English"],
                    "total_phases": 3
                },
                "salary": {
                    "pay_scale": "₹23,700 - ₹42,020",
                    "pay_level": "Scale-I (JMGS-I)",
                    "initial_salary": 57800,
                    "max_salary": 66000,
                    "allowances": ["DA", "HRA", "CCA", "Special Allowance"],
                    "other_benefits": "Medical, LTC, Newspaper Allowance, Performance Linked Incentive, Pension"
                },
                "selection_process": [
                    {"phase": 1, "name": "Preliminary Examination", "qualifying": True},
                    {"phase": 2, "name": "Mains Examination", "qualifying": False},
                    {"phase": 3, "name": "Personal Interview", "qualifying": False},
                    {"phase": 4, "name": "Document Verification", "qualifying": True},
                    {"phase": 5, "name": "Medical Examination", "qualifying": True}
                ],
                "documents_required": [
                    {"name": "10th Certificate", "mandatory": True, "format": "PDF", "max_size_kb": 500},
                    {"name": "12th Certificate", "mandatory": True, "format": "PDF", "max_size_kb": 500},
                    {"name": "Graduation Certificate", "mandatory": True, "format": "PDF", "max_size_kb": 500},
                    {"name": "Graduation Marksheets", "mandatory": True, "format": "PDF", "max_size_kb": 1000},
                    {"name": "Category Certificate", "mandatory": False, "format": "PDF", "max_size_kb": 300},
                    {"name": "Photo", "mandatory": True, "format": "JPG", "max_size_kb": 100},
                    {"name": "Signature", "mandatory": True, "format": "JPG", "max_size_kb": 50}
                ],
                "status": "active",
                "is_featured": True,
                "is_trending": True,
                "priority": 8
            },
            
            # Job 5: CTET (Central Teacher Eligibility Test)
            {
                "job_title": "CTET (Central Teacher Eligibility Test) July 2026",
                "slug": "ctet-july-2026",
                "organization": "Central Board of Secondary Education",
                "department": "CBSE",
                "post_code": "CTET-JUL-2026",
                "job_type": "latest_job",
                "employment_type": "eligibility_test",
                "qualification_level": "12th",
                "total_vacancies": 0,
                "vacancy_breakdown": {
                    "by_category": {
                        "note": "CTET is an eligibility test, not a recruitment. No fixed vacancies."
                    },
                    "by_post": [
                        {
                            "post_name": "Paper I - Primary Teacher (Class I-V)",
                            "post_code": "PAPER-1",
                            "total": 0,
                            "qualification": "12th + 2 Year Diploma in Elementary Education",
                            "age_limit": "18-No Upper Limit",
                            "pay_scale": "Varies by School/State"
                        },
                        {
                            "post_name": "Paper II - Upper Primary Teacher (Class VI-VIII)",
                            "post_code": "PAPER-2",
                            "total": 0,
                            "qualification": "Graduation + B.Ed./Diploma in Elementary Education",
                            "age_limit": "18-No Upper Limit",
                            "pay_scale": "Varies by School/State"
                        }
                    ]
                },
                "description": "<h2>CTET July 2026 Examination</h2><p>Central Board of Secondary Education (CBSE) conducts CTET (Central Teacher Eligibility Test) twice a year for candidates aspiring to become teachers in classes I to VIII in Central Government Schools (KVS, NVS, Central Tibetan Schools, etc.)</p><p>CTET certificate is valid for lifetime (no expiry). Candidates can appear in CTET as many times as they want to improve their score.</p>",
                "short_description": "CTET July 2026 notification. Teacher eligibility test for Class I-VIII. 12th+D.El.Ed or Graduation+B.Ed required.",
                "eligibility": {
                    "min_qualification": "12th",
                    "required_stream": None,
                    "qualification_details": "Paper I: 12th + 2-Year Diploma in Elementary Education OR B.El.Ed OR 4-Year integrated B.A.Ed/B.Sc.Ed\nPaper II: Graduation + B.Ed OR Graduation + 2-Year Diploma in Elementary Education",
                    "age_limit": {
                        "min": 18,
                        "max": None,
                        "note": "No upper age limit",
                        "cutoff_date": None
                    }
                },
                "application_details": {
                    "application_mode": "Online",
                    "application_link": "https://ctet.nic.in",
                    "official_website": "https://ctet.nic.in",
                    "notification_pdf": "https://ctet.nic.in/webinfo/file/pdffiles/Notification-CTET-JUL-2026.pdf",
                    "application_fee": {
                        "Paper-I-Only": 1000,
                        "Paper-II-Only": 1000,
                        "Paper-I-and-II-Both": 1200,
                        "SC-Paper-I-Only": 500,
                        "SC-Paper-II-Only": 500,
                        "SC-Both-Papers": 600,
                        "ST-Paper-I-Only": 500,
                        "ST-Paper-II-Only": 500,
                        "ST-Both-Papers": 600
                    },
                    "fee_payment_mode": "Online (Debit/Credit Card, Net Banking, UPI, E-Wallet)",
                    "important_links": [
                        {"type": "apply_online", "text": "Apply Online", "url": "https://ctet.nic.in"},
                        {"type": "download_notification", "text": "Download Notification", "url": "https://ctet.nic.in/notification.pdf"},
                        {"type": "syllabus", "text": "Exam Syllabus", "url": "https://ctet.nic.in/syllabus.pdf"},
                        {"type": "previous_papers", "text": "Previous Papers", "url": "https://ctet.nic.in/previous_papers.php"}
                    ]
                },
                "important_dates": {
                    "notification_date": "2026-03-01",
                    "application_start": "2026-03-10",
                    "application_end": "2026-04-10",
                    "correction_start": "2026-04-15",
                    "correction_end": "2026-04-20",
                    "admit_card_release": "2026-06-25",
                    "exam_date": "2026-07-20",
                    "answer_key_release": "2026-07-28",
                    "result_date": "2026-08-30"
                },
                "exam_details": {
                    "exam_pattern": [
                        {
                            "phase": "Paper I (Primary Level: Class I-V)",
                            "subjects": [
                                {"name": "Child Development & Pedagogy", "questions": 30, "marks": 30},
                                {"name": "Language I (Compulsory)", "questions": 30, "marks": 30},
                                {"name": "Language II (Compulsory)", "questions": 30, "marks": 30},
                                {"name": "Mathematics", "questions": 30, "marks": 30},
                                {"name": "Environmental Studies", "questions": 30, "marks": 30}
                            ],
                            "total_marks": 150,
                            "duration_minutes": 150,
                            "negative_marking": 0,
                            "exam_mode": "Online (CBT)",
                            "qualifying_marks": {
                                "General": 90,
                                "OBC": 90,
                                "SC": 82.5,
                                "ST": 82.5
                            }
                        },
                        {
                            "phase": "Paper II (Upper Primary Level: Class VI-VIII)",
                            "subjects": [
                                {"name": "Child Development & Pedagogy", "questions": 30, "marks": 30},
                                {"name": "Language I (Compulsory)", "questions": 30, "marks": 30},
                                {"name": "Language II (Compulsory)", "questions": 30, "marks": 30},
                                {"name": "Mathematics & Science OR Social Studies", "questions": 60, "marks": 60}
                            ],
                            "total_marks": 150,
                            "duration_minutes": 150,
                            "negative_marking": 0,
                            "exam_mode": "Online (CBT)",
                            "qualifying_marks": {
                                "General": 90,
                                "OBC": 90,
                                "SC": 82.5,
                                "ST": 82.5
                            }
                        }
                    ],
                    "syllabus_link": "https://ctet.nic.in/syllabus.pdf",
                    "exam_language": ["Hindi", "English", "Urdu", "Assamese", "Bengali", "Garo", "Gujarati", "Kannada", "Khasi", "Malayalam", "Manipuri", "Marathi", "Mizo", "Nepali", "Oriya", "Punjabi", "Tamil", "Telugu", "Tibetan"],
                    "total_phases": 1
                },
                "salary": {
                    "pay_scale": "Varies by School/State",
                    "note": "KVS PGT: ₹44,900 - ₹1,42,400, TGT: ₹44,900 - ₹1,42,400, PRT: ₹35,400 - ₹1,12,400"
                },
                "selection_process": [
                    {"phase": 1, "name": "CTET Examination", "qualifying": False},
                    {"phase": 2, "name": "Note", "qualifying": True, "description": "After qualifying CTET, candidates need to apply separately for teaching jobs in KVS, NVS, or other schools"}
                ],
                "documents_required": [
                    {"name": "10th Certificate", "mandatory": True, "format": "PDF", "max_size_kb": 500},
                    {"name": "12th Certificate", "mandatory": True, "format": "PDF", "max_size_kb": 500},
                    {"name": "Graduation Certificate", "mandatory": True, "format": "PDF", "max_size_kb": 500},
                    {"name": "B.Ed/D.El.Ed Certificate", "mandatory": True, "format": "PDF", "max_size_kb": 500},
                    {"name": "Category Certificate", "mandatory": False, "format": "PDF", "max_size_kb": 300},
                    {"name": "Photo", "mandatory": True, "format": "JPG", "max_size_kb": 100},
                    {"name": "Signature", "mandatory": True, "format": "JPG", "max_size_kb": 50}
                ],
                "status": "active",
                "is_featured": True,
                "priority": 7
            }
        ]
        
        # Create jobs in database
        print("Creating 5 sample job postings...")
        for idx, job_data in enumerate(jobs_data, 1):
            try:
                # Check if job already exists
                existing_job = JobVacancy.query.filter_by(slug=job_data['slug']).first()
                if existing_job:
                    print(f"✓ Job {idx} already exists: {job_data['job_title']}")
                    continue
                
                # Extract dates from important_dates dict
                dates = job_data.pop('important_dates', {})
                
                # Create new job with extracted dates
                job = JobVacancy(
                    job_title=job_data['job_title'],
                    slug=job_data['slug'],
                    organization=job_data['organization'],
                    department=job_data['department'],
                    post_code=job_data['post_code'],
                    job_type=job_data['job_type'],
                    employment_type=job_data['employment_type'],
                    qualification_level=job_data['qualification_level'],
                    total_vacancies=job_data['total_vacancies'],
                    vacancy_breakdown=job_data['vacancy_breakdown'],
                    description=job_data['description'],
                    short_description=job_data['short_description'],
                    eligibility=job_data['eligibility'],
                    application_details=job_data['application_details'],
                    # Date fields from important_dates
                    notification_date=parse_date(dates.get('notification_date')),
                    application_start=parse_date(dates.get('application_start')),
                    application_end=parse_date(dates.get('application_end')),
                    last_date_fee=parse_date(dates.get('last_date_fee_payment')),
                    admit_card_release=parse_date(dates.get('admit_card_release')),
                    exam_city_release=parse_date(dates.get('exam_city_release')),
                    exam_start=parse_date(dates.get('exam_start') or dates.get('prelims_exam') or dates.get('exam_date')),
                    exam_end=parse_date(dates.get('exam_end')),
                    correction_start=parse_date(dates.get('correction_start')),
                    correction_end=parse_date(dates.get('correction_end')),
                    answer_key_release=parse_date(dates.get('answer_key_release')),
                    result_date=parse_date(dates.get('result_date') or dates.get('final_result')),
                    exam_details=job_data.get('exam_details', {}),
                    salary_initial=job_data.get('salary', {}).get('initial_salary'),
                    salary_max=job_data.get('salary', {}).get('max_salary'),
                    salary=job_data.get('salary', {}),
                    selection_process=job_data.get('selection_process', []),
                    documents_required=job_data.get('documents_required', []),
                    status=job_data['status'],
                    is_featured=job_data.get('is_featured', False),
                    is_urgent=job_data.get('is_urgent', False),
                    is_trending=job_data.get('is_trending', False),
                    priority=job_data['priority'],
                    published_at=datetime.utcnow() if job_data['status'] == 'active' else None
                )
                
                db.session.add(job)
                db.session.commit()
                print(f"✓ Created Job {idx}: {job_data['job_title']}")
                
            except Exception as e:
                print(f"✗ Error creating Job {idx}: {str(e)}")
                import traceback
                traceback.print_exc()
                db.session.rollback()
        
        print("\n✅ Seed data creation completed!")
        print(f"Total jobs in database: {JobVacancy.query.count()}")


if __name__ == "__main__":
    create_seed_jobs()
