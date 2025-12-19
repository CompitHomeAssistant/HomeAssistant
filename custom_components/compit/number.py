"""Number platform for Compit integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.number import NumberEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER_NAME
from .coordinator import CompitConfigEntry, CompitDataUpdateCoordinator

if TYPE_CHECKING:
    from compit_inext_api import Parameter
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

NUMERIC_PARAM_TYPE = "Numeric"
PARALLEL_UPDATES = 0


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: CompitConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Compit number entities from a config entry."""

    coordinator = entry.runtime_data
    number_entities: list[CompitNumber] = []

    for device_id in coordinator.connector.all_devices:
        device = coordinator.connector.get_device(device_id)
        if device is None:
            continue

        for parameter in device.definition.parameters or []:
            if parameter is None or parameter.type != NUMERIC_PARAM_TYPE:
                continue

            device_param = next(
                (p for p in device.state.params if p.code == parameter.parameter_code),
                None,
            )
            if device_param is None or device_param.hidden:
                continue

            if getattr(parameter, "ReadOnly", False):
                # Read-only numeric values are exposed as sensors.
                continue

            number_entities.append(
                CompitNumber(
                    coordinator,
                    device_id,
                    device.definition.name,
                    parameter,
                ),
            )

    async_add_entities(number_entities)


class CompitNumber(CoordinatorEntity[CompitDataUpdateCoordinator], NumberEntity):
    """Representation of a Compit numeric parameter."""

    def __init__(
        self,
        coordinator: CompitDataUpdateCoordinator,
        device_id: int,
        device_name: str,
        parameter: Parameter,
    ) -> None:
        """Initialize the number entity."""
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

        self._attr_native_min_value = parameter.min_value or 0.0
        self._attr_native_max_value = parameter.max_value or 100.0
        self._attr_native_unit_of_measurement = parameter.unit

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available
            and self.coordinator.connector.get_device(self.device_id) is not None
        )

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        param = self.coordinator.connector.get_device_parameter(
            self.device_id,
            self.parameter.parameter_code,
        )
        if param is None or param.value is None:
            return None
        try:
            return float(param.value)
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await self.coordinator.connector.set_device_parameter(
            self.device_id,
            self.parameter.parameter_code,
            value,
        )
