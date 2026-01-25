# Security Overview

## Threat Model
- Public, read-only Streamlit dashboard; no user authentication or data submission.
- Weekly GitHub Actions pipeline fetches Adzuna data, normalizes, trains models, and produces summaries.
- File-based storage (Parquet/CSV/artifacts) persisted in the repo workspace; no database.
- External dependency on Adzuna API credentials provided via GitHub Secrets at runtime.

## Mitigations Implemented
- **Secret protection**: Adzuna credentials are loaded from environment only, masked in all logs, and `.env` is removed after CI usage. Request logging avoids full URLs.
- **Artifact hardening**: Scheduled workflow uploads only summary markdown/JSON outputs (no raw text, debug CSVs, or model binaries) with short retention.
- **Supply-chain hardening**: GitHub Actions pinned to immutable commit SHAs; Trivy scanning remains enabled for vulnerability detection.
- **Resource guards**: Streamlit restricts columns, caps loaded rows, caches with TTL, and only loads from predefined curated Parquet files.
- **Dependency hygiene**: Runtime and UI requirements updated to recent patched versions; CI security scan continues.

## Residual Risks / Operational Notes
- Model and data quality depend on Adzuna inputs; poisoned or low-quality upstream data can affect analytics.
- Large Parquet files beyond the configured cap will be truncated for UI stability; run offline analysis if full detail is required.
- Public dashboard intentionally unauthenticated—any published summaries should avoid sensitive or proprietary content.
- Keep GitHub Secrets rotated regularly and monitor CI logs/artifacts for anomalies despite masking.
