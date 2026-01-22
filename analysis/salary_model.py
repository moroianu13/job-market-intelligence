from __future__ import annotations

import argparse
from pathlib import Path
import joblib

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer


def list_to_str(x) -> str:
    """Convert list or array to space-separated string."""
    if hasattr(x, '__iter__') and not isinstance(x, str):
        items = [str(item) for item in x if item]
        return " ".join(sorted(set(items))) if items else ""
    return ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/curated/jobs_all_labeled.parquet")
    parser.add_argument("--out", default="models/salary")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(args.input)

    # Target
    df["salary_mid"] = (df["salary_min"] + df["salary_max"]) / 2
    df = df[(df["salary_mid"] >= 10000) & (df["salary_mid"] <= 300000)]
    df = df.dropna(subset=["salary_mid"])

    if df.empty:
        raise RuntimeError("No salary data available for training.")

    # Features
    df["roles_txt"] = df["roles"].apply(list_to_str)
    df["skills_txt"] = df["skills"].apply(list_to_str)
    df["title_txt"] = df["title"].fillna("").astype(str)
    
    # Fill empty roles with a placeholder to avoid empty vocabulary errors
    df["roles_txt"] = df["roles_txt"].replace("", "no_role")
    # Keep empty string for skills (no placeholder needed)

    X = df[["country", "roles_txt", "skills_txt", "title_txt"]]
    y = df["salary_mid"]  # Use actual salary, not log-transformed

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("country", CountVectorizer(), "country"),
            ("roles", TfidfVectorizer(min_df=1), "roles_txt"),
            ("skills", CountVectorizer(min_df=1), "skills_txt"),
            ("title", TfidfVectorizer(ngram_range=(1, 2), min_df=2), "title_txt"),
        ]
    )

    model = Pipeline(
        steps=[
            ("prep", preprocessor),
            ("reg", Ridge(alpha=10.0)),
        ]
    )

    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    metrics = {
        "rows_total": int(len(df)),
        "mae": float(mae),
        "r2": float(r2),
    }

    # Evaluate by country
    test = X_test.copy()
    test["y_true_salary"] = y_test.values
    test["y_pred_salary"] = preds

    by_country = (
        test.groupby("country")
        .apply(
            lambda g: pd.Series({
                "n": len(g),
                "mae_salary": mean_absolute_error(g["y_true_salary"], g["y_pred_salary"]),
            }),
            include_groups=False
        )
        .reset_index()
        .sort_values("n", ascending=False)
    )

    by_country.to_csv(out_dir / "metrics_by_country.csv", index=False)
    test.head(200).to_csv(out_dir / "predictions_sample.csv", index=False)

    joblib.dump(model, out_dir / "salary_model.joblib")
    (out_dir / "metrics.json").write_text(
        pd.Series(metrics).to_json(indent=2), encoding="utf-8"
    )

    print("✅ Salary model trained")
    print(f"📉 MAE: €{mae:,.0f}")
    print(f"📈 R²: {r2:.3f}")
    print(f"💾 Saved to: {out_dir}")
    print(f"\nMetrics by country (n >= 10):")
    print(by_country[by_country["n"] >= 10].to_string(index=False))


if __name__ == "__main__":
    main()
