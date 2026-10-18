"""
Visual Privacy Redaction Sub-Package.
Provides Dual-Pass Gemini VLM spatial detection, coordinate denormalization,
and deterministic Pillow solid-black masking.
"""
from .engine import (
    call_gemini_with_retry,
    get_genai_client,
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
    "get_genai_client",
    "load_image_from_source",
    "process_review_image",
]
