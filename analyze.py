import os
import pandas as pd
import json
import re
from collections import Counter
from itertools import combinations

# ── Load data ───────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SORTED_FILE = os.path.join(SCRIPT_DIR, "1100 VIM Exceptions Data(DATA - 1100 Sorted) (1).csv")
INC_FILE    = os.path.join(SCRIPT_DIR, "1100 Data inc.csv")
# Correct invoice universe: 2025 Invoices US file (includes invoices with no exceptions)
UNIVERSE_FILE = os.path.join(SCRIPT_DIR, "data_verify", "2025 invoices US(1head data) (3).csv")
OUT_DIR = os.path.join(SCRIPT_DIR, "output")

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
universe_raw = pd.read_csv(UNIVERSE_FILE, encoding="latin-1", low_memory=False)

print(f"Sorted raw rows:   {len(sorted_raw)}")
print(f"Inc raw rows:      {len(inc_raw)}")
print(f"Universe raw rows: {len(universe_raw)}")

# ── Cleaning helpers ─────────────────────────────────────────────────────────
TRANSPORT_PREFIX = "52"
VALID_PO_TYPES   = ["NB", "ZCP"]
# Vendors excluded from first-pass calculation (must match dashboard chart filter)
FP_EXCLUDE_VENDORS = {"SOUTHERN IONICS INCORPORATED", "TERRA FIRST"}

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
inc_df    = clean(inc_raw, filter_po=False)  # keep all PO types for exception inc analysis

# Posted only for most analyses
sorted_posted = sorted_df[sorted_df["Document Status"].astype(str).str.strip() == "15"]
inc_posted    = inc_df[inc_df["Document Status"].astype(str).str.strip() == "15"]

# ── Correct invoice universe (denominator for first-pass) ────────────────────
# Filter to Posted + Regular (PO Type descr = "Regular") — gives 16,580 invoices
# matching Dheer's verified pivot in Sheet1 of 2025 Invoices US file.
universe_df = universe_raw[
    (universe_raw["Status Descrip"].str.strip() == "Posted") &
    (universe_raw["PO Type descr"].str.strip() == "Regular")
].copy()
universe_df["Document Id"] = universe_raw.loc[universe_df.index, "Document Id"]
universe_df["Channel ID"] = universe_df["Channel ID"].astype(str).str.strip()
universe_df["PO category decription"] = universe_df["PO category decription"].astype(str).str.strip()
universe_df["Name 1"] = universe_df["Name 1"].astype(str).str.upper().str.strip()
universe_df["Month"] = pd.to_datetime(universe_df["Document Create Date"], errors="coerce").dt.to_period("M")
# Drop the two vendors excluded from all dashboard charts so KPI + chart denominators match
universe_df = universe_df[~universe_df["Name 1"].isin(FP_EXCLUDE_VENDORS)]
# First_Pass will be set after inc_posted is available (section 4)

print(f"\nUniverse (Posted + Regular): {len(universe_df)} rows, {universe_df['Document Id'].nunique()} unique invoices")

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
# Strict definition: an invoice is first-pass only if it has NO exception of any kind
# in the inc dataset (incl. Exc 0 and 91, all PO types and suppliers). Denominator
# excludes the two flagged vendors so KPI matches the filtered charts.
inc_all_posted = inc_raw[inc_raw["Document Status"].astype(str).str.strip() == "15"]
exc_inv_ids = set(inc_all_posted["Document Id"].unique())
universe_df["First_Pass"] = ~universe_df["Document Id"].isin(exc_inv_ids)
all_inv = universe_df[["Document Id","Channel ID","PO category decription","First_Pass"]].drop_duplicates("Document Id").copy()

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
print(f"\nOverall first-pass rate (Posted Regular, correct universe): {overall_fp_rate:.1f}%")

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
# Total invoices per month from universe (Document Create Date).
# Not-first-pass invoices per month = sorted exception doc IDs matched back to universe months.
monthly_all = (
    universe_df[universe_df["Month"].notna()]
    .groupby("Month")["Document Id"]
    .nunique()
    .reset_index(name="Total_Invoices")
)
monthly_nfp = (
    universe_df[universe_df["Month"].notna() & ~universe_df["First_Pass"]]
    .groupby("Month")["Document Id"]
    .nunique()
    .reset_index(name="Exc_Invoices")
)
monthly_trend = monthly_all.merge(monthly_nfp, on="Month", how="left").fillna(0)
monthly_trend["First_Pass_Rate"] = (
    (monthly_trend["Total_Invoices"] - monthly_trend["Exc_Invoices"])
    / monthly_trend["Total_Invoices"] * 100
).round(2)
monthly_trend["Month_str"] = monthly_trend["Month"].astype(str)
monthly_trend.to_csv(f"{OUT_DIR}/06_monthly_trends.csv", index=False)
print("\n--- Monthly Trends ---")
print(monthly_trend[["Month_str","Total_Invoices","Exc_Invoices","First_Pass_Rate"]].to_string(index=False))

# ── 6b. Per-Month KPI Rollup (STRICT, matches headline KPIs) ─────────────────
# All four headline KPIs broken down by month. Total_Invoices and FP Rate come
# from universe_df (Document Create Date). Exception events and unique vendors
# come from inc_posted using its own Created at month.
inc_posted_m = inc_posted.copy()
inc_posted_m["Month"] = pd.to_datetime(inc_posted_m["Created at"], errors="coerce").dt.to_period("M")

monthly_exc_events = (
    inc_posted_m[inc_posted_m["Month"].notna()]
    .groupby("Month").size().reset_index(name="Total_Exception_Events")
)
monthly_exc_vendors = (
    inc_posted_m[inc_posted_m["Month"].notna()]
    .groupby("Month")["Supplier"].nunique()
    .reset_index(name="Unique_Vendors_With_Exceptions")
)

monthly_kpis = (
    monthly_trend[["Month","Month_str","Total_Invoices","Exc_Invoices","First_Pass_Rate"]]
    .merge(monthly_exc_events, on="Month", how="left")
    .merge(monthly_exc_vendors, on="Month", how="left")
    .fillna(0)
)
monthly_kpis["Total_Exception_Events"] = monthly_kpis["Total_Exception_Events"].astype(int)
monthly_kpis["Unique_Vendors_With_Exceptions"] = monthly_kpis["Unique_Vendors_With_Exceptions"].astype(int)
monthly_kpis.to_csv(f"{OUT_DIR}/06b_monthly_kpis.csv", index=False)
print("\n--- Monthly KPIs (strict, per-month rollup) ---")
print(monthly_kpis[["Month_str","Total_Invoices","First_Pass_Rate","Total_Exception_Events","Unique_Vendors_With_Exceptions"]].to_string(index=False))

# ── 6c. Strict Exception Frequency (incl. Exc 0 & 91) ────────────────────────
exc_freq_strict = (
    inc_posted
    .groupby(["Exception ID","Exception description"])
    .size()
    .reset_index(name="Count")
    .sort_values("Count", ascending=False)
)
exc_freq_strict["Pct"] = (exc_freq_strict["Count"] / exc_freq_strict["Count"].sum() * 100).round(2)
exc_freq_strict.to_csv(f"{OUT_DIR}/01b_exception_freq_strict.csv", index=False)
print("\n--- Exception Frequency STRICT (top 15, includes Exc 0 & 91) ---")
print(exc_freq_strict.head(15).to_string(index=False))

# ── 6d. Strict Exception by Category (incl. Exc 0 & 91) ──────────────────────
cat_exc_strict = (
    inc_posted
    .groupby(["PO category decription","Exception ID","Exception description"])
    .size()
    .reset_index(name="Count")
    .sort_values(["PO category decription","Count"], ascending=[True,False])
)
cat_exc_strict.to_csv(f"{OUT_DIR}/03b_cat_exc_strict.csv", index=False)

cat_summary_strict = (
    inc_posted
    .groupby("PO category decription")
    .size()
    .reset_index(name="Exception_Events")
    .sort_values("Exception_Events", ascending=False)
)
print("\n--- Exception Events by Category STRICT (incl. Exc 0 & 91) ---")
print(cat_summary_strict.to_string(index=False))

# ── 6e. Strict Vendor Aggregations (incl. Exc 0 & 91) ────────────────────────
# Same SI/TF vendor exclusion as the filtered view so the toggle is an
# apples-to-apples "Exc 0 & 91 in or out" comparison.
inc_posted_vend = inc_posted.copy()
inc_posted_vend["Name 1"] = inc_posted_vend["Name 1"].astype(str).str.upper().str.strip()
inc_posted_excl = inc_posted_vend[~inc_posted_vend["Name 1"].isin(FP_EXCLUDE_VENDORS)]

vendor_inv_strict = (
    inc_posted_excl
    .groupby(["Supplier","Name 1"])["Document Id"]
    .nunique()
    .reset_index(name="Unique_Invoices")
)
vendor_events_strict = (
    inc_posted_excl
    .groupby(["Supplier","Name 1"])
    .size()
    .reset_index(name="Exception_Events")
)
vendor_strict = vendor_inv_strict.merge(vendor_events_strict, on=["Supplier","Name 1"])
vendor_strict["Avg_Exc_Per_Inv"] = (vendor_strict["Exception_Events"] / vendor_strict["Unique_Invoices"]).round(2)
vendor_top_strict = vendor_strict.sort_values("Exception_Events", ascending=False).head(50)
vendor_top_strict.to_csv(f"{OUT_DIR}/02b_top_vendors_strict.csv", index=False)
print("\n--- Top 10 Vendors STRICT (incl. Exc 0 & 91) ---")
print(vendor_top_strict.head(10)[["Name 1","Unique_Invoices","Exception_Events","Avg_Exc_Per_Inv"]].to_string(index=False))

# ── 6f. Strict Workload Concentration (Pareto, incl. Exc 0 & 91) ─────────────
total_events_strict_all = vendor_strict["Exception_Events"].sum()
vendor_strict_sorted = vendor_strict.sort_values("Exception_Events", ascending=False).reset_index(drop=True)
vendor_strict_sorted["Cumulative_Events"] = vendor_strict_sorted["Exception_Events"].cumsum()
vendor_strict_sorted["Cumulative_Pct"] = (
    vendor_strict_sorted["Cumulative_Events"] / total_events_strict_all * 100
).round(2)
vendor_strict_sorted.to_csv(f"{OUT_DIR}/07b_workload_conc_strict.csv", index=False)

# ── 6g. Strict Vendor Exception Detail (top 20 + SI/TF for drill-down) ──────
# Per-vendor exception-type breakdown using inc_posted (incl. 0 & 91). Includes
# the two SI/TF vendors so the vendor table can drill into them on demand.
top_strict_sup_ids = set(vendor_top_strict.head(20)["Supplier"].astype(str)) | {"51003869","51003955"}
ved_strict_rows = []
for sup_id in top_strict_sup_ids:
    sub = inc_posted_vend[inc_posted_vend["Supplier"].astype(str) == sup_id]
    if sub.empty:
        continue
    name = sub["Name 1"].iloc[0]
    excs = (
        sub.groupby(["Exception ID","Exception description"])
        .size()
        .reset_index(name="cnt")
        .sort_values("cnt", ascending=False)
    )
    excs_records = []
    for _, r in excs.iterrows():
        try:
            eid = int(r["Exception ID"])
        except (ValueError, TypeError):
            eid = str(r["Exception ID"])
        excs_records.append({
            "id": eid,
            "desc": str(r["Exception description"]),
            "cnt": int(r["cnt"]),
        })
    ved_strict_rows.append({
        "sup": str(sup_id),
        "name": name,
        "inv": int(sub["Document Id"].nunique()),
        "exc": int(len(sub)),
        "excs": excs_records,
    })

# ── 6h. Strict Co-occurrence Pairs (from inc_posted, incl. Exc 0 & 91) ───────
# Sort by Created at since inc_raw lacks Work Item ID; this gives chronological
# ordering of exceptions for pair detection.
inc_pairs_src = inc_posted.copy()
if "Created at" in inc_pairs_src.columns:
    inc_pairs_src["Created at_sort"] = pd.to_datetime(inc_pairs_src["Created at"], errors="coerce")
    inc_pairs_src = inc_pairs_src.sort_values(["Document Id","Created at_sort"])
else:
    inc_pairs_src = inc_pairs_src.sort_values(["Document Id"])

inv_exc_seq_strict = (
    inc_pairs_src
    .groupby("Document Id")["Exception ID"]
    .apply(list)
    .reset_index(name="Exc_Seq")
)
pairs_strict = Counter()
for seq in inv_exc_seq_strict["Exc_Seq"]:
    unique_ids = list(dict.fromkeys(seq))
    if len(unique_ids) >= 2:
        for a, b in zip(unique_ids, unique_ids[1:]):
            pairs_strict[(a, b)] += 1
pairs_strict_df = pd.DataFrame(
    [(f"{a} -> {b}", v) for (a,b), v in pairs_strict.most_common(20)],
    columns=["Pair","Count"]
)
pairs_strict_df.to_csv(f"{OUT_DIR}/05b_exception_pairs_strict.csv", index=False)
print("\n--- Top 10 Exception Pairs STRICT (incl. Exc 0 & 91) ---")
print(pairs_strict_df.head(10).to_string(index=False))

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
    "monthly_kpis": monthly_kpis[["Month_str","Total_Invoices","First_Pass_Rate","Total_Exception_Events","Unique_Vendors_With_Exceptions"]].to_dict(orient="records"),
    "exc_freq_strict": exc_freq_strict.head(20).to_dict(orient="records"),
    "cat_exc_strict": cat_exc_strict.to_dict(orient="records"),
    "cat_summary_strict": cat_summary_strict.to_dict(orient="records"),
    "workload_conc": vendor_sorted_by_events.head(50)[["Name 1","Supplier","Exception_Events","Unique_Invoices","Cumulative_Pct"]].to_dict(orient="records"),
    "vendor_top30_strict": vendor_top_strict.head(30).to_dict(orient="records"),
    "workload_conc_strict": vendor_strict_sorted.head(50)[["Name 1","Supplier","Exception_Events","Unique_Invoices","Cumulative_Pct"]].to_dict(orient="records"),
    "vendor_exc_detail_strict": ved_strict_rows,
    "exc_pairs_strict": pairs_strict_df.head(15).to_dict(orient="records"),
}

with open(f"{OUT_DIR}/dashboard_data.json", "w") as f:
    json.dump(dashboard_data, f, default=str, indent=2)

print("\nAll CSVs and JSON saved to output/")
print("Dashboard data ready.")
