import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode, author
from typing import List, Dict, Any
from .models import Record
from .utils import normalize_string
import re

def customizations(record):
    """Customization function for bibtexparser."""
    record = convert_to_unicode(record)
    record = author(record)
    return record

def load_bibtex(file_path: str) -> List[Record]:
    with open(file_path, 'r', encoding='utf-8') as bibtex_file:
        parser = BibTexParser()
        parser.customization = customizations
        bib_database = bibtexparser.load(bibtex_file, parser=parser)
    
    records = []
    for entry in bib_database.entries:
        # Normalize fields
        title = entry.get('title', '').strip()
        abstract = entry.get('abstract', '').strip()
        doi = entry.get('doi', '').strip()
        
        # Handle authors list to string
        authors_list = entry.get('author', [])
        if isinstance(authors_list, list):
            authors_str = ", ".join(authors_list)
        else:
            authors_str = str(authors_list)

        # Generate a unique ID if not present (prefer BibTeX ID)
        record_id = entry.get('ID', '')
        
        record = Record(
            id=record_id,
            title=title,
            abstract=abstract,
            authors=authors_str,
            year=entry.get('year', '').strip(),
            doi=doi,
            source_file=file_path,
            raw_data=entry,
            normalized_title=normalize_string(title)
        )
        records.append(record)
    return records
