import logging

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, DEVICE_MODEL, MANUFACTURER, SENSOR_TYPES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up WalleCube sensors from a config entry."""
    device_id = entry.data["device_id"]
    sensors: list[WalleCubeSensor] = []

    for sensor_type, cfg in SENSOR_TYPES.items():
        sensors.append(WalleCubeSensor(device_id, sensor_type, cfg))

    async_add_entities(sensors)


class WalleCubeSensor(SensorEntity):
    """Representation of a WalleCube sensor."""

    def __init__(self, device_id, sensor_id, config) -> None:
        self._device_id = device_id
        self._sensor_id = sensor_id
        self._config = config
        self._state = None
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
    def state_class(self) -> SensorStateClass:
        """Return the type of state class."""
        return self._config["state_class"]

    @property
    def device_class(self) -> SensorDeviceClass:
        """Return entity device class."""
        return self._config["device_class"]

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the native unit."""
        return self._config["unit"]

    @property
    def icon(self) -> str:
        """Return icon."""
        if self._sensor_id == "batteryCapacity":
            if self._state is None:
                return f"{self._config['icon']}-unknown"
            battery_life = max(10, min(int(round(self._state / 10) * 10), 100))
            if battery_life >= 100:
                return self._config["icon"]
            return f"{self._config['icon']}-{battery_life}"
        return self._config["icon"]

    @property
    def native_value(self):
        return self._state

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
    def _async_update_state(self, new_state) -> None:
        """Handle state update from dispatcher."""
        self._state = new_state
        self.async_write_ha_state()