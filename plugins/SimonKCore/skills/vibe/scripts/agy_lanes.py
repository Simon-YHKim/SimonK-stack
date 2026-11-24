"""D-131 subscription-only, brief-in/text-out Antigravity lanes."""
import re

NEON = "gemini-4-neon"
HYDROGEN = "gemini-4-hydrogen"
ARGON = "gemini-4-argon"
PROSE_MODELS = (NEON + "-medium", ARGON + "-high")
ADVISORY_MODELS = {
    NEON + "-high": ("PLAN_ARCHITECTURE", "CODE_COMPLEX", "CODE_FIX", "CODE_NEW", "CODE_REVIEW", "KOREAN_DOC"),
    HYDROGEN + "-low": ("BULK_LIGHT", "CODE_REVIEW"),
    ARGON + "-high": ("REASONING_ABSTRACT", "CODE_REVIEW_FINAL", "PLAN_ARCHITECTURE"),
}
MODELS = frozenset((*PROSE_MODELS, *ADVISORY_MODELS))


def applicable_bucket(bucket, slug):
    family = slug.split("-")[2]
    # Shared Gemini windows and the requested family's measured windows both apply.
    return isinstance(bucket, str) and (bucket in {"gemini-weekly", "gemini-5h"} or
            re.fullmatch(r"gemini-(?:4-)?" + family + r"(?:-wtu)?-(?:weekly|5h)", bucket) is not None)


def unknown_bucket(bucket):
    """An unrecognized Gemini or unnamed window may constrain this request."""
    if not isinstance(bucket, str) or not bucket:
        return True
    return bucket.startswith("gemini") and not any(applicable_bucket(bucket, slug) for slug in MODELS)
