import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import CompitAPI
from .const import DOMAIN


class CompitConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self.data_schema = None

    async def async_step_user(self, user_input=None):
        """
        Handles the user step of the configuration flow for setting up the Compit integration.

        This asynchronous method manages the user input form for authentication. It validates
        the credentials provided by the user by communicating with the Compit API and ensures
        that the entered data is correct. If the authentication is successful, an entry is
        created for the integration; otherwise, the appropriate error message is displayed
        to the user.

        Parameters:
            user_input: The dictionary containing the user-provided input. Expected fields are
                'email' and 'password'. If None, the method will return the initial user input
                form.

        Returns:
            Returns either the configuration entry created upon successful authentication or
            a form displaying errors if the authentication fails.

        Raises:
            KeyError: Raised if user_input lacks required keys ('email' or 'password'),
                although validation prevents this in practice.
        """
        errors = {}

        if user_input is not None:
            session = async_create_clientsession(self.hass)
            api = CompitAPI(user_input["email"], user_input["password"], session)
            success = await api.authenticate()

            if success:
                return self.async_create_entry(title="Compit", data=user_input)
            else:
                errors["base"] = "invalid_auth"

        self.data_schema = vol.Schema(
            {
                vol.Required("email"): str,
                vol.Required("password"): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=self.data_schema, errors=errors
        )


class CompitOptionsFlowHandler(config_entries.OptionsFlow):
    """
    Handles the option flow for the Compit integration.

    This class defines how the user can modify configuration options in the entry
    through the Home Assistant UI. It provides steps for user interaction and processes
    the provided input to update the configuration.

    Attributes:
        config_entry: The configuration entry for the integration.

    Methods:
        async_step_init: Handles the initial step of the options flow, which allows the
        user to either provide input to modify options or display a form for input.
    """

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "custom_option",
                        default=self.config_entry.options.get("custom_option", ""),
                    ): str,
                }
            ),
        )
