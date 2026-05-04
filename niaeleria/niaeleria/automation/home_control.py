# ════════════════════════════════════════════════════════════════════
# home_control.py
# Save as: niaeleria/automation/home_control.py
# ════════════════════════════════════════════════════════════════════

import json
import logging
from datetime import datetime
from niaeleria.security.audit import log_event

_hc_log = logging.getLogger("nia.home_control")


class HomeController:
    """
    Smart home controller via MQTT.
    Translates natural-language device commands into MQTT messages.
    Supports lights, switches, thermostats, locks, scenes.

    "Dad, your home does what you say — I make sure of it." — Nia
    """

    # Device registry: name → MQTT topic
    # Dad can extend this via the API or config
    _devices: dict[str, str] = {
        "living_room_light": "home/lights/living_room",
        "bedroom_light":     "home/lights/bedroom",
        "front_door_lock":   "home/locks/front_door",
        "thermostat":        "home/climate/thermostat",
        "tv":                "home/appliances/tv",
        "all_lights":        "home/lights/all",
    }

    def __init__(self, mqtt_client) -> None:
        self._mqtt = mqtt_client

    def command(self, device: str, action: str, value: str | int | float | None = None) -> bool:
        """
        Send a command to a smart home device.
        Returns True if published successfully.
        """
        from niaeleria.security.kill_switch import assert_alive
        assert_alive()

        device_key = device.lower().replace(" ", "_")
        topic = self._devices.get(device_key)

        if not topic:
            _hc_log.warning("Dad, I don't know a device called '%s'. Known: %s",
                            device, list(self._devices.keys()))
            return False

        payload = json.dumps({
            "action": action,
            "value": value,
            "source": "nia_voice",
            "ts": datetime.now().isoformat(),
        })

        success = self._mqtt.publish(topic, payload)
        if success:
            _hc_log.info("Dad, sent '%s' → %s (topic: %s)", action, device, topic)
            log_event("nia.home", "device_command", target=device,
                      details={"action": action, "value": value, "topic": topic},
                      approved=True)
        return success

    def parse_natural_language(self, command: str) -> dict | None:
        """
        Parse natural-language home commands.
        e.g. "turn off the living room light" → {device, action, value}
        Simple rule-based parser; the LLM brain handles complex variants.
        """
        cmd = command.lower()
        action = None
        device = None
        value = None

        # Action detection
        if any(w in cmd for w in ("turn on", "switch on", "enable", "open")):
            action = "on"
        elif any(w in cmd for w in ("turn off", "switch off", "disable", "close")):
            action = "off"
        elif "dim" in cmd or "set" in cmd:
            action = "set"
            import re
            match = re.search(r"(\d+)\s*(?:percent|%)?", cmd)
            value = int(match.group(1)) if match else 50
        elif "lock" in cmd:
            action = "lock"
        elif "unlock" in cmd:
            action = "unlock"
        elif any(w in cmd for w in ("temperature", "degrees", "celsius", "heat", "cool")):
            action = "set_temperature"
            import re
            match = re.search(r"(\d+)\s*(?:degrees?|°|c|f)?", cmd)
            value = int(match.group(1)) if match else None

        # Device detection
        for device_key in self._devices:
            if device_key.replace("_", " ") in cmd:
                device = device_key
                break

        if not device:
            if "light" in cmd:
                device = "all_lights"
            elif "door" in cmd or "lock" in cmd:
                device = "front_door_lock"
            elif "thermostat" in cmd or "temperature" in cmd:
                device = "thermostat"
            elif "tv" in cmd or "television" in cmd:
                device = "tv"

        if action and device:
            return {"device": device, "action": action, "value": value}

        return None

    def register_device(self, name: str, mqtt_topic: str) -> None:
        """Dad can add new devices at runtime."""
        self._devices[name.lower().replace(" ", "_")] = mqtt_topic
        _hc_log.info("Dad, I've registered new device '%s' → %s", name, mqtt_topic)

