import logging
import asyncio
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_PASSWORD,
)
from homeassistant.core import callback
from homeassistant.components import mqtt
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN

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
        Проверка MQTT-доступа через встроенную интеграцию Home Assistant.

        Механизм:
        1. Подписываемся на временный топик.
        2. Публикуем тестовое сообщение с указанными username/password.
        3. Если брокер принимает — сообщение вернётся.
        4. Если нет — будет timeout.
        """

        test_topic = f"wallecube/test/{username}"
        test_payload = f"auth_test:{username}:{password}"

        event = asyncio.Event()
        result = {"success": False, "error": "auth_failed", "message": ""}

        @callback
        def _on_message(msg):
            if msg.payload.decode() == test_payload:
                result["success"] = True
                result["error"] = None
                result["message"] = "MQTT authentication OK"
                event.set()

        # Подписка
        unsub = await mqtt.async_subscribe(
            self.hass,
            test_topic,
            _on_message,
            qos=0
        )

        try:
            # Публикация
            await mqtt.async_publish(
                self.hass,
                test_topic,
                test_payload,
                qos=0,
                retain=False,
                username=username,
                password=password,
            )

            await asyncio.wait_for(event.wait(), timeout=timeout)

        except asyncio.TimeoutError:
            result["message"] = "MQTT authentication timeout"
        except Exception as e:
            result["message"] = f"Unexpected error: {e}"
        finally:
            unsub()

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