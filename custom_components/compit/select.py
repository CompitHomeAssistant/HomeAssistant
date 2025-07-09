import logging

from homeassistant.components.select import SelectEntity
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
            CompitSelect(coordinator, device, parameter, device_definition.name)
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
               == Platform.SELECT
        ]
    )


class CompitSelect(CoordinatorEntity, SelectEntity):

    def __init__(
            self,
            coordinator: CompitDataUpdateCoordinator,
            device: Device,
            parameter: Parameter,
            device_name: str,
    ):
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.unique_id = f"select_{device.label}{parameter.parameter_code}"
        self.label = f"{device.label} {parameter.label}"
        self.parameter = parameter
        self.device = device
        self.device_name = device_name
        value = self.coordinator.data[self.device.id].state.get_parameter_value(
            self.parameter
        )
        self._value = next(
            detail for detail in self.parameter.details if detail.state == value.value
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
    def options(self) -> list[str]:
        params = [detail.description for detail in self.parameter.details]
        return params

    @property
    def state(self):

        if self._value is not None:
            parameter = next(
                (
                    detail
                    for detail in self.parameter.details
                    if detail.param == self._value.param
                ),
                None,
            )
            if parameter is not None:
                return parameter.description
            else:
                return self._value.description

        return None

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

    async def async_select_option(self, option: str) -> None:
        value = next(
            (
                detail
                for detail in self.parameter.details
                if detail.description == option
            ),
            None,
        )
        self._value = value
        try:
            if (
                    await self.coordinator.api.update_device_parameter(
                        self.device.id, self.parameter.parameter_code, value.state
                    )
                    != False
            ):
                self._value = value
                self.async_write_ha_state()
                await self.coordinator.async_request_refresh()
        except Exception as e:
            _LOGGER.error(e)
