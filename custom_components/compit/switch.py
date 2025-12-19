"""Switch (boolean) platform for Compit integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER_NAME
from .coordinator import CompitConfigEntry, CompitDataUpdateCoordinator

if TYPE_CHECKING:
    from compit_inext_api import Parameter
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

BOOLEAN_PARAM_TYPE = "Boolean"
PARALLEL_UPDATES = 0


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: CompitConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Compit switch entities from a config entry."""

    coordinator = entry.runtime_data
    switch_entities: list[CompitSwitch] = []

    for device_id in coordinator.connector.all_devices:
        device = coordinator.connector.get_device(device_id)
        if device is None:
            continue

        for parameter in device.definition.parameters or []:
            if parameter is None or parameter.type != BOOLEAN_PARAM_TYPE:
                continue

            if getattr(parameter, "ReadOnly", False):
                # Boolean read-only values should be exposed as sensors (if needed).
                continue

            device_param = next(
                (p for p in device.state.params if p.code == parameter.parameter_code),
                None,
            )
            if device_param is None or device_param.hidden:
                continue

            switch_entities.append(
                CompitSwitch(
                    coordinator,
                    device_id,
                    device.definition.name,
                    parameter,
                ),
            )

    async_add_entities(switch_entities)


class CompitSwitch(CoordinatorEntity[CompitDataUpdateCoordinator], SwitchEntity):
    """Representation of a Compit boolean parameter."""

    def __init__(
        self,
        coordinator: CompitDataUpdateCoordinator,
        device_id: int,
        device_name: str,
        parameter: Parameter,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self.device_id = device_id
        self.parameter = parameter

        self._attr_name = parameter.label
        self._attr_unique_id = f"{device_id}_{parameter.parameter_code}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(device_id))},
            name=device_name,
            manufacturer=MANUFACTURER_NAME,
            model=device_name,
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available
            and self.coordinator.connector.get_device(self.device_id) is not None
        )

    @property
    def is_on(self) -> bool | None:
        """Return if the switch is on."""
        param = self.coordinator.connector.get_device_parameter(
            self.device_id,
            self.parameter.parameter_code,
        )
        if param is None or param.value is None:
            return None
        return bool(param.value)

    async def async_turn_on(self) -> None:
        """Turn the entity on."""
        await self.coordinator.connector.set_device_parameter(
            self.device_id,
            self.parameter.parameter_code,
            1,
        )

    async def async_turn_off(self) -> None:
        """Turn the entity off."""
        await self.coordinator.connector.set_device_parameter(
            self.device_id,
            self.parameter.parameter_code,
            0,
        )
