"""
Unified Git-Style Legal Diff Generator for Translucid.
Emits unified diffs (review.diff) and aligned 2-column CSV comparisons
between raw whistleblower submissions and statutory-sanitized outputs.
"""
import csv
import difflib
from collections.abc import Sequence
from pathlib import Path


def generate_unified_diff(
    raw_text: str,
    sanitized_text: str,
    record_id: str = "submission",
    context_lines: int = 3,
) -> str:
    """
    Computes a unified diff between raw input text and sanitized output text.
    """
    raw_lines = [f"[{record_id}] {line}" for line in (raw_text or "").splitlines()]
    sanitized_lines = [f"[{record_id}] {line}" for line in (sanitized_text or "").splitlines()]

    diff_lines = list(
        difflib.unified_diff(
            raw_lines,
            sanitized_lines,
            fromfile=f"a/{record_id}/raw",
            tofile=f"b/{record_id}/sanitized",
            lineterm="",
            n=context_lines,
        )
    )
    return "\n".join(diff_lines) + ("\n" if diff_lines else "")


def export_aligned_diff_artifacts(
    records: Sequence[dict[str, str]],
    out_dir: Path,
) -> tuple[Path, Path, Path]:
    """
    Writes raw.csv, sanitized.csv, and review.diff to out_dir for 1-click human inspection.
    Each record dict expects keys: 'short_id', 'raw_content', 'sanitized_content'.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_csv_path = out_dir / "raw.csv"
    sanitized_csv_path = out_dir / "sanitized.csv"
    diff_file_path = out_dir / "review.diff"

    raw_lines_for_diff: list[str] = ["short_id | content"]
    san_lines_for_diff: list[str] = ["short_id | content"]

    with (
        open(raw_csv_path, "w", encoding="utf-8", newline="") as f_raw,
        open(sanitized_csv_path, "w", encoding="utf-8", newline="") as f_san,
    ):
        w_raw = csv.writer(f_raw)
        w_san = csv.writer(f_san)
        w_raw.writerow(["short_id", "content"])
        w_san.writerow(["short_id", "content"])

        for row in records:
            short_id = row.get("short_id", "unknown")
            raw_c = " ".join((row.get("raw_content") or "").splitlines()).strip()
            san_c = " ".join((row.get("sanitized_content") or "").splitlines()).strip()
            w_raw.writerow([short_id, raw_c])
            w_san.writerow([short_id, san_c])
            raw_lines_for_diff.append(f"[{short_id}] {raw_c}")
            san_lines_for_diff.append(f"[{short_id}] {san_c}")

    diff_lines = list(
        difflib.unified_diff(
            raw_lines_for_diff,
            san_lines_for_diff,
            fromfile="a/raw.csv",
            tofile="b/sanitized.csv",
            lineterm="",
            n=1,
        )
    )
    with open(diff_file_path, "w", encoding="utf-8") as f_diff:
        if diff_lines:
            f_diff.write("\n".join(diff_lines) + "\n")
        else:
            f_diff.write("# No differences between raw.csv and sanitized.csv\n")

    return raw_csv_path, sanitized_csv_path, diff_file_path
