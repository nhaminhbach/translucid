"""
Deterministic Coordinate Transformation and Pillow Masking Engine.
Maps normalized Gemini tokens [ymin, xmin, ymax, xmax] (0-1000) to pixel coordinates
and renders mathematically irreversible solid black rectangular masks.
"""
from collections.abc import Sequence

from PIL import Image, ImageDraw


def denormalize_box(
    box_2d: Sequence[int],
    width: int,
    height: int,
    padding: int = 5
) -> list[int]:
    """
    Translates vertical-first normalized Gemini tokens [ymin, xmin, ymax, xmax] (0-1000)
    to horizontal-first absolute pixel coordinates [x0, y0, x1, y1] with safety padding.

    Clamps bounds to [0, width] and [0, height].
    """
    if len(box_2d) != 4:
        raise ValueError(f"box_2d must contain 4 coordinates, got {len(box_2d)}")

    ymin, xmin, ymax, xmax = box_2d

    # Correct axis order mapping
    x0 = max(0, int((xmin / 1000.0) * width) - padding)
    y0 = max(0, int((ymin / 1000.0) * height) - padding)
    x1 = min(width, int((xmax / 1000.0) * width) + padding)
    y1 = min(height, int((ymax / 1000.0) * height) + padding)

    # Invert inverted min/max if model hallucinated reverse order
    if x0 > x1:
        x0, x1 = x1, x0
    if y0 > y1:
        y0, y1 = y1, y0

    return [x0, y0, x1, y1]


def apply_solid_black_masks(
    image: Image.Image,
    boxes_2d: Sequence[Sequence[int]],
    padding: int = 5
) -> Image.Image:
    """
    Renders solid black opaque rectangles over target coordinates.
    Guarantees RGB conversion from RGBA/paletted formats on a white canvas.
    """
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        bg = Image.new("RGB", image.size, (255, 255, 255))
        rgba = image.convert("RGBA")
        bg.paste(rgba, mask=rgba.split()[3])
        img_rgb = bg
    else:
        img_rgb = image.convert("RGB")

    width, height = img_rgb.size
    draw = ImageDraw.Draw(img_rgb)

    for box in boxes_2d:
        x0, y0, x1, y1 = denormalize_box(box, width, height, padding=padding)
        if x1 > x0 and y1 > y0:
            draw.rectangle([x0, y0, x1, y1], fill=(0, 0, 0))

    return img_rgb
