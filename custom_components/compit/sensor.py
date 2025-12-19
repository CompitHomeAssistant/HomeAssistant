"""Sensor platform for Compit integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER_NAME
from .coordinator import CompitConfigEntry, CompitDataUpdateCoordinator

if TYPE_CHECKING:
    from compit_inext_api import Parameter
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

SENSOR_PARAM_TYPE = "Sensor"
PARALLEL_UPDATES = 0


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: CompitConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Compit sensor entities from a config entry."""

    coordinator = entry.runtime_data
    sensor_entities: list[CompitSensor] = []

    for device_id in coordinator.connector.all_devices:
        device = coordinator.connector.get_device(device_id)
        if device is None:
            continue

        for parameter in device.definition.parameters or []:
            if parameter is None:
                continue

            is_sensor = parameter.type == SENSOR_PARAM_TYPE
            is_readonly = parameter.type == getattr(
                parameter,
                "ReadOnly",
                False,
            )

            if not (is_sensor or is_readonly):
                continue

            device_param = next(
                (p for p in device.state.params if p.code == parameter.parameter_code),
                None,
            )
            if device_param is None or device_param.hidden:
                continue

            sensor_entities.append(
                CompitSensor(
                    coordinator,
                    device_id,
                    device.definition.name,
                    parameter,
                ),
            )

    async_add_entities(sensor_entities)


class CompitSensor(CoordinatorEntity[CompitDataUpdateCoordinator], SensorEntity):
    """Representation of a Compit sensor parameter."""

    def __init__(
        self,
        coordinator: CompitDataUpdateCoordinator,
        device_id: int,
        device_name: str,
        parameter: Parameter,
    ) -> None:
        """Initialize the sensor entity."""
        super().__init__(coordinator)
        self.device_id = device_id
        self.parameter = parameter

        self._attr_name = parameter.label
        self._attr_unique_id = f"{device_id}_{parameter.parameter_code}"
        self._attr_native_unit_of_measurement = parameter.unit
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
    def native_value(self) -> str | int | float | bool | None:
        """Return the current value."""
        param = self.coordinator.connector.get_device_parameter(
            self.device_id,
            self.parameter.parameter_code,
        )

        if param is None or len(str(param.value)) > 20:
            return None  # Too long or invalid value, put in extra attributes instead

        return param.value

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        """Return extra state attributes."""
        param = self.coordinator.connector.get_device_parameter(
            self.device_id,
            self.parameter.parameter_code,
        )

        if param is None or len(str(param.value)) > 1000 or len(str(param.value)) <= 20:
            return None

        return {"raw": param.value}
