"""Fiber-section public API."""

from femora.core.section_manager import SectionManager
from femora.components.section.fiber.element import FiberElement
from femora.components.section.fiber.layers import CircularLayer, StraightLayer
from femora.components.section.fiber.patches import CircularPatch, QuadrilateralPatch, RectangularPatch
from femora.components.section.fiber.rc import RCSection
from femora.components.section.fiber.section import FiberSection

SectionManager.register_section_type("Fiber", FiberSection)
SectionManager.register_section_type("RC", RCSection)

__all__ = [
    "FiberElement",
    "FiberSection",
    "RCSection",
    "RectangularPatch",
    "QuadrilateralPatch",
    "CircularPatch",
    "StraightLayer",
    "CircularLayer",
]
