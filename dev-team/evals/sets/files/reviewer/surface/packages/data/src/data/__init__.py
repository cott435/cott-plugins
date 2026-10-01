"""The data package's public surface: `fetch_bars` and `clean_bars`.

Importing `data` loads no section and no third-party package: each public name is
imported from its section the first time it is asked for.
"""

from __future__ import annotations

from importlib import import_module
from types import MappingProxyType

__all__ = ["clean_bars", "fetch_bars"]

_SOURCES = MappingProxyType(
    {
        "clean_bars": "data.clean.api",
        "fetch_bars": "data.ingest.client",
    }
)


def __getattr__(name: str) -> object:
    """Import a public name from its section on first access."""
    if name not in _SOURCES:
        raise AttributeError(f"module 'data' has no attribute {name!r}")
    value = getattr(import_module(_SOURCES[name]), name)
    globals()[name] = value
    return value
