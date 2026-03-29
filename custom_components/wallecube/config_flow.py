from homeassistant.config_entries import ConfigFlow, OptionsFlow, CONF_DEVICE_ID, CONF_PASSWORD
from homeassistant.core import callback
from homeassistant.const import CONF_HOST, CONF_PORT
import voluptuous as vol

import asyncio
import logging

from paho.mqtt.client import Client as MQTTClient, CONNACK_ACCEPTED
from .const import DOMAIN, MQTT_BROKER, MQTT_PORT

_LOGGER = logging.getLogger(__name__)


class WalleCubeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WalleCube."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            password = user_input[CONF_PASSWORD]

            result = await self._verify_mqtt_credentials(device_id, password)
            if result['success']:
                _LOGGER.debug("MQTT verification successful")
                return self.async_create_entry(
                    title=f"WalleCube {device_id}",
                    data=user_input
                )
            else:
                errors["base"] = f"error_code_{result['error_code']}"
                _LOGGER.warning("MQTT verification failed: %s", result['error_message'])

        return self.async_show_form(
            step_id="user",
            data_schema=self._get_schema(),
            errors=errors,
        )

    def _get_schema(self):
        """Return the schema for the user input."""
        return vol.Schema({
            vol.Required(CONF_DEVICE_ID): str,
            vol.Required(CONF_PASSWORD): str,
        })

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return WalleCubeOptionsFlow(config_entry)

    async def _verify_mqtt_credentials(self, username, password, timeout=30):
        """Verify MQTT credentials asynchronously."""
        result = {"success": False, "error_code": None, "error_message": ""}

        loop = asyncio.get_event_loop()
        event = asyncio.Event()

        def on_connect(client, userdata, flags, rc):
            if rc == CONNACK_ACCEPTED:
                result["success"] = True
                result["error_message"] = "Connection successful"
            else:
                result["error_code"] = rc
                result["error_message"] = f"Connection failed, error code: {rc} (possible username/password error)"
            loop.call_soon_threadsafe(event.set)

        def on_disconnect(client, userdata, rc):
            if rc != 0:
                result["error_code"] = rc
                result["error_message"] = f"Disconnected unexpectedly, error code: {rc}"
                loop.call_soon_threadsafe(event.set)

        client_id = f'{username}_{int(time.time())}'
        client = MQTTClient(client_id)
        client.username_pw_set(username, password)
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect

        try:
            client.loop_start()
            client.connect_async(MQTT_BROKER, MQTT_PORT)

            await asyncio.wait_for(event.wait(), timeout=timeout)

        except asyncio.TimeoutError:
            result["success"] = False
            result["error_message"] = "Connection timeout, possible network issue or incorrect credentials"
        except Exception as e:
            result["success"] = False
            result["error_message"] = f"Unexpected error: {str(e)}"
        finally:
            client.loop_stop()
            client.disconnect()

        return result



class WalleCubeOptionsFlow(OptionsFlow):
    """WalleCube options flow."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
        )
