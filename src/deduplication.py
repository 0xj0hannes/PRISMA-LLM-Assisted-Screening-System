from typing import List, Dict
from .models import Record

def deduplicate_records(records: List[Record]) -> List[Record]:
    """
    Deduplicate records based on:
    1. DOI (exact match)
    2. Title + Year + First Author (exact match of normalized string)
    """
    # Canonical records map: {canonical_id: record}
    canonical_records: Dict[str, Record] = {}
    
    # Indexes for fast lookup
    seen_dois: Dict[str, str] = {} # doi -> canonical_id
    seen_tya: Dict[str, str] = {} # title_year_author_key -> canonical_id
    
    deduplicated_count = 0
    
    for record in records:
        is_duplicate = False
        canonical_id = None
        
        # 1. DOI Check
        if record.doi:
            clean_doi = record.doi.lower().strip()
            if clean_doi in seen_dois:
                is_duplicate = True
                canonical_id = seen_dois[clean_doi]
                reason = f"DOI match ({clean_doi})"
        
        # 2. Title + Year + First Author Check (High Confidence)
        if not is_duplicate:
            first_author = record.authors.split(',')[0].strip().lower() if record.authors else ""
            tya_key = f"{record.normalized_title}|{record.year}|{first_author}"
            if tya_key in seen_tya:
                is_duplicate = True
                canonical_id = seen_tya[tya_key]
                reason = "Title + Year + Author match"

        if is_duplicate:
            print(f"  Duplicate found: \"{record.title[:60]}...\"")
            print(f"    Reason: {reason}")
            print(f"    Duplicate of: {canonical_id}")
            record.is_duplicate = True
            record.duplicate_of = canonical_id
            deduplicated_count += 1
        else:
            # New canonical record
            canonical_records[record.id] = record
            
            # Update indexes
            if record.doi:
                seen_dois[record.doi.lower().strip()] = record.id
            
            first_author = record.authors.split(',')[0].strip().lower() if record.authors else ""
            tya_key = f"{record.normalized_title}|{record.year}|{first_author}"
            seen_tya[tya_key] = record.id
            
    return list(canonical_records.values())
