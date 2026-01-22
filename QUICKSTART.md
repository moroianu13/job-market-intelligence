# 🚀 Quick Start Guide

## Prerequisites

- Python 3.10+
- Adzuna API credentials ([Get them here](https://developer.adzuna.com/))
- 2GB+ disk space for data

## Installation

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd job-market-intelligence
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure API credentials**
   
   Create `.env` file:
   ```env
   ADZUNA_APP_ID=your_app_id_here
   ADZUNA_APP_KEY=your_app_key_here
   ```

## One-Command Usage

### Run Full Pipeline

```bash
# Complete pipeline (fetch → label → eda → models)
python orchestration/run_pipeline.py --all

# With ML classification
python orchestration/run_pipeline.py --all --ml

# Force rerun everything
python orchestration/run_pipeline.py --all --force
```

### Run Specific Steps

```bash
# Fetch data only
python orchestration/run_pipeline.py --fetch

# Label jobs with rule-based classifier
python orchestration/run_pipeline.py --label

# Label with ML classifier
python orchestration/run_pipeline.py --label --ml

# Generate EDA report
python orchestration/run_pipeline.py --eda

# Train salary model
python orchestration/run_pipeline.py --salary

# Train ML role classifier
python orchestration/run_pipeline.py --train-role-model

# Custom data collection
python orchestration/run_pipeline.py --fetch --countries de,gb,fr --pages 5
```

### Launch Interactive Dashboard

```bash
streamlit run app/streamlit_app.py
```

Open your browser to `http://localhost:8501`

### Generate Demo Report

```bash
python demo/showcase.py --examples 10
```

View report at: `reports/demo/<date>/DEMO.md`

## Using Makefile (Recommended)

```bash
# Show all commands
make help

# Quick commands
make install      # Install dependencies
make test         # Run tests
make pipeline     # Run full pipeline
make demo         # Generate demo report
make ui           # Launch Streamlit dashboard

# Individual steps
make fetch        # Fetch data
make label        # Label with rules
make label-ml     # Label with ML
make eda          # Generate EDA report
make salary       # Train salary model
make train-ml     # Train ML classifier
```

## Docker Deployment

### Build and Run

```bash
# Build image
docker build -t job-intelligence .

# Run pipeline
docker-compose run --rm pipeline python orchestration/run_pipeline.py --all

# Launch UI
docker-compose up streamlit
```

Open browser to `http://localhost:8501`

### With Docker Compose

```bash
# Run full pipeline
make docker-pipeline

# Launch UI
make docker-ui

# Stop services
make docker-down
```

## Project Structure

```
job-market-intelligence/
├── ingestion/              # Data collection
│   └── fetch_adzuna.py
├── processing/             # Data transformation
│   ├── normalize_all_adzuna.py
│   ├── label_all_jobs.py
│   └── skill_extraction.py
├── preprocessing/          # Classification logic
│   └── role_labels.py
├── analysis/              # Analytical models
│   ├── eda_report.py
│   └── salary_model.py
├── ml/                    # Machine learning
│   └── role_classifier/
├── orchestration/         # Pipeline runner
│   └── run_pipeline.py
├── demo/                  # Demo & showcase
│   └── showcase.py
├── app/                   # Streamlit UI
│   └── streamlit_app.py
├── tests/                 # Test suite
├── config.py              # Central configuration
└── Makefile              # Convenience commands
```

## Pipeline Output Structure

```
data/
├── raw/adzuna/YYYY-MM-DD/         # Raw API responses
└── curated/
    ├── jobs_all_labeled.parquet   # Rule-based classification
    └── jobs_all_labeled_ml.parquet # ML-based classification

models/
├── role_classifier/YYYY-MM-DD/    # Trained ML classifiers
│   ├── role_classifier.joblib
│   └── vectorizer.joblib
└── salary/YYYY-MM-DD/             # Salary models
    ├── salary_model.joblib
    └── metrics.json

reports/
├── eda/YYYY-MM-DD/                # EDA reports & plots
│   ├── EDA_REPORT.md
│   ├── role_distribution.png
│   └── top_skills.png
└── demo/YYYY-MM-DD/               # Demo reports
    └── DEMO.md
```

## Common Workflows

### First-Time Setup

```bash
# 1. Install and configure
make install
cp .env.example .env  # Edit with your credentials

# 2. Run full pipeline
make pipeline

# 3. View results
make demo
make ui
```

### Daily Data Update

```bash
# Fetch today's data
make fetch

# Label with existing ML model
make label-ml

# Generate reports
make eda
```

### Train New Models

```bash
# 1. Collect training data
make fetch
make label  # Use rule-based for initial labels

# 2. Train ML classifier
make train-ml

# 3. Re-label with ML
make label-ml

# 4. Train salary model
make salary
```

### Development

```bash
# Run tests
make test

# Format code
black .

# Type checking
mypy .

# Clean cache
make clean
```

## Configuration

### Environment Variables

```env
# Required
ADZUNA_APP_ID=your_id
ADZUNA_APP_KEY=your_key

# Optional
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### Custom Pipeline Configuration

Edit `config.py`:

```python
DEFAULT_COUNTRIES = ("de", "gb", "fr", "es")  # Countries to fetch
DEFAULT_QUERIES = ("data scientist", "ml engineer")  # Search queries
DEFAULT_PAGES_PER_QUERY = 3  # Pages per query
```

## Troubleshooting

**No data files found**
```bash
# Run pipeline first
python orchestration/run_pipeline.py --fetch --label
```

**API credentials error**
```bash
# Check .env file exists and has correct values
cat .env
```

**Tests failing**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Port 8501 already in use**
```bash
# Use different port
streamlit run app/streamlit_app.py --server.port 8502
```

## Performance Tips

1. **Parallel Data Collection**: Modify `fetch_adzuna.py` to use `concurrent.futures`
2. **Caching**: Pipeline skips existing outputs unless `--force` is used
3. **Batch Size**: Adjust `results_per_page` in config for faster API calls
4. **Model Training**: Use subset of data for faster iteration

## API Limits

- Adzuna free tier: 250 calls/month
- Each pipeline run uses: ~54 calls (9 countries × 3 queries × 2 pages)
- ~4-5 full runs per month possible

## Support & Documentation

- **Full API Docs**: `docs/API.md`
- **ML Classifier**: `ml/role_classifier/README.md`
- **Contributing**: `CONTRIBUTING.md`
- **License**: `LICENSE`

---

**Need help?** Open an issue or check the documentation!
