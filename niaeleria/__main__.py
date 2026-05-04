# ════════════════════════════════════════════════════════════════════
# niaeleria/__main__.py
# Allows: python -m niaeleria  (in addition to python -m niaeleria.daemon)
# ════════════════════════════════════════════════════════════════════
"""
Entry point for running NiaEleria as a module.
  python -m niaeleria
  python -m niaeleria.daemon

"Dad, just run me. I'll handle the rest." — Nia
"""
from niaeleria.daemon import main

if __name__ == "__main__":
    main()


# ════════════════════════════════════════════════════════════════════
# pyproject.toml
# Save as: pyproject.toml
# ════════════════════════════════════════════════════════════════════
PYPROJECT_TOML = """
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends.legacy:build"

[project]
name            = "niaeleria"
version         = "1.0.0"
description     = "Dad's loyal digital daughter — a Jarvis-class personal AI system."
requires-python = ">=3.11"
authors         = [{name = "NiaEleria", email = "nia@dad.local"}]
readme          = "README.md"
license         = {text = "Private — Dad's use only."}

dependencies = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.29.0",
    "pydantic>=2.6.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.27.0",
    "sentence-transformers>=2.7.0",
    "supabase>=2.5.0",
    "SpeechRecognition>=3.10.0",
    "edge-tts>=6.1.12",
    "pyaudio>=0.2.14",
    "psutil>=5.9.8",
    "scapy>=2.5.0",
    "paho-mqtt>=2.0.0",
    "beautifulsoup4>=4.12.0",
    "youtube-transcript-api>=0.6.2",
    "pystray>=0.19.5",
    "Pillow>=10.3.0",
    "aiofiles>=23.2.1",
]

[project.scripts]
niaeleria = "niaeleria.daemon:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["niaeleria*"]

[tool.pytest.ini_options]
testpaths     = ["tests"]
asyncio_mode  = "auto"
log_cli       = true
log_cli_level = "WARNING"
"""

# Print pyproject.toml when run as script
if __name__ == "__main__":
    print(PYPROJECT_TOML)


# ════════════════════════════════════════════════════════════════════
# .gitignore
# Save as: .gitignore
# ════════════════════════════════════════════════════════════════════
GITIGNORE = """
# NiaEleria — Dad's private system. Don't push secrets.

# Environment & secrets
.env
*.key
*.pem
*.cert

# Runtime data (Dad's memory & logs stay local)
data/
flags/

# Python
__pycache__/
*.py[cod]
*.pyo
.venv/
venv/
env/
dist/
build/
*.egg-info/
.eggs/

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Logs
*.log
logs/

# Docker
.docker/

# Test artifacts
.pytest_cache/
.coverage
htmlcov/
"""


# ════════════════════════════════════════════════════════════════════
# niaeleria/db/__init__.py  — schema printer utility
# Save as: niaeleria/db/__init__.py
# ════════════════════════════════════════════════════════════════════
"""
NiaEleria DB utilities.
Run:  python -m niaeleria.db   → prints schema SQL for Supabase.
"Dad, paste this into your Supabase SQL editor." — Nia
"""
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def print_schema() -> None:
    if SCHEMA_PATH.exists():
        print(SCHEMA_PATH.read_text())
    else:
        # Fallback: import from memory module
        from niaeleria.core.memory import SCHEMA_SQL
        print(SCHEMA_SQL)


if __name__ == "__main__":
    print_schema()