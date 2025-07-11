"""Home Assistant integration."""

import json
import logging
import os

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CompitAPI
from .const import DOMAIN, PLATFORMS
from .coordinator import CompitDataUpdateCoordinator
from .types.DeviceDefinitions import DeviceDefinitions

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Compit integration from a config entry."""
    try:
        _LOGGER.debug("Setting up Compit integration for entry: %s", entry.entry_id)
        session = async_get_clientsession(hass)

        # Extract and log authentication attempt
        email = entry.data["email"]
        _LOGGER.debug("Authenticating with email: %s", email)
        api = CompitAPI(email, entry.data["password"], session)

        # Log authentication and device definition loading
        _LOGGER.info("Authenticating with Compit API")
        authenticated_gates = await api.authenticate()
        if not authenticated_gates:
            _LOGGER.error("Authentication failed")
            return False

        _LOGGER.info("Successfully authenticated with Compit API")

        _LOGGER.debug(
            "Loading device definitions for language: %s", hass.config.language
        )

        device_definitions = await get_device_definitions(hass, hass.config.language)

        # Set up coordinator
        _LOGGER.debug("Initializing data coordinator")

        coordinator = CompitDataUpdateCoordinator(
            hass, authenticated_gates.gates, api, device_definitions
        )
        await coordinator.async_config_entry_first_refresh()

        # Store coordinator in hass.data
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

        # Set up platforms
        _LOGGER.info("Setting up platforms for Compit integration")
        for platform in PLATFORMS:
            coordinator.platforms.append(platform)

        # Use the correct method for forwarding entry setups
        _LOGGER.debug("Setting up platforms: %s", PLATFORMS)
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        _LOGGER.info("Compit integration successfully set up")
        return True
    except Exception as e:
        _LOGGER.exception("Error during Compit integration setup: %s", e)
        # Raising the exception will mark the setup as failed
        raise


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Compit integration for entry: %s", entry.entry_id)

    try:
        # Use the correct method for unloading entry setups
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

        if unload_ok:
            _LOGGER.debug("Successfully unloaded all platforms")
            hass.data[DOMAIN].pop(entry.entry_id)
            _LOGGER.info("Compit integration successfully unloaded")
        else:
            _LOGGER.warning("Some platforms failed to unload properly")

        return unload_ok
    except Exception as e:
        _LOGGER.exception("Error during unloading Compit integration: %s", e)
        return False


async def get_device_definitions(hass: HomeAssistant, lang: str) -> DeviceDefinitions:
    """Load device definitions from JSON file based on language."""
    file_name = f"devices_{lang}.json"
    _LOGGER.debug("Loading device definitions from %s", file_name)

    try:
        file_path = os.path.join(os.path.dirname(__file__), "definitions", file_name)
        _LOGGER.debug("Full file path: %s", file_path)

        with open(file_path, "r", encoding="utf-8") as file:
            definitions = DeviceDefinitions.from_json(json.load(file))
            _LOGGER.debug(
                "Successfully loaded device definitions for language: %s", lang
            )

            return definitions
    except FileNotFoundError:
        _LOGGER.warning("Device definitions file not found: %s", file_path)
        if lang != "en":
            _LOGGER.info("Falling back to English device definitions")
            return await get_device_definitions(hass, "en")

        _LOGGER.error("English device definitions file not found")
        raise

    except json.JSONDecodeError:
        _LOGGER.error("Failed to parse device definitions file: %s", file_path)
        raise
