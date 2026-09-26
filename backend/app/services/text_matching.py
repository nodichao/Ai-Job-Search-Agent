"""Small deterministic text normalization helpers used by filtering/matching."""
import re
import unicodedata


def normalize_term(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", without_marks))


def terms_overlap(left: str, right: str) -> bool:
    a, b = normalize_term(left), normalize_term(right)
    return bool(a and b and (a == b or a in b or b in a))


def token_jaccard(left: str, right: str) -> float:
    a, b = set(normalize_term(left).split()), set(normalize_term(right).split())
    return len(a & b) / len(a | b) if a and b else 0.0
