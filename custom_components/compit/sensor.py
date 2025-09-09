from homeassistant.components.sensor import SensorEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANURFACER_NAME
from .coordinator import CompitDataUpdateCoordinator
from .sensor_matcher import SensorMatcher
from .types.DeviceDefinitions import Parameter
from .types.SystemInfo import Device


async def async_setup_entry(hass: HomeAssistant, entry, async_add_devices):
    """
    Sets up a sensor platform for a given configuration entry.

    This function initializes and adds sensor devices based on the configuration
    entry and the corresponding device data. It retrieves device definitions,
    matches devices and their parameters to the sensor platform, and dynamically
    creates sensors.

    Args:
        hass (HomeAssistant): The Home Assistant instance.
        entry: The configuration entry providing details for setup.
        async_add_devices: Function to add discovered devices asynchronously.
    """
    coordinator: CompitDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices(
        [
            CompitSensor(coordinator, device, parameter, device_definition.name)
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
            == Platform.SENSOR
        ]
    )


class CompitSensor(CoordinatorEntity, SensorEntity):
    def __init__(
        self,
        coordinator: CompitDataUpdateCoordinator,
        device: Device,
        parameter: Parameter,
        device_name: str,
    ):
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.unique_id = f"sensor_{device.label}{parameter.parameter_code}"
        self.label = f"{device.label} {parameter.label}"
        self.parameter = parameter
        self.device = device
        self.device_name = device_name

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
    def state(self):
        value = self.coordinator.data[self.device.id].state.get_parameter_value(
            self.parameter
        )

        if value is None:
            return None
        if value.value_label is not None:
            return value.value_label
        if len(str(value.value)) > 100:
            return str(value.value)[:100] + "..."
        return value.value

    @property
    def unit_of_measurement(self):
        return self.parameter.unit
