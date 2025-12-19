"""Define an object to manage fetching Compit data."""

import logging
from datetime import timedelta

from compit_inext_api import (
    CannotConnect,
    CompitApiConnector,
    DeviceInstance,
    InvalidAuth,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

SCAN_INTERVAL = timedelta(seconds=30)
_LOGGER: logging.Logger = logging.getLogger(__name__)

type CompitConfigEntry = ConfigEntry[CompitDataUpdateCoordinator]


class CompitDataUpdateCoordinator(DataUpdateCoordinator[dict[int, DeviceInstance]]):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        connector: CompitApiConnector,
    ) -> None:
        """Initialize."""
        self.connector = connector

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
            config_entry=config_entry,
        )

    async def _async_update_data(self) -> dict[int, DeviceInstance]:
        """Update data via library."""
        try:
            await self.connector.update_state(device_id=None)  # Update all devices
        except InvalidAuth as err:
            raise ConfigEntryAuthFailed("Invalid authentication") from err
        except CannotConnect as err:
            raise UpdateFailed("Failed to connect") from err
        except Exception as err:
            raise UpdateFailed("Unexpected error") from err

        return self.connector.all_devices
