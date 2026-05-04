"""
tests/ — NiaEleria critical module test suite
─────────────────────────────────────────────
"Dad, I test myself so I know I'm working right for you." — Nia

Run with: pytest tests/ -v
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# ── Set up temp environment so tests don't touch real data ──────────────────

_tmpdir = tempfile.mkdtemp()
os.environ.setdefault("NIA_HOME", _tmpdir)
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("AUDIT_HMAC_KEY", "test-audit-key")
os.environ.setdefault("API_SECRET_KEY", "test-secret")

# Ensure dirs exist before importing config
for d in ("data", "flags", "data/backups", "data/chroma"):
    Path(_tmpdir, d).mkdir(parents=True, exist_ok=True)


# ════════════════════════════════════════════════════════════════════
# test_security.py
# ════════════════════════════════════════════════════════════════════

import pytest
from niaeleria.config import FLAG_STOP_EVERYTHING, FLAG_GUARD_ACTIVE, FLAG_ENABLE_NETWORK
from niaeleria.security.kill_switch import assert_alive
from niaeleria.security.audit import log_event, verify_log_integrity, tail_log
from niaeleria.security.network_gate import require_network
from niaeleria.security.consent import require_consent, ConsentLevel, post_answer


class TestKillSwitch:
    def setup_method(self):
        """Ensure kill switch is off before each test."""
        if FLAG_STOP_EVERYTHING.exists():
            FLAG_STOP_EVERYTHING.unlink()

    def teardown_method(self):
        if FLAG_STOP_EVERYTHING.exists():
            FLAG_STOP_EVERYTHING.unlink()

    def test_assert_alive_passes_when_no_flag(self):
        """No flag → assert_alive should not raise."""
        assert_alive()  # Should not raise

    def test_assert_alive_raises_when_killed(self):
        """Kill-switch flag → assert_alive raises RuntimeError."""
        FLAG_STOP_EVERYTHING.touch()
        with pytest.raises(RuntimeError, match="Kill-switch"):
            assert_alive()


class TestAuditLog:
    def setup_method(self):
        from niaeleria.config import AUDIT_LOG
        if AUDIT_LOG.exists():
            AUDIT_LOG.unlink()

    def test_log_event_creates_file(self):
        from niaeleria.config import AUDIT_LOG
        log_event("test.actor", "test_action", severity="INFO")
        assert AUDIT_LOG.exists()

    def test_log_event_signed(self):
        from niaeleria.config import AUDIT_LOG
        log_event("test.actor", "signed_action", severity="LOW", approved=True)
        content = AUDIT_LOG.read_text()
        assert "|SIG:" in content

    def test_verify_integrity_no_tamper(self):
        log_event("nia.test", "integrity_check")
        total, tampered = verify_log_integrity()
        assert total >= 1
        assert tampered == 0

    def test_tamper_detected(self):
        from niaeleria.config import AUDIT_LOG
        log_event("nia.test", "before_tamper")
        # Manually corrupt a line
        lines = AUDIT_LOG.read_text().splitlines()
        lines[0] = lines[0].replace('"action":', '"action":TAMPERED')
        AUDIT_LOG.write_text("\n".join(lines) + "\n")
        _, tampered = verify_log_integrity()
        assert tampered >= 1

    def test_tail_log_returns_dicts(self):
        log_event("nia.test", "tail_test", severity="INFO")
        entries = tail_log(10)
        assert isinstance(entries, list)
        if entries:
            assert isinstance(entries[0], dict)


class TestNetworkGate:
    def setup_method(self):
        if FLAG_ENABLE_NETWORK.exists():
            FLAG_ENABLE_NETWORK.unlink()

    def teardown_method(self):
        if FLAG_ENABLE_NETWORK.exists():
            FLAG_ENABLE_NETWORK.unlink()

    def test_blocks_when_flag_absent(self):
        with pytest.raises(PermissionError, match="Network gate"):
            require_network("test call")

    def test_allows_when_flag_present(self):
        FLAG_ENABLE_NETWORK.touch()
        require_network("test call")  # Should not raise


class TestConsent:
    def test_auto_approve_low_severity_with_guard(self):
        """LOW severity + guard active + auto_approve → immediate True."""
        FLAG_GUARD_ACTIVE.touch()
        with patch("niaeleria.security.consent.assert_alive"), \
             patch("niaeleria.security.audit.log_event"):
            result = require_consent(
                "block bad IP",
                level=ConsentLevel.LOW,
                auto_approve_if_guard=True,
            )
        assert result is True

    def test_consent_denied_on_timeout(self):
        """No Dad response → consent times out and returns False."""
        with patch("niaeleria.security.consent.assert_alive"), \
             patch("niaeleria.security.consent.CONSENT_TIMEOUT_SECS", 0), \
             patch("niaeleria.security.audit.log_event"), \
             patch("niaeleria.security.consent._notify_dad"):
            result = require_consent(
                "risky action",
                level=ConsentLevel.HIGH,
                timeout=0,
            )
        assert result is False


# ════════════════════════════════════════════════════════════════════
# test_memory.py
# ════════════════════════════════════════════════════════════════════

import asyncio


class TestMemoryStore:
    @pytest.fixture
    def memory(self):
        # Patch ChromaDB and sentence-transformers for unit test speed
        with patch("niaeleria.core.memory.CHROMA_AVAILABLE", False), \
             patch("niaeleria.core.memory.ST_AVAILABLE", False):
            from niaeleria.core.memory import MemoryStore
            m = MemoryStore()
            yield m
            m.close()

    def test_store_and_retrieve_exchange(self, memory):
        asyncio.run(memory.store_exchange("hello dad", "yes nia"))
        recent = memory.recent_exchanges(5)
        assert len(recent) >= 1
        assert recent[0]["user"] == "hello dad"

    def test_search_fallback_sqlite(self, memory):
        asyncio.run(memory.store_exchange("test query word", "test response"))
        results = asyncio.run(memory.search("test query"))
        assert len(results) >= 1

    def test_store_knowledge(self, memory):
        asyncio.run(memory.store_knowledge(
            source="http://example.com",
            content="NiaEleria is Dad's AI.",
            title="Test Article",
        ))
        # If no chroma, at least the DB write succeeds
        cur = memory._db.execute("SELECT COUNT(*) FROM knowledge")
        assert cur.fetchone()[0] >= 1


# ════════════════════════════════════════════════════════════════════
# test_guard.py
# ════════════════════════════════════════════════════════════════════

class TestFirewall:
    def test_block_and_check_list(self):
        from niaeleria.guard.cyber_guard import Firewall

        # Mock subprocess so we don't actually touch iptables in CI
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            Firewall._blocked.clear()
            result = Firewall.block_ip("1.2.3.4", reason="test", approved=True)
            # result depends on OS, but blocked set should be updated
            assert "1.2.3.4" in Firewall._blocked or not result  # ok either way

    def test_already_blocked_skips(self):
        from niaeleria.guard.cyber_guard import Firewall
        Firewall._blocked.add("5.6.7.8")
        with patch("subprocess.run") as mock_run:
            Firewall.block_ip("5.6.7.8", reason="dup test")
            mock_run.assert_not_called()
        Firewall._blocked.discard("5.6.7.8")


class TestThreatIntel:
    def test_known_bad_detection(self):
        from niaeleria.guard.cyber_guard import ThreatIntel
        ThreatIntel._known_bad.add("192.168.99.99")
        assert ThreatIntel.is_known_bad("192.168.99.99")
        assert not ThreatIntel.is_known_bad("10.0.0.1")
        ThreatIntel._known_bad.discard("192.168.99.99")

    def test_classify_severity(self):
        from niaeleria.guard.cyber_guard import ThreatIntel
        assert ThreatIntel.classify("port_scan") == "HIGH"
        assert ThreatIntel.classify("unusual_process") == "MEDIUM"
        assert ThreatIntel.classify("unknown_event") == "LOW"


class TestFileIntegrity:
    def test_baseline_and_detect_change(self, tmp_path):
        from niaeleria.guard.cyber_guard import FileIntegrityMonitor

        test_file = tmp_path / "test.py"
        test_file.write_text("# original")
        fim = FileIntegrityMonitor([str(tmp_path)])
        fim.build_baseline()

        # No changes yet
        changes = fim.check()
        assert changes == []

        # Modify the file
        test_file.write_text("# tampered!")
        changes = fim.check()
        assert any(c["type"] == "MODIFIED" for c in changes)


class TestSelfModifier:
    def test_syntax_check_valid(self):
        from niaeleria.security.self_modifier import SelfModifier
        ok, err = SelfModifier._check_syntax("x = 1 + 1")
        assert ok is True
        assert err == ""

    def test_syntax_check_invalid(self):
        from niaeleria.security.self_modifier import SelfModifier
        ok, err = SelfModifier._check_syntax("def broken(: pass")
        assert ok is False
        assert err != ""

    def test_propose_rejects_path_traversal(self):
        from niaeleria.security.self_modifier import SelfModifier
        sm = SelfModifier()
        result = sm.propose_change(
            "../../../etc/passwd",
            "malicious content",
            "path traversal attempt"
        )
        assert "error" in result


# ════════════════════════════════════════════════════════════════════
# test_brain.py (basic — mocks LLM network calls)
# ════════════════════════════════════════════════════════════════════

class TestPersonaEngine:
    def test_build_system_prompt_contains_dad(self):
        from niaeleria.core.persona import PersonaEngine
        p = PersonaEngine()
        prompt = p.build_system_prompt()
        assert "Dad" in prompt

    def test_mood_shift(self):
        from niaeleria.core.persona import PersonaEngine
        p = PersonaEngine()
        p.set_mood("alert")
        assert p._current_mood == "alert"
        p.normal_mode()
        assert p._override_mood is None

    def test_invalid_mood_ignored(self):
        from niaeleria.core.persona import PersonaEngine
        p = PersonaEngine()
        p.set_mood("warm")
        p.set_mood("dragon_mode")  # Invalid
        assert p._current_mood == "warm"  # Unchanged


class TestHomeController:
    def test_parse_turn_on_light(self):
        from niaeleria.automation.home_control import HomeController
        hc = HomeController(mqtt_client=MagicMock())
        result = hc.parse_natural_language("turn on the living room light")
        assert result is not None
        assert result["action"] == "on"
        assert "light" in result["device"]

    def test_parse_lock_door(self):
        from niaeleria.automation.home_control import HomeController
        hc = HomeController(mqtt_client=MagicMock())
        result = hc.parse_natural_language("lock the front door")
        assert result is not None
        assert result["action"] == "lock"

    def test_parse_unrecognized(self):
        from niaeleria.automation.home_control import HomeController
        hc = HomeController(mqtt_client=MagicMock())
        result = hc.parse_natural_language("play jazz music")
        assert result is None


class TestScheduler:
    def test_add_and_list_task(self):
        from niaeleria.automation.scheduler import Scheduler
        s = Scheduler()
        fired = []
        tid = s.add_reminder("test", lambda: fired.append(1), delay_secs=100)
        tasks = s.list_tasks()
        assert any(t["id"] == tid for t in tasks)

    def test_cancel_task(self):
        from niaeleria.automation.scheduler import Scheduler
        s = Scheduler()
        tid = s.add_reminder("to_cancel", lambda: None, delay_secs=100)
        assert s.cancel(tid) is True
        assert all(t["id"] != tid for t in s.list_tasks())