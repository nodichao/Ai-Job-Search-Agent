"""Small deterministic text normalization helpers used by filtering/matching."""
import re
import unicodedata
from enum import StrEnum


class TitleRelation(StrEnum):
    EXACT = "EXACT"
    PARTIAL = "PARTIAL"
    NO_OVERLAP = "NO_OVERLAP"


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


def compare_titles(left: str, right: str) -> TitleRelation:
    """Compare titles lexically without treating a shared generic token as equivalence.

    An exact normalized title is a match. Any non-exact token overlap is only
    partial evidence; callers must not promote it to SATISFIED. No shared tokens
    is a lexical conflict for an explicit preferred-title criterion.
    """
    normalized_left = normalize_term(left)
    normalized_right = normalize_term(right)
    if normalized_left and normalized_left == normalized_right:
        return TitleRelation.EXACT
    left_tokens = set(normalized_left.split())
    right_tokens = set(normalized_right.split())
    if left_tokens & right_tokens:
        return TitleRelation.PARTIAL
    return TitleRelation.NO_OVERLAP
