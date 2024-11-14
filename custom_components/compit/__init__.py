"""Przykład integracji z Home Assistant."""
import asyncio
import json
import os
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .types.DeviceDefinitions import DeviceDefinitions
from .coordinator import CompitDataUpdateCoordinator
from .const import DOMAIN, PLATFORMS
from .api import CompitAPI

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    try:
        session = async_get_clientsession(hass)
        api = CompitAPI(entry.data["email"], entry.data["password"], session)
        gates = await api.authenticate()
        device_definitions = await get_device_definitions(hass, hass.config.language)

        coordinator = CompitDataUpdateCoordinator(hass, gates.gates, api, device_definitions)
        await coordinator.async_config_entry_first_refresh()

        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

        for platform in PLATFORMS:
            coordinator.platforms.append(platform)
            hass.async_create_task(
                hass.config_entries.async_forward_entry_setup(entry, platform)
            )
    except Exception as e:
        print(f"Wystąpił błąd: {e}")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = all(
        await asyncio.gather(
            *[hass.config_entries.async_forward_entry_unload(entry, platform) for platform in PLATFORMS]
        )
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

async def get_device_definitions(hass: HomeAssistant, lang: str) -> DeviceDefinitions:

    file_name = f"devices_{lang}.json"

    try:
        file_path = os.path.join(os.path.dirname(__file__), 'definitions', file_name)

        with open(file_path, 'r', encoding='utf-8') as file:
            return DeviceDefinitions.from_json(json.load(file))
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        return get_device_definitions(hass, "en")