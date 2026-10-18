"""
Agentic Grounded Privacy & Compliance Pipeline sub-package.
Provides high-recall spatial visual privacy redaction, deterministic solid black masking,
additive residual leak recovery, and canonical evaluation benchmarking.
"""
from .engine import (
    call_gemini_with_retry,
    load_image_from_source,
    process_review_image,
)
from .masks import apply_solid_black_masks, denormalize_box
from .schemas import BoundingBox, RedactionPlan, ResidualAudit

__all__ = [
    "BoundingBox",
    "RedactionPlan",
    "ResidualAudit",
    "apply_solid_black_masks",
    "call_gemini_with_retry",
    "denormalize_box",
    "load_image_from_source",
    "process_review_image",
]
