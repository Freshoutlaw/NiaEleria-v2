"""
niaeleria/voice/wake_word.py
─────────────────────────────
"Hey Nia" wake-word detection — no PyAudio required.

Priority chain:
  1. Porcupine (pvporcupine)  — accurate, sub-100ms, fully offline
     Uses sounddevice for mic input instead of PyAudio.
  2. Keyword fallback         — continuous STT clips checked for wake phrase
     Uses SpeechToText (sounddevice-based) internally.

"Dad, just say my name. I'm always listening." — Nia
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable

from niaeleria.config import WAKE_WORD, PORCUPINE_ACCESS_KEY, WAKE_WORD_MODEL_PATH, is_killed
from niaeleria.security.kill_switch import assert_alive

log = logging.getLogger("nia.wake_word")


class WakeWordDetector:
    """
    Listens continuously in the background for "Hey Nia".
    Fires on_wake() callback when detected.
    No PyAudio dependency — uses sounddevice for all audio I/O.
    """

    def __init__(self, on_wake: Callable[[], None]) -> None:
        self._on_wake        = on_wake
        self._running        = False
        self._use_porcupine  = bool(PORCUPINE_ACCESS_KEY or WAKE_WORD_MODEL_PATH)
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._running = True
        target = self._porcupine_loop if self._use_porcupine else self._keyword_loop
        self._thread = threading.Thread(
            target=target, name="WakeWord", daemon=True
        )
        self._thread.start()
        log.info(
            "Dad, I'm listening for '%s' via %s.",
            WAKE_WORD,
            "Porcupine" if self._use_porcupine else "keyword fallback",
        )

    def stop(self) -> None:
        self._running = False
        log.info("Dad, wake-word listener stopped.")

    # ── Porcupine (accurate, offline, sounddevice mic) ─────────────

    def _porcupine_loop(self) -> None:
        try:
            import pvporcupine
            import sounddevice as sd
            import numpy as np
            import struct

            create_args = {
                "access_key": PORCUPINE_ACCESS_KEY,
            }
            if WAKE_WORD_MODEL_PATH:
                create_args["keyword_paths"] = [WAKE_WORD_MODEL_PATH]
                log.info("Using custom wake-word model: %s", WAKE_WORD_MODEL_PATH)
            else:
                create_args["keywords"] = ["hey siri"]

            porcupine = pvporcupine.create(**create_args)
            frame_len  = porcupine.frame_length
            samplerate = porcupine.sample_rate

            log.debug(
                "Porcupine ready — frame_length=%d, sample_rate=%d",
                frame_len, samplerate,
            )

            with sd.InputStream(
                samplerate=samplerate,
                channels=1,
                dtype="int16",
                blocksize=frame_len,
            ) as stream:
                while self._running:
                    assert_alive()
                    pcm_chunk, _overflow = stream.read(frame_len)
                    pcm = pcm_chunk.flatten().tolist()
                    idx = porcupine.process(pcm)
                    if idx >= 0:
                        log.info("Dad, wake word detected via Porcupine!")
                        self._on_wake()
                        time.sleep(1.0)  # brief pause to avoid double-fire

        except ImportError:
            log.warning("pvporcupine not installed — switching to keyword fallback.")
            self._keyword_loop()
        except Exception as exc:
            log.error("Porcupine error: %s — switching to keyword fallback.", exc)
            self._keyword_loop()

    # ── Keyword fallback (sounddevice-based STT clips) ─────────────

    def _keyword_loop(self) -> None:
        """
        Continuously record short audio clips and transcribe them.
        If the wake phrase is detected in the transcription, fire on_wake().
        Uses our PyAudio-free SpeechToText internally.
        """
        try:
            import sounddevice as sd   # confirm available
        except ImportError:
            log.error(
                "Dad, sounddevice not installed — wake word disabled. "
                "Run: pip install sounddevice"
            )
            return

        from niaeleria.voice.stt import SpeechToText
        stt = SpeechToText()

        if not stt._available:
            log.error("Dad, STT unavailable — wake word listener cannot start.")
            return

        wake_lower = WAKE_WORD.lower()
        log.info(
            "Dad, keyword fallback active — listening for '%s'.", WAKE_WORD
        )

        while self._running:
            try:
                assert_alive()
            except RuntimeError:
                break

            text = stt.listen_for_wake_word()

            if text and wake_lower in text.lower():
                log.info("Dad, wake phrase detected: '%s'", text)
                self._on_wake()
                time.sleep(1.5)   # prevent immediate re-trigger
            else:
                time.sleep(0.1)   # tiny pause before next clip