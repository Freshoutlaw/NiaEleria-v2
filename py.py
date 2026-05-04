#!/usr/bin/env python3
"""
Project Scaffold Generator for Niaeleria
Creates the full directory tree and stub files.
"""

import os
import stat
from pathlib import Path

# ------------------------------------------------------------
#  Define the project structure and file contents
# ------------------------------------------------------------

PROJECT_ROOT = Path.cwd() / "niaeleria"

# Content for files (as strings)
CONTENT = {
    # Root level files
    ".env.example": """# Niaeleria Environment Variables
OPENAI_API_KEY=your_openai_key_here
CHROMA_PERSIST_DIR=./data/chroma
AUDIT_KEY=your_hmac_key_here
MQTT_BROKER=localhost
MQTT_PORT=1883
""",
    "requirements.txt": """fastapi==0.115.6
uvicorn[standard]==0.34.0
websockets==12.0
pydantic==2.10.4
python-dotenv==1.0.1
chromadb==0.5.20
openai==1.59.7
edge-tts==6.1.15
SpeechRecognition==3.12.0
pystray==0.19.0
Pillow==10.4.0
paho-mqtt==1.6.1
schedule==1.2.2
psutil==6.1.1
scapy==2.5.0  # optional, for packet sniffing
nmap==1.7.0
docker==7.1.0
requests==2.32.3
beautifulsoup4==4.12.3
yt-dlp==2024.12.23
pytest==8.3.4
""",
    "Dockerfile": """FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONPATH=/app
CMD ["python", "-m", "niaeleria.daemon"]
""",
    "docker-compose.yml": """version: '3.8'
services:
  niaeleria:
    build: .
    volumes:
      - ./data:/app/data
      - ./flags:/app/flags
    environment:
      - ENV=production
    restart: unless-stopped
    network_mode: host   # for firewall & packet operations
""",
    "bootstrap.sh": """#!/bin/bash
# Quick bootstrap for Niaeleria
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
mkdir -p data/flags data/backups
touch flags/ENABLE_NETWORK   # enable network by default (remove if you want offline)
echo "Bootstrap done. Run 'python -m niaeleria.daemon'"
""",
    "README.md": """# Niaeleria
Your AI companion with memory, voice, automation, and security guard.

## Quick Start
1. Copy `.env.example` to `.env` and fill in your keys.
2. Run `bash bootstrap.sh`
3. Start the daemon: `python -m niaeleria.daemon`

## Flags
- `flags/GUARD_ACTIVE` – enables cyber guard
- `flags/STOP_EVERYTHING` – emergency stop (delete to resume)
- `flags/ENABLE_NETWORK` – allows network operations

## API
Web UI runs on `http://localhost:8000`
""",
    ".gitignore": """# Byte-compiled
__pycache__/
*.pyc

# Virtual environments
venv/
env/

# Runtime data
data/
flags/
*.log

# IDE
.vscode/
.idea/
""",

    # Top‑level package __init__.py
    "niaeleria/__init__.py": "\"\"\"Niaeleria - Your AI companion\"\"\"\n__version__ = \"0.1.0\"\n",
    "niaeleria/config.py": """import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    # Paths
    base_dir: Path = Path(__file__).parent.parent
    data_dir: Path = base_dir / "data"
    flags_dir: Path = base_dir / "flags"
    chroma_dir: Path = data_dir / "chroma"
    audit_log: Path = data_dir / "audit.log"
    backups_dir: data_dir / "backups"

    # API keys
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    audit_key: str = os.getenv("AUDIT_KEY", "")

    # MQTT
    mqtt_broker: str = os.getenv("MQTT_BROKER", "localhost")
    mqtt_port: int = int(os.getenv("MQTT_PORT", "1883"))

    # Features
    network_enabled: bool = (flags_dir / "ENABLE_NETWORK").exists()
    guard_active: bool = (flags_dir / "GUARD_ACTIVE").exists()
    kill_switch: bool = (flags_dir / "STOP_EVERYTHING").exists()

    def refresh_flags(self):
        self.network_enabled = (self.flags_dir / "ENABLE_NETWORK").exists()
        self.guard_active = (self.flags_dir / "GUARD_ACTIVE").exists()
        self.kill_switch = (self.flags_dir / "STOP_EVERYTHING").exists()

config = Config()
""",
    "niaeleria/daemon.py": "\"\"\"Master service launcher & watchdog\"\"\"\nimport time\nimport logging\nfrom .config import config\nfrom .security.kill_switch import KillSwitch\n\nlogging.basicConfig(level=logging.INFO)\nlog = logging.getLogger(__name__)\n\ndef main():\n    log.info(\"Starting Niaeleria daemon...\")\n    kill = KillSwitch()\n    while True:\n        if kill.is_triggered():\n            log.warning(\"Kill switch active – exiting\")\n            break\n        # TODO: launch all subsystems (API, guard, sync, etc.)\n        time.sleep(5)\n\nif __name__ == \"__main__\":\n    main()\n",

    # Core module
    "niaeleria/core/__init__.py": "# Core intelligence modules\n",
    "niaeleria/core/brain.py": "\"\"\"LLM brain – RAG, chat, calls Dad by name\"\"\"\nfrom openai import OpenAI\nfrom ..config import config\n\nclass Brain:\n    def __init__(self):\n        self.client = OpenAI(api_key=config.openai_api_key)\n        self.persona = None  # will be set by Persona engine\n\n    def chat(self, message: str, context: list = None):\n        # Placeholder: integrate RAG and mood\n        response = self.client.chat.completions.create(\n            model=\"gpt-4o-mini\",\n            messages=[{\"role\": \"user\", \"content\": message}]\n        )\n        return response.choices[0].message.content\n",
    "niaeleria/core/persona.py": "\"\"\"Mood-aware system prompt engine\"\"\"\nimport random\n\nclass Persona:\n    MOODS = [\"cheerful\", \"analytic\", \"protective\", \"sleepy\"]\n\n    def __init__(self):\n        self.current_mood = \"cheerful\"\n\n    def get_system_prompt(self) -> str:\n        prompts = {\n            \"cheerful\": \"You are Nia, a helpful and enthusiastic AI companion.\",\n            \"analytic\": \"Provide detailed, precise, logical answers.\",\n            \"protective\": \"Prioritise safety and caution in all suggestions.\",\n            \"sleepy\": \"Be minimal and brief, only essential info.\"\n        }\n        return prompts.get(self.current_mood, prompts[\"cheerful\"])\n\n    def update_mood_from_conversation(self, user_input: str):\n        # simple keyword heuristic\n        if \"urgent\" in user_input:\n            self.current_mood = \"protective\"\n        elif \"explain\" in user_input:\n            self.current_mood = \"analytic\"\n        else:\n            self.current_mood = random.choice(self.MOODS)\n",
    "niaeleria/core/memory.py": "\"\"\"SQLite + ChromaDB episodic memory\"\"\"\nimport sqlite3\nimport chromadb\nfrom ..config import config\n\nclass Memory:\n    def __init__(self):\n        self.sql_conn = sqlite3.connect(config.data_dir / \"memory.db\")\n        self.sql_conn.execute(\"CREATE TABLE IF NOT EXISTS episodes (id INTEGER PRIMARY KEY, timestamp TEXT, content TEXT)\")\n        self.chroma_client = chromadb.PersistentClient(path=str(config.chroma_dir))\n        self.collection = self.chroma_client.get_or_create_collection(\"episodes\")\n\n    def add_episode(self, text: str):\n        # store in SQLite\n        self.sql_conn.execute(\"INSERT INTO episodes (content) VALUES (?)\", (text,))\n        self.sql_conn.commit()\n        # vector store\n        self.collection.add(documents=[text], ids=[str(hash(text))])\n\n    def recall_similar(self, query: str, k=3):\n        results = self.collection.query(query_texts=[query], n_results=k)\n        return results['documents'][0] if results else []\n",
    "niaeleria/core/learner.py": "\"\"\"Internet learning, URL scraping, YouTube\"\"\"\nimport requests\nfrom bs4 import BeautifulSoup\nfrom yt_dlp import YoutubeDL\nfrom ..security.network_gate import require_network\n\nclass Learner:\n    @require_network\n    def scrape_url(self, url: str) -> str:\n        resp = requests.get(url, timeout=10)\n        soup = BeautifulSoup(resp.text, 'html.parser')\n        return soup.get_text()[:5000]\n\n    @require_network\n    def youtube_transcript(self, video_url: str) -> str:\n        # simplistic: use yt-dlp to get subtitles\n        ydl_opts = {'skip_download': True, 'writesubtitles': True, 'subtitleslangs': ['en']}\n        with YoutubeDL(ydl_opts) as ydl:\n            info = ydl.extract_info(video_url, download=False)\n            # actual subtitle extraction would be more involved\n            return str(info.get('description', ''))[:2000]\n",

    # Security module
    "niaeleria/security/__init__.py": "# Security & consent subsystems\n",
    "niaeleria/security/kill_switch.py": "\"\"\"STOP_EVERYTHING poller — highest priority\"\"\"\nfrom ..config import config\n\nclass KillSwitch:\n    def is_triggered(self) -> bool:\n        config.refresh_flags()\n        return config.kill_switch\n\n    def trigger(self):\n        (config.flags_dir / \"STOP_EVERYTHING\").touch()\n\n    def clear(self):\n        (config.flags_dir / \"STOP_EVERYTHING\").unlink(missing_ok=True)\n",
    "niaeleria/security/consent.py": "\"\"\"Consent manager — gates all actions\"\"\"\nfrom enum import Enum\nimport json\n\nclass ActionType(Enum):\n    NETWORK_ACCESS = \"network_access\"\n    FILE_MODIFICATION = \"file_modification\"\n    SELF_MODIFICATION = \"self_modification\"\n\nclass ConsentManager:\n    def __init__(self):\n        self.consent_file = None  # would load from config\n\n    def request_consent(self, action: ActionType, details: str) -> bool:\n        \"\"\"Always ask the user via API/systray; for stub return True\"\"\"\n        print(f\"[CONSENT] Action {action.value}: {details}\")\n        # In real implementation: prompt user, check flag file, etc.\n        return True\n\n    def revoke(self, action: ActionType):\n        pass\n",
    "niaeleria/security/audit.py": "\"\"\"HMAC-SHA256 append-only audit log\"\"\"\nimport hmac\nimport hashlib\nfrom datetime import datetime\nfrom ..config import config\n\nclass AuditLog:\n    def __init__(self):\n        self.log_path = config.audit_log\n        self.key = config.audit_key.encode()\n        if not self.log_path.exists():\n            self.log_path.touch()\n\n    def _hmac(self, entry: str) -> str:\n        return hmac.new(self.key, entry.encode(), hashlib.sha256).hexdigest()\n\n    def log(self, event: str, details: str):\n        timestamp = datetime.utcnow().isoformat()\n        line = f\"{timestamp} | {event} | {details}\"\n        signature = self._hmac(line)\n        with self.log_path.open(\"a\") as f:\n            f.write(f\"{line} | HMAC={signature}\\n\")\n",
    "niaeleria/security/network_gate.py": "\"\"\"ENABLE_NETWORK flag enforcement\"\"\"\nfrom functools import wraps\nfrom ..config import config\n\nclass NetworkDisabledError(Exception):\n    pass\n\ndef require_network(func):\n    @wraps(func)\n    def wrapper(*args, **kwargs):\n        config.refresh_flags()\n        if not config.network_enabled:\n            raise NetworkDisabledError(\"Network access denied – enable by touching flags/ENABLE_NETWORK\")\n        return func(*args, **kwargs)\n    return wrapper\n",
    "niaeleria/security/self_modifier.py": "\"\"\"Consent-gated self-modification engine\"\"\"\nimport shutil\nfrom pathlib import Path\nfrom .consent import ConsentManager, ActionType\nfrom ..config import config\n\nclass SelfModifier:\n    def __init__(self):\n        self.consent = ConsentManager()\n        self.backup_dir = config.backups_dir\n        self.backup_dir.mkdir(parents=True, exist_ok=True)\n\n    def replace_file(self, target_path: Path, new_content: str) -> bool:\n        if not self.consent.request_consent(ActionType.SELF_MODIFICATION, f\"Replace {target_path}\"):\n            return False\n        # backup\n        backup_path = self.backup_dir / f\"{target_path.name}.bak\"\n        shutil.copy2(target_path, backup_path)\n        # write new content\n        target_path.write_text(new_content)\n        return True\n",

    # Guard module
    "niaeleria/guard/__init__.py": "# Cyber guard and threat detection\n",
    "niaeleria/guard/cyber_guard.py": "\"\"\"Always-on: packet sniff, process, file integrity\"\"\"\nimport hashlib\nfrom pathlib import Path\n\nclass CyberGuard:\n    def __init__(self):\n        self.baseline = {}\n\n    def hash_file(self, path: Path) -> str:\n        return hashlib.sha256(path.read_bytes()).hexdigest()\n\n    def monitor_file(self, path: Path):\n        # store baseline and later check for changes\n        self.baseline[str(path)] = self.hash_file(path)\n\n    def check_integrity(self, path: Path) -> bool:\n        return self.baseline.get(str(path)) == self.hash_file(path)\n\n    def start_packet_sniffer(self):\n        # stub: implement with scapy\n        pass\n",
    "niaeleria/guard/firewall.py": "\"\"\"iptables/netsh/pfctl abstraction\"\"\"\nimport platform\nimport subprocess\n\nclass Firewall:\n    def __init__(self):\n        self.os_type = platform.system()\n\n    def block_ip(self, ip: str):\n        if self.os_type == \"Linux\":\n            subprocess.run([\"iptables\", \"-A\", \"INPUT\", \"-s\", ip, \"-j\", \"DROP\"], check=False)\n        elif self.os_type == \"Windows\":\n            subprocess.run([\"netsh\", \"advfirewall\", \"firewall\", \"add\", \"rule\", f\"name=block_{ip}\", \"dir=in\", \"action=block\", f\"remoteip={ip}\"], check=False)\n        # macOS pfctl stubbed\n",
    "niaeleria/guard/threat_intel.py": "\"\"\"Threat classification, IP reputation\"\"\"\nimport requests\nfrom ..security.network_gate import require_network\n\nclass ThreatIntel:\n    @require_network\n    def check_ip(self, ip: str) -> dict:\n        # using free abuseipdb or similar\n        # stub returns dummy\n        return {\"reputation\": \"unknown\", \"abuse_score\": 0}\n",
    "niaeleria/guard/toolkit.py": "\"\"\"Sandboxed nmap/nuclei/hashcat (Docker)\"\"\"\nimport docker\n\nclass SandboxedTools:\n    def __init__(self):\n        self.docker = docker.from_env()\n\n    def run_nmap(self, target: str) -> str:\n        container = self.docker.containers.run(\n            \"instrumentisto/nmap\",\n            f\"nmap -sV {target}\",\n            remove=True,\n            detach=False\n        )\n        return container.decode()\n",

    # Voice module
    "niaeleria/voice/__init__.py": "# Voice interaction\n",
    "niaeleria/voice/wake_word.py": "\"\"\"Hey Nia detection (Porcupine/snowboy)\"\"\"\nclass WakeWordDetector:\n    def __init__(self):\n        # placeholder: use porcupine or snowboy\n        pass\n    def listen(self) -> bool:\n        # pretend we heard 'Hey Nia'\n        return False\n",
    "niaeleria/voice/stt.py": "\"\"\"Speech-to-text\"\"\"\nimport speech_recognition as sr\n\nclass STT:\n    def __init__(self):\n        self.recognizer = sr.Recognizer()\n        self.mic = sr.Microphone()\n\n    def listen_once(self) -> str:\n        with self.mic as source:\n            audio = self.recognizer.listen(source)\n        try:\n            return self.recognizer.recognize_google(audio)\n        except sr.UnknownValueError:\n            return \"\"\n",
    "niaeleria/voice/tts.py": "\"\"\"Text-to-speech (edge-tts)\"\"\"\nimport edge_tts\nimport asyncio\n\nclass TTS:\n    async def say(self, text: str, voice: str = \"en-US-JennyNeural\"):\n        communicate = edge_tts.Communicate(text, voice)\n        await communicate.save(\"output.mp3\")\n        # then play (stub)\n",

    # Automation
    "niaeleria/automation/__init__.py": "# Automation & scheduling\n",
    "niaeleria/automation/scheduler.py": "\"\"\"Reminders, recurring tasks, morning briefing\"\"\"\nimport schedule\nimport time\nimport threading\n\nclass Scheduler:\n    def __init__(self):\n        self.jobs = []\n\n    def add_reminder(self, time_str: str, message: str):\n        schedule.every().day.at(time_str).do(lambda: print(f\"REMINDER: {message}\"))\n\n    def start(self):\n        def run_loop():\n            while True:\n                schedule.run_pending()\n                time.sleep(1)\n        threading.Thread(target=run_loop, daemon=True).start()\n",
    "niaeleria/automation/home_control.py": "\"\"\"MQTT-based smart home commands\"\"\"\nimport paho.mqtt.client as mqtt\nfrom ..config import config\n\nclass HomeControl:\n    def __init__(self):\n        self.client = mqtt.Client()\n        self.client.connect(config.mqtt_broker, config.mqtt_port)\n\n    def turn_on_light(self, room: str):\n        self.client.publish(f\"home/{room}/light\", \"ON\")\n\n    def set_temperature(self, room: str, temp: float):\n        self.client.publish(f\"home/{room}/thermostat\", str(temp))\n",
    "niaeleria/automation/briefing.py": "\"\"\"Morning briefing composer\"\"\"\nfrom datetime import datetime\n\nclass Briefing:\n    def compose(self) -> str:\n        return f\"Good morning! Today is {datetime.now().strftime('%A')}. Weather: sunny, 22°C. No urgent alerts.\"\n",

    # Sync
    "niaeleria/sync/__init__.py": "# Cross-device sync\n",
    "niaeleria/sync/mqtt_sync.py": "\"\"\"Cross-device MQTT broker/agent\"\"\"\nimport paho.mqtt.client as mqtt\nimport json\n\nclass MQTTSync:\n    def __init__(self, broker, port):\n        self.client = mqtt.Client()\n        self.client.connect(broker, port)\n        self.client.subscribe(\"nia/state\")\n\n    def publish_state(self, state: dict):\n        self.client.publish(\"nia/state\", json.dumps(state))\n",

    # API
    "niaeleria/api/__init__.py": "# FastAPI server\n",
    "niaeleria/api/server.py": "\"\"\"FastAPI + WebSocket server\"\"\"\nfrom fastapi import FastAPI, WebSocket\nfrom fastapi.staticfiles import StaticFiles\nfrom .routes import chat, security, memory, automation, selfmod\n\napp = FastAPI(title=\"Niaeleria API\")\n\napp.include_router(chat.router, prefix=\"/chat\", tags=[\"chat\"])\napp.include_router(security.router, prefix=\"/security\", tags=[\"security\"])\napp.include_router(memory.router, prefix=\"/memory\", tags=[\"memory\"])\napp.include_router(automation.router, prefix=\"/automation\", tags=[\"automation\"])\napp.include_router(selfmod.router, prefix=\"/selfmod\", tags=[\"selfmod\"])\n\n# serve static web UI\napp.mount(\"/\", StaticFiles(directory=\"niaeleria/api/static\", html=True), name=\"static\")\n\n@app.websocket(\"/ws\")\nasync def websocket_endpoint(websocket: WebSocket):\n    await websocket.accept()\n    while True:\n        data = await websocket.receive_text()\n        await websocket.send_text(f\"Echo: {data}\")\n",
    "niaeleria/api/routes/__init__.py": "# API route modules\n",
    "niaeleria/api/routes/chat.py": "from fastapi import APIRouter\n\nrouter = APIRouter()\n\n@router.post(\"/send\")\nasync def send_message(message: str):\n    # integrate with Brain\n    return {\"response\": \"Hello from Nia!\"}\n",
    "niaeleria/api/routes/security.py": "from fastapi import APIRouter\nfrom ...security.kill_switch import KillSwitch\n\nrouter = APIRouter()\n\n@router.get(\"/status\")\nasync def security_status():\n    ks = KillSwitch()\n    return {\"kill_switch\": ks.is_triggered()}\n",
    "niaeleria/api/routes/memory.py": "from fastapi import APIRouter\nfrom ...core.memory import Memory\n\nrouter = APIRouter()\nmemory = Memory()\n\n@router.get(\"/recall\")\nasync def recall(query: str):\n    return {\"memories\": memory.recall_similar(query)}\n",
    "niaeleria/api/routes/automation.py": "from fastapi import APIRouter\n\nrouter = APIRouter()\n\n@router.post(\"/reminder\")\nasync def set_reminder(time: str, message: str):\n    # use scheduler\n    return {\"status\": \"reminder set\"}\n",
    "niaeleria/api/routes/selfmod.py": "from fastapi import APIRouter\nfrom ...security.self_modifier import SelfModifier\n\nrouter = APIRouter()\nmodifier = SelfModifier()\n\n@router.post(\"/replace\")\nasync def replace_file(path: str, content: str):\n    success = modifier.replace_file(path, content)\n    return {\"success\": success}\n",

    # Web UI static files
    "niaeleria/api/static/index.html": """<!DOCTYPE html>
<html>
<head><title>Niaeleria</title><link rel="stylesheet" href="/style.css"></head>
<body>
    <div id="app">
        <h1>Niaeleria Dashboard</h1>
        <button onclick="fetch('/security/status')">Check Security</button>
    </div>
    <script src="/app.js"></script>
</body>
</html>""",
    "niaeleria/api/static/app.js": "console.log('Niaeleria UI ready');",
    "niaeleria/api/static/style.css": "body { font-family: sans-serif; background: #f0f0f0; }",

    # Tray
    "niaeleria/tray/__init__.py": "# System tray\n",
    "niaeleria/tray/tray_app.py": "\"\"\"System tray (pystray)\"\"\"\nimport pystray\nfrom PIL import Image\n\nclass TrayApp:\n    def __init__(self):\n        self.icon = pystray.Icon(\"niaeleria\", Image.new(\"RGB\", (64,64), color=\"blue\"), \"Niaeleria\")\n        self.icon.menu = pystray.Menu(\n            pystray.MenuItem(\"Open API\", lambda: None),\n            pystray.MenuItem(\"Stop\", self.stop)\n        )\n\n    def run(self):\n        self.icon.run()\n\n    def stop(self):\n        self.icon.stop()\n",

    # Tests
    "tests/test_security.py": "def test_kill_switch(): pass\n",
    "tests/test_memory.py": "def test_memory(): pass\n",
    "tests/test_brain.py": "def test_brain(): pass\n",
    "tests/test_guard.py": "def test_guard(): pass\n",
}

# ------------------------------------------------------------
#  Helper to create directories and files
# ------------------------------------------------------------

def create_structure():
    # Create root project directory
    PROJECT_ROOT.mkdir(exist_ok=True)

    # Create data and flags (gitignored, but needed)
    (PROJECT_ROOT / "data").mkdir(exist_ok=True)
    (PROJECT_ROOT / "flags").mkdir(exist_ok=True)
    (PROJECT_ROOT / "data/backups").mkdir(parents=True, exist_ok=True)

    # Create all files with their content
    for rel_path, content in CONTENT.items():
        file_path = PROJECT_ROOT / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        print(f"Created: {file_path}")

    # Make bootstrap.sh executable
    bootstrap = PROJECT_ROOT / "bootstrap.sh"
    if bootstrap.exists():
        st = os.stat(bootstrap)
        os.chmod(bootstrap, st.st_mode | stat.S_IEXEC)

    print("\n✅ Niaeleria project scaffold created successfully!")
    print(f"   Location: {PROJECT_ROOT}")
    print("   Next steps: cd niaeleria ; cp .env.example .env ; bash bootstrap.sh")

if __name__ == "__main__":
    create_structure()