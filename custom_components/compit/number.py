import logging

from homeassistant.components.number import NumberEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANURFACER_NAME
from .coordinator import CompitDataUpdateCoordinator
from .sensor_matcher import SensorMatcher
from .types.DeviceDefinitions import Parameter
from .types.SystemInfo import Device

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_devices):
    coordinator: CompitDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    # coordinator.device_definitions.devices
    async_add_devices(
        [
            CompitNumber(coordinator, device, parameter, device_definition.name)
            for gate in coordinator.gates
            for device in gate.devices
            if (
                   device_definition := next(
                       (
                           definition
                           for definition in coordinator.device_definitions.devices
                           if definition.code == device.type
                       ),
                       None,
                   )
               )
               is not None
            for parameter in device_definition.parameters
            if SensorMatcher.get_platform(
            parameter,
            coordinator.data[device.id].state.get_parameter_value(parameter),
        )
               == Platform.NUMBER
        ]
    )


class CompitNumber(CoordinatorEntity, NumberEntity):

    def __init__(
            self,
            coordinator: CompitDataUpdateCoordinator,
            device: Device,
            parameter: Parameter,
            device_name: str,
    ):
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.unique_id = f"number_{device.label}{parameter.parameter_code}"
        self.label = f"{device.label} {parameter.label}"
        self.parameter = parameter
        self.device = device
        self._attr_unit_of_measurement = parameter.unit
        self.device_name = device_name
        self._value = (
            self.coordinator.data[self.device.id]
            .state.get_parameter_value(self.parameter)
            .value
        )

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.device.id)},
            "name": self.device.label,
            "manufacturer": MANURFACER_NAME,
            "model": self.device_name,
            "sw_version": "1.0",
        }

    @property
    def name(self):
        return f"{self.label}"

    @property
    def native_value(self):
        return self._value

    @property
    def native_min_value(self):
        if isinstance(self.parameter.min_value, (int, float)):
            return self.parameter.min_value
        return (
            self.coordinator.data[self.device.id]
            .state.get_parameter_value(self.parameter)
            .min
        )

    @property
    def native_max_value(self):
        if isinstance(self.parameter.max_value, (int, float)):
            return self.parameter.max_value
        return (
            self.coordinator.data[self.device.id]
            .state.get_parameter_value(self.parameter)
            .max
        )

    @property
    def native_unit_of_measurement(self):
        return self._attr_unit_of_measurement

    @property
    def extra_state_attributes(self):
        items = []

        items.append(
            {
                "device": self.device.label,
                "device_id": self.device.id,
                "device_class": self.device.class_,
                "device_type": self.device.type,
            }
        )

        return {
            "details": items,
        }

    async def async_set_native_value(self, value: int) -> None:
        try:
            if (
                    await self.coordinator.api.update_device_parameter(
                        self.device.id, self.parameter.parameter_code, value
                    )
                    != False
            ):
                self._value = value
                self.async_write_ha_state()
                await self.coordinator.async_request_refresh()
        except Exception as e:
            _LOGGER.error(e)
