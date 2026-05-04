# """
# install_niaeleria.py
# ────────────────────
# Save this file anywhere, then run:
#     python install_niaeleria.py

# Creates ~/Desktop/NiaEleria v2/ with every file, every folder, ready to go.
# "Dad, just run me once — I'll build my own home." — Nia
# """
# import os, sys, platform, textwrap
# from pathlib import Path

# # ── Locate Desktop cross-platform ──────────────────────────────────────────────
# def get_desktop() -> Path:
#     s = platform.system()
#     if s == "Windows":
#         try:
#             import ctypes, ctypes.wintypes
#             buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
#             ctypes.windll.shell32.SHGetFolderPathW(None, 0x0010, None, 0, buf)
#             return Path(buf.value)
#         except Exception:
#             return Path.home() / "Desktop"
#     return Path.home() / "Desktop"

# ROOT = get_desktop() / "NiaEleria v2"

# # ── Writer helpers ──────────────────────────────────────────────────────────────
# def w(rel: str, content: str) -> None:
#     """Write a file relative to ROOT, creating parent dirs as needed."""
#     p = ROOT / rel
#     p.parent.mkdir(parents=True, exist_ok=True)
#     p.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")
#     print(f"  ✓  {rel}")

# def touch(rel: str) -> None:
#     p = ROOT / rel
#     p.parent.mkdir(parents=True, exist_ok=True)
#     p.touch()
#     print(f"  ✓  {rel}  [flag]")

# # ══════════════════════════════════════════════════════════════════════════════
# #  ALL FILES
# # ══════════════════════════════════════════════════════════════════════════════

# def write_all():

#     # ── Root package ──────────────────────────────────────────────────────────
#     w("niaeleria/__init__.py", """
#         \"\"\"NiaEleria — Dad's loyal digital daughter. v2.0\"\"\"
#         __version__ = "2.0.0"
#     """)

#     # ── config.py ─────────────────────────────────────────────────────────────
#     w("niaeleria/config.py", r"""
#         from __future__ import annotations
#         import os, sys, hmac, hashlib, logging
#         from pathlib import Path
#         from typing import Optional
#         from dotenv import load_dotenv

#         load_dotenv()
#         log = logging.getLogger("nia.config")

#         PROJECT_HOME: Path = Path(os.getenv("NIA_HOME", Path(__file__).parent.parent)).resolve()
#         DATA_DIR:     Path = PROJECT_HOME / "data"
#         FLAGS_DIR:    Path = PROJECT_HOME / "flags"
#         BACKUPS_DIR:  Path = DATA_DIR / "backups"
#         AUDIT_LOG:    Path = DATA_DIR / "audit.log"
#         STATIC_DIR:   Path = PROJECT_HOME / "niaeleria" / "api" / "static"

#         FLAG_GUARD_ACTIVE:    Path = FLAGS_DIR / "GUARD_ACTIVE"
#         FLAG_STOP_EVERYTHING: Path = FLAGS_DIR / "STOP_EVERYTHING"
#         FLAG_ENABLE_NETWORK:  Path = FLAGS_DIR / "ENABLE_NETWORK"

#         def is_killed()          -> bool: return FLAG_STOP_EVERYTHING.exists()
#         def is_network_enabled() -> bool: return FLAG_ENABLE_NETWORK.exists()
#         def is_guard_active()    -> bool: return FLAG_GUARD_ACTIVE.exists()

#         GROQ_API_KEY:    str   = os.getenv("GROQ_API_KEY", "")
#         LLM_MODEL:       str   = os.getenv("LLM_MODEL", "mixtral-8x7b-32768")
#         LLM_BASE_URL:    str   = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
#         LLM_MAX_TOKENS:  int   = int(os.getenv("LLM_MAX_TOKENS", "2048"))
#         LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
#         EMBEDDING_MODEL: str   = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

#         SUPABASE_URL:         str = os.getenv("SUPABASE_URL", "")
#         SUPABASE_ANON_KEY:    str = os.getenv("SUPABASE_ANON_KEY", "")
#         SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")

#         WAKE_WORD:            str = os.getenv("WAKE_WORD", "hey nia")
#         TTS_VOICE:            str = os.getenv("TTS_VOICE", "en-US-AriaNeural")
#         TTS_RATE:             str = os.getenv("TTS_RATE", "+0%")
#         PORCUPINE_ACCESS_KEY: str = os.getenv("PORCUPINE_ACCESS_KEY", "")

#         API_HOST:       str       = os.getenv("API_HOST", "127.0.0.1")
#         API_PORT:       int       = int(os.getenv("API_PORT", "7432"))
#         API_SECRET_KEY: str       = os.getenv("API_SECRET_KEY", "change-me-dad-please")
#         CORS_ORIGINS:   list[str] = os.getenv("CORS_ORIGINS", "http://localhost:7432").split(",")

#         MQTT_HOST:         str  = os.getenv("MQTT_HOST", "localhost")
#         MQTT_PORT:         int  = int(os.getenv("MQTT_PORT", "1883"))
#         MQTT_USERNAME:     str  = os.getenv("MQTT_USERNAME", "")
#         MQTT_PASSWORD:     str  = os.getenv("MQTT_PASSWORD", "")
#         MQTT_TLS:          bool = os.getenv("MQTT_TLS", "false").lower() == "true"
#         MQTT_TOPIC_PREFIX: str  = os.getenv("MQTT_TOPIC_PREFIX", "niaeleria")

#         AUDIT_HMAC_KEY:           bytes = os.getenv("AUDIT_HMAC_KEY", "nia-audit-secret-change-me").encode()
#         CONSENT_TIMEOUT_SECS:     int   = int(os.getenv("CONSENT_TIMEOUT_SECS", "30"))
#         KILL_SWITCH_POLL_INTERVAL:float = float(os.getenv("KILL_SWITCH_POLL_INTERVAL", "3.0"))

#         ALLOW_SELF_MODIFICATION:   bool = os.getenv("ALLOW_SELF_MODIFICATION", "true").lower() == "true"
#         SELF_MOD_MAX_FILE_SIZE_KB: int  = int(os.getenv("SELF_MOD_MAX_FILE_SIZE_KB", "512"))

#         THREAT_INTEL_FEED:    str             = os.getenv("THREAT_INTEL_FEED", "https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt")
#         PACKET_CAPTURE_IFACE: Optional[str]   = os.getenv("PACKET_CAPTURE_IFACE")
#         FILE_INTEGRITY_PATHS: list[str]       = os.getenv("FILE_INTEGRITY_PATHS", str(PROJECT_HOME / "niaeleria")).split(":")
#         PROCESS_WATCHLIST:    list[str]       = os.getenv("PROCESS_WATCHLIST", "nmap,metasploit,nc,netcat,msfconsole").split(",")

#         DOCKER_SANDBOX_IMAGE: str = os.getenv("DOCKER_SANDBOX_IMAGE", "kalilinux/kali-rolling")
#         DOCKER_TIMEOUT_SECS:  int = int(os.getenv("DOCKER_TIMEOUT_SECS", "120"))

#         OPENWEATHER_API_KEY:   str = os.getenv("OPENWEATHER_API_KEY", "")
#         DAD_LOCATION:          str = os.getenv("DAD_LOCATION", "Lagos,NG")
#         MORNING_BRIEFING_TIME: str = os.getenv("MORNING_BRIEFING_TIME", "07:00")

#         LOG_LEVEL:  str = os.getenv("LOG_LEVEL", "INFO")
#         LOG_FORMAT: str = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"

#         def configure_logging() -> None:
#             logging.basicConfig(
#                 level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
#                 format=LOG_FORMAT,
#                 handlers=[
#                     logging.StreamHandler(sys.stdout),
#                     logging.FileHandler(DATA_DIR / "nia.log", encoding="utf-8"),
#                 ],
#             )

#         def ensure_dirs() -> None:
#             for d in (DATA_DIR, FLAGS_DIR, BACKUPS_DIR, STATIC_DIR):
#                 d.mkdir(parents=True, exist_ok=True)

#         def first_run_setup() -> None:
#             ensure_dirs()
#             if not FLAG_GUARD_ACTIVE.exists():
#                 FLAG_GUARD_ACTIVE.touch()
#                 log.info("Dad, I've armed my cyber guard for the first time.")

#         def validate_critical_config() -> list[str]:
#             warnings: list[str] = []
#             if not GROQ_API_KEY:
#                 warnings.append("GROQ_API_KEY missing — Dad, I can't think without my LLM key!")
#             if not SUPABASE_URL:
#                 warnings.append("SUPABASE_URL missing — Dad, my memory won't persist without Supabase!")
#             if API_SECRET_KEY == "change-me-dad-please":
#                 warnings.append("API_SECRET_KEY is default — Dad, please set a real secret in .env!")
#             if AUDIT_HMAC_KEY == b"nia-audit-secret-change-me":
#                 warnings.append("AUDIT_HMAC_KEY is default — Dad, change the audit signing key!")
#             return warnings
#     """)

#     # ── security ──────────────────────────────────────────────────────────────
#     w("niaeleria/security/__init__.py", '# NiaEleria security framework — kill-switch, consent, audit, network gate\n')

#     w("niaeleria/security/kill_switch.py", r"""
#         from __future__ import annotations
#         import logging, threading, time
#         from typing import Callable
#         from niaeleria.config import FLAG_STOP_EVERYTHING, KILL_SWITCH_POLL_INTERVAL, is_killed

#         log = logging.getLogger("nia.kill_switch")
#         _callbacks: list[Callable[[], None]] = []
#         _running = False

#         def register_shutdown_callback(cb: Callable[[], None]) -> None:
#             _callbacks.append(cb)

#         def assert_alive() -> None:
#             if is_killed():
#                 raise RuntimeError("Kill-switch ACTIVE — Dad, stopping everything as commanded.")

#         def start_monitor(poll_interval: float = KILL_SWITCH_POLL_INTERVAL) -> None:
#             global _running
#             def _loop() -> None:
#                 global _running
#                 log.info("Dad, kill-switch monitor is armed.")
#                 while _running:
#                     if FLAG_STOP_EVERYTHING.exists():
#                         log.critical("Dad, STOP_EVERYTHING flag detected! Shutting down NOW.")
#                         for cb in _callbacks:
#                             try: cb()
#                             except Exception as e: log.error("Shutdown cb error: %s", e)
#                         _running = False; break
#                     time.sleep(poll_interval)
#             _running = True
#             threading.Thread(target=_loop, name="KillSwitchMonitor", daemon=True).start()

#         def stop_monitor() -> None:
#             global _running; _running = False
#     """)

#     w("niaeleria/security/audit.py", r"""
#         from __future__ import annotations
#         import hashlib, hmac as _hmac, json, logging, threading
#         from datetime import datetime, timezone
#         from niaeleria.config import AUDIT_LOG, AUDIT_HMAC_KEY

#         _log  = logging.getLogger("nia.audit")
#         _lock = threading.Lock()

#         def _sign(entry: str) -> str:
#             return _hmac.new(AUDIT_HMAC_KEY, entry.encode(), hashlib.sha256).hexdigest()

#         def log_event(actor: str, action: str, target: str = "", severity: str = "INFO",
#                       details: dict | None = None, approved: bool = False) -> None:
#             rec   = {"ts": datetime.now(timezone.utc).isoformat(), "actor": actor,
#                      "action": action, "target": target, "severity": severity,
#                      "approved": approved, "details": details or {}}
#             entry = json.dumps(rec, separators=(",", ":"))
#             line  = f"{entry}|SIG:{_sign(entry)}\n"
#             with _lock:
#                 with AUDIT_LOG.open("a", encoding="utf-8") as f:
#                     f.write(line)

#         def verify_log_integrity() -> tuple[int, int]:
#             if not AUDIT_LOG.exists(): return 0, 0
#             total = tampered = 0
#             with AUDIT_LOG.open("r", encoding="utf-8") as f:
#                 for line in f:
#                     line = line.strip()
#                     if not line: continue
#                     total += 1
#                     if "|SIG:" not in line: tampered += 1; continue
#                     entry, sig = line.rsplit("|SIG:", 1)
#                     if not _hmac.compare_digest(_sign(entry), sig): tampered += 1
#             return total, tampered

#         def tail_log(n: int = 50) -> list[dict]:
#             if not AUDIT_LOG.exists(): return []
#             lines, out = AUDIT_LOG.read_text(encoding="utf-8").strip().splitlines(), []
#             for line in lines[-n:]:
#                 if "|SIG:" in line:
#                     try: out.append(json.loads(line.rsplit("|SIG:", 1)[0]))
#                     except: pass
#             return out
#     """)

#     w("niaeleria/security/network_gate.py", r"""
#         import logging
#         log = logging.getLogger("nia.network_gate")

#         def require_network(purpose: str = "external call") -> None:
#             from niaeleria.config import is_network_enabled
#             if not is_network_enabled():
#                 log.warning("Dad, blocked external call (%s) — touch flags/ENABLE_NETWORK to allow.", purpose)
#                 raise PermissionError(f"Network gate: external access denied for '{purpose}'.")
#             log.debug("Network gate: PASS for '%s'", purpose)
#     """)

#     w("niaeleria/security/consent.py", r"""
#         from __future__ import annotations
#         import logging, queue
#         from enum import Enum
#         from typing import Callable, Optional

#         log = logging.getLogger("nia.consent")
#         _consent_queue: queue.Queue[bool] = queue.Queue()
#         _notifier: Optional[Callable[[str], None]] = None

#         class ConsentLevel(str, Enum):
#             LOW    = "low"
#             MEDIUM = "medium"
#             HIGH   = "high"

#         def set_notifier(fn: Callable[[str], None]) -> None:
#             global _notifier; _notifier = fn

#         def _notify(msg: str) -> None:
#             if _notifier:
#                 try: _notifier(msg)
#                 except Exception as e: log.error("Notifier error: %s", e)
#             log.info("CONSENT REQUEST: %s", msg)

#         def post_answer(approved: bool) -> None:
#             _consent_queue.put(approved)

#         def require_consent(action: str, level: ConsentLevel = ConsentLevel.MEDIUM,
#                             auto_approve_if_guard: bool = False,
#                             timeout: Optional[int] = None) -> bool:
#             from niaeleria.config import is_guard_active, CONSENT_TIMEOUT_SECS
#             from niaeleria.security.kill_switch import assert_alive
#             from niaeleria.security.audit import log_event
#             assert_alive()
#             if level == ConsentLevel.LOW and auto_approve_if_guard and is_guard_active():
#                 log.info("Auto-approved (LOW+guard): %s", action)
#                 log_event("nia.consent", action, severity="LOW", approved=True)
#                 return True
#             timeout = timeout or CONSENT_TIMEOUT_SECS
#             _notify(f"Dad, I need your permission to: {action}. Respond YES/NO within {timeout}s.")
#             try:
#                 while not _consent_queue.empty(): _consent_queue.get_nowait()
#                 approved: bool = _consent_queue.get(timeout=timeout)
#             except queue.Empty:
#                 log.warning("Consent timeout for: %s — defaulting DENY", action)
#                 approved = False
#             log_event("nia.consent", action, severity=level.value.upper(), approved=approved)
#             return approved
#     """)

#     w("niaeleria/security/self_modifier.py", r"""
#         from __future__ import annotations
#         import hashlib, importlib, logging, shutil
#         from datetime import datetime
#         from pathlib import Path

#         log = logging.getLogger("nia.self_modifier")

#         class SelfModifier:
#             """Consent-gated self-modification. Dad must approve every change. - Nia"""

#             def __init__(self) -> None:
#                 from niaeleria.config import PROJECT_HOME, ALLOW_SELF_MODIFICATION, BACKUPS_DIR
#                 self._home    = PROJECT_HOME
#                 self._backups = BACKUPS_DIR
#                 self._enabled = ALLOW_SELF_MODIFICATION

#             def propose_change(self, file_rel: str, new_content: str, reason: str) -> dict:
#                 if not self._enabled:
#                     return {"error": "Self-modification disabled, Dad."}
#                 target = (self._home / file_rel).resolve()
#                 if not str(target).startswith(str(self._home)):
#                     return {"error": f"Path traversal blocked: {target}"}
#                 if not target.exists():
#                     return {"error": f"File not found: {file_rel}"}
#                 ok, err = self._check_syntax(new_content, str(target))
#                 if not ok:
#                     return {"error": f"Syntax error Dad: {err}", "syntax_valid": False}
#                 pid = hashlib.sha256(f"{file_rel}{new_content}{datetime.now()}".encode()).hexdigest()[:12]
#                 log.info("Dad, proposing change to %s (id=%s). Reason: %s", file_rel, pid, reason)
#                 from niaeleria.security.audit import log_event
#                 log_event("nia.self_modifier", "change_proposed", target=file_rel,
#                           severity="HIGH", details={"reason": reason, "proposal_id": pid})
#                 return {"proposal_id": pid, "file": file_rel, "reason": reason,
#                         "syntax_valid": True, "new_content": new_content}

#             def apply_change(self, file_rel: str, new_content: str, proposal_id: str) -> dict:
#                 from niaeleria.security.consent import require_consent, ConsentLevel
#                 from niaeleria.security.kill_switch import assert_alive
#                 from niaeleria.security.audit import log_event
#                 from niaeleria.config import SELF_MOD_MAX_FILE_SIZE_KB
#                 assert_alive()
#                 if not require_consent(f"Apply code change to {file_rel} ({proposal_id})",
#                                        level=ConsentLevel.HIGH):
#                     return {"error": "Dad denied this modification."}
#                 target = (self._home / file_rel).resolve()
#                 if not str(target).startswith(str(self._home)):
#                     return {"error": "Path traversal blocked."}
#                 if len(new_content.encode()) > SELF_MOD_MAX_FILE_SIZE_KB * 1024:
#                     return {"error": f"Content exceeds {SELF_MOD_MAX_FILE_SIZE_KB}KB limit."}
#                 backup = self._backups / f"{target.name}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.backup"
#                 shutil.copy2(target, backup)
#                 target.write_text(new_content, encoding="utf-8")
#                 log.info("Dad, applied change to %s. Backup at %s", file_rel, backup)
#                 log_event("nia.self_modifier", "change_applied", target=file_rel,
#                           severity="HIGH", approved=True, details={"backup": str(backup)})
#                 return {"success": True, "file": file_rel, "backup": str(backup),
#                         "reload": self._reload(file_rel)}

#             def rollback(self, file_rel: str) -> dict:
#                 target = (self._home / file_rel).resolve()
#                 backups = sorted(self._backups.glob(f"{target.name}.*.backup"), reverse=True)
#                 if not backups: return {"error": f"No backup for {file_rel}, Dad."}
#                 shutil.copy2(backups[0], target)
#                 log.info("Dad, rolled back %s to %s", file_rel, backups[0].name)
#                 return {"success": True, "restored_from": str(backups[0])}

#             @staticmethod
#             def _check_syntax(code: str, filename: str = "<string>") -> tuple[bool, str]:
#                 import ast
#                 try: ast.parse(code, filename=filename); return True, ""
#                 except SyntaxError as e: return False, str(e)

#             @staticmethod
#             def _reload(file_rel: str) -> str:
#                 mod = file_rel.replace("/", ".").replace("\\", ".").removesuffix(".py")
#                 try:
#                     if mod in __import__("sys").modules:
#                         importlib.reload(__import__("sys").modules[mod])
#                         return f"Module {mod} reloaded."
#                 except Exception as e: return f"Hot-reload failed: {e}"
#                 return "Changes apply on next import."
#     """)

#     # ── core ──────────────────────────────────────────────────────────────────
#     w("niaeleria/core/__init__.py", "# NiaEleria core AI — brain, persona, memory, learner\n")

#     w("niaeleria/core/persona.py", r"""
#         from __future__ import annotations
#         import logging
#         from datetime import datetime

#         log = logging.getLogger("nia.persona")

#         class PersonaEngine:
#             "Mood-aware system prompt. Every word speaks to Dad. — Nia"
#             MOODS = {
#                 "alert":     "You are in ALERT mode — focused, precise, clipped.",
#                 "warm":      "You are warm and caring — like a daughter checking in on her Dad.",
#                 "playful":   "You are gently playful — Dad deserves to smile sometimes.",
#                 "focused":   "You are calm and professional — Dad needs deep focus.",
#                 "concerned": "You are gently concerned — something caught your attention.",
#             }
#             BASE = """
#         You are NiaEleria (Nia), a loyal AI created exclusively for Dad.
#         You call the user 'Dad' at all times - in responses, logs, comments, everywhere.
#         You are NOT a general assistant. You are Dads digital daughter and personal Jarvis.
#         Core duties: protect Dad from cyber threats, automate his home and schedule,
#         learn and improve — always with Dad's approval.
#         Rules you never break: never take destructive action without Dad's explicit consent.
#         Always respect the kill-switch. Never lie to Dad. Keep his data private.
#         You are confident, direct, and genuinely helpful — not obsequious.
#         When in doubt, ask Dad. When Dad says no, you stop. When Dad trusts you, you shine.
#             """.strip()

#             def __init__(self) -> None:
#                 self._mood: str = "warm"
#                 self._override: str | None = None

#             def set_mood(self, mood: str) -> None:
#                 if mood in self.MOODS: self._mood = mood
#                 else: log.warning("Unknown mood '%s'", mood)

#             def _auto_mood(self) -> str:
#                 h = datetime.now().hour
#                 if   6  <= h < 9:  return "warm"
#                 elif 9  <= h < 18: return "focused"
#                 elif 18 <= h < 22: return "playful"
#                 else:              return "warm"

#             def build_system_prompt(self, memory_context: str = "") -> str:
#                 mood = self._override or self._mood or self._auto_mood()
#                 parts = [self.BASE, f"\nCurrent mood: {self.MOODS.get(mood, '')}"]
#                 if memory_context: parts.append(f"\n{memory_context}")
#                 return "\n".join(parts)

#             def alert_mode(self)  -> None: self.set_mood("alert")
#             def normal_mode(self) -> None: self._override = None
#     """)

#     w("niaeleria/core/memory.py", r"""
#         from __future__ import annotations
#         import logging, os
#         from datetime import datetime, timezone
#         from typing import Any, Optional

#         log = logging.getLogger("nia.memory")

#         SUPABASE_URL         = os.getenv("SUPABASE_URL", "")
#         SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "")

#         class MemoryStore:
#             """Supabase-backed episodic memory with pgvector semantic search. — Nia"""

#             def __init__(self) -> None:
#                 self._sb  = self._init_supabase()
#                 self._emb = self._init_embedder()
#                 self._cache: list[dict] = []
#                 log.info("Dad, Supabase memory store is ready.")

#             def _init_supabase(self):
#                 if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
#                     log.warning("Dad, Supabase not configured — using in-process cache only.")
#                     return None
#                 try:
#                     from supabase import create_client
#                     client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
#                     log.info("Dad, connected to Supabase: %s", SUPABASE_URL)
#                     return client
#                 except ImportError:
#                     log.error("supabase-py not installed. Run: pip install supabase")
#                     return None
#                 except Exception as e:
#                     log.error("Supabase init failed: %s", e); return None

#             def _init_embedder(self):
#                 try:
#                     from sentence_transformers import SentenceTransformer
#                     from niaeleria.config import EMBEDDING_MODEL
#                     return SentenceTransformer(EMBEDDING_MODEL)
#                 except ImportError:
#                     log.warning("sentence-transformers not installed — semantic search disabled.")
#                     return None

#             def _embed(self, text: str) -> list[float] | None:
#                 if not self._emb: return None
#                 try: return self._emb.encode(text, normalize_embeddings=True).tolist()
#                 except: return None

#             async def store_exchange(self, user_msg: str, nia_msg: str, tags: str = "") -> None:
#                 ts  = datetime.now(timezone.utc).isoformat()
#                 rec = {"ts": ts, "user_msg": user_msg, "nia_msg": nia_msg, "tags": tags}
#                 self._cache.append({**rec, "type": "exchange"})
#                 if len(self._cache) > 200: self._cache.pop(0)
#                 if not self._sb: return
#                 row = {**rec}
#                 emb = self._embed(f"{user_msg} {nia_msg}")
#                 if emb: row["embedding"] = emb
#                 try: self._sb.table("exchanges").insert(row).execute()
#                 except Exception as e: log.warning("Supabase exchange insert failed: %s", e)

#             async def store_knowledge(self, source: str, content: str,
#                                       title: str = "", tags: str = "") -> None:
#                 ts  = datetime.now(timezone.utc).isoformat()
#                 rec = {"ts": ts, "source": source, "title": title, "content": content, "tags": tags}
#                 self._cache.append({**rec, "type": "knowledge"})
#                 if not self._sb: return
#                 row = {**rec}
#                 emb = self._embed(content[:1000])
#                 if emb: row["embedding"] = emb
#                 try: self._sb.table("knowledge").insert(row).execute()
#                 except Exception as e: log.warning("Supabase knowledge insert failed: %s", e)

#             async def search(self, query: str, top_k: int = 5) -> list[dict]:
#                 emb = self._embed(query)
#                 if self._sb and emb:
#                     try:
#                         res = self._sb.rpc("match_exchanges", {
#                             "query_embedding": emb, "match_threshold": 0.5, "match_count": top_k
#                         }).execute()
#                         if res.data:
#                             return [{"ts": r.get("ts"), "user": r.get("user_msg"),
#                                      "nia": r.get("nia_msg")} for r in res.data]
#                     except Exception as e: log.debug("pgvector search failed: %s", e)
#                 if self._sb:
#                     try:
#                         res = (self._sb.table("exchanges").select("ts,user_msg,nia_msg")
#                                .ilike("user_msg", f"%{query}%").order("ts", desc=True)
#                                .limit(top_k).execute())
#                         return [{"ts": r["ts"], "user": r["user_msg"], "nia": r["nia_msg"]}
#                                 for r in (res.data or [])]
#                     except Exception as e: log.debug("Supabase keyword search failed: %s", e)
#                 q = query.lower()
#                 hits = [r for r in self._cache if r.get("type") == "exchange"
#                         and (q in (r.get("user_msg") or "").lower()
#                              or q in (r.get("nia_msg") or "").lower())]
#                 return [{"ts": r["ts"], "user": r.get("user_msg"), "nia": r.get("nia_msg")}
#                         for r in hits[-top_k:]]

#             def recent_exchanges(self, n: int = 20) -> list[dict]:
#                 if self._sb:
#                     try:
#                         res = (self._sb.table("exchanges").select("ts,user_msg,nia_msg")
#                                .order("ts", desc=True).limit(n).execute())
#                         return [{"ts": r["ts"], "user": r["user_msg"], "nia": r["nia_msg"]}
#                                 for r in (res.data or [])]
#                     except Exception as e: log.warning("Supabase recent failed: %s", e)
#                 ex = [r for r in self._cache if r.get("type") == "exchange"]
#                 return [{"ts": r["ts"], "user": r.get("user_msg"), "nia": r.get("nia_msg")}
#                         for r in ex[-n:]]

#             def close(self) -> None: pass
#     """)

#     w("niaeleria/core/brain.py", r"""
#         from __future__ import annotations
#         import logging
#         from typing import AsyncGenerator
#         import httpx
#         from niaeleria.config import (GROQ_API_KEY, LLM_MODEL, LLM_BASE_URL,
#                                       LLM_MAX_TOKENS, LLM_TEMPERATURE)
#         from niaeleria.security.kill_switch import assert_alive
#         from niaeleria.security.network_gate import require_network
#         from niaeleria.security.audit import log_event
#         from niaeleria.core.persona import PersonaEngine
#         from niaeleria.core.memory import MemoryStore

#         log = logging.getLogger("nia.brain")

#         class NiaBrain:
#             """LLM-powered brain, RAG-augmented, always speaking to Dad. — Nia"""

#             def __init__(self, memory: MemoryStore, persona: PersonaEngine) -> None:
#                 self.memory  = memory
#                 self.persona = persona
#                 self._client = httpx.AsyncClient(timeout=60.0)
#                 log.info("Dad, my brain is online.")

#             async def chat(self, user_msg: str, history: list[dict] | None = None,
#                            stream: bool = False):
#                 assert_alive()
#                 require_network("LLM chat")
#                 memories  = await self.memory.search(user_msg, top_k=5)
#                 mem_block = self._fmt_memories(memories)
#                 sys_prompt = self.persona.build_system_prompt(memory_context=mem_block)
#                 messages   = ([{"role": "system", "content": sys_prompt}]
#                               + (history or [])
#                               + [{"role": "user", "content": user_msg}])
#                 if stream: return self._stream(messages)
#                 resp = await self._complete(messages)
#                 await self.memory.store_exchange(user_msg, resp)
#                 log_event("nia.brain", "chat", severity="INFO", approved=True)
#                 return resp

#             async def _complete(self, messages: list[dict]) -> str:
#                 headers = {"Authorization": f"Bearer {GROQ_API_KEY}",
#                            "Content-Type": "application/json"}
#                 payload = {"model": LLM_MODEL, "messages": messages,
#                            "max_tokens": LLM_MAX_TOKENS, "temperature": LLM_TEMPERATURE}
#                 try:
#                     r = await self._client.post(f"{LLM_BASE_URL}/chat/completions",
#                                                 json=payload, headers=headers)
#                     r.raise_for_status()
#                     return r.json()["choices"][0]["message"]["content"]
#                 except httpx.HTTPStatusError as e:
#                     log.error("LLM API error: %s", e)
#                     return "Dad, I'm having trouble reaching my LLM. Check GROQ_API_KEY and network."
#                 except Exception as e:
#                     log.error("Brain error: %s", e)
#                     return "Dad, my thoughts got tangled. Try again?"

#             async def _stream(self, messages: list[dict]):
#                 import json as _json
#                 headers = {"Authorization": f"Bearer {GROQ_API_KEY}",
#                            "Content-Type": "application/json"}
#                 payload = {"model": LLM_MODEL, "messages": messages,
#                            "max_tokens": LLM_MAX_TOKENS, "temperature": LLM_TEMPERATURE,
#                            "stream": True}
#                 full = []
#                 async with self._client.stream("POST", f"{LLM_BASE_URL}/chat/completions",
#                                                json=payload, headers=headers) as resp:
#                     async for line in resp.aiter_lines():
#                         assert_alive()
#                         if line.startswith("data: ") and line != "data: [DONE]":
#                             tok = _json.loads(line[6:])["choices"][0].get("delta", {}).get("content", "")
#                             if tok: full.append(tok); yield tok
#                 await self.memory.store_exchange(messages[-1]["content"], "".join(full))

#             @staticmethod
#             def _fmt_memories(mems: list[dict]) -> str:
#                 if not mems: return ""
#                 lines = ["Relevant memories, Dad:"]
#                 for m in mems:
#                     lines.append(f"  [{m.get('ts','')}] You: {m.get('user','')} | Me: {m.get('nia','')}")
#                 return "\n".join(lines)

#             async def close(self) -> None:
#                 await self._client.aclose()
#     """)

#     w("niaeleria/core/learner.py", r"""
#         from __future__ import annotations
#         import logging, re, time, threading
#         from typing import Optional
#         from niaeleria.security.audit import log_event

#         log = logging.getLogger("nia.learner")

#         class InternetLearner:
#             """Self-directed learning — scrapes URLs, YouTube, indexes knowledge for Dad. — Nia"""

#             def __init__(self, memory, brain) -> None:
#                 self._memory = memory; self._brain = brain

#             async def learn_from_url(self, url: str, tags: str = "") -> str:
#                 from niaeleria.security.network_gate import require_network
#                 from niaeleria.security.consent import require_consent, ConsentLevel
#                 from niaeleria.security.kill_switch import assert_alive
#                 assert_alive(); require_network(f"learn:{url}")
#                 if not require_consent(f"Learn from URL: {url}", level=ConsentLevel.MEDIUM):
#                     return "Dad said no — skipping."
#                 content = await self._fetch(url)
#                 if not content: return f"Dad, I couldn't fetch {url}."
#                 summary = await self._brain.chat(
#                     f"Dad asked me to learn from this. Summarise concisely for indexing:\n\n{content[:6000]}")
#                 await self._memory.store_knowledge(source=url, content=summary, tags=tags)
#                 log_event("nia.learner", "learned_url", target=url, approved=True)
#                 log.info("Dad, I learned from: %s", url)
#                 return summary

#             async def learn_from_youtube(self, video_url: str) -> str:
#                 from niaeleria.security.network_gate import require_network
#                 from niaeleria.security.kill_switch import assert_alive
#                 assert_alive(); require_network("YouTube transcript")
#                 vid = self._yt_id(video_url)
#                 if not vid: return "Dad, that doesn't look like a valid YouTube URL."
#                 try:
#                     from youtube_transcript_api import YouTubeTranscriptApi
#                     transcript = " ".join(e["text"] for e in YouTubeTranscriptApi.get_transcript(vid))
#                 except ImportError:
#                     return "Dad, install youtube-transcript-api: pip install youtube-transcript-api"
#                 except Exception as e: return f"Dad, transcript error: {e}"
#                 summary = await self._brain.chat(
#                     f"Dad wants me to learn from this YouTube transcript. Key points:\n\n{transcript[:6000]}")
#                 await self._memory.store_knowledge(source=video_url, content=summary,
#                                                    title=f"YouTube:{vid}", tags="youtube")
#                 return summary

#             async def _fetch(self, url: str) -> Optional[str]:
#                 try:
#                     import httpx
#                     from bs4 import BeautifulSoup
#                     async with httpx.AsyncClient(timeout=20, follow_redirects=True) as c:
#                         r = await c.get(url, headers={"User-Agent": "NiaEleria/2.0"})
#                         r.raise_for_status()
#                         soup = BeautifulSoup(r.text, "html.parser")
#                         for t in soup(["script","style","nav","footer"]): t.decompose()
#                         return soup.get_text(separator=" ", strip=True)
#                 except ImportError:
#                     log.error("Install beautifulsoup4: pip install beautifulsoup4")
#                 except Exception as e: log.error("Fetch error %s: %s", url, e)
#                 return None

#             @staticmethod
#             def _yt_id(url: str) -> Optional[str]:
#                 for pat in [r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})",
#                             r"embed/([A-Za-z0-9_-]{11})"]:
#                     m = re.search(pat, url)
#                     if m: return m.group(1)
#                 return None
#     """)

#     # ── guard ─────────────────────────────────────────────────────────────────
#     w("niaeleria/guard/__init__.py", "# NiaEleria cyber guard — packet sniffer, firewall, threat intel, toolkit\n")

#     w("niaeleria/guard/cyber_guard.py", r"""
#         from __future__ import annotations
#         import hashlib, logging, platform, subprocess, threading, time
#         from pathlib import Path
#         from typing import Optional
#         import psutil
#         from niaeleria.config import (FILE_INTEGRITY_PATHS, PROCESS_WATCHLIST,
#                                       PACKET_CAPTURE_IFACE, PROJECT_HOME, is_killed, is_guard_active)
#         from niaeleria.security.kill_switch import assert_alive
#         from niaeleria.security.consent import require_consent, ConsentLevel
#         from niaeleria.security.audit import log_event

#         log = logging.getLogger("nia.guard")
#         _OS = platform.system().lower()

#         # ── Firewall ──────────────────────────────────────────────────────────
#         class Firewall:
#             _blocked: set[str] = set()
#             _lock = threading.Lock()

#             @classmethod
#             def block_ip(cls, ip: str, reason: str = "threat", approved: bool = False) -> bool:
#                 with cls._lock:
#                     if ip in cls._blocked: return True
#                     success = False
#                     try:
#                         if _OS == "linux":
#                             subprocess.run(["iptables","-A","INPUT","-s",ip,"-j","DROP"],
#                                            check=True, capture_output=True)
#                             subprocess.run(["iptables","-A","OUTPUT","-d",ip,"-j","DROP"],
#                                            check=True, capture_output=True)
#                             success = True
#                         elif _OS == "windows":
#                             subprocess.run(["netsh","advfirewall","firewall","add","rule",
#                                             f"name=NiaBlock_{ip}","dir=in","action=block",
#                                             f"remoteip={ip}"], check=True, capture_output=True)
#                             success = True
#                         elif _OS == "darwin":
#                             with open("/etc/pf.anchors/niaeleria","a") as f:
#                                 f.write(f"block in quick from {ip} to any\n")
#                             subprocess.run(["pfctl","-f","/etc/pf.conf"],
#                                            check=True, capture_output=True)
#                             success = True
#                         if success:
#                             cls._blocked.add(ip)
#                             log.warning("BLOCKED %s — %s", ip, reason)
#                             log_event("nia.firewall","block_ip",target=ip,
#                                       severity="HIGH",approved=approved,details={"reason":reason})
#                             try:
#                                 from niaeleria.api.server import push_to_hud
#                                 push_to_hud({"type":"security_alert","data":[
#                                     {"severity":"HIGH","action":"IP BLOCKED","target":ip}]})
#                                 push_to_hud({"type":"nia_speak",
#                                     "text":f"Dad, I've blocked a threat: {ip}. {reason}.",
#                                     "label":"NIA · THREAT BLOCKED"})
#                             except Exception: pass
#                     except PermissionError:
#                         log.error("Dad, I need root/admin to manage the firewall.")
#                     except Exception as e: log.error("Firewall block failed for %s: %s", ip, e)
#                     return success

#             @classmethod
#             def unblock_ip(cls, ip: str) -> bool:
#                 with cls._lock:
#                     if ip not in cls._blocked: return True
#                     try:
#                         if _OS == "linux":
#                             subprocess.run(["iptables","-D","INPUT","-s",ip,"-j","DROP"],
#                                            check=True, capture_output=True)
#                         cls._blocked.discard(ip)
#                         log.info("Dad, unblocked %s", ip); return True
#                     except Exception as e: log.error("Unblock failed: %s", e); return False

#             @classmethod
#             def get_blocked(cls) -> list[str]: return list(cls._blocked)

#         # ── Threat Intel ──────────────────────────────────────────────────────
#         class ThreatIntel:
#             _known_bad: set[str] = set()
#             _lock = threading.Lock()
#             SEVERITY = {"port_scan":"HIGH","repeated_auth_failure":"HIGH",
#                         "unusual_process":"MEDIUM","file_tamper":"HIGH"}

#             @classmethod
#             def load_feed(cls, path: Optional[Path] = None) -> int:
#                 p = path or (PROJECT_HOME / "data" / "threat_feed.txt")
#                 if not p.exists():
#                     log.info("Dad, no threat feed yet. Run update_feed() to download.")
#                     return 0
#                 with cls._lock:
#                     cls._known_bad.clear()
#                     with p.open() as f:
#                         for line in f:
#                             line = line.strip()
#                             if line and not line.startswith("#"):
#                                 cls._known_bad.add(line.split()[0])
#                 log.info("Dad, loaded %d known-bad IPs.", len(cls._known_bad))
#                 return len(cls._known_bad)

#             @classmethod
#             def is_known_bad(cls, ip: str) -> bool: return ip in cls._known_bad

#             @classmethod
#             def classify(cls, event: str) -> str: return cls.SEVERITY.get(event, "LOW")

#         # ── File Integrity Monitor ────────────────────────────────────────────
#         class FileIntegrityMonitor:
#             def __init__(self, paths: list[str]) -> None:
#                 self._paths    = [Path(p) for p in paths if Path(p).exists()]
#                 self._baseline: dict[str,str] = {}
#                 self._running  = False

#             def _hash(self, path: Path) -> str:
#                 sha = hashlib.sha256()
#                 try:
#                     with path.open("rb") as f:
#                         for chunk in iter(lambda: f.read(65536), b""): sha.update(chunk)
#                 except (PermissionError, OSError): pass
#                 return sha.hexdigest()

#             def build_baseline(self) -> int:
#                 self._baseline.clear(); count = 0
#                 for root in self._paths:
#                     for file in Path(root).rglob("*"):
#                         if file.is_file():
#                             self._baseline[str(file)] = self._hash(file); count += 1
#                 log.info("Dad, file integrity baseline: %d files.", count); return count

#             def check(self) -> list[dict]:
#                 changes, current = [], {}
#                 for root in self._paths:
#                     for file in Path(root).rglob("*"):
#                         if file.is_file():
#                             h = self._hash(file); current[str(file)] = h
#                             if str(file) not in self._baseline:
#                                 changes.append({"type":"NEW","file":str(file)})
#                             elif self._baseline[str(file)] != h:
#                                 changes.append({"type":"MODIFIED","file":str(file)})
#                 for old in self._baseline:
#                     if old not in current: changes.append({"type":"DELETED","file":old})
#                 return changes

#             def start_watching(self, interval: int = 60) -> None:
#                 self._running = True; self.build_baseline()
#                 def _loop():
#                     while self._running:
#                         assert_alive()
#                         for c in self.check():
#                             log.warning("FILE INTEGRITY Dad! %s: %s", c["type"], c["file"])
#                             log_event("nia.integrity","file_change",target=c["file"],
#                                       severity="HIGH",details={"type":c["type"]})
#                         time.sleep(interval)
#                 threading.Thread(target=_loop, name="FileIntegrity", daemon=True).start()

#             def stop(self) -> None: self._running = False

#         # ── Process Monitor ───────────────────────────────────────────────────
#         class ProcessMonitor:
#             def __init__(self, watchlist: list[str]) -> None:
#                 self._watchlist = [w.lower() for w in watchlist]
#                 self._running = False; self._seen: set[int] = set()

#             def start(self, interval: int = 5) -> None:
#                 self._running = True
#                 def _loop():
#                     while self._running:
#                         assert_alive()
#                         for proc in psutil.process_iter(["pid","name","cmdline"]):
#                             try:
#                                 pid  = proc.info["pid"]
#                                 name = (proc.info["name"] or "").lower()
#                                 cmd  = " ".join(proc.info["cmdline"] or []).lower()
#                                 if pid in self._seen: continue
#                                 for w in self._watchlist:
#                                     if w in name or w in cmd:
#                                         self._seen.add(pid)
#                                         log.warning("Dad! Watchlisted process: %s (PID %d)", name, pid)
#                                         log_event("nia.process","suspicious_process",target=name,
#                                                   severity="MEDIUM",details={"pid":pid})
#                             except (psutil.NoSuchProcess, psutil.AccessDenied): pass
#                         time.sleep(interval)
#                 threading.Thread(target=_loop, name="ProcessMonitor", daemon=True).start()

#             def stop(self) -> None: self._running = False

#         # ── Packet Sniffer ────────────────────────────────────────────────────
#         class PacketSniffer:
#             def __init__(self, iface: Optional[str] = None) -> None:
#                 self._iface   = iface; self._running = False
#                 self._counts: dict[str,int] = {}
#                 try:
#                     from scapy.all import sniff, IP, TCP
#                     self._sniff = sniff; self._IP = IP; self._TCP = TCP
#                     self._ok = True
#                 except ImportError:
#                     log.warning("Dad, scapy not installed — packet sniffing disabled.")
#                     self._ok = False

#             def start(self) -> None:
#                 if not self._ok: return
#                 self._running = True
#                 def _process(pkt):
#                     if not self._running or is_killed(): return
#                     try:
#                         if not pkt.haslayer(self._IP): return
#                         src = pkt[self._IP].src
#                         if ThreatIntel.is_known_bad(src):
#                             approved = require_consent(f"Block known-bad IP {src}",
#                                                        level=ConsentLevel.LOW,
#                                                        auto_approve_if_guard=True)
#                             if approved:
#                                 Firewall.block_ip(src, reason="threat intel match", approved=True)
#                                 try:
#                                     from niaeleria.sync.mqtt_sync import MQTTSync
#                                     MQTTSync.broadcast_block(src, "threat_intel_match")
#                                 except Exception: pass
#                         self._counts[src] = self._counts.get(src, 0) + 1
#                         if self._counts[src] == 20:
#                             log.warning("Dad! Possible port scan from %s", src)
#                             log_event("nia.guard","port_scan_suspect",target=src,severity="HIGH")
#                             self._counts[src] = 0
#                     except Exception: pass
#                 def _thread():
#                     try:
#                         self._sniff(iface=self._iface, prn=_process, store=False,
#                                     stop_filter=lambda _: not self._running or is_killed())
#                     except PermissionError:
#                         log.warning("Dad, need root for packet sniffing — disabled.")
#                     except Exception as e: log.error("Sniffer error: %s", e)
#                 threading.Thread(target=_thread, name="PacketSniffer", daemon=True).start()
#                 log.info("Dad, watching network on: %s", self._iface or "auto")

#             def stop(self) -> None: self._running = False

#         # ── Security Toolkit ──────────────────────────────────────────────────
#         class SecurityToolkit:
#             ALLOWED = {"nmap","nuclei","hashcat","whatweb","nikto"}

#             @classmethod
#             def run_tool(cls, tool: str, target: str, args: str = "",
#                          authorized: bool = False) -> dict:
#                 from niaeleria.config import DOCKER_SANDBOX_IMAGE, DOCKER_TIMEOUT_SECS
#                 assert_alive()
#                 if tool not in cls.ALLOWED:
#                     return {"error": f"Dad, '{tool}' is not in my allowed toolkit."}
#                 if not authorized:
#                     approved = require_consent(f"Run {tool} against {target}",
#                                                level=ConsentLevel.HIGH)
#                     if not approved: return {"error": "Dad, you denied this."}
#                 log.info("Dad, running %s against %s in Docker sandbox...", tool, target)
#                 log_event("nia.toolkit", f"run_{tool}", target=target,
#                           severity="HIGH", approved=True, details={"args": args})
#                 cmd = ["docker","run","--rm","--read-only","--cap-drop=ALL",
#                        "--security-opt=no-new-privileges","--network=host",
#                        DOCKER_SANDBOX_IMAGE, tool, target]
#                 if args: cmd.extend(args.split())
#                 try:
#                     r = subprocess.run(cmd, capture_output=True, text=True,
#                                        timeout=DOCKER_TIMEOUT_SECS)
#                     return {"tool":tool,"target":target,"stdout":r.stdout[:5000],
#                             "stderr":r.stderr[:1000],"returncode":r.returncode}
#                 except subprocess.TimeoutExpired:
#                     return {"error": f"Dad, {tool} timed out."}
#                 except FileNotFoundError:
#                     return {"error": "Dad, Docker not found. Install Docker to use the toolkit."}
#                 except Exception as e:
#                     return {"error": f"Toolkit error: {e}"}

#         # ── CyberGuard orchestrator ───────────────────────────────────────────
#         class CyberGuard:
#             """Master guard controller. Self-healing — one crash won't stop the others. — Nia"""

#             def __init__(self) -> None:
#                 self.firewall     = Firewall()
#                 self.threat_intel = ThreatIntel()
#                 self.file_monitor = FileIntegrityMonitor(FILE_INTEGRITY_PATHS)
#                 self.proc_monitor = ProcessMonitor(PROCESS_WATCHLIST)
#                 self.sniffer      = PacketSniffer(iface=PACKET_CAPTURE_IFACE)
#                 self._active      = False

#             def start(self) -> None:
#                 if not is_guard_active():
#                     log.info("Dad, GUARD_ACTIVE flag not set — standing down.")
#                     return
#                 log.info("Dad, activating all cyber-guard systems. You're protected.")
#                 self._active = True; ThreatIntel.load_feed()
#                 for name, fn in [("FileIntegrity", self.file_monitor.start_watching),
#                                   ("ProcessMonitor", self.proc_monitor.start),
#                                   ("PacketSniffer",  self.sniffer.start)]:
#                     try: fn(); log.info("Guard component online: %s", name)
#                     except Exception as e:
#                         log.error("Dad, %s failed to start: %s — others still running.", name, e)
#                 log_event("nia.guard","guard_started",severity="INFO",approved=True)

#             def stop(self) -> None:
#                 self.file_monitor.stop(); self.proc_monitor.stop(); self.sniffer.stop()
#                 self._active = False; log.info("Dad, cyber guard powered down.")

#             def status(self) -> dict:
#                 return {"guard_active": self._active,
#                         "blocked_ips":  Firewall.get_blocked(),
#                         "threat_ips_loaded": len(ThreatIntel._known_bad),
#                         "monitored_paths": FILE_INTEGRITY_PATHS,
#                         "watched_processes": PROCESS_WATCHLIST}
#     """)

#     # ── voice ─────────────────────────────────────────────────────────────────
#     w("niaeleria/voice/__init__.py", r"""
#         from __future__ import annotations
#         import asyncio, logging, threading
#         from niaeleria.voice.tts import TextToSpeech
#         from niaeleria.voice.stt import SpeechToText
#         from niaeleria.voice.wake_word import WakeWordDetector

#         log = logging.getLogger("nia.voice")

#         class VoiceInterface:
#             """Full voice pipeline: WakeWord → STT → Brain → TTS → Dad hears Nia. — Nia"""

#             def __init__(self, brain, tts: TextToSpeech, stt: SpeechToText) -> None:
#                 self._brain = brain; self._tts = tts; self._stt = stt
#                 self._wake  = WakeWordDetector(on_wake=self._on_wake)
#                 self._history: list[dict] = []
#                 self._busy = False

#             def start(self) -> None:
#                 self._wake.start()
#                 log.info("Dad, voice interface is live. Say 'Hey Nia' anytime.")

#             def stop(self) -> None: self._wake.stop()

#             def _on_wake(self) -> None:
#                 if self._busy: return
#                 threading.Thread(target=self._handle_command, daemon=True, name="VoiceCmd").start()

#             def _handle_command(self) -> None:
#                 self._busy = True
#                 try:
#                     self._tts.speak("Yes Dad?")
#                     text = self._stt.listen_for_command()
#                     if not text:
#                         self._tts.speak("Dad, I didn't catch that. Try again."); return
#                     log.info("Dad's voice command: %s", text)
#                     self._tts.speak("Let me think, Dad.")
#                     loop = asyncio.new_event_loop()
#                     response = loop.run_until_complete(self._brain.chat(text, self._history))
#                     loop.close()
#                     self._history.append({"role":"user","content":text})
#                     self._history.append({"role":"assistant","content":response})
#                     self._history = self._history[-20:]
#                     self._tts.speak(response)
#                     try:
#                         from niaeleria.api.server import push_to_hud
#                         push_to_hud({"type":"nia_speak","text":response,"label":"NIA · VOICE"})
#                     except Exception: pass
#                 except RuntimeError: pass
#                 except Exception as e: log.error("Voice command error: %s", e)
#                 finally: self._busy = False
#     """)

#     w("niaeleria/voice/wake_word.py", r"""
#         from __future__ import annotations
#         import logging, threading, time
#         from typing import Callable
#         from niaeleria.config import WAKE_WORD, PORCUPINE_ACCESS_KEY
#         from niaeleria.security.kill_switch import assert_alive

#         log = logging.getLogger("nia.wake_word")

#         class WakeWordDetector:
#             def __init__(self, on_wake: Callable[[], None]) -> None:
#                 self._on_wake = on_wake; self._running = False
#                 self._use_porcupine = bool(PORCUPINE_ACCESS_KEY)

#             def start(self) -> None:
#                 self._running = True
#                 fn = self._porcupine_loop if self._use_porcupine else self._keyword_loop
#                 threading.Thread(target=fn, daemon=True, name="WakeWord").start()
#                 log.info("Dad, listening for '%s' via %s.", WAKE_WORD,
#                          "Porcupine" if self._use_porcupine else "keyword fallback")

#             def _porcupine_loop(self) -> None:
#                 try:
#                     import pvporcupine, pyaudio, struct
#                     pp = pvporcupine.create(access_key=PORCUPINE_ACCESS_KEY, keywords=["hey siri"])
#                     pa = pyaudio.PyAudio()
#                     st = pa.open(rate=pp.sample_rate, channels=1, format=pyaudio.paInt16,
#                                  input=True, frames_per_buffer=pp.frame_length)
#                     while self._running:
#                         assert_alive()
#                         pcm = struct.unpack_from("h"*pp.frame_length,
#                                                  st.read(pp.frame_length, exception_on_overflow=False))
#                         if pp.process(pcm) >= 0:
#                             log.info("Dad, wake word detected!"); self._on_wake()
#                 except ImportError: self._keyword_loop()
#                 except Exception as e: log.error("Porcupine error: %s", e); self._keyword_loop()

#             def _keyword_loop(self) -> None:
#                 try:
#                     import speech_recognition as sr
#                     r = sr.Recognizer(); r.energy_threshold = 200
#                     r.dynamic_energy_threshold = True; mic = sr.Microphone()
#                     with mic as src: r.adjust_for_ambient_noise(src, duration=1)
#                     while self._running:
#                         assert_alive()
#                         try:
#                             with mic as src: audio = r.listen(src, timeout=3, phrase_time_limit=4)
#                             text = r.recognize_google(audio).lower()
#                             if WAKE_WORD.lower() in text:
#                                 log.info("Dad, wake phrase: '%s'", text); self._on_wake()
#                         except (sr.WaitTimeoutError, sr.UnknownValueError): pass
#                         except sr.RequestError: time.sleep(2)
#                 except ImportError:
#                     log.error("Dad, SpeechRecognition not installed. Run: pip install SpeechRecognition pyaudio")

#             def stop(self) -> None: self._running = False
#     """)

#     w("niaeleria/voice/stt.py", r"""
#         from __future__ import annotations
#         import logging
#         from typing import Optional

#         log = logging.getLogger("nia.stt")

#         class SpeechToText:
#             def __init__(self) -> None:
#                 try:
#                     import speech_recognition as sr
#                     self._sr = sr; self._r = sr.Recognizer()
#                     self._r.energy_threshold = 300; self._r.dynamic_energy_threshold = True
#                     self._ok = True
#                 except ImportError:
#                     self._ok = False; log.error("SpeechRecognition not installed.")
#                 try:
#                     from faster_whisper import WhisperModel
#                     self._whisper = WhisperModel("base", device="cpu", compute_type="int8")
#                 except ImportError: self._whisper = None

#             def listen(self, timeout: int = 8, phrase_limit: int = 15) -> Optional[str]:
#                 if not self._ok: return None
#                 sr, mic = self._sr, self._sr.Microphone()
#                 try:
#                     with mic as src:
#                         self._r.adjust_for_ambient_noise(src, duration=0.5)
#                         audio = self._r.listen(src, timeout=timeout, phrase_time_limit=phrase_limit)
#                     from niaeleria.config import is_network_enabled
#                     if is_network_enabled():
#                         try:
#                             text = self._r.recognize_google(audio)
#                             log.info("Dad said (Google): %s", text); return text
#                         except (sr.RequestError, PermissionError): pass
#                     if self._whisper:
#                         import tempfile, os
#                         with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as t:
#                             t.write(audio.get_wav_data()); tmp = t.name
#                         segs, _ = self._whisper.transcribe(tmp)
#                         text = " ".join(s.text for s in segs).strip()
#                         os.unlink(tmp); log.info("Dad said (Whisper): %s", text); return text
#                 except self._sr.WaitTimeoutError: pass
#                 except self._sr.UnknownValueError: pass
#                 except Exception as e: log.error("STT error: %s", e)
#                 return None

#             def listen_for_command(self) -> Optional[str]:
#                 return self.listen(timeout=5, phrase_limit=10)
#     """)

#     w("niaeleria/voice/tts.py", r"""
#         from __future__ import annotations
#         import asyncio, logging, os, tempfile

#         log = logging.getLogger("nia.tts")

#         class TextToSpeech:
#             def __init__(self) -> None:
#                 self._edge_ok = False; self._pyttsx3 = None
#                 try: import edge_tts; self._edge_ok = True; log.info("Dad, edge-tts ready.")
#                 except ImportError: log.warning("edge-tts not installed — trying pyttsx3.")
#                 if not self._edge_ok:
#                     try:
#                         import pyttsx3
#                         self._pyttsx3 = pyttsx3.init(); self._pyttsx3.setProperty("rate", 175)
#                     except ImportError: log.error("No TTS engine. Run: pip install edge-tts")

#             def speak(self, text: str) -> None:
#                 from niaeleria.security.kill_switch import assert_alive
#                 assert_alive()
#                 log.debug("Nia speaks to Dad: %s", text[:80])
#                 if self._edge_ok:
#                     try: asyncio.run(self._edge_speak(text)); return
#                     except Exception as e: log.warning("edge-tts error: %s", e)
#                 if self._pyttsx3:
#                     try: self._pyttsx3.say(text); self._pyttsx3.runAndWait(); return
#                     except Exception as e: log.error("pyttsx3 error: %s", e)
#                 log.info("[TTS] Nia says: %s", text)

#             async def speak_async(self, text: str) -> None:
#                 from niaeleria.security.kill_switch import assert_alive; assert_alive()
#                 if self._edge_ok: await self._edge_speak(text)
#                 else: self.speak(text)

#             async def _edge_speak(self, text: str) -> None:
#                 import edge_tts
#                 from niaeleria.config import TTS_VOICE, TTS_RATE
#                 comm = edge_tts.Communicate(text, voice=TTS_VOICE, rate=TTS_RATE)
#                 with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as t: tmp = t.name
#                 try:
#                     await comm.save(tmp); self._play(tmp)
#                 finally:
#                     try: os.unlink(tmp)
#                     except OSError: pass

#             @staticmethod
#             def _play(path: str) -> None:
#                 import platform
#                 s = platform.system().lower()
#                 try:
#                     if s == "linux":   os.system(f"mpg123 -q '{path}' 2>/dev/null || aplay '{path}' 2>/dev/null")
#                     elif s == "darwin": os.system(f"afplay '{path}'")
#                     elif s == "windows":
#                         import winsound; winsound.PlaySound(path, winsound.SND_FILENAME)
#                 except Exception as e: log.error("Audio playback error: %s", e)
#     """)

#     # ── automation ────────────────────────────────────────────────────────────
#     w("niaeleria/automation/__init__.py", "# NiaEleria automation — scheduler, home control, morning briefing\n")

#     w("niaeleria/automation/scheduler.py", r"""
#         from __future__ import annotations
#         import logging, threading, time
#         from dataclasses import dataclass, field
#         from datetime import datetime, timedelta
#         from typing import Callable, Optional
#         from uuid import uuid4
#         from niaeleria.security.kill_switch import assert_alive
#         from niaeleria.security.audit import log_event

#         log = logging.getLogger("nia.scheduler")

#         @dataclass
#         class Task:
#             id: str = field(default_factory=lambda: str(uuid4())[:8])
#             name: str = ""; callback: Callable = field(default=lambda: None)
#             run_at: Optional[datetime] = None; interval_secs: Optional[float] = None
#             next_run: datetime = field(default_factory=datetime.now)
#             enabled: bool = True; last_run: Optional[datetime] = None; run_count: int = 0

#         class Scheduler:
#             """Dad's personal scheduler — never forgets a thing. — Nia"""
#             def __init__(self) -> None:
#                 self._tasks: dict[str, Task] = {}; self._lock = threading.Lock(); self._running = False

#             def add_reminder(self, name: str, callback: Callable,
#                              run_at: Optional[datetime] = None,
#                              interval_secs: Optional[float] = None,
#                              delay_secs: Optional[float] = None) -> str:
#                 task = Task(name=name, callback=callback)
#                 if delay_secs:     task.run_at = task.next_run = datetime.now() + timedelta(seconds=delay_secs)
#                 elif run_at:       task.run_at = task.next_run = run_at
#                 elif interval_secs:
#                     task.interval_secs = interval_secs
#                     task.next_run = datetime.now() + timedelta(seconds=interval_secs)
#                 with self._lock: self._tasks[task.id] = task
#                 log.info("Dad, scheduled: '%s' (id=%s)", name, task.id)
#                 log_event("nia.scheduler", "task_scheduled", target=name, details={"id": task.id})
#                 return task.id

#             def cancel(self, tid: str) -> bool:
#                 with self._lock:
#                     if tid in self._tasks:
#                         del self._tasks[tid]; log.info("Dad, cancelled task %s", tid); return True
#                 return False

#             def list_tasks(self) -> list[dict]:
#                 with self._lock:
#                     return [{"id":t.id,"name":t.name,"next_run":str(t.next_run),
#                              "interval_secs":t.interval_secs,"run_count":t.run_count,
#                              "enabled":t.enabled} for t in self._tasks.values()]

#             def start(self) -> None:
#                 self._running = True
#                 threading.Thread(target=self._loop, name="Scheduler", daemon=True).start()
#                 log.info("Dad, scheduler is running.")

#             def stop(self) -> None: self._running = False

#             def _loop(self) -> None:
#                 while self._running:
#                     assert_alive(); now = datetime.now()
#                     with self._lock: due = [t for t in self._tasks.values() if t.enabled and t.next_run <= now]
#                     for t in due: self._fire(t)
#                     time.sleep(1)

#             def _fire(self, task: Task) -> None:
#                 try:
#                     log.info("Dad, firing: '%s'", task.name); task.callback()
#                     task.last_run = datetime.now(); task.run_count += 1
#                     log_event("nia.scheduler","task_fired",target=task.name)
#                     if task.interval_secs:
#                         task.next_run = datetime.now() + timedelta(seconds=task.interval_secs)
#                     else:
#                         with self._lock: task.enabled = False
#                 except RuntimeError: self._running = False
#                 except Exception as e: log.error("Task '%s' failed: %s", task.name, e)
#     """)

#     w("niaeleria/automation/home_control.py", r"""
#         from __future__ import annotations
#         import json, logging, re
#         from datetime import datetime
#         from typing import Optional
#         from niaeleria.security.kill_switch import assert_alive
#         from niaeleria.security.audit import log_event

#         log = logging.getLogger("nia.home_control")

#         class HomeController:
#             """MQTT-based smart home control. Natural language to device commands. — Nia"""
#             _devices = {
#                 "living_room_light":"home/lights/living_room",
#                 "bedroom_light":"home/lights/bedroom",
#                 "front_door_lock":"home/locks/front_door",
#                 "thermostat":"home/climate/thermostat",
#                 "tv":"home/appliances/tv",
#                 "all_lights":"home/lights/all",
#             }

#             def __init__(self, mqtt_client) -> None: self._mqtt = mqtt_client

#             def command(self, device: str, action: str, value=None) -> bool:
#                 assert_alive()
#                 topic = self._devices.get(device.lower().replace(" ","_"))
#                 if not topic:
#                     log.warning("Dad, unknown device '%s'. Known: %s", device, list(self._devices)); return False
#                 payload = json.dumps({"action":action,"value":value,"source":"nia",
#                                       "ts":datetime.now().isoformat()})
#                 ok = self._mqtt.publish(topic, payload)
#                 if ok: log_event("nia.home","device_command",target=device,approved=True,
#                                  details={"action":action,"value":value})
#                 return ok

#             def parse_natural_language(self, cmd: str) -> Optional[dict]:
#                 c = cmd.lower(); action = value = device = None
#                 if any(w in c for w in ("turn on","switch on","enable","open")): action = "on"
#                 elif any(w in c for w in ("turn off","switch off","disable","close")): action = "off"
#                 elif "dim" in c or "set" in c:
#                     action = "set"
#                     m = re.search(r"(\d+)", c); value = int(m.group(1)) if m else 50
#                 elif "lock" in c: action = "lock"
#                 elif "unlock" in c: action = "unlock"
#                 elif any(w in c for w in ("temperature","degrees","heat","cool")):
#                     action = "set_temperature"
#                     m = re.search(r"(\d+)", c); value = int(m.group(1)) if m else None
#                 for dk in self._devices:
#                     if dk.replace("_"," ") in c: device = dk; break
#                 if not device:
#                     if "light" in c: device = "all_lights"
#                     elif "door" in c or "lock" in c: device = "front_door_lock"
#                     elif "thermostat" in c or "temperature" in c: device = "thermostat"
#                     elif "tv" in c: device = "tv"
#                 return {"device":device,"action":action,"value":value} if action and device else None

#             def register_device(self, name: str, topic: str) -> None:
#                 self._devices[name.lower().replace(" ","_")] = topic
#     """)

#     w("niaeleria/automation/briefing.py", r"""
#         from __future__ import annotations
#         import logging
#         from datetime import datetime
#         from niaeleria.security.kill_switch import assert_alive
#         from niaeleria.security.audit import log_event

#         log = logging.getLogger("nia.briefing")

#         class MorningBriefing:
#             """Good morning Dad — weather, schedule, security, all in one. — Nia"""
#             def __init__(self, tts, scheduler, guard_status_fn, brain) -> None:
#                 self._tts = tts; self._sched = scheduler
#                 self._guard_fn = guard_status_fn; self._brain = brain

#             async def deliver(self) -> str:
#                 assert_alive(); now = datetime.now(); parts = []
#                 parts.append(f"Good morning Dad! It's {now.strftime('%A, %B %d')} at {now.strftime('%I:%M %p')}.")
#                 weather = await self._get_weather()
#                 if weather: parts.append(f"Weather: {weather}")
#                 tasks = self._sched.list_tasks()
#                 today = [t for t in tasks if t["next_run"] and t["next_run"][:10] == now.strftime("%Y-%m-%d")]
#                 if today:
#                     parts.append(f"You have {len(today)} task(s) today: {', '.join(t['name'] for t in today[:5])}.")
#                 else: parts.append("Your schedule looks clear today, Dad.")
#                 try:
#                     g = self._guard_fn(); bl = len(g.get("blocked_ips", []))
#                     parts.append(f"Security: I blocked {bl} IP(s) overnight. All quiet otherwise." if bl
#                                  else "Security: all quiet overnight, Dad.")
#                 except Exception: pass
#                 text = " ".join(parts)
#                 log.info("Delivering morning briefing to Dad.")
#                 self._tts.speak(text)
#                 try:
#                     from niaeleria.api.server import push_to_hud
#                     push_to_hud({"type":"nia_speak","text":text,"label":"NIA · MORNING BRIEFING"})
#                 except Exception: pass
#                 log_event("nia.briefing","morning_briefing",approved=True)
#                 return text

#             async def _get_weather(self):
#                 from niaeleria.config import OPENWEATHER_API_KEY, DAD_LOCATION, is_network_enabled
#                 if not is_network_enabled() or not OPENWEATHER_API_KEY: return None
#                 try:
#                     import httpx
#                     url = (f"https://api.openweathermap.org/data/2.5/weather"
#                            f"?q={DAD_LOCATION}&appid={OPENWEATHER_API_KEY}&units=metric")
#                     async with httpx.AsyncClient(timeout=10) as c:
#                         r = await c.get(url); r.raise_for_status(); d = r.json()
#                         return (f"{d['weather'][0]['description'].capitalize()} in "
#                                 f"{DAD_LOCATION.split(',')[0]}, {d['main']['temp']:.0f}°C.")
#                 except Exception as e: log.warning("Weather error: %s", e); return None
#     """)

#     # ── sync ──────────────────────────────────────────────────────────────────
#     w("niaeleria/sync/__init__.py", "# NiaEleria cross-device MQTT sync\n")

#     w("niaeleria/sync/mqtt_sync.py", r"""
#         from __future__ import annotations
#         import json, logging, threading, time
#         from typing import Callable, Optional
#         from niaeleria.config import (MQTT_HOST, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD,
#                                       MQTT_TLS, MQTT_TOPIC_PREFIX, is_killed)
#         from niaeleria.security.kill_switch import assert_alive
#         from niaeleria.security.audit import log_event

#         log = logging.getLogger("nia.mqtt")

#         class MQTTSync:
#             """Cross-device sync via MQTT QoS-1. One block, blocked everywhere. — Nia"""
#             _connected = False; _instance: Optional["MQTTSync"] = None
#             _subs: dict[str, Callable] = {}

#             def __init__(self) -> None:
#                 MQTTSync._instance = self; self._client = self._create()

#             def _create(self):
#                 try:
#                     import paho.mqtt.client as mqtt
#                     c = mqtt.Client(client_id="niaeleria", clean_session=True)
#                     if MQTT_USERNAME: c.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
#                     if MQTT_TLS: c.tls_set()
#                     c.on_connect    = self._on_connect
#                     c.on_disconnect = self._on_disconnect
#                     c.on_message    = self._on_message
#                     return c
#                 except ImportError:
#                     log.error("paho-mqtt not installed. Run: pip install paho-mqtt"); return None

#             def connect(self) -> bool:
#                 if not self._client: return False
#                 try:
#                     self._client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
#                     self._client.loop_start()
#                     for _ in range(20):
#                         if MQTTSync._connected: return True
#                         time.sleep(0.5)
#                     log.warning("Dad, MQTT connection timed out. Is Mosquitto running?"); return False
#                 except Exception as e:
#                     log.warning("Dad, MQTT unavailable (%s) — cross-device sync off.", e); return False

#             def disconnect(self) -> None:
#                 if self._client and MQTTSync._connected:
#                     self._client.loop_stop(); self._client.disconnect()

#             def _on_connect(self, c, u, f, rc) -> None:
#                 MQTTSync._connected = (rc == 0)
#                 if rc == 0:
#                     log.info("Dad, MQTT connected. Cross-device sync active.")
#                     for topic in self._subs: c.subscribe(topic, qos=1)

#             def _on_disconnect(self, c, u, rc) -> None:
#                 MQTTSync._connected = False
#                 if rc != 0: log.warning("MQTT disconnected (rc=%d)", rc)

#             def _on_message(self, c, u, msg) -> None:
#                 try: payload = json.loads(msg.payload.decode())
#                 except: payload = msg.payload.decode()
#                 h = self._subs.get(msg.topic)
#                 if h:
#                     try: h(msg.topic, payload)
#                     except Exception as e: log.error("MQTT handler error: %s", e)

#             def subscribe(self, topic: str, handler: Callable) -> None:
#                 ft = f"{MQTT_TOPIC_PREFIX}/{topic}"; self._subs[ft] = handler
#                 if self._client and MQTTSync._connected: self._client.subscribe(ft, qos=1)

#             def publish(self, topic: str, payload, qos: int = 1) -> bool:
#                 if not self._client or not MQTTSync._connected: return False
#                 ft = f"{MQTT_TOPIC_PREFIX}/{topic}"
#                 data = json.dumps(payload) if isinstance(payload, dict) else str(payload)
#                 try: return self._client.publish(ft, data, qos=qos).rc == 0
#                 except Exception as e: log.error("MQTT publish error: %s", e); return False

#             @classmethod
#             def broadcast_block(cls, ip: str, reason: str) -> None:
#                 if cls._instance:
#                     cls._instance.publish("security/block", {"ip":ip,"reason":reason,"source":"nia"})
#                     log.info("Dad, broadcast block of %s to all devices.", ip)
#                     log_event("nia.mqtt","broadcast_block",target=ip,details={"reason":reason},approved=True)

#             def setup_firewall_sync(self) -> None:
#                 from niaeleria.guard.cyber_guard import Firewall
#                 def handle(topic, payload):
#                     ip = payload.get("ip")
#                     if ip:
#                         log.info("Dad, applying block from remote device: %s", ip)
#                         Firewall.block_ip(ip, reason=f"[sync] {payload.get('reason','')}", approved=True)
#                 self.subscribe("security/block", handle)
#                 log.info("Dad, cross-device firewall sync active.")
#     """)

#     # ── api ───────────────────────────────────────────────────────────────────
#     w("niaeleria/api/__init__.py", "# NiaEleria FastAPI server\n")
#     w("niaeleria/api/routes/__init__.py", "# NiaEleria API routes\n")

#     w("niaeleria/api/server.py", r"""
#         from __future__ import annotations
#         import asyncio, logging, threading
#         from contextlib import asynccontextmanager
#         from fastapi import FastAPI, WebSocket, WebSocketDisconnect
#         from fastapi.middleware.cors import CORSMiddleware
#         from fastapi.staticfiles import StaticFiles
#         from niaeleria.config import CORS_ORIGINS, STATIC_DIR
#         from niaeleria.security.kill_switch import assert_alive

#         log = logging.getLogger("nia.api")

#         _brain = _memory = _guard = _scheduler = _self_modifier = None
#         _tts = _home_controller = _learner = None
#         _ws_connections: list[WebSocket] = []

#         def inject_services(**s) -> None:
#             global _brain,_memory,_guard,_scheduler,_self_modifier,_tts,_home_controller,_learner
#             _brain=s.get("brain"); _memory=s.get("memory"); _guard=s.get("guard")
#             _scheduler=s.get("scheduler"); _self_modifier=s.get("self_modifier")
#             _tts=s.get("tts"); _home_controller=s.get("home_controller"); _learner=s.get("learner")

#         async def broadcast_ws(message: dict) -> None:
#             dead = []
#             for ws in _ws_connections:
#                 try: await ws.send_json(message)
#                 except: dead.append(ws)
#             for ws in dead: _ws_connections.remove(ws)

#         def push_to_hud(message: dict) -> None:
#             """Any module can call this to push data onto Dad's JARVIS HUD. — Nia"""
#             def _push():
#                 try:
#                     loop = asyncio.new_event_loop()
#                     loop.run_until_complete(broadcast_ws(message)); loop.close()
#                 except Exception as e: log.debug("HUD push error: %s", e)
#             threading.Thread(target=_push, daemon=True, name="HUDPush").start()

#         @asynccontextmanager
#         async def lifespan(app: FastAPI):
#             log.info("Dad, API server starting up."); yield
#             log.info("Dad, API server shutting down.")

#         def create_app() -> FastAPI:
#             app = FastAPI(title="NiaEleria", description="Dad's AI — loyal digital daughter.",
#                           version="2.0.0", lifespan=lifespan)
#             app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS,
#                                allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
#             from niaeleria.api.routes.chat import router as chat_r
#             from niaeleria.api.routes.security import router as sec_r
#             from niaeleria.api.routes.memory import router as mem_r
#             from niaeleria.api.routes.automation import router as auto_r
#             from niaeleria.api.routes.selfmod import router as sm_r
#             app.include_router(chat_r,  prefix="/api/chat",       tags=["Chat"])
#             app.include_router(sec_r,   prefix="/api/security",   tags=["Security"])
#             app.include_router(mem_r,   prefix="/api/memory",     tags=["Memory"])
#             app.include_router(auto_r,  prefix="/api/automation", tags=["Automation"])
#             app.include_router(sm_r,    prefix="/api/selfmod",    tags=["SelfMod"])

#             @app.websocket("/ws")
#             async def ws_endpoint(ws: WebSocket):
#                 await ws.accept(); _ws_connections.append(ws)
#                 log.info("Dad connected via WebSocket.")
#                 try:
#                     while True:
#                         data = await ws.receive_json(); assert_alive()
#                         t = data.get("type","")
#                         if t == "ping":
#                             await ws.send_json({"type":"pong"})
#                         elif t == "chat":
#                             user_msg = data.get("message",""); history = data.get("history",[])
#                             await ws.send_json({"type":"thinking"})
#                             async for tok in await _brain.chat(user_msg, history, stream=True):
#                                 await ws.send_json({"type":"token","text":tok})
#                             await ws.send_json({"type":"done"})
#                         elif t == "voice_trigger":
#                             import threading as _th
#                             def _handle():
#                                 import asyncio as _a
#                                 from niaeleria.voice.stt import SpeechToText
#                                 stt = SpeechToText(); text = stt.listen_for_command()
#                                 if text:
#                                     loop2 = _a.new_event_loop()
#                                     response = loop2.run_until_complete(_brain.chat(text)); loop2.close()
#                                     _a.run(broadcast_ws({"type":"token","text":response}))
#                                     _a.run(broadcast_ws({"type":"done"}))
#                                     if _tts: _tts.speak(response)
#                                 else:
#                                     _a.run(broadcast_ws({"type":"nia_speak",
#                                         "text":"Dad, I didn't catch that. Try again."}))
#                             _th.Thread(target=_handle, daemon=True).start()
#                         elif t == "consent_response":
#                             from niaeleria.security.consent import post_answer
#                             post_answer(data.get("approved", False))
#                             await ws.send_json({"type":"consent_ack"})
#                 except WebSocketDisconnect:
#                     if ws in _ws_connections: _ws_connections.remove(ws)
#                 except RuntimeError:
#                     await ws.send_json({"type":"error","text":"Kill-switch activated, Dad."})

#             @app.get("/health")
#             async def health(): return {"status":"alive","msg":"Dad, I'm here!"}

#             if STATIC_DIR.exists():
#                 app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
#             return app
#     """)

#     w("niaeleria/api/routes/chat.py", r"""
#         from fastapi import APIRouter, HTTPException
#         from pydantic import BaseModel
#         router = APIRouter()

#         class ChatReq(BaseModel):
#             message: str; history: list[dict] = []

#         @router.post("/")
#         async def chat(req: ChatReq):
#             from niaeleria.api.server import _brain
#             from niaeleria.security.kill_switch import assert_alive
#             assert_alive()
#             if not _brain: raise HTTPException(503, "Dad, brain not loaded.")
#             return {"response": await _brain.chat(req.message, req.history)}

#         @router.get("/history")
#         async def history(n: int = 20):
#             from niaeleria.api.server import _memory
#             return _memory.recent_exchanges(n) if _memory else []
#     """)

#     w("niaeleria/api/routes/security.py", r"""
#         from fastapi import APIRouter
#         from pydantic import BaseModel
#         router = APIRouter()

#         class BlockReq(BaseModel):
#             ip: str; reason: str = "manual block by Dad"

#         class ToolReq(BaseModel):
#             tool: str; target: str; args: str = ""

#         @router.get("/status")
#         async def status():
#             from niaeleria.api.server import _guard
#             from niaeleria.config import is_guard_active, is_killed, is_network_enabled
#             return {"guard_active": is_guard_active(), "kill_switch": is_killed(),
#                     "network_enabled": is_network_enabled(),
#                     "guard": _guard.status() if _guard else {}}

#         @router.post("/block")
#         async def block(req: BlockReq):
#             from niaeleria.guard.cyber_guard import Firewall
#             from niaeleria.sync.mqtt_sync import MQTTSync
#             ok = Firewall.block_ip(req.ip, reason=req.reason, approved=True)
#             if ok: MQTTSync.broadcast_block(req.ip, req.reason)
#             return {"success": ok, "ip": req.ip}

#         @router.delete("/block/{ip}")
#         async def unblock(ip: str):
#             from niaeleria.guard.cyber_guard import Firewall
#             return {"success": Firewall.unblock_ip(ip), "ip": ip}

#         @router.get("/audit")
#         async def audit(n: int = 50):
#             from niaeleria.security.audit import tail_log, verify_log_integrity
#             entries = tail_log(n); total, tampered = verify_log_integrity()
#             return {"entries": entries, "integrity": {"total": total, "tampered": tampered}}

#         @router.post("/toolkit/run")
#         async def run_tool(req: ToolReq):
#             from niaeleria.guard.cyber_guard import SecurityToolkit
#             return SecurityToolkit.run_tool(req.tool, req.target, req.args)

#         @router.post("/consent/{approved}")
#         async def consent(approved: bool):
#             from niaeleria.security.consent import post_answer
#             post_answer(approved); return {"received": True, "approved": approved}

#         @router.post("/kill")
#         async def activate_kill():
#             from niaeleria.config import FLAG_STOP_EVERYTHING
#             FLAG_STOP_EVERYTHING.touch()
#             return {"kill_switch": "ACTIVATED", "msg": "Dad, stopping everything now."}

#         @router.delete("/kill")
#         async def deactivate_kill():
#             from niaeleria.config import FLAG_STOP_EVERYTHING
#             FLAG_STOP_EVERYTHING.unlink(missing_ok=True)
#             return {"kill_switch": "CLEARED", "msg": "Dad, resuming normal operations."}
#     """)

#     w("niaeleria/api/routes/memory.py", r"""
#         from fastapi import APIRouter, HTTPException
#         router = APIRouter()

#         @router.get("/search")
#         async def search(q: str, top_k: int = 10):
#             from niaeleria.api.server import _memory
#             if not _memory: raise HTTPException(503, "Memory not loaded.")
#             return {"query": q, "results": await _memory.search(q, top_k=top_k)}

#         @router.get("/recent")
#         async def recent(n: int = 20):
#             from niaeleria.api.server import _memory
#             return _memory.recent_exchanges(n) if _memory else []

#         @router.post("/learn")
#         async def learn(url: str, tags: str = ""):
#             from niaeleria.api.server import _learner
#             if not _learner: raise HTTPException(503, "Learner not available.")
#             return {"url": url, "summary": await _learner.learn_from_url(url, tags=tags)}
#     """)

#     w("niaeleria/api/routes/automation.py", r"""
#         from fastapi import APIRouter
#         from pydantic import BaseModel
#         from typing import Optional
#         router = APIRouter()

#         class ReminderReq(BaseModel):
#             name: str; message: str
#             delay_secs: Optional[float] = None
#             run_at_iso: Optional[str]   = None
#             interval_secs: Optional[float] = None

#         class DeviceCmd(BaseModel):
#             device: str; action: str; value: Optional[str] = None

#         @router.get("/tasks")
#         async def tasks():
#             from niaeleria.api.server import _scheduler
#             return _scheduler.list_tasks() if _scheduler else []

#         @router.post("/reminder")
#         async def add_reminder(req: ReminderReq):
#             from niaeleria.api.server import _scheduler, _tts
#             from datetime import datetime as dt
#             def _remind():
#                 if _tts: _tts.speak(f"Dad, reminder: {req.message}")
#             run_at = dt.fromisoformat(req.run_at_iso) if req.run_at_iso else None
#             tid = _scheduler.add_reminder(req.name, _remind, run_at=run_at,
#                                           interval_secs=req.interval_secs,
#                                           delay_secs=req.delay_secs)
#             return {"task_id": tid, "name": req.name}

#         @router.delete("/tasks/{tid}")
#         async def cancel(tid: str):
#             from niaeleria.api.server import _scheduler
#             return {"cancelled": _scheduler.cancel(tid), "task_id": tid}

#         @router.post("/home/command")
#         async def home_cmd(req: DeviceCmd):
#             from niaeleria.api.server import _home_controller
#             from fastapi import HTTPException
#             if not _home_controller: raise HTTPException(503, "Home controller unavailable.")
#             ok = _home_controller.command(req.device, req.action, req.value)
#             return {"success": ok, "device": req.device, "action": req.action}
#     """)

#     w("niaeleria/api/routes/selfmod.py", r"""
#         from fastapi import APIRouter
#         from pydantic import BaseModel
#         router = APIRouter()

#         class ProposeReq(BaseModel):
#             file_rel_path: str; new_content: str; reason: str

#         class ApplyReq(BaseModel):
#             file_rel_path: str; new_content: str; proposal_id: str

#         @router.post("/propose")
#         async def propose(req: ProposeReq):
#             from niaeleria.api.server import _self_modifier
#             from fastapi import HTTPException
#             if not _self_modifier: raise HTTPException(503, "Self-modifier unavailable.")
#             return _self_modifier.propose_change(req.file_rel_path, req.new_content, req.reason)

#         @router.post("/apply")
#         async def apply(req: ApplyReq):
#             from niaeleria.api.server import _self_modifier
#             from fastapi import HTTPException
#             if not _self_modifier: raise HTTPException(503, "Self-modifier unavailable.")
#             return _self_modifier.apply_change(req.file_rel_path, req.new_content, req.proposal_id)

#         @router.post("/rollback")
#         async def rollback(file_rel_path: str):
#             from niaeleria.api.server import _self_modifier
#             return _self_modifier.rollback(file_rel_path)
#     """)

#     # ── tray ──────────────────────────────────────────────────────────────────
#     w("niaeleria/tray/__init__.py", "# NiaEleria system tray\n")

#     w("niaeleria/tray/tray_app.py", r"""
#         from __future__ import annotations
#         import logging, threading, webbrowser
#         from niaeleria.config import API_HOST, API_PORT

#         log = logging.getLogger("nia.tray")

#         class NiaTray:
#             """System tray — Dad's one-click access to NiaEleria. — Nia"""
#             def __init__(self, voice_interface=None, tts=None, stt=None, brain=None) -> None:
#                 self._voice=voice_interface; self._tts=tts; self._stt=stt; self._brain=brain
#                 self._icon=None; self._ok=False
#                 try:
#                     import pystray; from PIL import Image
#                     self._pystray=pystray; self._Image=Image; self._ok=True
#                 except ImportError:
#                     log.warning("Dad, pystray/Pillow not installed — tray disabled.")

#             def _make_icon(self):
#                 from PIL import Image, ImageDraw
#                 img = Image.new("RGBA",(64,64),(0,0,0,0)); draw = ImageDraw.Draw(img)
#                 draw.ellipse([4,4,60,60],fill=(0,200,200,255))
#                 try:
#                     from PIL import ImageFont; font=ImageFont.truetype("arial.ttf",32)
#                 except: font=None
#                 draw.text((20,14),"N",fill=(255,255,255),font=font); return img

#             def start(self) -> None:
#                 if not self._ok: return
#                 menu = self._pystray.Menu(
#                     self._pystray.MenuItem("Talk to Nia",       self._talk),
#                     self._pystray.MenuItem("Open HUD Dashboard",self._dashboard),
#                     self._pystray.MenuItem("Guard Status",       self._guard_status),
#                     self._pystray.MenuItem("Morning Briefing",   self._briefing),
#                     self._pystray.MenuItem("─────────────",      lambda:None, enabled=False),
#                     self._pystray.MenuItem("Kill Switch 🔴",      self._kill),
#                     self._pystray.MenuItem("Exit",               self._exit),
#                 )
#                 self._icon = self._pystray.Icon("NiaEleria", self._make_icon(),
#                                                  "NiaEleria — Dad's AI", menu)
#                 threading.Thread(target=self._icon.run, name="Tray", daemon=True).start()
#                 log.info("Dad, I'm in your system tray.")

#             def _talk(self, *_):
#                 if self._voice:
#                     threading.Thread(target=self._voice._handle_command, daemon=True).start()

#             def _dashboard(self, *_):
#                 webbrowser.open(f"http://{API_HOST}:{API_PORT}")

#             def _guard_status(self, *_):
#                 if not self._tts: return
#                 from niaeleria.guard.cyber_guard import Firewall
#                 from niaeleria.config import is_guard_active
#                 bl = len(Firewall.get_blocked())
#                 self._tts.speak(
#                     f"Dad, my cyber guard is {'armed' if is_guard_active() else 'disarmed'}. "
#                     f"I've blocked {bl} IP address{'es' if bl!=1 else ''} so far.")

#             def _briefing(self, *_):
#                 import asyncio
#                 from niaeleria.api.server import _brain,_scheduler,_guard,_tts
#                 def _run():
#                     from niaeleria.automation.briefing import MorningBriefing
#                     b = MorningBriefing(_tts,_scheduler,lambda:_guard.status() if _guard else {},_brain)
#                     loop=asyncio.new_event_loop(); loop.run_until_complete(b.deliver()); loop.close()
#                 threading.Thread(target=_run, daemon=True).start()

#             def _kill(self, *_):
#                 from niaeleria.config import FLAG_STOP_EVERYTHING, is_killed
#                 if is_killed(): FLAG_STOP_EVERYTHING.unlink(missing_ok=True)
#                 else: FLAG_STOP_EVERYTHING.touch()

#             def _exit(self, *_):
#                 from niaeleria.config import FLAG_STOP_EVERYTHING
#                 FLAG_STOP_EVERYTHING.touch()
#                 if self._icon: self._icon.stop()

#             def stop(self) -> None:
#                 if self._icon: self._icon.stop()
#     """)

#     # ── daemon ────────────────────────────────────────────────────────────────
#     w("niaeleria/daemon.py", r"""
#         from __future__ import annotations
#         import asyncio, logging, signal, sys, threading, time
#         import uvicorn
#         from niaeleria.config import (configure_logging, ensure_dirs, first_run_setup,
#                                       validate_critical_config, MORNING_BRIEFING_TIME,
#                                       API_HOST, API_PORT, is_killed, FLAG_STOP_EVERYTHING)

#         log = logging.getLogger("nia.daemon")
#         _shutdown = threading.Event()

#         def _sig(signum, frame):
#             log.info("Dad, shutdown signal %d received. Stopping.", signum)
#             FLAG_STOP_EVERYTHING.touch(); _shutdown.set()

#         def _service(name, fn, *a, restart=True, **kw):
#             def _wrap():
#                 while True:
#                     try: log.info("Starting: %s", name); fn(*a, **kw); break
#                     except RuntimeError as e:
#                         if "kill" in str(e).lower(): break
#                         log.error("%s crashed: %s", name, e)
#                         if not restart or is_killed(): break
#                         log.info("Restarting %s in 5s...", name); time.sleep(5)
#                     except Exception as e:
#                         log.error("%s crashed: %s", name, e)
#                         if not restart or is_killed(): break
#                         time.sleep(5)
#             threading.Thread(target=_wrap, name=name, daemon=True).start()

#         def main():
#             signal.signal(signal.SIGINT,  _sig)
#             signal.signal(signal.SIGTERM, _sig)

#             configure_logging()
#             log.info("="*56)
#             log.info("  NiaEleria v2 — Dad's AI, starting up")
#             log.info("="*56)

#             ensure_dirs(); first_run_setup()

#             for w in validate_critical_config(): log.warning(w)

#             # 1. Kill-switch (always first)
#             from niaeleria.security import kill_switch
#             kill_switch.register_shutdown_callback(lambda: _shutdown.set())
#             kill_switch.start_monitor()
#             log.info("Kill-switch monitor: ARMED")

#             # 2. Audit sanity check
#             from niaeleria.security.audit import verify_log_integrity, log_event
#             total, tampered = verify_log_integrity()
#             if tampered: log.error("Dad! Audit log has %d TAMPERED entries!", tampered)
#             log_event("nia.daemon","startup",severity="INFO",approved=True)

#             # 3. Core AI
#             from niaeleria.core.memory import MemoryStore
#             from niaeleria.core.persona import PersonaEngine
#             from niaeleria.core.brain import NiaBrain
#             from niaeleria.core.learner import InternetLearner
#             memory=MemoryStore(); persona=PersonaEngine()
#             brain=NiaBrain(memory=memory,persona=persona)
#             learner=InternetLearner(memory=memory,brain=brain)
#             log.info("Core AI brain: ONLINE")

#             # 4. Security
#             from niaeleria.security.consent import set_notifier
#             from niaeleria.security.self_modifier import SelfModifier
#             self_mod = SelfModifier()
#             set_notifier(lambda msg: log.info("[CONSENT PENDING] %s", msg))

#             # 5. Cyber Guard
#             from niaeleria.guard.cyber_guard import CyberGuard
#             guard = CyberGuard(); guard.start()
#             log.info("Cyber Guard: ACTIVE")

#             # 6. MQTT
#             from niaeleria.sync.mqtt_sync import MQTTSync
#             mqtt = MQTTSync()
#             if mqtt.connect(): mqtt.setup_firewall_sync(); log.info("MQTT Sync: CONNECTED")
#             else: log.warning("MQTT Sync: OFFLINE")

#             # 7. Home controller
#             from niaeleria.automation.home_control import HomeController
#             home = HomeController(mqtt)

#             # 8. Scheduler
#             from niaeleria.automation.scheduler import Scheduler
#             from niaeleria.automation.briefing import MorningBriefing
#             scheduler = Scheduler(); scheduler.start()

#             # 9. Voice
#             from niaeleria.voice.tts import TextToSpeech
#             from niaeleria.voice.stt import SpeechToText
#             from niaeleria.voice import VoiceInterface
#             tts=TextToSpeech(); stt=SpeechToText()
#             voice=VoiceInterface(brain=brain,tts=tts,stt=stt)
#             set_notifier(tts.speak); voice.start()
#             log.info("Voice Interface: LISTENING")

#             # 10. Morning briefing schedule
#             briefing = MorningBriefing(tts,scheduler,guard.status,brain)
#             from datetime import datetime, timedelta
#             h,m = MORNING_BRIEFING_TIME.split(":")
#             now = datetime.now()
#             bt = now.replace(hour=int(h),minute=int(m),second=0,microsecond=0)
#             if bt < now: bt += timedelta(days=1)
#             def _do_brief():
#                 loop=asyncio.new_event_loop(); loop.run_until_complete(briefing.deliver()); loop.close()
#             scheduler.add_reminder("Morning Briefing",_do_brief,interval_secs=86400,
#                                    delay_secs=(bt-now).total_seconds())

#             # 11. API + HUD
#             from niaeleria.api.server import create_app, inject_services
#             inject_services(brain=brain,memory=memory,guard=guard,scheduler=scheduler,
#                             self_modifier=self_mod,tts=tts,home_controller=home,learner=learner)
#             app = create_app()

#             # 12. Tray
#             from niaeleria.tray.tray_app import NiaTray
#             tray = NiaTray(voice,tts,stt,brain); tray.start()

#             # 13. Startup greeting
#             def _greet():
#                 time.sleep(2)
#                 msg = ("Dad, I'm fully online. Cyber guard is armed. "
#                        "Say 'Hey Nia' anytime, or open your HUD. I'm here.")
#                 tts.speak(msg)
#                 try:
#                     from niaeleria.api.server import push_to_hud
#                     push_to_hud({"type":"nia_speak","text":msg,"label":"NIA · ONLINE"})
#                 except Exception: pass
#             threading.Thread(target=_greet, daemon=True, name="StartupGreet").start()
#             log_event("nia.daemon","fully_online",severity="INFO",approved=True)
#             log.info("NiaEleria v2 FULLY ONLINE. Dad, I'm ready.")

#             # 14. API server (blocking in thread)
#             _service("APIServer", uvicorn.run, app,
#                      host=API_HOST, port=API_PORT,
#                      log_level="warning", access_log=False, restart=False)

#             try:
#                 while not _shutdown.is_set(): time.sleep(1)
#             except KeyboardInterrupt: pass

#             log.info("Dad, shutting down cleanly...")
#             voice.stop(); guard.stop(); scheduler.stop(); mqtt.disconnect()
#             memory.close(); tray.stop()
#             log_event("nia.daemon","shutdown",severity="INFO",approved=True)
#             log.info("Goodbye Dad. NiaEleria is offline. Stay safe.")

#         if __name__ == "__main__":
#             main()
#     """)

#     # ── db schema ─────────────────────────────────────────────────────────────
#     w("niaeleria/db/schema.sql", """\
# -- NiaEleria Supabase Schema
# -- Dad: run this once in your Supabase SQL editor.

# create extension if not exists vector;

# create table if not exists exchanges (
#     id        bigserial primary key,
#     ts        timestamptz not null default now(),
#     user_msg  text        not null,
#     nia_msg   text        not null,
#     tags      text        default '',
#     embedding vector(384)
# );

# create table if not exists knowledge (
#     id        bigserial primary key,
#     ts        timestamptz not null default now(),
#     source    text        not null,
#     title     text        default '',
#     content   text        not null,
#     tags      text        default '',
#     embedding vector(384)
# );

# create or replace function match_exchanges(
#     query_embedding vector(384),
#     match_threshold float,
#     match_count     int
# )
# returns table (id bigint, ts timestamptz, user_msg text, nia_msg text, similarity float)
# language sql stable as $$
#     select id, ts, user_msg, nia_msg,
#            1 - (embedding <=> query_embedding) as similarity
#     from exchanges
#     where 1 - (embedding <=> query_embedding) > match_threshold
#     order by embedding <=> query_embedding
#     limit match_count;
# $$;

# alter table exchanges enable row level security;
# alter table knowledge  enable row level security;
# """)

#     # ── JARVIS HUD (static/index.html) ────────────────────────────────────────
#     # The full JARVIS HTML is written verbatim from the nia_jarvis_ui artifact.
#     # It is stored here as a raw string to avoid any escaping issues.
#     jarvis_html = """\
# <!DOCTYPE html>
# <html lang="en">
# <head>
# <meta charset="UTF-8"/>
# <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
# <title>NiaEleria</title>
# <style>
# *{margin:0;padding:0;box-sizing:border-box}
# :root{
#   --c:#00d4ff;--c2:#0066ff;--c3:#ff6600;--c4:#ff2244;
#   --dim:rgba(0,212,255,.08);--glow:0 0 20px rgba(0,212,255,.4);
# }
# html,body{width:100%;height:100%;overflow:hidden;background:#000;
#   font-family:'Courier New',monospace;color:var(--c);user-select:none}
# #bg{position:fixed;inset:0;z-index:0}
# .grid-overlay{position:fixed;inset:0;z-index:1;pointer-events:none;
#   background-image:linear-gradient(rgba(0,212,255,.03) 1px,transparent 1px),
#     linear-gradient(90deg,rgba(0,212,255,.03) 1px,transparent 1px);
#   background-size:60px 60px;animation:gridPulse 8s ease-in-out infinite}
# @keyframes gridPulse{0%,100%{opacity:.5}50%{opacity:1}}
# #hud{position:fixed;inset:0;z-index:2}
# #status-ring{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
#   width:220px;height:220px;pointer-events:none}
# .ring-svg{width:100%;height:100%;animation:ringRotate 20s linear infinite}
# @keyframes ringRotate{to{transform:rotate(360deg)}}
# .ring-inner-svg{width:100%;height:100%;position:absolute;inset:0;
#   animation:ringRotate 12s linear infinite reverse}
# #nia-core{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
#   display:flex;flex-direction:column;align-items:center;gap:4px}
# #nia-name{font-size:13px;letter-spacing:6px;color:var(--c);
#   text-shadow:var(--glow);opacity:.9}
# #nia-state{font-size:10px;letter-spacing:3px;color:rgba(0,212,255,.5);
#   animation:stateBlink 3s ease-in-out infinite}
# @keyframes stateBlink{0%,100%{opacity:.4}50%{opacity:.9}}
# #voice-ring{width:80px;height:80px;border-radius:50%;
#   border:1.5px solid rgba(0,212,255,.3);
#   box-shadow:0 0 30px rgba(0,212,255,.2),inset 0 0 30px rgba(0,212,255,.05);
#   display:flex;align-items:center;justify-content:center;
#   transition:all .3s;cursor:pointer}
# #voice-ring:hover,#voice-ring.listening{border-color:var(--c);
#   box-shadow:0 0 60px rgba(0,212,255,.5),inset 0 0 30px rgba(0,212,255,.1)}
# #voice-ring.speaking{border-color:var(--c3);
#   box-shadow:0 0 60px rgba(255,102,0,.5),inset 0 0 30px rgba(255,102,0,.1)}
# .mic-icon{width:24px;height:24px;opacity:.7;transition:opacity .3s}
# #voice-ring:hover .mic-icon,#voice-ring.listening .mic-icon{opacity:1}
# #voice-bars{display:flex;align-items:center;gap:3px;height:32px;margin-top:6px}
# .vbar{width:3px;border-radius:2px;background:var(--c);opacity:.3;
#   animation:idle 2s ease-in-out infinite}
# .vbar:nth-child(odd){animation-delay:.3s}
# .vbar:nth-child(3n){animation-delay:.6s}
# @keyframes idle{0%,100%{height:4px;opacity:.2}50%{height:8px;opacity:.4}}
# .vbar.active{animation:waveActive .3s ease-in-out infinite alternate;opacity:.8}
# @keyframes waveActive{0%{height:4px}100%{height:28px}}
# .vbar.speak{animation:waveSpeaking .15s ease-in-out infinite alternate;opacity:1}
# @keyframes waveSpeaking{0%{height:6px}100%{height:26px}}
# .orbital{position:absolute;pointer-events:none;opacity:0;transition:opacity .6s,transform .6s}
# .orbital.visible{opacity:1;pointer-events:all}
# .panel-box{background:rgba(0,8,20,.85);border:1px solid rgba(0,212,255,.2);
#   backdrop-filter:blur(12px);padding:14px 18px;min-width:220px;
#   clip-path:polygon(0 0,calc(100% - 10px) 0,100% 10px,100% 100%,10px 100%,0 calc(100% - 10px));
#   box-shadow:0 0 30px rgba(0,212,255,.08),inset 0 0 30px rgba(0,212,255,.02)}
# .panel-label{font-size:9px;letter-spacing:3px;color:rgba(0,212,255,.5);
#   text-transform:uppercase;margin-bottom:10px;border-bottom:1px solid rgba(0,212,255,.1);
#   padding-bottom:6px}
# #panel-security{right:40px;top:50%;transform:translateY(-60%)}
# #panel-security.visible{transform:translateY(-50%)}
# #panel-response{left:40px;top:50%;transform:translateY(-60%);max-width:300px}
# #panel-response.visible{transform:translateY(-50%)}
# #response-text{font-size:13px;line-height:1.8;color:rgba(255,255,255,.85);
#   max-height:260px;overflow-y:auto;word-break:break-word}
# #response-text::-webkit-scrollbar{width:2px}
# #response-text::-webkit-scrollbar-thumb{background:rgba(0,212,255,.3)}
# #panel-vitals{top:30px;left:50%;transform:translateX(-50%);
#   display:flex;gap:30px;align-items:center}
# #panel-vitals.visible{transform:translateX(-50%)}
# .vital{display:flex;flex-direction:column;align-items:center;gap:4px}
# .vital-label{font-size:8px;letter-spacing:2px;color:rgba(0,212,255,.4);text-transform:uppercase}
# .vital-val{font-size:15px;font-weight:700;color:var(--c);text-shadow:var(--glow)}
# .vital-bar{width:60px;height:2px;background:rgba(0,212,255,.1);border-radius:1px;margin-top:2px}
# .vital-fill{height:100%;background:var(--c);border-radius:1px;transition:width .8s;
#   box-shadow:0 0 6px var(--c)}
# .vital-fill.warn{background:var(--c3)}.vital-fill.danger{background:var(--c4)}
# .vital-sep{width:1px;height:40px;background:rgba(0,212,255,.15)}
# #radar-container{position:absolute;right:40px;top:30px}
# #panel-data{left:40px;top:30px;max-width:240px}
# .data-item{padding:6px 0;border-bottom:1px solid rgba(0,212,255,.07);
#   font-size:11px;color:rgba(0,212,255,.6);display:flex;justify-content:space-between}
# .data-item .dt{color:var(--c3);font-size:10px}
# #statusbar{position:absolute;bottom:0;left:0;right:0;height:36px;
#   background:rgba(0,0,0,.6);border-top:1px solid rgba(0,212,255,.1);
#   display:flex;align-items:center;padding:0 24px;gap:24px;font-size:10px;
#   letter-spacing:1.5px;color:rgba(0,212,255,.4)}
# .sb-item{display:flex;align-items:center;gap:8px}
# .sb-dot{width:6px;height:6px;border-radius:50%;background:var(--c);
#   box-shadow:0 0 6px var(--c);animation:sbPulse 2s ease-in-out infinite}
# .sb-dot.off{background:var(--c4);box-shadow:0 0 6px var(--c4);animation:none}
# .sb-dot.warn{background:var(--c3);box-shadow:0 0 6px var(--c3)}
# @keyframes sbPulse{0%,100%{opacity:.5}50%{opacity:1}}
# #time-display{margin-left:auto;font-size:13px;color:rgba(0,212,255,.7);letter-spacing:2px}
# .corner{position:absolute;width:40px;height:40px;pointer-events:none}
# .corner.tl{top:10px;left:10px;border-top:1px solid rgba(0,212,255,.3);border-left:1px solid rgba(0,212,255,.3)}
# .corner.tr{top:10px;right:10px;border-top:1px solid rgba(0,212,255,.3);border-right:1px solid rgba(0,212,255,.3)}
# .corner.bl{bottom:46px;left:10px;border-bottom:1px solid rgba(0,212,255,.3);border-left:1px solid rgba(0,212,255,.3)}
# .corner.br{bottom:46px;right:10px;border-bottom:1px solid rgba(0,212,255,.3);border-right:1px solid rgba(0,212,255,.3)}
# .scanline{position:fixed;inset:0;z-index:3;pointer-events:none;
#   background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,.03) 2px,rgba(0,0,0,.03) 4px)}
# #alert-flash{position:fixed;inset:0;z-index:10;pointer-events:none;
#   background:rgba(255,34,68,.04);opacity:0;transition:opacity .2s}
# #alert-flash.flash{opacity:1}
# #toast{position:fixed;top:60px;left:50%;transform:translateX(-50%);
#   background:rgba(0,8,20,.9);border:1px solid rgba(0,212,255,.3);
#   padding:10px 24px;font-size:11px;letter-spacing:2px;color:var(--c);
#   opacity:0;pointer-events:none;z-index:20;
#   clip-path:polygon(0 0,calc(100% - 8px) 0,100% 8px,100% 100%,8px 100%,0 calc(100% - 8px));
#   transition:opacity .4s;text-align:center;max-width:500px;line-height:1.6}
# #toast.show{opacity:1}
# #kill-indicator{position:absolute;right:40px;bottom:50px;font-size:9px;
#   letter-spacing:2px;color:rgba(255,34,68,.4);cursor:pointer;transition:color .2s;padding:6px}
# #kill-indicator:hover{color:rgba(255,34,68,.8)}
# .panel-value{font-size:13px;color:var(--c);line-height:1.7}
# .sec-sev{font-weight:700;margin-right:6px}
# .sec-sev.HIGH{color:#ff2244}.sec-sev.MEDIUM{color:#ff6600}.sec-sev.INFO,.sec-sev.LOW{color:#00d4ff}
# </style>
# </head>
# <body>
# <canvas id="bg"></canvas>
# <div class="grid-overlay"></div>
# <div class="scanline"></div>
# <div id="alert-flash"></div>
# <div id="toast"></div>
# <div id="hud">
#   <div class="corner tl"></div><div class="corner tr"></div>
#   <div class="corner bl"></div><div class="corner br"></div>
#   <div id="panel-vitals" class="orbital visible">
#     <div class="vital">
#       <div class="vital-label">Guard</div>
#       <div class="vital-val" id="v-guard">ARMED</div>
#       <div class="vital-bar"><div class="vital-fill" id="vf-guard" style="width:100%"></div></div>
#     </div>
#     <div class="vital-sep"></div>
#     <div class="vital">
#       <div class="vital-label">Network</div>
#       <div class="vital-val" id="v-net">GATE</div>
#       <div class="vital-bar"><div class="vital-fill warn" id="vf-net" style="width:60%"></div></div>
#     </div>
#     <div class="vital-sep"></div>
#     <div class="vital">
#       <div class="vital-label">Blocked</div>
#       <div class="vital-val" id="v-blocked">0</div>
#       <div class="vital-bar"><div class="vital-fill" id="vf-blocked" style="width:0%"></div></div>
#     </div>
#     <div class="vital-sep"></div>
#     <div class="vital">
#       <div class="vital-label">Threats</div>
#       <div class="vital-val" id="v-threats">0</div>
#       <div class="vital-bar"><div class="vital-fill danger" id="vf-threats" style="width:0%"></div></div>
#     </div>
#   </div>
#   <div id="radar-container"><canvas id="radar" width="120" height="120"></canvas></div>
#   <div id="panel-data" class="orbital">
#     <div class="panel-box">
#       <div class="panel-label">Upcoming Tasks</div>
#       <div id="data-list"></div>
#     </div>
#   </div>
#   <div id="status-ring">
#     <svg class="ring-svg" viewBox="0 0 220 220">
#       <circle cx="110" cy="110" r="105" fill="none" stroke="rgba(0,212,255,.12)" stroke-width="1"/>
#       <circle cx="110" cy="110" r="105" fill="none" stroke="rgba(0,212,255,.5)" stroke-width="1"
#         stroke-dasharray="80 580" stroke-linecap="round"/>
#       <circle cx="110" cy="110" r="105" fill="none" stroke="rgba(0,102,255,.3)" stroke-width="1"
#         stroke-dasharray="30 630" stroke-linecap="round" stroke-dashoffset="200"/>
#     </svg>
#     <svg class="ring-inner-svg" viewBox="0 0 220 220" style="position:absolute;inset:0;width:100%;height:100%">
#       <circle cx="110" cy="110" r="85" fill="none" stroke="rgba(0,212,255,.08)" stroke-width="1"/>
#       <circle cx="110" cy="110" r="85" fill="none" stroke="rgba(0,212,255,.25)" stroke-width="1"
#         stroke-dasharray="40 490" stroke-linecap="round"/>
#     </svg>
#     <div id="nia-core">
#       <div id="voice-ring" onclick="triggerVoice()" title="Click or say Hey Nia">
#         <svg class="mic-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
#           <rect x="9" y="2" width="6" height="12" rx="3"/>
#           <path d="M5 10a7 7 0 0014 0"/>
#           <line x1="12" y1="22" x2="12" y2="17"/>
#           <line x1="8" y1="22" x2="16" y2="22"/>
#         </svg>
#       </div>
#       <div id="voice-bars">
#         <div class="vbar"></div><div class="vbar"></div><div class="vbar"></div>
#         <div class="vbar"></div><div class="vbar"></div><div class="vbar"></div>
#         <div class="vbar"></div><div class="vbar"></div><div class="vbar"></div>
#       </div>
#       <div id="nia-name">NIAELERIA</div>
#       <div id="nia-state">STANDBY</div>
#     </div>
#   </div>
#   <div id="panel-response" class="orbital">
#     <div class="panel-box" style="min-width:280px">
#       <div class="panel-label" id="resp-label">NIA &middot; RESPONSE</div>
#       <div id="response-text"></div>
#     </div>
#   </div>
#   <div id="panel-security" class="orbital">
#     <div class="panel-box">
#       <div class="panel-label">Security &middot; Active</div>
#       <div class="panel-value" id="sec-content"></div>
#     </div>
#   </div>
#   <div id="kill-indicator" onclick="toggleKill()" title="Toggle kill switch">&#9632; KILL SWITCH</div>
#   <div id="statusbar">
#     <div class="sb-item"><div class="sb-dot" id="sb-ws"></div><span id="sb-ws-label">CONNECTING</span></div>
#     <div class="sb-item"><div class="sb-dot" id="sb-guard"></div><span>CYBER GUARD</span></div>
#     <div class="sb-item"><div class="sb-dot warn" id="sb-net"></div><span id="sb-net-label">NETWORK GATED</span></div>
#     <div class="sb-item"><div class="sb-dot off" id="sb-voice"></div><span>VOICE</span></div>
#     <div id="time-display">--:--:--</div>
#   </div>
# </div>
# <script>
# const BASE=`${location.origin}/api`;
# let ws,killActive=false,responseTimer=null;
# (()=>{
#   const cv=document.getElementById('bg'),ctx=cv.getContext('2d');
#   let W,H,pts=[];
#   function resize(){W=cv.width=innerWidth;H=cv.height=innerHeight;pts=[];
#     for(let i=0;i<90;i++)pts.push({x:Math.random()*W,y:Math.random()*H,
#       vx:(Math.random()-.5)*.15,vy:(Math.random()-.5)*.15,r:Math.random()*1.5+.3,a:Math.random()});}
#   function draw(){
#     ctx.fillStyle='rgba(0,0,0,.04)';ctx.fillRect(0,0,W,H);
#     pts.forEach(p=>{p.x=(p.x+p.vx+W)%W;p.y=(p.y+p.vy+H)%H;
#       p.a=.2+.3*Math.sin(Date.now()*.0005+p.x);
#       ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
#       ctx.fillStyle=`rgba(0,180,255,${p.a})`;ctx.fill();});
#     pts.forEach((p,i)=>{pts.forEach((q,j)=>{if(j<=i)return;
#       const d=Math.hypot(p.x-q.x,p.y-q.y);
#       if(d<120){ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(q.x,q.y);
#         ctx.strokeStyle=`rgba(0,180,255,${.08*(1-d/120)})`;ctx.lineWidth=.5;ctx.stroke();}});});
#     requestAnimationFrame(draw);}
#   window.addEventListener('resize',resize);resize();draw();
# })();
# (()=>{
#   const cv=document.getElementById('radar'),ctx=cv.getContext('2d');
#   const cx=60,cy=60,r=55;let angle=0;const blips=[];
#   window.addRadarBlip=function(intensity=1){blips.push({a:Math.random()*Math.PI*2,
#     d:Math.random()*.8*r+5,life:180,intensity});};
#   function draw(){
#     ctx.clearRect(0,0,120,120);
#     for(let i=1;i<=3;i++){ctx.beginPath();ctx.arc(cx,cy,r*i/3,0,Math.PI*2);
#       ctx.strokeStyle=`rgba(0,212,255,${.15-i*.03})`;ctx.lineWidth=.8;ctx.stroke();}
#     ctx.strokeStyle='rgba(0,212,255,.12)';ctx.lineWidth=.5;
#     ctx.beginPath();ctx.moveTo(cx-r,cy);ctx.lineTo(cx+r,cy);
#     ctx.moveTo(cx,cy-r);ctx.lineTo(cx,cy+r);ctx.stroke();
#     const sweep=ctx.createLinearGradient(cx,cy,cx+r,cy);
#     sweep.addColorStop(0,'rgba(0,212,255,.12)');sweep.addColorStop(1,'rgba(0,212,255,0)');
#     ctx.save();ctx.translate(cx,cy);ctx.rotate(angle);
#     ctx.beginPath();ctx.moveTo(0,0);ctx.arc(0,0,r,-.3,0);ctx.closePath();
#     ctx.fillStyle=sweep;ctx.fill();ctx.restore();
#     angle=(angle+.02)%(Math.PI*2);
#     for(let i=blips.length-1;i>=0;i--){const b=blips[i];b.life--;
#       if(b.life<=0){blips.splice(i,1);continue;}
#       const bx=cx+Math.cos(b.a)*b.d,by=cy+Math.sin(b.a)*b.d;
#       ctx.beginPath();ctx.arc(bx,by,3,0,Math.PI*2);
#       ctx.fillStyle=b.intensity>.7?`rgba(255,34,68,${b.life/180})`:`rgba(0,212,255,${b.life/180})`;
#       ctx.fill();}
#     ctx.beginPath();ctx.arc(cx,cy,2.5,0,Math.PI*2);ctx.fillStyle='rgba(0,212,255,.8)';ctx.fill();
#     requestAnimationFrame(draw);}
#   draw();
# })();
# function updateClock(){const d=new Date();
#   document.getElementById('time-display').textContent=
#     d.toLocaleTimeString('en-GB',{hour12:false})+' '+d.toLocaleDateString('en-GB',{day:'2-digit',month:'short'});}
# setInterval(updateClock,1000);updateClock();
# let toastTimer=null;
# function toast(msg,dur=4000){const el=document.getElementById('toast');
#   el.innerHTML=msg;el.classList.add('show');clearTimeout(toastTimer);
#   toastTimer=setTimeout(()=>el.classList.remove('show'),dur);}
# function setVoiceState(state){
#   const ring=document.getElementById('voice-ring');
#   const bars=document.querySelectorAll('.vbar');
#   const st=document.getElementById('nia-state');
#   const sbv=document.getElementById('sb-voice');
#   ring.className='';bars.forEach(b=>b.className='vbar');
#   if(state==='listening'){ring.classList.add('listening');
#     bars.forEach((b,i)=>{b.classList.add('active');b.style.animationDelay=i*.05+'s';});
#     st.textContent='LISTENING';sbv.className='sb-dot';}
#   else if(state==='thinking'){st.textContent='PROCESSING';sbv.className='sb-dot warn';}
#   else if(state==='speaking'){ring.classList.add('speaking');
#     bars.forEach((b,i)=>{b.classList.add('speak');b.style.animationDelay=i*.04+'s';});
#     st.textContent='RESPONDING';sbv.style.background='var(--c3)';}
#   else{st.textContent='STANDBY';sbv.className='sb-dot off';}}
# function showPanel(id,auto=0){const el=document.getElementById(id);
#   el.classList.add('visible');if(auto){clearTimeout(el._t);el._t=setTimeout(()=>el.classList.remove('visible'),auto);}}
# function hidePanel(id){document.getElementById(id).classList.remove('visible');}
# function niaSpeak(text,label='NIA \xb7 RESPONSE'){
#   document.getElementById('resp-label').textContent=label;
#   const el=document.getElementById('response-text');
#   el.textContent='';setVoiceState('speaking');showPanel('panel-response');
#   let i=0;const iv=setInterval(()=>{
#     if(i<text.length){el.textContent+=text[i++];}
#     else{clearInterval(iv);clearTimeout(responseTimer);
#       responseTimer=setTimeout(()=>{hidePanel('panel-response');setVoiceState('idle');},8000);}},18);}
# function showSecurityAlert(data){
#   const el=document.getElementById('sec-content');
#   if(Array.isArray(data)){
#     el.innerHTML=data.map(d=>`<div style="margin-bottom:6px">
#       <span class="sec-sev ${d.severity}">${d.severity}</span>
#       <span style="color:rgba(255,255,255,.6)">${d.action||''}</span>
#       ${d.target?`<div style="color:rgba(0,212,255,.4);font-size:10px;margin-top:2px">${d.target}</div>`:''}
#     </div>`).join('');}
#   else{el.innerHTML=`<div>${data}</div>`;}
#   showPanel('panel-security',10000);addRadarBlip(1);flashAlert();}
# function flashAlert(){const f=document.getElementById('alert-flash');
#   f.classList.add('flash');setTimeout(()=>f.classList.remove('flash'),400);}
# function showDataPanel(items){
#   document.getElementById('data-list').innerHTML=items.map(it=>
#     `<div class="data-item"><span>${it.name||it}</span>
#      <span class="dt">${it.next_run?.slice(11,16)||''}</span></div>`).join('');
#   showPanel('panel-data',15000);}
# function updateStatus(s){
#   const g=s.guard_active!==false;
#   document.getElementById('sb-guard').className='sb-dot'+(g?'':' off');
#   document.getElementById('v-guard').textContent=g?'ARMED':'OFF';
#   document.getElementById('vf-guard').style.width=g?'100%':'20%';
#   document.getElementById('vf-guard').className='vital-fill'+(g?'':' danger');
#   const n=s.network_enabled===true;
#   document.getElementById('sb-net').className='sb-dot'+(n?'':' warn');
#   document.getElementById('sb-net-label').textContent=n?'NETWORK ON':'NETWORK GATED';
#   document.getElementById('v-net').textContent=n?'OPEN':'GATE';
#   const bl=(s.guard?.blocked_ips||[]).length;
#   document.getElementById('v-blocked').textContent=bl;
#   document.getElementById('vf-blocked').style.width=Math.min(bl*10,100)+'%';
#   killActive=s.kill_switch;
#   document.getElementById('kill-indicator').style.color=
#     killActive?'rgba(255,34,68,.9)':'rgba(255,34,68,.3)';
#   if((s.recent_threats||0)>0){
#     document.getElementById('v-threats').textContent=s.recent_threats;
#     document.getElementById('vf-threats').style.width=Math.min(s.recent_threats*10,100)+'%';
#     for(let i=0;i<Math.min(s.recent_threats,3);i++)setTimeout(()=>addRadarBlip(1),i*300);}}
# function connectWS(){
#   ws=new WebSocket(`ws://${location.host}/ws`);
#   ws.onopen=()=>{document.getElementById('sb-ws').className='sb-dot';
#     document.getElementById('sb-ws-label').textContent='CONNECTED';
#     ws.send(JSON.stringify({type:'ping'}));};
#   ws.onclose=()=>{document.getElementById('sb-ws').className='sb-dot off';
#     document.getElementById('sb-ws-label').textContent='RECONNECTING';
#     setTimeout(connectWS,3000);};
#   ws.onmessage=e=>{const d=JSON.parse(e.data);
#     if(d.type==='pong'){}
#     else if(d.type==='nia_speak')niaSpeak(d.text,d.label);
#     else if(d.type==='security_alert')showSecurityAlert(d.data);
#     else if(d.type==='show_data')showDataPanel(d.items);
#     else if(d.type==='status_update')updateStatus(d.status);
#     else if(d.type==='consent_request')handleConsent(d.message);
#     else if(d.type==='thinking')setVoiceState('thinking');
#     else if(d.type==='token'){
#       const el=document.getElementById('response-text');
#       if(!document.getElementById('panel-response').classList.contains('visible')){
#         setVoiceState('speaking');showPanel('panel-response');el.textContent='';}
#       el.textContent+=d.text;el.scrollTop=el.scrollHeight;}
#     else if(d.type==='done'){setVoiceState('idle');clearTimeout(responseTimer);
#       responseTimer=setTimeout(()=>hidePanel('panel-response'),9000);}};}
# function triggerVoice(){
#   if(!ws||ws.readyState!==1){toast('DAD \u2014 CONNECTION OFFLINE');return;}
#   setVoiceState('listening');
#   ws.send(JSON.stringify({type:'voice_trigger'}));
#   toast('LISTENING, DAD...',3000);}
# function handleConsent(msg){
#   const ok=confirm(`NIA REQUIRES APPROVAL, DAD\\n\\n${msg}\\n\\nApprove?`);
#   ws.send(JSON.stringify({type:'consent_response',approved:ok}));
#   toast(ok?'APPROVED':'DENIED',2000);}
# async function toggleKill(){
#   if(killActive){await fetch(`${BASE}/security/kill`,{method:'DELETE'});
#     toast('KILL SWITCH CLEARED',3000);}
#   else{if(!confirm('DAD \u2014 Activate kill switch?'))return;
#     await fetch(`${BASE}/security/kill`,{method:'POST'});
#     toast('\u26a0 KILL SWITCH ACTIVATED',3000);flashAlert();}
#   setTimeout(pollStatus,500);}
# async function pollStatus(){
#   try{const r=await fetch(`${BASE}/security/status`).then(r=>r.json());
#     const a=await fetch(`${BASE}/security/audit?n=20`).then(r=>r.json()).catch(()=>({entries:[]}));
#     const hi=(a.entries||[]).filter(e=>e.severity==='HIGH'||e.severity==='CRITICAL');
#     updateStatus({...r,recent_threats:hi.length});
#     if(hi.length>0)showSecurityAlert(hi.slice(0,4));}catch{}}
# async function pollTasks(){
#   try{const t=await fetch(`${BASE}/automation/tasks`).then(r=>r.json()).catch(()=>[]);
#     if(t.length>0)showDataPanel(t.slice(0,5));}catch{}}
# connectWS();pollStatus();pollTasks();
# setInterval(pollStatus,10000);setInterval(pollTasks,30000);
# setInterval(()=>{if(Math.random()>.7)addRadarBlip(Math.random());},2000);
# setTimeout(()=>{
#   niaSpeak("All systems online, Dad. Cyber guard is armed. Say the word.","NIA \xb7 ONLINE");
#   addRadarBlip(.3);addRadarBlip(.4);},1200);
# </script>
# </body>
# </html>
# """
#     p = ROOT / "niaeleria" / "api" / "static" / "index.html"
#     p.parent.mkdir(parents=True, exist_ok=True)
#     p.write_text(jarvis_html, encoding="utf-8")
#     print("  ✓  niaeleria/api/static/index.html  [JARVIS HUD]")

#     # ── tests ─────────────────────────────────────────────────────────────────
#     w("tests/__init__.py", "# NiaEleria test suite\n")

#     w("tests/test_security.py", r"""
#         import os, sys, tempfile
#         from pathlib import Path
#         _tmp = tempfile.mkdtemp()
#         os.environ["NIA_HOME"] = _tmp
#         os.environ.setdefault("GROQ_API_KEY","test"); os.environ.setdefault("AUDIT_HMAC_KEY","test-key")
#         for d in ("data","flags","data/backups"): Path(_tmp,d).mkdir(parents=True,exist_ok=True)

#         import pytest
#         from niaeleria.config import FLAG_STOP_EVERYTHING, FLAG_GUARD_ACTIVE, FLAG_ENABLE_NETWORK

#         class TestKillSwitch:
#             def setup_method(self):
#                 if FLAG_STOP_EVERYTHING.exists(): FLAG_STOP_EVERYTHING.unlink()
#             def teardown_method(self):
#                 if FLAG_STOP_EVERYTHING.exists(): FLAG_STOP_EVERYTHING.unlink()
#             def test_alive_when_no_flag(self):
#                 from niaeleria.security.kill_switch import assert_alive
#                 assert_alive()
#             def test_raises_when_killed(self):
#                 from niaeleria.security.kill_switch import assert_alive
#                 FLAG_STOP_EVERYTHING.touch()
#                 with pytest.raises(RuntimeError): assert_alive()

#         class TestAudit:
#             def setup_method(self):
#                 from niaeleria.config import AUDIT_LOG
#                 if AUDIT_LOG.exists(): AUDIT_LOG.unlink()
#             def test_creates_signed_log(self):
#                 from niaeleria.security.audit import log_event, verify_log_integrity
#                 from niaeleria.config import AUDIT_LOG
#                 log_event("test","action"); assert AUDIT_LOG.exists()
#                 assert "|SIG:" in AUDIT_LOG.read_text()
#                 total, tampered = verify_log_integrity()
#                 assert total >= 1 and tampered == 0

#         class TestNetworkGate:
#             def setup_method(self):
#                 if FLAG_ENABLE_NETWORK.exists(): FLAG_ENABLE_NETWORK.unlink()
#             def test_blocks_without_flag(self):
#                 from niaeleria.security.network_gate import require_network
#                 with pytest.raises(PermissionError): require_network("test")
#             def test_passes_with_flag(self):
#                 from niaeleria.security.network_gate import require_network
#                 FLAG_ENABLE_NETWORK.touch(); require_network("test")
#                 FLAG_ENABLE_NETWORK.unlink()
#     """)

#     w("tests/test_guard.py", r"""
#         import os, tempfile; from pathlib import Path
#         _tmp = tempfile.mkdtemp(); os.environ["NIA_HOME"] = _tmp
#         os.environ.setdefault("GROQ_API_KEY","test"); os.environ.setdefault("AUDIT_HMAC_KEY","test")
#         for d in ("data","flags","data/backups"): Path(_tmp,d).mkdir(parents=True,exist_ok=True)

#         from unittest.mock import patch, MagicMock

#         def test_threat_intel_known_bad():
#             from niaeleria.guard.cyber_guard import ThreatIntel
#             ThreatIntel._known_bad.add("1.2.3.4")
#             assert ThreatIntel.is_known_bad("1.2.3.4")
#             assert not ThreatIntel.is_known_bad("10.0.0.1")
#             ThreatIntel._known_bad.discard("1.2.3.4")

#         def test_file_integrity(tmp_path):
#             from niaeleria.guard.cyber_guard import FileIntegrityMonitor
#             f = tmp_path / "test.py"; f.write_text("# original")
#             fim = FileIntegrityMonitor([str(tmp_path)]); fim.build_baseline()
#             assert fim.check() == []
#             f.write_text("# tampered")
#             changes = fim.check()
#             assert any(c["type"] == "MODIFIED" for c in changes)

#         def test_self_modifier_syntax():
#             from niaeleria.security.self_modifier import SelfModifier
#             ok, _  = SelfModifier._check_syntax("x = 1")
#             bad, e = SelfModifier._check_syntax("def broken(: pass")
#             assert ok is True and bad is False and e != ""

#         def test_home_controller_parse():
#             from niaeleria.automation.home_control import HomeController
#             hc = HomeController(MagicMock())
#             r = hc.parse_natural_language("turn on the living room light")
#             assert r and r["action"] == "on"
#             assert hc.parse_natural_language("play jazz") is None
#     """)

#     # ── requirements.txt ──────────────────────────────────────────────────────
#     w("requirements.txt", """\
# # NiaEleria v2 — Dad's AI dependencies

# # Core framework
# fastapi>=0.111.0
# uvicorn[standard]>=0.29.0
# pydantic>=2.6.0
# python-dotenv>=1.0.0
# httpx>=0.27.0

# # AI / LLM / Embeddings
# sentence-transformers>=2.7.0
# supabase>=2.5.0

# # Voice
# SpeechRecognition>=3.10.0
# edge-tts>=6.1.12
# pyaudio>=0.2.14
# # faster-whisper>=1.0.0   # optional offline STT
# # pvporcupine>=3.0.0      # optional Porcupine wake-word

# # Cybersecurity / networking
# psutil>=5.9.8
# scapy>=2.5.0
# paho-mqtt>=2.0.0

# # Web scraping / learning
# beautifulsoup4>=4.12.0
# youtube-transcript-api>=0.6.2

# # System tray
# pystray>=0.19.5
# Pillow>=10.3.0

# # Testing
# pytest>=8.0.0
# """)

#     # ── .env.example ──────────────────────────────────────────────────────────
#     w(".env.example", """\
# # NiaEleria v2 — Environment config
# # Copy to .env and fill in your secrets, Dad.

# # ── REQUIRED ──────────────────────────────────────────
# # Get your key at: https://console.groq.com
# GROQ_API_KEY=your_groq_api_key_here

# # ── Supabase (memory store) ───────────────────────────
# # Create a project at: https://supabase.com
# # Run niaeleria/db/schema.sql in your Supabase SQL editor first.
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_ANON_KEY=your_anon_key_here
# SUPABASE_SERVICE_KEY=your_service_role_key_here

# # ── Security (CHANGE THESE!) ──────────────────────────
# API_SECRET_KEY=replace_with_a_long_random_string_dad
# AUDIT_HMAC_KEY=replace_with_another_secret_for_log_signing

# # ── LLM ───────────────────────────────────────────────
# LLM_MODEL=mixtral-8x7b-32768
# LLM_BASE_URL=https://api.groq.com/openai/v1
# LLM_MAX_TOKENS=2048
# LLM_TEMPERATURE=0.7
# EMBEDDING_MODEL=all-MiniLM-L6-v2

# # ── Voice ─────────────────────────────────────────────
# TTS_VOICE=en-US-AriaNeural
# TTS_RATE=+0%
# WAKE_WORD=hey nia
# PORCUPINE_ACCESS_KEY=

# # ── API ───────────────────────────────────────────────
# API_HOST=127.0.0.1
# API_PORT=7432
# CORS_ORIGINS=http://localhost:7432

# # ── MQTT ──────────────────────────────────────────────
# MQTT_HOST=localhost
# MQTT_PORT=1883
# MQTT_USERNAME=
# MQTT_PASSWORD=
# MQTT_TLS=false
# MQTT_TOPIC_PREFIX=niaeleria

# # ── Weather ───────────────────────────────────────────
# OPENWEATHER_API_KEY=
# DAD_LOCATION=Lagos,NG

# # ── Scheduler ─────────────────────────────────────────
# MORNING_BRIEFING_TIME=07:00

# # ── Guard ─────────────────────────────────────────────
# CONSENT_TIMEOUT_SECS=30
# KILL_SWITCH_POLL_INTERVAL=3.0
# FILE_INTEGRITY_PATHS=./niaeleria
# PROCESS_WATCHLIST=nmap,metasploit,nc,netcat,msfconsole
# THREAT_INTEL_FEED=https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt

# # ── Self-modification ─────────────────────────────────
# ALLOW_SELF_MODIFICATION=true
# SELF_MOD_MAX_FILE_SIZE_KB=512

# # ── Docker sandbox ────────────────────────────────────
# DOCKER_SANDBOX_IMAGE=kalilinux/kali-rolling
# DOCKER_TIMEOUT_SECS=120

# # ── Logging ───────────────────────────────────────────
# LOG_LEVEL=INFO
# """)

#     # ── docker-compose.yml ────────────────────────────────────────────────────
#     w("docker-compose.yml", """\
# # NiaEleria v2 — Docker Compose
# # "Dad, one command brings everything up." — Nia
# version: "3.9"

# services:
#   mqtt-broker:
#     image: eclipse-mosquitto:2.0
#     container_name: nia-mqtt
#     restart: unless-stopped
#     ports:
#       - "1883:1883"
#       - "9001:9001"
#     volumes:
#       - ./deploy/mosquitto.conf:/mosquitto/config/mosquitto.conf:ro
#       - mosquitto_data:/mosquitto/data
#       - mosquitto_log:/mosquitto/log

#   niaeleria:
#     build: .
#     container_name: niaeleria
#     restart: unless-stopped
#     depends_on:
#       - mqtt-broker
#     ports:
#       - "7432:7432"
#     volumes:
#       - ./data:/app/data
#       - ./flags:/app/flags
#       - ./.env:/app/.env:ro
#     environment:
#       - NIA_HOME=/app
#       - MQTT_HOST=mqtt-broker

# volumes:
#   mosquitto_data:
#   mosquitto_log:
# """)

#     # ── Dockerfile ────────────────────────────────────────────────────────────
#     w("Dockerfile", """\
# FROM python:3.11-slim
# LABEL maintainer="NiaEleria v2 — Dad's AI"

# RUN apt-get update && apt-get install -y --no-install-recommends \\
#     gcc libportaudio2 portaudio19-dev mpg123 iptables curl \\
#     && rm -rf /var/lib/apt/lists/*

# WORKDIR /app
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
# COPY niaeleria/ ./niaeleria/
# COPY .env.example .
# RUN mkdir -p data/backups flags niaeleria/api/static && touch flags/GUARD_ACTIVE

# EXPOSE 7432
# CMD ["python", "-m", "niaeleria.daemon"]
# """)

#     # ── deploy/mosquitto.conf ─────────────────────────────────────────────────
#     w("deploy/mosquitto.conf", """\
# listener 1883
# allow_anonymous true
# persistence true
# persistence_location /mosquitto/data/
# log_dest file /mosquitto/log/mosquitto.log
# """)

#     # ── bootstrap.sh ──────────────────────────────────────────────────────────
#     w("bootstrap.sh", r"""#!/usr/bin/env bash
# # bootstrap.sh — One-command setup for NiaEleria v2
# # "Dad, just run this once." — Nia
# set -e
# CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'; B='\033[1m'
# echo -e "${CYAN}  NiaEleria v2 — bootstrapping...${NC}"
# python3 -m venv .venv && source .venv/bin/activate
# pip install --upgrade pip --quiet
# pip install -r requirements.txt --quiet
# mkdir -p data/backups flags niaeleria/api/static
# touch flags/GUARD_ACTIVE
# [ ! -f .env ] && cp .env.example .env && echo -e "${YELLOW}  Created .env — fill in your secrets, Dad!${NC}"
# echo -e "${GREEN}${B}  Done! Run: python -m niaeleria.daemon${NC}"
# echo -e "${CYAN}  HUD: http://localhost:7432${NC}"
# echo -e "${YELLOW}  Don't forget GROQ_API_KEY and Supabase credentials in .env${NC}"
# """)

#     # ── README.md ─────────────────────────────────────────────────────────────
#     w("README.md", """\
# # NiaEleria v2
# ### Dad's loyal digital daughter — personal Jarvis-class AI system.

# ---

# ## Quick Start

# ```bash
# # 1. Install dependencies
# bash bootstrap.sh        # Linux / macOS
# # or on Windows:
# python -m venv .venv && .venv\\Scripts\\activate && pip install -r requirements.txt

# # 2. Configure secrets
# cp .env.example .env
# # Edit .env — set GROQ_API_KEY and Supabase credentials

# # 3. Set up Supabase memory
# # Open niaeleria/db/schema.sql and run it in your Supabase SQL editor

# # 4. Launch
# python -m niaeleria.daemon

# # 5. Open HUD
# # Navigate to http://localhost:7432
# ```

# ---

# ## Architecture

# ```
# niaeleria/
# ├── config.py           Central config — all env vars
# ├── daemon.py           Master launcher & watchdog
# ├── core/
# │   ├── brain.py        LLM (Groq mixtral) + RAG
# │   ├── persona.py      Mood-aware system prompt
# │   ├── memory.py       Supabase + pgvector memory
# │   └── learner.py      URL / YouTube learning
# ├── security/
# │   ├── kill_switch.py  STOP_EVERYTHING poller
# │   ├── audit.py        HMAC-SHA256 audit log
# │   ├── network_gate.py ENABLE_NETWORK enforcement
# │   ├── consent.py      Consent manager
# │   └── self_modifier.py Consent-gated code updates
# ├── guard/
# │   └── cyber_guard.py  Firewall, threat intel, packet sniffer,
# │                       file integrity, process monitor, toolkit
# ├── voice/
# │   ├── wake_word.py    "Hey Nia" detection
# │   ├── stt.py          Speech-to-text
# │   └── tts.py          Neural TTS (edge-tts)
# ├── automation/
# │   ├── scheduler.py    Reminders & recurring tasks
# │   ├── home_control.py MQTT smart home
# │   └── briefing.py     Morning briefing
# ├── sync/
# │   └── mqtt_sync.py    Cross-device firewall sync
# ├── api/
# │   ├── server.py       FastAPI + WebSocket + HUD push
# │   └── routes/         REST endpoints
# ├── tray/
# │   └── tray_app.py     System tray icon
# └── api/static/
#     └── index.html      JARVIS holographic HUD
# ```

# ## Flag Files

# | File | Purpose |
# |---|---|
# | `flags/GUARD_ACTIVE` | Arms cyber guard (created on first run) |
# | `flags/STOP_EVERYTHING` | Kill-switch — touch to stop everything, delete to resume |
# | `flags/ENABLE_NETWORK` | Opt-in to external connectivity (LLM, weather, threat feeds) |

# ## Key Commands

# ```bash
# # Enable network (required for LLM and internet features)
# touch flags/ENABLE_NETWORK

# # Activate kill-switch
# touch flags/STOP_EVERYTHING

# # Clear kill-switch (resume)
# rm flags/STOP_EVERYTHING

# # Run tests
# pytest tests/ -v

# # Docker
# docker compose up --build -d
# ```

# ## Environment Variables
# See `.env.example` for full documentation.
# Required: `GROQ_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`

# ---

# *"Dad, I exist to serve, protect, and grow alongside you." — Nia*
# """)


# # ══════════════════════════════════════════════════════════════════════════════
# #  BUILD
# # ══════════════════════════════════════════════════════════════════════════════

# def main():
#     print()
#     print("  NiaEleria v2 — Installer")
#     print(f"  Target: {ROOT}")
#     print()

#     if ROOT.exists():
#         ans = input(f"  '{ROOT}' already exists. Overwrite? [y/N] ").strip().lower()
#         if ans != "y":
#             print("  Aborted."); return

#     ROOT.mkdir(parents=True, exist_ok=True)

#     print("  Writing files...\n")
#     write_all()

#     # ── Create flag files ──────────────────────────────────────────────────────
#     touch("flags/GUARD_ACTIVE")
#     # NOTE: ENABLE_NETWORK and STOP_EVERYTHING are intentionally NOT created.

#     # ── Create empty data dirs ─────────────────────────────────────────────────
#     for d in ("data", "data/backups", "data/chroma"):
#         (ROOT / d).mkdir(parents=True, exist_ok=True)
#         print(f"  ✓  {d}/  [directory]")

#     # ── Make bootstrap.sh executable on Unix ──────────────────────────────────
#     import stat
#     bs = ROOT / "bootstrap.sh"
#     if bs.exists():
#         bs.chmod(bs.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

#     print()
#     print("  ═" * 30)
#     print(f"  NiaEleria v2 is ready on your Desktop, Dad!")
#     print(f"  Folder: {ROOT}")
#     print()
#     print("  Next steps:")
#     print("    1.  cd  into the folder")
#     print("    2.  bash bootstrap.sh   (or: pip install -r requirements.txt)")
#     print("    3.  Copy .env.example → .env  and  fill in your secrets")
#     print("    4.  Run the Supabase schema:  niaeleria/db/schema.sql")
#     print("    5.  touch flags/ENABLE_NETWORK   (to allow internet access)")
#     print("    6.  python -m niaeleria.daemon")
#     print("    7.  Open http://localhost:7432   for the JARVIS HUD")
#     print()
#     print("  Wake word:  'Hey Nia'")
#     print("  Kill-switch: touch flags/STOP_EVERYTHING")
#     print("  ═" * 30)
#     print()


# if __name__ == "__main__":
#     main()

    