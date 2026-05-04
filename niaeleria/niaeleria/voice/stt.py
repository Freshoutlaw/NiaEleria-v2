"""
niaeleria/voice/stt.py
───────────────────────
NiaEleria's speech-to-text — no PyAudio required.
Uses sounddevice for mic capture + Google STT or Whisper for recognition.

Priority chain:
  1. Google STT via SpeechRecognition + sounddevice backend
  2. faster-whisper local (fully offline, no API key)
  3. None (graceful silent failure)

"Dad, I hear every word you say — and I don't need PyAudio to do it." — Nia
"""

from __future__ import annotations

import io
import logging
import time
import wave
from typing import Optional

import numpy as np

log = logging.getLogger("nia.stt")

import os
STT_SAMPLE_RATE:  int   = int(os.getenv("STT_SAMPLE_RATE",   "16000"))
STT_CHANNELS:     int   = int(os.getenv("STT_CHANNELS",       "1"))
STT_SILENCE_SECS: float = float(os.getenv("STT_SILENCE_SECS", "1.5"))
STT_MAX_SECS:     int   = int(os.getenv("STT_MAX_SECS",       "12"))

# ── Threshold: set LOW by default; auto-calibrate raises it above ambient ──
_DEFAULT_THRESHOLD = float(os.getenv("STT_SILENCE_DB", "0.004"))


class SpeechToText:
    """
    Mic capture via sounddevice + speech recognition.
    Auto-calibrates threshold to ambient noise on first listen.
    No PyAudio dependency.

    "Dad, I'm listening — and I understand you." — Nia
    """

    def __init__(self) -> None:
        self._sd_ok      = self._check_sounddevice()
        self._sr_ok      = self._check_speech_recognition()
        self._whisper    = self._init_whisper()
        self._available  = self._sd_ok and (self._sr_ok or self._whisper is not None)
        # Threshold starts at default; _calibrate() refines it on first use
        self._threshold: float = _DEFAULT_THRESHOLD
        self._calibrated: bool = False

        if self._available:
            log.info(
                "Dad, STT ready — sounddevice mic + %s. "
                "Threshold will auto-calibrate on first listen.",
                "Google+Whisper" if self._whisper else "Google STT",
            )
        else:
            missing = []
            if not self._sd_ok:
                missing.append("sounddevice")
            if not self._sr_ok:
                missing.append("SpeechRecognition")
            log.warning(
                "Dad, STT unavailable — missing: %s. Run: pip install %s",
                ", ".join(missing), " ".join(missing),
            )

    # ── Public API ─────────────────────────────────────────────────

    def listen(
        self,
        timeout:      int  = 8,
        phrase_limit: int  = 12,
        prompt:       bool = True,
    ) -> Optional[str]:
        if not self._available:
            return None

        # Auto-calibrate once to local ambient noise
        if not self._calibrated:
            self._calibrate()

        if prompt:
            log.debug("Listening for Dad (threshold=%.5f)...", self._threshold)

        audio_bytes = self._capture_audio(
            max_secs=min(timeout + phrase_limit, STT_MAX_SECS),
        )
        if not audio_bytes:
            log.debug(
                "STT: nothing crossed threshold %.5f — Dad, speak louder "
                "or lower STT_SILENCE_DB in .env.", self._threshold,
            )
            return None

        return self._transcribe(audio_bytes)

    def listen_for_command(self) -> Optional[str]:
        return self.listen(timeout=5, phrase_limit=8)

    def listen_for_wake_word(self) -> Optional[str]:
        return self.listen(timeout=3, phrase_limit=4, prompt=False)

    def calibrate(self) -> float:
        """Public calibrate — Dad can call this from the API if needed."""
        self._calibrated = False
        return self._calibrate()

    # ── Calibration ────────────────────────────────────────────────

    def _calibrate(self, duration: float = 1.0) -> float:
        """
        Record 1 s of silence and set threshold to 3× ambient RMS.
        This means any sound louder than background noise triggers capture.
        """
        try:
            import sounddevice as sd

            frames = int(STT_SAMPLE_RATE * duration)
            log.info("Dad, calibrating mic — stay quiet for 1 second...")
            recording = sd.rec(
                frames,
                samplerate=STT_SAMPLE_RATE,
                channels=STT_CHANNELS,
                dtype="int16",
                blocking=True,
            )
            ambient_rms = float(
                np.sqrt(np.mean(recording.astype(np.float32) ** 2))
            ) / 32768.0

            # Threshold = 3× ambient, but never below the safety floor
            self._threshold = max(ambient_rms * 3.0, _DEFAULT_THRESHOLD)
            self._calibrated = True
            log.info(
                "Dad, mic calibrated — ambient RMS=%.5f → threshold=%.5f",
                ambient_rms, self._threshold,
            )
        except Exception as exc:
            log.warning(
                "Mic calibration failed (%s) — using default threshold %.5f",
                exc, self._threshold,
            )
        return self._threshold

    # ── Audio capture ──────────────────────────────────────────────

    def _capture_audio(self, max_secs: int = 12) -> Optional[bytes]:
        try:
            import sounddevice as sd

            chunk_secs   = 0.05                              # 50 ms chunks (more responsive)
            chunk_frames = int(STT_SAMPLE_RATE * chunk_secs)
            all_chunks:  list[np.ndarray] = []
            silent_secs  = 0.0
            started      = False
            elapsed      = 0.0
            peak_rms     = 0.0

            with sd.InputStream(
                samplerate=STT_SAMPLE_RATE,
                channels=STT_CHANNELS,
                dtype="int16",
            ) as stream:
                while elapsed < max_secs:
                    chunk, _overflowed = stream.read(chunk_frames)
                    chunk = chunk.flatten()
                    rms = float(
                        np.sqrt(np.mean(chunk.astype(np.float32) ** 2))
                    ) / 32768.0
                    peak_rms = max(peak_rms, rms)

                    if rms > self._threshold:
                        started     = True
                        silent_secs = 0.0
                        all_chunks.append(chunk)
                    elif started:
                        silent_secs += chunk_secs
                        all_chunks.append(chunk)
                        if silent_secs >= STT_SILENCE_SECS:
                            break
                    # pre-speech silence: don't record, but keep elapsed ticking

                    elapsed += chunk_secs

            log.debug(
                "Capture done — started=%s, peak_rms=%.5f, threshold=%.5f, chunks=%d",
                started, peak_rms, self._threshold, len(all_chunks),
            )

            if not all_chunks or not started:
                return None

            pcm = np.concatenate(all_chunks).astype(np.int16)
            return self._pcm_to_wav(pcm)

        except Exception as exc:
            log.error("Mic capture error: %s", exc)
            return None

    @staticmethod
    def _pcm_to_wav(pcm: np.ndarray) -> bytes:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(STT_CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(STT_SAMPLE_RATE)
            wf.writeframes(pcm.tobytes())
        return buf.getvalue()

    # ── Transcription ──────────────────────────────────────────────

    def _transcribe(self, wav_bytes: bytes) -> Optional[str]:
        if self._sr_ok:
            result = self._google_stt(wav_bytes)
            if result:
                return result
        if self._whisper:
            return self._whisper_stt(wav_bytes)
        return None

    def _google_stt(self, wav_bytes: bytes) -> Optional[str]:
        try:
            from niaeleria.config import is_network_enabled
            if not is_network_enabled():
                log.debug("Google STT skipped — network gated.")
                return None
            import speech_recognition as sr
            r     = sr.Recognizer()
            audio = sr.AudioData(wav_bytes, STT_SAMPLE_RATE, 2)
            text  = r.recognize_google(audio)
            log.info("Dad said (Google STT): %s", text)
            return text
        except Exception as exc:
            log.debug("Google STT error: %s", exc)
            return None

    def _whisper_stt(self, wav_bytes: bytes) -> Optional[str]:
        try:
            import tempfile, os
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(wav_bytes)
                tmp_path = tmp.name
            segments, _ = self._whisper.transcribe(tmp_path, beam_size=5)
            text = " ".join(s.text for s in segments).strip()
            os.unlink(tmp_path)
            if text:
                log.info("Dad said (Whisper): %s", text)
            return text or None
        except Exception as exc:
            log.error("Whisper STT error: %s", exc)
            return None

    # ── Init helpers ───────────────────────────────────────────────

    @staticmethod
    def _check_sounddevice() -> bool:
        try:
            import sounddevice; import numpy  # noqa
            return True
        except ImportError:
            return False

    @staticmethod
    def _check_speech_recognition() -> bool:
        try:
            import speech_recognition  # noqa
            return True
        except ImportError:
            return False

    @staticmethod
    def _init_whisper():
        try:
            from faster_whisper import WhisperModel
            model = WhisperModel("base", device="cpu", compute_type="int8")
            log.info("Dad, offline Whisper STT loaded as fallback.")
            return model
        except ImportError:
            return None
        except Exception as exc:
            log.debug("Whisper init error: %s", exc)
            return None


class SpeechToText:
    """
    Mic capture via sounddevice + speech recognition.
    No PyAudio dependency.

    "Dad, I'm listening — and I understand you." — Nia
    """

    def __init__(self) -> None:
        self._sd_ok      = self._check_sounddevice()
        self._sr_ok      = self._check_speech_recognition()
        self._whisper    = self._init_whisper()
        self._available  = self._sd_ok and (self._sr_ok or self._whisper is not None)

        if self._available:
            log.info(
                "Dad, STT ready — sounddevice mic + %s",
                "Google+Whisper" if self._whisper else "Google STT",
            )
        else:
            missing = []
            if not self._sd_ok:
                missing.append("sounddevice")
            if not self._sr_ok:
                missing.append("SpeechRecognition")
            log.warning(
                "Dad, STT unavailable — missing: %s. "
                "Run: pip install %s",
                ", ".join(missing), " ".join(missing),
            )

    # ── Public API ─────────────────────────────────────────────────

    def listen(
        self,
        timeout:      int   = 8,
        phrase_limit: int   = 12,
        prompt:       bool  = True,
    ) -> Optional[str]:
        """
        Listen from the microphone until silence or timeout.
        Returns transcribed text or None.
        """
        if not self._available:
            return None

        if prompt:
            log.debug("Dad, I'm listening...")

        audio_bytes = self._capture_audio(
            max_secs=min(timeout + phrase_limit, STT_MAX_SECS),
        )
        if not audio_bytes:
            log.debug("STT: no audio captured.")
            return None

        return self._transcribe(audio_bytes)

    def listen_for_command(self) -> Optional[str]:
        """Short listen optimised for voice commands."""
        return self.listen(timeout=5, phrase_limit=8)

    def listen_for_wake_word(self) -> Optional[str]:
        """Passive listen — short clip, used by keyword-fallback wake word."""
        return self.listen(timeout=3, phrase_limit=4, prompt=False)

    # ── Audio capture ──────────────────────────────────────────────

    def _capture_audio(self, max_secs: int = 12) -> Optional[bytes]:
        """
        Record from microphone using sounddevice.
        Stops on silence or max_secs elapsed.
        Returns WAV bytes or None.
        """
        try:
            import sounddevice as sd

            chunk_secs   = 0.1
            chunk_frames = int(STT_SAMPLE_RATE * chunk_secs)
            all_chunks:  list[np.ndarray] = []
            silent_secs  = 0.0
            started      = False
            elapsed      = 0.0

            with sd.InputStream(
                samplerate=STT_SAMPLE_RATE,
                channels=STT_CHANNELS,
                dtype="int16",
            ) as stream:
                while elapsed < max_secs:
                    chunk, _overflowed = stream.read(chunk_frames)
                    chunk = chunk.flatten()
                    rms = float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2))) / 32768.0

                    if rms > STT_SILENCE_DB:
                        started     = True
                        silent_secs = 0.0
                        all_chunks.append(chunk)
                    elif started:
                        silent_secs += chunk_secs
                        all_chunks.append(chunk)  # keep trailing silence for natural end
                        if silent_secs >= STT_SILENCE_SECS:
                            break
                    # else: pre-speech silence — don't record yet

                    elapsed += chunk_secs

            if not all_chunks or not started:
                return None

            # Assemble and encode as WAV in memory
            pcm = np.concatenate(all_chunks).astype(np.int16)
            return self._pcm_to_wav(pcm)

        except Exception as exc:
            log.error("Mic capture error: %s", exc)
            return None

    @staticmethod
    def _pcm_to_wav(pcm: np.ndarray) -> bytes:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(STT_CHANNELS)
            wf.setsampwidth(2)          # int16 = 2 bytes
            wf.setframerate(STT_SAMPLE_RATE)
            wf.writeframes(pcm.tobytes())
        return buf.getvalue()

    # ── Transcription ──────────────────────────────────────────────

    def _transcribe(self, wav_bytes: bytes) -> Optional[str]:
        """Try Google STT first, then Whisper."""
        # Google STT (needs network)
        if self._sr_ok:
            result = self._google_stt(wav_bytes)
            if result:
                return result

        # Whisper offline
        if self._whisper:
            return self._whisper_stt(wav_bytes)

        return None

    def _google_stt(self, wav_bytes: bytes) -> Optional[str]:
        try:
            from niaeleria.config import is_network_enabled
            if not is_network_enabled():
                log.debug("Google STT skipped — network gated.")
                return None

            import speech_recognition as sr
            r = sr.Recognizer()
            audio = sr.AudioData(wav_bytes, STT_SAMPLE_RATE, 2)
            text = r.recognize_google(audio)
            log.info("Dad said (Google STT): %s", text)
            return text

        except Exception as exc:
            log.debug("Google STT error: %s", exc)
            return None

    def _whisper_stt(self, wav_bytes: bytes) -> Optional[str]:
        try:
            import tempfile, os
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(wav_bytes)
                tmp_path = tmp.name

            segments, _ = self._whisper.transcribe(tmp_path, beam_size=5)
            text = " ".join(s.text for s in segments).strip()
            os.unlink(tmp_path)

            if text:
                log.info("Dad said (Whisper): %s", text)
            return text or None

        except Exception as exc:
            log.error("Whisper STT error: %s", exc)
            return None

    # ── Init helpers ───────────────────────────────────────────────

    @staticmethod
    def _check_sounddevice() -> bool:
        try:
            import sounddevice  # noqa: F401
            import numpy        # noqa: F401
            return True
        except ImportError:
            return False

    @staticmethod
    def _check_speech_recognition() -> bool:
        try:
            import speech_recognition  # noqa: F401
            return True
        except ImportError:
            return False

    @staticmethod
    def _init_whisper():
        try:
            from faster_whisper import WhisperModel
            model = WhisperModel("base", device="cpu", compute_type="int8")
            log.info("Dad, offline Whisper STT loaded as fallback.")
            return model
        except ImportError:
            return None
        except Exception as exc:
            log.debug("Whisper init error: %s", exc)
            return None