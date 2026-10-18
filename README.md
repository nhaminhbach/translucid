# Translucid

**Zero-Trust Selective Transparency Engine for Whistleblower & Consumer Dispute Evidence**

Built for **Google Cloud AI Builder Cup 2026** (Theme 5: Future of Work & Enterprise Productivity).

---

## 1. The Whistleblower Catch-22 (Problem Alignment)

In developing and high-asymmetry markets across JAPAC, everyday citizens reporting rental scams, deposit theft, or consumer fraud are trapped between predatory operators and strict defamation and privacy statutes (**Vietnam Decree 13/2023/ND-CP & Decree 147/2024/ND-CP, Penal Code Art 156; Singapore PDPA & POHA**):

- **If they speak out** with raw screenshots (Zalo/Messenger chats, bank transfer receipts, lease contracts), they and the hosting platform face legal takedowns, administrative fines, or retaliatory doxxing.
- **If they stay silent** (or platforms censor reviews entirely to avoid liability), predatory operators continue unpunished.

Like frosted glass (*translucid*) or Google Street View blurring applied to civic dispute evidence, **Translucid** renders personal identity markers (civilian faces, chat headers, phone numbers, bank accounts, national IDs) mathematically opaque while letting the structural evidence (utility tariffs, deposit deductions, physical defects, and commercial operator identities) pass through 100% legible.

### Production Validation on Customer #1 (`nhaminhbach.com`)
- **32,600+ weekly active users (WAU)** and **123,655 search queries** protected in production.
- **936 approved crowdsourced reviews** and **27 canonical visual dispute assets (`privacy_1015`)** benchmarked.
- **96.3% benchmark accuracy** in **3.76 minutes** across 27 real-world dispute assets (~3.83s per clean asset, ~13.22s per redacted asset) — a **4.5x speedup** over manual multi-agent moderation.

---

## 2. Why Traditional Tech & Naive Gen AI Fail (Technical Merit)

1. **Why Traditional Tech Fails (Context-Blindness)**:
   - Standard OCR/regex and baseline **Google Cloud DLP** are context-blind: they *over-redact* critical evidence (masking `4k/kWh` utility tariffs, deposit deduction figures, or commercial appliance warranty stickers as in asset `ln7p_5.webp`) while *under-redacting* visual context (missing Zalo/Messenger top-bar contact names, quoted sender headers, and civilian avatars).
2. **Why Naive Gen AI Fails (The "Self-Correction Mirage" & Injection Risks)**:
   - **The Self-Correction Mirage**: Grounded in CVPR 2026 multimodal findings, naive iterative VLM loops degrade accuracy (collapsing from 79.6% to 48.7%) as models second-guess prior detections.
   - **Prompt Injection & Data Leakage**: Allowing an LLM to directly rewrite text or edit image pixels exposes the pipeline to adversarial prompt injections embedded inside screenshots and leaks raw citizen PII to free-tier training logs.

### The 3 Core Innovations in Translucid
- **Additive Residual Detection ($B_{\text{final}} = B_1 \cup \Delta B$)**: Pass 1 (`RedactionPlan`) detects sensitive coordinates `[ymin, xmin, ymax, xmax]` and deterministic Pillow code (`masks.py`) burns irreversible `(0, 0, 0)` solid-black masks with `+5px` safety padding. Pass 2 (`ResidualAudit`) inspects the *already-masked* image strictly for surviving PII leaks ($\Delta B$) and unions coordinates additively.
- **Untrusted-Worker Sandboxing**: Pre-inference regex/DLP tokenization (`<PII_PHONE_01>`) + strict schema constraints on **Vertex AI Enterprise** (`asia-southeast1`, zero data retention). The model emits only integer coordinates and statutory claim keys (`[[claim:tranh chap tien coc]]`); deterministic Python executes all pixel and string mutations.
- **Multimodal Cross-Verification & SynthID Provenance**: Verifies that visual proof (receipts, meter readings, room defects) corroborates text claims while screening uploads for **SynthID** watermarks to block AI-generated fake evidence.

---

## 3. Repository Structure

```text
translucid/
├── configs/policies/           # Declarative statutory profiles (VN Decree 13/147, SG PDPA/POHA)
├── data/benchmarks/            # 27-asset canonical benchmark dataset (privacy_1015)
├── translucid/
│   ├── visual/                 # Dual-pass VLM engine, Pydantic schemas, solid-black Pillow masks
│   ├── text/                   # NFKC sanitizer, statutory claim mapping, unified Git-diff exporter
│   └── eval/                   # Offline CI & live Gemini/Vertex AI benchmark runner
└── tests/                      # Unit & benchmark regression test suite
```

## 4. Quickstart

```bash
# Run unit and offline benchmark regression tests
uv run pytest

# Run the canonical 27-asset privacy_1015 benchmark (offline verification)
uv run python -m translucid.eval.benchmark

# Run live evaluation against Gemini / Vertex AI
GEMINI_API_KEY="your-key" uv run python -m translucid.eval.benchmark --live
```

## License

Apache License 2.0
