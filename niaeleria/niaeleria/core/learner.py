"""
niaeleria/core/learner.py
──────────────────────────
NiaEleria's internet learning engine.
Scrapes URLs, extracts YouTube transcripts, summarises via LLM,
and indexes everything into Dad's Supabase knowledge base.

Every learning session:
  • Requires ENABLE_NETWORK flag
  • Requires Dad's consent
  • Is summarised by the LLM
  • Is stored in Supabase (knowledge table)
  • Is announced on the HUD

"Dad, every page I read, I read for you." — Nia
"""

from __future__ import annotations

import logging
import re
import threading
import time
from typing import Optional

from niaeleria.security.kill_switch import assert_alive
from niaeleria.security.network_gate import require_network
from niaeleria.security.consent import require_consent, ConsentLevel
from niaeleria.security.audit import log_event

log = logging.getLogger("nia.learner")


def _push(msg: dict) -> None:
    try:
        from niaeleria.api.server import push_to_hud
        push_to_hud(msg)
    except Exception:
        pass


class InternetLearner:
    """
    Self-directed learning module.

    Capabilities:
      learn_from_url(url)      — fetch, extract, summarise, index
      learn_from_youtube(url)  — transcript, summarise, index
      start_background_learning(urls, interval_hours) — periodic re-index

    Knowledge is stored in Supabase `knowledge` table with pgvector embeddings,
    making it available to Nia's RAG pipeline in every future conversation.

    "Dad, I get smarter every day — and it all goes into memory for you." — Nia
    """

    def __init__(self, memory, brain) -> None:
        self._memory = memory
        self._brain  = brain
        self._bg_thread: Optional[threading.Thread] = None
        self._bg_running = False

    # ── Public API ──────────────────────────────────────────────────

    async def learn_from_url(self, url: str, tags: str = "") -> str:
        """
        Fetch a URL, extract text, summarise via LLM, store in Supabase.
        Returns the summary string.
        """
        assert_alive()
        require_network(f"learn from URL: {url}")

        approved = require_consent(
            f"Fetch and learn from URL: {url}",
            level=ConsentLevel.MEDIUM,
        )
        if not approved:
            return "Dad said no — skipping URL learning."

        _push({
            "type": "nia_speak",
            "text": f"Dad, I'm fetching and reading that page now. Give me a moment.",
            "label": "NIA · LEARNING",
        })

        content = await self._fetch_url(url)
        if not content:
            msg = f"Dad, I couldn't read content from {url}. The page may be blocked or empty."
            _push({"type": "nia_speak", "text": msg, "label": "NIA · LEARNING"})
            return msg

        title   = self._extract_title(content)
        summary = await self._summarise(url, content[:6000])

        await self._memory.store_knowledge(
            source=url,
            content=summary,
            title=title,
            tags=tags or "url,learned",
        )

        log_event(
            "nia.learner", "learned_url", target=url,
            severity="INFO", approved=True,
            details={"title": title, "summary_len": len(summary)},
        )
        log.info("Dad, I learned from: %s (%s)", url, title)

        _push({
            "type": "nia_speak",
            "text": (
                f"Done, Dad. I've read and indexed '{title}'. "
                f"Summary: {summary[:180]}{'...' if len(summary) > 180 else ''}"
            ),
            "label": "NIA · LEARNED",
        })
        return summary

    async def learn_from_youtube(self, video_url: str, tags: str = "") -> str:
        """
        Extract a YouTube video transcript, summarise, and store in Supabase.
        """
        assert_alive()
        require_network("YouTube transcript fetch")

        video_id = self._extract_youtube_id(video_url)
        if not video_id:
            return "Dad, that doesn't look like a valid YouTube URL."

        _push({
            "type": "nia_speak",
            "text": f"Dad, pulling the transcript from that YouTube video now.",
            "label": "NIA · LEARNING",
        })

        try:
            from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
            try:
                entries = YouTubeTranscriptApi.get_transcript(video_id)
            except (TranscriptsDisabled, NoTranscriptFound):
                msg = f"Dad, that video doesn't have an available transcript (ID: {video_id})."
                _push({"type": "nia_speak", "text": msg, "label": "NIA · LEARNING"})
                return msg

            transcript = " ".join(e["text"] for e in entries)

        except ImportError:
            return (
                "Dad, youtube-transcript-api isn't installed. "
                "Run: pip install youtube-transcript-api"
            )
        except Exception as exc:
            msg = f"Dad, I couldn't get the transcript: {exc}"
            _push({"type": "nia_speak", "text": msg, "label": "NIA · LEARNING"})
            return msg

        summary = await self._summarise(video_url, transcript[:6000])

        await self._memory.store_knowledge(
            source=video_url,
            content=summary,
            title=f"YouTube: {video_id}",
            tags=tags or "youtube,video,learned",
        )

        log_event(
            "nia.learner", "learned_youtube", target=video_url,
            severity="INFO", approved=True,
            details={"video_id": video_id, "transcript_len": len(transcript)},
        )
        log.info("Dad, I learned from YouTube: %s", video_id)

        _push({
            "type": "nia_speak",
            "text": (
                f"Done, Dad. Indexed that YouTube video. "
                f"Summary: {summary[:180]}{'...' if len(summary) > 180 else ''}"
            ),
            "label": "NIA · LEARNED",
        })
        return summary

    async def search_knowledge(self, query: str, top_k: int = 5) -> list[dict]:
        """Search learned knowledge base semantically."""
        return await self._memory.search(query, top_k=top_k)

    def start_background_learning(
        self,
        urls: list[str],
        interval_hours: float = 24.0,
    ) -> None:
        """
        Periodically revisit a list of URLs and refresh their knowledge.
        Runs in a background daemon thread.
        """
        if self._bg_running:
            log.info("Background learning already running, Dad.")
            return

        self._bg_running = True

        def _loop() -> None:
            import asyncio
            log.info(
                "Dad, background learning is active for %d URL(s). "
                "Refreshing every %.0f hours.", len(urls), interval_hours,
            )
            while self._bg_running:
                loop = asyncio.new_event_loop()
                for url in urls:
                    try:
                        assert_alive()
                        loop.run_until_complete(
                            self.learn_from_url(url, tags="auto,background")
                        )
                    except RuntimeError:
                        self._bg_running = False
                        break
                    except Exception as exc:
                        log.warning(
                            "Background learning error for %s: %s", url, exc
                        )
                loop.close()

                if not self._bg_running:
                    break

                sleep_secs = interval_hours * 3600
                log.info(
                    "Dad, background learning cycle complete. Next in %.0f hours.",
                    interval_hours,
                )
                # Sleep in small intervals so kill-switch is respected
                deadline = time.monotonic() + sleep_secs
                while time.monotonic() < deadline and self._bg_running:
                    if is_killed():
                        self._bg_running = False
                        break
                    time.sleep(5)

        self._bg_thread = threading.Thread(
            target=_loop, name="BackgroundLearner", daemon=True
        )
        self._bg_thread.start()

    def stop_background_learning(self) -> None:
        self._bg_running = False

    # ── Private helpers ─────────────────────────────────────────────

    async def _summarise(self, source: str, content: str) -> str:
        """Ask the LLM to summarise content for indexing into Dad's knowledge base."""
        prompt = (
            f"Dad asked me to learn from this content (source: {source}). "
            "Please summarise it clearly and concisely so I can index it into "
            "my knowledge base. Focus on key facts, concepts, and actionable insights:\n\n"
            f"{content}"
        )
        try:
            return await self._brain.chat(prompt)
        except Exception as exc:
            log.warning("Summarisation failed: %s", exc)
            return content[:500]

    async def _fetch_url(self, url: str) -> Optional[str]:
        """Fetch and extract readable text from a URL."""
        try:
            import httpx
            from bs4 import BeautifulSoup
            async with httpx.AsyncClient(
                timeout=20,
                follow_redirects=True,
                headers={"User-Agent": "NiaEleria/1.0 (Dad's AI)"},
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                # Strip noise
                for tag in soup(["script", "style", "nav", "footer", "header",
                                  "aside", "form", "noscript"]):
                    tag.decompose()

                text = soup.get_text(separator=" ", strip=True)
                # Collapse whitespace
                text = re.sub(r"\s{3,}", "  ", text)
                return text

        except ImportError:
            log.error(
                "Dad, beautifulsoup4 not installed. "
                "Run: pip install beautifulsoup4"
            )
        except Exception as exc:
            log.error("URL fetch error (%s): %s", url, exc)
        return None

    @staticmethod
    def _extract_title(text: str) -> str:
        m = re.search(r"<title[^>]*>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
        if m:
            return m.group(1).strip()[:120]
        # Try first meaningful line
        lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 20]
        return lines[0][:80] if lines else "Untitled"

    @staticmethod
    def _extract_youtube_id(url: str) -> Optional[str]:
        patterns = [
            r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})",
            r"(?:embed/|shorts/)([A-Za-z0-9_-]{11})",
        ]
        for pat in patterns:
            m = re.search(pat, url)
            if m:
                return m.group(1)
        return None


# Make is_killed available at module level for background loop
from niaeleria.config import is_killed