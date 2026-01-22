# 💼 Job Market Intelligence

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit-red)](https://job-reports.streamlit.app/)
[![CI/CD](https://github.com/moroianu13/job-market-intelligence/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/moroianu13/job-market-intelligence/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-53%20passed-success)](tests/)

**[🚀 View Live Dashboard](https://job-reports.streamlit.app/)**

Automated job market analysis platform with ML-powered role classification, ghost job detection, and interactive visualizations. Collects and analyzes data science job postings across Europe using the Adzuna API.

## ✨ Features

- 🤖 **ML Role Classification**: 91.6% F1-score Logistic Regression model
- 👻 **Ghost Job Detection**: Historical tracking and repost identification
- 📊 **Interactive Dashboard**: Streamlit UI with filters and visualizations
- 💰 **Salary Analysis**: Ridge regression model (R²: 0.70) for salary predictions
- 🔍 **Skills Extraction**: NLP-based tech stack identification
- 📈 **Market Insights**: Trends, demand analysis, and geographic patterns
- 🧪 **53 Tests**: Comprehensive test coverage with pytest

## 🎯 Quick Start

### Prerequisites

- Python 3.10+
- Adzuna API credentials ([get free key](https://developer.adzuna.com/))

### Installation

```bash
# Clone repository
git clone https://github.com/moroianu13/job-market-intelligence.git
cd job-market-intelligence

# Install dependencies
pip install -r requirements.txt

# Configure API credentials
cp .env.example .env
# Edit .env with your credentials
```

### Run Pipeline

```bash
# Full pipeline (fetch, label, analyze, train models, detect ghost jobs)
python orchestration/run_pipeline.py --all

# Or run individual steps
python orchestration/run_pipeline.py --fetch     # Fetch job data
python orchestration/run_pipeline.py --label     # Label roles
python orchestration/run_pipeline.py --eda       # Generate EDA reports
python orchestration/run_pipeline.py --insights  # Market insights
python orchestration/run_pipeline.py --salary    # Salary predictions
python orchestration/run_pipeline.py --ghost-detection  # Detect ghost jobs
```

### Launch Dashboard

```bash
streamlit run app/streamlit_app.py
```

Visit `http://localhost:8501` to explore the dashboard.

## 📁 Project Structure

```
├── ingestion/          # Data collection from Adzuna API
├── processing/         # Data cleaning, labeling, fingerprinting
├── ml/                 # ML models for role classification
├── analysis/           # EDA, insights, ghost job detection
├── orchestration/      # Pipeline runner
├── app/                # Streamlit dashboard
├── tests/              # 53 comprehensive tests
└── data/
    ├── raw/            # Raw API responses
    ├── curated/        # Processed datasets
    └── snapshots/      # Historical data for ghost detection
```

## 🔬 ML Models

### Role Classifier
- **Algorithm**: Logistic Regression
- **Features**: TF-IDF on job descriptions
- **Performance**: 91.6% F1-score, 91.0% precision, 92.3% recall
- **Classes**: Data Engineer, Data Scientist, ML Engineer, Data Analyst

### Salary Predictor
- **Algorithm**: Ridge Regression
- **Features**: Role, country, skills, job description length
- **Performance**: R² = 0.70, MAE = €9,847

### Ghost Job Detector
- **Method**: SHA1 fingerprinting + historical analysis
- **Detects**: Duplicate jobs, frequent reposts, suspicious patterns
- **Retention**: 90-day historical snapshots

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=. --cov-report=term-missing

# Run specific test suite
pytest tests/test_fingerprints.py
```

**Test Coverage**: 53 tests covering fingerprinting, role classification, ghost detection, and pipeline components.

## 📊 Data Sources

- **API**: [Adzuna Job Search API](https://developer.adzuna.com/)
- **Countries**: Austria, Belgium, Germany, Poland, UK
- **Roles**: Data Engineer, Data Scientist, ML Engineer, Data Analyst
- **Update Frequency**: Weekly (via GitHub Actions)

## 🛠️ Tech Stack

- **Python 3.10+**: Core language
- **pandas**: Data manipulation
- **scikit-learn**: ML models
- **Streamlit**: Interactive dashboard
- **pytest**: Testing framework
- **GitHub Actions**: CI/CD automation

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a PR.

## 🔗 Links

- **Live Dashboard**: https://job-reports.streamlit.app/
- **GitHub Repository**: https://github.com/moroianu13/job-market-intelligence
- **Adzuna API**: https://developer.adzuna.com/

---

Made with ❤️ for data professionals exploring the European job market.
