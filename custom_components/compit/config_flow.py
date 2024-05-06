from homeassistant import config_entries
from .const import DOMAIN
from .api import CompitAPI
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_create_clientsession
import voluptuous as vol

class CompitConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1
    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            session = async_create_clientsession(self.hass)
            api = CompitAPI(user_input["email"], user_input["password"], session)
            success = await api.authenticate()

            if success:
                return self.async_create_entry(title="Compit", data=user_input)
            else:
                errors["base"] = "invalid_auth"

        self.data_schema = vol.Schema({
            vol.Required("email"): str,
            vol.Required("password"): str,
        })

        return self.async_show_form(
            step_id="user", data_schema=self.data_schema, errors=errors
        )
class CompitOptionsFlowHandler(config_entries.OptionsFlow):

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional("custom_option", default=self.config_entry.options.get("custom_option", "")): str,
            })
        )