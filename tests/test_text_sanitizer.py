"""
Unit tests for translucid.text (sanitize.py and diff.py).
Verifies NFKC normalization, phone PII masking, Penal Code Art 156 -> Civil Code Art 328
claim neutralization, and unified diff generation.
"""
from translucid.text import (
    export_aligned_diff_artifacts,
    generate_unified_diff,
    normalize_unicode_text,
    sanitize_review_text,
)


def test_nfkc_normalization_and_phone_masking():
    raw = "Chủ nhà sđt 0987654321 giữ tiền cọc"
    sanitized = sanitize_review_text(raw, target_phone="0987654321")
    assert "0987654321" not in sanitized
    assert "098***4321" in sanitized


def test_criminal_accusation_to_civil_claim_neutralization():
    raw = "Chủ trọ lừa đảo chiếm đoạt tiền cọc của sinh viên"
    sanitized = sanitize_review_text(raw)
    assert "lừa đảo" not in sanitized.lower()
    assert "[[claim:" in sanitized


def test_address_abbreviation_guard():
    raw = "Đ/c: Ngõ 12 Cầu Giấy, phòng ẩm mốc"
    sanitized = sanitize_review_text(raw)
    assert "[[profanity:" not in sanitized
    assert "Ngõ 12 Cầu Giấy" in sanitized


def test_unified_diff_and_csv_export(tmp_path):
    raw = "Chủ nhà 0912345678 lừa đảo tiền cọc"
    san = sanitize_review_text(raw, target_phone="0912345678")
    diff_str = generate_unified_diff(raw, san, record_id="R01")
    assert "--- a/R01/raw" in diff_str
    assert "+++ b/R01/sanitized" in diff_str

    raw_csv, san_csv, diff_file = export_aligned_diff_artifacts(
        [{"short_id": "R01", "raw_content": raw, "sanitized_content": san}],
        out_dir=tmp_path,
    )
    assert raw_csv.exists()
    assert san_csv.exists()
    assert diff_file.exists()
    assert "R01" in diff_file.read_text(encoding="utf-8")
