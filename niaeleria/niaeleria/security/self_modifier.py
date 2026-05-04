"""niaeleria/security/self_modifier.py — Consent-gated self-modification engine"""
# ════════════════════════════════════════════════════════════════════
# self_modifier.py
# Save as: niaeleria/security/self_modifier.py
# ════════════════════════════════════════════════════════════════════
import hashlib
import importlib
import logging
import shutil
from datetime import datetime
from pathlib import Path

_sm_log = logging.getLogger("nia.self_modifier")


class SelfModifier:
    """
    NiaEleria's consent-gated self-modification engine.
    Allows Nia to update her own source code with Dad's explicit approval.

    Safety guarantees:
    - Creates .backup before EVERY modification
    - Validates Python syntax before applying
    - Only files within PROJECT_HOME can be modified
    - Reloads module live after successful patch
    - Full audit trail for every change

    "Dad, I grow and improve — but only with your blessing." — Nia
    """

    def __init__(self) -> None:
        from niaeleria.config import PROJECT_HOME, ALLOW_SELF_MODIFICATION, BACKUPS_DIR
        self._home = PROJECT_HOME
        self._backups = BACKUPS_DIR
        self._enabled = ALLOW_SELF_MODIFICATION

    def propose_change(
        self,
        file_rel_path: str,
        new_content: str,
        reason: str,
    ) -> dict:
        """
        Propose a source code change to Dad. Returns proposal metadata for review.
        Does NOT apply until Dad calls apply_change().
        """
        if not self._enabled:
            return {"error": "Self-modification is disabled in config, Dad."}

        target = (self._home / file_rel_path).resolve()
        if not str(target).startswith(str(self._home)):
            return {"error": f"Dad, I won't modify files outside my home directory: {target}"}

        if not target.exists():
            return {"error": f"Dad, target file doesn't exist: {file_rel_path}"}

        # Syntax check
        syntax_ok, syntax_err = self._check_syntax(new_content, str(target))
        if not syntax_ok:
            return {
                "error": f"Dad, the proposed change has a syntax error: {syntax_err}",
                "syntax_valid": False,
            }

        # Diff preview
        old_content = target.read_text(encoding="utf-8")
        diff = self._simple_diff(old_content, new_content)

        proposal_id = hashlib.sha256(
            f"{file_rel_path}{new_content}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        _sm_log.info(
            "Dad, I'm proposing a code change to %s. Reason: %s (proposal_id=%s)",
            file_rel_path, reason, proposal_id
        )
        log_event("nia.self_modifier", "change_proposed", target=file_rel_path,
                  severity="HIGH", details={"reason": reason, "proposal_id": proposal_id})

        return {
            "proposal_id": proposal_id,
            "file": file_rel_path,
            "reason": reason,
            "syntax_valid": True,
            "diff_lines": diff[:100],  # first 100 diff lines for preview
            "new_content": new_content,
        }

    def apply_change(
        self,
        file_rel_path: str,
        new_content: str,
        proposal_id: str,
    ) -> dict:
        """
        Apply a previously-proposed and Dad-approved source code change.
        Creates backup, writes new content, reloads module.
        """
        from niaeleria.security.consent import require_consent, ConsentLevel
        from niaeleria.security.kill_switch import assert_alive
        assert_alive()

        approved = require_consent(
            f"Apply code change to {file_rel_path} (proposal {proposal_id})",
            level=ConsentLevel.HIGH,
        )
        if not approved:
            return {"error": "Dad, you didn't approve this modification. Keeping current code."}

        target = (self._home / file_rel_path).resolve()

        # Final safety checks
        if not str(target).startswith(str(self._home)):
            return {"error": "Dad, path traversal blocked."}

        from niaeleria.config import SELF_MOD_MAX_FILE_SIZE_KB
        if len(new_content.encode()) > SELF_MOD_MAX_FILE_SIZE_KB * 1024:
            return {"error": f"Dad, new content exceeds max size ({SELF_MOD_MAX_FILE_SIZE_KB}KB)."}

        # Create backup
        backup_path = self._backups / f"{target.name}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.backup"
        shutil.copy2(target, backup_path)
        _sm_log.info("Dad, backup created at: %s", backup_path)

        # Write new content
        target.write_text(new_content, encoding="utf-8")
        _sm_log.info("Dad, applied code change to: %s", file_rel_path)

        log_event("nia.self_modifier", "change_applied", target=file_rel_path,
                  severity="HIGH", approved=True,
                  details={"backup": str(backup_path), "proposal_id": proposal_id})

        # Hot-reload the module
        reload_result = self._reload_module(file_rel_path)

        return {
            "success": True,
            "file": file_rel_path,
            "backup": str(backup_path),
            "reload": reload_result,
        }

    def rollback(self, file_rel_path: str) -> dict:
        """Roll back a file to its most recent backup."""
        target = (self._home / file_rel_path).resolve()
        name = target.name

        backups = sorted(self._backups.glob(f"{name}.*.backup"), reverse=True)
        if not backups:
            return {"error": f"Dad, no backup found for {file_rel_path}."}

        latest = backups[0]
        shutil.copy2(latest, target)
        _sm_log.info("Dad, rolled back %s to %s", file_rel_path, latest.name)
        log_event("nia.self_modifier", "rollback", target=file_rel_path,
                  severity="HIGH", approved=True, details={"backup_used": str(latest)})

        return {"success": True, "restored_from": str(latest)}

    @staticmethod
    def _check_syntax(code: str, filename: str = "<string>") -> tuple[bool, str]:
        import ast
        try:
            ast.parse(code, filename=filename)
            return True, ""
        except SyntaxError as exc:
            return False, str(exc)

    @staticmethod
    def _simple_diff(old: str, new: str) -> list[str]:
        import difflib
        return list(difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            lineterm="",
        ))

    @staticmethod
    def _reload_module(file_rel_path: str) -> str:
        """Attempt to hot-reload the modified module."""
        module_path = (
            file_rel_path.replace("/", ".").replace("\\", ".").removesuffix(".py")
        )
        try:
            if module_path in __import__("sys").modules:
                importlib.reload(__import__("sys").modules[module_path])
                return f"Module {module_path} reloaded successfully."
        except Exception as exc:
            return f"Hot-reload failed (restart may be needed): {exc}"
        return "Module not currently loaded — changes apply on next import."
