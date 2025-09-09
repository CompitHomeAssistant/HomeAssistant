import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CompitDataUpdateCoordinator
from .sensor_matcher import SensorMatcher
from .types.DeviceDefinitions import Parameter
from .types.SystemInfo import Device

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_devices):
    """
    Sets up the switch platform for a specific entry in Home Assistant.

    This function initializes and adds switch devices dynamically based on the
    provided entry, using the data from the specified coordinator object. The
    devices are filtered according to their type, platform compatibility, and available
    parameters.

    Args:
        hass (HomeAssistant): The Home Assistant core object.
        entry: The configuration entry for the integration.
        async_add_devices: Callback function to add devices to Home Assistant.

    """
    coordinator: CompitDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices(
        [
            CompitSwitch(coordinator, device, parameter, device_definition.name)
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
            == Platform.SWITCH
        ]
    )


class CompitSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(
        self,
        coordinator: CompitDataUpdateCoordinator,
        device: Device,
        parameter: Parameter,
        device_name: str,
    ):
        super().__init__(coordinator)
        self.coordinator = coordinator
        # Use a "switch_" prefix for clarity
        self.unique_id = f"switch_{device.label}{parameter.parameter_code}"
        self.label = f"{device.label} {parameter.label}"
        self.parameter = parameter
        self.device = device
        self.device_name = device_name

        # Initialize boolean state
        self._is_on: bool = False

        # Safely read current value from coordinator
        data_entry = (
            self.coordinator.data.get(self.device.id)
            if hasattr(self.coordinator, "data")
            else None
        )
        state_obj = (
            getattr(data_entry, "state", None) if data_entry is not None else None
        )

        # If a state is already a boolean, use it directly
        if isinstance(state_obj, bool):
            self._is_on = state_obj
        # If a state has get_parameter_value, resolve the parameter
        elif hasattr(state_obj, "get_parameter_value"):
            value = state_obj.get_parameter_value(self.parameter)
            if value is not None:
                # Prefer numeric/boolean value when present
                raw_val = getattr(value, "value", None)
                if raw_val is not None:
                    # Coerce to boolean
                    try:
                        self._is_on = bool(int(raw_val))  # handles "0"/"1"/0/1
                    except Exception:
                        self._is_on = bool(raw_val)
                else:
                    # Fall back to matching by value_code against parameter details
                    vcode = getattr(value, "value_code", None)
                    details = self.parameter.details or []
                    matched = next(
                        (d for d in details if getattr(d, "param", None) == vcode), None
                    )
                    if matched is not None and hasattr(matched, "state"):
                        self._is_on = bool(getattr(matched, "state"))

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
        return self._is_on

    @property
    def extra_state_attributes(self):
        items = [
            {
                "device": self.device.label,
                "device_id": self.device.id,
                "device_class": self.device.class_,
                "device_type": self.device.type,
            }
        ]

        return {
            "details": items,
        }

    async def async_turn_on(self, **kwargs):
        try:
            ok = await self.coordinator.api.update_device_parameter(
                self.device.id, self.parameter.parameter_code, 1
            )
            if not ok:
                await self.coordinator.async_request_refresh()
            self._is_on = True
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error(e)

    async def async_turn_off(self, **kwargs):
        try:
            ok = await self.coordinator.api.update_device_parameter(
                self.device.id, self.parameter.parameter_code, 0
            )
            if not ok:
                await self.coordinator.async_request_refresh()
            self._is_on = False
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error(e)

    async def async_toggle(self, **kwargs):
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()
