"niaeleria/sync/mqtt_sync.py      — Cross-device MQTT broker/agent"

from __future__ import annotations
# ════════════════════════════════════════════════════════════════════
# mqtt_sync.py
# Save as: niaeleria/sync/mqtt_sync.py
# ════════════════════════════════════════════════════════════════════

import json
import logging
import threading
import time
from typing import Callable, Optional

from niaeleria.config import (
    MQTT_HOST, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD,
    MQTT_TLS, MQTT_TOPIC_PREFIX, is_killed,
)
from niaeleria.security.kill_switch import assert_alive
from niaeleria.security.audit import log_event

log = logging.getLogger("nia.mqtt")


class MQTTSync:
    """
    Cross-device synchronisation agent via MQTT (QoS 1).
    Broadcasts firewall blocks, memory updates, and status across all Dad's devices.
    Uses Mosquitto broker (local or remote).

    "Dad, all your devices stay in sync — one block, blocked everywhere." — Nia
    """

    _client = None
    _connected = False
    _subscriptions: dict[str, Callable] = {}
    _instance: Optional["MQTTSync"] = None

    def __init__(self) -> None:
        MQTTSync._instance = self
        self._client = self._create_client()

    def _create_client(self):
        try:
            import paho.mqtt.client as mqtt

            client = mqtt.Client(client_id="niaeleria-agent", clean_session=True)

            if MQTT_USERNAME:
                client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

            if MQTT_TLS:
                client.tls_set()

            client.on_connect = self._on_connect
            client.on_disconnect = self._on_disconnect
            client.on_message = self._on_message

            return client
        except ImportError:
            log.error("paho-mqtt not installed. Dad, run: pip install paho-mqtt")
            return None

    def connect(self) -> bool:
        if not self._client:
            return False
        try:
            self._client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
            self._client.loop_start()
            # Wait for connection
            for _ in range(20):
                if MQTTSync._connected:
                    return True
                time.sleep(0.5)
            log.warning("Dad, MQTT connection timed out. Is the broker running?")
            return False
        except Exception as exc:
            log.warning("Dad, MQTT broker unavailable (%s) — cross-device sync disabled.", exc)
            return False

    def disconnect(self) -> None:
        if self._client and MQTTSync._connected:
            self._client.loop_stop()
            self._client.disconnect()

    def _on_connect(self, client, userdata, flags, rc) -> None:
        MQTTSync._connected = (rc == 0)
        if rc == 0:
            log.info("Dad, I'm connected to the MQTT broker. Cross-device sync is active.")
            # Re-subscribe to all topics
            for topic in self._subscriptions:
                client.subscribe(topic, qos=1)
        else:
            log.warning("MQTT connect failed, code %d", rc)

    def _on_disconnect(self, client, userdata, rc) -> None:
        MQTTSync._connected = False
        if rc != 0:
            log.warning("Dad, MQTT disconnected unexpectedly (rc=%d). Reconnecting...", rc)

    def _on_message(self, client, userdata, msg) -> None:
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode())
        except Exception:
            payload = msg.payload.decode()

        handler = self._subscriptions.get(topic)
        if handler:
            try:
                handler(topic, payload)
            except Exception as exc:
                log.error("MQTT message handler error: %s", exc)

    def subscribe(self, topic: str, handler: Callable) -> None:
        """Subscribe to an MQTT topic with a message handler."""
        full_topic = f"{MQTT_TOPIC_PREFIX}/{topic}"
        self._subscriptions[full_topic] = handler
        if self._client and MQTTSync._connected:
            self._client.subscribe(full_topic, qos=1)
        log.debug("Subscribed to MQTT topic: %s", full_topic)

    def publish(self, topic: str, payload: dict | str, qos: int = 1) -> bool:
        """Publish a message. Returns True on success."""
        if not self._client or not MQTTSync._connected:
            log.debug("MQTT publish skipped — not connected: %s", topic)
            return False

        full_topic = f"{MQTT_TOPIC_PREFIX}/{topic}"
        data = json.dumps(payload) if isinstance(payload, dict) else str(payload)

        try:
            result = self._client.publish(full_topic, data, qos=qos)
            return result.rc == 0
        except Exception as exc:
            log.error("MQTT publish error: %s", exc)
            return False

    @classmethod
    def broadcast_block(cls, ip: str, reason: str) -> None:
        """Broadcast a firewall block to all connected devices."""
        if cls._instance:
            cls._instance.publish(
                "security/block",
                {"ip": ip, "reason": reason, "source": "niaeleria"}
            )
            log.info("Dad, I've broadcast block of %s to all devices.", ip)
            log_event("nia.mqtt", "broadcast_block", target=ip,
                      details={"reason": reason}, approved=True)

    def setup_firewall_sync(self) -> None:
        """
        Listen for block broadcasts from other devices and apply them locally.
        This is how one device's discovery protects all of Dad's devices.
        """
        from niaeleria.guard.cyber_guard import Firewall

        def handle_block(topic: str, payload: dict) -> None:
            ip = payload.get("ip")
            reason = payload.get("reason", "cross-device sync")
            if ip:
                log.info("Dad, applying block from remote device: %s (%s)", ip, reason)
                Firewall.block_ip(ip, reason=f"[sync] {reason}", approved=True)

        self.subscribe("security/block", handle_block)
        log.info("Dad, cross-device firewall sync is active.")


