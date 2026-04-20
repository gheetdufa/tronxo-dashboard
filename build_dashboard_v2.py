"""
Build v2 of the self-contained HTML dashboard — adds 4 new sections:
  - Exception 91 deep dive (GR Not Done)
  - Exception 151 deep dive (Manual Check / Missing Indexing)
  - Exception 29 deep dive (Missing Mandatory Information)
  - COUPA + Service explained (why it beats 80%)
"""
import json, os, subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "output")


def _build_id():
    gh = os.environ.get("GITHUB_SHA", "")
    if gh and len(gh) >= 7:
        return gh[:7]
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=SCRIPT_DIR,
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).decode().strip()
    except Exception:
        return "local"


BUILD_ID = _build_id()

with open(f"{OUT_DIR}/dashboard_data.json") as f:
    D = json.load(f)
with open(f"{OUT_DIR}/extended_data.json") as f:
    E = json.load(f)

DATA_JS = json.dumps(D, default=str)
EXT_JS  = json.dumps(E, default=str)

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<meta name="dashboard-build" content="__BUILD_ID__"/>
<title>Tronox 1100 – AP Invoice Exception Dashboard (Audit 2026-01)</title>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<style>
:root{
  --tronox-blue:#1a3d6b;
  --tronox-teal:#007a8a;
  --tronox-green:#2d8a4e;
  --accent:#e8503a;
  --bg:#f4f6f9;
  --card:#ffffff;
  --border:#dde3ec;
  --text:#1e2a3a;
  --muted:#6b7a90;
  --sidebar-w:240px;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',Arial,sans-serif;background:var(--bg);color:var(--text);display:flex;min-height:100vh}

/* ── Sidebar ── */
#sidebar{
  width:var(--sidebar-w);min-width:var(--sidebar-w);
  background:var(--tronox-blue);color:#fff;
  display:flex;flex-direction:column;
  position:fixed;top:0;left:0;height:100vh;
  overflow-y:auto;z-index:100;
}
#sidebar .logo{padding:20px 16px 12px;border-bottom:1px solid rgba(255,255,255,.15)}
#sidebar .logo .brand{font-size:1.2rem;font-weight:700;letter-spacing:.4px}
#sidebar .logo .sub{font-size:.68rem;opacity:.7;margin-top:3px}
#sidebar nav{flex:1;padding:8px 0}
#sidebar nav .nav-group{padding:8px 16px 2px;font-size:.65rem;text-transform:uppercase;letter-spacing:1px;opacity:.5}
#sidebar nav a{
  display:block;padding:8px 16px;color:rgba(255,255,255,.82);
  text-decoration:none;font-size:.8rem;border-left:3px solid transparent;
  transition:all .15s;
}
#sidebar nav a:hover,#sidebar nav a.active{
  color:#fff;background:rgba(255,255,255,.1);border-left-color:var(--tronox-teal);
}
#sidebar .footer-note{padding:10px 16px;font-size:.65rem;opacity:.45;border-top:1px solid rgba(255,255,255,.1)}

/* ── Main ── */
#main{margin-left:var(--sidebar-w);flex:1;padding:26px 30px;min-width:0}
h1.page-title{font-size:1.45rem;color:var(--tronox-blue);margin-bottom:3px}
.page-sub{font-size:.82rem;color:var(--muted);margin-bottom:22px}

/* ── Sections ── */
.section{display:none;animation:fadeIn .22s}
.section.active{display:block}
@keyframes fadeIn{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}

/* ── KPI Cards ── */
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:12px;margin-bottom:24px}
.kpi-card{background:var(--card);border-radius:10px;padding:16px;border:1px solid var(--border);display:flex;flex-direction:column;gap:5px}
.kpi-label{font-size:.69rem;color:var(--muted);text-transform:uppercase;letter-spacing:.4px}
.kpi-value{font-size:1.8rem;font-weight:700;color:var(--tronox-blue)}
.kpi-value.danger{color:var(--accent)}
.kpi-value.ok{color:var(--tronox-green)}
.kpi-value.warn{color:#c07000}
.kpi-note{font-size:.68rem;color:var(--muted)}

/* ── Cards ── */
.card{background:var(--card);border-radius:10px;padding:18px 20px;border:1px solid var(--border);margin-bottom:20px}
.card-title{font-size:.97rem;font-weight:600;color:var(--tronox-blue);margin-bottom:3px}
.card-sub{font-size:.76rem;color:var(--muted);margin-bottom:12px}

/* ── Interpretation ── */
.interp{background:#eef3fa;border-left:3px solid var(--tronox-teal);padding:10px 14px;border-radius:0 6px 6px 0;font-size:.79rem;line-height:1.65;color:#2b3a52;margin-top:14px}
.interp.warn{background:#fff8e1;border-left-color:#f0a500}
.interp.ok{background:#e8f5e9;border-left-color:var(--tronox-green)}
.interp.danger{background:#ffebee;border-left-color:var(--accent)}
.interp strong{font-weight:600}

/* ── Badge ── */
.badge{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:12px;font-size:.74rem;font-weight:600}
.badge.red{background:#ffebee;color:#c62828}
.badge.green{background:#e8f5e9;color:#1b5e20}
.badge.amber{background:#fff8e1;color:#856404}
.badge.blue{background:#e3f2fd;color:#0d47a1}
.badge.teal{background:#e0f4f6;color:#004d5a}

/* ── Stat highlight row ── */
.stat-row{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:16px}
.stat-box{flex:1;min-width:120px;background:#f0f4fa;border-radius:8px;padding:12px 14px}
.stat-box .sv{font-size:1.5rem;font-weight:700;color:var(--tronox-blue)}
.stat-box .sl{font-size:.7rem;color:var(--muted);margin-top:2px}
.stat-box.red .sv{color:var(--accent)}
.stat-box.green .sv{color:var(--tronox-green)}
.stat-box.amber .sv{color:#c07000}

/* ── Tables ── */
.tbl-wrap{overflow-x:auto;margin-top:14px}
table{width:100%;border-collapse:collapse;font-size:.76rem}
thead tr{background:var(--tronox-blue);color:#fff}
thead th{padding:7px 9px;text-align:left;cursor:pointer;user-select:none;white-space:nowrap}
thead th:hover{background:var(--tronox-teal)}
tbody tr:nth-child(even){background:#f7f9fc}
tbody td{padding:5px 9px;border-bottom:1px solid #eaecf0}
tbody tr:hover{background:#e8f0fe}

/* ── 2-col grid ── */
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:900px){.grid2{grid-template-columns:1fr}}

/* ── Divider label ── */
.section-label{font-size:.75rem;text-transform:uppercase;letter-spacing:.6px;color:var(--muted);margin:18px 0 10px;padding-bottom:4px;border-bottom:1px solid var(--border)}

/* ── Print ── */
@media print{
  #sidebar{display:none}
  #main{margin-left:0}
  .section{display:block!important}
  .card{break-inside:avoid}
}
</style>
</head>
<body>

<nav id="sidebar">
  <div class="logo">
    <div class="brand">TRONOX 1100</div>
    <div class="sub">AP Exception Dashboard · Audit 2026-01</div>
  </div>
  <nav>
    <div class="nav-group">Overview</div>
    <a href="#" class="active" data-sec="overview">&#9632; KPIs &amp; Summary</a>
    <a href="#" data-sec="exc-freq">&#9632; Exception Frequency</a>
    <div class="nav-group">Exception Deep Dives</div>
    <a href="#" data-sec="exc91">&#9632; Exc 91 — GR Not Done</a>
    <a href="#" data-sec="exc151">&#9632; Exc 151 — Missing Indexing</a>
    <a href="#" data-sec="exc29">&#9632; Exc 29 — Missing Info</a>
    <a href="#" data-sec="coupa-svc">&#9632; COUPA + Service Explained</a>
    <div class="nav-group">Vendor &amp; Category</div>
    <a href="#" data-sec="vendors">&#9632; Top Problem Vendors</a>
    <a href="#" data-sec="category">&#9632; Material Category</a>
    <div class="nav-group">Ingestion &amp; Trends</div>
    <a href="#" data-sec="channel">&#9632; Ingestion Method</a>
    <a href="#" data-sec="trends">&#9632; Monthly Trends</a>
    <div class="nav-group">Workload</div>
    <a href="#" data-sec="combos">&#9632; Exception Combinations</a>
    <a href="#" data-sec="workload">&#9632; AP Workload Concentration</a>
    <a href="#" data-sec="dq">&#9632; Data Quality Notes</a>
  </nav>
  <div class="footer-note">S4 AP Audit · 1100 · FY2025–2026<br/>Transport vendors excl · NB &amp; ZCP only<br/>Build <span id="dash-build-id">__BUILD_ID__</span></div>
</nav>

<main id="main">
  <h1 class="page-title">AP Invoice Exception Analysis — 1100 (US)</h1>
  <p class="page-sub">newTRON S4 Implementation · Internal Audit Ref: 2026-01 · Data through Jan 2026</p>

  <!-- ═══════════════ OVERVIEW ═══════════════ -->
  <div class="section active" id="sec-overview">
    <div class="stat-row" style="margin-bottom:14px">
      <div class="stat-box red"><div class="sv" id="fp-kpi">–</div><div class="sl">First-Pass Rate (vs 80% target)</div></div>
      <div class="stat-box"><div class="sv" id="inv-kpi">–</div><div class="sl">Total Invoices Analysed</div></div>
      <div class="stat-box"><div class="sv" id="exc-kpi">–</div><div class="sl">Total Exception Events</div></div>
      <div class="stat-box amber"><div class="sv" id="vend-kpi">–</div><div class="sl">Vendors w/ Exceptions</div></div>
      <div class="stat-box green"><div class="sv">83.4%</div><div class="sl">COUPA + Service (best performer)</div></div>
    </div>
    <div id="kpi-grid" class="kpi-grid"></div>
    <div class="card">
      <div class="card-title">First-Pass Rate by Channel × Category — Full Matrix</div>
      <div class="card-sub">Each cell shows the first-pass rate; green ≥ 80%, amber 50–79%, red &lt; 50%</div>
      <div id="chart-cc-heatmap" style="height:320px"></div>
      <div class="interp">
        <strong>COUPA + Service (83.4%)</strong> is the only channel/category combination that beats the 80% target — a finding that requires careful interpretation
        (see the dedicated section). Every other combination falls well short, with <strong>MAIL_IES + Standard (18.5%)</strong> being the worst performer
        and the single largest volume bucket. Fixing MAIL_IES + Standard is the highest-impact lever available.
      </div>
    </div>
    <div class="card">
      <div class="card-title">Top 10 Exception Types</div>
      <div id="chart-overview-exc" style="height:300px"></div>
    </div>
  </div>

  <!-- ═══════════════ EXCEPTION FREQUENCY ═══════════════ -->
  <div class="section" id="sec-exc-freq">
    <div class="card">
      <div class="card-title">Exception Frequency — All Types Ranked</div>
      <div class="card-sub">Sorted dataset (excl. IDs 0 &amp; 91) · Posted NB/ZCP · non-transport</div>
      <div id="chart-exc-bar" style="height:420px"></div>
      <div class="interp warn">
        <strong>Exception 1 "Process PO Invoice" (~30%)</strong> is a system artefact — VIM fires it every time it processes a PO invoice match step.
        It requires no AP action and inflates the exception count artificially. Removing it from AP's queue would immediately improve the apparent first-pass rate.
        <br/><br/>
        The two genuine data-quality workhorse exceptions — <strong>151 (Manual Check / Missing Indexing)</strong> and <strong>29 (Missing Mandatory Info)</strong> —
        together account for ~39% of real AP workload. These are explored in detail in their own sections.
      </div>
    </div>
    <div class="card">
      <div class="card-title">Exception Frequency Data Table</div>
      <div class="tbl-wrap"><table id="tbl-exc-freq">
        <thead><tr><th onclick="sortTable(this)">Exc ID</th><th onclick="sortTable(this)">Description</th><th onclick="sortTable(this)">Count</th><th onclick="sortTable(this)">% of Total</th></tr></thead>
        <tbody id="tbody-exc-freq"></tbody>
      </table></div>
    </div>
  </div>

  <!-- ═══════════════ EXCEPTION 91 ═══════════════ -->
  <div class="section" id="sec-exc91">
    <div class="stat-row">
      <div class="stat-box"><div class="sv" id="e91-total">–</div><div class="sl">Total Exc 91 Events (inc file)</div></div>
      <div class="stat-box"><div class="sv" id="e91-inv">–</div><div class="sl">Unique Invoices Affected</div></div>
      <div class="stat-box amber"><div class="sv">100%</div><div class="sl">All on ZCP PO type</div></div>
      <div class="stat-box red"><div class="sv">92.5%</div><div class="sl">Standard Material Category</div></div>
    </div>

    <div class="card">
      <div class="card-title">Exception 91 — GR Not Done (Simple Check): Breakdown by Material Category</div>
      <div class="card-sub">Exception 91 is excluded from the sorted dataset but retained in the full inc dataset. All occurrences are on ZCP (Work Order) PO type.</div>
      <div class="grid2">
        <div id="chart-e91-cat-pie" style="height:300px"></div>
        <div id="chart-e91-cat-bar" style="height:300px"></div>
      </div>
      <div class="interp danger">
        <strong>Why is Exception 91 almost entirely Standard materials (92.5%)?</strong><br/>
        ZCP = "Regular WO/services" PO type, meaning these are procurement orders raised against maintenance or operational <em>work orders</em>.
        Standard materials bought via work orders (e.g., spare parts, consumables for a specific job) require a goods receipt (GR) confirmation
        before VIM can match the invoice. If the maintenance team hasn't confirmed the GR in S4 by the time the invoice arrives, Exception 91 fires.
        <br/><br/>
        The audit team has classified Exception 91 as non-material (excluded from sorted file) because it auto-resolves once the GR is posted —
        but it represents a <strong>process timing gap between maintenance execution and procurement confirmation</strong>.
        The spike in Standard category (92.5%) vs Service (4.5%) confirms this is a <em>goods-receipt workflow lag</em>, not a
        vendor data quality issue.
      </div>
    </div>

    <div class="card">
      <div class="card-title">Exc 91 — Monthly Volume by Category</div>
      <div class="card-sub">Growing trend in Standard materials through mid-2025 suggests increasing WO invoice volume without GR discipline improving</div>
      <div id="chart-e91-monthly" style="height:300px"></div>
    </div>

    <div class="card">
      <div class="card-title">Exc 91 — Channel × Category Breakdown</div>
      <div class="card-sub">Which ingestion channels are affected by GR-not-done delays</div>
      <div id="chart-e91-ch-cat" style="height:280px"></div>
      <div class="interp">
        COUPA contributes 1,684 Exc 91 events (mostly Standard), showing that even Coupa-submitted invoices are held up by GR timing gaps.
        This means moving invoices to Coupa will NOT fix the GR discipline issue — that requires a <strong>warehouse/maintenance team intervention</strong>,
        not an AP-side fix.
      </div>
    </div>

    <div class="card">
      <div class="card-title">Exc 91 — Top 20 Vendors</div>
      <div class="card-sub">These vendors' invoices most frequently arrive before the goods receipt is posted</div>
      <div id="chart-e91-vendors" style="height:420px"></div>
      <div class="tbl-wrap"><table id="tbl-e91-vendors">
        <thead><tr><th onclick="sortTable(this)">Vendor #</th><th onclick="sortTable(this)">Name</th><th onclick="sortTable(this)">Exc 91 Events</th><th onclick="sortTable(this)">Unique Invoices</th></tr></thead>
        <tbody id="tbody-e91-vendors"></tbody>
      </table></div>
    </div>

    <div class="card">
      <div class="card-title">Exc 91 — Co-occurring Exceptions</div>
      <div class="card-sub">What other exceptions appear on the same invoices that triggered Exc 91?</div>
      <div id="chart-e91-cooccur" style="height:280px"></div>
      <div class="interp">
        Exception 0 (675 co-occurrences) on Exc-91 invoices means many are also below the low-value threshold — double non-material exceptions.
        Exceptions 151 and 1 appearing on these invoices indicates that GR-delayed invoices also tend to have indexing/data quality issues,
        suggesting the same vendors with poor GR discipline also submit incomplete invoice data.
      </div>
    </div>
  </div>

  <!-- ═══════════════ EXCEPTION 151 ═══════════════ -->
  <div class="section" id="sec-exc151">
    <div class="stat-row">
      <div class="stat-box red"><div class="sv" id="e151-total">–</div><div class="sl">Total Exc 151 Events</div></div>
      <div class="stat-box"><div class="sv" id="e151-inv">–</div><div class="sl">Unique Invoices</div></div>
      <div class="stat-box amber"><div class="sv">86.8%</div><div class="sl">MAIL_IES channel</div></div>
      <div class="stat-box"><div class="sv">100%</div><div class="sl">All ZCP PO type</div></div>
    </div>

    <div class="card">
      <div class="card-title">Exception 151 — Manual Check / Missing Indexing Data: Category Breakdown</div>
      <div class="card-sub">"Indexing" = VIM's OCR/data extraction could not parse mandatory header fields from the invoice image</div>
      <div class="grid2">
        <div id="chart-e151-cat-pie" style="height:300px"></div>
        <div id="chart-e151-ch-cat" style="height:300px"></div>
      </div>
      <div class="interp danger">
        <strong>What is Exception 151?</strong> VIM's intelligent document recognition (IDR/OCR) layer failed to extract one or more mandatory
        indexing fields (e.g., PO number, vendor number, invoice date, line amounts). This forces AP to manually key or correct the data.
        <br/><br/>
        It affects both <strong>Standard (55%) and Service (44%)</strong> invoices almost equally, which rules out category-specific formatting as the root cause.
        The overwhelming concentration in <strong>MAIL_IES (87%)</strong> is the key signal — paper or email invoices scanned through IES have lower OCR accuracy
        than structured COUPA or EDI submissions. <strong>Every Exc 151 event = one manual AP data-entry touch.</strong>
        <br/><br/>
        <strong>Remediation path:</strong> For top vendors (Carmeuse, PPG, Southern Ionics), enforce structured invoice submission via COUPA or EDI.
        For the long tail, improve IES template matching and vendor invoice formatting guidelines.
      </div>
    </div>

    <div class="card">
      <div class="card-title">Exc 151 — Monthly Trend by Category</div>
      <div id="chart-e151-monthly" style="height:300px"></div>
      <div class="interp warn">
        Exception 151 volume has remained <strong>persistently high</strong> with no material improvement since go-live.
        This confirms it is a structural data quality issue (MAIL_IES OCR failure) rather than a teething problem that self-corrects over time.
      </div>
    </div>

    <div class="card">
      <div class="card-title">Exc 151 — Top 20 Vendors by Event Count</div>
      <div id="chart-e151-vendors" style="height:420px"></div>
      <div class="tbl-wrap"><table id="tbl-e151-vendors">
        <thead><tr><th onclick="sortTable(this)">Vendor #</th><th onclick="sortTable(this)">Name</th><th onclick="sortTable(this)">Exc 151 Events</th><th onclick="sortTable(this)">Unique Invoices</th><th onclick="sortTable(this)">Avg Exc/Inv</th></tr></thead>
        <tbody id="tbody-e151-vendors"></tbody>
      </table></div>
    </div>

    <div class="card">
      <div class="card-title">Exc 151 — Co-occurring Exceptions</div>
      <div class="card-sub">Other exceptions on the same invoices that had Exc 151</div>
      <div id="chart-e151-cooccur" style="height:260px"></div>
    </div>
  </div>

  <!-- ═══════════════ EXCEPTION 29 ═══════════════ -->
  <div class="section" id="sec-exc29">
    <div class="stat-row">
      <div class="stat-box red"><div class="sv" id="e29-total">–</div><div class="sl">Total Exc 29 Events</div></div>
      <div class="stat-box"><div class="sv" id="e29-inv">–</div><div class="sl">Unique Invoices</div></div>
      <div class="stat-box amber"><div class="sv">98.7%</div><div class="sl">MAIL_IES channel</div></div>
      <div class="stat-box red"><div class="sv">54.7%</div><div class="sl">Service category (dominant)</div></div>
    </div>

    <div class="card">
      <div class="card-title">Exception 29 — Missing Mandatory Information (PO): Category Breakdown</div>
      <div class="card-sub">Fires when PO header or line mandatory fields (e.g., delivery address, cost centre, order unit) are missing or mismatched</div>
      <div class="grid2">
        <div id="chart-e29-cat-pie" style="height:300px"></div>
        <div id="chart-e29-ch-cat" style="height:300px"></div>
      </div>
      <div class="interp danger">
        <strong>Exception 29 vs Exception 151 — what's the difference?</strong>
        Exception 151 = invoice OCR/parsing failure (AP can't read the data). Exception 29 = invoice data was read, but a mandatory field
        on the <em>PO side</em> is missing or doesn't match the invoice — the PO itself is incomplete or misconfigured in S4.
        <br/><br/>
        The Service-heavy skew (54.7%) is diagnostic: service POs frequently omit mandatory fields like service entry sheet references,
        cost centres, or activity types because service procurement is less standardised than materials procurement.
        <strong>MAIL_IES accounts for 98.7% of Exc 29 events</strong> (only 6 events on COUPA) — structured COUPA submission requires
        these fields up front, naturally filtering them out before invoice submission.
        <br/><br/>
        <strong>Remediation path:</strong> PO data completeness audit for top Exc-29 vendors (Southern Ionics: 367 events, Terra First: 305).
        For service POs, mandate SES creation before approving invoice submission.
      </div>
    </div>

    <div class="card">
      <div class="card-title">Exc 29 — Monthly Trend by Category</div>
      <div id="chart-e29-monthly" style="height:300px"></div>
      <div class="interp warn">
        Service invoices generating Exc 29 are <strong>elevated throughout the entire review period</strong> with a notable spike in May 2025 (go-live month).
        Standard material Exc 29 events have grown over the review period, suggesting PO data quality in S4 for materials is also degrading —
        possibly from master data migration gaps during S4 cutover.
      </div>
    </div>

    <div class="card">
      <div class="card-title">Exc 29 — Top 20 Vendors</div>
      <div id="chart-e29-vendors" style="height:420px"></div>
      <div class="interp">
        <strong>Southern Ionics (367 events) and Terra First (305 events)</strong> together account for 26% of all Exc 29 events.
        Both are high-volume chemical/material suppliers. A targeted PO data quality review with these two vendors alone
        would remove more than a quarter of all Exception 29 occurrences.
      </div>
      <div class="tbl-wrap"><table id="tbl-e29-vendors">
        <thead><tr><th onclick="sortTable(this)">Vendor #</th><th onclick="sortTable(this)">Name</th><th onclick="sortTable(this)">Exc 29 Events</th><th onclick="sortTable(this)">Unique Invoices</th><th onclick="sortTable(this)">Avg Exc/Inv</th></tr></thead>
        <tbody id="tbody-e29-vendors"></tbody>
      </table></div>
    </div>

    <div class="card">
      <div class="card-title">Exc 29 — Co-occurring Exceptions</div>
      <div class="card-sub">Exc 29 commonly cascades into Exc 1 (151 times) and Exc 151 (187 times), confirming multi-exception chains</div>
      <div id="chart-e29-cooccur" style="height:260px"></div>
    </div>
  </div>

  <!-- ═══════════════ COUPA + SERVICE ═══════════════ -->
  <div class="section" id="sec-coupa-svc">
    <div class="stat-row">
      <div class="stat-box green"><div class="sv">83.4%</div><div class="sl">COUPA + Service first-pass rate</div></div>
      <div class="stat-box red"><div class="sv">35.6%</div><div class="sl">COUPA + Standard first-pass rate</div></div>
      <div class="stat-box amber"><div class="sv">530</div><div class="sl">Total COUPA + Service invoices</div></div>
      <div class="stat-box"><div class="sv">675</div><div class="sl">Exception 0 events on "passed" invoices</div></div>
    </div>

    <div class="card">
      <div class="card-title">Why COUPA + Service Exceeds 80% — The Exception 0 Effect</div>
      <div class="card-sub">Breakdown of exceptions on passed vs failed COUPA+Service invoices</div>
      <div class="grid2">
        <div id="chart-cs-pass" style="height:300px"></div>
        <div id="chart-cs-fail" style="height:300px"></div>
      </div>
      <div class="interp ok">
        <strong>The 83.4% first-pass rate for COUPA+Service is real but requires context.</strong><br/><br/>
        The 442 "first-pass" COUPA+Service invoices are counted as passed because they do <em>not appear in the sorted dataset</em>
        (which excludes Exception IDs 0 and 91). However, looking at the full inc dataset, those same invoices generated
        <strong>675 occurrences of Exception 0 ("PO Low-value service invoice")</strong> — a non-material routing step that VIM
        performs automatically without AP intervention.<br/><br/>
        In other words: <strong>COUPA+Service invoices are routing through Exception 0 as a low-value fast-track</strong>.
        These are small-value service orders that skip the normal matching logic and get approved automatically.
        This is working as designed — the low-value threshold is doing its job — but it means the 83.4% rate is partly
        a function of invoice value (small service invoices pass easily) rather than data quality superiority.
        <br/><br/>
        The remaining failed invoices (88) hit <strong>Exception 151 (109 events)</strong> and <strong>Exception 1 (98 events)</strong> —
        the former being genuine indexing failures, the latter being the system artefact.
      </div>
    </div>

    <div class="card">
      <div class="card-title">Why COUPA + Standard Only Achieves 35.6%</div>
      <div class="card-sub">Exception profile of the 629 failed COUPA+Standard invoices</div>
      <div id="chart-cstd-fail" style="height:300px"></div>
      <div class="interp danger">
        <strong>COUPA + Standard fails primarily because of Exception 38 "Freight on Invoice" (411 events)</strong> — this is a
        structural S4 configuration issue, not a vendor data quality problem. When a supplier includes a freight/delivery charge
        on their invoice body, VIM flags it as Exception 38 because the freight line item is not mapped to a corresponding
        PO line in S4.
        <br/><br/>
        <strong>This is a configuration gap introduced during S4 implementation</strong>: Standard material POs in S4 typically do not have
        a freight line, so any invoice containing freight triggers an exception regardless of the accuracy of the rest of the invoice data.
        Fixing this requires either: (a) adding a standard freight line to relevant PO types in S4, or (b) configuring a tolerances rule
        for freight amounts below a threshold.
        <br/><br/>
        Exception 151 (208 events) and Exception 1 (148 events) account for the remaining failures.
      </div>
    </div>

    <div class="card">
      <div class="card-title">COUPA Monthly Performance by Category</div>
      <div class="card-sub">How COUPA's first-pass rate evolves over time, split by material category</div>
      <div id="chart-coupa-monthly" style="height:320px"></div>
      <div class="interp">
        COUPA+Service has maintained consistently high first-pass rates throughout the review period,
        while COUPA+Standard has struggled. This persistence confirms that the COUPA+Standard failure
        is systemic (Exception 38 configuration gap) rather than improving naturally with adoption.
      </div>
    </div>

    <div class="card">
      <div class="card-title">Full Channel × Category First-Pass Matrix</div>
      <div class="card-sub">All combinations — including MAIL_IES and VIM_IES</div>
      <div id="chart-cc-matrix" style="height:300px"></div>
      <div class="tbl-wrap"><table id="tbl-cc-matrix">
        <thead><tr><th onclick="sortTable(this)">Channel</th><th onclick="sortTable(this)">Category</th><th onclick="sortTable(this)">Total Invoices</th><th onclick="sortTable(this)">First-Pass</th><th onclick="sortTable(this)">First-Pass %</th></tr></thead>
        <tbody id="tbody-cc-matrix"></tbody>
      </table></div>
    </div>
  </div>

  <!-- ═══════════════ VENDORS ═══════════════ -->
  <div class="section" id="sec-vendors">
    <div class="card">
      <div class="card-title">Top 30 Vendors by Exception Events (Volume)</div>
      <div class="card-sub">Posted NB/ZCP invoices · transport vendors excluded</div>
      <div id="chart-vendor-vol" style="height:520px"></div>
      <div class="interp">
        The top 10 vendors generate <strong id="top10-pct">–</strong>% of all exception events. Targeted vendor improvement programs for the top 20–30 suppliers
        would reduce total exception volume by ~40%.
      </div>
    </div>
    <div class="card">
      <div class="card-title">Exception Type Breakdown by Supplier (Top 20 by Volume)</div>
      <div class="card-sub">Each bar is a supplier; segments show which exception types make up their workload — hover for counts</div>
      <div id="chart-vendor-breakdown" style="height:580px"></div>
      <div class="interp">
        Suppliers with large <strong>Exc 1 (Process PO Invoice)</strong> segments are primarily affected by the system artefact — their real workload
        may be lower than the bar suggests. Focus remediation effort on suppliers with significant
        <strong>Exc 151 (Missing Indexing)</strong>, <strong>Exc 29 (Missing Info)</strong>, <strong>Exc 75 (Price Discrepancy)</strong>,
        or <strong>Exc 38 (Freight)</strong> segments, as those represent genuine data quality or configuration gaps.
      </div>
    </div>
    <div class="card">
      <div class="card-title">Top 20 Vendors by Exception Intensity (Avg Exceptions/Invoice, min 10 invoices)</div>
      <div id="chart-vendor-int" style="height:400px"></div>
    </div>
    <div class="card">
      <div class="card-title">Top 30 Vendor Detail</div>
      <div class="tbl-wrap"><table id="tbl-vendors">
        <thead><tr><th onclick="sortTable(this)">Vendor #</th><th onclick="sortTable(this)">Name</th><th onclick="sortTable(this)">Invoices</th><th onclick="sortTable(this)">Exception Events</th><th onclick="sortTable(this)">Avg Exc/Inv</th></tr></thead>
        <tbody id="tbody-vendors"></tbody>
      </table></div>
    </div>
  </div>

  <!-- ═══════════════ CATEGORY ═══════════════ -->
  <div class="section" id="sec-category">
    <div class="card">
      <div class="card-title">Exception Volume by Material Category</div>
      <div class="grid2">
        <div id="chart-cat-pie" style="height:320px"></div>
        <div id="chart-cat-bar" style="height:320px"></div>
      </div>
      <div class="interp">
        Standard materials dominate by volume (~60%) but Service invoices (~37%) are disproportionately problematic.
        Service invoices require SES creation before matching — delays in SES drive a cascade of exceptions.
      </div>
    </div>
    <div class="card">
      <div class="card-title">Exception Type by Category (Stacked)</div>
      <div id="chart-cat-exc" style="height:400px"></div>
    </div>
    <div class="card">
      <div class="card-title">Category Exception Detail</div>
      <div class="tbl-wrap"><table id="tbl-cat-exc">
        <thead><tr><th onclick="sortTable(this)">Category</th><th onclick="sortTable(this)">Exc ID</th><th onclick="sortTable(this)">Description</th><th onclick="sortTable(this)">Count</th></tr></thead>
        <tbody id="tbody-cat-exc"></tbody>
      </table></div>
    </div>
  </div>

  <!-- ═══════════════ CHANNEL ═══════════════ -->
  <div class="section" id="sec-channel">
    <div class="card">
      <div class="card-title">First-Pass Rate by Ingestion Channel</div>
      <div id="chart-channel-fp" style="height:320px"></div>
      <div class="interp">
        COUPA achieves ~52% overall but MAIL_IES (86% of volume) sits at 33%. Channel migration alone won't solve the problem
        — COUPA+Standard only reaches 35.6%, worse than MAIL_IES+Service (49.8%).
      </div>
    </div>
    <div class="card">
      <div class="card-title">First-Pass Rate: Channel × Category</div>
      <div id="chart-channel-cat" style="height:320px"></div>
    </div>
    <div class="card">
      <div class="card-title">Channel × Category Detail</div>
      <div class="tbl-wrap"><table id="tbl-channel-cat">
        <thead><tr><th onclick="sortTable(this)">Channel</th><th onclick="sortTable(this)">Category</th><th onclick="sortTable(this)">Total</th><th onclick="sortTable(this)">First-Pass</th><th onclick="sortTable(this)">%</th></tr></thead>
        <tbody id="tbody-channel-cat"></tbody>
      </table></div>
    </div>
  </div>

  <!-- ═══════════════ TRENDS ═══════════════ -->
  <div class="section" id="sec-trends">
    <div class="card">
      <div class="card-title">Monthly Invoice Volume &amp; Exception Events</div>
      <div id="chart-monthly-vol" style="height:300px"></div>
    </div>
    <div class="card">
      <div class="card-title">Monthly First-Pass Rate (%) vs. 80% Target</div>
      <div id="chart-monthly-fp" style="height:300px"></div>
      <div class="interp warn">
        First-pass peaked at ~45% in Aug 2025 then deteriorated to ~30% in Dec 2025. The trend has <strong>not</strong> converged toward 80%.
        Without targeted intervention the situation will not self-correct.
      </div>
    </div>
    <div class="card">
      <div class="card-title">Monthly Detail</div>
      <div class="tbl-wrap"><table id="tbl-monthly">
        <thead><tr><th onclick="sortTable(this)">Month</th><th onclick="sortTable(this)">Total Invoices</th><th onclick="sortTable(this)">Exception Invoices</th><th onclick="sortTable(this)">First-Pass Invoices</th><th onclick="sortTable(this)">First-Pass %</th></tr></thead>
        <tbody id="tbody-monthly"></tbody>
      </table></div>
    </div>
  </div>

  <!-- ═══════════════ COMBOS ═══════════════ -->
  <div class="section" id="sec-combos">
    <div class="card">
      <div class="card-title">Exception Count Distribution per Invoice</div>
      <div id="chart-exc-dist" style="height:300px"></div>
    </div>
    <div class="card">
      <div class="card-title">Top Exception Chains (2-exception pairs)</div>
      <div id="chart-pairs" style="height:320px"></div>
    </div>
    <div class="card">
      <div class="card-title">Top Exception Chains (3-exception triples)</div>
      <div id="chart-triples" style="height:300px"></div>
    </div>
    <div class="card">
      <div class="card-title">Chain Detail Tables</div>
      <div class="grid2">
        <div>
          <div class="section-label">Top Pairs</div>
          <div class="tbl-wrap"><table id="tbl-pairs"><thead><tr><th onclick="sortTable(this)">Pair</th><th onclick="sortTable(this)">Count</th></tr></thead><tbody id="tbody-pairs"></tbody></table></div>
        </div>
        <div>
          <div class="section-label">Top Triples</div>
          <div class="tbl-wrap"><table id="tbl-triples"><thead><tr><th onclick="sortTable(this)">Triple</th><th onclick="sortTable(this)">Count</th></tr></thead><tbody id="tbody-triples"></tbody></table></div>
        </div>
      </div>
    </div>
  </div>

  <!-- ═══════════════ WORKLOAD ═══════════════ -->
  <div class="section" id="sec-workload">
    <div class="card">
      <div class="card-title">AP Workload Concentration — Pareto by Vendor</div>
      <div id="chart-pareto" style="height:420px"></div>
      <div class="interp">
        Top 10 vendors = <strong id="top10-pct2">–</strong>% · Top 20 = <strong id="top20-pct">–</strong>% · Top 50 = <strong id="top50-pct">–</strong>% of exception events.
        A flat Pareto means the problem is broadly distributed — no single vendor fix will be transformative, but a vendor improvement program targeting the top 30 would still deliver the largest near-term gains.
      </div>
    </div>
    <div class="card">
      <div class="card-title">Top 50 Vendors by Workload</div>
      <div class="tbl-wrap"><table id="tbl-workload">
        <thead><tr><th onclick="sortTable(this)">#</th><th onclick="sortTable(this)">Vendor #</th><th onclick="sortTable(this)">Name</th><th onclick="sortTable(this)">Exception Events</th><th onclick="sortTable(this)">Invoices</th><th onclick="sortTable(this)">Cumulative %</th></tr></thead>
        <tbody id="tbody-workload"></tbody>
      </table></div>
    </div>
  </div>

  <!-- ═══════════════ DATA QUALITY ═══════════════ -->
  <div class="section" id="sec-dq">
    <div class="card">
      <div class="card-title">Data Quality &amp; Methodology Notes</div>
      <div style="display:flex;flex-direction:column;gap:14px;font-size:.81rem;line-height:1.7;margin-top:8px">
        <div><strong>1. Transport Vendor Exclusion</strong><br/>Suppliers with IDs starting "52" (DM Trans, Gulf Relay, BNSF Railway, etc.) removed from all analyses. Raw sorted: 15,841 → after exclusion: 13,363 exception events (posted NB/ZCP).</div>
        <div><strong>2. Exception 1 — System Artefact</strong><br/>Exc 1 "Process PO Invoice" = 4,050 events (30.3%). No AP action required — VIM fires it on every PO match step. Suppressing this would materially improve reported metrics without fixing any real problem.</div>
        <div><strong>3. Duplicate Column Names</strong><br/>"Created at" and "Time Stamp" each appear twice. First instance used for date analysis. Verify with SAP/VIM team which represents creation vs posting date.</div>
        <div><strong>4. January 2026 Partial Month</strong><br/>Only 15 invoices in Jan 2026 — data extract cutoff. Excluded from trend charts. Not a trend signal.</div>
        <div><strong>5. First-Pass Rate Methodology</strong><br/>An invoice is "first-pass" if its Document ID is absent from the sorted dataset (which excludes Exc 0 and 91). Invoices with only Exc 0 (low-value fast-track) or Exc 91 (GR timing) count as first-pass. The COUPA+Service 83.4% rate is driven partly by the low-value Exception 0 routing mechanism.</div>
        <div><strong>6. PO Type Scope</strong><br/>NB and ZCP only. Intercompany, transport PO types, and Non-PO (#N/A) excluded. Total analysis universe: 12,859 unique invoices.</div>
        <div><strong>7. Amount Parsing</strong><br/>Gross amounts had embedded commas/quotes. Stripped for numeric analysis. &lt;0.5% rows excluded due to parse errors.</div>
        <div><strong>8. Exception 91 — All ZCP</strong><br/>Exception 91 appears exclusively on ZCP (Work Order) PO type, confirming its root cause is goods-receipt lag on maintenance/WO-backed procurement rather than any vendor or data quality issue.</div>
      </div>
    </div>
  </div>
</main>

<script>
const D = """ + DATA_JS + r""";
const E = """ + EXT_JS + r""";

// ── Navigation ──
document.querySelectorAll('#sidebar nav a').forEach(a=>{
  a.addEventListener('click',e=>{
    e.preventDefault();
    document.querySelectorAll('#sidebar nav a').forEach(x=>x.classList.remove('active'));
    a.classList.add('active');
    document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));
    document.getElementById('sec-'+a.dataset.sec).classList.add('active');
    renderSection(a.dataset.sec);
  });
});

// ── Colour palette ──
const BLUE='#1a3d6b',TEAL='#007a8a',GREEN='#2d8a4e',RED='#e8503a',AMBER='#f0a500',GREY='#6b7a90';
const PAL=[BLUE,TEAL,GREEN,RED,AMBER,'#7b5ea7','#c0392b','#2980b9','#27ae60','#d35400','#8e44ad','#16a085'];

const LY={margin:{l:50,r:20,t:30,b:70},paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',
  font:{family:'Segoe UI,Arial',size:11,color:'#1e2a3a'},
  xaxis:{gridcolor:'#e8edf3'},yaxis:{gridcolor:'#e8edf3'}};

// ── Sort table ──
function sortTable(th){
  const tbl=th.closest('table'),tbody=tbl.querySelector('tbody');
  const col=th.cellIndex,rows=[...tbody.querySelectorAll('tr')];
  const asc=th.dataset.asc!=='1';
  rows.sort((a,b)=>{
    const va=a.cells[col].textContent.trim(),vb=b.cells[col].textContent.trim();
    const na=parseFloat(va.replace(/,/g,'')),nb=parseFloat(vb.replace(/,/g,''));
    if(!isNaN(na)&&!isNaN(nb)) return asc?na-nb:nb-na;
    return asc?va.localeCompare(vb):vb.localeCompare(va);
  });
  rows.forEach(r=>tbody.appendChild(r));
  th.closest('thead').querySelectorAll('th').forEach(x=>x.dataset.asc='');
  th.dataset.asc=asc?'1':'0';
}

function buildTable(id,rows,cols){
  const tb=document.getElementById(id);
  if(!tb) return;
  tb.innerHTML=rows.map(r=>'<tr>'+cols.map(c=>`<td>${r[c]??''}</td>`).join('')+'</tr>').join('');
}

const rendered={};
function renderSection(sec){
  if(rendered[sec]) return;
  rendered[sec]=true;

  const ly=LY;

  // ── OVERVIEW ──
  if(sec==='overview'){
    const kpi=D.kpi;
    document.getElementById('fp-kpi').textContent=kpi.first_pass_rate+'%';
    document.getElementById('inv-kpi').textContent=kpi.total_invoices.toLocaleString();
    document.getElementById('exc-kpi').textContent=kpi.total_exception_events.toLocaleString();
    document.getElementById('vend-kpi').textContent=kpi.unique_vendors_with_exceptions;

    // Channel x Category heatmap using grouped bar
    const cc=E.cc_fp;
    const channels=[...new Set(cc.map(r=>r['Channel ID']))];
    const cats=[...new Set(cc.map(r=>r['PO category decription']))];
    const traces=channels.map((ch,i)=>({
      name:ch,x:cats,
      y:cats.map(cat=>{const r=cc.find(x=>x['Channel ID']===ch&&x['PO category decription']===cat);return r?r.FP_Rate:null;}),
      type:'bar',marker:{color:PAL[i]},
      customdata:cats.map(cat=>{const r=cc.find(x=>x['Channel ID']===ch&&x['PO category decription']===cat);return r?[r.Total,r.FP_Count]:['–','–'];}),
      hovertemplate:`<b>${ch} / %{x}</b><br>FP Rate: %{y}%<br>Total: %{customdata[0]}<br>Passed: %{customdata[1]}<extra></extra>`
    }));
    Plotly.newPlot('chart-cc-heatmap',traces,{...ly,barmode:'group',
      yaxis:{title:'First-Pass Rate (%)',range:[0,100]},
      shapes:[{type:'line',x0:-0.5,x1:cats.length-0.5,y0:80,y1:80,line:{color:GREEN,dash:'dash',width:2}}],
      annotations:[{x:cats.length-0.8,y:83,text:'80% Target',showarrow:false,font:{color:GREEN,size:11}}],
      legend:{x:1,xanchor:'right',y:1}},{responsive:true});

    const ef=D.exc_freq.slice(0,10);
    Plotly.newPlot('chart-overview-exc',[
      {x:ef.map(r=>r.Count),y:ef.map(r=>`ID ${r['Exception ID']}: ${r['Exception description'].substring(0,42)}`),
       type:'bar',orientation:'h',marker:{color:ef.map((_,i)=>PAL[i])},
       text:ef.map(r=>r.Pct+'%'),textposition:'outside',
       hovertemplate:'<b>%{y}</b><br>Count: %{x}<extra></extra>'}
    ],{...ly,margin:{l:300,r:60,t:20,b:40},xaxis:{title:'Exception Events'},yaxis:{autorange:'reversed'}},{responsive:true});
  }

  // ── EXCEPTION FREQUENCY ──
  if(sec==='exc-freq'){
    const ef=D.exc_freq;
    Plotly.newPlot('chart-exc-bar',[
      {x:ef.map(r=>`ID ${r['Exception ID']}`),y:ef.map(r=>r.Count),type:'bar',
       marker:{color:ef.map(r=>r['Exception ID']===1?RED:BLUE)},
       text:ef.map(r=>r.Pct+'%'),textposition:'outside',
       customdata:ef.map(r=>r['Exception description']),
       hovertemplate:'<b>%{customdata}</b><br>Count: %{y}<br>Share: %{text}<extra></extra>'}
    ],{...ly,xaxis:{title:'Exception ID'},yaxis:{title:'Exception Events'},margin:{...ly.margin,b:60}},{responsive:true});
    buildTable('tbody-exc-freq',ef,['Exception ID','Exception description','Count','Pct']);
  }

  // ── EXCEPTION 91 ──
  if(sec==='exc91'){
    document.getElementById('e91-total').textContent=E.e91_total.toLocaleString();
    document.getElementById('e91-inv').textContent=E.e91_unique_inv.toLocaleString();

    const cats=E.e91_cat;
    Plotly.newPlot('chart-e91-cat-pie',[
      {labels:cats.map(r=>r['PO category decription']),values:cats.map(r=>r.Events),
       type:'pie',hole:.4,marker:{colors:[BLUE,TEAL,AMBER,GREEN]},
       textinfo:'label+percent',hovertemplate:'<b>%{label}</b><br>%{value} events<extra></extra>'}
    ],{...ly,margin:{l:10,r:10,t:30,b:10},showlegend:false},{responsive:true});

    Plotly.newPlot('chart-e91-cat-bar',[
      {x:cats.map(r=>r['PO category decription']),y:cats.map(r=>r.Events),type:'bar',
       marker:{color:[BLUE,TEAL,AMBER,GREEN]},
       text:cats.map(r=>r.Pct+'%'),textposition:'outside',
       customdata:cats.map(r=>r.Unique_Inv),
       hovertemplate:'<b>%{x}</b><br>Events: %{y} (%{text})<br>Unique invoices: %{customdata}<extra></extra>'}
    ],{...ly,yaxis:{title:'Exception Events'},margin:{l:50,r:20,t:30,b:60}},{responsive:true});

    const m91=E.e91_monthly;
    const months91=[...new Set(m91.map(r=>r.Month))].sort();
    const cats91=[...new Set(m91.map(r=>r['PO category decription']))];
    const t91=cats91.map((cat,i)=>({
      name:cat,x:months91,type:'bar',marker:{color:PAL[i]},
      y:months91.map(mo=>{const r=m91.find(x=>x.Month===mo&&x['PO category decription']===cat);return r?r.Events:0;}),
      hovertemplate:`<b>${cat}</b><br>%{x}: %{y}<extra></extra>`
    }));
    Plotly.newPlot('chart-e91-monthly',t91,{...ly,barmode:'stack',yaxis:{title:'Exception Events'},xaxis:{title:'Month'},legend:{x:1,xanchor:'right',y:1}},{responsive:true});

    const ch91=E.e91_ch_cat;
    const chans91=[...new Set(ch91.map(r=>r['Channel ID']))];
    const ccat91=[...new Set(ch91.map(r=>r['PO category decription']))];
    const tch91=chans91.map((ch,i)=>({
      name:ch,x:ccat91,type:'bar',marker:{color:PAL[i]},
      y:ccat91.map(cat=>{const r=ch91.find(x=>x['Channel ID']===ch&&x['PO category decription']===cat);return r?r.Events:0;}),
      customdata:ccat91.map(cat=>{const r=ch91.find(x=>x['Channel ID']===ch&&x['PO category decription']===cat);return r?r.Unique_Inv:0;}),
      hovertemplate:`<b>${ch} / %{x}</b><br>Events: %{y}<br>Invoices: %{customdata}<extra></extra>`
    }));
    Plotly.newPlot('chart-e91-ch-cat',tch91,{...ly,barmode:'group',yaxis:{title:'Exception Events'},legend:{x:1,xanchor:'right',y:1}},{responsive:true});

    const v91=E.e91_vendors;
    Plotly.newPlot('chart-e91-vendors',[
      {x:v91.map(r=>r.Events),y:v91.map(r=>r['Name 1'].length>36?r['Name 1'].substring(0,36)+'…':r['Name 1']),
       type:'bar',orientation:'h',marker:{color:BLUE},
       customdata:v91.map(r=>r.Unique_Inv),
       hovertemplate:'<b>%{y}</b><br>Events: %{x}<br>Invoices: %{customdata}<extra></extra>'}
    ],{...ly,margin:{l:260,r:60,t:20,b:50},xaxis:{title:'Exception Events'},yaxis:{autorange:'reversed'}},{responsive:true});
    buildTable('tbody-e91-vendors',v91,['Supplier','Name 1','Events','Unique_Inv']);

    const cc91=E.e91_cooccur;
    Plotly.newPlot('chart-e91-cooccur',[
      {x:cc91.map(r=>r.Count),y:cc91.map(r=>`ID ${r['Exception ID']}: ${r['Exception description'].substring(0,40)}`),
       type:'bar',orientation:'h',marker:{color:TEAL},
       text:cc91.map(r=>r.Count),textposition:'outside',
       hovertemplate:'<b>%{y}</b><br>Co-occurrences: %{x}<extra></extra>'}
    ],{...ly,margin:{l:280,r:60,t:20,b:50},xaxis:{title:'Co-occurrence Count'},yaxis:{autorange:'reversed'}},{responsive:true});
  }

  // ── EXCEPTION 151 ──
  if(sec==='exc151'){
    document.getElementById('e151-total').textContent=E.e151_total.toLocaleString();
    document.getElementById('e151-inv').textContent=E.e151_unique_inv.toLocaleString();

    const c151=E.e151_cat;
    Plotly.newPlot('chart-e151-cat-pie',[
      {labels:c151.map(r=>r['PO category decription']),values:c151.map(r=>r.Events),
       type:'pie',hole:.4,marker:{colors:[BLUE,TEAL,AMBER,GREEN]},
       textinfo:'label+percent',hovertemplate:'<b>%{label}</b><br>%{value} events<extra></extra>'}
    ],{...ly,margin:{l:10,r:10,t:30,b:10},showlegend:false},{responsive:true});

    const ch151=E.e151_ch_cat;
    const chans151=[...new Set(ch151.map(r=>r['Channel ID']))];
    const ccat151=[...new Set(ch151.map(r=>r['PO category decription']))];
    const tch151=chans151.map((ch,i)=>({
      name:ch,x:ccat151,type:'bar',marker:{color:PAL[i]},
      y:ccat151.map(cat=>{const r=ch151.find(x=>x['Channel ID']===ch&&x['PO category decription']===cat);return r?r.Events:0;}),
      customdata:ccat151.map(cat=>{const r=ch151.find(x=>x['Channel ID']===ch&&x['PO category decription']===cat);return r?r.Unique_Inv:0;}),
      hovertemplate:`<b>${ch} / %{x}</b><br>Events: %{y}<br>Invoices: %{customdata}<extra></extra>`
    }));
    Plotly.newPlot('chart-e151-ch-cat',tch151,{...ly,barmode:'group',yaxis:{title:'Exception Events'},legend:{x:1,xanchor:'right',y:1}},{responsive:true});

    const m151=E.e151_monthly;
    const months151=[...new Set(m151.map(r=>r.Month))].sort();
    const cats151=[...new Set(m151.map(r=>r['PO category decription']))];
    const tm151=cats151.map((cat,i)=>({
      name:cat,x:months151,type:'bar',marker:{color:PAL[i]},
      y:months151.map(mo=>{const r=m151.find(x=>x.Month===mo&&x['PO category decription']===cat);return r?r.Events:0;}),
      hovertemplate:`<b>${cat}</b><br>%{x}: %{y}<extra></extra>`
    }));
    Plotly.newPlot('chart-e151-monthly',tm151,{...ly,barmode:'stack',yaxis:{title:'Exception Events'},xaxis:{title:'Month'},legend:{x:1,xanchor:'right',y:1}},{responsive:true});

    const v151=E.e151_vendors;
    Plotly.newPlot('chart-e151-vendors',[
      {x:v151.map(r=>r.Events),y:v151.map(r=>r['Name 1'].length>36?r['Name 1'].substring(0,36)+'…':r['Name 1']),
       type:'bar',orientation:'h',marker:{color:RED},
       customdata:v151.map(r=>[r.Unique_Inv,r.Avg_Exc_Per_Inv]),
       hovertemplate:'<b>%{y}</b><br>Events: %{x}<br>Invoices: %{customdata[0]}<br>Avg exc/inv: %{customdata[1]}<extra></extra>'}
    ],{...ly,margin:{l:260,r:60,t:20,b:50},xaxis:{title:'Exception Events'},yaxis:{autorange:'reversed'}},{responsive:true});
    buildTable('tbody-e151-vendors',v151,['Supplier','Name 1','Events','Unique_Inv','Avg_Exc_Per_Inv']);

    const cc151=E.e151_cooccur;
    Plotly.newPlot('chart-e151-cooccur',[
      {x:cc151.map(r=>r.Count),y:cc151.map(r=>`ID ${r['Exception ID']}: ${r['Exception description'].substring(0,40)}`),
       type:'bar',orientation:'h',marker:{color:AMBER},
       text:cc151.map(r=>r.Count),textposition:'outside',
       hovertemplate:'<b>%{y}</b><br>Co-occurrences: %{x}<extra></extra>'}
    ],{...ly,margin:{l:280,r:60,t:20,b:50},xaxis:{title:'Count'},yaxis:{autorange:'reversed'}},{responsive:true});
  }

  // ── EXCEPTION 29 ──
  if(sec==='exc29'){
    document.getElementById('e29-total').textContent=E.e29_total.toLocaleString();
    document.getElementById('e29-inv').textContent=E.e29_unique_inv.toLocaleString();

    const c29=E.e29_cat;
    Plotly.newPlot('chart-e29-cat-pie',[
      {labels:c29.map(r=>r['PO category decription']),values:c29.map(r=>r.Events),
       type:'pie',hole:.4,marker:{colors:[TEAL,BLUE,AMBER,GREEN]},
       textinfo:'label+percent',hovertemplate:'<b>%{label}</b><br>%{value} events<extra></extra>'}
    ],{...ly,margin:{l:10,r:10,t:30,b:10},showlegend:false},{responsive:true});

    const ch29=E.e29_ch_cat;
    const chans29=[...new Set(ch29.map(r=>r['Channel ID']))];
    const ccat29=[...new Set(ch29.map(r=>r['PO category decription']))];
    const tch29=chans29.map((ch,i)=>({
      name:ch,x:ccat29,type:'bar',marker:{color:PAL[i]},
      y:ccat29.map(cat=>{const r=ch29.find(x=>x['Channel ID']===ch&&x['PO category decription']===cat);return r?r.Events:0;}),
      hovertemplate:`<b>${ch} / %{x}</b><br>Events: %{y}<extra></extra>`
    }));
    Plotly.newPlot('chart-e29-ch-cat',tch29,{...ly,barmode:'group',yaxis:{title:'Exception Events'},legend:{x:1,xanchor:'right',y:1}},{responsive:true});

    const m29=E.e29_monthly;
    const months29=[...new Set(m29.map(r=>r.Month))].sort();
    const cats29=[...new Set(m29.map(r=>r['PO category decription']))];
    const tm29=cats29.map((cat,i)=>({
      name:cat,x:months29,type:'bar',marker:{color:PAL[i]},
      y:months29.map(mo=>{const r=m29.find(x=>x.Month===mo&&x['PO category decription']===cat);return r?r.Events:0;}),
      hovertemplate:`<b>${cat}</b><br>%{x}: %{y}<extra></extra>`
    }));
    Plotly.newPlot('chart-e29-monthly',tm29,{...ly,barmode:'stack',yaxis:{title:'Exception Events'},xaxis:{title:'Month'},legend:{x:1,xanchor:'right',y:1}},{responsive:true});

    const v29=E.e29_vendors;
    Plotly.newPlot('chart-e29-vendors',[
      {x:v29.map(r=>r.Events),y:v29.map(r=>r['Name 1'].length>36?r['Name 1'].substring(0,36)+'…':r['Name 1']),
       type:'bar',orientation:'h',marker:{color:TEAL},
       customdata:v29.map(r=>[r.Unique_Inv,r.Avg_Exc_Per_Inv]),
       hovertemplate:'<b>%{y}</b><br>Events: %{x}<br>Invoices: %{customdata[0]}<br>Avg exc/inv: %{customdata[1]}<extra></extra>'}
    ],{...ly,margin:{l:260,r:60,t:20,b:50},xaxis:{title:'Exception Events'},yaxis:{autorange:'reversed'}},{responsive:true});
    buildTable('tbody-e29-vendors',v29,['Supplier','Name 1','Events','Unique_Inv','Avg_Exc_Per_Inv']);

    const cc29=E.e29_cooccur;
    Plotly.newPlot('chart-e29-cooccur',[
      {x:cc29.map(r=>r.Count),y:cc29.map(r=>`ID ${r['Exception ID']}: ${r['Exception description'].substring(0,40)}`),
       type:'bar',orientation:'h',marker:{color:TEAL},
       text:cc29.map(r=>r.Count),textposition:'outside',
       hovertemplate:'<b>%{y}</b><br>Co-occurrences: %{x}<extra></extra>'}
    ],{...ly,margin:{l:280,r:60,t:20,b:50},xaxis:{title:'Count'},yaxis:{autorange:'reversed'}},{responsive:true});
  }

  // ── COUPA + SERVICE ──
  if(sec==='coupa-svc'){
    const passExc=E.coupa_svc_pass_exc;
    const failExc=E.coupa_svc_fail_exc;
    const stdFail=E.coupa_std_fail_exc;

    Plotly.newPlot('chart-cs-pass',[
      {labels:passExc.map(r=>`ID ${r['Exception ID']}: ${r['Exception description']}`),
       values:passExc.map(r=>r.Count),type:'pie',hole:.35,
       marker:{colors:[GREEN,TEAL,BLUE,AMBER]},
       textinfo:'label+percent',
       hovertemplate:'<b>%{label}</b><br>%{value} events<extra></extra>',
       title:{text:'Exceptions on PASSED invoices<br>(from full inc dataset)',font:{size:12}}}
    ],{...ly,margin:{l:10,r:10,t:60,b:10},showlegend:false},{responsive:true});

    Plotly.newPlot('chart-cs-fail',[
      {labels:failExc.map(r=>`ID ${r['Exception ID']}: ${r['Exception description']}`),
       values:failExc.map(r=>r.Count),type:'pie',hole:.35,
       marker:{colors:[RED,AMBER,BLUE,TEAL,GREEN]},
       textinfo:'label+percent',
       hovertemplate:'<b>%{label}</b><br>%{value} events<extra></extra>',
       title:{text:'Exceptions on FAILED invoices<br>(16.6% of COUPA+Service)',font:{size:12}}}
    ],{...ly,margin:{l:10,r:10,t:60,b:10},showlegend:false},{responsive:true});

    Plotly.newPlot('chart-cstd-fail',[
      {x:stdFail.map(r=>r.Count),y:stdFail.map(r=>`ID ${r['Exception ID']}: ${r['Exception description'].substring(0,45)}`),
       type:'bar',orientation:'h',marker:{color:stdFail.map(r=>r['Exception ID']===38?RED:BLUE)},
       text:stdFail.map(r=>r.Count),textposition:'outside',
       hovertemplate:'<b>%{y}</b><br>Count: %{x}<extra></extra>'}
    ],{...ly,margin:{l:310,r:60,t:20,b:50},xaxis:{title:'Exception Events'},yaxis:{autorange:'reversed'}},{responsive:true});

    const cm=E.coupa_monthly.filter(r=>r.Month&&r.Month!=='2026-01');
    const ccats=[...new Set(cm.map(r=>r['PO category decription']))];
    const months=[...new Set(cm.map(r=>r.Month))].sort();
    const tcm=ccats.map((cat,i)=>({
      name:cat,x:months,type:'scatter',mode:'lines+markers',marker:{size:7},line:{width:2.5,color:PAL[i]},
      y:months.map(mo=>{const r=cm.find(x=>x.Month===mo&&x['PO category decription']===cat);return r?r.FP_Rate:null;}),
      hovertemplate:`<b>${cat}</b><br>%{x}: %{y}%<extra></extra>`
    }));
    tcm.push({x:months,y:months.map(()=>80),name:'80% Target',type:'scatter',mode:'lines',
      line:{color:GREEN,dash:'dash',width:2},showlegend:true});
    Plotly.newPlot('chart-coupa-monthly',tcm,{...ly,yaxis:{title:'First-Pass Rate (%)',range:[0,100]},xaxis:{title:'Month'},legend:{x:1,xanchor:'right',y:1}},{responsive:true});

    const cc=E.cc_fp;
    const chans=[...new Set(cc.map(r=>r['Channel ID']))];
    const cats=[...new Set(cc.map(r=>r['PO category decription']))];
    const tcc=chans.map((ch,i)=>({
      name:ch,x:cats,type:'bar',marker:{color:PAL[i]},
      y:cats.map(cat=>{const r=cc.find(x=>x['Channel ID']===ch&&x['PO category decription']===cat);return r?r.FP_Rate:null;}),
      customdata:cats.map(cat=>{const r=cc.find(x=>x['Channel ID']===ch&&x['PO category decription']===cat);return r?[r.Total,r.FP_Count]:['–','–'];}),
      hovertemplate:`<b>${ch} / %{x}</b><br>FP Rate: %{y}%<br>Total: %{customdata[0]}<br>Passed: %{customdata[1]}<extra></extra>`
    }));
    tcc.push({x:cats,y:cats.map(()=>80),name:'80% Target',type:'scatter',mode:'lines',line:{color:GREEN,dash:'dash',width:2}});
    Plotly.newPlot('chart-cc-matrix',tcc,{...ly,barmode:'group',
      yaxis:{title:'First-Pass Rate (%)'},shapes:[],legend:{x:1,xanchor:'right',y:1}},{responsive:true});
    buildTable('tbody-cc-matrix',cc,['Channel ID','PO category decription','Total','FP_Count','FP_Rate']);
  }

  // ── VENDORS ──
  if(sec==='vendors'){
    document.getElementById('top10-pct').textContent=D.kpi.top10_vendor_pct;
    const vt=D.vendor_top30;
    Plotly.newPlot('chart-vendor-vol',[
      {x:vt.map(r=>r.Exception_Events),y:vt.map(r=>r['Name 1'].length>35?r['Name 1'].substring(0,35)+'…':r['Name 1']),
       type:'bar',orientation:'h',marker:{color:BLUE},
       customdata:vt.map(r=>[r.Unique_Invoices,r.Avg_Exc_Per_Inv]),
       hovertemplate:'<b>%{y}</b><br>Events: %{x}<br>Invoices: %{customdata[0]}<br>Avg: %{customdata[1]}<extra></extra>'}
    ],{...ly,margin:{l:260,r:60,t:20,b:50},xaxis:{title:'Exception Events'},yaxis:{autorange:'reversed'}},{responsive:true});
    const vi=D.vendor_intensity;
    Plotly.newPlot('chart-vendor-int',[
      {x:vi.map(r=>r.Avg_Exc_Per_Inv),y:vi.map(r=>r['Name 1'].length>35?r['Name 1'].substring(0,35)+'…':r['Name 1']),
       type:'bar',orientation:'h',marker:{color:vi.map(r=>r.Avg_Exc_Per_Inv>=3?RED:r.Avg_Exc_Per_Inv>=2?AMBER:TEAL)},
       customdata:vi.map(r=>[r.Unique_Invoices,r.Exception_Events]),
       hovertemplate:'<b>%{y}</b><br>Avg exc/inv: %{x}<br>Invoices: %{customdata[0]}<br>Total events: %{customdata[1]}<extra></extra>'}
    ],{...ly,margin:{l:260,r:60,t:20,b:50},xaxis:{title:'Avg Exceptions per Invoice'},yaxis:{autorange:'reversed'}},{responsive:true});
    buildTable('tbody-vendors',vt,['Supplier','Name 1','Unique_Invoices','Exception_Events','Avg_Exc_Per_Inv']);

    // ── Stacked exception breakdown per supplier ──
    const ved=E.vendor_exc_detail;
    const top20=vt.slice(0,20);
    const top20Sups=top20.map(r=>r.Supplier);
    const vbNames=top20.map(r=>r['Name 1'].length>35?r['Name 1'].substring(0,35)+'…':r['Name 1']);
    // Rank exception IDs by total count across these vendors
    const excTot={};
    ved.forEach(r=>{excTot[r['Exception ID']]=(excTot[r['Exception ID']]||0)+r.Count;});
    const topEids=Object.entries(excTot).sort((a,b)=>b[1]-a[1]).slice(0,10).map(([id])=>+id);
    const excDesc={};
    ved.forEach(r=>{excDesc[r['Exception ID']]=r['Exception description'].substring(0,35);});
    const vbTraces=topEids.map((eid,i)=>({
      name:`${eid} – ${excDesc[eid]||''}`,
      x:top20Sups.map(sup=>{const row=ved.find(r=>r.Supplier===sup&&r['Exception ID']===eid);return row?row.Count:0;}),
      y:vbNames,type:'bar',orientation:'h',marker:{color:PAL[i%PAL.length]},
      hovertemplate:`<b>%{y}</b><br>Exc ${eid}: %{x}<extra></extra>`
    }));
    Plotly.newPlot('chart-vendor-breakdown',vbTraces,{...ly,barmode:'stack',
      margin:{l:260,r:60,t:20,b:120},
      xaxis:{title:'Exception Events'},yaxis:{autorange:'reversed'},
      legend:{orientation:'h',x:0,y:-0.22,font:{size:10}}},{responsive:true});
  }

  // ── CATEGORY ──
  if(sec==='category'){
    const cs=D.cat_summary;
    Plotly.newPlot('chart-cat-pie',[
      {labels:cs.map(r=>r['PO category decription']),values:cs.map(r=>r.Exception_Events),
       type:'pie',hole:.4,marker:{colors:[BLUE,TEAL,AMBER,GREEN]},
       textinfo:'label+percent',hovertemplate:'<b>%{label}</b><br>%{value}<extra></extra>'}
    ],{...ly,margin:{l:10,r:10,t:30,b:10},showlegend:false},{responsive:true});
    Plotly.newPlot('chart-cat-bar',[
      {x:cs.map(r=>r['PO category decription']),y:cs.map(r=>r.Exception_Events),type:'bar',
       marker:{color:[BLUE,TEAL,AMBER,GREEN]},text:cs.map(r=>r.Exception_Events.toLocaleString()),textposition:'outside',
       hovertemplate:'<b>%{x}</b><br>Events: %{y}<extra></extra>'}
    ],{...ly,margin:{l:50,r:20,t:30,b:60},yaxis:{title:'Exception Events'}},{responsive:true});
    const ce=D.cat_exc;
    const cats=[...new Set(ce.map(r=>r['PO category decription']))];
    const excIds=[...new Set(ce.map(r=>r['Exception ID']))].slice(0,10);
    const traces=excIds.map((eid,i)=>({
      name:`ID ${eid}`,x:cats,
      y:cats.map(cat=>{const row=ce.find(r=>r['PO category decription']===cat&&r['Exception ID']===eid);return row?row.Count:0;}),
      type:'bar',marker:{color:PAL[i%PAL.length]},
      hovertemplate:`<b>ID ${eid}</b><br>%{x}: %{y}<extra></extra>`
    }));
    Plotly.newPlot('chart-cat-exc',traces,{...ly,barmode:'stack',yaxis:{title:'Exception Events'},legend:{x:1,xanchor:'right',y:1}},{responsive:true});
    buildTable('tbody-cat-exc',ce,['PO category decription','Exception ID','Exception description','Count']);
  }

  // ── CHANNEL ──
  if(sec==='channel'){
    const cf=D.channel_fp;
    Plotly.newPlot('chart-channel-fp',[
      {x:cf.map(r=>r['Channel ID']),y:cf.map(r=>r.Total),name:'Total Invoices',type:'bar',marker:{color:BLUE},
       hovertemplate:'<b>%{x}</b><br>Total: %{y}<extra></extra>'},
      {x:cf.map(r=>r['Channel ID']),y:cf.map(r=>r.First_Pass_Count),name:'First-Pass',type:'bar',marker:{color:GREEN},
       hovertemplate:'<b>%{x}</b><br>First-pass: %{y}<extra></extra>'},
      {x:cf.map(r=>r['Channel ID']),y:cf.map(r=>r.First_Pass_Rate),name:'Rate %',type:'scatter',mode:'lines+markers+text',yaxis:'y2',
       line:{color:AMBER,width:3},marker:{size:10},text:cf.map(r=>r.First_Pass_Rate+'%'),textposition:'top center'},
      {x:cf.map(r=>r['Channel ID']),y:[80,80,80],name:'80% Target',type:'scatter',mode:'lines',yaxis:'y2',line:{color:GREEN,dash:'dash',width:2}}
    ],{...ly,barmode:'overlay',yaxis:{title:'Invoice Count'},yaxis2:{title:'FP Rate (%)',overlaying:'y',side:'right',range:[0,100]},legend:{x:1.05,y:1},margin:{l:60,r:80,t:30,b:60}},{responsive:true});
    const cc=D.channel_cat_fp;
    const channels=[...new Set(cc.map(r=>r['Channel ID']))];
    const catsCh=[...new Set(cc.map(r=>r['PO category decription']))];
    const tch=channels.map((ch,i)=>({
      name:ch,x:catsCh,type:'bar',marker:{color:PAL[i]},
      y:catsCh.map(cat=>{const r=cc.find(x=>x['Channel ID']===ch&&x['PO category decription']===cat);return r?r.First_Pass_Rate:null;}),
      hovertemplate:`<b>${ch}</b><br>%{x}: %{y}%<extra></extra>`
    }));
    Plotly.newPlot('chart-channel-cat',tch,{...ly,barmode:'group',yaxis:{title:'First-Pass Rate (%)'},
      shapes:[{type:'line',x0:-0.5,x1:catsCh.length-0.5,y0:80,y1:80,line:{color:GREEN,dash:'dash',width:2}}],
      legend:{x:1,xanchor:'right',y:1}},{responsive:true});
    buildTable('tbody-channel-cat',cc,['Channel ID','PO category decription','Total','First_Pass_Count','First_Pass_Rate']);
  }

  // ── TRENDS ──
  if(sec==='trends'){
    const mn=D.monthly.filter(r=>r.Month_str!=='2026-01');
    Plotly.newPlot('chart-monthly-vol',[
      {x:mn.map(r=>r.Month_str),y:mn.map(r=>r.Total_Invoices),name:'Total',type:'bar',marker:{color:BLUE}},
      {x:mn.map(r=>r.Month_str),y:mn.map(r=>r.Exc_Invoices),name:'Exception Invoices',type:'bar',marker:{color:RED}}
    ],{...ly,barmode:'overlay',yaxis:{title:'Invoice Count'},legend:{x:1,xanchor:'right',y:1}},{responsive:true});
    Plotly.newPlot('chart-monthly-fp',[
      {x:mn.map(r=>r.Month_str),y:mn.map(r=>r.First_Pass_Rate),type:'scatter',mode:'lines+markers',
       name:'First-Pass %',line:{color:TEAL,width:3},marker:{size:8},
       text:mn.map(r=>r.First_Pass_Rate+'%'),textposition:'top center'},
      {x:mn.map(r=>r.Month_str),y:mn.map(()=>80),name:'80% Target',type:'scatter',mode:'lines',line:{color:GREEN,dash:'dash',width:2}}
    ],{...ly,yaxis:{title:'First-Pass Rate (%)',range:[0,100]},legend:{x:1,xanchor:'right',y:1}},{responsive:true});
    buildTable('tbody-monthly',D.monthly,['Month_str','Total_Invoices','Exc_Invoices','First_Pass_Rate']);
  }

  // ── COMBOS ──
  if(sec==='combos'){
    const ed=D.exc_dist;
    Plotly.newPlot('chart-exc-dist',[
      {x:ed.map(r=>r.N_Exceptions.toString()),y:ed.map(r=>r.Invoice_Count),type:'bar',
       marker:{color:PAL},text:ed.map(r=>r.Invoice_Count.toLocaleString()),textposition:'outside',
       hovertemplate:'<b>%{x} exception(s)</b><br>Invoices: %{y}<extra></extra>'}
    ],{...ly,xaxis:{title:'Exceptions per Invoice'},yaxis:{title:'Invoice Count'}},{responsive:true});
    const ep=D.exc_pairs;
    Plotly.newPlot('chart-pairs',[
      {x:ep.map(r=>r.Count),y:ep.map(r=>r.Pair),type:'bar',orientation:'h',marker:{color:TEAL},
       text:ep.map(r=>r.Count),textposition:'outside'}
    ],{...ly,margin:{l:100,r:60,t:20,b:50},xaxis:{title:'Occurrences'},yaxis:{autorange:'reversed'}},{responsive:true});
    const et=D.exc_triples;
    Plotly.newPlot('chart-triples',[
      {x:et.map(r=>r.Count),y:et.map(r=>r.Triple),type:'bar',orientation:'h',marker:{color:AMBER},
       text:et.map(r=>r.Count),textposition:'outside'}
    ],{...ly,margin:{l:140,r:60,t:20,b:50},xaxis:{title:'Occurrences'},yaxis:{autorange:'reversed'}},{responsive:true});
    buildTable('tbody-pairs',ep,['Pair','Count']);
    buildTable('tbody-triples',et,['Triple','Count']);
  }

  // ── WORKLOAD ──
  if(sec==='workload'){
    const wc=D.workload_conc;
    const top10pct=wc[9]?.Cumulative_Pct??'–';
    const top20pct=wc[19]?.Cumulative_Pct??'–';
    const top50pct=wc[49]?.Cumulative_Pct??'–';
    if(document.getElementById('top10-pct2')) document.getElementById('top10-pct2').textContent=top10pct;
    if(document.getElementById('top20-pct')) document.getElementById('top20-pct').textContent=top20pct;
    if(document.getElementById('top50-pct')) document.getElementById('top50-pct').textContent=top50pct;
    Plotly.newPlot('chart-pareto',[
      {x:wc.map((_,i)=>i+1),y:wc.map(r=>r.Exception_Events),name:'Events',type:'bar',marker:{color:BLUE},
       hovertemplate:'Rank %{x} – %{customdata}<br>Events: %{y}<extra></extra>',customdata:wc.map(r=>r['Name 1'])},
      {x:wc.map((_,i)=>i+1),y:wc.map(r=>r.Cumulative_Pct),name:'Cumulative %',type:'scatter',mode:'lines',yaxis:'y2',line:{color:RED,width:3}},
      {x:[1,50],y:[80,80],name:'80% line',type:'scatter',mode:'lines',yaxis:'y2',line:{color:AMBER,dash:'dot',width:2}}
    ],{...ly,barmode:'overlay',yaxis:{title:'Exception Events'},yaxis2:{title:'Cumulative %',overlaying:'y',side:'right',range:[0,100]},xaxis:{title:'Vendor Rank'},legend:{x:1.05,y:1},margin:{l:60,r:80,t:30,b:60}},{responsive:true});
    buildTable('tbody-workload',wc.map((r,i)=>({...r,rank:i+1})),['rank','Supplier','Name 1','Exception_Events','Unique_Invoices','Cumulative_Pct']);
  }
}

renderSection('overview');
</script>
</body>
</html>
"""

HTML = HTML.replace("__BUILD_ID__", BUILD_ID)

for _name in ("index.html", "dashboard.html"):
    with open(f"{OUT_DIR}/{_name}", "w", encoding="utf-8") as f:
        f.write(HTML)

# If GitHub Pages uses "Deploy from a branch" with path "/" (legacy), the site serves
# this repo-root file — keep it identical to output/index.html.
root_index = os.path.join(SCRIPT_DIR, "index.html")
with open(root_index, "w", encoding="utf-8") as f:
    f.write(HTML)

sz = os.path.getsize(f"{OUT_DIR}/index.html")
print(f"Dashboard v2 saved — {sz/1024:.0f} KB (output/ + repo index.html)")
