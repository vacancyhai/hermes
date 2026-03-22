"""AI-powered structured data extraction from government job notification text.

Uses Anthropic Claude API to extract structured job fields from raw PDF text.
Graceful no-op if ANTHROPIC_API_KEY is not set.
"""

import json
import logging

from app.config import settings

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """You are a data extraction assistant for Indian government job notifications.

Extract the following structured fields from the given text. Return ONLY valid JSON with these fields:

{
  "job_title": "string — official post/exam name",
  "organization": "string — issuing organization (SSC, UPSC, Railway, etc.)",
  "department": "string or null — specific department if mentioned",
  "qualification_level": "one of: 10th, 12th, diploma, graduate, postgraduate, phd, or null",
  "total_vacancies": "integer or null",
  "description": "string — brief summary of the notification (2-3 sentences)",
  "short_description": "string — one-line summary",
  "application_start": "YYYY-MM-DD or null",
  "application_end": "YYYY-MM-DD or null",
  "notification_date": "YYYY-MM-DD or null",
  "exam_start": "YYYY-MM-DD or null",
  "fee_general": "integer (INR) or null",
  "fee_obc": "integer (INR) or null",
  "fee_sc_st": "integer (INR) or null",
  "fee_ews": "integer (INR) or null",
  "fee_female": "integer (INR) or null",
  "salary_initial": "integer (annual INR) or null",
  "salary_max": "integer (annual INR) or null",
  "eligibility": {"age_min": "int or null", "age_max": "int or null", "states": ["list of eligible states or empty"]},
  "source_url": "string URL if found in text, or null",
  "selection_process": ["list of selection stages, e.g. Written Exam, Interview"]
}

Rules:
- Extract dates in YYYY-MM-DD format. Convert Indian date formats (DD/MM/YYYY, DD.MM.YYYY).
- Fee amounts in INR (integers only, no decimals).
- If a field is not found, use null (not empty string).
- For salary, convert monthly to annual (multiply by 12) if needed.
- Return ONLY the JSON object, no explanation or markdown."""


def extract_job_data(pdf_text: str) -> dict | None:
    """Send PDF text to Claude API for structured extraction.

    Returns extracted dict or None if API is unavailable.
    """
    if not settings.ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not set — skipping AI extraction")
        return None

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        message = client.messages.create(
            model=settings.AI_MODEL,
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": f"{EXTRACTION_PROMPT}\n\n---\n\nNOTIFICATION TEXT:\n\n{pdf_text[:8000]}",
                }
            ],
        )

        # Extract JSON from response
        response_text = message.content[0].text.strip()

        # Handle potential markdown code blocks
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        return json.loads(response_text)

    except json.JSONDecodeError as e:
        logger.error("AI extraction: invalid JSON in response: %s", e)
        return None
    except Exception as e:
        logger.error("AI extraction failed (%s): %s", type(e).__name__, e)
        return None
