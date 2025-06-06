from typing import List


class Device:
    def __init__(self, class_: int, id: int, label: str, type: int, version: int):
        self.class_ = class_
        self.id = id
        self.label = label
        self.type = type
        self.version = version


class Gate:
    def __init__(self, code: str, devices: List[Device], id: int, label: str):
        self.code = code
        self.devices = devices
        self.id = id
        self.label = label


class SystemInfo:
    def __init__(self, gates: List[Gate]):
        self.gates = gates

    @classmethod
    def from_json(cls, data: dict):
        gates = [
            Gate(
                code=g["code"],
                devices=[
                    Device(
                        class_=d["class"], id=d["id"], label=d["label"], type=d["type"], version=d.get("version", 1)
                    )
                    for d in g["devices"]
                ],
                id=g["id"],
                label=g["label"],
            )
            for g in data["gates"]
        ]
        return cls(gates=gates)
