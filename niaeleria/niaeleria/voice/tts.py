"""
niaeleria/voice/tts.py
───────────────────────
NiaEleria's voice output — powered by ElevenLabs neural TTS.
No PyAudio required. Audio is played via sounddevice + numpy.

Priority chain:
  1. ElevenLabs API  (best quality — Dad hears a real voice)
  2. edge-tts        (fallback — still neural, no API key needed)
  3. pyttsx3         (last resort — offline, robotic but functional)
  4. Log-only        (silent fallback if nothing is installed)

"Dad, I don't sound like a robot — I sound like me." — Nia
"""

from __future__ import annotations

import io
import logging
import os
import tempfile
import threading
from typing import Optional

log = logging.getLogger("nia.tts")

# ── Config from env ────────────────────────────────────────────────
ELEVENLABS_API_KEY:  str = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "Rachel")
ELEVENLABS_MODEL:    str = os.getenv("ELEVENLABS_MODEL",    "eleven_turbo_v2")


class TextToSpeech:
    """
    NiaEleria's voice output — ElevenLabs primary, graceful fallback chain.
    Thread-safe: speak() can be called from any thread.
    Kill-switch respected before every utterance.

    "Dad, you should hear my voice — I think you'll like it." — Nia
    """

    def __init__(self) -> None:
        self._lock    = threading.Lock()   # prevent overlapping speech
        self._el      = self._init_elevenlabs()
        self._edge_ok = self._check_edge_tts()
        self._pyttsx3 = self._init_pyttsx3()
        self._sd_ok   = self._check_sounddevice()

        if self._el:
            log.info("Dad, ElevenLabs voice is ready (voice: %s).", ELEVENLABS_VOICE_ID)
        elif self._edge_ok:
            log.info("Dad, edge-tts fallback voice is ready.")
        elif self._pyttsx3:
            log.info("Dad, pyttsx3 fallback voice is ready.")
        else:
            log.warning("Dad, no TTS engine found. I'll log speech instead of speaking.")

    # ── Public API ─────────────────────────────────────────────────

    def speak(self, text: str) -> None:
        """Speak text aloud. Blocks until audio finishes."""
        from niaeleria.security.kill_switch import assert_alive
        try:
            assert_alive()
        except RuntimeError:
            return   # kill-switch — stay silent

        if not text or not text.strip():
            return

        log.debug("Nia speaking to Dad: %.80s...", text)

        with self._lock:
            if self._el:
                if self._speak_elevenlabs(text):
                    return
                log.warning("ElevenLabs failed — trying fallback chain.")

            if self._edge_ok:
                if self._speak_edge(text):
                    return
                log.warning("edge-tts failed — trying pyttsx3.")

            if self._pyttsx3:
                self._speak_pyttsx3(text)
                return

            # Absolute last resort — just log it
            log.info("[TTS SILENT] Nia would say: %s", text)

    def speak_async(self, text: str) -> None:
        """Non-blocking speak — fires and forgets in a daemon thread."""
        threading.Thread(
            target=self.speak, args=(text,), daemon=True, name="NiaTTS"
        ).start()

    # ── ElevenLabs ─────────────────────────────────────────────────

    def _init_elevenlabs(self):
        if not ELEVENLABS_API_KEY:
            log.info(
                "Dad, ELEVENLABS_API_KEY not set — "
                "ElevenLabs TTS disabled. Add it to .env to enable."
            )
            return None
        try:
            from elevenlabs.client import ElevenLabs
            client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
            return client
        except ImportError:
            log.warning(
                "Dad, elevenlabs package not installed. "
                "Run: pip install elevenlabs"
            )
            return None
        except Exception as exc:
            log.warning("ElevenLabs init error: %s", exc)
            return None

    def _speak_elevenlabs(self, text: str) -> bool:
        """Generate audio via ElevenLabs API and play it. Returns True on success."""
        try:
            from elevenlabs import VoiceSettings

            audio_gen = self._el.text_to_speech.convert(
                text=text,
                voice_id=ELEVENLABS_VOICE_ID,
                model_id=ELEVENLABS_MODEL,
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.8,
                    style=0.2,
                    use_speaker_boost=True,
                ),
                output_format="mp3_44100_128",
            )

            # Collect all audio bytes
            audio_bytes = b"".join(audio_gen)

            # Play via sounddevice (no PyAudio)
            if self._sd_ok and self._play_with_sounddevice(audio_bytes, fmt="mp3"):
                return True

            # Fallback: write to temp file and play with OS player
            return self._play_audio_file(audio_bytes, suffix=".mp3")

        except Exception as exc:
            message = str(exc).lower()
            if "401" in message or "unauthorized" in message or "detected_unusual_activity" in message:
                log.warning(
                    "ElevenLabs API blocked or unauthorized — disabling ElevenLabs for this session."
                )
                self._el = None
            log.error("ElevenLabs speak error: %s", exc)
            return False

    # ── edge-tts ───────────────────────────────────────────────────

    def _check_edge_tts(self) -> bool:
        try:
            import edge_tts  # noqa: F401
            return True
        except ImportError:
            return False

    def _speak_edge(self, text: str) -> bool:
        """Generate audio via edge-tts and play it. Returns True on success."""
        try:
            import asyncio
            import edge_tts

            voice = os.getenv("TTS_VOICE", "en-US-AriaNeural")
            rate  = os.getenv("TTS_RATE",  "+0%")

            communicate = edge_tts.Communicate(
                text,
                voice=voice,
                rate=rate,
            )

            # Run async in a new loop (we're in a sync thread)
            audio_bytes = b""

            async def _collect():
                nonlocal audio_bytes
                chunks = []
                async for chunk in communicate.stream(
                    audio_format="riff-16khz-16bit-mono-pcm"
                ):
                    if chunk["type"] == "audio":
                        chunks.append(chunk["data"])
                audio_bytes = b"".join(chunks)

            loop = asyncio.new_event_loop()
            task = loop.create_task(_collect())
            try:
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(task)
                except RuntimeError as exc:
                    if "running event loop" in str(exc).lower():
                        try:
                            import nest_asyncio
                            nest_asyncio.apply(loop)
                            loop.run_until_complete(task)
                        except ImportError:
                            log.warning(
                                "nest_asyncio not installed — edge-tts may not work if an event loop is already running."
                            )
                            raise
                    else:
                        raise
            finally:
                if not task.done():
                    task.cancel()
                asyncio.set_event_loop(None)
                loop.close()

            if not audio_bytes:
                return False

            if self._sd_ok and self._play_with_sounddevice(audio_bytes, fmt="wav"):
                return True

            return self._play_audio_file(audio_bytes, suffix=".wav")

        except Exception as exc:
            log.error("edge-tts speak error: %s", exc)
            return False

    # ── pyttsx3 ────────────────────────────────────────────────────

    def _init_pyttsx3(self):
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", 175)
            voices = engine.getProperty("voices")
            # Try to pick a female voice
            for v in (voices or []):
                if "female" in v.name.lower() or "zira" in v.name.lower():
                    engine.setProperty("voice", v.id)
                    break
            return engine
        except ImportError:
            return None
        except Exception as exc:
            log.debug("pyttsx3 init error: %s", exc)
            return None

    def _speak_pyttsx3(self, text: str) -> None:
        try:
            log.info("pyttsx3 speaking fallback voice.")
            self._pyttsx3.say(text)
            self._pyttsx3.runAndWait()
        except Exception as exc:
            log.error("pyttsx3 speak error: %s", exc)

    # ── Audio playback helpers ─────────────────────────────────────

    def _check_sounddevice(self) -> bool:
        try:
            import sounddevice  # noqa: F401
            import numpy        # noqa: F401
            return True
        except ImportError:
            return False

    def _play_with_sounddevice(self, audio_bytes: bytes, fmt: str = "mp3") -> bool:
        """
        Decode audio bytes and play via sounddevice (no PyAudio required).
        Supports mp3 and wav.
        """
        try:
            import sounddevice as sd
            import numpy as np

            if fmt == "mp3":
                # Decode mp3 → pcm using pydub (if available) or soundfile
                pcm, samplerate = self._decode_mp3(audio_bytes)
            else:
                import soundfile as sf
                buf = io.BytesIO(audio_bytes)
                pcm, samplerate = sf.read(buf, dtype="float32")

            if pcm is None:
                return False

            sd.play(pcm, samplerate=samplerate, blocking=True)
            return True

        except Exception as exc:
            log.debug("sounddevice playback error: %s", exc)
            return False

    @staticmethod
    def _decode_mp3(audio_bytes: bytes):
        """Decode MP3 bytes to numpy float32 array + sample rate."""
        # Try pydub first (most reliable)
        try:
            from pydub import AudioSegment
            import numpy as np
            seg = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
            samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
            samples /= (2 ** (seg.sample_width * 8 - 1))  # normalise to [-1, 1]
            if seg.channels == 2:
                samples = samples.reshape((-1, 2))
            return samples, seg.frame_rate
        except ImportError:
            pass

        # Try soundfile (works if ffmpeg is available)
        try:
            import soundfile as sf
            buf = io.BytesIO(audio_bytes)
            return sf.read(buf, dtype="float32")
        except Exception:
            pass

        return None, None

    @staticmethod
    def _play_audio_file(audio_bytes: bytes, suffix: str = ".mp3") -> bool:
        """Write bytes to a temp file and play with the OS audio player."""
        import platform
        system = platform.system().lower()

        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            if system == "windows":
                # Use Windows built-in Media Player silently
                import subprocess
                subprocess.run(
                    ["powershell", "-c",
                     f"(New-Object Media.SoundPlayer '{tmp_path}').PlaySync()"]
                    if suffix == ".wav" else
                    ["start", "/wait", "", tmp_path],
                    shell=(suffix != ".wav"),
                    capture_output=True,
                )
                return True
            elif system == "darwin":
                os.system(f"afplay '{tmp_path}'")
                return True
            elif system == "linux":
                # Try common Linux players
                for player in ("mpg123", "mpg321", "ffplay", "aplay"):
                    if os.system(f"command -v {player} > /dev/null 2>&1") == 0:
                        os.system(f"{player} -q '{tmp_path}' > /dev/null 2>&1")
                        return True
        except Exception as exc:
            log.error("Audio file playback error: %s", exc)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

        return False