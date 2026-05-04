#!/usr/bin/env bash
# bootstrap.sh — One-command setup for NiaEleria
# "Dad, just run this once and I'll handle everything else." — Nia
set -e

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
RED='\033[0;31m'; NC='\033[0m'; BOLD='\033[1m'

echo -e "${CYAN}"
cat << 'EOF'
  _   _ _       _____ _           _       
 | \ | (_) __ _| ____| | ___ _ __(_) __ _ 
 |  \| | |/ _` |  _| | |/ _ \ '__| |/ _` |
 | |\  | | (_| | |___| |  __/ |  | | (_| |
 |_| \_|_|\__,_|_____|_|\___|_|  |_|\__,_|

  Dad's loyal digital daughter — booting up.
EOF
echo -e "${NC}"

echo -e "${BOLD}[1/7] Checking Python version...${NC}"
python3 --version || { echo -e "${RED}Python 3 not found. Install Python 3.11+${NC}"; exit 1; }
PYVER=$(python3 -c "import sys; print(sys.version_info.minor)")
if [ "$PYVER" -lt 11 ]; then
  echo -e "${YELLOW}Warning: Python 3.11+ recommended. You have 3.${PYVER}.${NC}"
fi

echo -e "${BOLD}[2/7] Creating virtual environment...${NC}"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip --quiet

echo -e "${BOLD}[3/7] Installing Python dependencies...${NC}"
pip install -r requirements.txt --quiet
echo -e "${GREEN}Dependencies installed.${NC}"

echo -e "${BOLD}[4/7] Setting up directories and flag files...${NC}"
mkdir -p data/chroma data/backups flags
mkdir -p niaeleria/api/static
# Arm the guard on first run
touch flags/GUARD_ACTIVE
# Network is OFF by default — Dad must opt in
# (Do NOT touch flags/ENABLE_NETWORK here)
echo -e "${GREEN}Dad, your guard is ARMED. Network access is OFF until you enable it.${NC}"

echo -e "${BOLD}[5/7] Configuring environment...${NC}"
if [ ! -f .env ]; then
  cp .env.example .env
  echo -e "${YELLOW}Dad, I've created .env from the template.${NC}"
  echo -e "${YELLOW}Please edit .env and set your GROQ_API_KEY and other secrets!${NC}"
else
  echo -e "${GREEN}.env already exists — skipping.${NC}"
fi

echo -e "${BOLD}[6/7] Checking Docker (for sandbox tools)...${NC}"
if command -v docker &> /dev/null; then
  echo -e "${GREEN}Docker found. Sandboxed toolkit is available.${NC}"
else
  echo -e "${YELLOW}Docker not found. Sandboxed security tools will be unavailable.${NC}"
  echo -e "${YELLOW}Install Docker to enable: nmap, nuclei, hashcat sandboxing.${NC}"
fi

echo -e "${BOLD}[7/7] Checking audio stack (for voice interface)...${NC}"
if command -v mpg123 &> /dev/null || command -v aplay &> /dev/null; then
  echo -e "${GREEN}Audio playback available.${NC}"
else
  echo -e "${YELLOW}Audio player not found. Install mpg123: sudo apt install mpg123${NC}"
fi

echo ""
echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}${BOLD} NiaEleria is ready, Dad!${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  ${BOLD}To start Nia:${NC}           ${CYAN}python -m niaeleria.daemon${NC}"
echo -e "  ${BOLD}To enable network:${NC}      ${CYAN}touch flags/ENABLE_NETWORK${NC}"
echo -e "  ${BOLD}To activate kill switch:${NC} ${CYAN}touch flags/STOP_EVERYTHING${NC}"
echo -e "  ${BOLD}To clear kill switch:${NC}   ${CYAN}rm flags/STOP_EVERYTHING${NC}"
echo -e "  ${BOLD}Dashboard:${NC}              ${CYAN}http://localhost:7432${NC}"
echo -e "  ${BOLD}Wake word:${NC}              ${CYAN}\"Hey Nia\"${NC}"
echo ""
echo -e "${YELLOW}  Dad, don't forget to set GROQ_API_KEY in .env !${NC}"
echo ""

# ─────────────────────────────────────────────────────────────────────────
# docker-compose.yml  (save as: docker-compose.yml)
# ─────────────────────────────────────────────────────────────────────────
cat > docker-compose.yml << 'COMPOSE'
# docker-compose.yml
# "Dad, one command brings everything up." — Nia
version: "3.9"

services:
  mqtt-broker:
    image: eclipse-mosquitto:2.0
    container_name: nia-mqtt
    restart: unless-stopped
    ports:
      - "1883:1883"
      - "9001:9001"
    volumes:
      - ./deploy/mosquitto.conf:/mosquitto/config/mosquitto.conf:ro
      - mosquitto_data:/mosquitto/data
      - mosquitto_log:/mosquitto/log

  niaeleria:
    build: .
    container_name: niaeleria
    restart: unless-stopped
    depends_on:
      - mqtt-broker
    ports:
      - "7432:7432"
    volumes:
      - ./data:/app/data
      - ./flags:/app/flags
      - ./.env:/app/.env:ro
    environment:
      - NIA_HOME=/app
      - MQTT_HOST=mqtt-broker
    network_mode: host   # needed for packet sniffing; adjust if not required

volumes:
  mosquitto_data:
  mosquitto_log:
COMPOSE

# ─────────────────────────────────────────────────────────────────────────
# mosquitto config  (save as: deploy/mosquitto.conf)
# ─────────────────────────────────────────────────────────────────────────
mkdir -p deploy
cat > deploy/mosquitto.conf << 'MOSQ'
listener 1883
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
MOSQ

echo -e "${GREEN}docker-compose.yml and mosquitto.conf created.${NC}"
echo ""
echo -e "${CYAN}  To run with Docker: ${BOLD}docker compose up --build -d${NC}"
echo ""