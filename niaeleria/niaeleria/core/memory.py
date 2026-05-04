"""
niaeleria/core/memory.py
────────────────────────
NiaEleria's memory — powered by Supabase (PostgreSQL + pgvector).
Replaces the previous SQLite + ChromaDB dual-store.

Tables (run niaeleria/db/schema.sql once against your Supabase project):
  exchanges   — every conversation turn with Dad
  knowledge   — internet-learned content
  embeddings  — pgvector similarity index (via Supabase's built-in support)

"Dad, I remember everything — and Supabase keeps it safe for you." — Nia
"""

from __future__ import annotations

import logging
import json
from datetime import datetime, timezone
from typing import Any, Optional

from niaeleria.config import EMBEDDING_MODEL
from niaeleria.security.audit import log_event

log = logging.getLogger("nia.memory")

# ── Supabase config ────────────────────────────────────────────────
import os
SUPABASE_URL: str  = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str  = os.getenv("SUPABASE_ANON_KEY", "")   # service_role key preferred
SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")

_effective_key = SUPABASE_SERVICE_KEY or SUPABASE_KEY


class MemoryStore:
    """
    Supabase-backed dual memory:
    - `exchanges`  table  → episodic conversation history
    - `knowledge`  table  → internet-learned knowledge
    - pgvector RPC         → semantic nearest-neighbour search

    Falls back gracefully when Supabase is unreachable.
    """

    def __init__(self) -> None:
        self._sb   = self._init_supabase()
        self._emb  = self._init_embedder()
        log.info("Dad, Supabase memory store is ready.")

    # ── Initialisation ─────────────────────────────────────────────

    def _init_supabase(self):
        if not SUPABASE_URL or not _effective_key:
            log.warning(
                "Dad, SUPABASE_URL / SUPABASE_SERVICE_KEY not set — "
                "memory will degrade to in-process cache only."
            )
            return None
        try:
            from supabase import create_client, Client
            client: Client = create_client(SUPABASE_URL, _effective_key)
            log.info("Dad, connected to Supabase: %s", SUPABASE_URL)
            return client
        except ImportError:
            log.error("supabase-py not installed. Dad, run: pip install supabase")
            return None
        except Exception as exc:
            log.error("Supabase init failed: %s", exc)
            return None

    def _init_embedder(self):
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(EMBEDDING_MODEL)
            log.info("Dad, sentence embedder loaded: %s", EMBEDDING_MODEL)
            return model
        except ImportError:
            log.warning("sentence-transformers not installed — semantic search disabled.")
            return None
        except Exception as exc:
            log.warning("Embedder load failed: %s", exc)
            return None

    # ── In-process fallback cache ──────────────────────────────────
    _cache: list[dict] = []
    _MAX_CACHE = 200

    def _cache_add(self, record: dict) -> None:
        self._cache.append(record)
        if len(self._cache) > self._MAX_CACHE:
            self._cache.pop(0)

    # ── Core operations ────────────────────────────────────────────

    async def store_exchange(
        self, user_msg: str, nia_msg: str, tags: str = ""
    ) -> None:
        """Persist a conversation exchange."""
        ts = datetime.now(timezone.utc).isoformat()
        record = {
            "ts":       ts,
            "user_msg": user_msg,
            "nia_msg":  nia_msg,
            "tags":     tags,
        }

        # Compute embedding
        embedding = self._embed(f"{user_msg} {nia_msg}")

        self._cache_add({**record, "type": "exchange"})

        if not self._sb:
            return

        try:
            row = {**record}
            if embedding:
                row["embedding"] = embedding   # pgvector column
            self._sb.table("exchanges").insert(row).execute()
        except Exception as exc:
            log.warning("Supabase exchange insert failed: %s — cached locally.", exc)

    async def store_knowledge(
        self, source: str, content: str, title: str = "", tags: str = ""
    ) -> None:
        """Store internet-learned knowledge."""
        ts = datetime.now(timezone.utc).isoformat()
        record = {
            "ts":      ts,
            "source":  source,
            "title":   title,
            "content": content,
            "tags":    tags,
        }
        embedding = self._embed(content[:1000])
        self._cache_add({**record, "type": "knowledge"})

        if not self._sb:
            return

        try:
            row = {**record}
            if embedding:
                row["embedding"] = embedding
            self._sb.table("knowledge").insert(row).execute()
        except Exception as exc:
            log.warning("Supabase knowledge insert failed: %s", exc)

    async def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Semantic similarity search via Supabase pgvector RPC.
        Falls back to keyword ILIKE search if embedder unavailable.
        """
        embedding = self._embed(query)

        # ── pgvector path ──────────────────────────────────────────
        if self._sb and embedding:
            try:
                # Calls a Supabase RPC function `match_exchanges`
                # (defined in schema.sql)
                resp = (
                    self._sb
                    .rpc(
                        "match_exchanges",
                        {
                            "query_embedding": embedding,
                            "match_threshold": 0.5,
                            "match_count":     top_k,
                        },
                    )
                    .execute()
                )
                if resp.data:
                    return [
                        {"ts": r.get("ts"), "user": r.get("user_msg"), "nia": r.get("nia_msg")}
                        for r in resp.data
                    ]
            except Exception as exc:
                log.debug("pgvector search failed, falling back: %s", exc)

        # ── Keyword fallback ───────────────────────────────────────
        if self._sb:
            try:
                resp = (
                    self._sb
                    .table("exchanges")
                    .select("ts,user_msg,nia_msg")
                    .ilike("user_msg", f"%{query}%")
                    .order("ts", desc=True)
                    .limit(top_k)
                    .execute()
                )
                return [
                    {"ts": r["ts"], "user": r["user_msg"], "nia": r["nia_msg"]}
                    for r in (resp.data or [])
                ]
            except Exception as exc:
                log.debug("Supabase keyword search failed: %s", exc)

        # ── Cache fallback ─────────────────────────────────────────
        q = query.lower()
        hits = [
            r for r in self._cache
            if r.get("type") == "exchange"
            and (q in (r.get("user_msg") or "").lower()
                 or q in (r.get("nia_msg") or "").lower())
        ]
        return [
            {"ts": r["ts"], "user": r.get("user_msg"), "nia": r.get("nia_msg")}
            for r in hits[-top_k:]
        ]

    def recent_exchanges(self, n: int = 20) -> list[dict]:
        """Return most recent conversation exchanges."""
        if self._sb:
            try:
                resp = (
                    self._sb
                    .table("exchanges")
                    .select("ts,user_msg,nia_msg")
                    .order("ts", desc=True)
                    .limit(n)
                    .execute()
                )
                return [
                    {"ts": r["ts"], "user": r["user_msg"], "nia": r["nia_msg"]}
                    for r in (resp.data or [])
                ]
            except Exception as exc:
                log.warning("Supabase recent_exchanges failed: %s", exc)

        # Cache fallback
        ex = [r for r in self._cache if r.get("type") == "exchange"]
        return [
            {"ts": r["ts"], "user": r.get("user_msg"), "nia": r.get("nia_msg")}
            for r in ex[-n:]
        ]

    def close(self) -> None:
        """Nothing to explicitly close with Supabase HTTP client."""
        log.debug("MemoryStore closed.")

    # ── Helpers ────────────────────────────────────────────────────

    def _embed(self, text: str) -> list[float] | None:
        """Return embedding vector or None if embedder unavailable."""
        if self._emb is None:
            return None
        try:
            return self._emb.encode(text, normalize_embeddings=True).tolist()
        except Exception as exc:
            log.debug("Embedding error: %s", exc)
            return None


# ════════════════════════════════════════════════════════════════════
# db/schema.sql  — run once against your Supabase project
# Save as: niaeleria/db/schema.sql
# ════════════════════════════════════════════════════════════════════
SCHEMA_SQL = """
-- NiaEleria Supabase Schema
-- Run once in your Supabase SQL editor, Dad.

-- Enable pgvector extension
create extension if not exists vector;

-- Conversation exchanges
create table if not exists exchanges (
    id        bigserial primary key,
    ts        timestamptz not null default now(),
    user_msg  text        not null,
    nia_msg   text        not null,
    tags      text        default '',
    embedding vector(384)          -- all-MiniLM-L6-v2 = 384 dims
);

-- Internet-learned knowledge
create table if not exists knowledge (
    id        bigserial primary key,
    ts        timestamptz not null default now(),
    source    text        not null,
    title     text        default '',
    content   text        not null,
    tags      text        default '',
    embedding vector(384)
);

-- Semantic search RPC — called by MemoryStore.search()
create or replace function match_exchanges(
    query_embedding vector(384),
    match_threshold float,
    match_count     int
)
returns table (
    id       bigint,
    ts       timestamptz,
    user_msg text,
    nia_msg  text,
    similarity float
)
language sql stable
as $$
    select
        id, ts, user_msg, nia_msg,
        1 - (embedding <=> query_embedding) as similarity
    from exchanges
    where 1 - (embedding <=> query_embedding) > match_threshold
    order by embedding <=> query_embedding
    limit match_count;
$$;

-- Row Level Security (Dad only — set this to your auth.uid())
alter table exchanges  enable row level security;
alter table knowledge  enable row level security;

-- Policy: service_role key bypasses RLS (used by NiaEleria backend)
-- If using anon key, add explicit policies here.
"""

if __name__ == "__main__":
    # Dad can run:  python -m niaeleria.core.memory
    # to print the schema SQL for copying into Supabase
    print(SCHEMA_SQL)