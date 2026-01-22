# Job Market Intelligence

**Production-ready data pipeline for tech job market analysis across Europe**

[![Tests](https://img.shields.io/badge/tests-26%20passing-brightgreen)]() 
[![Python](https://img.shields.io/badge/python-3.10+-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

A professional data pipeline for collecting, processing, and analyzing job market data from Adzuna API. Features ML-powered role classification, salary prediction, automated EDA reports, and an interactive Streamlit dashboard.

## ✨ Features

- **One-Command Pipeline**: Full orchestration with `--all` flag or granular step control
- **Historical Data Tracking**: Dated snapshots for trend analysis and repost detection
- **Ghost Job Detection**: Identify suspicious job postings that stay active for extended periods
- **Dual Classification**: Rule-based (keyword matching) + ML-based (91.6% F1 score)
- **Automated EDA**: Generate comprehensive reports with visualizations
- **Salary Modeling**: Ridge regression for salary prediction (R²: 0.70)
- **Skills Extraction**: 80+ technical skills automatically detected
- **Interactive UI**: Streamlit dashboard with filters, charts, and ML comparison
- **Docker Ready**: Full containerization with docker-compose
- **Multi-Country**: DE, PL, GB, AT, NL, BE, FR, ES, IT
- **Production Code**: Typed, tested (53/53 passing), logged, documented
- **CI/CD**: Automated testing, building, deployment via GitHub Actions
- **Cloud Ready**: Kubernetes, Terraform (AWS), Docker Compose configurations
- **Monitoring**: Prometheus + Grafana dashboards, health checks, alerting

## 🚀 Quick Start

### Local Development

```bash
# Install
git clone https://github.com/moroianu13/job-market-intelligence.git
cd job-market-intelligence
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Configure (get credentials from https://developer.adzuna.com/)
echo "ADZUNA_APP_ID=your_id" > .env
echo "ADZUNA_APP_KEY=your_key" >> .env

# Run pipeline
python orchestration/run_pipeline.py --all --ml --ghost-detection

# Launch dashboard
streamlit run app/streamlit_app.py
```

### Production Deployment

**Free Options (No Credit Card Required):**

```bash
# Option 1: Streamlit Cloud (Recommended - 100% FREE)
# 1. Go to https://share.streamlit.io
# 2. Connect your GitHub repo
# 3. Deploy! (5 minutes, zero cost)

# Option 2: Railway.app ($5 credit/month, no CC for hobby)
railway login
railway init
railway up

# Option 3: Render.com (Free tier)
# 1. Connect GitHub at render.com
# 2. Create Web Service
# 3. Deploy!
```

See **[FREE_DEPLOYMENT.md](FREE_DEPLOYMENT.md)** for 100% free deployment options.

For enterprise deployment, see **[DEPLOYMENT.md](DEPLOYMENT.md)**.

Or use **Makefile**:
```bash
make install      # Install dependencies
make pipeline     # Run full pipeline
make ui           # Launch Streamlit UI
```

See **[QUICKSTART.md](QUICKSTART.md)** for detailed instructions.

## 📊 Demo

```bash
# Generate demo report with examples
python demo/showcase.py

# View report
cat reports/demo/$(date +%Y-%m-%d)/DEMO.md
```

## 📋 Role Categories

The system classifies jobs into the following categories:

1. **Data Scientist** - ML models, statistical analysis, experimentation
2. **Data Engineer** - ETL pipelines, data warehousing, big data
3. **Machine Learning Engineer** - ML deployment, MLOps, AI systems
4. **Data Analyst** - Business intelligence, reporting, dashboards
5. **Cybersecurity Specialist** - Security engineering, infosec, threat analysis
6. **DevOps Engineer** - Infrastructure automation, CI/CD, SRE
7. **Software Engineer** - Full-stack, backend, frontend development
8. **Other** - Jobs that don't match specific technical categories

## 🏗️ Project Structure

```
job-market-intelligence/
├── ingestion/              # Data collection layer
│   └── fetch_adzuna.py    # Adzuna API client
├── preprocessing/          # Role classification logic
│   └── role_labels.py     # Rule-based role definitions and keyword matching
├── processing/             # Data transformation layer
│   ├── normalize_all_adzuna.py  # JSON to DataFrame normalization
│   ├── label_all_jobs.py        # Apply role labels to jobs (rules or ML)
│   ├── skill_extraction.py      # Extract technical skills
│   └── fingerprints.py          # Job fingerprinting for repost detection
├── analysis/              # Analytical models
│   ├── eda_report.py     # Exploratory data analysis
│   ├── salary_model.py   # Salary prediction model
│   └── repost_detector.py # Ghost job detection
├── ml/                   # Machine learning models
│   └── role_classifier/  # ML-based role classification
│       ├── train_classifier.py   # Train multi-label classifier
│       ├── predict_classifier.py # Inference and prediction
│       ├── compare_classifiers.py # Compare rule-based vs ML
│       └── README.md             # Detailed ML documentation
├── data/
│   ├── raw/               # Raw API responses (gitignored)
│   │   ├── adzuna/       # Production data by date/country/query
│   │   └── mock/         # Sample data for testing
│   └── curated/          # Processed Parquet files (gitignored)
│       ├── jobs_all_labeled.parquet      # Latest rule-based
│       ├── jobs_all_labeled_ml.parquet   # Latest ML-based
│       └── snapshots/                     # Historical snapshots by date
├── models/               # Trained models (gitignored)
│   ├── role_classifier/  # Role classification models
│   └── salary/           # Salary prediction models
├── tests/                # Test suite
└── orchestration/        # Workflow automation
    └── run_pipeline.py   # End-to-end pipeline runner
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- Adzuna API credentials ([Get them here](https://developer.adzuna.com/))

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd job-market-intelligence
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```env
   ADZUNA_APP_ID=your_app_id_here
   ADZUNA_APP_KEY=your_app_key_here
   ```

### Usage

#### 1. Fetch Job Data

Collect job postings from Adzuna API:

```bash
python ingestion/fetch_adzuna.py
```

This will:
- Fetch jobs across 9 European countries
- Search for 3 query types: "data scientist", "data engineer", "machine learning engineer"
- Save 2 pages (50 results per page) for each country/query combination
- Store raw JSON files in `data/raw/adzuna/YYYY-MM-DD/`

#### 2. Process and Label Jobs

Normalize and classify the collected data:

**Option A: Use Rule-Based Classification (Default)**
```bash
python processing/label_all_jobs.py
```

**Option B: Use ML-Based Classification**
```bash
python processing/label_all_jobs.py --ml --model models/role_classifier/2026-01-22
```

This will:
- Load all raw JSON files
- Normalize data into a structured DataFrame
- Apply role classification (rule-based or ML-based)
- Extract technical skills from descriptions
- Save curated data to `data/curated/jobs_all_labeled.parquet`

#### 3. Train ML Role Classifier (Optional)

Train your own ML classifier:

```bash
python ml/role_classifier/train_classifier.py \
    --data data/curated/jobs_all_labeled.parquet \
    --out models/role_classifier/2026-01-22
```

Compare ML vs rule-based performance:

```bash
# First label with ML
python processing/label_all_jobs.py --ml

# Then compare
python ml/role_classifier/compare_classifiers.py
```

#### 4. Train Salary Prediction Model (Optional)

Build a salary prediction model:

```bash
python analysis/salary_model.py --out models/salary/2026-01-22
```

#### 5. Analyze Results

Load and analyze the curated data:

```python
import pandas as pd

df = pd.read_parquet("data/curated/jobs_all_labeled.parquet")

# Distribution of roles
print(df["roles"].explode().value_counts())

# Average salaries by role
print(df.groupby("country")[["salary_min", "salary_max"]].mean())
```

## 🔧 Configuration

### Modify Data Collection Parameters

Edit `ingestion/fetch_adzuna.py` to customize:

```python
@dataclass(frozen=True)
class FetchConfig:
    countries: tuple[str, ...] = ("de", "pl", "gb", "at", "nl", "be", "fr", "es", "it")
    queries: tuple[str, ...] = ("data scientist", "data engineer", "machine learning engineer")
    results_per_page: int = 50
    pages_per_query: int = 2
    sleep_seconds: float = 2.0
```

### Customize Role Classifications

Modify keyword patterns in `preprocessing/role_labels.py`:

```python
ROLE_KEYWORDS = {
    "data_scientist": [
        r"data scientist",
        r"applied scientist",
        # Add more patterns
    ],
    # ...
}
```

## 📊 Data Schema

### Curated Data Schema

| Column | Type | Description |
|--------|------|-------------|
| `job_id` | str | Unique Adzuna job identifier |
| `title` | str | Job title |
| `description` | str | Full job description |
| `created` | str | Job posting creation date |
| `redirect_url` | str | URL to original job posting |
| `company` | str | Company name |
| `category` | str | Adzuna job category |
| `location` | str | Job location |
| `salary_min` | float | Minimum salary |
| `salary_max` | float | Maximum salary |
| `run_date` | str | Date when data was collected |
| `country` | str | Country code (de, pl, gb, etc.) |
| `query` | str | Search query used to find this job |
| `roles` | list[str] | Classified role labels (multi-label) |
| `skills` | list[str] | Extracted technical skills |
| `job_fingerprint` | str | SHA1 hash for tracking reposts across runs |
| `source_file` | str | Original JSON file path |

## 📸 Historical Data & Ghost Job Detection

### Historical Data Retention

The system maintains **versioned snapshots** of all curated data for trend analysis:

```
data/curated/
├── jobs_all_labeled_ml.parquet        # Latest version (for UI)
└── snapshots/
    ├── 2026-01-15/
    │   └── jobs_all_labeled_ml.parquet
    ├── 2026-01-22/
    │   └── jobs_all_labeled_ml.parquet
    └── 2026-01-29/
        └── jobs_all_labeled_ml.parquet
```

**Key Benefits:**
- Track how job postings change over time
- Detect reposted jobs (same job, different posting dates)
- Identify ghost jobs that stay active for months
- Analyze market trends and seasonal patterns
- Historical backfilling for retrospective analysis

### How Ghost Jobs Are Detected

**Ghost jobs** are suspicious postings that remain active far longer than normal hiring cycles. These may indicate:
- Companies perpetually "hiring" to collect resumes
- Fake postings to gauge market interest
- Outdated listings never removed

**Detection Strategy:**

1. **Job Fingerprinting**: Each job gets a stable identifier based on:
   - Normalized title (case/whitespace insensitive)
   - Normalized company name
   - Normalized location
   - URL domain (not full URL, to survive tracking params)

2. **Historical Tracking**: Load all snapshots and group by fingerprint to compute:
   - `first_seen`: First date job appeared
   - `last_seen`: Most recent appearance
   - `days_seen`: Number of distinct scraping dates
   - `repost_count`: Total times job was observed
   - `active_span_days`: Days between first and last observation

3. **Ghost Job Heuristic** (configurable):
   ```python
   ghost_job = (days_seen >= 3) AND (active_span_days >= 30)
   ```
   
   **Rationale**: Real jobs typically fill within 2-4 weeks. Jobs appearing on 3+ separate scraping runs spanning 30+ days are suspicious.

### Running Ghost Detection

```bash
# Detect ghost jobs from all historical snapshots
python analysis/repost_detector.py

# With custom thresholds
python analysis/repost_detector.py --min-days-seen 5 --min-active-span 45

# Integrated in pipeline
python orchestration/run_pipeline.py --all --ghost-detection
```

**Output:**
- `reports/ghost_jobs/<date>/ghost_jobs.csv` - Full list of flagged jobs
- `reports/ghost_jobs/<date>/summary.json` - Statistics and top offenders

**Example Summary:**
```json
{
  "analysis_date": "2026-01-22",
  "total_unique_jobs": 1247,
  "ghost_jobs_count": 89,
  "ghost_jobs_pct": 7.14,
  "metrics": {
    "avg_active_span_days": 68,
    "max_active_span_days": 120,
    "max_repost_count": 12
  }
}
```

### Fingerprint Stability

The fingerprinting algorithm is designed to be:
- **Deterministic**: Same job → same fingerprint
- **Robust**: Minor text changes don't break tracking
- **Sensitive**: Different jobs → different fingerprints

Example:
```python
from processing.fingerprints import make_fingerprint

job1 = {"title": "Data Scientist", "company": "Tech Corp", "location": "Berlin", "redirect_url": "https://example.com/job1"}
job2 = {"title": "DATA SCIENTIST", "company": "tech corp", "location": "  Berlin  ", "redirect_url": "https://example.com/job1?ref=linkedin"}

# Same fingerprint despite case/whitespace/URL param differences
make_fingerprint(job1) == make_fingerprint(job2)  # True
```

## 🤖 ML Role Classifier

The project includes an advanced machine learning classifier that can replace the rule-based system:

### Performance Metrics

- **F1 Score (micro)**: 0.916
- **F1 Score (macro)**: 0.834
- **Hamming Loss**: 0.024
- **Agreement with rules**: 90.5%

### Key Advantages

1. **Generalization**: Learns patterns beyond exact keyword matching
2. **Multi-label**: Better handles jobs with overlapping responsibilities (17.1% vs 13.4%)
3. **Interpretable**: Provides top features for each role category
4. **Fast**: Processes 2486 jobs in <1 second

### Architecture

- **Text Features**: TF-IDF vectorization (max 5000 features, 1-2 grams)
- **Model**: MultiOutputClassifier with LogisticRegression
- **Training Data**: 1988 jobs (80% split)
- **Test Data**: 498 jobs (20% split)

See [ml/role_classifier/README.md](ml/role_classifier/README.md) for detailed documentation.

## 📈 Salary Prediction Model

Ridge regression model for predicting salaries based on:
- Job role
- Technical skills
- Country
- Job title keywords

**Performance:**
- MAE: €15,528
- R²: 0.700

Run with:
```bash
python analysis/salary_model.py --out models/salary/2026-01-22
```
| `source_file` | str | Original JSON file path |

## 🧪 Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black .

# Lint
flake8 .

# Type checking
mypy .
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🔗 Links

- [Adzuna API Documentation](https://developer.adzuna.com/)
- [Project Issues](https://github.com/your-username/job-market-intelligence/issues)

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

---

**Note**: This project requires valid Adzuna API credentials. Free tier allows 500 API calls per month.
