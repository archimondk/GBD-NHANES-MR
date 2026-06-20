"""
NHANES GDM Study - EDA, Table 1, and Descriptive Figures
=========================================================
Generates:
  - Inclusion criteria filtering
  - Table 1 (baseline characteristics by GDM status)
  - Exploratory figures (distributions, trends, correlations)
  - Summary statistics for the paper's Results section
"""

import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

warnings.filterwarnings("ignore")

# ── Paths ──────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
FIG_DIR = PROJECT_ROOT / "output" / "figures"
TBL_DIR = PROJECT_ROOT / "output" / "tables"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TBL_DIR.mkdir(parents=True, exist_ok=True)

sns.set_style("whitegrid")
plt.rcParams.update({"figure.max_open_warning": 0, "font.size": 11})


# ── Load Data ─────────────────────────────────────────────────────────────
def load_data():
    """Load merged dataset and apply inclusion/exclusion criteria."""
    df = pd.read_pickle(DATA_DIR / "nhanes_gdm_merged.pkl")
    print(f"Loaded: {len(df):,} rows")

    # Inclusion criteria:
    # 1. Female (RIDEXPRG is only coded for females)
    # 2. Reproductive age: 15-49 years (GDM can occur up to ~49)
    # 3. Has GDM outcome data (either glucose or self-report)
    # 4. Has at least one metal measurement (lead or mercury)

    n0 = len(df)
    sub = df[df["pregnant"].notna()].copy()
    n1 = len(sub)
    print(f"  Female only (RIDEXPRG not null): {n1:,} (removed {n0-n1:,})")

    sub = sub[(sub["age"] >= 15) & (sub["age"] <= 49)].copy()
    n2 = len(sub)
    print(f"  Age 15-49: {n2:,} (removed {n1-n2:,})")

    # Has GDM outcome
    has_gdm = sub["gdm_self_report"].notna() | sub["gdm_glucose"].notna()
    n_before_gdm = len(sub)
    sub = sub[has_gdm].copy()
    n3 = len(sub)
    print(f"  Has GDM outcome: {n3:,} (removed {n_before_gdm-n3:,})")

    # Has at least one metal measurement
    has_lead = sub["lead_ugdl"].notna()
    has_hg = sub["mercury_ugl"].notna()
    has_metal = has_lead | has_hg
    sub = sub[has_metal].copy()
    n4 = len(sub)
    print(f"  Has metal data: {n4:,} (removed {n3-n4:,})")

    print(f"\nFinal analytic sample: {n4:,} women aged 15-49")

    # Recode variables
    sub["gdm"] = sub["gdm"].astype(int)
    sub["gdm_label"] = sub["gdm"].map({1: "GDM", 0: "No GDM"})
    sub["pregnant_flag"] = sub["pregnant"] == 1

    # Race simplified
    sub["race"] = sub["race_group"]

    # Metal tertiles for table
    sub["lead_tertile"] = pd.qcut(sub["lead_ugdl"].rank(method="first"),
                                   q=3, labels=["T1 (Low)", "T2 (Mid)", "T3 (High)"])
    sub["mercury_tertile"] = pd.qcut(sub["mercury_ugl"].rank(method="first"),
                                      q=3, labels=["T1 (Low)", "T2 (Mid)", "T3 (High)"])

    return sub


# ── Theme ──────────────────────────────────────────────────────────────────
TITLE_FONT = 13
AXIS_FONT = 11
GDM_COLORS = {"No GDM": "#4A90D9", "GDM": "#D94A4A"}


# ── Table 1 ───────────────────────────────────────────────────────────────
def make_table1(df):
    """Create Table 1: Baseline characteristics by GDM status."""
    print("\n-- Generating Table 1 --")

    def describe_var(var, data, fmt=".1f"):
        """Weighted or unweighted description."""
        vals = data[var].dropna()
        if np.issubdtype(vals.dtype, np.number):
            mean = vals.mean()
            std = vals.std()
            return f"{mean:{fmt}} ({std:{fmt}})"
        else:
            return vals.value_counts(normalize=True).to_dict()

    rows = []

    # Overall N
    for label, grp in [("Overall", df), ("No GDM", df[df["gdm"] == 0]),
                       ("GDM", df[df["gdm"] == 1])]:
        n = len(grp)
        rows.append({
            "Characteristic": f"N",
            "Overall": f"{len(df):,}" if label == "Overall" else "",
            "No GDM": f"{len(df[df['gdm']==0]):,}" if label == "No GDM" else "",
            "GDM": f"{len(df[df['gdm']==1]):,}" if label == "GDM" else "",
        })
        break

    # Continuous vars
    cont_vars = [
        ("Age (years)", "age"),
        ("BMI (kg/m²)", "bmi"),
        ("Waist circumference (cm)", "waist_cm"),
        ("Blood lead (μg/dL)", "lead_ugdl"),
        ("Blood mercury (μg/L)", "mercury_ugl"),
        ("Blood cadmium (μg/L)", "cadmium_ugl"),
    ]

    for label, var in cont_vars:
        for grp_name, grp_df in [("Overall", df), ("No GDM", df[df["gdm"] == 0]),
                                  ("GDM", df[df["gdm"] == 1])]:
            vals = grp_df[var].dropna()
            if len(vals) == 0:
                continue
            if grp_name == "Overall":
                q25, q50, q75 = vals.quantile([0.25, 0.50, 0.75])
                rows.append({
                    "Characteristic": label,
                    "Overall": f"{vals.mean():.2f} ({vals.std():.2f})",
                    "No GDM": "",
                    "GDM": "",
                })
                rows.append({
                    "Characteristic": "  Median (IQR)",
                    "Overall": f"{q50:.2f} ({q25:.2f}–{q75:.2f})",
                    "No GDM": "",
                    "GDM": "",
                })
            elif grp_name == "No GDM":
                # Fill in the No GDM cell for the previous row
                for r in reversed(rows):
                    if r["Characteristic"] == label:
                        r["No GDM"] = f"{vals.mean():.2f} ({vals.std():.2f})"
                        break
            else:  # GDM
                for r in reversed(rows):
                    if r["Characteristic"] == label:
                        r["GDM"] = f"{vals.mean():.2f} ({vals.std():.2f})"
                        break

    # Categorical vars
    cat_vars = [
        ("Race/Ethnicity", "race"),
        ("Education Level", "education"),
        ("Currently pregnant", "pregnant_flag"),
    ]

    for label, var in cat_vars:
        for grp_name, grp_df in [("Overall", df), ("No GDM", df[df["gdm"] == 0]),
                                  ("GDM", df[df["gdm"] == 1])]:
            vals = grp_df[var].dropna()
            if len(vals) == 0:
                continue
            if grp_name == "Overall":
                dist = vals.value_counts(normalize=True)
                rows.append({"Characteristic": label, "Overall": "",
                             "No GDM": "", "GDM": ""})
                for cat in dist.index[:6]:  # top 6 categories
                    pct = dist[cat] * 100
                    n_cat = (vals == cat).sum()
                    rows.append({
                        "Characteristic": f"  {cat}",
                        "Overall": f"{n_cat} ({pct:.1f}%)",
                        "No GDM": "",
                        "GDM": "",
                    })
            elif grp_name == "No GDM":
                dist = vals.value_counts(normalize=True)
                for cat in dist.index[:6]:
                    n_cat = (vals == cat).sum()
                    pct = dist[cat] * 100
                    for r in rows:
                        if r["Characteristic"] == f"  {cat}":
                            r["No GDM"] = f"{n_cat} ({pct:.1f}%)"
                            break
            else:
                dist = vals.value_counts(normalize=True)
                for cat in dist.index[:6]:
                    n_cat = (vals == cat).sum()
                    pct = dist[cat] * 100
                    for r in rows:
                        if r["Characteristic"] == f"  {cat}":
                            r["GDM"] = f"{n_cat} ({pct:.1f}%)"
                            break

    table1 = pd.DataFrame(rows)
    out_path = TBL_DIR / "table1_baseline_characteristics.csv"
    table1.to_csv(out_path, index=False)
    print(f"  Saved: {out_path}")
    return table1


# ── Figures ───────────────────────────────────────────────────────────────
def fig_distribution(df):
    """Figure 1: Distribution of blood lead and mercury by GDM status."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    for i, (metal, label, unit) in enumerate([
        ("lead_ugdl", "Blood Lead", "μg/dL"),
        ("mercury_ugl", "Blood Mercury", "μg/L"),
    ]):
        vals = df[metal].dropna()
        vals_log = np.log1p(vals)

        # Histogram
        ax = axes[i, 0]
        for gdm_val, gdm_lbl in [(0, "No GDM"), (1, "GDM")]:
            subset = df[df["gdm"] == gdm_val][metal].dropna()
            ax.hist(subset, bins=60, alpha=0.6, density=True,
                    label=gdm_lbl, color=GDM_COLORS[gdm_lbl])
        ax.set_xlabel(f"{label} ({unit})", fontsize=AXIS_FONT)
        ax.set_ylabel("Density", fontsize=AXIS_FONT)
        ax.set_title(f"{label} Distribution by GDM Status", fontsize=TITLE_FONT)
        ax.legend(fontsize=10)

        # Log-transformed
        ax = axes[i, 1]
        for gdm_val, gdm_lbl in [(0, "No GDM"), (1, "GDM")]:
            subset = np.log1p(df[df["gdm"] == gdm_val][metal].dropna())
            ax.hist(subset, bins=50, alpha=0.6, density=True,
                    label=gdm_lbl, color=GDM_COLORS[gdm_lbl])
        ax.set_xlabel(f"log({label} + 1)", fontsize=AXIS_FONT)
        ax.set_ylabel("Density", fontsize=AXIS_FONT)
        ax.set_title(f"{label} (log-transformed)", fontsize=TITLE_FONT)
        ax.legend(fontsize=10)

    plt.tight_layout()
    path = FIG_DIR / "fig1_distributions.png"
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def fig_boxplots(df):
    """Figure 2: Boxplots of metal levels by GDM status."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))

    metals = [
        ("lead_ugdl", "Blood Lead (μg/dL)"),
        ("mercury_ugl", "Blood Mercury (μg/L)"),
        ("cadmium_ugl", "Blood Cadmium (μg/L)"),
    ]

    for ax, (metal, label) in zip(axes, metals):
        data = df[df[metal].notna()].copy()
        # Log scale for better visualization
        data["value"] = np.log1p(data[metal])
        sns.boxplot(x="gdm_label", y="value", data=data, ax=ax,
                    palette=GDM_COLORS, width=0.5)
        ax.set_xlabel("")
        ax.set_ylabel(f"log({label}+1)", fontsize=AXIS_FONT)
        ax.set_title(label, fontsize=TITLE_FONT)

    plt.tight_layout()
    path = FIG_DIR / "fig2_metal_boxplots_by_gdm.png"
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def fig_temporal_trend(df):
    """Figure 3: GDM prevalence and metal levels over time."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # GDM prevalence by cycle
    ax = axes[0]
    cycle_data = df.groupby("cycle").agg(
        gdm_n=("gdm", "sum"),
        total=("gdm", "count"),
    )
    cycle_data["prev"] = cycle_data["gdm_n"] / cycle_data["total"] * 100

    years = [c[:4] for c in cycle_data.index]
    ax.plot(years, cycle_data["prev"].values, "o-", color="#2C3E50",
            linewidth=2, markersize=8)
    ax.set_xticks(range(len(years)))
    ax.set_xticklabels(years, rotation=45, fontsize=9)
    ax.set_ylabel("GDM Prevalence (%)", fontsize=AXIS_FONT)
    ax.set_title("GDM Prevalence by NHANES Cycle", fontsize=TITLE_FONT)

    # Metal levels over time
    ax = axes[1]
    for metal, label, color in [
        ("lead_ugdl", "Blood Lead", "#3498DB"),
        ("mercury_ugl", "Blood Mercury", "#E74C3C"),
    ]:
        means = df.groupby("cycle")[metal].mean()
        ax.plot(years, means.values, "o-", label=label,
                color=color, linewidth=2, markersize=8)
    ax.set_xticks(range(len(years)))
    ax.set_xticklabels(years, rotation=45, fontsize=9)
    ax.set_ylabel("Mean Metal Level", fontsize=AXIS_FONT)
    ax.set_title("Metal Levels Over Time", fontsize=TITLE_FONT)
    ax.legend(fontsize=10)

    plt.tight_layout()
    path = FIG_DIR / "fig3_temporal_trends.png"
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def fig_correlation_matrix(df):
    """Figure 4: Correlation matrix of key variables."""
    corr_vars = ["age", "bmi", "waist_cm", "lead_ugdl", "mercury_ugl",
                 "cadmium_ugl", "gdm"]
    available = [v for v in corr_vars if v in df.columns]
    corr_df = df[available].dropna()
    corr_df.columns = [c.replace("_ugdl", "").replace("_ugl", "")
                        .replace("_cm", "").replace("_flag", "")
                        for c in corr_df.columns]

    fig, ax = plt.subplots(figsize=(9, 7))
    cmap = sns.diverging_palette(240, 10, as_cmap=True)
    sns.heatmap(corr_df.corr(), annot=True, fmt=".2f", cmap=cmap,
                vmin=-0.5, vmax=0.5, center=0, square=True,
                linewidths=0.5, ax=ax, cbar_kws={"shrink": 0.8})
    ax.set_title("Correlation Matrix", fontsize=TITLE_FONT)
    plt.tight_layout()
    path = FIG_DIR / "fig4_correlation_matrix.png"
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


# ── Summary Stats for Results ─────────────────────────────────────────────
def print_summary_stats(df):
    """Print summary statistics for the paper's Results section."""
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS FOR RESULTS SECTION")
    print("=" * 60)

    gdm_yes = df[df["gdm"] == 1]
    gdm_no = df[df["gdm"] == 0]

    print(f"\nStudy Population:")
    print(f"  Total analytic sample: {len(df):,}")
    print(f"  GDM cases: {len(gdm_yes):,} ({len(gdm_yes)/len(df)*100:.1f}%)")
    print(f"  Non-GDM: {len(gdm_no):,} ({len(gdm_no)/len(df)*100:.1f}%)")
    print(f"  Mean age (SD): {df['age'].mean():.1f} ({df['age'].std():.1f})")

    print(f"\nBlood Metals (geometric mean, μg/dL or μg/L):")
    for metal, label in [("lead_ugdl", "Lead"), ("mercury_ugl", "Mercury"),
                          ("cadmium_ugl", "Cadmium")]:
        vals = df[metal].dropna()
        gm = np.exp(np.log(vals).mean())
        gdm_vals = gdm_yes[metal].dropna()
        ngdm_vals = gdm_no[metal].dropna()
        print(f"  {label}: GM = {gm:.3f}, "
              f"GDM mean = {gdm_vals.mean():.3f}, "
              f"No GDM mean = {ngdm_vals.mean():.3f}")

    print(f"\nBy Race/Ethnicity:")
    for race in df["race"].dropna().unique():
        sub = df[df["race"] == race]
        gdm_rate = sub["gdm"].mean() * 100
        print(f"  {race}: {len(sub):,} ({gdm_rate:.1f}% GDM)")


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("NHANES GDM Study - Exploratory Data Analysis")
    print("=" * 60)

    df = load_data()

    # Table 1
    table1 = make_table1(df)
    print(table1.to_string(index=False))

    # Figures
    print("\n-- Generating Figures --")
    fig_distribution(df)
    fig_boxplots(df)
    fig_temporal_trend(df)
    fig_correlation_matrix(df)

    # Summary
    print_summary_stats(df)

    print("\nAll EDA outputs saved to:")
    print(f"  Figures: {FIG_DIR}")
    print(f"  Tables: {TBL_DIR}")
    print("Done!")


if __name__ == "__main__":
    main()
