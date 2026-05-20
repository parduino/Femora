from __future__ import annotations

import math
from typing import Iterable, Optional

from femora.core.damping_base import Damping


def _coerce_float(value, field: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} should be a float") from exc


def _coerce_optional_float(value, field: str) -> Optional[float]:
    if value in (None, ""):
        return None
    return _coerce_float(value, field)


def _coerce_optional_int(value, field: str) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} should be an integer") from exc


class RayleighDamping(Damping):
    def __init__(
        self,
        alphaM: float = 0.0,
        betaK: float = 0.0,
        betaKInit: float = 0.0,
        betaKComm: float = 0.0,
        user_name: Optional[str] = None,
    ):
        alphaM = _coerce_float(alphaM, "alphaM")
        betaK = _coerce_float(betaK, "betaK")
        betaKInit = _coerce_float(betaKInit, "betaKInit")
        betaKComm = _coerce_float(betaKComm, "betaKComm")

        for field, value in {
            "alphaM": alphaM,
            "betaK": betaK,
            "betaKInit": betaKInit,
            "betaKComm": betaKComm,
        }.items():
            if value < 0:
                raise ValueError(f"{field} should be a non-negative float")

        if alphaM + betaK + betaKInit + betaKComm <= 1e-10:
            raise ValueError("At least one of the damping factors should be greater than 0")

        super().__init__(user_name=user_name)
        self.alphaM = alphaM
        self.betaK = betaK
        self.betaKInit = betaKInit
        self.betaKComm = betaKComm

    def __str__(self) -> str:
        res = super().__str__()
        res += f"\n\talphaM: {self.alphaM}"
        res += f"\n\tbetaK: {self.betaK}"
        res += f"\n\tbetaKInit: {self.betaKInit}"
        res += f"\n\tbetaKComm: {self.betaKComm}"
        return res

    def to_tcl(self) -> str:
        return (
            f"# damping rayleigh {self.tag} {self.alphaM} {self.betaK} "
            f"{self.betaKInit} {self.betaKComm} (normal rayleigh damping)"
        )

    @staticmethod
    def get_type() -> str:
        return "Rayleigh"


class ModalDamping(Damping):
    def __init__(
        self,
        numberofModes: int,
        damping_factors: Iterable[float] | str,
        user_name: Optional[str] = None,
    ):
        try:
            numberofModes = int(numberofModes)
        except (TypeError, ValueError) as exc:
            raise ValueError("numberofModes should be an integer") from exc
        if numberofModes <= 0:
            raise ValueError("numberofModes should be greater than 0")

        if isinstance(damping_factors, str):
            damping_factors = [part.strip() for part in damping_factors.split(",")]
        elif not isinstance(damping_factors, Iterable):
            raise ValueError("damping_factors should be a list")

        values = []
        for factor in damping_factors:
            value = _coerce_float(factor, "damping_factors")
            if value < 0 or value > 1:
                raise ValueError(
                    "damping_factors should be greater than or equal to 0 and less than or equal to 1"
                )
            values.append(value)

        if len(values) != numberofModes:
            raise ValueError("damping_factors should have the same length as numberofModes")

        super().__init__(user_name=user_name)
        self.numberofModes = numberofModes
        self.damping_factors = values

    def __str__(self) -> str:
        res = super().__str__()
        res += f"\n\tNumber of Modes: {self.numberofModes}"
        res += f"\n\tDamping Factors: {self.damping_factors}"
        return res

    def to_tcl(self) -> str:
        return f"-modalDamping {' '.join(str(x) for x in self.damping_factors)}"

    @staticmethod
    def get_type() -> str:
        return "Modal"


class FrequencyRayleighDamping(RayleighDamping):
    def __init__(
        self,
        damping_factor: float,
        f1: float = 0.2,
        f2: float = 20.0,
        user_name: Optional[str] = None,
    ):
        f1 = _coerce_float(f1, "f1")
        f2 = _coerce_float(f2, "f2")
        damping_factor = _coerce_float(damping_factor, "damping_factor")

        if f1 <= 0:
            raise ValueError("f1 should be greater than 0")
        if f2 <= 0:
            raise ValueError("f2 should be greater than 0")
        if damping_factor < 0 or damping_factor > 1:
            raise ValueError("damping_factor should be greater than or equal to 0 and less than or equal to 1")

        omega1 = 2 * math.pi * f1
        omega2 = 2 * math.pi * f2
        alphaM = 2 * damping_factor * omega1 * omega2 / (omega1 + omega2)
        betaK = (2 * damping_factor) / (omega1 + omega2)

        super().__init__(
            alphaM=alphaM,
            betaK=betaK,
            betaKInit=0.0,
            betaKComm=0.0,
            user_name=user_name,
        )
        self.f1 = f1
        self.f2 = f2
        self.damping_factor = damping_factor

    def __str__(self) -> str:
        res = super().__str__()
        res += f"\n\tf1: {self.f1}"
        res += f"\n\tf2: {self.f2}"
        res += f"\n\tDamping Factor: {self.damping_factor}"
        return res

    @staticmethod
    def get_type() -> str:
        return "Frequency Rayleigh"

    def to_tcl(self) -> str:
        return (
            f"# damping rayleigh {self.tag} {self.alphaM} {self.betaK} {self.betaKInit} {self.betaKComm} "
            f"(frequency rayleigh damping with f1 = {self.f1} and f2 = {self.f2} "
            f"and damping factor = {self.damping_factor})"
        )


class UniformDamping(Damping):
    def __init__(
        self,
        dampingRatio: float,
        freql: float,
        freq2: float,
        Ta: Optional[float] = None,
        Td: Optional[float] = None,
        tsTagScaleFactorVsTime: Optional[int] = None,
        user_name: Optional[str] = None,
    ):
        dampingRatio = _coerce_float(dampingRatio, "dampingRatio")
        freql = _coerce_float(freql, "freql")
        freq2 = _coerce_float(freq2, "freq2")
        Ta = _coerce_optional_float(Ta, "Ta")
        Td = _coerce_optional_float(Td, "Td")
        tsTagScaleFactorVsTime = _coerce_optional_int(
            tsTagScaleFactorVsTime, "tsTagScaleFactorVsTime"
        )

        if dampingRatio < 0 or dampingRatio > 1:
            raise ValueError("dampingRatio should be greater than or equal to 0 and less than or equal to 1")
        if freql <= 0:
            raise ValueError("freql should be greater than 0")
        if freq2 <= 0 or freq2 <= freql:
            raise ValueError("freq2 should be greater than 0 and greater than freql")

        super().__init__(user_name=user_name)
        self.dampingRatio = dampingRatio
        self.freql = freql
        self.freq2 = freq2
        self.Ta = Ta
        self.Td = Td
        self.tsTagScaleFactorVsTime = tsTagScaleFactorVsTime

    def __str__(self) -> str:
        res = super().__str__()
        res += f"\n\tDamping Ratio: {self.dampingRatio}"
        res += f"\n\tLower Frequency: {self.freql}"
        res += f"\n\tUpper Frequency: {self.freq2}"
        res += f"\n\tTa: {self.Ta if self.Ta is not None else 'default'}"
        res += f"\n\tTd: {self.Td if self.Td is not None else 'default'}"
        res += (
            f"\n\ttsTagScaleFactorVsTime: "
            f"{self.tsTagScaleFactorVsTime if self.tsTagScaleFactorVsTime is not None else 'No time series'}"
        )
        return res

    def to_tcl(self) -> str:
        res = f"damping Uniform {self.tag} {self.dampingRatio} {self.freql} {self.freq2}"
        if self.Ta is not None:
            res += f" -activateTime  {self.Ta}"
        if self.Td is not None:
            res += f" -deactivateTime {self.Td}"
        if self.tsTagScaleFactorVsTime is not None:
            res += f" -fact {self.tsTagScaleFactorVsTime}"
        return res

    @staticmethod
    def get_type() -> str:
        return "Uniform"


class SecantStiffnessProportional(Damping):
    def __init__(
        self,
        damping_factor: float,
        Ta: Optional[float] = None,
        Td: Optional[float] = None,
        tsTagScaleFactorVsTime: Optional[int] = None,
        user_name: Optional[str] = None,
    ):
        damping_factor = _coerce_float(damping_factor, "damping_factor")
        Ta = _coerce_optional_float(Ta, "Ta")
        Td = _coerce_optional_float(Td, "Td")
        tsTagScaleFactorVsTime = _coerce_optional_int(
            tsTagScaleFactorVsTime, "tsTagScaleFactorVsTime"
        )

        if damping_factor < 0 or damping_factor > 1:
            raise ValueError("damping_factor should be greater than or equal to 0 and less than or equal to 1")

        super().__init__(user_name=user_name)
        self.damping_factor = damping_factor
        self.Ta = Ta
        self.Td = Td
        self.tsTagScaleFactorVsTime = tsTagScaleFactorVsTime

    def __str__(self) -> str:
        res = super().__str__()
        res += f"\n\tDamping Factor: {self.damping_factor}"
        res += f"\n\tTa: {self.Ta if self.Ta is not None else 'default'}"
        res += f"\n\tTd: {self.Td if self.Td is not None else 'default'}"
        res += (
            f"\n\ttsTagScaleFactorVsTime: "
            f"{self.tsTagScaleFactorVsTime if self.tsTagScaleFactorVsTime is not None else 'No time series'}"
        )
        return res

    def to_tcl(self) -> str:
        res = f"damping SecStiff {self.tag} {self.damping_factor}"
        if self.Ta is not None:
            res += f" -activateTime  {self.Ta}"
        if self.Td is not None:
            res += f" -deactivateTime {self.Td}"
        if self.tsTagScaleFactorVsTime is not None:
            res += f" -fact {self.tsTagScaleFactorVsTime}"
        return res

    @staticmethod
    def get_type() -> str:
        return "Secant Stiffness Proportional"
