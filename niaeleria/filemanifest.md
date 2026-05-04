# NiaEleria — Complete File Manifest

Every file that needs to exist. Check these off as you build her out, Dad.

---

## Source Code

```
niaeleria/
├── __init__.py                     ✅  Package root
├── __main__.py                     ✅  python -m niaeleria entry
├── config.py                       ✅  All env vars, flag helpers
├── daemon.py                       ✅  Master launcher + watchdog + HUD broadcaster
│
├── core/
│   ├── __init__.py                 ✅  Exports PersonaEngine, MemoryStore, NiaBrain, InternetLearner
│   ├── brain.py                    ✅  Groq LLM + RAG + streaming
│   ├── persona.py                  ✅  Mood-aware system prompt, always "Dad"
│   ├── memory.py                   ✅  Supabase + pgvector episodic memory
│   └── learner.py                  ✅  URL scraping, YouTube, background loop
│
├── security/
│   ├── __init__.py                 ✅  Exports all security primitives
│   ├── kill_switch.py              ✅  STOP_EVERYTHING poller
│   ├── audit.py                    ✅  HMAC-SHA256 append-only log
│   ├── consent.py                  ✅  Consent manager (LOW/MEDIUM/HIGH)
│   ├── network_gate.py             ✅  ENABLE_NETWORK flag enforcement
│   └── self_modifier.py            ✅  Backup → validate → consent → apply → hot-reload
│
├── guard/
│   ├── __init__.py                 ✅  Exports CyberGuard + all components
│   └── cyber_guard.py              ✅  Firewall, ThreatIntel, FileIntegrity,
│                                       ProcessMonitor, PacketSniffer, Toolkit,
│                                       CyberGuard orchestrator — all HUD-wired
│
├── voice/
│   ├── __init__.py                 ✅  VoiceInterface pipeline
│   ├── wake_word.py                ✅  Porcupine + keyword fallback
│   ├── stt.py                      ✅  Google STT + Whisper offline
│   └── tts.py                      ✅  edge-tts neural + pyttsx3 fallback
│
├── automation/
│   ├── __init__.py                 ✅  Exports Scheduler, HomeController, MorningBriefing
│   ├── scheduler.py                ✅  One-shot + recurring tasks, kill-switch aware
│   ├── home_control.py             ✅  MQTT device commands + NL parser
│   └── briefing.py                 ✅  Morning briefing — HUD-aware, weather + guard
│
├── sync/
│   ├── __init__.py                 ✅  Exports MQTTSync
│   └── mqtt_sync.py                ✅  Cross-device firewall sync, QoS 1
│
├── api/
│   ├── __init__.py                 ✅  Exports create_app, inject_services, push_to_hud
│   ├── server.py                   ✅  FastAPI + WebSocket + push_to_hud() + voice_trigger
│   ├── routes/
│   │   ├── __init__.py             ✅
│   │   ├── chat.py                 ✅  Text chat + history + memory search
│   │   ├── security.py             ✅  Guard status, block/unblock, audit, toolkit,
│   │   │                               kill-switch, network toggle, threat intel update
│   │   ├── memory.py               ✅  Recent, search, learn URL, learn YouTube
│   │   ├── automation.py           ✅  Tasks, reminders, home commands, briefing
│   │   └── selfmod.py              ✅  Propose, apply, rollback, list backups
│   └── static/
│       └── index.html              ✅  JARVIS HUD — full standalone UI
│
├── tray/
│   ├── __init__.py                 ✅  Exports NiaTray
│   └── tray_app.py                 ✅  System tray icon + voice popup
│
└── db/
    ├── __init__.py                 ✅  Schema printer utility
    └── schema.sql                  ✅  Supabase: exchanges, knowledge, RPCs, pgvector
```

## Project Root Files

```
niaeleria/          (root)
├── requirements.txt                ✅  All Python dependencies
├── .env.example                    ✅  All env vars documented
├── .gitignore                      ✅  Secrets + data excluded
├── pyproject.toml                  ✅  Package metadata + entry point
├── Dockerfile                      ✅  Production container
├── docker-compose.yml              ✅  Nia + MQTT broker
├── bootstrap.sh                    ✅  One-command setup
├── Makefile                        ✅  make run / stop / test / schema etc.
└── README.md                       ✅  Full setup, architecture, API reference
```

## Deploy Folder

```
deploy/
├── mosquitto.conf                  ✅  MQTT broker config
└── nia.service                     ✅  systemd unit for Linux autostart
```

## Tests

```
tests/
├── conftest.py                     ✅  Shared fixtures, temp env, mocks
├── test_security.py                ✅  Kill-switch, audit, network gate, consent
├── test_memory.py                  ✅  Supabase fallback, store + search
├── test_guard.py                   ✅  Firewall, threat intel, file integrity, self-mod
├── test_brain.py                   ✅  Persona, home controller, scheduler
├── test_api.py                     ✅  All REST routes + TestClient
├── test_voice.py                   ✅  VoiceInterface, TTS, STT, WakeWord
└── test_learner.py                 ✅  URL extract, YouTube ID, consent, background loop
```

---

## First-Run Checklist for Dad

### 1. Prerequisites
```bash
# Python 3.11+
python3 --version

# Audio (Linux)
sudo apt install mpg123 portaudio19-dev python3-pyaudio

# Packet sniffing (Linux)
sudo apt install python3-scapy
# OR: sudo setcap cap_net_raw+eip $(which python3)

# Docker (for security toolkit)
# https://docs.docker.com/get-docker/
```

### 2. Accounts needed
| Service | Where | Required? |
|---|---|---|
| Groq | console.groq.com | ✅ Yes — the LLM |
| Supabase | supabase.com | ✅ Yes — memory |
| Picovoice | picovoice.ai | ⬜ Optional — better wake word |
| OpenWeatherMap | openweathermap.org | ⬜ Optional — weather briefing |

### 3. Supabase setup
1. Create a new project at supabase.com
2. Go to **Settings → API** — copy `URL` and `service_role` key
3. Go to **SQL Editor → New Query**
4. Run: `python -m niaeleria.db` → copy output → paste → Run

### 4. Bootstrap & configure
```bash
chmod +x bootstrap.sh && ./bootstrap.sh
# Edit .env — fill in GROQ_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY
```

### 5. Run
```bash
# Standard
make run

# With elevated privileges (for firewall + packet sniffing)
sudo -E .venv/bin/python -m niaeleria.daemon

# Docker
make docker-up
```

### 6. Enable network (Nia is offline by default)
```bash
make net-on
# or: touch flags/ENABLE_NETWORK
```

### 7. Dashboard
Open: **http://localhost:7432**
Click the central mic ring or say **"Hey Nia"**

### 8. Kill switch
```bash
make stop     # halt everything
make resume   # resume
```

---

## API Quick Reference

| Method | Endpoint | What it does |
|---|---|---|
| `GET` | `/health` | Alive check |
| `POST` | `/api/chat/` | Text message to Nia |
| `GET` | `/api/security/status` | Full system status |
| `POST` | `/api/security/block` | Block an IP |
| `DELETE` | `/api/security/block/{ip}` | Unblock |
| `GET` | `/api/security/audit` | Audit log |
| `POST` | `/api/security/kill` | Kill switch ON |
| `DELETE` | `/api/security/kill` | Kill switch OFF |
| `POST` | `/api/security/network/enable` | Enable network |
| `POST` | `/api/security/network/disable` | Gate network |
| `POST` | `/api/security/threat-intel/update` | Refresh IP blocklist |
| `GET` | `/api/memory/recent` | Recent conversations |
| `GET` | `/api/memory/search?q=` | Semantic search |
| `POST` | `/api/memory/learn/url` | Learn from URL |
| `POST` | `/api/memory/learn/youtube` | Learn from YouTube |
| `GET` | `/api/automation/tasks` | Scheduled tasks |
| `POST` | `/api/automation/reminder` | Add reminder |
| `POST` | `/api/automation/home/command` | Device command |
| `POST` | `/api/automation/home/voice` | NL home command |
| `POST` | `/api/automation/briefing` | Morning briefing |
| `POST` | `/api/selfmod/propose` | Propose code change |
| `POST` | `/api/selfmod/apply` | Apply approved change |
| `POST` | `/api/selfmod/rollback` | Rollback |
| `WS` | `/ws` | Real-time HUD bridge |

---

*NiaEleria v1.0.0 — Complete.*  
*"I'm ready when you are, Dad." — Nia*