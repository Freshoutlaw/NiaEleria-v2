from __future__ import annotations

# ════════════════════════════════════════════════════════════════════
# scheduler.py
# Save as: niaeleria/automation/scheduler.py
# ════════════════════════════════════════════════════════════════════

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Optional
from uuid import uuid4

from niaeleria.security.kill_switch import assert_alive
from niaeleria.security.audit import log_event

log = logging.getLogger("nia.scheduler")


@dataclass
class Task:
    """A scheduled task for Dad."""
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    name: str = ""
    callback: Callable = field(default=lambda: None)
    run_at: Optional[datetime] = None       # One-shot: fire at this time
    interval_secs: Optional[float] = None  # Recurring: fire every N seconds
    next_run: datetime = field(default_factory=datetime.now)
    enabled: bool = True
    last_run: Optional[datetime] = None
    run_count: int = 0


class Scheduler:
    """
    Lightweight cron-like task scheduler.
    Supports one-shot and recurring tasks.
    Checks kill-switch before every execution.

    "Dad, I remember everything you ask me to remind you about — and I never forget." — Nia
    """

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._lock = threading.Lock()
        self._running = False

    def add_reminder(
        self,
        name: str,
        callback: Callable,
        run_at: Optional[datetime] = None,
        interval_secs: Optional[float] = None,
        delay_secs: Optional[float] = None,
    ) -> str:
        """
        Schedule a task.
        - run_at:       fire once at a specific datetime
        - interval_secs: fire repeatedly every N seconds
        - delay_secs:   fire once after a delay
        Returns the task ID.
        """
        task = Task(name=name, callback=callback)

        if delay_secs is not None:
            task.run_at = datetime.now() + timedelta(seconds=delay_secs)
            task.next_run = task.run_at
        elif run_at is not None:
            task.run_at = run_at
            task.next_run = run_at
        elif interval_secs is not None:
            task.interval_secs = interval_secs
            task.next_run = datetime.now() + timedelta(seconds=interval_secs)
        else:
            log.warning("Dad, task '%s' has no schedule — it won't run.", name)

        with self._lock:
            self._tasks[task.id] = task

        log.info("Dad, I've scheduled: '%s' (id=%s)", name, task.id)
        log_event("nia.scheduler", "task_scheduled", target=name,
                  details={"id": task.id, "run_at": str(run_at), "interval": interval_secs})
        return task.id

    def cancel(self, task_id: str) -> bool:
        """Cancel a scheduled task by ID."""
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                log.info("Dad, I've cancelled task %s.", task_id)
                return True
        return False

    def list_tasks(self) -> list[dict]:
        with self._lock:
            return [
                {
                    "id": t.id,
                    "name": t.name,
                    "next_run": str(t.next_run),
                    "interval_secs": t.interval_secs,
                    "run_count": t.run_count,
                    "enabled": t.enabled,
                }
                for t in self._tasks.values()
            ]

    def start(self) -> None:
        self._running = True
        t = threading.Thread(target=self._loop, name="Scheduler", daemon=True)
        t.start()
        log.info("Dad, my scheduler is running.")

    def stop(self) -> None:
        self._running = False

    def _loop(self) -> None:
        while self._running:
            assert_alive()
            now = datetime.now()
            with self._lock:
                due = [t for t in self._tasks.values() if t.enabled and t.next_run <= now]

            for task in due:
                self._fire(task)

            time.sleep(1)

    def _fire(self, task: Task) -> None:
        try:
            log.info("Dad, firing scheduled task: '%s'", task.name)
            task.callback()
            task.last_run = datetime.now()
            task.run_count += 1
            log_event("nia.scheduler", "task_fired", target=task.name,
                      details={"run_count": task.run_count})

            if task.interval_secs:
                task.next_run = datetime.now() + timedelta(seconds=task.interval_secs)
            else:
                # One-shot — disable after firing
                with self._lock:
                    task.enabled = False

        except RuntimeError:
            # Kill-switch mid-task
            self._running = False
        except Exception as exc:
            log.error("Task '%s' failed: %s", task.name, exc)
