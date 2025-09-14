# File: custom_components/reitti/config_flow.py
# Date: 2025-09-14

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import DOMAIN, CONF_URL, CONF_DEVICE, CONF_PORT

class ReittiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Initial configuration step for user input."""
        errors = {}

        if user_input is not None:
            return self.async_create_entry(
                title=user_input.get("friendly_name", "Reitti Integration"),
                data={
                    CONF_URL: user_input[CONF_URL],
                    "api_key": user_input["api_key"],
                    CONF_DEVICE: user_input[CONF_DEVICE],
                    CONF_PORT: user_input.get(CONF_PORT, 8080),
                },
                options={
                    "interval_seconds": user_input.get("interval_seconds", 30),
                    "enable_debug_logging": user_input.get("enable_debug_logging", False),
                    "enable_push": user_input.get("enable_push", True),
                    "friendly_name": user_input.get("friendly_name", "Reitti Integration"),
                },
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_URL, default="http://reitti"): str,
                vol.Optional(CONF_PORT, default=8080): int,
                vol.Required("api_key"): str,
                vol.Required(CONF_DEVICE): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="device_tracker")
                ),
                vol.Optional("interval_seconds", default=30): int,
                vol.Optional("enable_debug_logging", default=False): bool,
                vol.Optional("enable_push", default=True): bool,
                vol.Optional("friendly_name", default="Reitti Integration"): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_options(self, user_input=None):
        """Options flow to adjust settings after integration is added."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_DEVICE,
                    default=self.options.get(CONF_DEVICE),
                    description="Device to track"
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="device_tracker")
                ),
                vol.Required(
                    "Enable push updates",
                    default=self.options.get("enable_push", True),
                    description="Enable automatic push updates"
                ): bool,
                vol.Required(
                    "Interval seconds",
                    default=self.options.get("interval_seconds", 30),
                    description="Push interval in seconds"
                ): int,
                vol.Required(
                    "Enable debug logging",
                    default=self.options.get("enable_debug_logging", False),
                    description="Enable debug logging"
                ): bool,
                vol.Required(
                    "friendly_name",
                    default=self.options.get("friendly_name", "Reitti Integration"),
                    description="Custom name for this Reitti instance/device"
                ): str,
            }
        )
        return self.async_show_form(step_id="options", data_schema=schema)
