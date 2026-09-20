"""
Task 28 - Customer Repeat Purchase Analysis
Dataset: UCI Online Retail II

Run:
    pip install -r requirements.txt
    python src/customer_repeat_purchase_analysis.py

Expected input:
    data/raw/online_retail_II.xlsx

The script:
1. Loads both UCI workbook sheets.
2. Cleans transaction data.
3. Creates invoice-level orders.
4. Builds customer-level repeat-purchase metrics.
5. Compares first-time vs repeat orders.
6. Builds a purchase-frequency table.
7. Builds an RFM-style segment table.
8. Exports CSVs and PNG charts.

The benchmark figures in the accompanying report are based on published analyses
of the same public UCI dataset; running this script recalculates everything locally.
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parents[1]
RAW = BASE / "data" / "raw" / "online_retail_II.xlsx"
OUT = BASE / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

if not RAW.exists():
    raise FileNotFoundError(
        f"Dataset not found: {RAW}\n"
        "Download Online Retail II from UCI and place online_retail_II.xlsx in data/raw/."
    )

# Load both sheets. UCI Online Retail II uses two annual sheets.
sheets = pd.read_excel(RAW, sheet_name=None)
frames = []
for sheet_name, df in sheets.items():
    df = df.copy()
    df["source_sheet"] = sheet_name
    frames.append(df)

df = pd.concat(frames, ignore_index=True)

# Standardise column names.
rename = {
    "Invoice": "InvoiceNo",
    "StockCode": "StockCode",
    "Description": "Description",
    "Quantity": "Quantity",
    "InvoiceDate": "InvoiceDate",
    "Price": "UnitPrice",
    "Customer ID": "CustomerID",
    "Country": "Country",
}
df = df.rename(columns=rename)

# Parse types.
df["InvoiceNo"] = df["InvoiceNo"].astype(str).str.strip()
df["CustomerID"] = pd.to_numeric(df["CustomerID"], errors="coerce")
df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")

# Remove exact duplicates across the combined workbook.
df = df.drop_duplicates()

# Customer-level repeat analysis should use identifiable, valid sales only.
df = df[df["CustomerID"].notna()].copy()
df = df[~df["InvoiceNo"].str.upper().str.startswith("C")].copy()
df = df[df["Quantity"] > 0].copy()
df = df[df["UnitPrice"] > 0].copy()
df = df[df["InvoiceDate"].notna()].copy()

df["Revenue"] = df["Quantity"] * df["UnitPrice"]
df["CustomerID"] = df["CustomerID"].astype(int)

# Invoice-level order table.
orders = (
    df.groupby(["CustomerID", "InvoiceNo"], as_index=False)
      .agg(
          OrderDate=("InvoiceDate", "min"),
          OrderRevenue=("Revenue", "sum"),
          Units=("Quantity", "sum"),
          LineItems=("StockCode", "count"),
      )
)
orders = orders.sort_values(["CustomerID", "OrderDate", "InvoiceNo"])
orders["OrderNumber"] = orders.groupby("CustomerID").cumcount() + 1
orders["CustomerType"] = np.where(orders["OrderNumber"] == 1, "First-Time Order", "Repeat Order")
orders.to_csv(OUT / "clean_orders.csv", index=False)

# Customer-level metrics.
customers = (
    orders.groupby("CustomerID", as_index=False)
    .agg(
        TotalOrders=("InvoiceNo", "nunique"),
        TotalRevenue=("OrderRevenue", "sum"),
        FirstPurchase=("OrderDate", "min"),
        LastPurchase=("OrderDate", "max"),
        ActiveMonths=("OrderDate", lambda s: s.dt.to_period("M").nunique()),
    )
)
customers["AOV"] = customers["TotalRevenue"] / customers["TotalOrders"]
customers["RepeatCustomer"] = customers["TotalOrders"] >= 2
customers["CustomerSegment"] = np.where(customers["RepeatCustomer"], "Repeat Buyer", "One-Time Buyer")
snapshot = orders["OrderDate"].max() + pd.Timedelta(days=1)
customers["RecencyDays"] = (snapshot - customers["LastPurchase"]).dt.days
customers.to_csv(OUT / "customer_repeat_metrics.csv", index=False)

# Repeat rate KPI.
total_customers = customers["CustomerID"].nunique()
repeat_customers = int(customers["RepeatCustomer"].sum())
one_time_customers = int(total_customers - repeat_customers)
repeat_rate = repeat_customers / total_customers * 100
one_time_share = one_time_customers / total_customers * 100

kpi = pd.DataFrame([
    ["Total identified customers", total_customers],
    ["Repeat customers", repeat_customers],
    ["One-time customers", one_time_customers],
    ["Repeat purchase rate (%)", round(repeat_rate, 2)],
    ["One-time buyer share (%)", round(one_time_share, 2)],
    ["Total orders", orders["InvoiceNo"].nunique()],
    ["Total revenue (GBP)", round(orders["OrderRevenue"].sum(), 2)],
])
kpi.columns = ["Metric", "Value"]
kpi.to_csv(OUT / "repeat_rate_calculated.csv", index=False)

# First-time vs repeat order comparison.
first_vs_repeat = (
    orders.groupby("CustomerType", as_index=False)
    .agg(
        Orders=("InvoiceNo", "nunique"),
        Customers=("CustomerID", "nunique"),
        Revenue=("OrderRevenue", "sum"),
        AOV=("OrderRevenue", "mean"),
    )
)
first_vs_repeat["RevenueSharePct"] = first_vs_repeat["Revenue"] / first_vs_repeat["Revenue"].sum() * 100
first_vs_repeat.to_csv(OUT / "first_time_vs_repeat_orders.csv", index=False)

# Purchase frequency buckets.
def bucket(n):
    if n == 1:
        return "1 order"
    if n <= 3:
        return "2-3 orders"
    if n <= 6:
        return "4-6 orders"
    if n <= 12:
        return "7-12 orders"
    return "13+ orders"

freq = (
    customers.assign(FrequencyBucket=customers["TotalOrders"].map(bucket))
    .groupby("FrequencyBucket", as_index=False)
    .agg(
        Customers=("CustomerID", "count"),
        Revenue=("TotalRevenue", "sum"),
        AvgOrders=("TotalOrders", "mean"),
        AvgAOV=("AOV", "mean"),
    )
)
freq["CustomerSharePct"] = freq["Customers"] / total_customers * 100
freq["RevenueSharePct"] = freq["Revenue"] / freq["Revenue"].sum() * 100
freq.to_csv(OUT / "purchase_frequency_segments.csv", index=False)

# Simple RFM quintile segmentation.
rfm = customers[["CustomerID", "RecencyDays", "TotalOrders", "TotalRevenue"]].copy()

def safe_qcut(series, ascending=True):
    # Rank first so duplicate values do not collapse bins.
    ranked = series.rank(method="first", ascending=ascending)
    return pd.qcut(ranked, 5, labels=[1,2,3,4,5]).astype(int)

# Recency: lower days = better => ascending=False before qcut labels 1..5.
rfm["R"] = safe_qcut(rfm["RecencyDays"], ascending=False)
rfm["F"] = safe_qcut(rfm["TotalOrders"], ascending=True)
rfm["M"] = safe_qcut(rfm["TotalRevenue"], ascending=True)

def segment(row):
    r, f = row["R"], row["F"]
    if r >= 5 and f >= 5:
        return "Champions"
    if r >= 4 and f >= 4:
        return "Loyal Customers"
    if r >= 4 and f <= 2:
        return "Potential Loyalist"
    if r == 3 and f >= 4:
        return "Need Attention"
    if r <= 2 and f >= 4:
        return "At Risk"
    if r <= 2 and f <= 2:
        return "Lost / Hibernating"
    return "Others"

rfm["Segment"] = rfm.apply(segment, axis=1)
rfm.to_csv(OUT / "rfm_customer_segments.csv", index=False)

rfm_summary = (
    rfm.merge(customers[["CustomerID", "TotalRevenue", "TotalOrders", "AOV", "RecencyDays"]], on="CustomerID")
    .groupby("Segment", as_index=False)
    .agg(
        Customers=("CustomerID", "count"),
        TotalRevenue=("TotalRevenue", "sum"),
        AvgRevenue=("TotalRevenue", "mean"),
        AvgOrders=("TotalOrders", "mean"),
        AvgAOV=("AOV", "mean"),
        AvgRecencyDays=("RecencyDays", "mean"),
    )
)
rfm_summary["CustomerSharePct"] = rfm_summary["Customers"] / total_customers * 100
rfm_summary["RevenueSharePct"] = rfm_summary["TotalRevenue"] / rfm_summary["TotalRevenue"].sum() * 100
rfm_summary = rfm_summary.sort_values("TotalRevenue", ascending=False)
rfm_summary.to_csv(OUT / "rfm_segment_summary.csv", index=False)

# Monthly repeat behavior.
orders["YearMonth"] = orders["OrderDate"].dt.to_period("M").astype(str)
monthly = (
    orders.groupby(["YearMonth", "CustomerType"], as_index=False)
    .agg(Orders=("InvoiceNo", "nunique"), Revenue=("OrderRevenue", "sum"))
)
monthly.to_csv(OUT / "monthly_first_vs_repeat.csv", index=False)

# Chart 1: customer split.
plt.figure(figsize=(7, 5))
plt.bar(["One-Time", "Repeat"], [one_time_customers, repeat_customers])
plt.title("Customer Repeat Purchase Split")
plt.ylabel("Customers")
plt.tight_layout()
plt.savefig(OUT / "repeat_customer_split.png", dpi=180)
plt.close()

# Chart 2: revenue split by first/repeat order.
plt.figure(figsize=(8, 5))
plot_df = first_vs_repeat.set_index("CustomerType")
plt.bar(plot_df.index, plot_df["Revenue"])
plt.title("Revenue: First-Time Orders vs Repeat Orders")
plt.ylabel("Revenue (GBP)")
plt.tight_layout()
plt.savefig(OUT / "first_time_vs_repeat_revenue.png", dpi=180)
plt.close()

# Chart 3: frequency distribution.
plt.figure(figsize=(8, 5))
freq_order = ["1 order", "2-3 orders", "4-6 orders", "7-12 orders", "13+ orders"]
freq_plot = freq.set_index("FrequencyBucket").reindex(freq_order).fillna(0)
plt.bar(freq_plot.index, freq_plot["Customers"])
plt.title("Customer Purchase Frequency")
plt.ylabel("Customers")
plt.xticks(rotation=20)
plt.tight_layout()
plt.savefig(OUT / "purchase_frequency.png", dpi=180)
plt.close()

print("Analysis complete.")
print(f"Customers: {total_customers:,}")
print(f"Repeat customers: {repeat_customers:,}")
print(f"Repeat purchase rate: {repeat_rate:.2f}%")
print(f"Orders: {orders['InvoiceNo'].nunique():,}")
print(f"Revenue: GBP {orders['OrderRevenue'].sum():,.2f}")
