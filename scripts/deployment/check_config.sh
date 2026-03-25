#!/usr/bin/env bash
# check_config.sh — Validate Hermes environment configuration
# Usage: ./check_config.sh [development|staging|production|all]
#
# Checks:
#   - Required vars are set and non-empty
#   - No unfilled placeholder values (<...>)
#   - No shell interpolation in .env values (${VAR} won't expand in .env)
#   - PgBouncer uses container port 5432 (not host port 6432)
#   - Production-specific secrets are not default/weak values
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

ENV_ARG="${1:-all}"
ERRORS=0
WARNINGS=0

# ─── Helpers ──────────────────────────────────────────────────────────────────

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

error()   { echo -e "  ${RED}✗ ERROR${NC}   $1"; ERRORS=$((ERRORS + 1)); }
warn()    { echo -e "  ${YELLOW}⚠ WARN${NC}    $1"; WARNINGS=$((WARNINGS + 1)); }
ok()      { echo -e "  ${GREEN}✓${NC}         $1"; }
section() { echo -e "\n${BOLD}${CYAN}── $1${NC}"; }

# Load an env file into an associative array
load_env() {
    local file="$1"
    declare -gA ENV_VARS=()
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip comments and blank lines
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// }" ]] && continue
        if [[ "$line" == *=* ]]; then
            local key="${line%%=*}"
            local val="${line#*=}"
            # Strip inline comments
            val="${val%%  #*}"
            ENV_VARS["$key"]="$val"
        fi
    done < "$file"
}

# Check a var is present and non-empty
check_required() {
    local key="$1"
    local val="${ENV_VARS[$key]:-}"
    if [[ -z "$val" ]]; then
        error "$key is missing or empty"
    else
        ok "$key is set"
    fi
}

# Check a var has no unfilled placeholder (<...>)
check_no_placeholder() {
    local key="$1"
    local val="${ENV_VARS[$key]:-}"
    if [[ "$val" == *"<"*">"* ]]; then
        error "$key still contains a placeholder value: $val"
    fi
}

# Check a var is set AND has no placeholder
check_filled() {
    local key="$1"
    local val="${ENV_VARS[$key]:-}"
    if [[ -z "$val" ]]; then
        error "$key is missing or empty"
    elif [[ "$val" == *"<"*">"* ]]; then
        error "$key still contains a placeholder: $val"
    else
        ok "$key is set"
    fi
}

# Warn if a var is empty (optional but recommended)
check_recommended() {
    local key="$1"
    local msg="${2:-}"
    local val="${ENV_VARS[$key]:-}"
    if [[ -z "$val" ]]; then
        warn "$key is empty${msg:+ — $msg}"
    else
        ok "$key is set"
    fi
}

# Check no ${VAR} interpolation in a value (doesn't expand in .env)
check_no_interpolation() {
    local key="$1"
    local val="${ENV_VARS[$key]:-}"
    if [[ "$val" == *'${'* ]]; then
        error "$key uses shell interpolation (\${...}) which does NOT expand in .env files — use a literal value"
    fi
}

# Check pgbouncer uses container port 5432 (not host-mapped 6432)
check_pgbouncer_port() {
    local key="${1:-DATABASE_URL}"
    local val="${ENV_VARS[$key]:-}"
    if [[ "$val" == *"@pgbouncer:6432"* ]]; then
        error "$key uses host port 6432 — inside Docker the container port is 5432 (change to @pgbouncer:5432)"
    elif [[ "$val" == *"@pgbouncer:5432"* ]]; then
        ok "$key pgbouncer port is correct (5432)"
    fi
}

# ─── Per-file checks ──────────────────────────────────────────────────────────

check_backend() {
    local env="$1"
    local file="$PROJECT_DIR/config/$env/.env.backend.$env"

    section "Backend — $env ($file)"

    if [[ ! -f "$file" ]]; then
        error "File not found: $file"
        return
    fi

    load_env "$file"

    # Core
    check_filled   "APP_ENV"
    check_filled   "SECRET_KEY"
    check_no_interpolation "SECRET_KEY"

    # Database
    check_filled   "DATABASE_URL"
    check_no_interpolation "DATABASE_URL"
    check_pgbouncer_port   "DATABASE_URL"
    check_filled   "POSTGRES_DB"
    check_filled   "POSTGRES_USER"
    check_filled   "POSTGRES_PASSWORD"
    check_no_interpolation "POSTGRES_PASSWORD"

    # Redis
    check_filled   "REDIS_URL"
    check_no_interpolation "REDIS_URL"
    check_no_interpolation "CELERY_BROKER_URL"
    check_no_interpolation "CELERY_RESULT_BACKEND"

    # JWT
    check_filled   "JWT_SECRET_KEY"
    check_no_interpolation "JWT_SECRET_KEY"

    # Mail
    check_filled   "MAIL_ENABLED"
    if [[ "${ENV_VARS[MAIL_ENABLED]:-}" == "true" || "${ENV_VARS[MAIL_ENABLED]:-}" == "True" ]]; then
        check_filled "MAIL_SERVER"
        check_no_placeholder "MAIL_SERVER"
    fi

    # Firebase
    check_filled   "FIREBASE_CREDENTIALS_PATH"
    check_no_placeholder "FIREBASE_CREDENTIALS_PATH"

    # SEO
    check_filled   "SITE_URL"
    check_no_placeholder "SITE_URL"
    check_filled   "FRONTEND_URL"
    check_no_placeholder "FRONTEND_URL"

    # PDF / AI
    check_filled   "PDF_UPLOAD_DIR"
    check_filled   "PDF_MAX_SIZE_MB"
    check_filled   "AI_MODEL"
    if [[ "$env" != "development" ]]; then
        check_recommended "ANTHROPIC_API_KEY" "PDF AI extraction will use fallback without this"
    fi

    # Notification delays
    check_filled   "NOTIFY_EMAIL_DELAY"
    check_filled   "NOTIFY_WHATSAPP_DELAY"
    check_filled   "NOTIFY_TELEGRAM_DELAY"

    # CORS
    check_filled   "CORS_ORIGINS"
    if [[ "$env" == "production" ]]; then
        local origins="${ENV_VARS[CORS_ORIGINS]:-}"
        if [[ "$origins" == *"localhost"* ]]; then
            warn "CORS_ORIGINS contains 'localhost' — remove for production"
        fi
    fi

    # Production-specific extra checks
    if [[ "$env" == "production" ]]; then
        local secret="${ENV_VARS[SECRET_KEY]:-}"
        local jwt="${ENV_VARS[JWT_SECRET_KEY]:-}"
        [[ "$secret" == *"change-me"* || "$secret" == *"dev-"* ]] && error "SECRET_KEY looks like a dev/default value"
        [[ "$jwt" == *"change-me"* || "$jwt" == *"dev-"* ]] && error "JWT_SECRET_KEY looks like a dev/default value"
        check_filled "REDIS_PASSWORD"
        check_filled "MAIL_USERNAME"
        check_filled "MAIL_PASSWORD"
        check_recommended "TELEGRAM_BOT_TOKEN" "Telegram notifications disabled without this"
        check_filled "FIREBASE_WEB_API_KEY"
    fi
}

check_frontend() {
    local env="$1"
    local file="$PROJECT_DIR/config/$env/.env.frontend.$env"

    section "User Frontend — $env ($file)"

    if [[ ! -f "$file" ]]; then
        error "File not found: $file"
        return
    fi

    load_env "$file"

    check_filled "BACKEND_API_URL"
    check_filled "SECRET_KEY"
    check_filled "FLASK_APP"
    check_filled "FLASK_ENV"
    check_filled "FIREBASE_WEB_API_KEY"
    check_filled "FIREBASE_AUTH_DOMAIN"
    check_filled "FIREBASE_PROJECT_ID"

    if [[ "$env" == "production" ]]; then
        local flask_debug="${ENV_VARS[FLASK_DEBUG]:-1}"
        [[ "$flask_debug" == "1" ]] && error "FLASK_DEBUG=1 must not be set in production"
    fi
}

check_frontend_admin() {
    local env="$1"
    local file="$PROJECT_DIR/config/$env/.env.frontend-admin.$env"

    section "Admin Frontend — $env ($file)"

    if [[ ! -f "$file" ]]; then
        error "File not found: $file"
        return
    fi

    load_env "$file"

    check_filled "BACKEND_API_URL"
    check_filled "SECRET_KEY"
    check_filled "FLASK_APP"
    check_filled "FLASK_ENV"

    if [[ "$env" == "production" ]]; then
        local flask_debug="${ENV_VARS[FLASK_DEBUG]:-1}"
        [[ "$flask_debug" == "1" ]] && error "FLASK_DEBUG=1 must not be set in production"
        local secret="${ENV_VARS[SECRET_KEY]:-}"
        [[ "$secret" == *"dev-"* || "$secret" == *"change-me"* ]] && error "SECRET_KEY looks like a dev value"
    fi
}

# ─── Runtime src/.env checks ─────────────────────────────────────────────────

check_runtime_envs() {
    for svc in backend frontend frontend-admin; do
        local file="$PROJECT_DIR/src/$svc/.env"
        section "Runtime: src/$svc/.env"
        if [[ ! -f "$file" ]]; then
            warn "File not found — run deploy_all.sh to copy from config/"
            continue
        fi
        ok "File exists: $file"

        load_env "$file"

        # Check runtime file matches expected APP_ENV
        local app_env="${ENV_VARS[APP_ENV]:-}"
        if [[ -z "$app_env" ]]; then
            # Frontend files don't have APP_ENV
            local flask_env="${ENV_VARS[FLASK_ENV]:-}"
            [[ -n "$flask_env" ]] && ok "FLASK_ENV=$flask_env"
        else
            ok "APP_ENV=$app_env"
            if [[ "$app_env" == "production" ]]; then
                local secret="${ENV_VARS[SECRET_KEY]:-}"
                [[ "$secret" == *"change-me"* || "$secret" == *"dev-"* ]] && \
                    error "Runtime SECRET_KEY is a dev/default value in production config!"
            fi
        fi
    done
}

# ─── Main ──────────────────────────────────────────────────────────────────────

ENVS=()
if [[ "$ENV_ARG" == "all" ]]; then
    ENVS=("development" "staging" "production")
else
    ENVS=("$ENV_ARG")
fi

echo -e "${BOLD}════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  Hermes Config Checker${NC}"
echo -e "${BOLD}════════════════════════════════════════════════${NC}"

for env in "${ENVS[@]}"; do
    check_backend       "$env"
    check_frontend      "$env"
    check_frontend_admin "$env"
done

check_runtime_envs

# ─── Summary ─────────────────────────────────────────────────────────────────

echo ""
echo -e "${BOLD}════════════════════════════════════════════════${NC}"
if [[ $ERRORS -gt 0 ]]; then
    echo -e "  ${RED}${BOLD}FAILED${NC} — $ERRORS error(s), $WARNINGS warning(s)"
    echo -e "${BOLD}════════════════════════════════════════════════${NC}"
    exit 1
elif [[ $WARNINGS -gt 0 ]]; then
    echo -e "  ${YELLOW}${BOLD}PASSED with warnings${NC} — 0 errors, $WARNINGS warning(s)"
    echo -e "${BOLD}════════════════════════════════════════════════${NC}"
    exit 0
else
    echo -e "  ${GREEN}${BOLD}ALL CHECKS PASSED${NC} — 0 errors, 0 warnings"
    echo -e "${BOLD}════════════════════════════════════════════════${NC}"
    exit 0
fi
