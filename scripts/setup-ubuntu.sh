#!/usr/bin/env bash
# =============================================================================
# OpenLI DMM - AWS Ubuntu 24.04 Server Setup
# =============================================================================
# Installs Docker, Docker Compose, and system prerequisites.
# Run as root or with sudo: sudo bash scripts/setup-ubuntu.sh
# =============================================================================

set -euo pipefail

echo "============================================"
echo "  OpenLI DMM - Ubuntu 24.04 Server Setup"
echo "============================================"

# --- System update ---
echo "[1/5] Updating system packages..."
apt-get update -y && apt-get upgrade -y

# --- Install prerequisites ---
echo "[2/5] Installing prerequisites..."
apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    jq \
    unzip

# --- Install Docker ---
echo "[3/5] Installing Docker Engine..."
if command -v docker &> /dev/null; then
    echo "  Docker already installed: $(docker --version)"
else
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    echo "  Docker installed: $(docker --version)"
fi

# --- Configure Docker ---
echo "[4/5] Configuring Docker..."
systemctl enable docker
systemctl start docker

# Add current user to docker group (if not root)
if [ -n "${SUDO_USER:-}" ]; then
    usermod -aG docker "$SUDO_USER"
    echo "  Added user '$SUDO_USER' to docker group"
fi

# --- Configure firewall ---
echo "[5/5] Configuring firewall..."
if command -v ufw &> /dev/null; then
    ufw allow 80/tcp   # HTTP (nginx)
    ufw allow 443/tcp  # HTTPS (nginx, future)
    ufw allow 22/tcp   # SSH
    echo "  Firewall rules configured (80, 443, 22)"
fi

echo ""
echo "============================================"
echo "  Setup complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Log out and back in (for docker group membership)"
echo "  2. Clone or copy the project to /opt/dmm/"
echo "  3. cd /opt/dmm && cp .env.example .env"
echo "  4. Edit .env with production values"
echo "  5. Run: bash scripts/deploy.sh"
echo ""
