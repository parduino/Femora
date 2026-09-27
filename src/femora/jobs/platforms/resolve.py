"""Resolve public platform names without putting provider logic in submit()."""

from collections.abc import Mapping


def _tacc(settings):
    from .tacc_remote import TACCPlatform
    from .tacc import TACCSettings

    options = dict(settings)
    connection = {}
    for key in ("app_id", "app_version", "base_url", "storage_system", "input_directory"):
        if key in options:
            connection[key] = options.pop(key)
    if not isinstance(connection.get("app_id"), str) or not connection["app_id"].strip():
        raise ValueError("TACC settings require a nonempty app_id")
    for key, value in connection.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"TACC setting {key} must be a nonempty string")
    try:
        resources = TACCSettings(**options)
    except TypeError as error:
        raise ValueError(f"Invalid TACC settings: {error}") from None
    for key in ("system", "queue", "allocation"):
        value = getattr(resources, key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"TACC setting {key} must be a nonempty string")
    for key in ("nodes", "cores_per_node", "minutes"):
        value = getattr(resources, key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"TACC setting {key} must be a positive integer")
    return TACCPlatform.login(**connection), resources


_FACTORIES = {"tacc": _tacc}


def resolve_platform(platform, settings):
    if not isinstance(platform, str):
        return platform, settings
    if platform not in _FACTORIES:
        raise ValueError(f"Unknown platform {platform!r}; supported names: {', '.join(_FACTORIES)}")
    if not isinstance(settings, Mapping):
        raise TypeError("Named platforms require a settings dictionary")
    return _FACTORIES[platform](settings)
