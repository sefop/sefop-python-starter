import json
from pathlib import Path

import pytest

import cli


def _write_request(data_root, request_id: str, payload: dict) -> None:
    folder = data_root / request_id
    folder.mkdir(parents=True)
    (folder / "data.json").write_text(json.dumps(payload), encoding="utf-8")


def test__cli_main__on_success__prints_only_output_path_and_writes_solution(tmp_path, monkeypatch, capsys):
    # ARRANGE — Settings.folder_path/output_folder_path are relative ("data"/"output"),
    # so chdir into a temp directory to keep the run isolated from the real repo.
    monkeypatch.chdir(tmp_path)
    _write_request(
        tmp_path / "data",
        "1",
        {
            "requestId": "1",
            "maxWeightKg": 1.0,
            "maxBudgetUsd": 5.0,
            "products": [{"name": "banana", "priceUsd": 1.00, "weightKg": 0.50, "calories": 100}],
        },
    )
    monkeypatch.setattr("sys.argv", ["cli", "1"])

    # ACT
    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    # ASSERT
    assert exc_info.value.code == 0
    printed = capsys.readouterr().out.strip()
    assert printed.startswith("Results written to ")
    run_folder = Path(printed.removeprefix("Results written to ").strip())
    assert (run_folder / "solution.csv").exists()
    assert (run_folder / "input.json").exists()


def test__cli_main__given_data_and_output_folder_flags__writes_under_those_folders_without_chdir(
    tmp_path, monkeypatch, capsys
):
    # ARRANGE — data and output folders live outside any "data"/"output" convention
    # entirely, to prove the flags are actually used instead of Settings' defaults.
    data_folder = tmp_path / "custom_data"
    output_folder = tmp_path / "custom_output"
    _write_request(
        data_folder,
        "1",
        {
            "requestId": "1",
            "maxWeightKg": 1.0,
            "maxBudgetUsd": 5.0,
            "products": [{"name": "banana", "priceUsd": 1.00, "weightKg": 0.50, "calories": 100}],
        },
    )
    monkeypatch.setattr(
        "sys.argv",
        ["cli", "1", "--data-folder", str(data_folder), "--output-folder", str(output_folder)],
    )

    # ACT
    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    # ASSERT
    assert exc_info.value.code == 0
    printed = capsys.readouterr().out.strip()
    run_folder = Path(printed.removeprefix("Results written to ").strip())
    assert run_folder.is_relative_to(output_folder)
    assert (run_folder / "solution.csv").exists()


def test__cli_main__on_failure__exits_nonzero_and_writes_no_csv(tmp_path, monkeypatch, capsys):
    # ARRANGE — budget too low for the only available product, so no recommendation exists
    monkeypatch.chdir(tmp_path)
    _write_request(
        tmp_path / "data",
        "1",
        {
            "requestId": "1",
            "maxWeightKg": 1.0,
            "maxBudgetUsd": 0.01,
            "products": [{"name": "banana", "priceUsd": 1.00, "weightKg": 0.50, "calories": 100}],
        },
    )
    monkeypatch.setattr("sys.argv", ["cli", "1"])

    # ACT
    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    # ASSERT
    assert exc_info.value.code == 1
    printed = capsys.readouterr().out.strip()
    run_folder = Path(printed.removeprefix("Results written to ").strip())
    assert not (run_folder / "solution.csv").exists()
    assert "FAILURE" in (run_folder / "status.txt").read_text(encoding="utf-8")
