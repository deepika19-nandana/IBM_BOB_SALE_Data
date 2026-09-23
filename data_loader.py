"""
data_loader.py
--------------
Handles CSV loading, data cleaning, validation, and quality reporting.
"""

import pandas as pd
import numpy as np
from pathlib import Path


# ── Column expectations ────────────────────────────────────────────────────────
EXPECTED_COLUMNS = [
    "Product_ID", "Sale_Date", "Sales_Rep", "Region", "Sales_Amount",
    "Quantity_Sold", "Product_Category", "Unit_Cost", "Unit_Price",
    "Customer_Type", "Discount", "Payment_Method", "Sales_Channel",
    "Region_and_Sales_Rep",
]

NUMERIC_COLS  = ["Sales_Amount", "Quantity_Sold", "Unit_Cost", "Unit_Price", "Discount"]
CATEGORY_COLS = ["Sales_Rep", "Region", "Product_Category", "Customer_Type",
                 "Payment_Method", "Sales_Channel"]


def load_raw(filepath: str | Path) -> pd.DataFrame:
    """Load CSV and return as a raw DataFrame."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    df = pd.read_csv(path)
    return df


def audit_quality(df: pd.DataFrame) -> dict:
    """
    Return a quality-audit dictionary before cleaning so the UI
    can display what was found and fixed.
    """
    report = {}

    # Missing / null values per column
    null_counts = df.isnull().sum()
    report["null_counts"] = null_counts[null_counts > 0].to_dict()
    report["total_nulls"] = int(null_counts.sum())

    # Duplicate rows
    report["duplicate_rows"] = int(df.duplicated().sum())

    # Negative / zero values in numeric cols that must be positive
    report["negative_sales"]    = int((df["Sales_Amount"]  <= 0).sum()) if "Sales_Amount"  in df.columns else 0
    report["negative_quantity"] = int((df["Quantity_Sold"] <= 0).sum()) if "Quantity_Sold" in df.columns else 0

    # Discount out of range [0, 1]
    if "Discount" in df.columns:
        report["bad_discount"] = int(((df["Discount"] < 0) | (df["Discount"] > 1)).sum())
    else:
        report["bad_discount"] = 0

    # Unparseable dates
    if "Sale_Date" in df.columns:
        parsed = pd.to_datetime(df["Sale_Date"], errors="coerce")
        report["bad_dates"] = int(parsed.isnull().sum())
    else:
        report["bad_dates"] = 0

    # Missing expected columns
    report["missing_columns"] = [c for c in EXPECTED_COLUMNS if c not in df.columns]

    return report


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all cleaning steps and return a clean DataFrame.
    Steps performed:
      1. Strip whitespace from string columns
      2. Parse Sale_Date as datetime
      3. Coerce numeric columns to float
      4. Drop duplicate rows
      5. Drop rows where Sales_Amount or Quantity_Sold are null / non-positive
      6. Clip Discount to [0, 1]
      7. Fill remaining nulls in categoricals with 'Unknown'
      8. Add derived columns: Month, Quarter, Profit, Profit_Margin, Revenue
    """
    df = df.copy()

    # 1. Strip whitespace
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    # 2. Parse dates
    df["Sale_Date"] = pd.to_datetime(df["Sale_Date"], errors="coerce")

    # 3. Coerce numeric columns
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 4. Drop duplicates
    df = df.drop_duplicates()

    # 5. Drop rows where core numeric values are invalid
    df = df.dropna(subset=["Sales_Amount", "Quantity_Sold"])
    df = df[df["Sales_Amount"] > 0]
    df = df[df["Quantity_Sold"] > 0]

    # 6. Clip discount
    if "Discount" in df.columns:
        df["Discount"] = df["Discount"].clip(lower=0.0, upper=1.0)

    # 7. Fill categorical nulls
    for col in CATEGORY_COLS:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown")

    # 8. Derived columns
    if "Unit_Price" in df.columns and "Unit_Cost" in df.columns:
        df["Profit"]        = (df["Unit_Price"] - df["Unit_Cost"]) * df["Quantity_Sold"]
        df["Profit_Margin"] = np.where(
            df["Unit_Price"] > 0,
            (df["Unit_Price"] - df["Unit_Cost"]) / df["Unit_Price"],
            np.nan,
        )

    df["Revenue"] = df["Sales_Amount"]   # alias for clarity

    # 9. Time dimensions
    df["Month"]   = df["Sale_Date"].dt.to_period("M").astype(str)
    df["Quarter"] = df["Sale_Date"].dt.to_period("Q").astype(str)
    df["Month_Num"] = df["Sale_Date"].dt.month

    df = df.reset_index(drop=True)
    return df


def load_and_clean(filepath: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Convenience wrapper.
    Returns (raw_df, clean_df, quality_report).
    """
    raw   = load_raw(filepath)
    audit = audit_quality(raw)
    clean_df = clean(raw)
    return raw, clean_df, audit
