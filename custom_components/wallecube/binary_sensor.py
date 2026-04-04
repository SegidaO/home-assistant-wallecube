import logging

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, DEVICE_MODEL, MANUFACTURER, BINARY_SENSOR_TYPES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up WalleCube binary sensors from a config entry."""
    device_id = entry.data["device_id"]
    sensors: list[WalleCubeBinarySensor] = []

    for sensor_type, cfg in BINARY_SENSOR_TYPES.items():
        sensors.append(WalleCubeBinarySensor(device_id, sensor_type, cfg))

    async_add_entities(sensors)


class WalleCubeBinarySensor(BinarySensorEntity):
    """Representation of a WalleCube binary sensor."""

    def __init__(self, device_id, sensor_id, config) -> None:
        self._device_id = device_id
        self._sensor_id = sensor_id
        self._config = config
        self._is_on = False
        self._attr_name = self._config["name"]

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self._device_id}_{self._sensor_id}"

    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": DEVICE_MODEL,
            "manufacturer": MANUFACTURER,
            "sw_version": "0.0.1",
        }

    @property
    def has_entity_name(self) -> bool:
        """Indicate that entity has name defined."""
        return True

    @property
    def device_class(self) -> BinarySensorDeviceClass:
        """Return entity device class."""
        return self._config["device_class"]

    @property
    def icon(self) -> str:
        """Return icon."""
        return self._config["icon_on"] if self._is_on else self._config["icon_off"]

    @property
    def is_on(self) -> bool:
        return self._is_on

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                self.unique_id,
                self._async_update_state,
            )
        )

    @callback
    def _async_update_state(self, new_state: bool) -> None:
        """Handle state update from dispatcher."""
        self._is_on = new_state
        self.async_write_ha_state()