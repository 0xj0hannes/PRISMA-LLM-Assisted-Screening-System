import re

def normalize_string(s: str) -> str:
    """Normalize string for comparison (lowercase, remove punctuation, collapse
    whitespace).

    Collapsing runs of whitespace to a single space is what makes the key stable
    across databases. BibTeX exporters wrap long fields across lines, so the same
    title arrives from one database as::

        Criminal profiling in digital forensics: Assumptions, challenges and probable solution

    and from another as::

        Criminal Profiling in Digital Forensics: Assumptions, Challenges and\\nProbable Solution

    Punctuation removal alone leaves the embedded newline in place, so the two
    records produce different keys and the duplicate is never detected. Roughly a
    fifth of records in a typical multi-database export carry a wrapped title.
    """
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r'[^\w\s]', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()
