"""Tests for src.reporting.generate_report (CSV export + PRISMA stats)."""
import json

import pandas as pd

import src.reporting as reporting


# A reporting config with two criteria, injected so the test does not depend on
# the contents of the repository's criteria.json.
REPORT_CONFIG = {
    "CRITERIA": {
        "IC1": {"name": "c1"},
        "IC2": {"name": "c2"},
    }
}


def _write_dataset(path):
    data = {
        "records": [
            {"id": "a", "title": "Kept", "year": "2024", "authors": "Doe",
             "doi": "10.1/a", "is_duplicate": False},
            {"id": "b", "title": "Dropped dup", "is_duplicate": True,
             "duplicate_of": "a"},
        ],
        "screening_results": {
            "a": {
                "record_id": "a",
                "decision": "Include",
                "unmet_criteria": "",
                "criteria": {
                    "IC1": {"score": 0.9, "evidences": ["e1", "e2"],
                            "rationale": "r1"},
                    "IC2": {"score": 0.8, "evidences": [], "rationale": "r2"},
                },
            }
        },
    }
    path.write_text(json.dumps(data), encoding="utf-8")


def test_report_emits_criterion_column_triplets(tmp_path, monkeypatch):
    monkeypatch.setattr(reporting, "load_config", lambda: REPORT_CONFIG)
    src = tmp_path / "in.json"
    out = tmp_path / "out.csv"
    _write_dataset(src)

    reporting.generate_report(str(src), str(out))

    df = pd.read_csv(out)
    for key in ("IC1", "IC2"):
        for suffix in ("Score", "Evidences", "Rationale"):
            assert f"{key}_{suffix}" in df.columns


def test_report_excludes_duplicates_and_keeps_canonical(tmp_path, monkeypatch):
    monkeypatch.setattr(reporting, "load_config", lambda: REPORT_CONFIG)
    src = tmp_path / "in.json"
    out = tmp_path / "out.csv"
    _write_dataset(src)

    reporting.generate_report(str(src), str(out))

    df = pd.read_csv(out)
    assert list(df["ID"]) == ["a"]
    assert df.loc[0, "Decision"] == "Include"
    # Evidence lists are joined with "; ".
    assert df.loc[0, "IC1_Evidences"] == "e1; e2"


def test_missing_input_file_is_handled(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(reporting, "load_config", lambda: REPORT_CONFIG)
    reporting.generate_report(str(tmp_path / "nope.json"),
                              str(tmp_path / "out.csv"))
    assert "not found" in capsys.readouterr().out.lower()
