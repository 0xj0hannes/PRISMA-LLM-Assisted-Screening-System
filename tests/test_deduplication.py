"""Tests for src.deduplication.deduplicate_records."""
from src.deduplication import deduplicate_records
from src.utils import normalize_string

from tests.conftest import make_record


def _rec(**kw):
    rec = make_record(**kw)
    rec.normalized_title = normalize_string(rec.title)
    return rec


def test_no_duplicates_passes_all_through():
    records = [
        _rec(id="a", title="First", doi="10.1/a"),
        _rec(id="b", title="Second", doi="10.1/b"),
    ]
    result = deduplicate_records(records)
    assert {r.id for r in result} == {"a", "b"}
    assert all(not r.is_duplicate for r in result)


def test_exact_doi_match_is_deduplicated():
    records = [
        _rec(id="canon", title="Original", doi="10.1/SAME"),
        _rec(id="dupe", title="Different title entirely", doi="10.1/same"),
    ]
    result = deduplicate_records(records)
    # Only the canonical record survives downstream.
    assert [r.id for r in result] == ["canon"]
    # The duplicate is flagged on the original list, pointing at the canonical id.
    assert records[1].is_duplicate is True
    assert records[1].duplicate_of == "canon"


def test_title_year_author_match_without_doi():
    records = [
        _rec(id="canon", title="A Shared Title", doi="", year="2020",
             authors="Doe, Jane"),
        _rec(id="dupe", title="A Shared Title!", doi="", year="2020",
             authors="Doe, Jane and Other, A"),
    ]
    result = deduplicate_records(records)
    assert [r.id for r in result] == ["canon"]
    assert records[1].is_duplicate is True
    assert records[1].duplicate_of == "canon"


def test_same_title_different_year_is_not_duplicate():
    records = [
        _rec(id="a", title="A Shared Title", doi="", year="2019",
             authors="Doe, Jane"),
        _rec(id="b", title="A Shared Title", doi="", year="2020",
             authors="Doe, Jane"),
    ]
    result = deduplicate_records(records)
    assert {r.id for r in result} == {"a", "b"}
