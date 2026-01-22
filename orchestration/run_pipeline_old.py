from __future__ import annotations

from datetime import datetime
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print(f"\n▶ Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def today() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def main() -> None:
    run_date = today()

    # 1) Ingestion
    run([sys.executable, "ingestion/fetch_adzuna.py"])

    # 2) Normalize + label (roles + skills)
    run([sys.executable, "processing/label_all_jobs.py"])

    # 3) Automated EDA
    run([
        sys.executable,
        "analysis/eda_report.py",
        "--out",
        f"reports/eda/{run_date}",
    ])
    
    run([sys.executable, "analysis/market_insights.py", "--out", f"reports/insights/{run_date}"])
    run([sys.executable, "analysis/salary_model.py", "--out", f"models/salary/{run_date}"])


    print("\n✅ FULL PIPELINE COMPLETED")
    print(f"📊 Reports: reports/eda/{run_date}/REPORT.md")


if __name__ == "__main__":
    main()
