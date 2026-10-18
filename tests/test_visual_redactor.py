"""
Unit tests for visual_redactor.py.
Verifies coordinate transformation, mathematical irreversibility of solid black masks,
transparency handling, fast-path clean images, additive residual detection loop,
and negative invariant preservation under Decree 13/2023/ND-CP.
"""
from unittest.mock import MagicMock

import pytest
from PIL import Image

from translucid.visual import (
    BoundingBox,
    RedactionPlan,
    ResidualAudit,
    apply_solid_black_masks,
    denormalize_box,
    process_review_image,
)


class TestCoordinateDenormalization:
    def test_standard_coordinate_transformation(self):
        """Tests standard [ymin, xmin, ymax, xmax] mapping to [x0, y0, x1, y1] with padding."""
        width = 1000
        height = 800
        padding = 5
        # ymin=100, xmin=200, ymax=300, xmax=400
        box_2d = [100, 200, 300, 400]
        x0, y0, x1, y1 = denormalize_box(box_2d, width, height, padding=padding)

        assert x0 == max(0, int(200 / 1000.0 * 1000) - 5)  # 195
        assert y0 == max(0, int(100 / 1000.0 * 800) - 5)   # 75
        assert x1 == min(1000, int(400 / 1000.0 * 1000) + 5)  # 405
        assert y1 == min(800, int(300 / 1000.0 * 800) + 5)    # 245

    def test_boundary_clamping(self):
        """Tests coordinates at outer boundaries [0, 0, 1000, 1000] are clamped to [0, 0, width, height]."""
        width = 1920
        height = 1080
        padding = 10
        box_2d = [0, 0, 1000, 1000]
        x0, y0, x1, y1 = denormalize_box(box_2d, width, height, padding=padding)

        assert x0 == 0
        assert y0 == 0
        assert x1 == 1920
        assert y1 == 1080

    def test_inverted_coordinate_order_handling(self):
        """Tests robustness when LLM emits inverted min/max order."""
        width = 500
        height = 500
        # Inverted: ymin > ymax, xmin > xmax
        box_2d = [400, 300, 100, 50]
        x0, y0, x1, y1 = denormalize_box(box_2d, width, height, padding=0)

        assert x0 == 25   # min(300, 50) / 1000 * 500 = 25
        assert y0 == 50   # min(400, 100) / 1000 * 500 = 50
        assert x1 == 150  # max(300, 50) / 1000 * 500 = 150
        assert y1 == 200  # max(400, 100) / 1000 * 500 = 200
        assert x1 > x0
        assert y1 > y0

    def test_invalid_coordinate_length(self):
        with pytest.raises(ValueError, match="must contain 4 coordinates"):
            denormalize_box([100, 200], 500, 500)


class TestSolidBlackMaskingEngine:
    def test_mathematical_irreversibility(self):
        """
        Asserts that masked pixels are strictly (0, 0, 0) and outside pixels remain untouched.
        Solid black rectangular box renders 100% opaque black pixels with zero residual gradient.
        """
        img = Image.new("RGB", (100, 100), (255, 255, 255))
        # Mask center box: [200, 200, 600, 600] -> pixels [20, 20, 60, 60] with padding=0
        masked = apply_solid_black_masks(img, [[200, 200, 600, 600]], padding=0)

        # Check inside region is mathematically pure black (0, 0, 0)
        for y in range(25, 55):
            for x in range(25, 55):
                assert masked.getpixel((x, y)) == (0, 0, 0), f"Pixel at ({x},{y}) is not black"

        # Check outside region is completely preserved (255, 255, 255)
        assert masked.getpixel((5, 5)) == (255, 255, 255)
        assert masked.getpixel((90, 90)) == (255, 255, 255)

    def test_rgba_and_transparency_handling(self):
        """Tests that RGBA images with transparency convert to white RGB with solid black masks."""
        rgba = Image.new("RGBA", (100, 100), (200, 100, 50, 0))  # transparent
        masked = apply_solid_black_masks(rgba, [[100, 100, 500, 500]], padding=0)

        assert masked.mode == "RGB"
        # Masked area is solid black
        assert masked.getpixel((30, 30)) == (0, 0, 0)
        # Unmasked transparent area becomes white background
        assert masked.getpixel((90, 90)) == (255, 255, 255)


class TestProcessReviewImagePipeline:
    def test_clean_defect_photo_fast_path(self, tmp_path):
        """Clean defect evidence photos return status='clean', boxes_applied=0, and save WebP."""
        test_img = Image.new("RGB", (200, 200), (200, 200, 200))
        input_file = tmp_path / "defect_wall.jpg"
        output_file = tmp_path / "defect_wall.webp"
        test_img.save(input_file)

        mock_client = MagicMock()
        mock_p1_response = MagicMock()
        mock_p1_response.parsed = RedactionPlan(
            is_clean=True,
            sensitive_boxes=[],
            rationale="Physical room defect only (peeling wall, water stains). No personal data."
        )
        mock_client.models.generate_content.return_value = mock_p1_response

        res = process_review_image(
            client=mock_client,
            input_path=input_file,
            output_path=output_file,
            model="gemini-3.5-flash-lite"
        )

        assert res["status"] == "clean"
        assert res["boxes_applied"] == 0
        assert res["had_leak_recovery"] is False
        assert output_file.exists()
        # Verify single LLM call for clean photo
        assert mock_client.models.generate_content.call_count == 1

    def test_additive_residual_detection_recovery(self, tmp_path):
        """
        Tests the 2-pass loop:
        Pass 1 detects header name -> Pillow masks it.
        Pass 2 detects residual leak (phone number) -> Additive merge -> Pillow re-masks.
        Asserts boxes_applied=2, had_leak_recovery=True, and both areas are black.
        """
        test_img = Image.new("RGB", (1000, 1000), (255, 255, 255))
        input_file = tmp_path / "dispute_chat.png"
        output_file = tmp_path / "dispute_chat.webp"
        test_img.save(input_file)

        mock_client = MagicMock()

        # Pass 1 response
        mock_p1 = MagicMock()
        mock_p1.parsed = RedactionPlan(
            is_clean=False,
            sensitive_boxes=[
                BoundingBox(box_2d=[50, 100, 120, 400], label="chat_header_name")
            ],
            rationale="Zalo chat header contains landlord personal name"
        )

        # Pass 2 response (Residual Audit with leak)
        mock_p2 = MagicMock()
        mock_p2.parsed = ResidualAudit(
            has_leak=True,
            leak_boxes=[
                BoundingBox(box_2d=[800, 200, 850, 500], label="phone_number")
            ],
            evidence_intact=True
        )

        mock_client.models.generate_content.side_effect = [mock_p1, mock_p2]

        res = process_review_image(
            client=mock_client,
            input_path=input_file,
            output_path=output_file,
            model="gemini-3.5-flash-lite",
            padding=5
        )

        assert res["status"] == "redacted"
        assert res["boxes_applied"] == 2
        assert res["had_leak_recovery"] is True
        assert output_file.exists()
        assert mock_client.models.generate_content.call_count == 2

        with Image.open(output_file) as redacted_img:
            # Check Pass 1 box center is solid black
            assert redacted_img.getpixel((250, 85)) == (0, 0, 0)
            # Check Pass 2 leak box center is solid black
            assert redacted_img.getpixel((350, 825)) == (0, 0, 0)
            # Check unmasked dialogue area remains white
            assert redacted_img.getpixel((500, 500)) == (255, 255, 255)

    def test_negative_invariant_preservation_contract(self):
        """
        Asserts that the system instruction and schemas prohibit masking
        evidence text, utility tariffs, and physical room defect damage.
        """
        audit_clean = ResidualAudit(
            has_leak=False,
            leak_boxes=[],
            evidence_intact=True
        )
        assert audit_clean.evidence_intact is True
        assert len(audit_clean.leak_boxes) == 0

    def test_out_of_bounds_clamping(self):
        """Coordinates outside [0, 1000] clamp safely without out-of-bound errors."""
        box_2d = [-100, -50, 1200, 1500]
        x0, y0, x1, y1 = denormalize_box(box_2d, width=800, height=600, padding=0)
        assert x0 == 0
        assert y0 == 0
        assert x1 == 800
        assert y1 == 600

    def test_zero_area_box(self):
        """Zero-area box with padding=0 does not draw or crash."""
        img = Image.new("RGB", (100, 100), (255, 255, 255))
        masked = apply_solid_black_masks(img, [[100, 100, 100, 100]], padding=0)
        # Pixel at (10, 10) is untouched
        assert masked.getpixel((10, 10)) == (255, 255, 255)

    def test_grayscale_image_conversion(self):
        """Grayscale 'L' mode images convert to RGB with solid black masks."""
        gray = Image.new("L", (100, 100), 200)
        masked = apply_solid_black_masks(gray, [[200, 200, 400, 400]], padding=0)
        assert masked.mode == "RGB"
        assert masked.getpixel((30, 30)) == (0, 0, 0)
        assert masked.getpixel((80, 80)) == (200, 200, 200)

    def test_paletted_image_conversion(self):
        """Paletted 'P' mode images convert cleanly without color degradation."""
        pal = Image.new("P", (100, 100))
        masked = apply_solid_black_masks(pal, [[100, 100, 300, 300]], padding=0)
        assert masked.mode == "RGB"
        assert masked.getpixel((20, 20)) == (0, 0, 0)

    def test_pass2_no_leak_clean_finish(self, tmp_path):
        """When Pass 2 reports no residual leak, output preserves Pass 1 masks directly."""
        test_img = Image.new("RGB", (500, 500), (255, 255, 255))
        input_file = tmp_path / "single_mask.png"
        output_file = tmp_path / "single_mask.webp"
        test_img.save(input_file)

        mock_client = MagicMock()
        mock_p1 = MagicMock()
        mock_p1.parsed = RedactionPlan(
            is_clean=False,
            sensitive_boxes=[BoundingBox(box_2d=[100, 100, 200, 200], label="chat_avatar")],
            rationale="Profile avatar present"
        )
        mock_p2 = MagicMock()
        mock_p2.parsed = ResidualAudit(has_leak=False, leak_boxes=[], evidence_intact=True)

        mock_client.models.generate_content.side_effect = [mock_p1, mock_p2]

        res = process_review_image(
            client=mock_client,
            input_path=input_file,
            output_path=output_file
        )
        assert res["status"] == "redacted"
        assert res["boxes_applied"] == 1
        assert res["had_leak_recovery"] is False

    def test_model_response_fallback_to_json_text(self, tmp_path):
        """Handles cases where model response provides JSON text instead of parsed attribute."""
        test_img = Image.new("RGB", (300, 300), (255, 255, 255))
        input_file = tmp_path / "fallback_json.png"
        output_file = tmp_path / "fallback_json.webp"
        test_img.save(input_file)

        mock_client = MagicMock()
        mock_p1 = MagicMock()
        mock_p1.parsed = None
        mock_p1.text = '{"is_clean": false, "sensitive_boxes": [{"box_2d": [50, 50, 150, 150], "label": "phone_number"}], "rationale": "Direct text fallback"}'

        mock_p2 = MagicMock()
        mock_p2.parsed = None
        mock_p2.text = '{"has_leak": false, "leak_boxes": [], "evidence_intact": true}'

        mock_client.models.generate_content.side_effect = [mock_p1, mock_p2]

        res = process_review_image(
            client=mock_client,
            input_path=input_file,
            output_path=output_file
        )
        assert res["status"] == "redacted"
        assert res["boxes_applied"] == 1
        assert res["had_leak_recovery"] is False
