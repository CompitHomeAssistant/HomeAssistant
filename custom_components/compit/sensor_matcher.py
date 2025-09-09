from homeassistant.const import Platform

from .types.DeviceDefinitions import Parameter
from .types.DeviceState import Param


class SensorMatcher:
    @staticmethod
    def get_platform(paramater: Parameter, value: Param) -> Platform | None:
        """
        Determines the platform type for a given parameter and its associated value.

        This method inspects the properties of the provided parameter and its value
        to identify the appropriate platform type, such as sensor, number, or selection.
        If no valid platform type is derived or the conditions for determination
        are unmet, it returns None.

        Args:
            paramater (Parameter): The parameter object containing information
                regarding the type, range, and details.
            value (Param): The value associated with the parameter which includes
                its visibility status.

        Returns:
            Platform | None: A platform description based on the provided parameter
            and value, or None if the conditions are not sufficient to determine
            a platform.
        """
        if value is None or value.hidden:
            return None
        if paramater.readWrite == "R":
            return Platform.SENSOR
        if paramater.min_value is not None and paramater.max_value is not None:
            return Platform.NUMBER
        if paramater.details is not None:
            return Platform.SELECT
