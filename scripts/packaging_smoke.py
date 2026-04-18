from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run_command(command: list[str], cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Run a subprocess and raise a useful error if it fails."""

    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        cwd=cwd,
        env=env,
        text=True,
    )
    if completed.returncode != 0:
        details = completed.stdout + completed.stderr
        raise RuntimeError(f"Command failed: {' '.join(command)}\n{details}")
    return completed


def main() -> int:
    """Verify installed-package typing and module entrypoint behavior."""

    repo_root = Path(__file__).resolve().parents[1]
    clean_env = os.environ.copy()
    clean_env.pop("PYTHONPATH", None)
    clean_env.pop("MYPYPATH", None)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        consumer = temp_path / "typed_consumer.py"
        consumer.write_text(
            "\n".join(
                [
                    "from stable_marriage import stable_marriage",
                    "",
                    'proposers = {"A": ["X", "Y"], "B": ["Y", "X"]}',
                    'receivers = {"X": ["A", "B"], "Y": ["B", "A"]}',
                    "result = stable_marriage(proposers, receivers)",
                    "reveal_type(result)",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        mypy = run_command(
            [sys.executable, "-m", "mypy", str(consumer)],
            cwd=temp_path,
            env=clean_env,
        )
        if 'Revealed type is "dict[str, str]"' not in mypy.stdout:
            raise RuntimeError(
                "Installed package was not treated as precisely typed.\n"
                f"{mypy.stdout}{mypy.stderr}"
            )

        completed = run_command(
            [
                sys.executable,
                "-m",
                "stable_marriage",
                "--input",
                str(repo_root / "data" / "sample_preferences.json"),
                "--indent",
                "0",
            ],
            cwd=temp_path,
            env=clean_env,
        )
        if json.loads(completed.stdout) != {"A": "X", "B": "Z", "C": "Y"}:
            raise RuntimeError(
                "Package entrypoint returned an unexpected matching.\n"
                f"{completed.stdout}{completed.stderr}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
