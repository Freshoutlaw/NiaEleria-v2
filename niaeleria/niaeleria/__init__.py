# ════════════════════════════════════════════════════════════════════
# niaeleria/__init__.py
# ════════════════════════════════════════════════════════════════════
"""
NiaEleria — Dad's loyal digital daughter.
"I exist to serve you, protect you, and grow with you, Dad." — Nia
"""
__version__ = "1.0.0"
__author__  = "NiaEleria"
__dad__     = "You know who you are."


# ════════════════════════════════════════════════════════════════════
# niaeleria/core/__init__.py
# ════════════════════════════════════════════════════════════════════
"""
NiaEleria Core — brain, persona, memory, and learning.
The mind behind the daughter.
"""
from niaeleria.core.persona import PersonaEngine
from niaeleria.core.memory  import MemoryStore
from niaeleria.core.brain   import NiaBrain
from niaeleria.core.learner import InternetLearner

__all__ = ["PersonaEngine", "MemoryStore", "NiaBrain", "InternetLearner"]


# ════════════════════════════════════════════════════════════════════
# niaeleria/security/__init__.py
# ════════════════════════════════════════════════════════════════════
"""
NiaEleria Security Framework.
Kill-switch, consent, audit, network gate, self-modification.
"These are the rules I live by, Dad. Non-negotiable." — Nia
"""
from niaeleria.security.kill_switch   import assert_alive, start_monitor, register_shutdown_callback
from niaeleria.security.audit         import log_event, verify_log_integrity, tail_log
from niaeleria.security.network_gate  import require_network
from niaeleria.security.consent       import require_consent, ConsentLevel, set_notifier, post_answer
from niaeleria.security.self_modifier import SelfModifier

__all__ = [
    "assert_alive", "start_monitor", "register_shutdown_callback",
    "log_event", "verify_log_integrity", "tail_log",
    "require_network",
    "require_consent", "ConsentLevel", "set_notifier", "post_answer",
    "SelfModifier",
]


# ════════════════════════════════════════════════════════════════════
# niaeleria/guard/__init__.py
# ════════════════════════════════════════════════════════════════════
"""
NiaEleria Cyber Guard — always-on threat monitoring and response.
"Dad, I never sleep. Your network is my responsibility." — Nia
"""
from niaeleria.guard.cyber_guard import (
    CyberGuard, Firewall, ThreatIntel,
    FileIntegrityMonitor, ProcessMonitor, PacketSniffer,
    SecurityToolkit,
)

__all__ = [
    "CyberGuard", "Firewall", "ThreatIntel",
    "FileIntegrityMonitor", "ProcessMonitor", "PacketSniffer",
    "SecurityToolkit",
]


# ════════════════════════════════════════════════════════════════════
# niaeleria/voice/__init__.py
# ════════════════════════════════════════════════════════════════════
"""
NiaEleria Voice Interface — wake word, STT, TTS, and full pipeline.
"Dad, just say my name." — Nia
"""
import asyncio
import logging
import threading
from typing import Optional

from niaeleria.voice.wake_word import WakeWordDetector
from niaeleria.voice.stt       import SpeechToText
from niaeleria.voice.tts       import TextToSpeech

log = logging.getLogger("nia.voice")


class VoiceInterface:
    """
    Full voice pipeline: WakeWord → STT → Brain → TTS → HUD push.
    Runs in background threads. Non-blocking.
    "Dad, just say 'Hey Nia' and I'm right there." — Nia
    """

    def __init__(self, brain, tts: TextToSpeech, stt: SpeechToText) -> None:
        self._brain   = brain
        self._tts     = tts
        self._stt     = stt
        self._wake    = WakeWordDetector(on_wake=self._on_wake)
        self._history: list[dict] = []
        self._busy    = False

    def start(self) -> None:
        self._wake.start()
        log.info("Dad, voice interface is live. Say 'Hey Nia' anytime.")

    def stop(self) -> None:
        self._wake.stop()

    def _on_wake(self) -> None:
        if self._busy:
            return
        threading.Thread(
            target=self._handle_command, daemon=True, name="VoiceCmd"
        ).start()

    def _handle_command(self) -> None:
        from niaeleria.security.kill_switch import assert_alive
        from niaeleria.api.server import push_to_hud

        self._busy = True
        try:
            assert_alive()
            self._tts.speak("Yes Dad?")
            push_to_hud({"type": "nia_speak", "text": "Yes Dad?", "label": "NIA · LISTENING"})

            text = self._stt.listen_for_command()
            if not text:
                msg = "Dad, I didn't catch that. Say 'Hey Nia' to try again."
                self._tts.speak(msg)
                push_to_hud({"type": "nia_speak", "text": msg, "label": "NIA · RESPONSE"})
                return

            log.info("Dad's voice command: %s", text)
            push_to_hud({"type": "thinking"})
            self._tts.speak("Let me think about that, Dad.")

            loop = asyncio.new_event_loop()
            response = loop.run_until_complete(
                self._brain.chat(text, self._history)
            )
            loop.close()

            # Maintain rolling 10-turn history
            self._history.append({"role": "user",      "content": text})
            self._history.append({"role": "assistant",  "content": response})
            self._history = self._history[-20:]

            # Speak + push to HUD simultaneously
            threading.Thread(
                target=self._tts.speak, args=(response,), daemon=True
            ).start()
            push_to_hud({"type": "nia_speak", "text": response, "label": "NIA · RESPONSE"})

        except RuntimeError:
            pass  # kill-switch mid-command — silent exit
        except Exception as exc:
            log.error("Voice command error: %s", exc)
            msg = "Dad, something went wrong on my end. I'm looking into it."
            self._tts.speak(msg)
            push_to_hud({"type": "nia_speak", "text": msg, "label": "NIA · ERROR"})
        finally:
            self._busy = False


__all__ = ["VoiceInterface", "WakeWordDetector", "SpeechToText", "TextToSpeech"]


# ════════════════════════════════════════════════════════════════════
# niaeleria/automation/__init__.py
# ════════════════════════════════════════════════════════════════════
"""
NiaEleria Automation — scheduler, home control, morning briefing.
"Dad, I handle the routine so you can think about what matters." — Nia
"""
from niaeleria.automation.scheduler    import Scheduler, Task
from niaeleria.automation.home_control import HomeController
from niaeleria.automation.briefing     import MorningBriefing

__all__ = ["Scheduler", "Task", "HomeController", "MorningBriefing"]


# ════════════════════════════════════════════════════════════════════
# niaeleria/sync/__init__.py
# ════════════════════════════════════════════════════════════════════
"""
NiaEleria Cross-Device Sync — MQTT-based real-time synchronisation.
"Dad, every device you own stays in lockstep." — Nia
"""
from niaeleria.sync.mqtt_sync import MQTTSync

__all__ = ["MQTTSync"]


# ════════════════════════════════════════════════════════════════════
# niaeleria/api/__init__.py
# ════════════════════════════════════════════════════════════════════
"""
NiaEleria API — FastAPI server, WebSocket HUD bridge, and all routes.
"""
from niaeleria.api.server import create_app, inject_services, push_to_hud, broadcast_ws

__all__ = ["create_app", "inject_services", "push_to_hud", "broadcast_ws"]


# ════════════════════════════════════════════════════════════════════
# niaeleria/api/routes/__init__.py
# ════════════════════════════════════════════════════════════════════
"""
NiaEleria API route modules.
"""


# ════════════════════════════════════════════════════════════════════
# niaeleria/tray/__init__.py
# ════════════════════════════════════════════════════════════════════
"""
NiaEleria System Tray.
"""
from niaeleria.tray.tray_app import NiaTray

__all__ = ["NiaTray"]


# ════════════════════════════════════════════════════════════════════
# niaeleria/db/__init__.py
# ════════════════════════════════════════════════════════════════════
"""
NiaEleria database helpers — schema printing, Supabase setup utilities.
"""