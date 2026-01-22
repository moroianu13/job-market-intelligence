.PHONY: help install test pipeline demo ui docker-build docker-run clean

# Default target
help:
	@echo "Job Market Intelligence - Makefile Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install dependencies"
	@echo "  make test             Run test suite"
	@echo ""
	@echo "Pipeline:"
	@echo "  make fetch            Fetch data from Adzuna API"
	@echo "  make label            Label jobs with roles and skills"
	@echo "  make eda              Generate EDA report"
	@echo "  make salary           Train salary model"
	@echo "  make train-ml         Train ML role classifier"
	@echo "  make pipeline         Run full pipeline"
	@echo "  make demo             Generate demo report"
	@echo ""
	@echo "UI:"
	@echo "  make ui               Launch Streamlit dashboard"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     Build Docker image"
	@echo "  make docker-pipeline  Run pipeline in Docker"
	@echo "  make docker-ui        Launch UI in Docker"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean            Remove generated files"
	@echo "  make clean-all        Remove all data, models, and reports"

# Setup
install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

# Pipeline steps
fetch:
	python ingestion/fetch_adzuna.py

label:
	python processing/label_all_jobs.py

label-ml:
	python processing/label_all_jobs.py --ml

eda:
	python analysis/eda_report.py

salary:
	python analysis/salary_model.py --out models/salary/$$(date +%Y-%m-%d)

train-ml:
	python ml/role_classifier/train_classifier.py \
		--data data/curated/jobs_all_labeled.parquet \
		--out models/role_classifier/$$(date +%Y-%m-%d)

pipeline:
	python orchestration/run_pipeline.py --all

pipeline-ml:
	python orchestration/run_pipeline.py --all --ml

demo:
	python demo/showcase.py

# UI
ui:
	streamlit run app/streamlit_app.py

# Docker
docker-build:
	docker build -t job-intelligence .

docker-pipeline:
	docker-compose run --rm pipeline python orchestration/run_pipeline.py --all

docker-ui:
	docker-compose up streamlit

docker-down:
	docker-compose down

# Cleaning
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

clean-all: clean
	rm -rf data/raw/adzuna/*
	rm -rf data/curated/*
	rm -rf models/*
	rm -rf reports/*
	@echo "⚠️  All data, models, and reports removed!"
