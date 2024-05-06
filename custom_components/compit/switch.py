
import logging
from homeassistant.const import Platform
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from .sensor_matcher import SensorMatcher
from .types.DeviceDefinitions import Parameter
from .types.DeviceState import DeviceInstance, DeviceState
from .types.SystemInfo import Device, Gate
from .coordinator import CompitDataUpdateCoordinator

from .const import (
    DOMAIN
)
_LOGGER: logging.Logger = logging.getLogger(__package__)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_devices):
    coordinator: CompitDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.device_definitions.devices
    async_add_devices(
        [
            CompitSwitch(coordinator, device, parameter, device_definition.name)

            for gate in coordinator.gates
            for device in gate.devices
            if (device_definition := next((definition for definition in coordinator.device_definitions.devices if definition.code == device.type), None)) is not None
            for parameter in device_definition.parameters
            if SensorMatcher.get_platform(parameter, coordinator.data[device.id].state.get_parameter_value(parameter)) == Platform.SWITCH
        ]
    )

class CompitSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator : CompitDataUpdateCoordinator, device: Device, parameter: Parameter, device_name: str):
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.unique_id = f"select_{device.label}{parameter.parameter_code}"
        self.label = f"{device.label} {parameter.label}"
        self.parameter = parameter
        self.device = device
        self.device_name = device_name
        value = self.coordinator.data[self.device.id].state.get_parameter_value(self.parameter)
        self._value = 0
        if value is not None:
             parameter = next((detail for detail in self.parameter.details if detail.param == value.value_code), None)
             if parameter is not None:
                self._value = parameter



    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.device.id)},
            "name": self.device.label,
            "manufacturer": "Compit",
            "model": self.device_name,
            "sw_version": "1.0",
        }

    @property
    def name(self):
        return f"{self.label}"

    @property
    def is_on(self):
        return self._value

    @property
    def extra_state_attributes(self):
        items = []

        items.append({
            "device": self.device.label,
            "device_id": self.device.id,
            "device_class": self.device.class_,
            "device_type": self.device.type
        })

        return {
            "details": items,
        }

    async def async_turn_on(self, **kwargs):
        try:
            if await self.coordinator.api.update_device_parameter(self.device.id, self.parameter.parameter_code, 1) != False:
                await self.coordinator.async_request_refresh()
            self._value = 1
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error(e)

    async def async_turn_off(self, **kwargs):
        try:
            if await self.coordinator.api.update_device_parameter(self.device.id, self.parameter.parameter_code, 0) != False:
                await self.coordinator.async_request_refresh()
            self._value = 0
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error(e)

    async def async_toggle(self, **kwargs):
        if self.is_on():
            await self.async_turn_off()
        else:
            await self.async_turn_on()