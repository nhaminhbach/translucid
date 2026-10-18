"""
Pydantic schemas for the Agentic Grounded Privacy & Compliance Pipeline.
Defines structured input/output representations for spatial detection and residual audits.
"""

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """
    Represents a localized sensitive entity on an image.
    Coordinates are normalized to a 0-1000 integer grid in vertical-first order:
    [ymin, xmin, ymax, xmax].
    """
    box_2d: list[int] = Field(
        ...,
        description="Bounding box coordinates in [ymin, xmin, ymax, xmax] format, normalized 0 to 1000."
    )
    label: str = Field(
        ...,
        description=(
            "Entity category: 'chat_header_name', 'chat_avatar', 'phone_number', "
            "'bank_account', 'citizen_id_cccd', 'civilian_face', 'vehicle_license_plate'."
        )
    )


class RedactionPlan(BaseModel):
    """Pass 1: Initial visual privacy detection plan."""
    is_clean: bool = Field(
        ...,
        description="True if image contains NO personal data, civilian faces, or sensitive contact markers."
    )
    sensitive_boxes: list[BoundingBox] = Field(
        default_factory=list,
        description="List of normalized [ymin, xmin, ymax, xmax] bounding boxes to mask."
    )
    rationale: str = Field(
        ...,
        description="Short statutory justification under Decree 13/2023/ND-CP."
    )


class ResidualAudit(BaseModel):
    """Pass 2: Additive residual detection audit on the masked image."""
    has_leak: bool = Field(
        ...,
        description="True if any unmasked personal identity markers remain visible on the masked image."
    )
    leak_boxes: list[BoundingBox] = Field(
        default_factory=list,
        description="Normalized [ymin, xmin, ymax, xmax] bounding boxes for any residual unmasked PII."
    )
    evidence_intact: bool = Field(
        ...,
        description="True if dispute dialogues, room defect damage, meter readings, tariffs, and timestamps remain readable."
    )
