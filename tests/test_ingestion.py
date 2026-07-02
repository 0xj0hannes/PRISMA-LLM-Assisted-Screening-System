"""Tests for src.ingestion.load_bibtex."""
from src.ingestion import load_bibtex

BIBTEX = r"""
@article{doe2024,
  title    = {A Study of {Human} Behaviour},
  author   = {Doe, Jane and Smith, John},
  year     = {2024},
  doi      = {10.1000/example},
  abstract = {An abstract about behaviour.}
}

@inproceedings{roe2023,
  title  = {Another Paper},
  author = {Roe, Richard},
  year   = {2023}
}
"""


def test_load_bibtex_parses_all_entries(tmp_path):
    bib = tmp_path / "refs.bib"
    bib.write_text(BIBTEX, encoding="utf-8")

    records = load_bibtex(str(bib))

    assert len(records) == 2
    by_id = {r.id: r for r in records}
    assert set(by_id) == {"doe2024", "roe2023"}


def test_fields_are_extracted_and_normalized(tmp_path):
    bib = tmp_path / "refs.bib"
    bib.write_text(BIBTEX, encoding="utf-8")

    rec = {r.id: r for r in load_bibtex(str(bib))}["doe2024"]

    assert rec.year == "2024"
    assert rec.doi == "10.1000/example"
    assert rec.abstract == "An abstract about behaviour."
    # Authors are flattened to a single comma-separated string.
    assert "Doe" in rec.authors and "Smith" in rec.authors
    # normalized_title is lowercased and stripped of punctuation/braces.
    assert rec.normalized_title == "a study of human behaviour"


def test_missing_optional_fields_default_safely(tmp_path):
    bib = tmp_path / "refs.bib"
    bib.write_text(BIBTEX, encoding="utf-8")

    rec = {r.id: r for r in load_bibtex(str(bib))}["roe2023"]

    assert rec.abstract == ""
    assert rec.doi == ""
    assert rec.title == "Another Paper"
