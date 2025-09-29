import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CompitDataUpdateCoordinator
from .types.DeviceDefinitions import Parameter
from .types.SystemInfo import Device

_LOGGER = logging.getLogger(__name__)


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
        self.unique_id = f"switch_{device.label}{parameter.parameter_code}"
        self.label = f"{device.label} {parameter.label}"
        self.parameter = parameter
        self.device = device
        self.device_name = device_name
        self._is_on: bool = False

        # Initialize from coordinator data safely (state may be bool or DeviceState)
        data_entry = getattr(self.coordinator, "data", {}).get(self.device.id)
        state_obj = (
            getattr(data_entry, "state", None) if data_entry is not None else None
        )

        if isinstance(state_obj, bool):
            self._is_on = state_obj
        elif hasattr(state_obj, "get_parameter_value"):
            try:
                value = state_obj.get_parameter_value(self.parameter)
            except Exception:  # defensive: unexpected state shape
                value = None
            if value is not None:
                raw_val = getattr(value, "value", None)
                if raw_val is not None:
                    try:
                        self._is_on = bool(int(raw_val))
                    except Exception:
                        self._is_on = bool(raw_val)
                else:
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
        # Try to reflect latest coordinator value if available
        try:
            data_entry = getattr(self.coordinator, "data", {}).get(self.device.id)
            state_obj = (
                getattr(data_entry, "state", None) if data_entry is not None else None
            )
            if isinstance(state_obj, bool):
                return state_obj
            if hasattr(state_obj, "get_parameter_value"):
                value = state_obj.get_parameter_value(self.parameter)
                if value is not None:
                    raw_val = getattr(value, "value", None)
                    if raw_val is not None:
                        try:
                            return bool(int(raw_val))
                        except Exception:
                            return bool(raw_val)
        except Exception:
            # fall back to cached flag
            pass
        return self._is_on

    @property
    def extra_state_attributes(self):
        return {
            "details": [
                {
                    "device": self.device.label,
                    "device_id": self.device.id,
                    "device_class": self.device.class_,
                    "device_type": self.device.type,
                }
            ],
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


# ... existing code ...


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    coordinator: CompitDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for gate in coordinator.gates:
        for device in gate.devices:
            device_definition = next(
                (
                    d
                    for d in coordinator.device_definitions.devices
                    if d.code == device.type
                ),
                None,
            )
            if device_definition is None:
                continue

            # Safely inspect current state
            data_entry = getattr(coordinator, "data", {}).get(device.id)
            state_obj = (
                getattr(data_entry, "state", None) if data_entry is not None else None
            )

            for parameter in device_definition.parameters:
                # Only writable, non-number, non-select -> treat as switch
                is_writable = getattr(parameter, "readWrite", "R") != "R"
                is_number_like = (
                    parameter.min_value is not None and parameter.max_value is not None
                )
                is_select_like = parameter.details is not None
                if not is_writable or is_number_like or is_select_like:
                    continue

                # If state is a DeviceState, check visibility; if bool or None, skip the check
                visible = True
                if hasattr(state_obj, "get_parameter_value"):
                    try:
                        v = state_obj.get_parameter_value(parameter)
                        visible = v is not None and not getattr(v, "hidden", False)
                    except Exception:
                        visible = False

                if visible:
                    entities.append(
                        CompitSwitch(
                            coordinator=coordinator,
                            device=device,
                            parameter=parameter,
                            device_name=device_definition.name,
                        )
                    )

    if entities:
        async_add_entities(entities)
