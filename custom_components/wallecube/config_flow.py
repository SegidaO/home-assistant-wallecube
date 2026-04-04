import asyncio
import logging
import time
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.const import CONF_DEVICE_ID, CONF_PASSWORD

from paho.mqtt.client import Client as MQTTClient, CONNACK_ACCEPTED

from .const import DOMAIN, MQTT_BROKER, MQTT_PORT

_LOGGER = logging.getLogger(__name__)


class WalleCubeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WalleCube."""

    VERSION = 2

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            password = user_input[CONF_PASSWORD]

            result = await self._verify_mqtt_credentials(device_id, password)

            if result["success"]:
                _LOGGER.debug("MQTT verification successful")
                return self.async_create_entry(
                    title=f"WalleCube {device_id}",
                    data=user_input
                )
            else:
                errors["base"] = result["error"]
                _LOGGER.warning("MQTT verification failed: %s", result["message"])

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

    async def _verify_mqtt_credentials(self, username: str, password: str, timeout: int = 10):
        """
        Проверка MQTT логина/пароля через paho-mqtt.
        Это разрешено, так как config_flow выполняется один раз и не создаёт постоянных потоков.
        """

        result = {"success": False, "error": "auth_failed", "message": ""}
        event = asyncio.Event()

        loop = asyncio.get_running_loop()

        def on_connect(client, userdata, flags, rc):
            if rc == CONNACK_ACCEPTED:
                result["success"] = True
                result["error"] = None
                result["message"] = "MQTT authentication OK"
            else:
                result["error"] = f"error_code_{rc}"
                result["message"] = f"MQTT connection failed, code {rc}"

            loop.call_soon_threadsafe(event.set)

        def on_disconnect(client, userdata, rc):
            if rc != 0:
                result["error"] = f"error_code_{rc}"
                result["message"] = f"Disconnected unexpectedly, code {rc}"
                loop.call_soon_threadsafe(event.set)

        client_id = f"{username}_{int(time.time())}"
        client = MQTTClient(client_id)
        client.username_pw_set(username, password)
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect

        try:
            client.connect_async(MQTT_BROKER, MQTT_PORT)
            client.loop_start()

            await asyncio.wait_for(event.wait(), timeout=timeout)

        except asyncio.TimeoutError:
            result["success"] = False
            result["error"] = "timeout"
            result["message"] = "MQTT authentication timeout"
        except Exception as e:
            result["success"] = False
            result["error"] = "unexpected"
            result["message"] = f"Unexpected error: {e}"
        finally:
            client.loop_stop()
            client.disconnect()

        return result


class WalleCubeOptionsFlow(OptionsFlow):
    """WalleCube options flow."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
        )