"""
Unit tests for the Privacy Redaction Benchmark Suite and module exports.
Verifies dataset integrity, manifest schema, offline benchmark execution,
and backwards-compatible package imports.
"""
from pathlib import Path

import pytest

from translucid import (
    BoundingBox,
    RedactionPlan,
    ResidualAudit,
    apply_solid_black_masks,
    denormalize_box,
    process_review_image,
    run_benchmark,
)

BENCHMARK_EXISTS = Path("data/benchmarks/privacy_1015/manifest.json").exists()


def test_package_exports():
    """Asserts that all public symbols are cleanly exported from the sub-package."""
    assert callable(process_review_image)
    assert callable(denormalize_box)
    assert callable(apply_solid_black_masks)
    assert callable(run_benchmark)
    assert BoundingBox is not None
    assert RedactionPlan is not None
    assert ResidualAudit is not None


@pytest.mark.skipif(not BENCHMARK_EXISTS, reason="Benchmark dataset not present locally")
def test_benchmark_manifest_and_dataset_integrity():
    """Asserts that the canonical benchmark dataset exists with all 27 raw and ground_truth assets."""
    benchmark_dir = Path("data/benchmarks/privacy_1015")
    assert benchmark_dir.exists()

    manifest_path = benchmark_dir / "manifest.json"
    assert manifest_path.exists()

    raw_dir = benchmark_dir / "raw"
    gt_dir = benchmark_dir / "ground_truth"
    assert raw_dir.exists()
    assert gt_dir.exists()

    raw_files = list(raw_dir.glob("*.webp"))
    gt_files = list(gt_dir.glob("*.webp"))
    assert len(raw_files) == 27
    assert len(gt_files) == 27


@pytest.mark.skipif(not BENCHMARK_EXISTS, reason="Benchmark dataset not present locally")
def test_benchmark_offline_run():
    """Executes offline verification against the benchmark manifest and verifies accuracy >= 95%."""
    benchmark_dir = Path("data/benchmarks/privacy_1015")
    summary = run_benchmark(benchmark_dir=benchmark_dir, live=False)

    assert summary["total_assets"] == 27
    assert summary["accuracy_pct"] >= 95.0
    assert summary["matches"] >= 26
