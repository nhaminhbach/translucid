"""
Dual-Pass Privacy Redaction Engine.
Orchestrates high-recall spatial detection and additive residual verification
using Google GenAI (Gemini API or Vertex AI Enterprise), with automatic exponential backoff on HTTP 429.
"""
import io
import os
import time
import urllib.request
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types
from google.genai.errors import ClientError
from PIL import Image

from .masks import apply_solid_black_masks
from .schemas import RedactionPlan, ResidualAudit


def get_genai_client(api_key: str | None = None) -> genai.Client:
    """
    Initializes a Google GenAI client supporting both Vertex AI Enterprise
    (GOOGLE_GENAI_USE_VERTEXAI=true, zero data retention) and Gemini API keys.
    """
    use_vertex = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in ("1", "true", "yes")
    project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT_ID")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
    resolved_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if use_vertex and project and not resolved_key:
        return genai.Client(vertexai=True, project=project, location=location)
    if resolved_key:
        return genai.Client(api_key=resolved_key)
    if project:
        return genai.Client(vertexai=True, project=project, location=location)
    return genai.Client()


def call_gemini_with_retry(
    client: genai.Client,
    model: str,
    contents: list,
    config: types.GenerateContentConfig,
    max_retries: int = 4,
    initial_delay: float = 2.5
) -> Any:
    """
    Executes a Gemini content generation call with exponential backoff retry
    to gracefully handle HTTP 429 (RESOURCE_EXHAUSTED) on high-throughput runs,
    with automatic fallback if a regional publisher model is unavailable.
    """
    delay = initial_delay
    last_err: Exception | None = None
    candidate_models = [model]
    for alt in ("gemini-2.5-flash", "gemini-2.0-flash"):
        if alt not in candidate_models:
            candidate_models.append(alt)

    for m in candidate_models:
        for attempt in range(max_retries + 1):
            try:
                return client.models.generate_content(
                    model=m,
                    contents=contents,
                    config=config
                )
            except ClientError as e:
                last_err = e
                if "404" in str(e) or "NOT_FOUND" in str(e):
                    # Regional model not found, try next candidate model
                    break
                if ("429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)) and attempt < max_retries:
                    print(f"  [Visual Redactor Rate-Limit] 429 detected. Backing off for {delay:.1f}s (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(delay)
                    delay *= 2.0
                    continue
                raise
            except Exception as e:
                last_err = e
                if attempt < max_retries:
                    time.sleep(delay)
                    delay *= 1.5
                    continue
                raise

    if last_err:
        raise last_err


def load_image_from_source(source: str | Path | Image.Image) -> Image.Image:
    """Loads an image from local filesystem path, remote HTTP URL, or PIL Image."""
    if isinstance(source, Image.Image):
        return source.copy()

    source_str = str(source).strip()
    if source_str.startswith(("http://", "https://")):
        req = urllib.request.Request(
            source_str,
            headers={"User-Agent": "Nhaminhbach-VisualRedactor/1.0"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        return Image.open(io.BytesIO(data))

    p = Path(source)
    if not p.exists():
        raise FileNotFoundError(f"Source image not found: {p}")
    return Image.open(p)


def process_review_image(
    input_path: str | Path | Image.Image,
    output_path: str | Path,
    client: genai.Client | None = None,
    model: str = "gemini-3.5-flash-lite",
    padding: int = 5
) -> dict[str, Any]:
    """
    Executes automated dual-pass visual privacy redaction on a review proof asset:
    1. Pass 1: High-recall spatial token bounding box detection.
    2. Pillow: Solid black rectangular masking with adaptive padding.
    3. Pass 2: Additive residual leak audit with additive recovery (capped at 1 retry).
    4. WebP encoding (Quality 90, Method 6).
    """
    t0 = time.time()
    effective_client = client or get_genai_client()
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    with load_image_from_source(input_path) as raw_image:
        working_img = raw_image.copy()

    # Pass 1: Grounded Spatial Masker
    pass1_prompt = (
        "You are an automated privacy redactor for Vietnamese rental dispute proofs (Nhaminhbach).\n"
        "Detect bounding boxes [ymin, xmin, ymax, xmax] (0-1000 normalized) covering:\n"
        "1. Chat UI headers (Zalo, Messenger, SMS, Telegram): contact display names, phone numbers, and profile avatars.\n"
        "2. Bank transaction receipts: account numbers and recipient real names.\n"
        "3. Identity documents: citizen ID (CCCD/CMND) numbers, birth dates, home addresses, signatures.\n"
        "4. Exterior/entrance photos: civilian faces, pedestrian portraits, and vehicle license plates.\n\n"
        "NEGATIVE INVARIANTS (DO NOT MASK):\n"
        "- Dispute chat dialogue messages, timestamps, fee breakdowns, and utility tariffs (e.g. 4k/kWh).\n"
        "- Physical room defects (mold, peeling walls, broken locks, water meters, cracked tiles, clogged drains).\n"
        "- Commercial rental brand names and operator logos (e.g. 90land, Nhà Xinh, Hoàng Long House).\n"
        "- Faces or models appearing on mass-produced commercial advertising posters, appliance branding stickers, or product packaging.\n"
        "If the image contains only room defect or building evidence, return is_clean = true and sensitive_boxes = []."
    )

    p1_response = call_gemini_with_retry(
        client=effective_client,
        model=model,
        contents=[working_img, pass1_prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RedactionPlan,
            temperature=0.0
        )
    )

    plan: RedactionPlan
    if hasattr(p1_response, "parsed") and p1_response.parsed:
        plan = p1_response.parsed
    else:
        plan = RedactionPlan.model_validate_json(p1_response.text)

    pass1_boxes = [{"box_2d": list(b.box_2d), "label": b.label} for b in plan.sensitive_boxes]

    # Fast Path: Clean defect image with zero sensitive regions
    if plan.is_clean or not plan.sensitive_boxes:
        raw_rgb = working_img.convert("RGB")
        raw_rgb.save(out_p, "WEBP", quality=90, method=6)
        return {
            "status": "clean",
            "boxes_applied": 0,
            "had_leak_recovery": False,
            "pass1_boxes": [],
            "pass2_leak_boxes": [],
            "latency_ms": round((time.time() - t0) * 1000, 1),
            "path": str(out_p)
        }

    # Apply Pass 1 Masks
    active_boxes = [b.box_2d for b in plan.sensitive_boxes]
    masked_img = apply_solid_black_masks(working_img, active_boxes, padding=padding)

    # Pass 2: Additive Residual Verification Audit
    pass2_prompt = (
        "Inspect this masked dispute proof image. Solid black rectangles have been applied.\n"
        "Scan for any residual unmasked PII: visible contact names in headers, phone numbers, "
        "bank accounts, citizen IDs, civilian faces, or vehicle license plates.\n"
        "If any sensitive PII leaked through, emit its [ymin, xmin, ymax, xmax] coordinates in leak_boxes.\n"
        "Ensure dispute text dialogue and room defect damage remain readable."
    )

    p2_response = call_gemini_with_retry(
        client=effective_client,
        model=model,
        contents=[masked_img, pass2_prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ResidualAudit,
            temperature=0.0
        )
    )

    audit: ResidualAudit
    if hasattr(p2_response, "parsed") and p2_response.parsed:
        audit = p2_response.parsed
    else:
        audit = ResidualAudit.model_validate_json(p2_response.text)

    pass2_leak_boxes = [{"box_2d": list(b.box_2d), "label": b.label} for b in audit.leak_boxes]

    # Additive Self-Correction (Max 1 retry)
    if audit.has_leak and audit.leak_boxes:
        for leak in audit.leak_boxes:
            active_boxes.append(leak.box_2d)
        masked_img = apply_solid_black_masks(working_img, active_boxes, padding=padding + 2)

    masked_img.save(out_p, "WEBP", quality=90, method=6)

    return {
        "status": "redacted",
        "boxes_applied": len(active_boxes),
        "had_leak_recovery": audit.has_leak,
        "pass1_boxes": pass1_boxes,
        "pass2_leak_boxes": pass2_leak_boxes,
        "latency_ms": round((time.time() - t0) * 1000, 1),
        "path": str(out_p)
    }
