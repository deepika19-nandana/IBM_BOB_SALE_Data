"""
analysis.py
-----------
All analytical computations: KPIs, groupings, correlations, and
business-insight generation.
"""

import pandas as pd
import numpy as np
from scipy import stats


# ── KPI Calculations ───────────────────────────────────────────────────────────

def compute_kpis(df: pd.DataFrame) -> dict:
    """Return a flat dict of top-level KPIs."""
    total_revenue  = df["Sales_Amount"].sum()
    total_orders   = len(df)
    total_units    = df["Quantity_Sold"].sum()
    avg_order_val  = df["Sales_Amount"].mean()
    avg_discount   = df["Discount"].mean() * 100  # as %
    total_profit   = df["Profit"].sum() if "Profit" in df.columns else np.nan
    avg_margin     = df["Profit_Margin"].mean() * 100 if "Profit_Margin" in df.columns else np.nan

    # Month-over-month growth (last two complete months)
    mom_growth = np.nan
    if "Month" in df.columns:
        monthly = df.groupby("Month")["Sales_Amount"].sum().sort_index()
        if len(monthly) >= 2:
            prev, curr = monthly.iloc[-2], monthly.iloc[-1]
            mom_growth = ((curr - prev) / prev) * 100 if prev != 0 else np.nan

    return {
        "Total Revenue":       round(total_revenue, 2),
        "Total Orders":        total_orders,
        "Total Units Sold":    int(total_units),
        "Avg Order Value":     round(avg_order_val, 2),
        "Avg Discount (%)":    round(avg_discount, 2),
        "Total Profit":        round(total_profit, 2) if not np.isnan(total_profit) else "N/A",
        "Avg Profit Margin (%)": round(avg_margin, 2) if not np.isnan(avg_margin) else "N/A",
        "MoM Revenue Growth (%)": round(mom_growth, 2) if not np.isnan(mom_growth) else "N/A",
    }


# ── Grouping & Aggregation ─────────────────────────────────────────────────────

def _std_agg(group_col: str, df: pd.DataFrame) -> pd.DataFrame:
    """Standard aggregation for a single grouping column."""
    return (
        df.groupby(group_col)
        .agg(
            Total_Revenue=("Sales_Amount", "sum"),
            Total_Orders=("Sales_Amount", "count"),
            Avg_Order_Value=("Sales_Amount", "mean"),
            Total_Units=("Quantity_Sold", "sum"),
            Avg_Discount=("Discount", "mean"),
        )
        .round(2)
        .reset_index()
        .sort_values("Total_Revenue", ascending=False)
    )


def by_region(df: pd.DataFrame) -> pd.DataFrame:
    return _std_agg("Region", df)

def by_category(df: pd.DataFrame) -> pd.DataFrame:
    return _std_agg("Product_Category", df)

def by_sales_rep(df: pd.DataFrame) -> pd.DataFrame:
    return _std_agg("Sales_Rep", df)

def by_channel(df: pd.DataFrame) -> pd.DataFrame:
    return _std_agg("Sales_Channel", df)

def by_payment(df: pd.DataFrame) -> pd.DataFrame:
    return _std_agg("Payment_Method", df)

def by_customer_type(df: pd.DataFrame) -> pd.DataFrame:
    return _std_agg("Customer_Type", df)


def monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly revenue trend sorted chronologically."""
    trend = (
        df.groupby("Month")
        .agg(
            Total_Revenue=("Sales_Amount", "sum"),
            Orders=("Sales_Amount", "count"),
            Avg_Order_Value=("Sales_Amount", "mean"),
        )
        .round(2)
        .reset_index()
        .sort_values("Month")
    )
    return trend


def quarterly_trend(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("Quarter")
        .agg(
            Total_Revenue=("Sales_Amount", "sum"),
            Orders=("Sales_Amount", "count"),
        )
        .round(2)
        .reset_index()
        .sort_values("Quarter")
    )


def category_by_region(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot: rows = Region, columns = Product_Category, values = Total Revenue."""
    pivot = df.pivot_table(
        values="Sales_Amount",
        index="Region",
        columns="Product_Category",
        aggfunc="sum",
        fill_value=0,
    ).round(2)
    return pivot.reset_index()


def top_products(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    return (
        df.groupby("Product_ID")
        .agg(
            Total_Revenue=("Sales_Amount", "sum"),
            Total_Orders=("Sales_Amount", "count"),
            Total_Units=("Quantity_Sold", "sum"),
        )
        .round(2)
        .reset_index()
        .sort_values("Total_Revenue", ascending=False)
        .head(n)
    )


# ── Correlation & Relationships ────────────────────────────────────────────────

def correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Pearson correlation for key numeric columns."""
    cols = ["Sales_Amount", "Quantity_Sold", "Unit_Cost", "Unit_Price", "Discount"]
    cols = [c for c in cols if c in df.columns]
    return df[cols].corr(method="pearson").round(3)


def discount_vs_revenue(df: pd.DataFrame) -> tuple[float, float, float]:
    """Pearson r, p-value, and slope of Discount → Sales_Amount."""
    x = df["Discount"].dropna()
    y = df.loc[x.index, "Sales_Amount"]
    r, p = stats.pearsonr(x, y)
    slope, intercept, *_ = stats.linregress(x, y)
    return round(r, 4), round(p, 6), round(slope, 4)


def quantity_vs_revenue(df: pd.DataFrame) -> tuple[float, float, float]:
    """Pearson r, p-value, and slope of Quantity_Sold → Sales_Amount."""
    x = df["Quantity_Sold"].dropna()
    y = df.loc[x.index, "Sales_Amount"]
    r, p = stats.pearsonr(x, y)
    slope, intercept, *_ = stats.linregress(x, y)
    return round(r, 4), round(p, 6), round(slope, 4)


# ── Business Insights ─────────────────────────────────────────────────────────

def generate_insights(df: pd.DataFrame, kpis: dict) -> list[dict]:
    """
    Return a list of insight dicts:
      { "title": str, "detail": str, "type": "positive" | "negative" | "neutral" }
    """
    insights = []

    # Best region
    reg = by_region(df)
    best_reg = reg.iloc[0]
    insights.append({
        "title": f"🏆 Top Region: {best_reg['Region']}",
        "detail": f"Generated ${best_reg['Total_Revenue']:,.2f} in revenue across "
                  f"{int(best_reg['Total_Orders'])} orders.",
        "type": "positive",
    })

    # Best category
    cat = by_category(df)
    best_cat = cat.iloc[0]
    insights.append({
        "title": f"📦 Top Category: {best_cat['Product_Category']}",
        "detail": f"Contributed ${best_cat['Total_Revenue']:,.2f} in total revenue.",
        "type": "positive",
    })

    # Best sales rep
    rep = by_sales_rep(df)
    best_rep = rep.iloc[0]
    insights.append({
        "title": f"🥇 Top Sales Rep: {best_rep['Sales_Rep']}",
        "detail": f"Closed {int(best_rep['Total_Orders'])} deals worth "
                  f"${best_rep['Total_Revenue']:,.2f}.",
        "type": "positive",
    })

    # Discount impact
    r, p, slope = discount_vs_revenue(df)
    disc_str = "positively" if r > 0 else "negatively"
    insights.append({
        "title": f"💸 Discount Impact: r = {r}",
        "detail": f"Discount is {disc_str} correlated with revenue (r={r}, p={p:.4f}). "
                  f"A 1-point increase in discount {'raises' if slope > 0 else 'lowers'} "
                  f"revenue by ${abs(slope):,.2f} on average.",
        "type": "neutral" if abs(r) < 0.3 else ("positive" if r > 0 else "negative"),
    })

    # Channel performance
    ch = by_channel(df)
    best_ch = ch.iloc[0]
    insights.append({
        "title": f"🛒 Best Channel: {best_ch['Sales_Channel']}",
        "detail": f"Accounts for ${best_ch['Total_Revenue']:,.2f} in revenue with an "
                  f"average order value of ${best_ch['Avg_Order_Value']:,.2f}.",
        "type": "positive",
    })

    # MoM growth
    mom = kpis.get("MoM Revenue Growth (%)", "N/A")
    if mom != "N/A":
        direction = "▲" if mom >= 0 else "▼"
        insights.append({
            "title": f"{direction} Month-over-Month Growth: {mom:+.2f}%",
            "detail": "Comparing the last two months of available data.",
            "type": "positive" if mom >= 0 else "negative",
        })

    # Customer type
    ct = by_customer_type(df)
    best_ct = ct.iloc[0]
    insights.append({
        "title": f"👤 Dominant Customer Type: {best_ct['Customer_Type']}",
        "detail": f"Accounts for {int(best_ct['Total_Orders'])} orders "
                  f"(${best_ct['Total_Revenue']:,.2f}).",
        "type": "neutral",
    })

    return insights
