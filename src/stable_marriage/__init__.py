"""Stable marriage solver package."""

from importlib.metadata import PackageNotFoundError, version

from .core import stable_marriage
from .types import Matching

try:
    __version__ = version("stable-marriage")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"

__all__ = ["Matching", "__version__", "stable_marriage"]
