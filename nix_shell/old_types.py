from typing import TypedDict


class InputDrv(TypedDict):
    dynamicOutputs: dict[str, str]
    outputs: list[str]


class Output(TypedDict):
    path: str


class NixDerivation(TypedDict):
    args: list[str]
    builder: str
    env: dict[str, str]
    inputDrvs: dict[str, InputDrv]
    inputSrcs: list[str]
    name: str
    outputs: dict[str, Output]
    system: str
