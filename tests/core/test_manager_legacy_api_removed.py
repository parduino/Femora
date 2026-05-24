import inspect

from femora.core.pattern_manager import PatternManager
from femora.core.time_series_manager import TimeSeriesManager


LEGACY_PATTERN_METHODS = {
    "create_pattern",
    "get_pattern",
    "remove_pattern",
    "get_all_patterns",
}

LEGACY_TIME_SERIES_METHODS = {
    "create_time_series",
    "get_time_series",
    "remove_time_series",
    "get_all_time_series",
}

PATTERN_PUBLIC_METHODS = {
    "add",
    "clear",
    "get",
    "get_all",
    "h5drm",
    "multiple_support",
    "plain",
    "remove",
    "set_tag_start",
    "uniform_excitation",
}

TIME_SERIES_PUBLIC_METHODS = {
    "add",
    "clear",
    "constant",
    "get",
    "get_all",
    "linear",
    "path",
    "pulse",
    "ramp",
    "rectangular",
    "remove",
    "set_tag_start",
    "triangular",
    "trig",
}


def _public_methods(cls):
    return {
        name
        for name, member in inspect.getmembers(cls, predicate=inspect.isfunction)
        if not name.startswith("_")
    }


def test_pattern_manager_has_no_legacy_aliases():
    public = _public_methods(PatternManager)
    assert LEGACY_PATTERN_METHODS.isdisjoint(public)
    assert PATTERN_PUBLIC_METHODS.issubset(public)


def test_time_series_manager_has_no_legacy_aliases():
    public = _public_methods(TimeSeriesManager)
    assert LEGACY_TIME_SERIES_METHODS.isdisjoint(public)
    assert TIME_SERIES_PUBLIC_METHODS.issubset(public)
