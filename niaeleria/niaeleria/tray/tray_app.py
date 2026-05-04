"""
niaeleria/tray/tray_app.py  — System tray icon with voice popup

"Dad, I live in your taskbar and I run in the background — always here." — Nia
"""

from __future__ import annotations

# ════════════════════════════════════════════════════════════════════
# tray_app.py
# Save as: niaeleria/tray/tray_app.py
# ════════════════════════════════════════════════════════════════════

import logging
import threading
from typing import Optional

log = logging.getLogger("nia.tray")


class NiaTray:
    """
    System tray icon for NiaEleria.
    Provides a quick-access popup for voice interaction on the desktop.
    Uses pystray + PIL for the icon.

    "Dad, I'm always in your taskbar — one click and I'm here." — Nia
    """

    def __init__(self, voice_interface=None, tts=None, stt=None, brain=None) -> None:
        self._voice = voice_interface
        self._tts = tts
        self._stt = stt
        self._brain = brain
        self._icon = None
        self._available = False

        try:
            import pystray
            from PIL import Image
            self._pystray = pystray
            self._Image = Image
            self._available = True
        except ImportError:
            log.warning(
                "Dad, pystray or Pillow not installed — system tray is disabled. "
                "Run: pip install pystray Pillow"
            )

    def _create_icon_image(self):
        """Create a simple Nia icon (cyan circle with 'N')."""
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([4, 4, 60, 60], fill=(0, 200, 200, 255))
        try:
            from PIL import ImageFont
            font = ImageFont.truetype("arial.ttf", 32)
        except Exception:
            font = None
        draw.text((20, 14), "N", fill=(255, 255, 255), font=font)
        return img

    def start(self) -> None:
        if not self._available:
            return

        menu = self._pystray.Menu(
            self._pystray.MenuItem("Talk to Nia", self._on_talk),
            self._pystray.MenuItem("Open Dashboard", self._on_dashboard),
            self._pystray.MenuItem("Guard Status", self._on_guard_status),
            self._pystray.MenuItem("Morning Briefing", self._on_briefing),
            self._pystray.MenuItem("─────────", lambda: None, enabled=False),
            self._pystray.MenuItem("Kill Switch 🔴", self._on_kill_switch),
            self._pystray.MenuItem("Exit", self._on_exit),
        )

        icon_img = self._create_icon_image()
        self._icon = self._pystray.Icon(
            "NiaEleria",
            icon_img,
            "NiaEleria — Dad's AI",
            menu,
        )

        t = threading.Thread(target=self._icon.run, name="SystemTray", daemon=True)
        t.start()
        log.info("Dad, I'm in your system tray. Right-click my icon anytime.")

    def _on_talk(self, icon, item) -> None:
        """Wake voice interface from tray."""
        if self._voice:
            threading.Thread(
                target=self._voice._handle_command, daemon=True, name="TrayVoice"
            ).start()
        elif self._tts:
            self._tts.speak("Yes Dad? I didn't catch that. Try the voice button.")

    def _on_dashboard(self, icon, item) -> None:
        """Open the web dashboard in the default browser."""
        import webbrowser
        from niaeleria.config import API_HOST, API_PORT
        url = f"http://{API_HOST}:{API_PORT}"
        webbrowser.open(url)
        log.info("Dad, opening dashboard: %s", url)

    def _on_guard_status(self, icon, item) -> None:
        """Speak a brief guard status report."""
        if not self._tts:
            return
        from niaeleria.config import is_guard_active, is_killed, FLAG_STOP_EVERYTHING
        from niaeleria.guard.cyber_guard import Firewall

        if is_killed():
            self._tts.speak("Dad, the kill switch is active. I'm in standby.")
            return

        blocked = len(Firewall.get_blocked())
        guard = "armed" if is_guard_active() else "disarmed"
        self._tts.speak(
            f"Dad, my cyber guard is {guard}. "
            f"I've blocked {blocked} IP address{'es' if blocked != 1 else ''} so far today."
        )

    def _on_briefing(self, icon, item) -> None:
        """Trigger morning briefing from tray."""
        import asyncio
        from niaeleria.api.server import _brain, _scheduler, _guard, _tts

        def _run():
            from niaeleria.automation.briefing import MorningBriefing
            briefing = MorningBriefing(
                tts=_tts,
                scheduler=_scheduler,
                guard_status_fn=lambda: _guard.status() if _guard else {},
                brain=_brain,
            )
            loop = asyncio.new_event_loop()
            loop.run_until_complete(briefing.deliver())
            loop.close()

        threading.Thread(target=_run, daemon=True, name="TrayBriefing").start()

    def _on_kill_switch(self, icon, item) -> None:
        """Toggle the kill-switch from the tray."""
        from niaeleria.config import FLAG_STOP_EVERYTHING, is_killed
        if is_killed():
            FLAG_STOP_EVERYTHING.unlink(missing_ok=True)
            log.info("Dad, kill-switch CLEARED from tray.")
            if self._tts:
                self._tts.speak("Dad, I'm back online.")
        else:
            FLAG_STOP_EVERYTHING.touch()
            log.critical("Dad, kill-switch ACTIVATED from tray.")

    def _on_exit(self, icon, item) -> None:
        """Graceful exit from tray."""
        from niaeleria.config import FLAG_STOP_EVERYTHING
        log.info("Dad, exit requested from tray. Shutting down.")
        FLAG_STOP_EVERYTHING.touch()
        icon.stop()

    def stop(self) -> None:
        if self._icon:
            self._icon.stop()


