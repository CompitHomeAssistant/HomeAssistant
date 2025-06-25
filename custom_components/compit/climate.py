import logging
from typing import List
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.climate import ClimateEntity
from homeassistant.core import HomeAssistant

from .types.DeviceDefinitions import Parameter
from .types.SystemInfo import Device
from .coordinator import CompitDataUpdateCoordinator
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from .const import DOMAIN, MANURFACER_NAME

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_devices):
    coordinator: CompitDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_devices(
        [
            CompitClimate(
                coordinator,
                device,
                device_definition.parameters,
                device_definition.name,
            )
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
            if (device_definition._class == 10)
        ]
    )


class CompitClimate(CoordinatorEntity, ClimateEntity):

    def __init__(
        self,
        coordinator: CompitDataUpdateCoordinator,
        device: Device,
        parameters: List[Parameter],
        device_name: str,
    ):
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.unique_id = f"{device.label}_climate"
        self.label = f"{device.label} climate"
        self.parameters = {
            parameter.parameter_code: parameter for parameter in parameters
        }
        self.device = device
        self.available_presets: Parameter = self.parameters.get("__trybpracytermostatu")
        self.available_fan_modes: Parameter = self.parameters.get("__trybaero")
        self.available_hvac_modes: Parameter = self.parameters.get(
            "__trybpracyinstalacji"
        )
        self.device_name = device_name
        self.set_initial_values()

    def set_initial_values(self):
        preset_mode = self.coordinator.data[self.device.id].state.get_parameter_value(
            "__trybpracytermostatu"
        )
        if preset_mode is not None:
            self._preset_mode = next(
                (
                    item
                    for item in self.available_presets.details
                    if item.state == preset_mode.value
                ),
                None,
            ).state
        else:
            self._preset_mode = None
        fan_mode = self.coordinator.data[self.device.id].state.get_parameter_value(
            "__trybaero"
        )
        if fan_mode is not None:
            self._fan_mode = next(
                (
                    item
                    for item in self.available_fan_modes.details
                    if item.state == fan_mode.value
                ),
                None,
            ).state
        else:
            self._fan_mode = None

        hvac_mode = self.coordinator.data[self.device.id].state.get_parameter_value(
            "__trybpracyinstalacji"
        )
        if hvac_mode is not None:
            if hvac_mode.value == 0:
                self._hvac_mode = HVACMode.HEAT
            if hvac_mode.value == 1:
                self._hvac_mode = HVACMode.OFF
            if hvac_mode.value == 2:
                self._hvac_mode = HVACMode.COOL
        else:
            self._hvac_mode = None

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
    def current_temperature(self):
        value = self.coordinator.data[self.device.id].state.get_parameter_value(
            "__tpokojowa"
        )
        if value is None:
            return None
        return value.value

    @property
    def target_temperature(self):
        value = self.coordinator.data[self.device.id].state.get_parameter_value(
            "__tpokzadana"
        )
        if value is None:
            return None
        return value.value

    @property
    def supported_features(self):
        return (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.PRESET_MODE
        )

    @property
    def preset_modes(self):
        if self.available_presets is None:
            return None
        return [item.description for item in self.available_presets.details]

    @property
    def fan_modes(self):
        if self.available_fan_modes is None:
            return None
        return [item.description for item in self.available_fan_modes.details]

    @property
    def hvac_modes(self):
        return [HVACMode.HEAT, HVACMode.COOL, HVACMode.OFF]

    @property
    def preset_mode(self):
        if self._preset_mode is None:
            return None

        return next(
            (
                item
                for item in self.available_presets.details
                if item.state == self._preset_mode
            ),
            None,
        ).description

    @property
    def fan_mode(self):
        if self._fan_mode is None:
            return None

        return next(
            (
                item
                for item in self.available_fan_modes.details
                if item.state == self._fan_mode
            ),
            None,
        ).description

    @property
    def hvac_mode(self):
        """Retirn current HVAC mode."""
        return self._hvac_mode

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temp = kwargs.get("temperature")
        self._temperature = temp
        self._preset_mode = 2
        await self.async_call_api("__trybpracytermostatu", 2)
        await self.async_call_api("__tempzadpracareczna", temp)

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        value = 0
        if hvac_mode == HVACMode.HEAT:
            value = 0
        elif hvac_mode == HVACMode.OFF:
            value = 1
        elif hvac_mode == HVACMode.COOL:
            value = 2
        self._hvac_mode = hvac_mode
        await self.async_call_api("__trybpracyinstalacji", value)

    async def async_set_preset_mode(self, preset_mode):
        """Set new target preset mode."""
        value = next(
            (
                item
                for item in self.available_presets.details
                if item.description == preset_mode
            ),
            None,
        )
        self._preset_mode = value.state
        await self.async_call_api("__trybpracytermostatu", value.state)

    async def async_set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        value = next(
            (
                item
                for item in self.available_fan_modes.details
                if item.description == fan_mode
            ),
            None,
        )
        self._fan_mode = value.state
        await self.async_call_api("__trybaero", value.state)

    @property
    def temperature_unit(self):
        return UnitOfTemperature.CELSIUS

    async def async_call_api(self, parameter: str, value: int) -> None:
        """Call the Compit API to update a device parameter.

        Args:
            parameter: The parameter code to update
            value: The new value to set for the parameter
        """
        try:
            if (
                await self.coordinator.api.update_device_parameter(
                    self.device.id, parameter, value
                )
                != False
            ):
                await self.coordinator.async_request_refresh()
                self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error(e)
