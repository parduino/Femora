from __future__ import annotations

import math
from typing import Iterable, Optional

from femora.core.damping_base import Damping


def _coerce_float(value, field: str) -> float:
    """Coerce a value to a float.

    Args:
        value: The value to convert.
        field: Field name for error reporting.

    Returns:
        The converted float value.

    Raises:
        ValueError: If the value cannot be converted to a float.
    """
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} should be a float") from exc


def _coerce_optional_float(value, field: str) -> Optional[float]:
    """Coerce a value to a float if it is not empty.

    Args:
        value: The value to convert.
        field: Field name for error reporting.

    Returns:
        The converted float value or None.
    """
    if value in (None, ""):
        return None
    return _coerce_float(value, field)


def _coerce_optional_int(value, field: str) -> Optional[int]:
    """Coerce a value to an integer if it is not empty.

    Args:
        value: The value to convert.
        field: Field name for error reporting.

    Returns:
        The converted integer value or None.

    Raises:
        ValueError: If the value cannot be converted to an integer.
    """
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} should be an integer") from exc


class RayleighDamping(Damping):
    """Classical mass- and stiffness-proportional Rayleigh damping model.

    RayleighDamping defines viscous damping factors proportional to mass (alphaM)
    and/or elements stiffness (betaK, betaKInit, betaKComm). It is commonly assigned
    to regions for dynamic transient simulations in OpenSees.

    Tcl form:
        Renders inside region definitions as:
        ``-rayleigh <alphaM> <betaK> <betaKInit> <betaKComm>``

    Note:
        - All factors must be non-negative.
        - At least one damping factor must be greater than zero.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        damping = model.damping.rayleigh(
            alphaM=0.05,
            betaK=0.01,
        )
        print(damping.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__", "get_type"],
    }

    def __init__(
        self,
        alphaM: float = 0.0,
        betaK: float = 0.0,
        betaKInit: float = 0.0,
        betaKComm: float = 0.0,
        user_name: Optional[str] = None,
    ):
        """Create a Rayleigh damping model.

        Args:
            alphaM: Mass-proportional damping factor.
            betaK: Current stiffness-proportional damping factor.
            betaKInit: Initial stiffness-proportional damping factor.
            betaKComm: Committed stiffness-proportional damping factor.
            user_name: Optional unique name for the damping object.

        Raises:
            ValueError: If any damping factor is negative or if all factors are zero.
        """
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
        """Render this Rayleigh damping model as an OpenSees Tcl comment.

        Returns:
            The Tcl string comment.
        """
        return (
            f"# damping rayleigh {self.tag} {self.alphaM} {self.betaK} "
            f"{self.betaKInit} {self.betaKComm} (normal rayleigh damping)"
        )

    @staticmethod
    def get_type() -> str:
        """Get the damping type name.

        Returns:
            The string "Rayleigh".
        """
        return "Rayleigh"


class ModalDamping(Damping):
    """Mode-specific damping ratios for dynamic transient analysis.

    ModalDamping defines viscous damping ratios directly for a specified number of
    eigenmodes. It is commonly used in structural dynamics when modal responses are decoupled.

    Tcl form:
        Renders inside region definitions as:
        ``-modalDamping <factor1> <factor2> ...``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        damping = model.damping.modal(
            numberofModes=3,
            damping_factors=[0.05, 0.05, 0.05],
        )
        print(damping.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__", "get_type"],
    }

    def __init__(
        self,
        numberofModes: int,
        damping_factors: Iterable[float] | str,
        user_name: Optional[str] = None,
    ):
        """Create a modal damping model.

        Args:
            numberofModes: Number of modes to apply damping to.
            damping_factors: Damping ratios (between 0.0 and 1.0) for each mode.
                Can be a list of floats or a comma-separated string.
            user_name: Optional unique name for the damping object.

        Raises:
            ValueError: If number of modes is invalid, or if the damping factors
                do not match the mode count, or are outside `[0.0, 1.0]`.
        """
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
        """Render this modal damping model as an OpenSees Tcl argument string.

        Returns:
            The Tcl argument string.
        """
        return f"-modalDamping {' '.join(str(x) for x in self.damping_factors)}"

    @staticmethod
    def get_type() -> str:
        """Get the damping type name.

        Returns:
            The string "Modal".
        """
        return "Modal"


class FrequencyRayleighDamping(RayleighDamping):
    """Frequency-based Rayleigh damping generator.

    FrequencyRayleighDamping automatically calculates Rayleigh alphaM and betaK factors
    given a target damping ratio and two control frequencies (such as first and second modes).

    Tcl form:
        Renders inside region definitions as:
        ``-rayleigh <alphaM> <betaK> 0.0 0.0``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        damping = model.damping.frequency_rayleigh(
            damping_factor=0.05,
            f1=0.2,
            f2=20.0,
        )
        print(damping.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__", "get_type"],
    }

    def __init__(
        self,
        damping_factor: float,
        f1: float = 0.2,
        f2: float = 20.0,
        user_name: Optional[str] = None,
    ):
        """Create a frequency-based Rayleigh damping model.

        Args:
            damping_factor: Target damping ratio (between 0.0 and 1.0).
            f1: First control frequency in Hz.
            f2: Second control frequency in Hz.
            user_name: Optional unique name for the damping object.

        Raises:
            ValueError: If frequencies are non-positive or if damping_factor is
                outside `[0.0, 1.0]`.
        """
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
        """Get the damping type name.

        Returns:
            The string "Frequency Rayleigh".
        """
        return "Frequency Rayleigh"

    def to_tcl(self) -> str:
        """Render this frequency Rayleigh damping model as an OpenSees Tcl comment.

        Returns:
            The Tcl string comment.
        """
        return (
            f"# damping rayleigh {self.tag} {self.alphaM} {self.betaK} {self.betaKInit} {self.betaKComm} "
            f"(frequency rayleigh damping with f1 = {self.f1} and f2 = {self.f2} "
            f"and damping factor = {self.damping_factor})"
        )


class UniformDamping(Damping):
    """Uniform viscous damping model spanning a specific frequency band.

    UniformDamping applies a constant damping ratio uniformly between lower and upper
    frequencies. It supports optional activation and deactivation schedules, as well
    as time-series-based amplitude scaling.

    Tcl form:
        ``damping Uniform <tag> <dampingRatio> <freql> <freq2> [-activateTime <Ta>] [-deactivateTime <Td>] [-fact <tsTag>]``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        damping = model.damping.uniform(
            dampingRatio=0.05,
            freql=0.2,
            freq2=20.0,
            Ta=0.0,
            Td=10.0,
        )
        print(damping.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__", "get_type"],
    }

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
        """Create a uniform damping model.

        Args:
            dampingRatio: Constant damping ratio (between 0.0 and 1.0).
            freql: Lower bound of the frequency range in Hz.
            freq2: Upper bound of the frequency range in Hz (must exceed `freql`).
            Ta: Optional activation time in seconds.
            Td: Optional deactivation time in seconds.
            tsTagScaleFactorVsTime: Optional time series tag for scaling damping.
            user_name: Optional unique name for the damping object.

        Raises:
            ValueError: If dampingRatio, freql, or freq2 parameters are invalid.
        """
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
        """Render this uniform damping model as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
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
        """Get the damping type name.

        Returns:
            The string "Uniform".
        """
        return "Uniform"


class SecantStiffnessProportional(Damping):
    """Secant stiffness-proportional viscous damping model.

    SecantStiffnessProportional defines damping proportional to the elements' secant
    stiffness. It supports activation scheduling and time-series-based scaling.

    Tcl form:
        ``damping SecStiff <tag> <damping_factor> [-activateTime <Ta>] [-deactivateTime <Td>] [-fact <tsTag>]``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        damping = model.damping.secant_stiffness_proportional(
            damping_factor=0.05,
            Ta=0.0,
        )
        print(damping.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__", "get_type"],
    }

    def __init__(
        self,
        damping_factor: float,
        Ta: Optional[float] = None,
        Td: Optional[float] = None,
        tsTagScaleFactorVsTime: Optional[int] = None,
        user_name: Optional[str] = None,
    ):
        """Create a secant stiffness-proportional damping model.

        Args:
            damping_factor: Damping ratio proportional to secant stiffness (between 0.0 and 1.0).
            Ta: Optional activation time in seconds.
            Td: Optional deactivation time in seconds.
            tsTagScaleFactorVsTime: Optional time series tag for scaling damping.
            user_name: Optional unique name for the damping object.

        Raises:
            ValueError: If damping_factor is outside `[0.0, 1.0]`.
        """
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
        """Render this secant stiffness-proportional damping model as an OpenSees Tcl command.

        Returns:
            The Tcl command string.
        """
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
        """Get the damping type name.

        Returns:
            The string "Secant Stiffness Proportional".
        """
        return "Secant Stiffness Proportional"
