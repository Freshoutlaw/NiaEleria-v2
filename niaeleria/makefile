# ═══════════════════════════════════════════════════════════════════
# Makefile — NiaEleria convenience commands for Dad
# "Dad, just type 'make' and I'll tell you what's available." — Nia
# ═══════════════════════════════════════════════════════════════════

.PHONY: help setup run stop schema test lint clean docker-up docker-down \
        guard-on guard-off net-on net-off kill resume tray logs

VENV     := .venv
PYTHON   := $(VENV)/bin/python
PIP      := $(VENV)/bin/pip
FLAGS    := flags

# ── Default target ─────────────────────────────────────────────────
help:
	@echo ""
	@echo "  NiaEleria — Dad's AI"
	@echo ""
	@echo "  make setup        Bootstrap: install deps, create dirs, copy .env"
	@echo "  make run          Start NiaEleria (foreground)"
	@echo "  make stop         Activate kill-switch"
	@echo "  make resume       Clear kill-switch"
	@echo "  make schema       Print Supabase schema SQL"
	@echo ""
	@echo "  make net-on       Enable external network access"
	@echo "  make net-off      Gate external network"
	@echo "  make guard-on     Arm cyber guard"
	@echo "  make guard-off    Disarm cyber guard"
	@echo ""
	@echo "  make test         Run test suite"
	@echo "  make lint         Run ruff linter"
	@echo "  make logs         Tail runtime log"
	@echo ""
	@echo "  make docker-up    Start with Docker Compose"
	@echo "  make docker-down  Stop Docker stack"
	@echo "  make clean        Remove __pycache__, .pytest_cache etc."
	@echo ""

# ── Setup ──────────────────────────────────────────────────────────
setup:
	@chmod +x bootstrap.sh && ./bootstrap.sh

$(VENV):
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip --quiet
	$(PIP) install -r requirements.txt --quiet
	@echo "Virtualenv ready, Dad."

# ── Run ────────────────────────────────────────────────────────────
run: $(VENV)
	@mkdir -p $(FLAGS) data/backups data/chroma niaeleria/api/static
	$(PYTHON) -m niaeleria.daemon

# ── Flag controls ──────────────────────────────────────────────────
stop:
	@touch $(FLAGS)/STOP_EVERYTHING
	@echo "Kill-switch ACTIVATED, Dad. NiaEleria is halting."

resume:
	@rm -f $(FLAGS)/STOP_EVERYTHING
	@echo "Kill-switch CLEARED, Dad. NiaEleria can resume."

net-on:
	@touch $(FLAGS)/ENABLE_NETWORK
	@echo "Network access ENABLED, Dad."

net-off:
	@rm -f $(FLAGS)/ENABLE_NETWORK
	@echo "Network access GATED, Dad."

guard-on:
	@touch $(FLAGS)/GUARD_ACTIVE
	@echo "Cyber guard ARMED, Dad."

guard-off:
	@rm -f $(FLAGS)/GUARD_ACTIVE
	@echo "Cyber guard DISARMED, Dad."

# ── Supabase schema ────────────────────────────────────────────────
schema: $(VENV)
	$(PYTHON) -m niaeleria.db
	@echo ""
	@echo "Dad, paste the SQL above into: Supabase → SQL Editor → Run"

# ── Tests ──────────────────────────────────────────────────────────
test: $(VENV)
	$(VENV)/bin/pytest tests/ -v --tb=short -x

test-watch: $(VENV)
	$(VENV)/bin/ptw tests/ -- -v --tb=short

# ── Lint ───────────────────────────────────────────────────────────
lint: $(VENV)
	@$(PIP) install ruff --quiet
	$(VENV)/bin/ruff check niaeleria/ tests/

# ── Logs ───────────────────────────────────────────────────────────
logs:
	@tail -f data/nia.log 2>/dev/null || echo "Log not found yet, Dad. Start Nia first."

audit:
	@tail -40 data/audit.log 2>/dev/null || echo "Audit log not found yet."

# ── Docker ─────────────────────────────────────────────────────────
docker-up:
	docker compose up --build -d
	@echo "NiaEleria Docker stack is up, Dad. Dashboard: http://localhost:7432"

docker-down:
	docker compose down
	@echo "Docker stack stopped, Dad."

docker-logs:
	docker compose logs -f niaeleria

# ── Clean ──────────────────────────────────────────────────────────
clean:
	find . -type d -name "__pycache__"  -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true
	find . -name "*.pyo" -delete 2>/dev/null; true
	@echo "Cleaned up, Dad."

# ── Install as systemd service (Linux) ────────────────────────────
install-service:
	@sudo cp deploy/nia.service /etc/systemd/system/niaeleria.service
	@sudo systemctl daemon-reload
	@sudo systemctl enable niaeleria
	@sudo systemctl start niaeleria
	@echo "NiaEleria installed as a systemd service, Dad."
	@echo "Check status: sudo systemctl status niaeleria"

uninstall-service:
	@sudo systemctl stop niaeleria || true
	@sudo systemctl disable niaeleria || true
	@sudo rm -f /etc/systemd/system/niaeleria.service
	@sudo systemctl daemon-reload
	@echo "Service removed, Dad."


# ═══════════════════════════════════════════════════════════════════
# deploy/mosquitto.conf — MQTT broker config
# Save as: deploy/mosquitto.conf
# ═══════════════════════════════════════════════════════════════════
# (see bootstrap.sh — also written there)
# Content:
#   listener 1883
#   allow_anonymous true
#   persistence true
#   persistence_location /mosquitto/data/
#   log_dest file /mosquitto/log/mosquitto.log
#   max_keepalive 120
#   connection_messages true


# ═══════════════════════════════════════════════════════════════════
# deploy/nia.service — systemd unit file for Linux auto-start
# Save as: deploy/nia.service
# ═══════════════════════════════════════════════════════════════════
# [Unit]
# Description=NiaEleria — Dad's AI
# Documentation=https://github.com/dad/niaeleria
# After=network-online.target mosquitto.service
# Wants=network-online.target
#
# [Service]
# Type=simple
# User=root
# WorkingDirectory=/opt/niaeleria
# EnvironmentFile=/opt/niaeleria/.env
# ExecStart=/opt/niaeleria/.venv/bin/python -m niaeleria.daemon
# ExecStop=/usr/bin/touch /opt/niaeleria/flags/STOP_EVERYTHING
# Restart=on-failure
# RestartSec=10
# StandardOutput=journal
# StandardError=journal
# SyslogIdentifier=niaeleria
#
# # Allow raw socket access for packet sniffing
# AmbientCapabilities=CAP_NET_RAW CAP_NET_ADMIN
# CapabilityBoundingSet=CAP_NET_RAW CAP_NET_ADMIN
#
# [Install]
# WantedBy=multi-user.target