import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import DOMAIN, CONF_URL, CONF_DEVICE, CONF_PORT

class ReittiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2  # bump version for changes

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            # Only URL, port, and API token are in data; everything else in options
            return self.async_create_entry(
                title="Reitti Integration",
                data={
                    CONF_URL: user_input[CONF_URL],
                    "api_key": user_input["api_key"],
                    CONF_PORT: user_input.get(CONF_PORT, 8080),
                },
                options={
                    CONF_DEVICE: user_input[CONF_DEVICE],
                    "interval_seconds": user_input.get("interval_seconds", 30),
                    "enable_debug_logging": user_input.get("enable_debug_logging", False),
                    "enable_push": user_input.get("enable_push", True),
                },
            )

        schema = vol.Schema({
            vol.Required(CONF_URL, default="http://reitti", description="Reitti Server URL"): str,
            vol.Optional(CONF_PORT, default=8080, description="Server Port"): int,
            vol.Required("api_key", description="Reitti API Token"): str,
            vol.Required(CONF_DEVICE, description="Device to Track"): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="device_tracker")
            ),
            vol.Optional("interval_seconds", default=60, description="Push Interval (seconds)"): int,
            vol.Optional("enable_debug_logging", default=False, description="Enable Debug Logging"): bool,
            vol.Optional("enable_push", default=True, description="Enable Automatic Push"): bool,
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_options(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema({
            vol.Required(
                CONF_DEVICE,
                default=self.options.get(CONF_DEVICE),
                description="Device to Track"
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="device_tracker")),
            vol.Required(
                "interval_seconds",
                default=self.options.get("interval_seconds", 30),
                description="Push Interval (seconds)"
            ): int,
            vol.Required(
                "enable_debug_logging",
                default=self.options.get("enable_debug_logging", False),
                description="Enable Debug Logging"
            ): bool,
            vol.Required(
                "enable_push",
                default=self.options.get("enable_push", True),
                description="Enable Automatic Push"
            ): bool,
        })

        return self.async_show_form(step_id="init", data_schema=schema)
