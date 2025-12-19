"""The Compit integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from compit_inext_api import CannotConnect, CompitApiConnector, InvalidAuth
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .coordinator import CompitConfigEntry, CompitDataUpdateCoordinator
from .device import setup_devices

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

PLATFORMS: tuple[Platform, ...] = (
    Platform.CLIMATE,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
)


async def async_setup_entry(hass: HomeAssistant, entry: CompitConfigEntry) -> bool:
    """Set up Compit from a config entry."""

    session = async_get_clientsession(hass)
    connector = CompitApiConnector(session)
    try:
        connected = await connector.init(
            entry.data[CONF_EMAIL],
            entry.data[CONF_PASSWORD],
            hass.config.language,
        )
    except CannotConnect as e:
        raise ConfigEntryNotReady(f"Error while connecting to Compit: {e}") from e
    except InvalidAuth as e:
        raise ConfigEntryAuthFailed(
            f"Invalid credentials for {entry.data[CONF_EMAIL]}",
        ) from e

    if not connected:
        raise ConfigEntryAuthFailed("Authentication API error")

    coordinator = CompitDataUpdateCoordinator(hass, entry, connector)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    setup_devices(hass, entry)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: CompitConfigEntry) -> bool:
    """Unload an entry for the Compit integration."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: CompitConfigEntry) -> None:
    """Handle an options update."""
    await hass.config_entries.async_reload(entry.entry_id)
