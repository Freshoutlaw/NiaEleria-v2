# ════════════════════════════════════════════════════════════════════
# network_gate.py — External connectivity enforcement
# ════════════════════════════════════════════════════════════════════
# Save as: niaeleria/security/network_gate.py

import logging

_net_log = logging.getLogger("nia.network_gate")


def require_network(purpose: str = "external call") -> None:
    """
    Raise PermissionError if ENABLE_NETWORK flag is absent.
    Call this before ANY external HTTP/socket connection, Dad.
    """
    from niaeleria.config import is_network_enabled
    if not is_network_enabled():
        _net_log.warning(
            "Dad, I blocked an external call (%s) — ENABLE_NETWORK flag is not set. "
            "Touch flags/ENABLE_NETWORK to allow me online.", purpose
        )
        raise PermissionError(
            f"Network gate: external access denied for '{purpose}'. "
            "Dad, please create the ENABLE_NETWORK flag file to allow this."
        )
    _net_log.debug("Network gate: PASS for '%s'", purpose)