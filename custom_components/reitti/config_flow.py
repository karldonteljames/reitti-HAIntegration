import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import DOMAIN, CONF_URL, CONF_DEVICE, CONF_PORT

class ReittiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Initial config step for user input."""
        errors = {}

        if user_input is not None:
            return self.async_create_entry(
                title="Reitti Integration",
                data={
                    CONF_URL: user_input[CONF_URL],
                    "api_key": user_input["api_key"],
                    CONF_DEVICE: user_input[CONF_DEVICE],
                    CONF_PORT: user_input.get(CONF_PORT, 8080),
                },
                options={
                    "interval_seconds": user_input.get("interval_seconds", 30),
                    "enable_debug_logging": user_input.get("enable_debug_logging", False),
                },
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_URL, default="http://reitti", description="Reitti server URL/Instance"): str,
                vol.Optional(CONF_PORT, default=8080, description="Server port (default 8080)"): int,
                vol.Required("api_key", description="Your Reitti API token"): str,
                vol.Required(CONF_DEVICE, description="Device you want to track"): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="device_tracker")
                ),
                vol.Optional("interval_seconds", default=30, description="No movement push interval (seconds)"): int,
                vol.Optional("enable_debug_logging", default=False, description="Enable debug logging"): bool,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_options(self, user_input=None):
        """Options flow to adjust interval and logging."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(
                    "interval_seconds",
                    default=self.options.get("interval_seconds", 30),
                    description="Push interval in seconds"
                ): int,
                vol.Required(
                    "enable_debug_logging",
                    default=self.options.get("enable_debug_logging", False),
                    description="Enable debug logging"
                ): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
