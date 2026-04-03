import pandas as pd
import json
import re
from collections import Counter
from itertools import combinations

# ── Load data ───────────────────────────────────────────────────────────────
SORTED_FILE = "c:/Users/dheer/Downloads/Repo/tronxo/dashboard/1100 VIM Exceptions Data(DATA - 1100 Sorted) (1).csv"
INC_FILE    = "c:/Users/dheer/Downloads/Repo/tronxo/dashboard/1100 Data inc.csv"
OUT_DIR     = "c:/Users/dheer/Downloads/Repo/tronxo/dashboard/output"

def load(path):
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    # Deduplicate column names (Created at / Time Stamp appear twice)
    cols = list(df.columns)
    seen = {}
    new_cols = []
    for c in cols:
        if c in seen:
            seen[c] += 1
            new_cols.append(f"{c}_{seen[c]}")
        else:
            seen[c] = 0
            new_cols.append(c)
    df.columns = new_cols
    return df

sorted_raw = load(SORTED_FILE)
inc_raw    = load(INC_FILE)

print(f"Sorted raw rows: {len(sorted_raw)}")
print(f"Inc raw rows:    {len(inc_raw)}")
print("Columns:", list(sorted_raw.columns))

# ── Cleaning helpers ─────────────────────────────────────────────────────────
TRANSPORT_PREFIX = "52"
VALID_PO_TYPES   = ["NB", "ZCP"]

def clean(df, filter_po=True):
    df = df.copy()
    df["Supplier"] = df["Supplier"].astype(str).str.strip()
    # Remove transport vendors (supplier starts with "52")
    df = df[~df["Supplier"].str.startswith(TRANSPORT_PREFIX)]
    # Normalise PO Type
    df["PO Type"] = df["PO Type"].astype(str).str.strip().str.upper()
    if filter_po:
        df = df[df["PO Type"].isin(VALID_PO_TYPES)]
    # Normalise amounts
    def parse_amt(v):
        try:
            return float(str(v).replace(",","").replace('"',''))
        except:
            return None
    df["Amount"] = df["Gross Invoice Amount"].apply(parse_amt)
    # Parse dates
    for col in ["Created at", "Document Date"]:
        if col in df.columns:
            df[col+"_dt"] = pd.to_datetime(df[col], errors="coerce")
    return df

sorted_df = clean(sorted_raw)
inc_df    = clean(inc_raw, filter_po=False)  # keep all PO types for first-pass calc

# Posted only for most analyses
sorted_posted = sorted_df[sorted_df["Document Status"].astype(str).str.strip() == "15"]
inc_posted    = inc_df[inc_df["Document Status"].astype(str).str.strip() == "15"]

print(f"\nAfter cleaning (non-transport, NB/ZCP):")
print(f"  Sorted posted rows: {len(sorted_posted)}")
print(f"  Inc posted rows:    {len(inc_posted)}")

# ── 1. Exception Frequency ───────────────────────────────────────────────────
exc_freq = (
    sorted_posted
    .groupby(["Exception ID","Exception description"])
    .size()
    .reset_index(name="Count")
    .sort_values("Count", ascending=False)
)
exc_freq["Pct"] = (exc_freq["Count"] / exc_freq["Count"].sum() * 100).round(2)
exc_freq.to_csv(f"{OUT_DIR}/01_exception_frequency.csv", index=False)
print("\n--- Exception Frequency (top 15) ---")
print(exc_freq.head(15).to_string(index=False))

# ── 2. Top Problem Vendors ───────────────────────────────────────────────────
# invoices = unique Document Ids
vendor_inv = (
    sorted_posted
    .groupby(["Supplier","Name 1"])["Document Id"]
    .nunique()
    .reset_index(name="Unique_Invoices")
)
vendor_events = (
    sorted_posted
    .groupby(["Supplier","Name 1"])
    .size()
    .reset_index(name="Exception_Events")
)
vendor = vendor_inv.merge(vendor_events, on=["Supplier","Name 1"])
vendor["Avg_Exc_Per_Inv"] = (vendor["Exception_Events"] / vendor["Unique_Invoices"]).round(2)
vendor_top = vendor.sort_values("Exception_Events", ascending=False).head(50)
vendor_top.to_csv(f"{OUT_DIR}/02_top_vendors.csv", index=False)
print("\n--- Top 10 Vendors by Exception Events ---")
print(vendor_top.head(10)[["Name 1","Unique_Invoices","Exception_Events","Avg_Exc_Per_Inv"]].to_string(index=False))

# ── 3. Exception by Material Category ────────────────────────────────────────
cat_exc = (
    sorted_posted
    .groupby(["PO category decription","Exception ID","Exception description"])
    .size()
    .reset_index(name="Count")
    .sort_values(["PO category decription","Count"], ascending=[True,False])
)
cat_exc.to_csv(f"{OUT_DIR}/03_exception_by_category.csv", index=False)

cat_summary = (
    sorted_posted
    .groupby("PO category decription")
    .size()
    .reset_index(name="Exception_Events")
    .sort_values("Exception_Events", ascending=False)
)
print("\n--- Exception Events by Category ---")
print(cat_summary.to_string(index=False))

# ── 4. Ingestion method + First-pass rate ────────────────────────────────────
# For first-pass: use inc_posted (all exceptions incl 0,91, non-transport, any PO type)
# An invoice is "first-pass" if its only exceptions in sorted_posted are absent
# i.e. Document Id does NOT appear in sorted_posted at all

# All unique posted invoices in inc (non-transport) – filter to NB/ZCP for apples-to-apples
inc_posted_nb_zcp = inc_posted[inc_posted["PO Type"].isin(VALID_PO_TYPES)]

all_inv = inc_posted_nb_zcp.groupby(["Document Id","Channel ID","PO category decription"]).first().reset_index()[
    ["Document Id","Channel ID","PO category decription"]
]
exc_inv_ids = set(sorted_posted["Document Id"].unique())
all_inv["First_Pass"] = ~all_inv["Document Id"].isin(exc_inv_ids)

channel_fp = (
    all_inv.groupby("Channel ID")
    .agg(Total=("Document Id","count"), First_Pass_Count=("First_Pass","sum"))
    .reset_index()
)
channel_fp["First_Pass_Rate"] = (channel_fp["First_Pass_Count"]/channel_fp["Total"]*100).round(2)
channel_fp.to_csv(f"{OUT_DIR}/04_channel_firstpass.csv", index=False)
print("\n--- First-pass by Channel ---")
print(channel_fp.to_string(index=False))

channel_cat_fp = (
    all_inv.groupby(["Channel ID","PO category decription"])
    .agg(Total=("Document Id","count"), First_Pass_Count=("First_Pass","sum"))
    .reset_index()
)
channel_cat_fp["First_Pass_Rate"] = (channel_cat_fp["First_Pass_Count"]/channel_cat_fp["Total"]*100).round(2)
channel_cat_fp.to_csv(f"{OUT_DIR}/04b_channel_cat_firstpass.csv", index=False)

overall_fp_rate = all_inv["First_Pass"].sum() / len(all_inv) * 100
print(f"\nOverall first-pass rate (NB/ZCP posted, non-transport): {overall_fp_rate:.1f}%")

# ── 5. Exception Combinations / Sequencing ───────────────────────────────────
# Per invoice, collect ordered list of exception IDs
inv_exc_seq = (
    sorted_posted
    .sort_values(["Document Id","Work Item ID"])
    .groupby("Document Id")["Exception ID"]
    .apply(list)
    .reset_index(name="Exc_Seq")
)
inv_exc_seq["N_Exceptions"] = inv_exc_seq["Exc_Seq"].apply(len)

dist = inv_exc_seq["N_Exceptions"].value_counts().sort_index().reset_index()
dist.columns = ["N_Exceptions","Invoice_Count"]
dist.to_csv(f"{OUT_DIR}/05_exception_count_dist.csv", index=False)

# Pairs
pairs = Counter()
triples = Counter()
for seq in inv_exc_seq["Exc_Seq"]:
    unique_ids = list(dict.fromkeys(seq))  # deduplicate preserving order
    if len(unique_ids) >= 2:
        for a, b in zip(unique_ids, unique_ids[1:]):
            pairs[(a,b)] += 1
    if len(unique_ids) >= 3:
        for a, b, c in zip(unique_ids, unique_ids[1:], unique_ids[2:]):
            triples[(a,b,c)] += 1

pairs_df = pd.DataFrame([(f"{a} -> {b}", v) for (a,b),v in pairs.most_common(20)],
                        columns=["Pair","Count"])
triples_df = pd.DataFrame([(f"{a} -> {b} -> {c}", v) for (a,b,c),v in triples.most_common(20)],
                          columns=["Triple","Count"])
pairs_df.to_csv(f"{OUT_DIR}/05_exception_pairs.csv", index=False)
triples_df.to_csv(f"{OUT_DIR}/05_exception_triples.csv", index=False)
print("\n--- Top 10 Exception Pairs ---")
print(pairs_df.head(10).to_string(index=False))

# ── 6. Monthly Trends ────────────────────────────────────────────────────────
sorted_posted2 = sorted_posted.copy()
sorted_posted2["Month"] = sorted_posted2["Created at_dt"].dt.to_period("M")

monthly_exc = (
    sorted_posted2.groupby("Month")
    .size()
    .reset_index(name="Exception_Events")
)

# Monthly first-pass using inc
inc_posted2 = inc_posted_nb_zcp.copy()
inc_posted2["Month"] = inc_posted2["Created at_dt"].dt.to_period("M")
monthly_all = (
    inc_posted2.groupby("Month")["Document Id"].nunique().reset_index(name="Total_Invoices")
)
# exception invoices per month
exc_by_month = (
    sorted_posted2.groupby("Month")["Document Id"].nunique().reset_index(name="Exc_Invoices")
)
monthly_trend = monthly_all.merge(exc_by_month, on="Month", how="left").fillna(0)
monthly_trend["First_Pass_Rate"] = (
    (monthly_trend["Total_Invoices"] - monthly_trend["Exc_Invoices"])
    / monthly_trend["Total_Invoices"] * 100
).round(2)
monthly_trend["Month_str"] = monthly_trend["Month"].astype(str)
monthly_trend.to_csv(f"{OUT_DIR}/06_monthly_trends.csv", index=False)
print("\n--- Monthly Trends ---")
print(monthly_trend[["Month_str","Total_Invoices","Exc_Invoices","First_Pass_Rate"]].to_string(index=False))

# ── 7. AP Workload Concentration ─────────────────────────────────────────────
total_events = vendor["Exception_Events"].sum()
vendor_sorted_by_events = vendor.sort_values("Exception_Events", ascending=False).reset_index(drop=True)
vendor_sorted_by_events["Cumulative_Events"] = vendor_sorted_by_events["Exception_Events"].cumsum()
vendor_sorted_by_events["Cumulative_Pct"] = (
    vendor_sorted_by_events["Cumulative_Events"] / total_events * 100
).round(2)
vendor_sorted_by_events.to_csv(f"{OUT_DIR}/07_workload_concentration.csv", index=False)

for n in [10, 20, 50]:
    top_n_pct = vendor_sorted_by_events.iloc[:n]["Exception_Events"].sum() / total_events * 100
    print(f"Top {n} vendors = {top_n_pct:.1f}% of exception events")

# ── KPI Summary ───────────────────────────────────────────────────────────────
total_invoices = all_inv["Document Id"].nunique()
first_pass_count = all_inv["First_Pass"].sum()
kpi = {
    "total_invoices": int(total_invoices),
    "first_pass_count": int(first_pass_count),
    "first_pass_rate": round(float(overall_fp_rate), 1),
    "total_exception_events": int(len(sorted_posted)),
    "unique_vendors_with_exceptions": int(vendor["Supplier"].nunique()),
    "top10_vendor_pct": round(float(vendor_sorted_by_events.iloc[:10]["Exception_Events"].sum() / total_events * 100), 1),
}
print("\n--- KPIs ---")
for k, v in kpi.items():
    print(f"  {k}: {v}")

# ── Build JSON payloads for dashboard ─────────────────────────────────────────
def to_json(obj):
    return json.dumps(obj, default=str)

# Prepare all data as dicts for embedding in HTML
dashboard_data = {
    "kpi": kpi,
    "exc_freq": exc_freq.head(20).to_dict(orient="records"),
    "vendor_top30": vendor_top.head(30).to_dict(orient="records"),
    "vendor_intensity": vendor[vendor["Unique_Invoices"] >= 10].sort_values("Avg_Exc_Per_Inv", ascending=False).head(20).to_dict(orient="records"),
    "cat_summary": cat_summary.to_dict(orient="records"),
    "cat_exc": cat_exc.head(60).to_dict(orient="records"),
    "channel_fp": channel_fp.to_dict(orient="records"),
    "channel_cat_fp": channel_cat_fp.to_dict(orient="records"),
    "exc_dist": dist.to_dict(orient="records"),
    "exc_pairs": pairs_df.head(15).to_dict(orient="records"),
    "exc_triples": triples_df.head(10).to_dict(orient="records"),
    "monthly": monthly_trend[["Month_str","Total_Invoices","Exc_Invoices","First_Pass_Rate"]].to_dict(orient="records"),
    "workload_conc": vendor_sorted_by_events.head(50)[["Name 1","Supplier","Exception_Events","Unique_Invoices","Cumulative_Pct"]].to_dict(orient="records"),
}

with open(f"{OUT_DIR}/dashboard_data.json", "w") as f:
    json.dump(dashboard_data, f, default=str, indent=2)

print("\nAll CSVs and JSON saved to output/")
print("Dashboard data ready.")
