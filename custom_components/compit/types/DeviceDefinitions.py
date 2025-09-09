from typing import List, Dict, Any, Optional


class ParameterDetails:
    def __init__(self, State: int, Description: str, Param: str):
        self.state = State
        self.description = Description
        self.param = Param


class Parameter:
    def __init__(
            self,
            ParameterCode: str,
            Label: str,
            ReadWrite: str = "R",
            Details: Optional[List[ParameterDetails]] = None,
            MinValue: Optional[float] = None,
            MaxValue: Optional[float] = None,
            Unit: Optional[str] = None,
    ):
        self.parameter_code = ParameterCode
        self.label = Label
        self.readWrite = ReadWrite
        self.details = (
            [ParameterDetails(**detail) if Details else None for detail in Details]
            if Details
            else None
        )
        self.min_value = MinValue
        self.max_value = MaxValue
        self.unit = Unit


class Device:
    def __init__(
            self,
            name: str,
            parameters: List[Parameter],
            code: int,
            _class: int,
            id: Optional[int],
    ):
        self.name = name
        self.parameters = parameters
        self.code = code
        self._class = _class
        self.id = id

    @classmethod
    def from_json(cls, data: Dict[str, Any]):
        parameters = [Parameter(**param) for param in data.get("Parameters", [])]
        return cls(
            name=data["Name"],
            parameters=parameters,
            code=data["Code"],
            _class=data["Class"],
            id=data.get("ID"),
        )


class DeviceDefinitions:
    def __init__(self, devices: List[Device]):
        self.devices = devices

    @classmethod
    def from_json(cls, data: Any):
        devices = [Device.from_json(device_data) for device_data in data]
        return cls(devices=devices)
