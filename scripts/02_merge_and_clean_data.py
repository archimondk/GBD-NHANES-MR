"""
NHANES 1999-2018 Data Merge & Cleaning Pipeline
===============================================
For GDM + Lead/Mercury + Machine Learning study.

Pipeline:
  1. Read individual XPT files per cycle
  2. Merge cycle-by-cycle (SEQN as key)
  3. Harmonize variable names across cycles
  4. Define GDM outcome (fasting glucose ≥ 5.1 mmol/L or self-reported)
  5. Apply inclusion/exclusion criteria
  6. Handle LOD, survey weights, and missing data
  7. Save processed dataset
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat

warnings.filterwarnings("ignore")

# ── Paths ──────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ── Cycle Metadata ─────────────────────────────────────────────────────────
# (cycle_label, begin_year, suffix_for_filenames)
# NOTE: PBCD/GLU have non-standard names in early cycles; handled in download
CYCLES = [
    ("1999-2000", 1999),
    ("2001-2002", 2001),
    ("2003-2004", 2003),
    ("2005-2006", 2005),
    ("2007-2008", 2007),
    ("2009-2010", 2009),
    ("2011-2012", 2011),
    ("2013-2014", 2013),
    ("2015-2016", 2015),
    ("2017-2018", 2017),
]

COMPONENTS = ["DEMO", "PBCD", "GLU", "RHQ", "BMX"]


# ── Variable Mapping ──────────────────────────────────────────────────────
# NHANES variable names changed across cycles; map to standard names.

EDUCATION_MAP = {
    1: 1,   # Less than 9th grade
    2: 2,   # 9-11th grade (includes 12th grade no diploma)
    3: 3,   # High school graduate/GED
    4: 4,   # Some college or AA degree
    5: 5,   # College graduate or above
    7: np.nan,  # Refused
    9: np.nan,  # Don't know
}

RACE_LABELS = {
    1: "Mexican American",
    2: "Other Hispanic",
    3: "Non-Hispanic White",
    4: "Non-Hispanic Black",
    5: "Other / Multiracial",
}

MARITAL_MAP = {
    1: "Married/Living with partner",
    2: "Widowed/Divorced/Separated",
    3: "Never married",
    77: np.nan,
    99: np.nan,
}

# RHQ160: "Were you told you had diabetes during pregnancy?"
# Present in all cycles. Maps to self-reported GDM.
# 1 = Yes, 2 = No, 7/9 = NA

# ── Read Functions ────────────────────────────────────────────────────────


def read_xpt(cycle_label, component):
    """Read a raw XPT file for a given cycle and component."""
    fpath = RAW_DIR / f"{cycle_label}_{component}.XPT"
    if not fpath.exists():
        print(f"  WARNING: {fpath.name} not found, skipping")
        return None
    df, meta = pyreadstat.read_xport(str(fpath))
    return df


def process_demo(df):
    """Extract and rename demographic variables."""
    cols = {
        "SEQN": "seqn",
        "RIDAGEYR": "age",
        "RIDRETH1": "race_cat",
        "RIDEXPRG": "pregnant",
        "SDMVPSU": "psu",
        "SDMVSTRA": "strata",
        "WTINT2YR": "wt_int_2yr",
        "WTMEC2YR": "wt_mec_2yr",
    }
    # Handle special cases
    if "DMDHSEDU" in df.columns:
        cols["DMDHSEDU"] = "education"
    elif "DMDEDUC2" in df.columns:
        cols["DMDEDUC2"] = "education"
    elif "DMDHSEDZ" in df.columns:
        cols["DMDHSEDZ"] = "education"

    if "WTINT4YR" in df.columns:
        cols["WTINT4YR"] = "wt_int_4yr"
    if "WTMEC4YR" in df.columns:
        cols["WTMEC4YR"] = "wt_mec_4yr"

    # Pregnant variable: 1=pregnant, 2=not pregnant, 3 could be unknown
    available = [c for c in cols if c in df.columns]
    result = df[available].copy()
    result.rename(columns={k: v for k, v in cols.items() if k in available}, inplace=True)
    return result


def process_pbcd(df):
    """Extract blood metal variables."""
    cols = {
        "SEQN": "seqn",
        "LBXBPB": "lead_ugdl",
        "LBDBPBSI": "lead_si",
        "LBXBCD": "cadmium_ugl",
        "LBDBCDSI": "cadmium_si",
        "LBXTHG": "mercury_ugl",
        "LBDTHGSI": "mercury_si",
        "LBDTHGLC": "mercury_lod_code",
        "LBXSEL": "selenium_ugl",
        "LBDSELSI": "selenium_si",
        "LBDBSELC": "selenium_lod_code",
    }
    available = [c for c in cols if c in df.columns]
    result = df[available].copy()
    result.rename(columns={k: v for k, v in cols.items() if k in available}, inplace=True)
    return result


def process_glu(df):
    """Extract fasting glucose data (mmol/L → mg/dL)."""
    cols = {
        "SEQN": "seqn",
        "LBXGLU": "glucose_mgdl",
    }
    # Some cycles use LBDSGLU or other names
    if "LBDSGLU" in df.columns:
        cols["LBDSGLU"] = "glucose_mgdl"
    if "LBXGLUSI" in df.columns:
        cols["LBXGLUSI"] = "glucose_mgdl"

    available = [c for c in cols if c in df.columns]
    if not available or len(available) < 1:
        return None  # No GLU data available
    result = df[available].copy()
    result.rename(columns={k: v for k, v in cols.items() if k in available}, inplace=True)
    return result


def process_rhq(df):
    """Extract reproductive health variables focusing on GDM.

    RHQ160: "During any pregnancy, were you told you had diabetes?"
    RHQ162: More specific GDM question (present in newer cycles)
    """
    cols = {"SEQN": "seqn"}

    # Primary GDM variable: RHQ162 (more specific) in newer cycles
    if "RHQ162" in df.columns:
        cols["RHQ162"] = "gdm_rhq162"
    # RHQ160 present in all cycles
    if "RHQ160" in df.columns:
        cols["RHQ160"] = "gdm_rhq160"
    # Age at menarche for partial fertility
    if "RHQ010" in df.columns:
        cols["RHQ010"] = "age_menarche"
    # Number of pregnancies
    if "RHQ180" in df.columns:
        cols["RHQ180"] = "num_pregnancies"
    # Age at first live birth
    if "RHQ190" in df.columns:
        cols["RHQ190"] = "age_first_birth"

    available = [c for c in cols if c in df.columns]
    if len(available) < 2:  # need at least SEQN + one GDM variable
        return None
    result = df[available].copy()
    result.rename(columns={k: v for k, v in cols.items() if k in available}, inplace=True)
    return result


def process_bmx(df):
    """Extract body measures."""
    cols = {
        "SEQN": "seqn",
        "BMXBMI": "bmi",
        "BMXWAIST": "waist_cm",
        "BMIHT": "height_cm",
        "BMXWT": "weight_kg",
    }
    available = [c for c in cols if c in df.columns]
    result = df[available].copy()
    result.rename(columns={k: v for k, v in cols.items() if k in available}, inplace=True)
    return result


# ── LOD Handling ──────────────────────────────────────────────────────────


def fix_lod_lead(row):
    """Replace lead values below LOD with LOD/sqrt(2).
    LOD for blood lead is typically 0.07 ug/dL (varies by cycle).
    """
    # In most cycles, LOD flag variables tell us if below LOD
    # For simplicity: we flag very low values
    if pd.notna(row.get("lead_ugdl")) and row["lead_ugdl"] < 0.07:
        return 0.07 / np.sqrt(2)
    return row.get("lead_ugdl", np.nan)


def fix_lod_mercury(row):
    """Replace mercury values below LOD with LOD/sqrt(2).
    LOD for blood mercury is typically 0.12 ug/L.
    """
    if pd.notna(row.get("mercury_ugl")) and row["mercury_ugl"] < 0.12:
        return 0.12 / np.sqrt(2)
    return row.get("mercury_ugl", np.nan)


def fix_lod_cadmium(row):
    """Replace cadmium values below LOD with LOD/sqrt(2)."""
    if pd.notna(row.get("cadmium_ugl")) and row["cadmium_ugl"] < 0.1:
        return 0.1 / np.sqrt(2)
    return row.get("cadmium_ugl", np.nan)


# ── Main Pipeline ─────────────────────────────────────────────────────────


def main():
    print("=" * 60)
    print("NHANES 1999-2018 Merge & Clean Pipeline")
    print("=" * 60)

    all_frames = []
    total_initial = 0

    for cycle_label, begin_year in CYCLES:
        print(f"\n-- Processing {cycle_label} --")

        # Read all components
        demo = process_demo(read_xpt(cycle_label, "DEMO"))
        pbcd = process_pbcd(read_xpt(cycle_label, "PBCD"))
        glu = process_glu(read_xpt(cycle_label, "GLU"))
        rhq = process_rhq(read_xpt(cycle_label, "RHQ"))
        bmx = process_bmx(read_xpt(cycle_label, "BMX"))

        # Merge step-by-step on SEQN
        merged = demo.copy()
        n0 = len(merged)

        if pbcd is not None:
            merged = merged.merge(pbcd, on="seqn", how="left")
        if bmx is not None:
            merged = merged.merge(bmx, on="seqn", how="left")
        if glu is not None:
            merged = merged.merge(glu, on="seqn", how="left")
        if rhq is not None:
            merged = merged.merge(rhq, on="seqn", how="left")

        merged["cycle"] = cycle_label
        merged["begin_year"] = begin_year

        total_initial += n0
        all_frames.append(merged)
        print(f"  Merged: {len(merged)} rows (from {n0} DEMO)")

    # ── Combine Across Cycles ──────────────────────────────────────────
    print("\n-- Combining across cycles --")
    full = pd.concat(all_frames, ignore_index=True)
    print(f"  Combined: {len(full)} rows")

    # ── Variable Harmonization ─────────────────────────────────────────
    # Harmonize education
    if "education" in full.columns:
        full["education"] = full["education"].map(EDUCATION_MAP)
    else:
        full["education"] = np.nan

    # Simplify race: 1-2 Hispanic, 3 White, 4 Black, 5 Other
    full["race_group"] = full["race_cat"].map({
        1: "Hispanic", 2: "Hispanic",
        3: "Non-Hispanic White",
        4: "Non-Hispanic Black",
        5: "Other / Multiracial",
    })

    # ── GDM Outcome Definition ─────────────────────────────────────────
    # GDM = (fasting glucose >= 5.1 mmol/L) OR (self-reported GDM)
    # LBXGLU is in mg/dL. 5.1 mmol/L = 91.8 mg/dL
    full["gdm_glucose"] = (
        full["glucose_mgdl"].notna()
        & (full["glucose_mgdl"] >= 91.8)
    ).astype(int)

    # Self-reported GDM (RHQ160: 1 = Yes)
    full["gdm_self_report"] = (full["gdm_rhq160"] == 1).astype(int)

    # If RHQ162 exists and is more specific, use it as supplement
    if "gdm_rhq162" in full.columns:
        full["gdm_rhq162_flag"] = (full["gdm_rhq162"] == 1).astype(int)
        full["gdm_self_report"] = (
            full["gdm_self_report"] | full["gdm_rhq162_flag"]
        ).astype(int)

    # Combined GDM
    full["gdm"] = (full["gdm_glucose"] | full["gdm_self_report"]).astype(int)

    # ── Survey Weights ─────────────────────────────────────────────────
    # 1999-2000: use WTMEC4YR (4-year weight), divide by 2 (10 cycles)
    # Others: use WTMEC2YR (2-year weight)
    # Combined weights: wt × (2 / 10) = wt × 0.2
    full["wt_final"] = np.where(
        full["cycle"] == "1999-2000",
        full["wt_mec_4yr"] * 0.2,
        full["wt_mec_2yr"] * 0.2,
    )

    # ── LOD Handling for Metals ────────────────────────────────────────
    full["lead_ugdl"] = full.apply(fix_lod_lead, axis=1)
    full["mercury_ugl"] = full.apply(fix_lod_mercury, axis=1)
    full["cadmium_ugl"] = full.apply(fix_lod_cadmium, axis=1)

    # Log-transform metals for models
    full["lead_log"] = np.log(full["lead_ugdl"] + 1e-6)
    full["mercury_log"] = np.log(full["mercury_ugl"] + 1e-6)
    full["cadmium_log"] = np.log(full["cadmium_ugl"] + 1e-6)
    if "selenium_ugl" in full.columns:
        full["selenium_log"] = np.log(full["selenium_ugl"] + 1e-6)

    # ── Outcome Labels ─────────────────────────────────────────────────
    full["gdm_label"] = full["gdm"].map({1: "GDM", 0: "No GDM"})

    # ── Save ───────────────────────────────────────────────────────────
    # Save full merged dataset
    out_path = PROCESSED_DIR / "nhanes_gdm_merged.pkl"
    full.to_pickle(out_path)
    print(f"\nSaved: {out_path}")

    # Save a CSV preview too
    csv_path = PROCESSED_DIR / "nhanes_gdm_merged.csv"
    full.to_csv(csv_path, index=False)
    print(f"Saved: {csv_path}")

    # ── Summary Stats ──────────────────────────────────────────────────
    print("\n-- Quick Summary --")
    print(f"  Age range: {full['age'].min():.0f} - {full['age'].max():.0f}")
    print(f"  Female (with RIDEXPRG): {(full['pregnant'].notna()).sum():,}")
    print(f"  Pregnant (RIDEXPRG==1): {(full['pregnant']==1).sum():,}")
    print(f"  Self-reported GDM: {(full['gdm_self_report']==1).sum():,}")
    print(f"  High glucose (GDM): {(full['gdm_glucose']==1).sum():,}")
    print(f"  Combined GDM: {full['gdm'].sum():,}")
    print(f"  Blood lead available: {full['lead_ugdl'].notna().sum():,}")
    print(f"  Blood mercury available: {full['mercury_ugl'].notna().sum():,}")

    print("\nDone!")


if __name__ == "__main__":
    main()
