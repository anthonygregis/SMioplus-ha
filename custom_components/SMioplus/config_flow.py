from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import voluptuous as vol

from . import DOMAIN

class SMioplusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        if user_input is not None:
            # TODO: Add validation of user input here if needed
            return self.async_create_entry(title="SMioplus", data=user_input)

        data_schema = vol.Schema({
            vol.Required("stack", default="0"): str,
            # Add other configuration fields as needed
        })

        return self.async_show_form(step_id="user", data_schema=data_schema)

    async def async_step_import(self, import_config):
        """Import a config entry from configuration.yaml."""
        return await self.async_step_user(import_config)