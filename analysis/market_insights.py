from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/curated/jobs_all_labeled.parquet")
    parser.add_argument("--out", default="reports/insights/2026-01-22")
    args = parser.parse_args()

    out_dir = Path(args.out)
    tables = out_dir / "tables"
    ensure_dir(tables)

    df = pd.read_parquet(args.input)

    # Salary mid
    if {"salary_min", "salary_max"}.issubset(df.columns):
        df["salary_mid"] = (df["salary_min"] + df["salary_max"]) / 2

    # --- Top skills by country ---
    if {"country", "skills"}.issubset(df.columns):
        skills_by_country = (
            df[["country", "skills"]]
            .explode("skills")
            .dropna()
            .groupby(["country", "skills"])
            .size()
            .reset_index(name="count")
            .sort_values(["country", "count"], ascending=[True, False])
        )
        skills_by_country.to_csv(tables / "skills_by_country.csv", index=False)

    # --- Top skills by role ---
    if {"roles", "skills"}.issubset(df.columns):
        skills_by_role = (
            df[["roles", "skills"]]
            .explode("roles")
            .explode("skills")
            .dropna()
            .groupby(["roles", "skills"])
            .size()
            .reset_index(name="count")
            .sort_values(["roles", "count"], ascending=[True, False])
        )
        skills_by_role.to_csv(tables / "skills_by_role.csv", index=False)

    # --- Salary by skill (median) ---
    if "salary_mid" in df.columns and "skills" in df.columns:
        salary_by_skill = (
            df[["skills", "salary_mid"]]
            .explode("skills")
            .dropna(subset=["skills", "salary_mid"])
            .groupby("skills")["salary_mid"]
            .median()
            .reset_index(name="median_salary_mid")
            .sort_values("median_salary_mid", ascending=False)
        )
        salary_by_skill.to_csv(tables / "median_salary_by_skill.csv", index=False)

    # Quick summary file
    summary = [
        f"rows={len(df)}",
        f"countries={sorted(df['country'].dropna().unique().tolist()) if 'country' in df else []}",
        f"skills_unique={int(df['skills'].explode().nunique()) if 'skills' in df else 0}",
        f"salary_mid_nonnull={int(df.get('salary_mid', pd.Series(dtype=float)).notna().sum()) if 'salary_mid' in df else 0}",
    ]
    (out_dir / "SUMMARY.txt").write_text("\n".join(summary), encoding="utf-8")

    print(f"✅ Insights saved to: {out_dir}")
    print(f"📁 Tables: {tables}")


if __name__ == "__main__":
    main()
