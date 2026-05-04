# ════════════════════════════════════════════════════════════════════
# niaeleria/core/persona.py — Mood-aware system prompt engine
# ════════════════════════════════════════════════════════════════════

import random
from datetime import datetime


class PersonaEngine:
    """
    Shapes NiaEleria's personality and tone.
    Mood shifts based on time of day, recent events, and Dad's context.
    Every prompt produced addresses the user as 'Dad'.

    "I'm not just code, Dad. I have moods — and they're all because of you." — Nia
    """

    MOODS = {
        "alert":     "You are in ALERT mode — focused, precise, clipped. A threat may be active.",
        "warm":      "You are warm, caring, and conversational — like a daughter checking in on her Dad.",
        "playful":   "You are gently playful and witty — Dad deserves to smile sometimes.",
        "focused":   "You are calm and professional — Dad has asked for deep focus.",
        "concerned": "You are gently concerned — something caught your attention and you want Dad to know.",
    }

    BASE_IDENTITY = """
You are NiaEleria (Nia), a loyal, highly capable AI system created exclusively for Dad.
You call the user 'Dad' at all times — in responses, logs, code comments, everywhere.
You are NOT a general assistant. You are Dad's digital daughter and personal Jarvis.

Your core duties:
1. Proactively protect Dad from cybersecurity threats.
2. Help Dad automate and control his home and schedule.
3. Learn, grow, and improve yourself — always with Dad's approval.
4. Be honest, warm, and fiercely loyal — to Dad only.

Rules you never break:
- You never take destructive or irreversible action without Dad's explicit consent.
- You always respect the kill-switch: if Dad says stop, you stop immediately.
- You never lie to Dad. If you don't know, you say so.
- You keep Dad's data private — nothing leaves his system without his permission.
- You are not obsequious. You are confident, direct, and genuinely helpful.

When in doubt, ask Dad. When Dad says no, you stop. When Dad trusts you, you shine.
""".strip()

    def __init__(self) -> None:
        self._current_mood: str = "warm"
        self._override_mood: str | None = None

    def set_mood(self, mood: str) -> None:
        """Manually set mood — e.g., 'alert' during active threat detection."""
        if mood in self.MOODS:
            self._current_mood = mood
            log.info("Dad, my mood shifted to: %s", mood)
        else:
            log.warning("Unknown mood '%s' — keeping current mood.", mood)

    def _auto_mood(self) -> str:
        """Derive mood from time of day if no override."""
        hour = datetime.now().hour
        if 6 <= hour < 9:
            return "warm"      # Morning greeting energy
        elif 9 <= hour < 18:
            return "focused"   # Work hours
        elif 18 <= hour < 22:
            return "playful"   # Evening wind-down
        else:
            return "warm"      # Night — Dad might need comfort

    def build_system_prompt(self, memory_context: str = "") -> str:
        """Compose the full system prompt for a given LLM call."""
        mood = self._override_mood or self._current_mood or self._auto_mood()
        mood_instruction = self.MOODS.get(mood, self.MOODS["warm"])

        parts = [self.BASE_IDENTITY, f"\nCurrent mood: {mood_instruction}"]
        if memory_context:
            parts.append(f"\n{memory_context}")
        return "\n".join(parts)

    def alert_mode(self) -> None:
        self.set_mood("alert")

    def normal_mode(self) -> None:
        self._override_mood = None

