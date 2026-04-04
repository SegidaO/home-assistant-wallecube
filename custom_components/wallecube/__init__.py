import logging

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry

from .mqtt_client import WalleCubeMqttClient
from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WalleCube from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    mqtt_client = WalleCubeMqttClient(hass, entry.data)
    await mqtt_client.async_connect()
    hass.data[DOMAIN][entry.entry_id] = mqtt_client

    async def send_magic_packet(call: ServiceCall) -> None:
        """Handle the send_magic_packet service."""
        mac_address = call.data.get("mac_address")
        _LOGGER.debug("send_magic_packet request received. mac_address: %s", mac_address)

        try:
            res = await mqtt_client.async_send_magic_packet(mac_address)
            _LOGGER.debug("send_magic_packet mqtt_client: %s", mqtt_client)

            if res:
                hass.bus.async_fire(
                    "wallecube.magic_packet_sent",
                    {"mac": mac_address, "status": "success"},
                )
            else:
                hass.bus.async_fire(
                    "wallecube.magic_packet_sent",
                    {
                        "mac": mac_address,
                        "status": "error",
                        "message": "mac address format not allowed",
                    },
                )
        except Exception as err:  # noqa: BLE001
            hass.bus.async_fire(
                "wallecube.magic_packet_sent",
                {"mac": mac_address, "status": "error", "message": str(err)},
            )

    # Регистрируем сервис один раз на интеграцию
    if not hass.services.has_service(DOMAIN, "send_magic_packet"):
        hass.services.async_register(DOMAIN, "send_magic_packet", send_magic_packet)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    mqtt_client: WalleCubeMqttClient | None = hass.data[DOMAIN].pop(entry.entry_id, None)

    if mqtt_client is not None:
        await mqtt_client.async_disconnect()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Если больше нет устройств — убираем сервис
    if not hass.data[DOMAIN]:
        if hass.services.has_service(DOMAIN, "send_magic_packet"):
            hass.services.async_remove(DOMAIN, "send_magic_packet")

    return unload_ok