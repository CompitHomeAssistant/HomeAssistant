import logging
from datetime import timedelta
from typing import Any, List, Dict, Tuple, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CompitAPI
from .const import DOMAIN
from .types.DeviceDefinitions import DeviceDefinitions, Device
from .types.DeviceState import DeviceInstance
from .types.SystemInfo import Gate

SCAN_INTERVAL = timedelta(minutes=1)
_LOGGER: logging.Logger = logging.getLogger(__package__)


class CompitDataUpdateCoordinator(DataUpdateCoordinator[dict[Any, DeviceInstance]]):
    """Class to manage fetching data from the API."""

    def __init__(
            self,
            hass: HomeAssistant,
            gates: List[Gate],
            api: CompitAPI,
            device_definitions: DeviceDefinitions,
    ) -> None:
        """Initialize."""
        self.devices: dict[Any, DeviceInstance] = {}
        self.api = api
        self.gates = gates
        self.device_definitions = device_definitions
        # Build an index for fast device definition lookup: key = (class, code/type)
        self._definitions_by_key: Dict[Tuple[int, int], Device] = self._build_definitions_index(device_definitions)
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    @staticmethod
    def _build_definitions_index(definitions: DeviceDefinitions) -> Dict[Tuple[int, int], Device]:
        """Create an index for device definitions keyed by (class, code)."""
        index: Dict[Tuple[int, int], Device] = {}
        for d in definitions.devices:
            index[(d._class, d.code)] = d
        return index

    def _find_definition(self, class_id: int, type_code: int) -> Optional[Device]:
        """Find a device definition by class and type/code."""
        return self._definitions_by_key.get((class_id, type_code))

    def _get_or_create_device_instance(self, device) -> DeviceInstance:
        """Return an existing DeviceInstance or create one using its definition."""
        dev_id = device.id
        instance = self.devices.get(dev_id)
        if instance is not None:
            return instance

        definition = self._find_definition(device.class_, device.type)
        if definition is None:
            raise UpdateFailed(
                f"Missing device definition for device id={dev_id}, class={device.class_}, type={device.type}"
            )

        instance = DeviceInstance(definition)
        self.devices[dev_id] = instance
        return instance

    async def _async_update_data(self) -> dict[Any, DeviceInstance]:
        """Update data via library."""
        try:
            for gate in self.gates:
                _LOGGER.info("Bramka: %s, Kod: %s", gate.label, gate.code)
                for device in gate.devices:
                    instance = self._get_or_create_device_instance(device)

                    _LOGGER.info(
                        "  Urządzenie: %s, ID: %s, Klasa: %s, Typ: %s",
                        device.label,
                        device.id,
                        device.class_,
                        device.type
                    )
                    state = await self.api.get_state(device.id)
                    instance.state = state

            return self.devices
        except Exception as exception:
            raise UpdateFailed(f"Update failed: {exception}") from exception
