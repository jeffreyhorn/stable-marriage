from __future__ import annotations

import json
from pathlib import Path

import pytest

from stable_marriage import cli


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
    path.write_text(json.dumps(payload))
    return path


def test_cli_prints_matching_to_stdout(tmp_path, capsys):
    input_path = make_sample_preferences(tmp_path / "prefs.json")

    exit_code = cli.main(["--input", str(input_path), "--indent", "0"])

    assert exit_code == 0
    captured = capsys.readouterr()
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
    assert json.loads(output_path.read_text()) == {"A": "X", "B": "Y"}


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
    ],
)
def test_cli_reports_errors(tmp_path, capsys, content):
    input_path = tmp_path / "prefs.json"
    input_path.write_text(content)

    exit_code = cli.main(["--input", str(input_path)])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err


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
