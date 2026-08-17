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


def test_wrapped_title_from_bibtex_export_is_deduplicated():
    """BibTeX exporters wrap long fields; the same paper must still match.

    Regression test: normalization used to strip punctuation but preserve
    whitespace, so an embedded newline survived into the key and the two
    records looked distinct. About a fifth of records in a multi-database
    export carry a wrapped title, so this silently leaked duplicates into the
    screened corpus.
    """
    scopus_style = "Criminal profiling in digital forensics: Assumptions, challenges and probable solution"
    wos_style = (
        "Criminal Profiling in Digital Forensics: Assumptions, Challenges and\n"
        "Probable Solution"
    )
    records = [
        _rec(id="canon", title=scopus_style, doi="10.1/x", year="2018",
             authors="Balogun, Adedayo M., Zuva, Tranos"),
        _rec(id="dupe", title=wos_style, doi="", year="2018",
             authors="Balogun, Adedayo M., Zuva, Tranos"),
    ]
    result = deduplicate_records(records)
    assert [r.id for r in result] == ["canon"]
    assert records[1].is_duplicate is True
    assert records[1].duplicate_of == "canon"


def test_normalize_string_collapses_all_whitespace():
    assert normalize_string("A  double   spaced\ttitle") == "a double spaced title"
    assert normalize_string("wrapped\nacross\nlines") == "wrapped across lines"
    assert normalize_string("Same Title") == normalize_string("Same\nTitle")


def test_wrapped_author_field_still_matches():
    """The author half of the key is normalized the same way as the title.

    The wrap here falls *inside* the first author segment, so the key only
    matches if the author string is whitespace-collapsed too -- exporters that
    write "Babko-Malaya Olga" across a line break would otherwise defeat the
    fallback key even when the title matches.
    """
    records = [
        _rec(id="canon", title="Shared Title", doi="", year="2021",
             authors="Babko-Malaya Olga, Cathey, Rebecca"),
        _rec(id="dupe", title="Shared Title", doi="", year="2021",
             authors="Babko-Malaya\nOlga, Cathey, Rebecca"),
    ]
    result = deduplicate_records(records)
    assert [r.id for r in result] == ["canon"]


def test_distinct_papers_are_not_merged_by_the_collapse():
    """Collapsing whitespace must not make genuinely different titles collide."""
    records = [
        _rec(id="a", title="Profiling the attacker", doi="", year="2020",
             authors="Doe, Jane"),
        _rec(id="b", title="Profiling the attackers", doi="", year="2020",
             authors="Doe, Jane"),
    ]
    result = deduplicate_records(records)
    assert {r.id for r in result} == {"a", "b"}
