# IBM_BOB_SALE_Data this project is about analyzing dataset of sales 
# 📊 Sales Analysis Dashboard

An end-to-end **Python data analytics project** that loads, cleans, analyses and visualises a sales dataset through an interactive **Streamlit** dashboard.

---

## 📁 Project Structure

```
ibm/
├── sales_data.csv                  ← Source dataset (1,000 transactions)
└── sales_analysis/
    ├── app.py                      ← Streamlit dashboard (6 tabs)
    ├── requirements.txt            ← Python dependencies
    ├── Sales_Analysis_Report.pptx  ← Presentation report
    └── modules/
        ├── __init__.py
        ├── data_loader.py          ← Load · Audit · Clean · Derive
        └── analysis.py             ← KPIs · Groups · Correlation · Insights
```

---

## 🗂️ Dataset

**File:** `sales_data.csv`  
**Rows:** 1,002 (1,000 clean after validation)  
**Columns:** 14

| Column | Description |
|--------|-------------|
| `Product_ID` | Unique product identifier |
| `Sale_Date` | Transaction date (2023) |
| `Sales_Rep` | Name of the sales representative |
| `Region` | North / South / East / West |
| `Sales_Amount` | Revenue per transaction ($) |
| `Quantity_Sold` | Units sold per transaction |
| `Product_Category` | Furniture / Electronics / Food / Clothing |
| `Unit_Cost` | Cost price per unit ($) |
| `Unit_Price` | Selling price per unit ($) |
| `Customer_Type` | New / Returning |
| `Discount` | Applied discount rate (0 – 1) |
| `Payment_Method` | Cash / Credit Card / Bank Transfer |
| `Sales_Channel` | Online / Retail |
| `Region_and_Sales_Rep` | Combined lookup key |

---

## ⚙️ Installation

### 1. Clone / navigate to the project folder

```bash
cd path/to/ibm
```

### 2. Install dependencies

```bash
pip install -r sales_analysis/requirements.txt
```

### 3. Run the dashboard

```bash
python -m streamlit run sales_analysis/app.py
```

> **Note:** Use `python -m streamlit` instead of `streamlit` directly to avoid Windows Application Control policy blocks on the `streamlit.exe` binary.

The app opens automatically at **http://localhost:8501**

---

## 📦 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `streamlit` | 1.35+ | Web dashboard framework |
| `pandas` | 2.2+ | Data loading, cleaning, aggregation |
| `numpy` | 1.26+ | Numeric computation |
| `scipy` | 1.13+ | Pearson correlation & linear regression |
| `plotly` | 5.22+ | Interactive charts |
| `statsmodels` | 0.15+ | OLS trendlines (used by Plotly) |
| `matplotlib` | 3.9+ | Supporting visualisation |
| `seaborn` | 0.13+ | Supporting visualisation |

---

## 🔄 Data Pipeline

```
sales_data.csv
      │
      ▼
 1. Load CSV          pandas.read_csv()
      │
      ▼
 2. Audit Quality     null counts · duplicates · bad dates
                      negative values · out-of-range discounts
      │
      ▼
 3. Clean Data        strip whitespace · parse dates · coerce types
                      drop duplicates · filter bad rows · clip discount
      │
      ▼
 4. Derive Columns    Profit · Profit_Margin · Month · Quarter
      │
      ▼
 5. Analyse           KPIs · groupings · correlations · insights
      │
      ▼
 6. Visualise         Streamlit dashboard (6 interactive tabs)
```

---

## 🖥️ Dashboard Tabs

### 📋 Overview
- 8 KPI metric cards (Total Revenue, Orders, Units, Avg Order Value, Profit, Margin, Discount, MoM Growth)
- Revenue by Region (bar chart)
- Revenue share by Category (donut pie)
- Monthly Revenue trend (area chart)
- Cleaned dataset preview (expandable table)

### 🔍 Data Quality
- Audit summary: null counts, duplicates, bad dates, negative values
- Bar charts for issue types
- Cleaning steps applied (table)
- Data types after cleaning
- Full descriptive statistics table

### 📈 Sales Trends
- Monthly Revenue & Order Volume (dual-axis bar + line)
- Quarterly Revenue (bar)
- Average Order Value per Month (line)
- Monthly Revenue by Product Category (stacked area)
- Monthly Revenue by Region (multi-line)

### 🗂️ Segment Analysis
- Sales Rep performance leaderboard (bar + detail table)
- Revenue by Payment Method (pie)
- Revenue by Customer Type (pie)
- Sales Channel comparison (grouped bar)
- Revenue heatmap: Region × Category
- Top 10 Products by Revenue (bar)
- Discount distribution by Category (box plot)

### 🔗 Relationships
- Pearson Correlation Matrix (heatmap)
- Discount vs Revenue (scatter + OLS trendline)
- Quantity Sold vs Revenue (scatter + OLS trendline)
- Unit Price vs Revenue by Category (bubble scatter)
- Profit Margin distribution by Category (violin)
- Avg Discount vs Avg Order Value by Sales Rep (bubble)

### 💡 Business Insights
- Auto-generated colour-coded insight cards (positive / negative / neutral)
- 7 actionable business recommendations (expandable)
- Segment performance summary table

---

## 🔽 Sidebar Filters

All charts and KPIs respond live to the following filters:

| Filter | Type |
|--------|------|
| Region | Multi-select |
| Product Category | Multi-select |
| Sales Rep | Multi-select |
| Sales Channel | Multi-select |
| Month Range | Slider (Jan – Dec 2023) |

---

## 📐 Module Reference

### `modules/data_loader.py`

| Function | Description |
|----------|-------------|
| `load_raw(filepath)` | Reads the CSV and returns a raw DataFrame |
| `audit_quality(df)` | Runs 7 quality checks on the raw data before cleaning |
| `clean(df)` | Applies 8 cleaning steps and adds 5 derived columns |
| `load_and_clean(filepath)` | Convenience wrapper — returns `(raw_df, clean_df, quality_report)` |

**Derived columns added by `clean()`:**

| Column | Formula |
|--------|---------|
| `Profit` | `(Unit_Price − Unit_Cost) × Quantity_Sold` |
| `Profit_Margin` | `(Unit_Price − Unit_Cost) / Unit_Price` |
| `Revenue` | Alias for `Sales_Amount` |
| `Month` | Period string e.g. `"2023-01"` |
| `Quarter` | Period string e.g. `"2023Q1"` |

---

### `modules/analysis.py`

| Function | Returns |
|----------|---------|
| `compute_kpis(df)` | Dict of 8 top-level KPI values |
| `by_region(df)` | Aggregated revenue table grouped by Region |
| `by_category(df)` | Aggregated revenue table grouped by Product Category |
| `by_sales_rep(df)` | Aggregated revenue table grouped by Sales Rep |
| `by_channel(df)` | Aggregated revenue table grouped by Sales Channel |
| `by_payment(df)` | Aggregated revenue table grouped by Payment Method |
| `by_customer_type(df)` | Aggregated revenue table grouped by Customer Type |
| `monthly_trend(df)` | Monthly revenue, order count and avg order value |
| `quarterly_trend(df)` | Quarterly revenue and order count |
| `category_by_region(df)` | Pivot table: Region × Category → Revenue |
| `top_products(df, n)` | Top N products by total revenue |
| `correlation_matrix(df)` | Pearson correlation matrix for 5 numeric features |
| `discount_vs_revenue(df)` | `(r, p_value, slope)` for Discount → Sales_Amount |
| `quantity_vs_revenue(df)` | `(r, p_value, slope)` for Quantity_Sold → Sales_Amount |
| `generate_insights(df, kpis)` | List of auto-generated insight dicts with type tags |

---

## 📊 Key Findings

| KPI | Value |
|-----|-------|
| Total Revenue | $5,019,265 |
| Total Orders | 1,000 |
| Total Units Sold | 25,355 |
| Avg Order Value | $5,019 |
| Total Profit | $6,487,847 |
| Avg Profit Margin | 14.28% |
| Avg Discount Rate | 15.24% |
| Top Region | West |
| Top Category | Furniture |
| Top Sales Rep | Eve |
| Best Channel | Online |

---

## 📁 Presentation

A full project presentation is included:

```
sales_analysis/Sales_Analysis_Report.pptx
```

**13 slides covering:**
1. Title
2. Project Objectives
3. Dataset Overview
4. Data Cleaning & Quality Audit
5. Key Performance Indicators
6. Sales Trends Over Time
7. Segment Analysis
8. Feature Relationships & Correlations
9. Visualisations Used
10. Auto-Generated Insights
11. Business Recommendations
12. Project Architecture & Tech Stack
13. Conclusion

---

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r sales_analysis/requirements.txt

# Launch the dashboard
python -m streamlit run sales_analysis/app.py
```

Then open  in your browser.

