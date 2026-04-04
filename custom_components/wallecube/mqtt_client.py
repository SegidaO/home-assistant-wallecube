import logging
import re
from typing import Any, Dict

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.components import mqtt
from homeassistant.components.mqtt.models import ReceiveMessage

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class WalleCubeMqttClient:
    """MQTT client for Walle Cube using Home Assistant MQTT integration."""

    def __init__(self, hass: HomeAssistant, config: Dict[str, Any]) -> None:
        self.hass = hass
        self.device_id: str = config["device_id"]
        self.password: str = config["password"]  # оставим на будущее, если понадобится аутентификация на стороне брокера
        self.topic_up: str = f"ups/up/{self.device_id}"
        self.topic_dn: str = f"ups/dn/{self.device_id}"
        self._unsub_up = None

    async def async_connect(self) -> None:
        """Подключиться к MQTT через встроенную интеграцию Home Assistant."""

        @callback
        def _message_received(msg: ReceiveMessage) -> None:
            self._handle_message(msg)

        _LOGGER.info("Subscribing to MQTT topic: %s", self.topic_up)
        self._unsub_up = await mqtt.async_subscribe(
            self.hass,
            self.topic_up,
            _message_received,
            qos=0,
        )

    async def async_disconnect(self) -> None:
        """Отписаться от MQTT-топика."""
        if self._unsub_up is not None:
            _LOGGER.info("Unsubscribing from MQTT topic: %s", self.topic_up)
            self._unsub_up()
            self._unsub_up = None

    @callback
    def _handle_message(self, message: ReceiveMessage) -> None:
        """Обработка входящих MQTT-сообщений."""
        if message.topic != self.topic_up:
            _LOGGER.debug("MQTT Received from unexpected topic: %s", message.topic)
            return

        _p = message.payload
        if isinstance(_p, str):
            # На всякий случай, если брокер прислал строку
            _p = _p.encode()

        _LOGGER.debug("MQTT Payload raw: %s", _p.hex())
        data: Dict[str, Any] = {}

        def convert2int(byte_data: bytes) -> int:
            return int.from_bytes(byte_data, byteorder="big")

        if len(_p) > 2 and _p[1] == 0x01:
            # High and low swaps
            p = _p[::-1]
            data["acOK"] = p[0] in [0x04, 0x05]
            data["charging"] = p[1] == 0x81
            data["totalConsumption"] = convert2int(p[2:6]) / 1000000  # kWh
            data["leftSecs"] = convert2int(p[6:8]) / 60  # min
            data["batteryCapacity"] = convert2int(p[8:10]) / 10  # %
            data["currentOut"] = convert2int(p[10:12]) / 1000  # A
            data["voltageOut"] = convert2int(p[12:14]) / 1000  # V
            data["pwrOut"] = data["voltageOut"] * data["currentOut"]  # W

            if data["charging"]:
                data["chargingCurrent"] = convert2int(p[14:16]) / 1000
            elif len(p) > 23 and p[23] not in [0x01, 0x02]:
                data["chargingCurrent"] = -convert2int(p[14:16]) / 1000

            data["batteryVoltage"] = convert2int(p[16:18]) / 1000  # V
            data["currentInput"] = convert2int(p[18:20]) / 1000  # A
            data["voltageInput"] = convert2int(p[20:22]) / 1000  # V
            if len(p) > 22:
                data["batteryTemperature"] = int(p[22])  # ℃

        elif len(_p) > 14 and _p[1] == 0x02:
            data["ipAddress"] = (
                f"{int(_p[12])}."
                f"{int(_p[13])}."
                f"{int(_p[14])}."
                f"{int(_p[7])}"
            )

        _LOGGER.debug("MQTT Payload decoded: %s", data)

        for sensor_name, sensor_value in data.items():
            async_dispatcher_send(
                self.hass,
                f"{DOMAIN}_{self.device_id}_{sensor_name}",
                sensor_value,
            )

    async def async_publish(self, topic: str, msg: bytes | str) -> None:
        """Публикация сообщения в MQTT через HA."""
        _LOGGER.debug("Publishing to topic %s: %s", topic, msg)
        await mqtt.async_publish(
            self.hass,
            topic,
            msg,
            qos=0,
            retain=False,
        )

    async def async_send_magic_packet(self, mac_address: str) -> bool:
        """Отправить magic packet на устройство через MQTT."""
        pattern = r"^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$"
        if not re.match(pattern, mac_address):
            _LOGGER.debug(
                "MQTT Client: Mac address %s format not allowed.", mac_address
            )
            return False

        _LOGGER.debug(
            "MQTT Client: Ready to send_magic_packet to %s.", mac_address
        )
        payload_hex = "5103000600" + mac_address.replace(":", "").upper()
        payload = bytes.fromhex(payload_hex)
        await self.async_publish(self.topic_dn, payload)
        return True