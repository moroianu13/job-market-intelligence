# Ghost Job Detection - Implementation Summary

**Date**: January 22, 2026  
**Feature**: Historical data tracking and ghost job detection

## 🎯 Objectives Achieved

✅ **Historical Data Versioning**: Dated snapshots of curated data  
✅ **Job Fingerprinting**: Stable identifiers for tracking reposts  
✅ **Ghost Job Detection**: Identify suspicious long-running postings  
✅ **Pipeline Integration**: Seamless --ghost-detection flag  
✅ **Comprehensive Testing**: 27 new tests, all passing (53 total)  
✅ **Documentation**: README with detailed explanations

---

## 📁 New Files Created

### Core Functionality
1. **`processing/fingerprints.py`** (145 lines)
   - `normalize_text()`: Case/whitespace normalization
   - `extract_domain()`: URL domain extraction
   - `make_fingerprint()`: SHA1 hash generation
   - `add_fingerprints()`: Batch fingerprint addition

2. **`analysis/repost_detector.py`** (315 lines)
   - `load_all_snapshots()`: Historical data loading
   - `compute_repost_metrics()`: Aggregate by fingerprint
   - `flag_ghost_jobs()`: Apply heuristic
   - `generate_ghost_job_report()`: CSV + JSON outputs
   - CLI interface with argparse

### Testing
3. **`tests/test_fingerprints.py`** (238 lines)
   - 19 tests covering normalization, domain extraction, fingerprinting
   - Tests for stability, case/whitespace insensitivity
   - Boundary conditions and edge cases

4. **`tests/test_repost_detector.py`** (267 lines)
   - 8 tests for repost metrics and ghost detection
   - Threshold boundary testing
   - End-to-end workflow validation

---

## 🔧 Modified Files

### Configuration
1. **`config.py`**
   - Added `SNAPSHOTS_DIR = CURATED_DATA_DIR / "snapshots"`
   - Added `GHOST_JOBS_DIR = REPORTS_DIR / "ghost_jobs"`

### Pipeline Integration
2. **`processing/label_all_jobs.py`**
   - Import `add_fingerprints` function
   - Call `add_fingerprints(df)` after skill extraction
   - Adds `job_fingerprint` column to all curated data

3. **`orchestration/run_pipeline.py`**
   - Added `_save_snapshot()` method (copies curated data to dated folder)
   - Added `step_ghost_detection()` method
   - Call snapshot saving after successful labeling
   - Added `--ghost-detection` CLI flag
   - Updated help text and examples

### Documentation
4. **`README.md`**
   - New section: "📸 Historical Data & Ghost Job Detection"
   - Explained snapshot structure
   - Documented fingerprinting algorithm
   - Ghost job heuristic rationale
   - Example usage and output formats

5. **`.gitignore`**
   - Changed `data/curated/` → `data/curated/*.parquet`
   - Added `data/curated/snapshots/` exclusion

---

## 🏗️ Architecture

### Data Flow

```
┌─────────────────────────────────────────────────────────┐
│ 1. Ingestion (fetch_adzuna.py)                         │
│    → data/raw/adzuna/<date>/<country>/<query>.json     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Processing (label_all_jobs.py)                      │
│    → Normalize, label roles, extract skills             │
│    → Add job fingerprints (NEW)                         │
│    → data/curated/jobs_all_labeled_ml.parquet           │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Snapshot Saving (NEW)                                │
│    → Copy to data/curated/snapshots/<date>/             │
│    → Preserves history for trend analysis               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Ghost Detection (repost_detector.py - NEW)          │
│    → Load all snapshots                                 │
│    → Group by job_fingerprint                           │
│    → Compute repost metrics                             │
│    → Flag ghosts: days_seen ≥ 3 AND span ≥ 30          │
│    → reports/ghost_jobs/<date>/ghost_jobs.csv           │
└─────────────────────────────────────────────────────────┘
```

### Fingerprinting Algorithm

**Input Components:**
```python
title       → "Data Scientist"
company     → "Tech Corp"
location    → "Berlin"
redirect_url → "https://example.com/jobs/123?ref=abc"
```

**Normalization:**
```python
title       → "data scientist"       (lowercase, whitespace normalized)
company     → "tech corp"             (lowercase, whitespace normalized)
location    → "berlin"                (lowercase, whitespace normalized)
url_domain  → "example.com"           (domain only, ignore params/path)
```

**Fingerprint:**
```python
fingerprint_str = "data scientist|tech corp|berlin|example.com"
fingerprint_hash = sha1(fingerprint_str).hexdigest()
# → "a1b2c3d4e5f6..." (40 character SHA1 hash)
```

**Properties:**
- ✅ **Stable**: Same job → same hash
- ✅ **Robust**: Minor variations (case, whitespace, URL params) → same hash
- ✅ **Sensitive**: Different jobs → different hashes
- ✅ **Deterministic**: Reproducible across runs

---

## 📊 Ghost Job Heuristic

### Rationale

**Normal Hiring Timeline:**
- Job posted → Applications collected (1-2 weeks) → Interviews (2-3 weeks) → Position filled
- **Total: 3-5 weeks**

**Ghost Job Characteristics:**
- Remains active for 8+ weeks (2+ months)
- Appears on multiple scraping runs
- No signs of urgency or deadline

### Detection Thresholds

**Default (Conservative):**
```python
ghost_job = (days_seen >= 3) AND (active_span_days >= 30)
```

**Rationale:**
- `days_seen >= 3`: Requires consistency (not just 1-2 appearances)
- `active_span_days >= 30`: Exceeds normal 3-5 week hiring cycle
- Both conditions must be true (AND operator)

**Customizable:**
```bash
# More lenient (catch more ghosts, higher false positives)
python analysis/repost_detector.py --min-days-seen 2 --min-active-span 21

# More strict (fewer false positives, might miss some)
python analysis/repost_detector.py --min-days-seen 5 --min-active-span 60
```

---

## 📈 Test Coverage

### Test Statistics
- **Total Tests**: 53 (26 original + 27 new)
- **New Tests**: 27 (19 fingerprints + 8 repost detector)
- **Pass Rate**: 100%
- **Test Time**: ~0.86s

### Fingerprint Tests (19)
- **Normalization** (5 tests): Case, whitespace, empty inputs, idempotency
- **Domain Extraction** (6 tests): Simple URLs, query params, fragments, case, invalid
- **Fingerprinting** (6 tests): Stability, case/whitespace insensitivity, URL param robustness, sensitivity
- **Batch Operations** (2 tests): DataFrame processing, empty inputs

### Repost Detector Tests (8)
- **Metrics Computation** (3 tests): Basic metrics, multiple jobs, single occurrence
- **Ghost Flagging** (4 tests): Detection logic, threshold boundaries, custom thresholds, empty data
- **End-to-End** (1 test): Complete workflow with synthetic historical data

---

## 🚀 Usage Examples

### 1. Run Pipeline with Ghost Detection

```bash
# Full pipeline with ML and ghost detection
python orchestration/run_pipeline.py --all --ml --ghost-detection

# Or specific steps
python orchestration/run_pipeline.py --label --ml --ghost-detection
```

### 2. Standalone Ghost Detection

```bash
# Using default thresholds
python analysis/repost_detector.py

# Custom analysis date
python analysis/repost_detector.py --run-date 2026-02-01

# Custom thresholds
python analysis/repost_detector.py --min-days-seen 5 --min-active-span 45
```

### 3. Analyze Outputs

**Ghost Jobs CSV:**
```bash
# Load in Python
import pandas as pd
ghosts = pd.read_parquet('reports/ghost_jobs/2026-01-22/ghost_jobs.csv')

# Top 10 by repost count
print(ghosts.nlargest(10, 'repost_count')[['title', 'company', 'repost_count', 'active_span_days']])
```

**Summary JSON:**
```bash
# View summary
cat reports/ghost_jobs/2026-01-22/summary.json | jq .

# Extract key metrics
jq '.metrics' reports/ghost_jobs/2026-01-22/summary.json
```

---

## 🔒 Data Retention Policy

### What Gets Saved
- ✅ **Snapshots**: Dated copies in `data/curated/snapshots/<date>/`
- ✅ **Reports**: Ghost job reports in `reports/ghost_jobs/<date>/`

### What Gets Ignored (`.gitignore`)
- ❌ Raw API data: `data/raw/adzuna/`
- ❌ Curated data: `data/curated/*.parquet`
- ❌ Snapshots: `data/curated/snapshots/`
- ❌ Models: `models/`
- ❌ Reports: `reports/`

### Retention Strategy
```
data/curated/
├── jobs_all_labeled_ml.parquet        # Latest (for UI/analysis)
└── snapshots/
    ├── 2026-01-01/                    # Keep indefinitely
    │   └── jobs_all_labeled_ml.parquet
    ├── 2026-01-08/
    │   └── jobs_all_labeled_ml.parquet
    └── 2026-01-15/
        └── jobs_all_labeled_ml.parquet
```

**Recommendation**: Keep snapshots for 6-12 months for meaningful ghost detection.

---

## ⚠️ Limitations & Future Work

### Current Limitations
1. **Memory**: Loads all snapshots into memory (OK for 10-20 snapshots, may need optimization for 100+)
2. **Heuristic**: Simple threshold-based (could be ML-based)
3. **No UI**: Ghost jobs not yet in Streamlit dashboard
4. **Storage**: Snapshots accumulate (no automatic cleanup)

### Future Enhancements
1. **Streaming**: Process snapshots incrementally for large histories
2. **ML-Based Detection**: Train classifier on labeled ghost jobs
3. **Dashboard Integration**: Add ghost job view to Streamlit UI
4. **Alerting**: Email/Slack notifications for high ghost job rates
5. **Benchmarking**: Validate heuristic against known ghost jobs
6. **Time-Series Analysis**: Trend detection, seasonality

---

## 📝 Changelog

### Added
- Historical snapshot versioning
- Job fingerprinting algorithm
- Ghost job detection module
- 27 new tests (100% passing)
- CLI flag `--ghost-detection`
- Comprehensive documentation

### Modified
- `config.py`: New paths for snapshots and ghost reports
- `processing/label_all_jobs.py`: Adds fingerprints to all jobs
- `orchestration/run_pipeline.py`: Snapshot saving and ghost detection
- `README.md`: New section on ghost job detection
- `.gitignore`: More granular data exclusions

### No Breaking Changes
- All existing functionality preserved
- All 26 original tests still passing
- Backward compatible CLI (new flag is optional)

---

## ✅ Completion Checklist

- [x] Historical data versioning implemented
- [x] Job fingerprinting with SHA1 hashing
- [x] Ghost job detection with configurable heuristic
- [x] Pipeline integration with --ghost-detection flag
- [x] Comprehensive testing (27 new tests)
- [x] Documentation in README
- [x] No breaking changes to existing code
- [x] All tests passing (53/53)

**Status**: ✅ **COMPLETE AND PRODUCTION-READY**
