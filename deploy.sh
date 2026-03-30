#!/usr/bin/env bash
set -euo pipefail

# ============================================================
#  Slack Anomaly Agent — AWS Deployment Script
# ============================================================
#
#  Prerequisites:
#    1. AWS CLI configured     → aws configure
#    2. AWS SAM CLI installed   → brew install aws-sam-cli
#    3. Docker running          → (for sam build --use-container)
#
#  Usage:
#    First deploy (interactive):  ./deploy.sh --guided
#    Subsequent deploys:          ./deploy.sh
#    Destroy stack:               ./deploy.sh --destroy
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

STACK_NAME="slack-anomaly-agent"

log()   { echo -e "${GREEN}[✓]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✗]${NC} $*"; exit 1; }

# --- Check prerequisites ---
check_prereqs() {
    command -v aws >/dev/null 2>&1  || error "AWS CLI not found. Install: brew install awscli"
    command -v sam >/dev/null 2>&1  || error "AWS SAM CLI not found. Install: brew install aws-sam-cli"
    command -v docker >/dev/null 2>&1 || warn "Docker not found. sam build --use-container requires Docker."

    # Verify AWS credentials
    aws sts get-caller-identity >/dev/null 2>&1 || error "AWS credentials not configured. Run: aws configure"
    log "Prerequisites OK"
}

# --- Build ---
build() {
    log "Building Lambda package with SAM..."
    sam build --use-container
    log "Build complete"
}

# --- Deploy ---
deploy() {
    if [[ "${1:-}" == "--guided" ]]; then
        log "Starting guided deployment..."
        sam deploy --guided
    else
        log "Deploying stack '${STACK_NAME}'..."
        sam deploy
    fi
    log "Deployment complete!"

    echo ""
    log "Stack outputs:"
    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --query "Stacks[0].Outputs" \
        --output table 2>/dev/null || true
}

# --- Destroy ---
destroy() {
    warn "This will DELETE the stack '${STACK_NAME}' and all its resources."
    read -rp "Are you sure? (y/N) " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        sam delete --stack-name "$STACK_NAME" --no-prompts
        log "Stack deleted."
    else
        warn "Aborted."
    fi
}

# --- Test locally ---
test_local() {
    log "Invoking function locally..."
    sam local invoke SlackAnomalyAgentFunction \
        --event events/test_event.json \
        --env-vars .env.json
}

# --- Tail logs ---
logs() {
    log "Tailing logs for ${STACK_NAME}..."
    sam logs --stack-name "$STACK_NAME" --tail
}

# --- Main ---
check_prereqs

case "${1:-}" in
    --guided)   build && deploy --guided ;;
    --destroy)  destroy ;;
    --test)     build && test_local ;;
    --logs)     logs ;;
    *)          build && deploy ;;
esac
