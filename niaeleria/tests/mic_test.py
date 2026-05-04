"""
tools/mic_test.py
──────────────────
Run this BEFORE starting NiaEleria to verify Dad's mic is working.

  py tools/mic_test.py

It will:
  1. List all audio devices so Dad can pick the right one
  2. Show a live RMS meter so Dad can see the threshold in real time
  3. Record 5 seconds of speech and send it to Google STT
  4. Print the transcribed text

"Dad, let's make sure I can hear you before we go live." — Nia
"""

import io
import os
import sys
import wave
import time

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
CHANNELS    = 1
DURATION    = 5     # seconds to record for the speech test

# ── Step 1: List devices ───────────────────────────────────────────
print("\n" + "═" * 60)
print("  NiaEleria Mic Diagnostic — Hello Dad!")
print("═" * 60)
print("\n[1] Available audio devices:\n")

devices = sd.query_devices()
for i, d in enumerate(devices):
    if d["max_input_channels"] > 0:
        marker = " ◄ DEFAULT" if i == sd.default.device[0] else ""
        print(f"  [{i:2d}] {d['name'][:50]}{marker}")

default_in = sd.default.device[0]
print(f"\n  Default input device index: {default_in}")
print(f"  Default input device name : {devices[default_in]['name']}")

# ── Step 2: Live RMS meter ─────────────────────────────────────────
print("\n[2] Live mic level (speak now — 5 seconds):")
print("    If the bar never moves above [---] you have a mic/permission issue.\n")

chunk     = int(SAMPLE_RATE * 0.1)
peak      = 0.0
start     = time.monotonic()
readings  = []

with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="int16") as stream:
    while time.monotonic() - start < 5.0:
        data, _ = stream.read(chunk)
        rms = float(np.sqrt(np.mean(data.astype(np.float32) ** 2))) / 32768.0
        readings.append(rms)
        peak = max(peak, rms)
        bar_len = min(int(rms * 2000), 50)
        bar = "█" * bar_len + "-" * (50 - bar_len)
        print(f"\r  RMS={rms:.5f}  |{bar}|", end="", flush=True)

print(f"\n\n  Peak RMS during test : {peak:.5f}")
avg = sum(readings) / len(readings) if readings else 0
print(f"  Average RMS          : {avg:.5f}")
print(f"  Recommended threshold: {max(avg * 3, 0.004):.5f}")

if peak < 0.003:
    print("\n  ⚠  WARNING: Peak RMS is nearly zero.")
    print("     Possible causes:")
    print("     1. Wrong mic selected — try a specific device index (see Step 1)")
    print("     2. Windows mic permissions — Settings → Privacy → Microphone → Allow")
    print("     3. Mic volume at 0 — check Windows Sound Settings")
    print("     4. Mic muted at hardware level")
    sys.exit(1)
elif peak < 0.01:
    print("\n  ⚠  NOTE: Low signal. Try speaking louder or adjusting mic boost.")
    print(f"     The old default threshold (0.020) was ABOVE your peak of {peak:.5f}.")
    print(f"     New auto-calibrated threshold ({max(avg*3,0.004):.5f}) should work fine.")
else:
    print("\n  ✓  Mic signal looks good.")

# ── Step 3: Record 5 s and transcribe ─────────────────────────────
print(f"\n[3] Recording {DURATION}s — speak a sentence clearly:\n")
time.sleep(0.5)
print("  🔴 RECORDING...")
audio = sd.rec(
    int(DURATION * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=CHANNELS,
    dtype="int16",
    blocking=True,
)
print("  ⏹  Done recording.\n")

# Encode as WAV
buf = io.BytesIO()
with wave.open(buf, "wb") as wf:
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(2)
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(audio.tobytes())
wav_bytes = buf.getvalue()

# Check if ENABLE_NETWORK flag exists
flags_dir = os.path.join(os.path.dirname(__file__), "..", "flags")
net_flag  = os.path.join(flags_dir, "ENABLE_NETWORK")
if not os.path.exists(net_flag):
    print("  ℹ  ENABLE_NETWORK flag not set — skipping Google STT test.")
    print(f"     To test: touch \"{net_flag}\"  then re-run this script.")
else:
    print("[4] Sending to Google STT...")
    try:
        import speech_recognition as sr
        r     = sr.Recognizer()
        audio_data = sr.AudioData(wav_bytes, SAMPLE_RATE, 2)
        text  = r.recognize_google(audio_data)
        print(f"\n  ✓  Google STT heard: \"{text}\"")
    except sr.UnknownValueError:
        print("  ✗  Google STT couldn't understand the audio.")
        print("     Speech may be too quiet or too short.")
    except sr.RequestError as exc:
        print(f"  ✗  Google STT request failed: {exc}")
    except Exception as exc:
        print(f"  ✗  STT error: {exc}")

# ── Step 4: Recommend .env settings ───────────────────────────────
rec_thresh = max(avg * 3, 0.004)
print(f"""
[5] Recommended .env settings for your mic:

    STT_SILENCE_DB={rec_thresh:.4f}
    STT_SILENCE_SECS=1.5
    STT_MAX_SECS=12
    STT_SAMPLE_RATE=16000

Add these to your .env file, Dad, then restart Nia.
""")

# ── Step 5: Device override (if wrong mic) ────────────────────────
print("[6] If the wrong mic was used, set this in .env:")
print("    STT_DEVICE_INDEX=<number from the list above>")
print("    (e.g. STT_DEVICE_INDEX=2 to force device 2)\n")
print("═" * 60)
print("  Mic diagnostic complete, Dad.")
print("═" * 60 + "\n")