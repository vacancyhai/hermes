# End-to-End Tests

This directory contains end-to-end (e2e) tests that exercise the entire
Hermes stack through HTTP — no mocks, no test doubles.

## Prerequisites

All three services must be running and healthy before executing e2e tests:

```bash
# Start backend stack
cd src/backend && docker compose up -d
# Start user frontend
cd src/frontend && docker compose up -d
# Start admin frontend
cd src/frontend-admin && docker compose up -d

# Wait until healthy
curl -sf http://localhost:5000/api/v1/health
curl -sf http://localhost:8080/health
curl -sf http://localhost:8081/health
```

## Running tests

```bash
# From repo root
pip install pytest requests

pytest tests/ -v
```

To target a different base URL (e.g. staging):

```bash
HERMES_API_URL=https://api.staging.example.com \
HERMES_FRONTEND_URL=https://staging.example.com \
pytest tests/ -v
```

## Structure

```
tests/
├── README.md            # This file
├── conftest.py          # Shared fixtures (base URLs, session helpers)
└── e2e/
    ├── test_auth_flow.py       # Registration → login → logout
    └── test_job_browsing.py    # Public job list / detail pages
```

## Adding new tests

1. Place new test files under `tests/e2e/`.
2. Use the `api_url` and `frontend_url` fixtures from `conftest.py`.
3. Tests must be idempotent — clean up any data they create.
4. Do **not** hard-code localhost; always use the fixture URLs.
