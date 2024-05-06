from typing import List, Optional, Any

from .DeviceDefinitions import Device, Parameter

class Param:
    def __init__(self, code: str, hidden: bool, max: Optional[float], min: Optional[float], value: Any, value_code: Optional[str], value_label: Optional[str], write: bool, ext_info: Optional[dict] = None):
        self.code = code
        self.hidden = hidden
        self.max = max
        self.min = min
        self.value = value
        self.value_code = value_code
        self.value_label = value_label
        self.write = write
        self.ext_info = ext_info

class DeviceState:
    def __init__(self, errors: List[Any], last_connected_at: str, params: List[Param]):
        self.errors = errors
        self.last_connected_at = last_connected_at
        self.params = params

    def get_parameter_value(self, param: str | Parameter) -> Param:
        if isinstance(param, str):
            return next(filter(lambda item: item.code == param, self.params), None)
        return next(filter(lambda item: item.code == param.parameter_code, self.params), None)


    @classmethod
    def from_json(cls, data: dict):
        params = [Param(
            code=p["code"],
            hidden=p["hidden"],
            max=p.get("max"),
            min=p.get("min"),
            value=p["value"],
            value_code=p.get("value_code"),
            value_label=p.get("value_label"),
            write=p["write"],
            ext_info=p.get("ext_info")
        ) for p in data["params"]]
        return cls(errors=data["errors"], last_connected_at=data["last_connected_at"], params=params)

class DeviceInstance:
    def __init__(self, definition: Device):
        self.definition = definition
        self.state: DeviceState