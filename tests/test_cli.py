from __future__ import annotations

import importlib
import io
import json
import os
import subprocess
import sys
import sysconfig
from pathlib import Path

import pytest

from stable_marriage import cli


class FakeStdin(io.StringIO):
    """StringIO test double with controllable TTY behavior."""

    def __init__(self, text: str, *, is_tty: bool) -> None:
        super().__init__(text)
        self._is_tty = is_tty

    def isatty(self) -> bool:
        return self._is_tty


def make_sample_preferences(path: Path) -> Path:
    payload = {
        "proposers": {
            "A": ["X", "Y"],
            "B": ["Y", "X"],
        },
        "receivers": {
            "X": ["A", "B"],
            "Y": ["B", "A"],
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_cli_prints_matching_to_stdout(tmp_path, capsys):
    input_path = make_sample_preferences(tmp_path / "prefs.json")

    exit_code = cli.main(["--input", str(input_path), "--indent", "0"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out == '{"A":"X","B":"Y"}\n'
    assert json.loads(captured.out) == {"A": "X", "B": "Y"}
    assert captured.err == ""


def test_cli_writes_output_file(tmp_path, capsys):
    input_path = make_sample_preferences(tmp_path / "prefs.json")
    output_path = tmp_path / "matching.json"

    exit_code = cli.main(
        ["--input", str(input_path), "--output", str(output_path), "--indent", "0"]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert output_path.read_text(encoding="utf-8") == '{"A":"X","B":"Y"}\n'
    assert json.loads(output_path.read_text(encoding="utf-8")) == {"A": "X", "B": "Y"}


def test_cli_reads_preferences_from_stdin(capsys, monkeypatch):
    monkeypatch.setattr(
        sys,
        "stdin",
        FakeStdin(
            json.dumps(
                {
                    "proposers": {"A": ["X", "Y"], "B": ["Y", "X"]},
                    "receivers": {"X": ["A", "B"], "Y": ["B", "A"]},
                }
            ),
            is_tty=False,
        ),
    )

    exit_code = cli.main(["--indent", "0"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out == '{"A":"X","B":"Y"}\n'
    assert captured.err == ""


def test_installed_console_script_smoke(tmp_path):
    input_path = make_sample_preferences(tmp_path / "prefs.json")
    script_name = "stable-marriage.exe" if os.name == "nt" else "stable-marriage"
    script_path = Path(sysconfig.get_path("scripts")) / script_name

    assert script_path.exists(), (
        f"Expected installed console script at {script_path}; "
        'run `pip install -e ".[dev]"` before running tests.'
    )

    completed = subprocess.run(
        [str(script_path), "--input", str(input_path), "--indent", "0"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert json.loads(completed.stdout) == {"A": "X", "B": "Y"}
    assert completed.stderr == ""


def test_python_dash_m_works_without_install(tmp_path):
    input_path = make_sample_preferences(tmp_path / "prefs.json")
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src")

    completed = subprocess.run(
        [
            sys.executable,
            "-S",
            "-m",
            "stable_marriage",
            "--input",
            str(input_path),
            "--indent",
            "0",
        ],
        check=False,
        capture_output=True,
        cwd=repo_root,
        env=env,
        text=True,
    )

    assert completed.returncode == 0
    assert json.loads(completed.stdout) == {"A": "X", "B": "Y"}
    assert completed.stderr == ""


def test_importing_package_main_module_does_not_execute_cli(monkeypatch):
    cli_called = False

    def fake_main() -> int:
        nonlocal cli_called
        cli_called = True
        return 0

    monkeypatch.setattr(cli, "main", fake_main)
    sys.modules.pop("stable_marriage.__main__", None)

    package_main = importlib.import_module("stable_marriage.__main__")

    assert package_main.run is not None
    assert cli_called is False


def test_package_main_run_dispatches_to_cli(monkeypatch):
    sys.modules.pop("stable_marriage.__main__", None)
    package_main = importlib.import_module("stable_marriage.__main__")

    monkeypatch.setattr(package_main, "main", lambda: 7)

    assert package_main.run() == 7


@pytest.mark.parametrize(
    "content",
    [
        "{}",
        '{"proposers": {}}',
        "not-json",
        json.dumps(
            {
                "proposers": {"A": "X"},
                "receivers": {"X": ["A"]},
            }
        ),
        json.dumps(
            {
                "proposers": {"A": ["X", ["Y", "Z"]]},
                "receivers": {"X": ["A", "B"], "Y": ["B", "A"]},
            }
        ),
        json.dumps(
            {
                "proposers": {"A": ["X"], "B": ["Y"]},
                "receivers": {"X": ["A", "B"], "Y": ["B", "A"]},
                "couples": {"C1": ["A", "B"]},
            }
        ),
        json.dumps(
            {
                "proposers": {"A": ["X"], "B": ["Y"]},
                "receivers": {"X": ["A", "B"], "Y": ["B", "A"]},
                "metadata": {"source": "fixture"},
            }
        ),
    ],
)
def test_cli_reports_errors(tmp_path, capsys, content):
    input_path = tmp_path / "prefs.json"
    input_path.write_text(content, encoding="utf-8")

    exit_code = cli.main(["--input", str(input_path)])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err


def test_cli_reports_couples_as_library_only_feature(tmp_path, capsys):
    input_path = tmp_path / "prefs.json"
    input_path.write_text(
        json.dumps(
            {
                "proposers": {"A": ["X", "Y"], "B": ["Y", "X"]},
                "receivers": {"X": ["A", "B"], "Y": ["B", "A"]},
                "couples": {"C1": ["A", "B"]},
            }
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(["--input", str(input_path)])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "one-to-one inputs" in captured.err
    assert "stable_marriage.experimental.stable_marriage_with_couples" in captured.err


def test_cli_reports_missing_input_file(capsys, tmp_path):
    input_path = tmp_path / "missing.json"

    exit_code = cli.main(["--input", str(input_path)])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "does not exist" in captured.err


def test_cli_reports_invalid_json_from_stdin(capsys, monkeypatch):
    monkeypatch.setattr(sys, "stdin", FakeStdin("not-json", is_tty=False))

    exit_code = cli.main([])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Standard input is not valid JSON" in captured.err


def test_cli_reports_missing_stdin_input(capsys, monkeypatch):
    monkeypatch.setattr(sys, "stdin", FakeStdin("", is_tty=True))

    exit_code = cli.main([])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "No input provided on stdin" in captured.err


def test_cli_reports_empty_non_tty_stdin(capsys, monkeypatch):
    monkeypatch.setattr(sys, "stdin", FakeStdin("   \n", is_tty=False))

    exit_code = cli.main([])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "No input provided on stdin" in captured.err


def test_cli_requires_top_level_json_object(tmp_path, capsys):
    input_path = tmp_path / "prefs.json"
    input_path.write_text("[]", encoding="utf-8")

    exit_code = cli.main(["--input", str(input_path)])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Preference file must be a JSON object." in captured.err


def test_cli_requires_object_rosters(tmp_path, capsys):
    input_path = tmp_path / "prefs.json"
    input_path.write_text(
        json.dumps({"proposers": [], "receivers": {"X": ["A"]}}), encoding="utf-8"
    )

    exit_code = cli.main(["--input", str(input_path)])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "'proposers' and 'receivers' must be JSON objects." in captured.err


def test_cli_reports_error_when_output_directory_missing(tmp_path, capsys):
    input_path = make_sample_preferences(tmp_path / "prefs.json")
    output_path = tmp_path / "missing-dir" / "matching.json"

    exit_code = cli.main(
        ["--input", str(input_path), "--output", str(output_path), "--indent", "2"]
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Error:" in captured.err


def test_cli_reports_error_when_input_cannot_be_read(tmp_path, capsys, monkeypatch):
    input_path = tmp_path / "prefs.json"
    input_path.write_text("{}", encoding="utf-8")

    original_read_text = Path.read_text

    def raising_read_text(self: Path, *args, **kwargs) -> str:
        if self == input_path:
            raise PermissionError("permission denied")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", raising_read_text)

    exit_code = cli.main(["--input", str(input_path)])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Unable to read input file" in captured.err
    assert "permission denied" in captured.err


def test_cli_reports_error_when_output_path_is_directory(tmp_path, capsys):
    input_path = make_sample_preferences(tmp_path / "prefs.json")
    output_path = tmp_path / "output-dir"
    output_path.mkdir()

    exit_code = cli.main(
        ["--input", str(input_path), "--output", str(output_path), "--indent", "2"]
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Unable to write matching" in captured.err


def test_cli_pretty_prints_for_positive_indent(tmp_path, capsys):
    input_path = make_sample_preferences(tmp_path / "prefs.json")

    exit_code = cli.main(["--input", str(input_path), "--indent", "2"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out.startswith('{\n  "A": "X",\n')
