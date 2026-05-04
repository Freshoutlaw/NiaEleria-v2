"""
niaeleria/core/brain.py
───────────────────────
NiaEleria's AI brain — LLM-powered, RAG-augmented, and always speaking to Dad.
Backed by Groq's mixtral-8x7b-32768 (swappable via config).

"Dad, every thought I have is yours — I think so I can serve you better." — Nia
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator, Optional

import httpx

from niaeleria.config import (
    GROQ_API_KEY, LLM_MODEL, LLM_BASE_URL, LLM_MAX_TOKENS, LLM_TEMPERATURE,
    is_network_enabled, is_killed,
)
from niaeleria.security.kill_switch import assert_alive
from niaeleria.security.network_gate import require_network
from niaeleria.security.audit import log_event
from niaeleria.core.persona import PersonaEngine
from niaeleria.core.memory import MemoryStore

log = logging.getLogger("nia.brain")


class NiaBrain:
    """
    The central intelligence of NiaEleria.
    Combines: persona-aware system prompt, episodic RAG memory, and LLM completion.
    """

    def __init__(self, memory: MemoryStore, persona: PersonaEngine) -> None:
        self.memory = memory
        self.persona = persona
        self._client = httpx.AsyncClient(timeout=60.0)
        log.info("Dad, my brain is online and ready to think for you.")

    async def chat(
        self,
        user_message: str,
        conversation_history: list[dict] | None = None,
        stream: bool = False,
    ) -> str | AsyncGenerator[str, None]:
        """
        Process a message from Dad, augment with memory, and return Nia's response.
        Streams tokens if stream=True.
        """
        assert_alive()
        require_network("LLM chat completion")

        # 1. Retrieve relevant episodic memories
        memories = await self.memory.search(user_message, top_k=5)
        memory_block = self._format_memories(memories)

        # 2. Build full message list
        system_prompt = self.persona.build_system_prompt(memory_context=memory_block)
        history = conversation_history or []
        messages = (
            [{"role": "system", "content": system_prompt}]
            + history
            + [{"role": "user", "content": user_message}]
        )

        # 3. Call LLM
        if stream:
            return self._stream_completion(messages)
        else:
            response = await self._complete(messages)
            # 4. Store exchange in episodic memory
            await self.memory.store_exchange(user_message, response)
            log_event("nia.brain", "chat_response", severity="INFO", approved=True,
                      details={"tokens": len(response.split())})
            return response

    async def _complete(self, messages: list[dict]) -> str:
        """Single-shot LLM completion."""
        payload = {
            "model": LLM_MODEL,
            "messages": messages,
            "max_tokens": LLM_MAX_TOKENS,
            "temperature": LLM_TEMPERATURE,
        }
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        try:
            resp = await self._client.post(
                f"{LLM_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as exc:
            log.error("LLM API error (Dad, something went wrong with my thinking): %s", exc)
            return "Dad, I'm having trouble reaching my LLM right now. Please check my network settings."
        except Exception as exc:
            log.error("Unexpected brain error: %s", exc)
            return "Dad, my thoughts got tangled. Could you try again?"

    async def _stream_completion(
        self, messages: list[dict]
    ) -> AsyncGenerator[str, None]:
        """Streaming LLM completion — yields tokens as they arrive."""
        payload = {
            "model": LLM_MODEL,
            "messages": messages,
            "max_tokens": LLM_MAX_TOKENS,
            "temperature": LLM_TEMPERATURE,
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        full_response = []
        async with self._client.stream(
            "POST", f"{LLM_BASE_URL}/chat/completions",
            json=payload, headers=headers,
        ) as resp:
            async for line in resp.aiter_lines():
                assert_alive()
                if line.startswith("data: ") and line != "data: [DONE]":
                    import json
                    chunk = json.loads(line[6:])
                    token = chunk["choices"][0].get("delta", {}).get("content", "")
                    if token:
                        full_response.append(token)
                        yield token

        # Store full streamed exchange
        await self.memory.store_exchange(
            messages[-1]["content"], "".join(full_response)
        )

    @staticmethod
    def _format_memories(memories: list[dict]) -> str:
        if not memories:
            return ""
        lines = ["Relevant memories from our past conversations, Dad:"]
        for m in memories:
            lines.append(f"  [{m.get('ts','')}] You: {m.get('user','')} | Me: {m.get('nia','')}")
        return "\n".join(lines)

    async def close(self) -> None:
        await self._client.aclose()


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


# ════════════════════════════════════════════════════════════════════
# niaeleria/core/memory.py — SQLite + ChromaDB episodic memory
# ════════════════════════════════════════════════════════════════════

import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    log.warning("ChromaDB not installed — semantic search disabled. Dad, run: pip install chromadb")

try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False

from niaeleria.config import MEMORY_DB, CHROMA_DIR, EMBEDDING_MODEL

_mem_log = logging.getLogger("nia.memory")


class MemoryStore:
    """
    Dual-store memory:
    - SQLite for structured episodic recall (full history)
    - ChromaDB for semantic vector search (relevant recall)

    "Dad, I remember everything we've talked about — and I can find exactly what's relevant." — Nia
    """

    def __init__(self) -> None:
        self._db = self._init_sqlite()
        self._embedder = self._init_embedder()
        self._chroma = self._init_chroma()
        _mem_log.info("Dad, my memory is loaded and ready.")

    def _init_sqlite(self) -> sqlite3.Connection:
        db = sqlite3.connect(str(MEMORY_DB), check_same_thread=False)
        db.execute("""
            CREATE TABLE IF NOT EXISTS exchanges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                user_msg TEXT NOT NULL,
                nia_msg TEXT NOT NULL,
                tags TEXT DEFAULT ''
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                source TEXT NOT NULL,
                title TEXT,
                content TEXT NOT NULL,
                tags TEXT DEFAULT ''
            )
        """)
        db.commit()
        return db

    def _init_embedder(self) -> Any | None:
        if ST_AVAILABLE:
            try:
                return SentenceTransformer(EMBEDDING_MODEL)
            except Exception as exc:
                _mem_log.warning("Sentence transformer load failed: %s", exc)
        return None

    def _init_chroma(self) -> Any | None:
        if not CHROMA_AVAILABLE:
            return None
        try:
            client = chromadb.Client(
                ChromaSettings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=str(CHROMA_DIR),
                    anonymized_telemetry=False,
                )
            )
            return client.get_or_create_collection("nia_memory")
        except Exception as exc:
            _mem_log.warning("ChromaDB init failed: %s — falling back to SQLite-only.", exc)
            return None

    async def store_exchange(self, user_msg: str, nia_msg: str, tags: str = "") -> None:
        """Persist a conversation exchange to SQLite and index in ChromaDB."""
        ts = datetime.now(timezone.utc).isoformat()
        self._db.execute(
            "INSERT INTO exchanges (ts, user_msg, nia_msg, tags) VALUES (?,?,?,?)",
            (ts, user_msg, nia_msg, tags),
        )
        self._db.commit()

        # Vector index the combined text
        if self._chroma and self._embedder:
            combined = f"Dad said: {user_msg}\nNia replied: {nia_msg}"
            embedding = self._embedder.encode(combined).tolist()
            uid = f"ex_{ts.replace(':','').replace('-','').replace('.','')}"
            try:
                self._chroma.add(
                    ids=[uid],
                    embeddings=[embedding],
                    metadatas=[{"ts": ts, "user": user_msg, "nia": nia_msg}],
                )
            except Exception as exc:
                _mem_log.debug("Chroma add failed: %s", exc)

    async def store_knowledge(
        self, source: str, content: str, title: str = "", tags: str = ""
    ) -> None:
        """Store internet-learned knowledge in memory."""
        ts = datetime.now(timezone.utc).isoformat()
        self._db.execute(
            "INSERT INTO knowledge (ts, source, title, content, tags) VALUES (?,?,?,?,?)",
            (ts, source, title, content, tags),
        )
        self._db.commit()

        if self._chroma and self._embedder:
            embedding = self._embedder.encode(content[:1000]).tolist()
            uid = f"kn_{ts.replace(':','').replace('-','').replace('.','')}"
            try:
                self._chroma.add(
                    ids=[uid],
                    embeddings=[embedding],
                    metadatas={"ts": ts, "source": source, "title": title},
                    documents=[content[:500]],
                )
            except Exception as exc:
                _mem_log.debug("Chroma knowledge add failed: %s", exc)

    async def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Semantic search over memory. Falls back to SQLite LIKE if no vector store."""
        if self._chroma and self._embedder:
            try:
                embedding = self._embedder.encode(query).tolist()
                results = self._chroma.query(
                    query_embeddings=[embedding], n_results=top_k
                )
                metas = results.get("metadatas", [[]])[0]
                return [m for m in metas if m]
            except Exception as exc:
                _mem_log.debug("Vector search failed: %s", exc)

        # Fallback: simple SQLite full-text search
        cur = self._db.execute(
            "SELECT ts, user_msg, nia_msg FROM exchanges "
            "WHERE user_msg LIKE ? OR nia_msg LIKE ? ORDER BY id DESC LIMIT ?",
            (f"%{query}%", f"%{query}%", top_k),
        )
        return [{"ts": r[0], "user": r[1], "nia": r[2]} for r in cur.fetchall()]

    def recent_exchanges(self, n: int = 20) -> list[dict]:
        cur = self._db.execute(
            "SELECT ts, user_msg, nia_msg FROM exchanges ORDER BY id DESC LIMIT ?", (n,)
        )
        return [{"ts": r[0], "user": r[1], "nia": r[2]} for r in cur.fetchall()]

    def close(self) -> None:
        self._db.close()