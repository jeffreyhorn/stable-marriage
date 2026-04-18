"""Allow execution via ``python -m stable_marriage``."""

from __future__ import annotations

from .cli import main


def run() -> int:
    """Dispatch the package module entrypoint to the CLI implementation."""

    return main()


if __name__ == "__main__":  # pragma: no cover - exercised via subprocess tests
    raise SystemExit(run())
