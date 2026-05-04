
# ════════════════════════════════════════════════════════════════════
# niaeleria/guard/toolkit.py — Sandboxed offensive/security toolkit
# ════════════════════════════════════════════════════════════════════

class SecurityToolkit:
    """
    Consent-gated, Docker-sandboxed security tools: nmap, nuclei, hashcat, etc.
    ONLY runs against authorized targets. NEVER autonomous. Fully audited.

    "Dad, I keep the knives locked up. You hold the key." — Nia
    """

    ALLOWED_TOOLS = {"nmap", "nuclei", "hashcat", "whatweb", "nikto"}

    @classmethod
    def run_tool(
        cls,
        tool: str,
        target: str,
        args: str = "",
        authorized_by_dad: bool = False,
    ) -> dict:
        """
        Run a security tool in a Docker sandbox with minimal privileges.
        Requires explicit Dad consent before execution.
        """
        from niaeleria.config import DOCKER_SANDBOX_IMAGE, DOCKER_TIMEOUT_SECS

        assert_alive()

        if tool not in cls.ALLOWED_TOOLS:
            return {"error": f"Dad, '{tool}' is not in my allowed toolkit. I won't run unknown tools."}

        if not authorized_by_dad:
            approved = require_consent(
                f"Run {tool} against {target}",
                level=ConsentLevel.HIGH,
            )
            if not approved:
                return {"error": f"Dad, you didn't approve running {tool} against {target}."}

        log.info("Dad, running %s against %s in sandbox...", tool, target)
        log_event("nia.toolkit", f"run_{tool}", target=target,
                  severity="HIGH", approved=True,
                  details={"args": args})

        cmd = [
            "docker", "run", "--rm",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--network=host",
            f"--timeout={DOCKER_TIMEOUT_SECS}",
            DOCKER_SANDBOX_IMAGE,
            tool, target,
        ]
        if args:
            cmd.extend(args.split())

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=DOCKER_TIMEOUT_SECS
            )
            return {
                "tool": tool,
                "target": target,
                "stdout": result.stdout[:5000],
                "stderr": result.stderr[:1000],
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"error": f"Dad, {tool} timed out after {DOCKER_TIMEOUT_SECS}s."}
        except FileNotFoundError:
            return {"error": "Dad, Docker is not installed or not in PATH."}
        except Exception as exc:
            return {"error": f"Dad, toolkit error: {exc}"}