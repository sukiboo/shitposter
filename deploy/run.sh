#!/usr/bin/env bash
set -euo pipefail

# Load deploy config from .env
set -a
set -f
source "$(dirname "$0")/../.env"
set +f
set +a

SERVER="$SERVER_USER@$SERVER_HOST"

# First-time setup or update
ssh "$SERVER" bash -s "$REPO_URL" "$SERVER_PATH" <<'REMOTE'
set -euo pipefail
REPO_URL="$1"
APP_DIR="$2"

# Install uv if missing
if ! command -v uv >/dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source "$HOME/.local/bin/env"
fi

# Clone or pull
if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR" && git pull --ff-only
else
    mkdir -p "$(dirname "$APP_DIR")"
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi

uv sync --no-dev
mkdir -p ~/.config/systemd/user
loginctl enable-linger "$(whoami)"
REMOTE

# Copy .env to server
scp .env "$SERVER:$SERVER_PATH/.env"

# Generate and install systemd units with substituted values
for unit in shitposter.service shitposter.timer; do
    sed -e "s|SERVER_PATH|$SERVER_PATH|g" \
        -e "s|STEPS_CONFIG|$STEPS_CONFIG|g" \
        -e "s|RUN_SCHEDULE|$RUN_SCHEDULE|g" \
        -e "s|RUN_TIMEZONE|$RUN_TIMEZONE|g" \
        "deploy/$unit" | ssh "$SERVER" "cat > ~/.config/systemd/user/$unit"
done

ssh "$SERVER" "systemctl --user daemon-reload && systemctl --user enable --now shitposter.timer"

echo -e "\n✅ Deploy successful, checking status:"
ssh "$SERVER" "systemctl --user status shitposter.timer"
