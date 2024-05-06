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
    """Ustawienie integracji na podstawie wpisu konfiguracyjnego."""
    # Utworzenie instancji API
    try:
        session = async_get_clientsession(hass)
        api = CompitAPI(entry.data["email"], entry.data["password"], session)
        gates = await api.authenticate()
        device_definitions = await get_device_definitions(hass)

        coordinator = CompitDataUpdateCoordinator(hass, gates.gates, api, device_definitions)
        await coordinator.async_config_entry_first_refresh()

        # Przechowywanie instancji API w danych hass, aby inne platformy mogły z niej korzystać
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
    """Obsługa usunięcia wpisu konfiguracyjnego."""
    # Usunięcie wszystkich załadowanych platform
    unload_ok = all(
        await asyncio.gather(
            *[hass.config_entries.async_forward_entry_unload(entry, platform) for platform in PLATFORMS]
        )
    )

    # Usunięcie danych API, jeśli wszystko zostało pomyślnie usunięte
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

async def get_device_definitions(hass: HomeAssistant) -> DeviceDefinitions:
    user_language = hass.config.language
    file_name = f"devices_{user_language}.json"

    try:
        file_path = os.path.join(os.path.dirname(__file__), 'definitions', file_name)

        with open(file_path, 'r', encoding='utf-8') as file:
            return DeviceDefinitions.from_json(json.load(file))
    except FileNotFoundError:
        print(f"Plik {file_path} nie został znaleziony.")
        return None