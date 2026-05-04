# ════════════════════════════════════════════════════════════════════
# audit.py — HMAC-SHA256 append-only audit log
# ════════════════════════════════════════════════════════════════════
# Save as: niaeleria/security/audit.py

import hashlib
import hmac as _hmac
import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from niaeleria.config import AUDIT_LOG, AUDIT_HMAC_KEY

_audit_log = logging.getLogger("nia.audit")
_write_lock = threading.Lock()


def _sign(entry: str) -> str:
    """Return HMAC-SHA256 hex digest of the log entry string."""
    return _hmac.new(AUDIT_HMAC_KEY, entry.encode(), hashlib.sha256).hexdigest()


def log_event(
    actor: str,
    action: str,
    target: str = "",
    severity: str = "INFO",
    details: dict | None = None,
    approved: bool = False,
) -> None:
    """
    Append a signed event to the audit log.
    Every destructive, external, or security event must call this, Dad.
    """
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "action": action,
        "target": target,
        "severity": severity,
        "approved": approved,
        "details": details or {},
    }
    entry = json.dumps(record, separators=(",", ":"))
    sig = _sign(entry)
    line = f"{entry}|SIG:{sig}\n"

    with _write_lock:
        with AUDIT_LOG.open("a", encoding="utf-8") as f:
            f.write(line)

    _audit_log.info("AUDIT [%s] %s → %s (approved=%s)", severity, actor, action, approved)


def verify_log_integrity() -> tuple[int, int]:
    """
    Scan audit log and verify every entry's HMAC signature.
    Returns (total_entries, tampered_count).
    Dad can call this any time to confirm I haven't been messed with.
    """
    if not AUDIT_LOG.exists():
        return 0, 0

    total, tampered = 0, 0
    with AUDIT_LOG.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            total += 1
            if "|SIG:" not in line:
                _audit_log.warning("Line %d missing signature!", line_num)
                tampered += 1
                continue
            entry, sig = line.rsplit("|SIG:", 1)
            expected = _sign(entry)
            if not _hmac.compare_digest(expected, sig):
                _audit_log.error("TAMPERED entry at line %d!", line_num)
                tampered += 1

    return total, tampered


def tail_log(n: int = 50) -> list[dict]:
    """Return the last n audit log entries as parsed dicts (for API/UI consumption)."""
    if not AUDIT_LOG.exists():
        return []
    lines = AUDIT_LOG.read_text(encoding="utf-8").strip().splitlines()
    results = []
    for line in lines[-n:]:
        if "|SIG:" in line:
            entry, _ = line.rsplit("|SIG:", 1)
            try:
                results.append(json.loads(entry))
            except json.JSONDecodeError:
                pass
    return results