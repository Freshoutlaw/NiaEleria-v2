from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Optional

from niaeleria.config import PROJECT_HOME
from niaeleria.security.audit import log_event

log = logging.getLogger("nia.guard")


class ThreatIntel:
    """
    Manages a local threat IP blocklist.
    Refreshed from the internet feed (when ENABLE_NETWORK is set).
    Also scores individual IPs/activities with a severity classifier.

    "Dad, I know the bad guys by reputation — and I keep an up-to-date list." — Nia
    """

    _known_bad: set[str] = set()
    _lock = threading.Lock()

    SEVERITY_RULES = {
        "port_scan": "HIGH",
        "repeated_auth_failure": "HIGH",
        "unusual_process": "MEDIUM",
        "outbound_unknown": "MEDIUM",
        "file_tamper": "HIGH",
    }

    @classmethod
    def load_feed(cls, feed_path: Optional[Path] = None) -> int:
        """Load IP blocklist from a local file. Returns count of IPs loaded."""
        if feed_path is None:
            feed_path = PROJECT_HOME / "data" / "threat_feed.txt"
        if not feed_path.exists():
            log.info("Dad, no local threat feed yet — run update_threat_feed() to download one.")
            return 0
        with cls._lock:
            cls._known_bad.clear()
            with feed_path.open() as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        cls._known_bad.add(line.split()[0])
        log.info("Dad, I loaded %d known-bad IPs into threat intel.", len(cls._known_bad))
        return len(cls._known_bad)

    @classmethod
    def is_known_bad(cls, ip: str) -> bool:
        return ip in cls._known_bad

    @classmethod
    def classify(cls, event_type: str) -> str:
        return cls.SEVERITY_RULES.get(event_type, "LOW")

    @classmethod
    async def update_feed(cls) -> int:
        """Download latest threat feed (requires ENABLE_NETWORK)."""
        from niaeleria.security.network_gate import require_network
        require_network("threat intel feed update")
        import httpx
        from niaeleria.config import THREAT_INTEL_FEED

        feed_path = PROJECT_HOME / "data" / "threat_feed.txt"
        log.info("Dad, downloading latest threat intelligence feed...")
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(THREAT_INTEL_FEED)
            resp.raise_for_status()
            feed_path.write_bytes(resp.content)
        return cls.load_feed(feed_path)
