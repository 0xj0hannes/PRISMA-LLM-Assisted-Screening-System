import re

def normalize_string(s: str) -> str:
    """Normalize string for comparison (lowercase, remove punctuation)."""
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r'[^\w\s]', '', s)
    return s.strip()
