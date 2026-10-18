"""
Integration tests for the Translucid FastAPI Web Showcase & Redaction Sandbox (app/main.py).
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["engine"] == "translucid"
    assert data["benchmark_assets_ready"] is True


def test_index_html_served():
    res = client.get("/")
    assert res.status_code == 200
    assert "TRANSLUCID" in res.text
    assert "Whistleblower Catch-22" in res.text


def test_benchmark_api_endpoint():
    res = client.get("/api/benchmark")
    assert res.status_code == 200
    data = res.json()
    assert data["total_assets"] == 27
    assert data["accuracy_pct"] >= 95.0
    assert len(data["curated_cases"]) >= 5
    assert "vn_decree13_147" in data["policies"]
    assert "sg_pdpa_poha" in data["policies"]


def test_redact_api_pipeline_execution():
    raw_text = "Chủ trọ tên Minh sđt 0912345678 lừa đảo chiếm đoạt tiền cọc 3.500.000đ"
    res = client.post(
        "/api/redact",
        json={
            "text": raw_text,
            "policy_id": "vn_decree13_147",
            "asset_filename": "4Z1w_0.webp",
            "run_live_vlm": False,
        },
    )
    assert res.status_code == 200
    data = res.json()
    tp = data["text_pipeline"]
    assert "<PII_PHONE_01>" in tp["quarantined_text"]
    assert "0912345678" not in tp["sanitized_text"]
    assert "[[pii:091***5678]]" in tp["sanitized_text"]
    assert "[[claim:" in tp["sanitized_text"]
    assert "--- a/vn_decree13_147/raw" in tp["unified_diff"]

    vp = data["visual_pipeline"]
    assert vp["status"] == "redacted"
    assert vp["boxes_applied"] >= 1
    assert len(vp["pass1_boxes"]) >= 1


def test_asset_serving_endpoints():
    res_gt = client.get("/assets/ground_truth/4Z1w_0.webp")
    assert res_gt.status_code == 200
    assert res_gt.headers["content-type"] == "image/webp"

    res_raw = client.get("/assets/raw/4Z1w_0.webp")
    assert res_raw.status_code == 200
    assert res_raw.headers["content-type"] == "image/webp"
