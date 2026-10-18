"""
Translucid: Zero-Trust Selective Transparency Engine for Whistleblower & Dispute Evidence.
Provides dual-pass additive visual PII redaction, untrusted-worker coordinate sandboxing,
deterministic statutory claim neutralization, and canonical benchmark evaluation.
"""
from translucid.eval.benchmark import run_benchmark
from translucid.text.diff import export_aligned_diff_artifacts, generate_unified_diff
from translucid.text.sanitize import (
    moderate_reviews_with_gemini,
    normalize_unicode_text,
    sanitize_review_text,
)
from translucid.visual import (
    BoundingBox,
    RedactionPlan,
    ResidualAudit,
    apply_solid_black_masks,
    call_gemini_with_retry,
    denormalize_box,
    load_image_from_source,
    process_review_image,
)

__version__ = "0.1.0"

__all__ = [
    "BoundingBox",
    "RedactionPlan",
    "ResidualAudit",
    "apply_solid_black_masks",
    "call_gemini_with_retry",
    "denormalize_box",
    "export_aligned_diff_artifacts",
    "generate_unified_diff",
    "load_image_from_source",
    "moderate_reviews_with_gemini",
    "normalize_unicode_text",
    "process_review_image",
    "run_benchmark",
    "sanitize_review_text",
]
