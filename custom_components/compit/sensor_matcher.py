from homeassistant.const import Platform

from .types.DeviceState import Param
from .types.DeviceDefinitions import Parameter

class SensorMatcher:
    @staticmethod
    def get_platform(paramater: Parameter, value: Param) -> Platform | None:
        if value is None or value.hidden:
            return None
        if paramater.readWrite == "R":
            return Platform.SENSOR
        if paramater.min_value is not None and paramater.max_value is not None:
            return Platform.NUMBER
        if paramater.details is not None:
            if len(paramater.details) == 2:
                return Platform.SWITCH
            return Platform.SELECT