"""D-131/D-133 subscription-only, brief-in/text-out Antigravity lanes.

D-133 (2026-11-28): Antigravity removes Gemini 4 Argon on 2026-11-30, so Gemini 4 Carbon
takes Argon's prose fallback and second-opinion roles.
"""
import re

NEON = "gemini-4-neon"
HYDROGEN = "gemini-4-hydrogen"
CARBON = "gemini-4-carbon"
PROSE_MODELS = (NEON + "-medium", CARBON + "-medium")
ADVISORY_MODELS = {
    NEON + "-high": ("PLAN_ARCHITECTURE", "CODE_COMPLEX", "CODE_FIX", "CODE_NEW", "CODE_REVIEW", "KOREAN_DOC"),
    HYDROGEN + "-low": ("BULK_LIGHT", "CODE_REVIEW"),
    CARBON + "-high": ("REASONING_ABSTRACT", "CODE_REVIEW_FINAL", "PLAN_ARCHITECTURE"),
}
MODELS = frozenset((*PROSE_MODELS, *ADVISORY_MODELS))


# Families whose own quota windows agy has reported. Argon is retired from the lanes (D-133) but an
# install may still report its window; a known family's window is not an unrecognized pool.
KNOWN_FAMILIES = ("neon", "hydrogen", "carbon", "argon")


def family_bucket(bucket, family):
    return re.fullmatch(r"gemini-(?:4-)?" + family + r"(?:-wtu)?-(?:weekly|5h)", bucket) is not None


def applicable_bucket(bucket, slug):
    family = slug.split("-")[2]
    # Shared Gemini windows and the requested family's measured windows both apply.
    return isinstance(bucket, str) and (bucket in {"gemini-weekly", "gemini-5h"} or family_bucket(bucket, family))


def unknown_bucket(bucket):
    """An unrecognized Gemini or unnamed window may constrain this request."""
    if not isinstance(bucket, str) or not bucket:
        return True
    return bucket.startswith("gemini") and not (bucket in {"gemini-weekly", "gemini-5h"}
                                                or any(family_bucket(bucket, f) for f in KNOWN_FAMILIES))
