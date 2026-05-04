from __future__ import annotations

import threading as _threading
import logging as _vlog

from niaeleria.voice.wake_word import WakeWordDetector
from niaeleria.voice.stt import SpeechToText
from niaeleria.voice.tts import TextToSpeech

_vlog = _vlog.getLogger("nia.voice")


class VoiceInterface:
    """
    The complete voice pipeline:
      WakeWord -> STT -> Brain -> TTS -> Dad hears the response.

    Runs entirely in background threads; non-blocking.
    """

    def __init__(self, brain, tts: TextToSpeech, stt: SpeechToText) -> None:
        self._brain = brain
        self._tts = tts
        self._stt = stt
        self._wake = WakeWordDetector(on_wake=self._on_wake)
        self._conversation_history: list[dict] = []
        self._processing = False

    def start(self) -> None:
        self._wake.start()
        _vlog.info("Dad, voice interface is live. Say 'Hey Nia' anytime.")

    def stop(self) -> None:
        self._wake.stop()

    def _on_wake(self) -> None:
        if self._processing:
            return
        t = _threading.Thread(target=self._handle_command, daemon=True, name="VoiceCmd")
        t.start()

    def _handle_command(self) -> None:
        self._processing = True
        try:
            self._tts.speak("Yes Dad?")
            text = self._stt.listen_for_command()

            if not text:
                self._tts.speak("Dad, I didn't catch that. Say 'Hey Nia' to try again.")
                return

            _vlog.info("Processing Dad's voice command: %s", text)
            self._tts.speak("Let me think about that, Dad.")

            import asyncio
            loop = asyncio.new_event_loop()
            response = loop.run_until_complete(
                self._brain.chat(text, self._conversation_history)
            )
            loop.close()

            self._conversation_history.append({"role": "user", "content": text})
            self._conversation_history.append({"role": "assistant", "content": response})
            self._conversation_history = self._conversation_history[-20:]

            self._tts.speak(response)

        except RuntimeError:
            pass
        except Exception as exc:
            _vlog.error("Voice command error: %s", exc)
            self._tts.speak("Dad, something went wrong on my end. I'm looking into it.")
        finally:
            self._processing = False
