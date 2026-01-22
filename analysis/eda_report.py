from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import json

import pandas as pd
import matplotlib.pyplot as plt


@dataclass(frozen=True)
class EDAConfig:
    input_path: Path
    out_dir: Path


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _save_table(df: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)


def _save_plot(fig, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def run_eda(cfg: EDAConfig) -> None:
    _ensure_dir(cfg.out_dir)
    figs_dir = cfg.out_dir / "figures"
    tables_dir = cfg.out_dir / "tables"
    _ensure_dir(figs_dir)
    _ensure_dir(tables_dir)

    df = pd.read_parquet(cfg.input_path)

    # --------- Basic snapshot ----------
    snapshot = {
        "rows": int(len(df)),
        "columns": list(df.columns),
        "countries": sorted(df["country"].dropna().unique().tolist()) if "country" in df else [],
        "roles_unique": int(df["roles"].explode().nunique()) if "roles" in df else 0,
        "skills_unique": int(df["skills"].explode().nunique()) if "skills" in df else 0,
    }
    (cfg.out_dir / "snapshot.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

    # --------- Demand: roles by country ----------
    if "roles" in df and "country" in df:
        roles_country = (
            df[["country", "roles"]]
            .explode("roles")
            .dropna()
            .groupby(["country", "roles"])
            .size()
            .reset_index(name="count")
            .sort_values(["country", "count"], ascending=[True, False])
        )
        _save_table(roles_country, tables_dir / "roles_by_country.csv")

        # Plot: Top 10 roles per country (one figure per country)
        for c in sorted(df["country"].dropna().unique()):
            sub = roles_country[roles_country["country"] == c].head(10)
            if sub.empty:
                continue
            fig = plt.figure()
            plt.barh(sub["roles"][::-1], sub["count"][::-1])
            plt.title(f"Top roles in {c} (count)")
            plt.xlabel("count")
            _save_plot(fig, figs_dir / f"top_roles_{c}.png")

    # --------- Demand: skills overall + by country ----------
    if "skills" in df:
        skills_overall = (
            df["skills"].explode().dropna().value_counts().reset_index()
        )
        skills_overall.columns = ["skill", "count"]
        _save_table(skills_overall, tables_dir / "skills_overall.csv")

        fig = plt.figure()
        top = skills_overall.head(20)
        plt.barh(top["skill"][::-1], top["count"][::-1])
        plt.title("Top skills (overall)")
        plt.xlabel("count")
        _save_plot(fig, figs_dir / "top_skills_overall.png")

        if "country" in df:
            skills_country = (
                df[["country", "skills"]]
                .explode("skills")
                .dropna()
                .groupby(["country", "skills"])
                .size()
                .reset_index(name="count")
                .sort_values(["country", "count"], ascending=[True, False])
            )
            _save_table(skills_country, tables_dir / "skills_by_country.csv")

    # --------- Salary coverage + salary stats ----------
    if {"salary_min", "salary_max"}.issubset(df.columns):
        df["salary_mid"] = (df["salary_min"] + df["salary_max"]) / 2

        salary_cov = pd.DataFrame(
            {
                "salary_min_nonnull": [int(df["salary_min"].notna().sum())],
                "salary_max_nonnull": [int(df["salary_max"].notna().sum())],
                "salary_mid_nonnull": [int(df["salary_mid"].notna().sum())],
                "rows_total": [int(len(df))],
            }
        )
        _save_table(salary_cov, tables_dir / "salary_coverage.csv")

        # Salary by role (median) where available
        if "roles" in df:
            salary_by_role = (
                df[["roles", "salary_mid"]]
                .explode("roles")
                .dropna(subset=["salary_mid", "roles"])
                .groupby("roles")["salary_mid"]
                .median()
                .reset_index(name="median_salary_mid")
                .sort_values("median_salary_mid", ascending=False)
            )
            _save_table(salary_by_role, tables_dir / "median_salary_by_role.csv")

    # --------- Simple Markdown report ----------
    md = []
    md.append("# EDA Report\n")
    md.append(f"- Rows: **{snapshot['rows']}**\n")
    md.append(f"- Countries: **{', '.join(snapshot['countries'])}**\n")
    md.append(f"- Unique roles: **{snapshot['roles_unique']}**\n")
    md.append(f"- Unique skills: **{snapshot['skills_unique']}**\n\n")

    md.append("## Figures\n")
    md.append("- `figures/top_skills_overall.png`\n")
    if snapshot["countries"]:
        md.append("- `figures/top_roles_<country>.png`\n")

    md.append("\n## Tables\n")
    md.append("- `tables/roles_by_country.csv`\n")
    md.append("- `tables/skills_overall.csv`\n")
    md.append("- `tables/skills_by_country.csv`\n")
    md.append("- `tables/salary_coverage.csv`\n")
    md.append("- `tables/median_salary_by_role.csv`\n")

    (cfg.out_dir / "REPORT.md").write_text("".join(md), encoding="utf-8")

    print(f"✅ EDA saved to: {cfg.out_dir}")
    print(f"✅ Snapshot: {cfg.out_dir / 'snapshot.json'}")
    print(f"✅ Report: {cfg.out_dir / 'REPORT.md'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Automated EDA report for labeled jobs dataset")
    parser.add_argument(
        "--input",
        default="data/curated/jobs_all_labeled.parquet",
        help="Path to curated labeled parquet",
    )
    parser.add_argument(
        "--out",
        default="reports/eda",
        help="Output folder for EDA report artifacts",
    )
    args = parser.parse_args()

    cfg = EDAConfig(input_path=Path(args.input), out_dir=Path(args.out))
    run_eda(cfg)


if __name__ == "__main__":
    main()
