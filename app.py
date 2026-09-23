"""
app.py  —  Sales Analytics Dashboard
======================================
Run with:  streamlit run sales_analysis/app.py
"""

import sys
from pathlib import Path

# Allow sibling imports when running directly
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from modules.data_loader import load_and_clean
from modules.analysis import (
    compute_kpis,
    by_region, by_category, by_sales_rep,
    by_channel, by_payment, by_customer_type,
    monthly_trend, quarterly_trend,
    category_by_region, top_products,
    correlation_matrix, discount_vs_revenue, quantity_vs_revenue,
    generate_insights,
)

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Colour Palette ─────────────────────────────────────────────────────────────
PALETTE   = px.colors.qualitative.Plotly
BLUE      = "#1f77b4"
GREEN     = "#2ca02c"
RED       = "#d62728"
ORANGE    = "#ff7f0e"

# ── Helpers ────────────────────────────────────────────────────────────────────
def fmt_currency(val) -> str:
    if isinstance(val, (int, float)):
        return f"${val:,.2f}"
    return str(val)

def fmt_pct(val) -> str:
    if isinstance(val, (int, float)):
        return f"{val:,.2f}%"
    return str(val)

def metric_delta(val, positive_is_good: bool = True):
    """Return (value_str, delta_str, delta_color) for st.metric."""
    if val == "N/A" or (isinstance(val, float) and np.isnan(val)):
        return str(val), None, None
    if isinstance(val, float):
        color = "normal" if (val >= 0) == positive_is_good else "inverse"
        return fmt_pct(val), f"{val:+.2f}%", color
    return str(val), None, None


# ── Load Data ──────────────────────────────────────────────────────────────────
DATA_PATH = Path(__file__).parent.parent / "sales_data.csv"

@st.cache_data(show_spinner="Loading and cleaning data…")
def get_data(path: Path):
    return load_and_clean(path)

try:
    raw_df, df, quality_report = get_data(DATA_PATH)
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/ios/100/4A90D9/combo-chart.png", width=60)
    st.title("Sales Analytics")
    st.markdown("---")

    # Filters
    st.subheader("🔽 Filters")

    all_regions    = sorted(df["Region"].unique())
    all_categories = sorted(df["Product_Category"].unique())
    all_reps       = sorted(df["Sales_Rep"].unique())
    all_channels   = sorted(df["Sales_Channel"].unique())
    all_months     = sorted(df["Month"].unique())

    sel_regions    = st.multiselect("Region",           all_regions,    default=all_regions)
    sel_categories = st.multiselect("Product Category", all_categories, default=all_categories)
    sel_reps       = st.multiselect("Sales Rep",        all_reps,       default=all_reps)
    sel_channels   = st.multiselect("Sales Channel",    all_channels,   default=all_channels)
    sel_months     = st.select_slider(
        "Month Range",
        options=all_months,
        value=(all_months[0], all_months[-1]),
    )

    st.markdown("---")
    st.caption("Data: sales_data.csv · 1 000+ rows")

# Apply sidebar filters
month_range = all_months[all_months.index(sel_months[0]) : all_months.index(sel_months[1]) + 1]

fdf = df[
    df["Region"].isin(sel_regions) &
    df["Product_Category"].isin(sel_categories) &
    df["Sales_Rep"].isin(sel_reps) &
    df["Sales_Channel"].isin(sel_channels) &
    df["Month"].isin(month_range)
].copy()

if fdf.empty:
    st.warning("No data matches the current filters. Please adjust your selections.")
    st.stop()

kpis = compute_kpis(fdf)

# ── Navigation Tabs ────────────────────────────────────────────────────────────
tabs = st.tabs([
    "📋 Overview",
    "🔍 Data Quality",
    "📈 Sales Trends",
    "🗂️ Segment Analysis",
    "🔗 Relationships",
    "💡 Business Insights",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.header("Executive Overview")
    st.markdown(
        f"Showing **{len(fdf):,}** transactions across "
        f"**{fdf['Region'].nunique()}** regions, "
        f"**{fdf['Product_Category'].nunique()}** categories, and "
        f"**{fdf['Sales_Rep'].nunique()}** sales reps."
    )

    # KPI Cards — row 1
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Total Revenue",    fmt_currency(kpis["Total Revenue"]))
    c2.metric("🧾 Total Orders",     f"{kpis['Total Orders']:,}")
    c3.metric("📦 Units Sold",       f"{kpis['Total Units Sold']:,}")
    c4.metric("🛒 Avg Order Value",  fmt_currency(kpis["Avg Order Value"]))

    # KPI Cards — row 2
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("💵 Total Profit",       fmt_currency(kpis["Total Profit"]))
    c6.metric("📉 Avg Profit Margin",  fmt_pct(kpis["Avg Profit Margin (%)"]))
    c7.metric("🏷️ Avg Discount",       fmt_pct(kpis["Avg Discount (%)"]))

    mom = kpis["MoM Revenue Growth (%)"]
    if mom != "N/A":
        c8.metric("📊 MoM Growth", fmt_pct(mom), delta=f"{mom:+.2f}%",
                  delta_color="normal" if mom >= 0 else "inverse")
    else:
        c8.metric("📊 MoM Growth", "N/A")

    st.markdown("---")

    # Revenue by Region (bar) + Revenue by Category (pie) side-by-side
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Revenue by Region")
        reg_df = by_region(fdf)
        fig = px.bar(
            reg_df, x="Region", y="Total_Revenue",
            color="Region", color_discrete_sequence=PALETTE,
            text_auto=".2s",
            labels={"Total_Revenue": "Revenue ($)", "Region": ""},
        )
        fig.update_layout(showlegend=False, margin=dict(t=20, b=20))
        st.plotly_chart(fig, width="stretch")

    with col_right:
        st.subheader("Revenue Share by Category")
        cat_df = by_category(fdf)
        fig = px.pie(
            cat_df, names="Product_Category", values="Total_Revenue",
            color_discrete_sequence=PALETTE,
            hole=0.4,
        )
        fig.update_traces(textinfo="percent+label")
        fig.update_layout(margin=dict(t=20, b=20))
        st.plotly_chart(fig, width="stretch")

    # Monthly revenue overview
    st.subheader("Monthly Revenue Overview")
    mt = monthly_trend(fdf)
    fig = px.area(
        mt, x="Month", y="Total_Revenue",
        labels={"Total_Revenue": "Revenue ($)", "Month": ""},
        color_discrete_sequence=[BLUE],
    )
    fig.update_layout(margin=dict(t=20, b=30))
    st.plotly_chart(fig, width="stretch")

    # Raw data preview
    with st.expander("📄 Preview Cleaned Dataset"):
        st.dataframe(
            fdf.drop(columns=["Month_Num"], errors="ignore").head(100),
            width="stretch",
            height=320,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — DATA QUALITY
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.header("Data Quality Report")
    st.markdown(
        "This tab shows the quality checks performed on the **raw** dataset "
        "before any cleaning was applied."
    )

    # Summary metrics
    q1, q2, q3, q4, q5 = st.columns(5)
    q1.metric("Raw Rows",        f"{len(raw_df):,}")
    q2.metric("Clean Rows",      f"{len(df):,}")
    q3.metric("Total Nulls",     quality_report["total_nulls"])
    q4.metric("Duplicate Rows",  quality_report["duplicate_rows"])
    q5.metric("Bad Dates",       quality_report["bad_dates"])

    st.markdown("---")

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Null Values per Column")
        null_data = quality_report["null_counts"]
        if null_data:
            null_df = pd.DataFrame(
                list(null_data.items()), columns=["Column", "Null Count"]
            ).sort_values("Null Count", ascending=False)
            fig = px.bar(
                null_df, x="Column", y="Null Count",
                color="Null Count", color_continuous_scale="Reds",
                text_auto=True,
            )
            fig.update_layout(showlegend=False, margin=dict(t=20, b=40))
            st.plotly_chart(fig, width="stretch")
        else:
            st.success("✅ No null values detected in the raw dataset.")

    with col_b:
        st.subheader("Data Issues Summary")
        issues = {
            "Duplicate Rows":       quality_report["duplicate_rows"],
            "Negative Sales":       quality_report["negative_sales"],
            "Negative Quantity":    quality_report["negative_quantity"],
            "Bad Discount Values":  quality_report["bad_discount"],
            "Unparseable Dates":    quality_report["bad_dates"],
        }
        issue_df = pd.DataFrame(
            list(issues.items()), columns=["Issue Type", "Count"]
        )
        fig = px.bar(
            issue_df, x="Issue Type", y="Count",
            color="Count", color_continuous_scale="Oranges",
            text_auto=True,
        )
        fig.update_layout(showlegend=False, margin=dict(t=20, b=80))
        st.plotly_chart(fig, width="stretch")

    st.subheader("Cleaning Steps Applied")
    steps = [
        ("Strip whitespace",        "Removed leading/trailing spaces from all text columns."),
        ("Parse Sale_Date",         "Converted Sale_Date to datetime; invalid dates dropped."),
        ("Coerce numeric columns",  "Forced Sales_Amount, Quantity_Sold, Unit_Cost, Unit_Price, Discount to float."),
        ("Drop duplicates",         f"{quality_report['duplicate_rows']} duplicate row(s) removed."),
        ("Filter invalid rows",     "Dropped rows with null or non-positive Sales_Amount / Quantity_Sold."),
        ("Clip Discount",           "Clipped Discount values to [0.0, 1.0]."),
        ("Fill categorical nulls",  "Replaced NaN in categorical columns with 'Unknown'."),
        ("Derived columns added",   "Profit, Profit_Margin, Revenue, Month, Quarter computed."),
    ]
    step_df = pd.DataFrame(steps, columns=["Step", "Description"])
    step_df.index += 1
    st.table(step_df)

    st.subheader("Data Types After Cleaning")
    dtypes_df = pd.DataFrame(
        {"Column": df.dtypes.index, "Data Type": df.dtypes.astype(str).values}
    )
    st.dataframe(dtypes_df, width="stretch", hide_index=True)

    st.subheader("Descriptive Statistics")
    # Convert to all-string to avoid Arrow serialisation issues with mixed types
    desc = fdf.describe(include="all").T.round(3).astype(str).replace("nan", "—")
    st.dataframe(desc, width="stretch", height=380)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — SALES TRENDS
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.header("Sales Trends Over Time")

    # Monthly Revenue + Orders dual axis
    st.subheader("Monthly Revenue & Order Volume")
    mt = monthly_trend(fdf)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(x=mt["Month"], y=mt["Total_Revenue"], name="Revenue ($)",
               marker_color=BLUE, opacity=0.75),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=mt["Month"], y=mt["Orders"], name="Orders",
                   mode="lines+markers", line=dict(color=ORANGE, width=2)),
        secondary_y=True,
    )
    fig.update_xaxes(title_text="Month")
    fig.update_yaxes(title_text="Revenue ($)",   secondary_y=False)
    fig.update_yaxes(title_text="Order Count",   secondary_y=True)
    fig.update_layout(legend=dict(orientation="h", y=1.1), margin=dict(t=40, b=40))
    st.plotly_chart(fig, width="stretch")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Quarterly Revenue")
        qt = quarterly_trend(fdf)
        fig = px.bar(
            qt, x="Quarter", y="Total_Revenue",
            color="Total_Revenue", color_continuous_scale="Blues",
            text_auto=".2s",
            labels={"Total_Revenue": "Revenue ($)"},
        )
        fig.update_layout(showlegend=False, margin=dict(t=20, b=30))
        st.plotly_chart(fig, width="stretch")

    with col2:
        st.subheader("Avg Order Value per Month")
        fig = px.line(
            mt, x="Month", y="Avg_Order_Value",
            markers=True,
            labels={"Avg_Order_Value": "Avg Order Value ($)"},
            color_discrete_sequence=[GREEN],
        )
        fig.update_layout(margin=dict(t=20, b=30))
        st.plotly_chart(fig, width="stretch")

    # Monthly Revenue by Category (stacked area)
    st.subheader("Monthly Revenue by Product Category")
    cat_month = (
        fdf.groupby(["Month", "Product_Category"])["Sales_Amount"]
        .sum()
        .reset_index()
        .sort_values("Month")
    )
    fig = px.area(
        cat_month, x="Month", y="Sales_Amount",
        color="Product_Category",
        color_discrete_sequence=PALETTE,
        labels={"Sales_Amount": "Revenue ($)"},
    )
    fig.update_layout(margin=dict(t=20, b=30))
    st.plotly_chart(fig, width="stretch")

    # Monthly Revenue by Region (line)
    st.subheader("Monthly Revenue by Region")
    reg_month = (
        fdf.groupby(["Month", "Region"])["Sales_Amount"]
        .sum()
        .reset_index()
        .sort_values("Month")
    )
    fig = px.line(
        reg_month, x="Month", y="Sales_Amount",
        color="Region",
        markers=True,
        color_discrete_sequence=PALETTE,
        labels={"Sales_Amount": "Revenue ($)"},
    )
    fig.update_layout(margin=dict(t=20, b=30))
    st.plotly_chart(fig, width="stretch")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — SEGMENT ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.header("Segment Analysis")

    # ─ Sales Rep Leaderboard ──────────────────────────────────────────────────
    st.subheader("Sales Rep Performance Leaderboard")
    rep_df = by_sales_rep(fdf)
    rep_df["Avg_Discount_Pct"] = (rep_df["Avg_Discount"] * 100).round(2)

    fig = px.bar(
        rep_df, x="Sales_Rep", y="Total_Revenue",
        color="Total_Revenue", color_continuous_scale="Viridis",
        text_auto=".2s",
        labels={"Total_Revenue": "Revenue ($)", "Sales_Rep": ""},
    )
    fig.update_layout(showlegend=False, margin=dict(t=20, b=30))
    st.plotly_chart(fig, width="stretch")

    with st.expander("Sales Rep Detail Table"):
        display_rep = rep_df.copy()
        display_rep["Total_Revenue"]    = display_rep["Total_Revenue"].map("${:,.2f}".format)
        display_rep["Avg_Order_Value"]  = display_rep["Avg_Order_Value"].map("${:,.2f}".format)
        display_rep["Avg_Discount_Pct"] = display_rep["Avg_Discount_Pct"].map("{:.2f}%".format)
        st.dataframe(display_rep.drop(columns=["Avg_Discount"]), width="stretch", hide_index=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        # Payment Method
        st.subheader("Revenue by Payment Method")
        pay_df = by_payment(fdf)
        fig = px.pie(
            pay_df, names="Payment_Method", values="Total_Revenue",
            color_discrete_sequence=PALETTE, hole=0.35,
        )
        fig.update_traces(textinfo="percent+label")
        fig.update_layout(margin=dict(t=20, b=20))
        st.plotly_chart(fig, width="stretch")

    with col2:
        # Customer Type
        st.subheader("Revenue by Customer Type")
        ct_df = by_customer_type(fdf)
        fig = px.pie(
            ct_df, names="Customer_Type", values="Total_Revenue",
            color_discrete_sequence=[BLUE, ORANGE], hole=0.35,
        )
        fig.update_traces(textinfo="percent+label")
        fig.update_layout(margin=dict(t=20, b=20))
        st.plotly_chart(fig, width="stretch")

    st.markdown("---")

    # Sales Channel comparison
    st.subheader("Sales Channel Comparison")
    ch_df = by_channel(fdf)
    fig = px.bar(
        ch_df, x="Sales_Channel", y=["Total_Revenue", "Total_Orders"],
        barmode="group",
        color_discrete_sequence=[BLUE, ORANGE],
        labels={"value": "Count / Revenue ($)", "Sales_Channel": ""},
    )
    fig.update_layout(margin=dict(t=20, b=30))
    st.plotly_chart(fig, width="stretch")

    st.markdown("---")

    # Category × Region heatmap
    st.subheader("Revenue Heatmap: Region × Product Category")
    pivot = category_by_region(fdf)
    pivot_melted = pivot.melt(id_vars="Region", var_name="Category", value_name="Revenue")
    fig = px.density_heatmap(
        pivot_melted, x="Category", y="Region", z="Revenue",
        color_continuous_scale="YlOrRd",
        text_auto=".2s",
    )
    fig.update_layout(margin=dict(t=20, b=40))
    st.plotly_chart(fig, width="stretch")

    st.markdown("---")

    # Top 10 Products
    st.subheader("Top 10 Products by Revenue")
    tp = top_products(fdf, 10)
    fig = px.bar(
        tp, x="Product_ID", y="Total_Revenue",
        color="Total_Revenue", color_continuous_scale="Teal",
        text_auto=".2s",
        labels={"Total_Revenue": "Revenue ($)", "Product_ID": "Product ID"},
    )
    fig.update_layout(showlegend=False, margin=dict(t=20, b=30))
    st.plotly_chart(fig, width="stretch")

    # Discount distribution by category
    st.subheader("Discount Distribution by Product Category")
    fig = px.box(
        fdf, x="Product_Category", y="Discount",
        color="Product_Category",
        color_discrete_sequence=PALETTE,
        points="outliers",
        labels={"Discount": "Discount Rate", "Product_Category": ""},
    )
    fig.update_layout(showlegend=False, margin=dict(t=20, b=30))
    st.plotly_chart(fig, width="stretch")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — RELATIONSHIPS
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.header("Feature Relationships & Correlations")

    # Correlation Matrix
    st.subheader("Pearson Correlation Matrix")
    corr = correlation_matrix(fdf)
    fig = px.imshow(
        corr,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1,
        aspect="auto",
    )
    fig.update_layout(margin=dict(t=20, b=20))
    st.plotly_chart(fig, width="stretch")

    st.markdown(
        "_Values close to **+1** indicate strong positive correlation; "
        "close to **−1** strong negative correlation; "
        "near **0** means little linear relationship._"
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Discount vs Revenue")
        r, p, slope = discount_vs_revenue(fdf)
        fig = px.scatter(
            fdf, x="Discount", y="Sales_Amount",
            color="Product_Category",
            trendline="ols",
            opacity=0.6,
            color_discrete_sequence=PALETTE,
            labels={"Discount": "Discount Rate", "Sales_Amount": "Revenue ($)"},
        )
        fig.update_layout(margin=dict(t=20, b=30))
        st.plotly_chart(fig, width="stretch")
        st.caption(f"Pearson r = **{r}** | p-value = **{p}** | slope = **{slope:+,.2f}**")

    with col2:
        st.subheader("Quantity Sold vs Revenue")
        rq, pq, slopeq = quantity_vs_revenue(fdf)
        fig = px.scatter(
            fdf, x="Quantity_Sold", y="Sales_Amount",
            color="Region",
            trendline="ols",
            opacity=0.6,
            color_discrete_sequence=PALETTE,
            labels={"Quantity_Sold": "Quantity Sold", "Sales_Amount": "Revenue ($)"},
        )
        fig.update_layout(margin=dict(t=20, b=30))
        st.plotly_chart(fig, width="stretch")
        st.caption(f"Pearson r = **{rq}** | p-value = **{pq}** | slope = **{slopeq:+,.2f}**")

    st.markdown("---")

    # Unit Price vs Sales Amount
    st.subheader("Unit Price vs Sales Amount (by Category)")
    fig = px.scatter(
        fdf, x="Unit_Price", y="Sales_Amount",
        color="Product_Category",
        size="Quantity_Sold",
        hover_data=["Sales_Rep", "Region", "Sale_Date"],
        opacity=0.65,
        color_discrete_sequence=PALETTE,
        labels={"Unit_Price": "Unit Price ($)", "Sales_Amount": "Revenue ($)"},
    )
    fig.update_layout(margin=dict(t=20, b=30))
    st.plotly_chart(fig, width="stretch")

    st.markdown("---")

    # Profit Margin distribution
    if "Profit_Margin" in fdf.columns:
        st.subheader("Profit Margin Distribution by Category")
        fig = px.violin(
            fdf, x="Product_Category", y="Profit_Margin",
            color="Product_Category",
            box=True,
            points="outliers",
            color_discrete_sequence=PALETTE,
            labels={"Profit_Margin": "Profit Margin", "Product_Category": ""},
        )
        fig.update_yaxes(tickformat=".0%")
        fig.update_layout(showlegend=False, margin=dict(t=20, b=30))
        st.plotly_chart(fig, width="stretch")

    # Avg Discount vs Avg Order Value by Sales Rep
    st.subheader("Avg Discount vs Avg Order Value (Sales Reps)")
    rep_df2 = by_sales_rep(fdf)
    fig = px.scatter(
        rep_df2,
        x="Avg_Discount", y="Avg_Order_Value",
        text="Sales_Rep",
        size="Total_Orders",
        color="Total_Revenue",
        color_continuous_scale="Plasma",
        labels={
            "Avg_Discount": "Avg Discount Rate",
            "Avg_Order_Value": "Avg Order Value ($)",
        },
    )
    fig.update_traces(textposition="top center")
    fig.update_xaxes(tickformat=".0%")
    fig.update_layout(margin=dict(t=20, b=30))
    st.plotly_chart(fig, width="stretch")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 6 — BUSINESS INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[5]:
    st.header("Business Insights & Recommendations")
    st.markdown(
        "The following insights are derived from the filtered dataset "
        "and can guide strategic decision-making."
    )

    insights = generate_insights(fdf, kpis)

    TYPE_COLOR = {
        "positive": "#d4edda",
        "negative": "#f8d7da",
        "neutral":  "#d1ecf1",
    }
    TYPE_BORDER = {
        "positive": "#28a745",
        "negative": "#dc3545",
        "neutral":  "#17a2b8",
    }

    for insight in insights:
        bg     = TYPE_COLOR.get(insight["type"],  "#f7f8fa")
        border = TYPE_BORDER.get(insight["type"], "#6c757d")
        st.markdown(
            f"""
            <div style="
                background:{bg};
                border-left:5px solid {border};
                border-radius:6px;
                padding:14px 18px;
                margin-bottom:12px;
            ">
                <p style="margin:0;font-weight:700;font-size:1rem;">{insight['title']}</p>
                <p style="margin:4px 0 0;color:#333;font-size:0.93rem;">{insight['detail']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.subheader("📋 Actionable Recommendations")

    recommendations = [
        ("Invest in top-performing regions",
         "Double down on marketing and inventory in the highest-revenue regions to "
         "capitalise on proven demand."),
        ("Optimise discount strategy",
         "Analyse which discount tiers actually drive revenue uplift vs margin erosion. "
         "Consider capping discounts at the breakeven threshold."),
        ("Expand best-selling categories",
         "Prioritise stock and promotions for the top product category. "
         "Explore cross-sell opportunities into adjacent categories."),
        ("Support high-performing sales reps",
         "Identify the techniques used by the top sales rep and incorporate them into "
         "team training programs."),
        ("Leverage the dominant sales channel",
         "Increase spend and content in the highest-performing channel. "
         "A/B test new campaigns there before rolling out broadly."),
        ("Retain returning customers",
         "Returning customers signal loyalty — introduce a loyalty programme or "
         "personalised offers to increase repeat purchase frequency."),
        ("Seasonal inventory planning",
         "Use monthly trend data to forecast demand spikes and pre-position inventory, "
         "reducing both stockouts and overstock costs."),
    ]

    for i, (title, detail) in enumerate(recommendations, 1):
        with st.expander(f"{i}. {title}"):
            st.markdown(detail)

    st.markdown("---")

    # Summary table: all segments at a glance
    st.subheader("Segment Performance Summary")
    summary_data = {
        "Segment": ["Region", "Category", "Sales Rep", "Channel", "Customer Type", "Payment Method"],
        "Best Performer": [
            by_region(fdf).iloc[0]["Region"],
            by_category(fdf).iloc[0]["Product_Category"],
            by_sales_rep(fdf).iloc[0]["Sales_Rep"],
            by_channel(fdf).iloc[0]["Sales_Channel"],
            by_customer_type(fdf).iloc[0]["Customer_Type"],
            by_payment(fdf).iloc[0]["Payment_Method"],
        ],
        "Top Revenue ($)": [
            f"${by_region(fdf).iloc[0]['Total_Revenue']:,.2f}",
            f"${by_category(fdf).iloc[0]['Total_Revenue']:,.2f}",
            f"${by_sales_rep(fdf).iloc[0]['Total_Revenue']:,.2f}",
            f"${by_channel(fdf).iloc[0]['Total_Revenue']:,.2f}",
            f"${by_customer_type(fdf).iloc[0]['Total_Revenue']:,.2f}",
            f"${by_payment(fdf).iloc[0]['Total_Revenue']:,.2f}",
        ],
    }
    st.dataframe(
        pd.DataFrame(summary_data),
        width="stretch",
        hide_index=True,
    )
