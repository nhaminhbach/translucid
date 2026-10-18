# Translucid

**Zero-Trust Selective Transparency Engine for Whistleblower & Consumer Dispute Evidence**

Built for **Google Cloud AI Builder Cup 2026** (Theme 5: Future of Work & Enterprise Productivity).

- **Live Cloud Run Prototype**: [https://translucid-nmbreovs7a-as.a.run.app](https://translucid-nmbreovs7a-as.a.run.app) (`asia-southeast1`)
- **Production Customer #1 (`nhaminhbach.com`)**: [https://nhaminhbach.com](https://nhaminhbach.com)
- **Downstream Google Gemini App MCP Server**: `https://translucid-982381915173.asia-southeast1.run.app/mcp`

---

## 1. The Whistleblower Catch-22 (Problem Alignment)

In developing and high-asymmetry markets across JAPAC, everyday citizens reporting rental scams, deposit theft, or consumer fraud are trapped between predatory operators and strict defamation and privacy statutes (**Vietnam Decree 13/2023/ND-CP & Decree 147/2024/ND-CP, Penal Code Art 156**):

- **If they speak out** with raw screenshots (Zalo/Messenger chats, bank transfer receipts, lease contracts), they and the hosting platform face legal takedowns, administrative fines, or retaliatory doxxing.
- **If they stay silent** (or platforms censor reviews entirely to avoid liability), predatory operators continue unpunished.

Like frosted glass (*translucid*) or Google Street View blurring applied to civic dispute evidence, **Translucid** renders personal identity markers (civilian faces, chat headers, phone numbers, bank accounts, national IDs) mathematically opaque while letting the structural evidence (utility tariffs, deposit deductions, physical defects, and commercial operator identities) pass through 100% legible.

### Production Validation on Customer #1 (`nhaminhbach.com`)
- **32,600+ weekly active users (WAU)** and **123,655 search queries** protected in production.
- **936 approved crowdsourced reviews** across **502 PostGIS buildings** and **27 canonical visual dispute assets (`privacy_1015`)** benchmarked.
- **96.3% benchmark accuracy** in **3.76 minutes** across 27 real-world dispute assets (~3.83s per clean asset, ~13.22s per redacted asset) — a **4.5x speedup** over manual multi-agent moderation.
- **Downstream Consumer AI Syndication**: Clean, legally compliant records produced by `Translucid` power `nhaminhbach.com` and are syndicated headlessly via Streamable HTTP JSON-RPC 2.0 (`https://mcp.nhaminhbach.com/mcp`) directly into the **Google Gemini App (`@Nhaminhbach`)**.

---

## 2. Why Traditional Tech & Naive Gen AI Fail (Technical Merit)

1. **Why Traditional Tech Fails (Context-Blindness)**:
   - Standard OCR/regex and baseline **Google Cloud DLP** are context-blind: they *over-redact* critical evidence (masking `4k/kWh` utility tariffs, deposit deduction figures, or commercial appliance warranty stickers as in asset `ln7p_5.webp`) while *under-redacting* visual context (missing Zalo/Messenger top-bar contact names, quoted sender headers, and civilian avatars).
2. **Why Naive Gen AI Fails (The "Self-Correction Mirage" & Injection Risks)**:
   - **The Self-Correction Mirage**: Grounded in CVPR 2026 multimodal findings, naive iterative VLM loops degrade accuracy (collapsing from 79.6% to 48.7%) as models second-guess prior detections.
   - **Prompt Injection & Data Leakage**: Allowing an LLM to directly rewrite text or edit image pixels exposes the pipeline to adversarial prompt injections embedded inside screenshots and leaks raw citizen PII to free-tier training logs.

### The 3 Core Innovations in Translucid
- **Additive Residual Detection ($B_{\text{final}} = B_1 \cup \Delta B$)**: Pass 1 (`RedactionPlan`) detects sensitive coordinates `[ymin, xmin, ymax, xmax]` and deterministic Pillow code (`masks.py`) burns irreversible `(0, 0, 0)` solid-black masks with `+5px` safety padding. Pass 2 (`ResidualAudit`) inspects the *already-masked* image strictly for surviving PII leaks ($\Delta B$) and unions coordinates additively.
- **Untrusted-Worker Sandboxing & Local Token Vault**: Pre-inference regex tokenization (`tokenize_pii_vault` -> `<PII_PHONE_01>`, `<PII_ID_01>`) + strict schema constraints on **Gemini API / Vertex AI Enterprise** (`asia-southeast1`, zero data retention). The model emits only integer coordinates and statutory claim keys (`[[claim:tranh chap tien coc]]`); deterministic Python executes all pixel and string mutations.
- **Zero-Leak Synthetic-PII Benchmark Packaging**: In `data/benchmarks/privacy_1015/`, all 27 `ground_truth/` images have real PII irreversibly burned out with `(0, 0, 0)` solid black, while `raw/` test fixtures are synthesized from `ground_truth/` with mock PII overlays so 100% of authentic dispute dialogue and physical defects are preserved with 0% real citizen PII exposure.

---

## 3. Repository Structure

```text
translucid/
├── app/
│   ├── main.py                 # FastAPI backend (/api/benchmark, /api/redact, /api/mcp-proxy)
│   └── static/index.html       # Single-page interactive showcase & live Gemini redaction workbench
├── configs/policies/           # Declarative statutory profile (VN Decree 13/147 + Civil Code 328)
├── data/benchmarks/            # 27-asset canonical benchmark dataset (privacy_1015)
├── translucid/
│   ├── visual/                 # Dual-pass VLM engine, Pydantic schemas, solid-black Pillow masks
│   ├── text/                   # NFKC sanitizer, token vault, statutory claim mapping, unified diff
│   └── eval/                   # Offline CI & live Gemini/Vertex AI benchmark runner
├── tests/                      # 29 unit, benchmark regression, and FastAPI integration tests
└── Dockerfile                  # Scale-to-zero Google Cloud Run container
```

## 4. Quickstart & Cloud Run Deployment

```bash
# 1. Run all 29 unit, benchmark, and FastAPI integration tests
uv run pytest -v

# 2. Launch the Interactive Showcase & Live Redaction Workbench locally
uv run uvicorn app.main:app --reload --port 8080

# 3. Run the canonical 27-asset privacy_1015 CLI benchmark
uv run python -m translucid.eval.benchmark

# 4. Deploy to Google Cloud Run (scale-to-zero)
gcloud run deploy translucid --source . --region asia-southeast1 --allow-unauthenticated --min-instances=0
```

## License

Apache License 2.0
