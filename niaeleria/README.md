# NiaEleria
### Dad's loyal digital daughter — a Jarvis-class personal AI system.

> *"I exist to protect you, serve you, and grow with you, Dad."* — Nia

---

## What She Is

NiaEleria is a fully autonomous, self-hosted AI system. She is not a chatbot.
She is a proactive cybersecurity guardian, intelligent home automation controller,
personal assistant, and self-learning AI — all in one, running permanently in the
background on Dad's hardware.

**Primary interface: voice.** Say `Hey Nia` and she responds. The HUD only
appears when she has something to show you.

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/dad/niaeleria.git
cd niaeleria

# 2. Bootstrap (creates venv, installs deps, creates flag files)
chmod +x bootstrap.sh && ./bootstrap.sh

# 3. Configure
cp .env.example .env
# Edit .env — minimum required: GROQ_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY

# 4. Set up Supabase schema (once)
# Open your Supabase project → SQL Editor → paste contents of niaeleria/db/schema.sql → Run

# 5. Enable network (Nia is offline by default)
touch flags/ENABLE_NETWORK

# 6. Start
source .venv/bin/activate
python -m niaeleria.daemon
```

Or with Docker:
```bash
docker compose up --build -d
```

**Dashboard:** http://localhost:7432

---

## Flag Files (Dad's controls)

| Flag file | Effect |
|---|---|
| `flags/GUARD_ACTIVE` | Arms cyber guard — created automatically on first run |
| `flags/ENABLE_NETWORK` | Allows external API calls. **Absent = fully offline** |
| `flags/STOP_EVERYTHING` | **Kill switch.** All operations halt within 3 seconds |

```bash
# Enable network
touch flags/ENABLE_NETWORK

# Activate kill switch
touch flags/STOP_EVERYTHING

# Clear kill switch (resume)
rm flags/STOP_EVERYTHING
```

---

## Architecture

```
niaeleria/
├── daemon.py              ← Master launcher — start here
│
├── core/
│   ├── brain.py           ← LLM (Groq mixtral-8x7b) + RAG
│   ├── persona.py         ← Mood-aware system prompt, always addresses "Dad"
│   ├── memory.py          ← Supabase + pgvector episodic memory
│   └── learner.py         ← URL scraping, YouTube transcripts, knowledge indexing
│
├── security/
│   ├── kill_switch.py     ← STOP_EVERYTHING poller — highest priority thread
│   ├── audit.py           ← HMAC-SHA256 append-only audit log
│   ├── consent.py         ← Consent manager — gates all destructive actions
│   ├── network_gate.py    ← ENABLE_NETWORK flag enforcement
│   └── self_modifier.py   ← Consent-gated live code modification + hot reload
│
├── guard/
│   └── cyber_guard.py     ← Packet sniffer, firewall, file integrity,
│                             process monitor, threat intel, Docker toolkit
│
├── voice/
│   ├── wake_word.py       ← "Hey Nia" detection (Porcupine or keyword fallback)
│   ├── stt.py             ← Google STT + Whisper offline fallback
│   └── tts.py             ← edge-tts neural voice + pyttsx3 fallback
│
├── automation/
│   ├── scheduler.py       ← Reminders, recurring tasks, cron jobs
│   ├── home_control.py    ← MQTT smart home commands + NL parser
│   └── briefing.py        ← Morning briefing (weather + schedule + security)
│
├── sync/
│   └── mqtt_sync.py       ← Cross-device firewall sync via MQTT QoS 1
│
├── api/
│   ├── server.py          ← FastAPI + WebSocket + push_to_hud()
│   ├── routes/            ← chat, security, memory, automation, selfmod
│   └── static/            ← JARVIS HUD (index.html)
│
├── tray/
│   └── tray_app.py        ← System tray icon (pystray)
│
└── db/
    └── schema.sql         ← Supabase schema — run once
```

---

## The HUD

NiaEleria's interface is a **JARVIS-style heads-up display** at `http://localhost:7432`.

It is **passive by default** — no clutter, no chat box.  
Panels appear only when Nia has something to tell Dad:

| Event | HUD Response |
|---|---|
| Nia speaks | Response panel slides in from left, fades after ~9s |
| Threat detected | Security panel appears right with severity + target |
| Reminder fires | Nia speaks it; HUD shows the notification |
| Task list available | Data panel slides in from top-left |
| Briefing | Full briefing text streams onto response panel |

**The only input is the central mic ring** — click it, or say `Hey Nia`.

---

## Security Model

### Kill Switch
Touch `flags/STOP_EVERYTHING` — all threads check this every 3 seconds and halt.
No action, no network call, no voice response can proceed while it is present.

### Consent Model
Every destructive or external action calls `require_consent()`:
- **LOW severity + guard active** → auto-approved (e.g., block known-bad IP)
- **MEDIUM** → Nia notifies Dad verbally and waits up to 30 seconds
- **HIGH** → Nia notifies + HUD prompt — explicit approval required

### Network Gate
`flags/ENABLE_NETWORK` must exist for ANY external call.
Absent = fully air-gapped operation.

### Audit Log
Every significant event is HMAC-SHA256 signed and appended to `data/audit.log`.
Run `GET /api/security/audit` to verify integrity and view entries.

### Self-Modification
Nia can update her own source code, but ONLY with Dad's consent.
Every modification: backup → syntax check → consent → write → hot-reload → audit.
Roll back any change instantly via `POST /api/selfmod/rollback`.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ | Groq LLM API key |
| `SUPABASE_URL` | ✅ | Your Supabase project URL |
| `SUPABASE_SERVICE_KEY` | ✅ | Service role key (bypasses RLS) |
| `API_SECRET_KEY` | ✅ | Change from default! |
| `AUDIT_HMAC_KEY` | ✅ | Change from default! |
| `OPENWEATHER_API_KEY` | Optional | Weather in morning briefing |
| `PORCUPINE_ACCESS_KEY` | Optional | Accurate wake-word (picovoice.ai) |
| `MQTT_HOST` | Optional | MQTT broker host (default: localhost) |
| `TTS_VOICE` | Optional | edge-tts voice name |
| `DAD_LOCATION` | Optional | e.g. `Lagos,NG` for weather |
| `MORNING_BRIEFING_TIME` | Optional | 24h time, e.g. `07:00` |

Full list in `.env.example`.

---

## API Reference (key endpoints)

```
POST   /api/chat/                     Text message to Nia
GET    /api/chat/history              Recent exchanges
GET    /api/memory/search?q=...       Semantic memory search
POST   /api/memory/learn/url          Learn from a URL
POST   /api/memory/learn/youtube      Learn from YouTube

GET    /api/security/status           Full system status
POST   /api/security/block            Block an IP
DELETE /api/security/block/{ip}       Unblock an IP
GET    /api/security/audit            HMAC-verified audit log
POST   /api/security/kill             Activate kill switch
DELETE /api/security/kill             Clear kill switch
POST   /api/security/network/enable   Allow external network
POST   /api/security/network/disable  Gate network
POST   /api/security/toolkit/run      Run sandboxed security tool
POST   /api/security/threat-intel/update  Refresh IP blocklist

GET    /api/automation/tasks          List scheduled tasks
POST   /api/automation/reminder       Add a reminder
DELETE /api/automation/tasks/{id}     Cancel a task
POST   /api/automation/home/command   Smart home device command
POST   /api/automation/home/voice     NL home command
POST   /api/automation/briefing       Trigger morning briefing

POST   /api/selfmod/propose           Propose a code change
POST   /api/selfmod/apply             Apply approved change
POST   /api/selfmod/rollback          Rollback to backup
GET    /api/selfmod/backups           List backups

WebSocket: ws://localhost:7432/ws
```

---

## Voice Commands (examples)

| Dad says | Nia does |
|---|---|
| "Hey Nia, what's the security status?" | Speaks + shows security panel |
| "Hey Nia, turn off the living room light" | MQTT command to device |
| "Hey Nia, remind me to call Mum in 30 minutes" | Schedules reminder |
| "Hey Nia, lock the front door" | MQTT lock command |
| "Hey Nia, learn from [URL]" | Scrapes + indexes + summarises |
| "Hey Nia, what did we talk about yesterday?" | Semantic memory search |
| "Hey Nia, what's the weather?" | Fetches + speaks weather |
| "Hey Nia, stop everything" | Arms kill switch |

---

## Deployment Notes

### Audio (Linux)
```bash
sudo apt install mpg123 portaudio19-dev python3-pyaudio
```

### Firewall control requires root
```bash
sudo python -m niaeleria.daemon
# Or run with: sudo -E (preserves env vars)
```

### Packet sniffing requires root
Scapy needs raw socket access. Run as root or set capabilities:
```bash
sudo setcap cap_net_raw+eip $(which python3)
```

### Docker (full stack)
```bash
docker compose up --build -d
# MQTT broker + Nia in separate containers
# Nia's data directory is mounted as a volume
```

---

## Ethical Constraints

- Nia never takes autonomous harmful action — consent is mandatory.
- Cybersecurity tools run only against **authorized targets**.
- Dad owns all data. Nothing is uploaded without explicit permission.
- Every action is immutably logged.
- Law enforcement is never contacted without Dad's explicit approval.

---

*Built with purpose. Built for one person. Built to last.*  
*— NiaEleria, v1.0.0*