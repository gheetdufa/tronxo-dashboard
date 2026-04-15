"""
Extended analysis for the Tronox 1100 dashboard.
Adds: Exception 91 deep dive, Exceptions 151 & 29 detail, COUPA+Service explanation.
"""
import os
import pandas as pd
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SORTED_FILE = os.path.join(SCRIPT_DIR, "1100 VIM Exceptions Data(DATA - 1100 Sorted) (1).csv")
INC_FILE = os.path.join(SCRIPT_DIR, "1100 Data inc.csv")
OUT_DIR = os.path.join(SCRIPT_DIR, "output")

def load(path):
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
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

TRANSPORT_PREFIX = "52"
VALID_PO_TYPES   = ["NB", "ZCP"]

def clean_base(df):
    df = df.copy()
    df["Supplier"] = df["Supplier"].astype(str).str.strip()
    df = df[~df["Supplier"].str.startswith(TRANSPORT_PREFIX)]
    df["PO Type"] = df["PO Type"].astype(str).str.strip().str.upper()
    df["Created at_dt"] = pd.to_datetime(df["Created at"], errors="coerce")
    df["Month"] = df["Created at_dt"].dt.to_period("M").astype(str)
    return df

sorted_raw = clean_base(load(SORTED_FILE))
inc_raw    = clean_base(load(INC_FILE))

sorted_posted = sorted_raw[
    (sorted_raw["Document Status"].astype(str).str.strip() == "15") &
    sorted_raw["PO Type"].isin(VALID_PO_TYPES)
]
inc_posted = inc_raw[
    (inc_raw["Document Status"].astype(str).str.strip() == "15") &
    inc_raw["PO Type"].isin(VALID_PO_TYPES)
]

exc_inv_ids = set(sorted_posted["Document Id"].unique())
all_inv = (
    inc_posted.groupby(["Document Id","Channel ID","PO category decription"])
    .first().reset_index()[["Document Id","Channel ID","PO category decription"]]
)
all_inv["First_Pass"] = ~all_inv["Document Id"].isin(exc_inv_ids)

# ═══════════════════════════════════════════════════════
# 1. EXCEPTION 91 — GR Not Done Simple Check
# ═══════════════════════════════════════════════════════
exc91 = inc_posted[inc_posted["Exception ID"] == 91].copy()

# Category breakdown
e91_cat = exc91.groupby("PO category decription").agg(
    Events=("Document Id","count"),
    Unique_Inv=("Document Id","nunique")
).reset_index().sort_values("Events", ascending=False)
e91_cat["Pct"] = (e91_cat["Events"] / e91_cat["Events"].sum() * 100).round(1)

# Channel x Category heatmap
e91_ch_cat = pd.crosstab(
    exc91["PO category decription"], exc91["Channel ID"]
).reset_index().rename(columns={"PO category decription":"Category"})
e91_ch_cat_long = exc91.groupby(["Channel ID","PO category decription"]).agg(
    Events=("Document Id","count"),
    Unique_Inv=("Document Id","nunique")
).reset_index()

# Monthly by category
e91_monthly = exc91.groupby(["Month","PO category decription"]).size().reset_index(name="Events")
e91_monthly = e91_monthly[e91_monthly["Month"] != "2026-01"]  # drop partial

# Top vendors
e91_vendors = (
    exc91.groupby(["Supplier","Name 1"]).agg(
        Events=("Document Id","count"),
        Unique_Inv=("Document Id","nunique")
    ).reset_index().sort_values("Events", ascending=False).head(20)
)

# Co-occurring exceptions on exc91 invoices (from inc_posted)
inv_91_ids = set(exc91["Document Id"])
cooccur_91 = (
    inc_posted[inc_posted["Document Id"].isin(inv_91_ids) & (inc_posted["Exception ID"] != 91)]
    .groupby(["Exception ID","Exception description"]).size().reset_index(name="Count")
    .sort_values("Count", ascending=False).head(10)
)

# Save
e91_vendors.to_csv(f"{OUT_DIR}/91_top_vendors.csv", index=False)
e91_monthly.to_csv(f"{OUT_DIR}/91_monthly_by_cat.csv", index=False)
e91_ch_cat_long.to_csv(f"{OUT_DIR}/91_channel_category.csv", index=False)

print("=== Exception 91 ===")
print(e91_cat.to_string(index=False))

# ═══════════════════════════════════════════════════════
# 2. EXCEPTION 151 — Manual Check / Missing Indexing
# ═══════════════════════════════════════════════════════
e151 = sorted_posted[sorted_posted["Exception ID"] == 151].copy()

e151_cat = e151.groupby("PO category decription").agg(
    Events=("Document Id","count"),
    Unique_Inv=("Document Id","nunique")
).reset_index().sort_values("Events", ascending=False)
e151_cat["Pct"] = (e151_cat["Events"] / e151_cat["Events"].sum() * 100).round(1)

e151_ch_cat = e151.groupby(["Channel ID","PO category decription"]).agg(
    Events=("Document Id","count"),
    Unique_Inv=("Document Id","nunique")
).reset_index()
e151_ch_cat["Pct_of_exc"] = (e151_ch_cat["Events"] / e151_ch_cat["Events"].sum() * 100).round(1)

e151_vendors = (
    e151.groupby(["Supplier","Name 1"]).agg(
        Events=("Document Id","count"),
        Unique_Inv=("Document Id","nunique")
    ).reset_index().sort_values("Events", ascending=False).head(20)
)
e151_vendors["Avg_Exc_Per_Inv"] = (e151_vendors["Events"]/e151_vendors["Unique_Inv"]).round(2)

e151_monthly = e151.groupby(["Month","PO category decription"]).size().reset_index(name="Events")
e151_monthly = e151_monthly[e151_monthly["Month"] != "2026-01"]

e151_touches = e151.groupby("Document Id")["Number of Touches"].max().reset_index(name="MaxTouches")
touch_dist_151 = e151_touches["MaxTouches"].clip(upper=10).value_counts().sort_index().reset_index()
touch_dist_151.columns = ["Touches","Invoice_Count"]

# Co-occurring exceptions on exc151 invoices
inv_151_ids = set(e151["Document Id"])
cooccur_151 = (
    sorted_posted[sorted_posted["Document Id"].isin(inv_151_ids) & (sorted_posted["Exception ID"] != 151)]
    .groupby(["Exception ID","Exception description"]).size().reset_index(name="Count")
    .sort_values("Count", ascending=False).head(10)
)

e151_vendors.to_csv(f"{OUT_DIR}/151_top_vendors.csv", index=False)
e151_monthly.to_csv(f"{OUT_DIR}/151_monthly_by_cat.csv", index=False)

print("\n=== Exception 151 ===")
print(e151_cat.to_string(index=False))
print("Channel x Category:")
print(e151_ch_cat.to_string(index=False))

# ═══════════════════════════════════════════════════════
# 3. EXCEPTION 29 — Missing Mandatory Information
# ═══════════════════════════════════════════════════════
e29 = sorted_posted[sorted_posted["Exception ID"] == 29].copy()

e29_cat = e29.groupby("PO category decription").agg(
    Events=("Document Id","count"),
    Unique_Inv=("Document Id","nunique")
).reset_index().sort_values("Events", ascending=False)
e29_cat["Pct"] = (e29_cat["Events"] / e29_cat["Events"].sum() * 100).round(1)

e29_ch_cat = e29.groupby(["Channel ID","PO category decription"]).agg(
    Events=("Document Id","count"),
    Unique_Inv=("Document Id","nunique")
).reset_index()
e29_ch_cat["Pct_of_exc"] = (e29_ch_cat["Events"] / e29_ch_cat["Events"].sum() * 100).round(1)

e29_vendors = (
    e29.groupby(["Supplier","Name 1"]).agg(
        Events=("Document Id","count"),
        Unique_Inv=("Document Id","nunique")
    ).reset_index().sort_values("Events", ascending=False).head(20)
)
e29_vendors["Avg_Exc_Per_Inv"] = (e29_vendors["Events"]/e29_vendors["Unique_Inv"]).round(2)

e29_monthly = e29.groupby(["Month","PO category decription"]).size().reset_index(name="Events")
e29_monthly = e29_monthly[e29_monthly["Month"] != "2026-01"]

inv_29_ids = set(e29["Document Id"])
cooccur_29 = (
    sorted_posted[sorted_posted["Document Id"].isin(inv_29_ids) & (sorted_posted["Exception ID"] != 29)]
    .groupby(["Exception ID","Exception description"]).size().reset_index(name="Count")
    .sort_values("Count", ascending=False).head(10)
)

e29_vendors.to_csv(f"{OUT_DIR}/29_top_vendors.csv", index=False)
e29_monthly.to_csv(f"{OUT_DIR}/29_monthly_by_cat.csv", index=False)

print("\n=== Exception 29 ===")
print(e29_cat.to_string(index=False))

# ═══════════════════════════════════════════════════════
# 4. COUPA + SERVICE deep dive
# ═══════════════════════════════════════════════════════
coupa_svc = all_inv[(all_inv["Channel ID"]=="COUPA") & (all_inv["PO category decription"]=="Service")]
coupa_std = all_inv[(all_inv["Channel ID"]=="COUPA") & (all_inv["PO category decription"]=="Standard")]

# All channel x category first-pass matrix
cc_fp = all_inv.groupby(["Channel ID","PO category decription"]).agg(
    Total=("Document Id","count"),
    FP_Count=("First_Pass","sum")
).reset_index()
cc_fp["FP_Rate"] = (cc_fp["FP_Count"]/cc_fp["Total"]*100).round(1)

# Exceptions on FAILED COUPA+Service invoices
fail_ids_cs = set(coupa_svc[~coupa_svc["First_Pass"]]["Document Id"])
exc_on_cs_fail = (
    sorted_posted[sorted_posted["Document Id"].isin(fail_ids_cs)]
    .groupby(["Exception ID","Exception description"]).size().reset_index(name="Count")
    .sort_values("Count", ascending=False)
)

# Exceptions on PASSED COUPA+Service invoices (from inc file)
pass_ids_cs = set(coupa_svc[coupa_svc["First_Pass"]]["Document Id"])
exc_on_cs_pass = (
    inc_posted[inc_posted["Document Id"].isin(pass_ids_cs)]
    .groupby(["Exception ID","Exception description"]).size().reset_index(name="Count")
    .sort_values("Count", ascending=False)
)

# Same for COUPA+Standard failures
fail_ids_cstd = set(coupa_std[~coupa_std["First_Pass"]]["Document Id"])
exc_on_cstd_fail = (
    sorted_posted[sorted_posted["Document Id"].isin(fail_ids_cstd)]
    .groupby(["Exception ID","Exception description"]).size().reset_index(name="Count")
    .sort_values("Count", ascending=False)
)

# Monthly COUPA performance by category
coupa_inv = all_inv[all_inv["Channel ID"]=="COUPA"].copy()
coupa_inv["Month"] = coupa_inv["Document Id"].map(
    inc_posted.drop_duplicates("Document Id").set_index("Document Id")["Month"]
)
coupa_monthly = coupa_inv.groupby(["Month","PO category decription"]).agg(
    Total=("Document Id","count"),
    FP_Count=("First_Pass","sum")
).reset_index()
coupa_monthly["FP_Rate"] = (coupa_monthly["FP_Count"]/coupa_monthly["Total"]*100).round(1)
coupa_monthly = coupa_monthly[coupa_monthly["Month"].notna() & (coupa_monthly["Month"] != "2026-01")]

print("\n=== COUPA + Service ===")
print(f"Total: {len(coupa_svc)}, First-pass: {coupa_svc['First_Pass'].sum()}, Rate: {coupa_svc['First_Pass'].mean()*100:.1f}%")
print("\nExceptions on FAILED COUPA+Service invoices:")
print(exc_on_cs_fail.to_string(index=False))
print("\nExceptions on PASSED COUPA+Service invoices (inc file):")
print(exc_on_cs_pass.to_string(index=False))
print("\n=== COUPA + Standard ===")
print(f"Total: {len(coupa_std)}, First-pass: {coupa_std['First_Pass'].sum()}, Rate: {coupa_std['First_Pass'].mean()*100:.1f}%")
print("\nExceptions on FAILED COUPA+Standard invoices:")
print(exc_on_cstd_fail.to_string(index=False))
print("\n=== Full Channel x Category Matrix ===")
print(cc_fp.to_string(index=False))

# ═══════════════════════════════════════════════════════
# 5. Save extended dashboard data
# ═══════════════════════════════════════════════════════
extended = {
    # Exception 91
    "e91_cat": e91_cat.to_dict(orient="records"),
    "e91_ch_cat": e91_ch_cat_long.to_dict(orient="records"),
    "e91_monthly": e91_monthly.to_dict(orient="records"),
    "e91_vendors": e91_vendors.head(20).to_dict(orient="records"),
    "e91_cooccur": cooccur_91.to_dict(orient="records"),
    # Exception 151
    "e151_cat": e151_cat.to_dict(orient="records"),
    "e151_ch_cat": e151_ch_cat.to_dict(orient="records"),
    "e151_vendors": e151_vendors.head(20).to_dict(orient="records"),
    "e151_monthly": e151_monthly.to_dict(orient="records"),
    "e151_cooccur": cooccur_151.to_dict(orient="records"),
    "e151_touch_dist": touch_dist_151.to_dict(orient="records"),
    # Exception 29
    "e29_cat": e29_cat.to_dict(orient="records"),
    "e29_ch_cat": e29_ch_cat.to_dict(orient="records"),
    "e29_vendors": e29_vendors.head(20).to_dict(orient="records"),
    "e29_monthly": e29_monthly.to_dict(orient="records"),
    "e29_cooccur": cooccur_29.to_dict(orient="records"),
    # COUPA + Service
    "cc_fp": cc_fp.to_dict(orient="records"),
    "coupa_svc_fail_exc": exc_on_cs_fail.to_dict(orient="records"),
    "coupa_svc_pass_exc": exc_on_cs_pass.to_dict(orient="records"),
    "coupa_std_fail_exc": exc_on_cstd_fail.to_dict(orient="records"),
    "coupa_monthly": coupa_monthly.to_dict(orient="records"),
    "coupa_svc_total": int(len(coupa_svc)),
    "coupa_svc_fp": int(coupa_svc["First_Pass"].sum()),
    "coupa_svc_fp_rate": round(float(coupa_svc["First_Pass"].mean()*100), 1),
    "coupa_std_fp_rate": round(float(coupa_std["First_Pass"].mean()*100), 1),
    "e91_total": int(len(exc91)),
    "e91_unique_inv": int(exc91["Document Id"].nunique()),
    "e151_total": int(len(e151)),
    "e151_unique_inv": int(e151["Document Id"].nunique()),
    "e29_total": int(len(e29)),
    "e29_unique_inv": int(e29["Document Id"].nunique()),
}

with open(f"{OUT_DIR}/extended_data.json", "w") as f:
    json.dump(extended, f, default=str, indent=2)

print("\nExtended data saved to output/extended_data.json")
