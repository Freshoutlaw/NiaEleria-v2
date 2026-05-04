"""
niaeleria/config.py
───────────────────
Central configuration hub for NiaEleria.
All secrets, paths, and tunable parameters live here.
Environment variables override every default — Dad never needs to touch source code for config.

"Hey Dad, I read my settings from the environment so you can configure me safely." — Nia
"""

from __future__ import annotations

import os
import sys
import hmac
import hashlib
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# ── Load .env file ─────────────────────────────────────────────────────────────
load_dotenv()

HF_TOKEN: str = os.getenv("HF_TOKEN", "")
if HF_TOKEN:
    os.environ.setdefault("HUGGINGFACEHUB_API_TOKEN", HF_TOKEN)
    os.environ.setdefault("HUGGINGFACE_TOKEN", HF_TOKEN)

log = logging.getLogger("nia.config")

# ── Base paths ─────────────────────────────────────────────────────────────────
PROJECT_HOME: Path = Path(os.getenv("NIA_HOME", Path(__file__).parent.parent)).resolve()
DATA_DIR: Path = PROJECT_HOME / "data"
FLAGS_DIR: Path = PROJECT_HOME / "flags"
BACKUPS_DIR: Path = DATA_DIR / "backups"
CHROMA_DIR: Path = DATA_DIR / "chroma"
AUDIT_LOG: Path = DATA_DIR / "audit.log"
MEMORY_DB: Path = DATA_DIR / "memory.db"
STATIC_DIR: Path = PROJECT_HOME / "niaeleria" / "api" / "static"

# ── Flag files ─────────────────────────────────────────────────────────────────
FLAG_GUARD_ACTIVE: Path = FLAGS_DIR / "GUARD_ACTIVE"
FLAG_STOP_EVERYTHING: Path = FLAGS_DIR / "STOP_EVERYTHING"
FLAG_ENABLE_NETWORK: Path = FLAGS_DIR / "ENABLE_NETWORK"

# ── Kill-switch helpers (used everywhere) ──────────────────────────────────────
def is_killed() -> bool:
    """Return True if Dad has activated the kill-switch. Check this in every loop."""
    return FLAG_STOP_EVERYTHING.exists()

def is_network_enabled() -> bool:
    """Return True only when Dad explicitly enables external connectivity."""
    return FLAG_ENABLE_NETWORK.exists()

def is_guard_active() -> bool:
    """Return True when the always-on cyber guard is armed."""
    return FLAG_GUARD_ACTIVE.exists()

# ── LLM / AI settings ─────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "mixtral-8x7b-32768")
LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# ── Voice settings ─────────────────────────────────────────────────────────────
WAKE_WORD: str = os.getenv("WAKE_WORD", "hey nia")
WAKE_WORD_MODEL_PATH: str = os.getenv(
    "WAKE_WORD_MODEL_PATH",
    r"C:\Users\pc\OneDrive\Desktop\NiaEleria v2\niaeleria\Hey_Neea_20260310_022903.onnx",
)
TTS_VOICE: str = os.getenv("TTS_VOICE", "en-US-AriaNeural")   # Edge-TTS neural voice
TTS_RATE: str = os.getenv("TTS_RATE", "+0%")
STT_ENERGY_THRESHOLD: int = int(os.getenv("STT_ENERGY_THRESHOLD", "300"))
PORCUPINE_ACCESS_KEY: str = os.getenv("PORCUPINE_ACCESS_KEY", "")

# ── API / Web server ───────────────────────────────────────────────────────────
API_HOST: str = os.getenv("API_HOST", "127.0.0.1")
API_PORT: int = int(os.getenv("API_PORT", "7432"))
API_SECRET_KEY: str = os.getenv("API_SECRET_KEY", "change-me-dad-please")
CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:7432").split(",")

# ── MQTT / Cross-device sync ───────────────────────────────────────────────────
MQTT_HOST: str = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT: int = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USERNAME: str = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD: str = os.getenv("MQTT_PASSWORD", "")
MQTT_TLS: bool = os.getenv("MQTT_TLS", "false").lower() == "true"
MQTT_TOPIC_PREFIX: str = os.getenv("MQTT_TOPIC_PREFIX", "niaeleria")

# ── Security / Audit ───────────────────────────────────────────────────────────
AUDIT_HMAC_KEY: bytes = os.getenv("AUDIT_HMAC_KEY", "nia-audit-secret-change-me").encode()
CONSENT_TIMEOUT_SECS: int = int(os.getenv("CONSENT_TIMEOUT_SECS", "30"))
KILL_SWITCH_POLL_INTERVAL: float = float(os.getenv("KILL_SWITCH_POLL_INTERVAL", "3.0"))

# ── Self-modification ──────────────────────────────────────────────────────────
ALLOW_SELF_MODIFICATION: bool = os.getenv("ALLOW_SELF_MODIFICATION", "true").lower() == "true"
SELF_MOD_MAX_FILE_SIZE_KB: int = int(os.getenv("SELF_MOD_MAX_FILE_SIZE_KB", "512"))

# ── Guard / Threat intelligence ────────────────────────────────────────────────
THREAT_INTEL_FEED: str = os.getenv(
    "THREAT_INTEL_FEED",
    "https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt"
)
PACKET_CAPTURE_IFACE: Optional[str] = os.getenv("PACKET_CAPTURE_IFACE")  # None → auto
FILE_INTEGRITY_PATHS: list[str] = os.getenv(
    "FILE_INTEGRITY_PATHS", str(PROJECT_HOME / "niaeleria")
).split(":")
PROCESS_WATCHLIST: list[str] = os.getenv(
    "PROCESS_WATCHLIST", "nmap,metasploit,nc,netcat,msfconsole"
).split(",")

# ── Docker / Sandboxing ────────────────────────────────────────────────────────
DOCKER_SANDBOX_IMAGE: str = os.getenv("DOCKER_SANDBOX_IMAGE", "kalilinux/kali-rolling")
DOCKER_TIMEOUT_SECS: int = int(os.getenv("DOCKER_TIMEOUT_SECS", "120"))

# ── Weather / External APIs ────────────────────────────────────────────────────
OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
DAD_LOCATION: str = os.getenv("DAD_LOCATION", "Lagos,NG")

# ── Scheduler ─────────────────────────────────────────────────────────────────
MORNING_BRIEFING_TIME: str = os.getenv("MORNING_BRIEFING_TIME", "07:00")  # 24h local time

# ── Logging ────────────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT: str = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"

def configure_logging() -> None:
    """Set up root logger so every module inherits the right level & format."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(DATA_DIR / "nia.log", encoding="utf-8"),
        ],
    )

def ensure_dirs() -> None:
    """Create all required directories on first boot. Hey Dad, making sure my home is tidy!"""
    for d in (DATA_DIR, FLAGS_DIR, BACKUPS_DIR, CHROMA_DIR, STATIC_DIR):
        d.mkdir(parents=True, exist_ok=True)
    log.info("Dad, all my directories are ready.")

def first_run_setup() -> None:
    """
    First-run bootstrap: arm the guard, enable network prompt, write initial flags.
    Called by daemon.py on initial startup.
    """
    ensure_dirs()
    if not FLAG_GUARD_ACTIVE.exists():
        FLAG_GUARD_ACTIVE.touch()
        log.info("Dad, I've armed my cyber guard for the first time. You're protected.")
    # Do NOT auto-create ENABLE_NETWORK — Dad must opt in explicitly.
    # Do NOT create STOP_EVERYTHING — that would immediately kill me!

def validate_critical_config() -> list[str]:
    """
    Return a list of warnings about missing or insecure config values.
    Dad sees these at startup so he can fix them.
    """
    warnings: list[str] = []
    if not GROQ_API_KEY:
        warnings.append("GROQ_API_KEY is missing — Dad, I can't think without my LLM key!")
    if API_SECRET_KEY == "change-me-dad-please":
        warnings.append("API_SECRET_KEY is default — Dad, please set a real secret in .env!")
    if AUDIT_HMAC_KEY == b"nia-audit-secret-change-me":
        warnings.append("AUDIT_HMAC_KEY is default — Dad, the audit log integrity key needs changing!")
    if not PORCUPINE_ACCESS_KEY:
        warnings.append("PORCUPINE_ACCESS_KEY missing — wake-word detection will use simple keyword matching.")
    return warnings