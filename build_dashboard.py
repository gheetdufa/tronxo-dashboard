"""
Build the self-contained HTML dashboard for Tronox 1100 AP Invoice Exception Analysis.
"""
import json, os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "output")

with open(f"{OUT_DIR}/dashboard_data.json") as f:
    D = json.load(f)

# Escape for inline JS
DATA_JS = json.dumps(D, default=str)

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
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
  --sidebar-w:230px;
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
#sidebar .logo{
  padding:22px 18px 14px;
  border-bottom:1px solid rgba(255,255,255,.15);
}
#sidebar .logo .brand{font-size:1.25rem;font-weight:700;letter-spacing:.5px}
#sidebar .logo .sub{font-size:.7rem;opacity:.7;margin-top:3px}
#sidebar nav{flex:1;padding:12px 0}
#sidebar nav a{
  display:block;padding:9px 18px;color:rgba(255,255,255,.82);
  text-decoration:none;font-size:.82rem;border-left:3px solid transparent;
  transition:all .18s;
}
#sidebar nav a:hover,#sidebar nav a.active{
  color:#fff;background:rgba(255,255,255,.1);border-left-color:var(--tronox-teal);
}
#sidebar .footer-note{padding:12px 18px;font-size:.68rem;opacity:.5;border-top:1px solid rgba(255,255,255,.1)}

/* ── Main ── */
#main{margin-left:var(--sidebar-w);flex:1;padding:28px 32px;min-width:0}

h1.page-title{font-size:1.5rem;color:var(--tronox-blue);margin-bottom:4px}
.page-sub{font-size:.85rem;color:var(--muted);margin-bottom:24px}

/* ── Sections ── */
.section{display:none;animation:fadeIn .25s}
.section.active{display:block}
@keyframes fadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}

/* ── KPI Cards ── */
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(175px,1fr));gap:14px;margin-bottom:28px}
.kpi-card{
  background:var(--card);border-radius:10px;padding:18px 16px;
  border:1px solid var(--border);
  display:flex;flex-direction:column;gap:6px;
}
.kpi-label{font-size:.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}
.kpi-value{font-size:1.9rem;font-weight:700;color:var(--tronox-blue)}
.kpi-value.danger{color:var(--accent)}
.kpi-value.ok{color:var(--tronox-green)}
.kpi-note{font-size:.7rem;color:var(--muted)}

/* ── Cards ── */
.card{
  background:var(--card);border-radius:10px;padding:20px 22px;
  border:1px solid var(--border);margin-bottom:22px;
}
.card-title{font-size:1rem;font-weight:600;color:var(--tronox-blue);margin-bottom:4px}
.card-sub{font-size:.78rem;color:var(--muted);margin-bottom:14px}
.interpretation{
  background:#eef3fa;border-left:3px solid var(--tronox-teal);
  padding:10px 14px;border-radius:0 6px 6px 0;
  font-size:.8rem;line-height:1.6;color:#2b3a52;margin-top:16px;
}

/* ── Tables ── */
.tbl-wrap{overflow-x:auto;margin-top:16px}
table{width:100%;border-collapse:collapse;font-size:.78rem}
thead tr{background:var(--tronox-blue);color:#fff}
thead th{padding:8px 10px;text-align:left;cursor:pointer;user-select:none;white-space:nowrap}
thead th:hover{background:var(--tronox-teal)}
tbody tr:nth-child(even){background:#f7f9fc}
tbody td{padding:6px 10px;border-bottom:1px solid #eaecf0}
tbody tr:hover{background:#e8f0fe}

/* ── Target badge ── */
.target-badge{
  display:inline-flex;align-items:center;gap:6px;
  background:#fff3cd;border:1px solid #ffc107;color:#856404;
  padding:5px 12px;border-radius:20px;font-size:.78rem;font-weight:600;
}

/* ── Progress bar ── */
.prog-bar-wrap{background:#e0e7ef;border-radius:4px;height:10px;width:100%;margin-top:6px}
.prog-bar{height:10px;border-radius:4px;background:var(--accent)}
.prog-bar.ok{background:var(--tronox-green)}

/* ── Alert box ── */
.alert{background:#fff3cd;border:1px solid #ffc107;border-radius:8px;padding:12px 16px;font-size:.8rem;margin-bottom:18px;color:#856404}
.alert strong{color:#533f03}

/* ── Print ── */
@media print{
  #sidebar{display:none}
  #main{margin-left:0}
  .section{display:block!important}
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
    <a href="#" class="active" data-sec="overview">&#9632; Overview &amp; KPIs</a>
    <a href="#" data-sec="exc-freq">&#9632; Exception Frequency</a>
    <a href="#" data-sec="vendors">&#9632; Top Problem Vendors</a>
    <a href="#" data-sec="category">&#9632; Material Category</a>
    <a href="#" data-sec="channel">&#9632; Ingestion Method</a>
    <a href="#" data-sec="combos">&#9632; Exception Combinations</a>
    <a href="#" data-sec="trends">&#9632; Monthly Trends</a>
    <a href="#" data-sec="workload">&#9632; Workload Concentration</a>
    <a href="#" data-sec="dq">&#9632; Data Quality Notes</a>
  </nav>
  <div class="footer-note">S4 AP Audit · Company 1100 · FY2025–2026<br/>Transport vendors excluded · NB &amp; ZCP POs only</div>
</nav>

<main id="main">
  <h1 class="page-title">AP Invoice Exception Analysis — 1100 (US)</h1>
  <p class="page-sub">newTRON S4 Implementation · Internal Audit Ref: 2026-01 · Data through Jan 2026</p>

  <!-- ═══════════════ OVERVIEW ═══════════════ -->
  <div class="section active" id="sec-overview">
    <div class="target-badge" style="margin-bottom:16px">&#9888; Target: 80% touchless first-pass &nbsp;|&nbsp; Current: <span id="fp-badge">–</span>%</div>
    <div class="kpi-grid" id="kpi-grid"></div>

    <div class="card">
      <div class="card-title">First-Pass Rate vs. 80% Target</div>
      <div class="card-sub">By ingestion channel – Posted NB/ZCP invoices, transport vendors excluded</div>
      <div id="chart-overview-fp" style="height:280px"></div>
      <div class="interpretation">
        The overall first-pass rate is <strong id="fp-text">–</strong>% against an 80% target — a gap of more than 40 percentage points.
        COUPA performs best at ~52% but still falls far short of target. MAIL_IES (by far the largest volume at ~86% of invoices)
        sits at only ~33%. Closing the gap requires both channel migration (more invoices through Coupa) and upstream data quality fixes
        so that invoices entering via any channel arrive complete.
      </div>
    </div>

    <div class="card">
      <div class="card-title">Exception Events by Type (Top 10)</div>
      <div class="card-sub">Sorted dataset · Posted invoices only · transport &amp; non-NB/ZCP excluded</div>
      <div id="chart-overview-exc" style="height:300px"></div>
    </div>
  </div>

  <!-- ═══════════════ EXCEPTION FREQUENCY ═══════════════ -->
  <div class="section" id="sec-exc-freq">
    <div class="card">
      <div class="card-title">Exception Frequency — All Types Ranked</div>
      <div class="card-sub">Each bar = total exception events of that type across all posted invoices</div>
      <div id="chart-exc-bar" style="height:420px"></div>
      <div class="interpretation">
        <strong>Exception 1 "Process PO Invoice"</strong> is the single largest exception at <strong id="exc1-pct">–</strong>% of all events (~4,050 occurrences).
        The audit team notes this exception has no actionable meaning — it is a system artefact triggered whenever VIM performs a PO match step.
        Suppressing or reclassifying this exception would remove ~30% of the noise from AP's queue and significantly improve reported first-pass rates.
        <br/><br/>
        The next two largest exceptions — <strong>151 "Manual Check / Missing Indexing Data"</strong> (~20%) and <strong>29 "Missing Mandatory Information"</strong> (~19%) — are genuine data-quality
        issues that require AP intervention. Together they account for ~39% of exceptions and represent the most material AP workload driver.
        Exception 75 "Price Discrepancy" (~7%) and Exception 38 "Freight on Invoice" (~6%) round out the top tier.
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

  <!-- ═══════════════ VENDORS ═══════════════ -->
  <div class="section" id="sec-vendors">
    <div class="card">
      <div class="card-title">Top 30 Vendors by Exception Events (Volume)</div>
      <div class="card-sub">Total exception events generated per vendor · Posted NB/ZCP invoices</div>
      <div id="chart-vendor-vol" style="height:520px"></div>
      <div class="interpretation">
        The top vendor by exception volume is <strong>Southern Ionics Incorporated</strong> with 1,061 exception events across 946 invoices —
        nearly 1 exception per invoice on average. This is likely driven by repetitive data entry patterns (e.g., consistent missing data fields).
        <br/><br/>
        The top 10 vendors generate <strong id="top10-pct">–</strong>% of all exception events. Targeted vendor onboarding clinics for the top 20–30 suppliers
        could reduce total exception volume by ~40%.
      </div>
    </div>

    <div class="card">
      <div class="card-title">Top 20 Vendors by Exception Intensity (Avg Exceptions/Invoice, min 10 invoices)</div>
      <div class="card-sub">High intensity = systemic data quality problem at that vendor</div>
      <div id="chart-vendor-int" style="height:400px"></div>
      <div class="interpretation">
        Vendors with high intensity (exceptions-per-invoice ratio) have <em>systemic</em> data quality problems rather than just high transaction volume.
        These are the highest-priority candidates for direct vendor outreach and EDI/PO-flip enablement.
      </div>
    </div>

    <div class="card">
      <div class="card-title">Top 30 Vendor Detail Table</div>
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
      <div class="card-sub">Standard = MRP/stores materials &nbsp;|&nbsp; Service = service entry sheet–backed invoices</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
        <div id="chart-cat-pie" style="height:340px"></div>
        <div id="chart-cat-bar" style="height:340px"></div>
      </div>
      <div class="interpretation">
        <strong>Standard (MRP/stores) invoices</strong> generate the most exception events in absolute terms (~60%), which is expected given their higher volume.
        However, <strong>Service invoices</strong> (~37% of exception events) are disproportionately problematic relative to their invoice count —
        service entry sheets (SES) must be created and confirmed before VIM can match the invoice, and delays or SES omissions cause a cascade of exceptions.
        <br/><br/>
        Service invoices are the #1 pain point per audit team assessment. SES creation lead time and "goods receipt not done" scenarios
        (though Exception 91 is excluded here) remain the primary driver of the service exception profile.
      </div>
    </div>

    <div class="card">
      <div class="card-title">Exception Type Breakdown by Category (Top exceptions per category)</div>
      <div id="chart-cat-exc" style="height:420px"></div>
    </div>

    <div class="card">
      <div class="card-title">Category Exception Detail Table</div>
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
      <div class="card-sub">An invoice is "first-pass" if it generates no exceptions in the sorted dataset (excl. IDs 0 &amp; 91)</div>
      <div id="chart-channel-fp" style="height:320px"></div>
      <div class="interpretation">
        <strong>COUPA</strong> achieves the highest first-pass rate at ~52% but represents only ~12% of invoice volume.
        <strong>MAIL_IES</strong> handles ~86% of invoices with only a ~33% first-pass rate — this is the primary lever for improvement.
        VIM_IES (direct SAP upload) performs similarly to MAIL_IES.<br/><br/>
        The audit expected COUPA first-pass of ~70%+; the ~52% actuality suggests that even COUPA-submitted invoices frequently have data gaps
        (likely service POs requiring SES, or price/quantity mismatches at the PO level). Shifting more volume to COUPA alone will not solve the problem
        without simultaneous PO data hygiene improvements.
      </div>
    </div>

    <div class="card">
      <div class="card-title">First-Pass Rate: Channel × Material Category</div>
      <div class="card-sub">Shows where Coupa's advantage is strongest</div>
      <div id="chart-channel-cat" style="height:340px"></div>
      <div class="interpretation">
        COUPA performs materially better for <strong>Standard</strong> materials than for Service POs, reflecting the SES dependency.
        Focusing COUPA adoption on Standard/MRP procurement would yield the fastest first-pass improvement.
      </div>
    </div>

    <div class="card">
      <div class="card-title">Channel × Category First-Pass Table</div>
      <div class="tbl-wrap"><table id="tbl-channel-cat">
        <thead><tr><th onclick="sortTable(this)">Channel</th><th onclick="sortTable(this)">Category</th><th onclick="sortTable(this)">Total Invoices</th><th onclick="sortTable(this)">First-Pass</th><th onclick="sortTable(this)">First-Pass %</th></tr></thead>
        <tbody id="tbody-channel-cat"></tbody>
      </table></div>
    </div>
  </div>

  <!-- ═══════════════ COMBOS ═══════════════ -->
  <div class="section" id="sec-combos">
    <div class="card">
      <div class="card-title">How Many Exceptions Does Each Invoice Trigger?</div>
      <div class="card-sub">Distribution across all invoices in the sorted dataset (excl. 0 &amp; 91)</div>
      <div id="chart-exc-dist" style="height:300px"></div>
      <div class="interpretation">
        Most invoices with exceptions trigger just 1 or 2 exceptions. However, a significant tail of invoices triggers 3 or more,
        indicating cascading failure chains where an initial data problem (e.g., missing PO info) triggers downstream blocks.
        Resolving root-cause exceptions earlier in the process would collapse these chains.
      </div>
    </div>

    <div class="card">
      <div class="card-title">Most Common 2-Exception Chains</div>
      <div class="card-sub">Ordered pairs of sequential exceptions on the same invoice</div>
      <div id="chart-pairs" style="height:340px"></div>
    </div>

    <div class="card">
      <div class="card-title">Most Common 3-Exception Chains</div>
      <div id="chart-triples" style="height:320px"></div>
    </div>

    <div class="card">
      <div class="card-title">Exception Chain Detail Tables</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
        <div>
          <div class="card-title" style="font-size:.85rem">Top Pairs</div>
          <div class="tbl-wrap"><table id="tbl-pairs">
            <thead><tr><th onclick="sortTable(this)">Exception Pair</th><th onclick="sortTable(this)">Count</th></tr></thead>
            <tbody id="tbody-pairs"></tbody>
          </table></div>
        </div>
        <div>
          <div class="card-title" style="font-size:.85rem">Top Triples</div>
          <div class="tbl-wrap"><table id="tbl-triples">
            <thead><tr><th onclick="sortTable(this)">Exception Triple</th><th onclick="sortTable(this)">Count</th></tr></thead>
            <tbody id="tbody-triples"></tbody>
          </table></div>
        </div>
      </div>
    </div>
  </div>

  <!-- ═══════════════ TRENDS ═══════════════ -->
  <div class="section" id="sec-trends">
    <div class="card">
      <div class="card-title">Monthly Invoice Volume &amp; Exception Events</div>
      <div class="card-sub">May 2025 = go-live month; volume ramps through mid-year</div>
      <div id="chart-monthly-vol" style="height:320px"></div>
    </div>

    <div class="card">
      <div class="card-title">Monthly First-Pass Rate (%) vs. 80% Target</div>
      <div id="chart-monthly-fp" style="height:300px"></div>
      <div class="interpretation">
        First-pass rate started very low at go-live (~21% in May 2025) and improved over the first few months as the AP team learned the system,
        peaking around 45% in August 2025. However, it then <strong>deteriorated</strong> through Q4 2025, dropping back to ~30% in December.
        This deterioration pattern often reflects end-of-year invoice surges outpacing AP capacity, or seasonal vendor behaviour changes.
        The rate has not shown a sustained improvement trajectory toward the 80% target — targeted interventions are needed.
      </div>
    </div>

    <div class="card">
      <div class="card-title">Monthly Trend Data Table</div>
      <div class="tbl-wrap"><table id="tbl-monthly">
        <thead><tr><th onclick="sortTable(this)">Month</th><th onclick="sortTable(this)">Total Invoices</th><th onclick="sortTable(this)">Exception Invoices</th><th onclick="sortTable(this)">First-Pass Invoices</th><th onclick="sortTable(this)">First-Pass %</th></tr></thead>
        <tbody id="tbody-monthly"></tbody>
      </table></div>
    </div>
  </div>

  <!-- ═══════════════ WORKLOAD ═══════════════ -->
  <div class="section" id="sec-workload">
    <div class="card">
      <div class="card-title">AP Workload Concentration — Cumulative Exception Events by Vendor</div>
      <div class="card-sub">Pareto view: how concentrated is the exception workload?</div>
      <div id="chart-pareto" style="height:420px"></div>
      <div class="interpretation">
        The top <strong>10 vendors</strong> drive <strong id="top10-pct2">–</strong>% of all exception events.
        The top <strong>20 vendors</strong> drive <strong id="top20-pct">–</strong>% and the top <strong>50</strong> drive <strong id="top50-pct">–</strong>%.
        <br/><br/>
        This is a relatively flat Pareto (not the classic 80/20), meaning exception workload is spread broadly across many vendors.
        There is no single "silver bullet" vendor fix — but targeting the top 20–30 through dedicated vendor management programs
        (EDI onboarding, PO-flip capability, vendor data clinics) would still yield the largest near-term workload reduction.
      </div>
    </div>

    <div class="card">
      <div class="card-title">Top 50 Vendors by Workload — Detail Table</div>
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
      <div class="alert" style="margin-top:0">
        <strong>Audit team should review these notes before drawing final conclusions from this dashboard.</strong>
      </div>

      <div style="display:flex;flex-direction:column;gap:14px;font-size:.83rem;line-height:1.7">
        <div>
          <strong>1. Transport Vendor Exclusion</strong><br/>
          All suppliers with Supplier ID starting with "52" (e.g., DM Trans, Gulf Relay, BNSF Railway) have been removed from all analyses.
          These are freight/logistics vendors whose exceptions are driven by volatile fuel surcharges and are accepted by the business.
          Raw sorted dataset: 15,841 rows → after exclusion: 13,363 exception events (posted NB/ZCP).
        </div>
        <div>
          <strong>2. Exception 1 "Process PO Invoice" — System Artefact</strong><br/>
          Exception ID 1 accounts for 30.3% of all events (4,050 occurrences) but the audit team notes it is a system-generated artefact
          with no meaningful AP action required. If this exception were suppressed or reclassified, the first-pass rate would improve substantially —
          but the underlying data quality issues (Exceptions 151, 29, 75) would remain.
        </div>
        <div>
          <strong>3. Duplicate "Created at" and "Time Stamp" Columns</strong><br/>
          Both CSV files contain two columns each named "Created at" and "Time Stamp". The first instance of each has been used for date analysis
          (the second appears to be a different stage timestamp). Verify with the VIM/SAP team which represents invoice creation vs. posting.
        </div>
        <div>
          <strong>4. January 2026 Data Truncation</strong><br/>
          The dataset contains only 15 invoices for January 2026, with a first-pass rate of 13.3%. This is almost certainly a data extract cutoff
          (partial month) and should not be interpreted as a trend deterioration. Monthly trend charts exclude Jan-2026 for clarity.
        </div>
        <div>
          <strong>5. First-Pass Rate Calculation Methodology</strong><br/>
          An invoice is counted as "first-pass" if its Document ID does not appear in the sorted dataset (which excludes Exception IDs 0 and 91).
          This means invoices with only Exception 0 (PO Low-value) or only Exception 91 (GR Not Done Simple Check) are treated as first-pass.
          The audit team has confirmed this is the intended methodology. The overall rate is <strong>35.4%</strong> (NB/ZCP, non-transport, posted).
        </div>
        <div>
          <strong>6. PO Type Scope</strong><br/>
          Analysis includes NB (Regular stores/MRP) and ZCP (Regular WO/services) PO types only. Intercompany types (ZCST, ZCUB, ZLP, ZSTO, ZUBO),
          transport types (ZTM, ZSTM), and Non-PO (#N/A) invoices have been excluded from primary analysis.
          The Inc file contains 35,142 rows total; after all filters, 12,859 unique invoices form the analysis universe.
        </div>
        <div>
          <strong>7. Amount Parsing</strong><br/>
          Gross Invoice Amounts contain embedded commas and quotes in the source CSV. These have been stripped for numeric analysis.
          A small number of rows had unparseable amounts (&lt;0.5%) and were excluded from any amount-based calculations.
        </div>
      </div>
    </div>
  </div>

</main>

<script>
// ── Embedded data ──
const D = """ + DATA_JS + r""";

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

// ── Colour palettes ──
const BLUE  = '#1a3d6b';
const TEAL  = '#007a8a';
const GREEN = '#2d8a4e';
const RED   = '#e8503a';
const AMBER = '#f0a500';
const GREY  = '#6b7a90';
const PAL   = ['#1a3d6b','#007a8a','#2d8a4e','#e8503a','#f0a500','#7b5ea7','#c0392b','#2980b9','#27ae60','#d35400'];

// ── Table sort ──
function sortTable(th){
  const tbl=th.closest('table');
  const tbody=tbl.querySelector('tbody');
  const col=th.cellIndex;
  const rows=[...tbody.querySelectorAll('tr')];
  const asc=th.dataset.asc!=='1';
  rows.sort((a,b)=>{
    const va=a.cells[col].textContent.trim();
    const vb=b.cells[col].textContent.trim();
    const na=parseFloat(va.replace(/,/g,'')), nb=parseFloat(vb.replace(/,/g,''));
    if(!isNaN(na)&&!isNaN(nb)) return asc?na-nb:nb-na;
    return asc?va.localeCompare(vb):vb.localeCompare(va);
  });
  rows.forEach(r=>tbody.appendChild(r));
  th.closest('thead').querySelectorAll('th').forEach(x=>x.dataset.asc='');
  th.dataset.asc=asc?'1':'0';
}

// ── Build table body ──
function buildTable(tbodyId, rows, cols){
  const tb=document.getElementById(tbodyId);
  if(!tb) return;
  tb.innerHTML=rows.map(r=>'<tr>'+cols.map(c=>`<td>${r[c]??''}</td>`).join('')+'</tr>').join('');
}

// ── Rendered flag ──
const rendered={};

function renderSection(sec){
  if(rendered[sec]) return;
  rendered[sec]=true;

  const ly={margin:{l:50,r:20,t:30,b:80},paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',
    font:{family:'Segoe UI,Arial',size:11,color:'#1e2a3a'},
    xaxis:{gridcolor:'#e8edf3'},yaxis:{gridcolor:'#e8edf3'}};

  if(sec==='overview'){
    // KPI cards
    const kpi=D.kpi;
    document.getElementById('fp-badge').textContent=kpi.first_pass_rate;
    document.getElementById('fp-text').textContent=kpi.first_pass_rate;
    const cards=[
      {label:'Total Invoices Analysed',value:kpi.total_invoices.toLocaleString(),note:'NB/ZCP posted, non-transport',cls:''},
      {label:'First-Pass Rate',value:kpi.first_pass_rate+'%',note:'Target: 80%',cls:'danger'},
      {label:'Total Exception Events',value:kpi.total_exception_events.toLocaleString(),note:'Excl. Exc 0 & 91',cls:''},
      {label:'Exception Invoices',value:(kpi.total_invoices-kpi.first_pass_count).toLocaleString(),note:'Invoices needing AP touch',cls:''},
      {label:'Unique Vendors w/ Exceptions',value:kpi.unique_vendors_with_exceptions.toLocaleString(),note:'Out of total vendor base',cls:''},
      {label:'Top 10 Vendors Drive',value:kpi.top10_vendor_pct+'%',note:'Of all exception events',cls:''},
    ];
    const grid=document.getElementById('kpi-grid');
    grid.innerHTML=cards.map(c=>`
      <div class="kpi-card">
        <div class="kpi-label">${c.label}</div>
        <div class="kpi-value ${c.cls}">${c.value}</div>
        <div class="kpi-note">${c.note}</div>
      </div>`).join('');

    // Channel FP bar
    const ch=D.channel_fp;
    Plotly.newPlot('chart-overview-fp',[
      {x:ch.map(r=>r['Channel ID']),y:ch.map(r=>r.First_Pass_Rate),type:'bar',
       marker:{color:ch.map(r=>r.First_Pass_Rate>=80?GREEN:r.First_Pass_Rate>=50?AMBER:RED)},
       text:ch.map(r=>r.First_Pass_Rate+'%'),textposition:'outside',
       customdata:ch.map(r=>[r.Total,r.First_Pass_Count]),
       hovertemplate:'<b>%{x}</b><br>First-pass: %{y}%<br>Total invoices: %{customdata[0]}<br>Passed: %{customdata[1]}<extra></extra>'},
      {x:['COUPA','MAIL_IES','VIM_IES'],y:[80,80,80],type:'scatter',mode:'lines',
       line:{color:GREEN,dash:'dash',width:2},name:'80% Target',showlegend:true}
    ],{...ly,yaxis:{...ly.yaxis,range:[0,95],title:'First-Pass Rate (%)'},
       xaxis:{title:'Ingestion Channel'},showlegend:true,
       legend:{x:1,xanchor:'right',y:1}},{responsive:true});

    // Top 10 exceptions bar
    const ef=D.exc_freq.slice(0,10);
    Plotly.newPlot('chart-overview-exc',[
      {x:ef.map(r=>r.Count),y:ef.map(r=>`ID ${r['Exception ID']}: ${r['Exception description'].substring(0,45)}...`),
       type:'bar',orientation:'h',
       marker:{color:PAL},
       text:ef.map(r=>r.Count.toLocaleString()),textposition:'outside',
       hovertemplate:'<b>%{y}</b><br>Count: %{x}<extra></extra>'}
    ],{...ly,margin:{l:320,r:60,t:20,b:40},xaxis:{title:'Exception Events'},yaxis:{autorange:'reversed'}},{responsive:true});
  }

  if(sec==='exc-freq'){
    const ef=D.exc_freq;
    const exc1=ef.find(r=>r['Exception ID']===1);
    if(exc1) document.getElementById('exc1-pct').textContent=exc1.Pct;
    Plotly.newPlot('chart-exc-bar',[
      {x:ef.map(r=>`ID ${r['Exception ID']}`),y:ef.map(r=>r.Count),type:'bar',
       marker:{color:ef.map((r,i)=>r['Exception ID']===1?RED:PAL[i%PAL.length])},
       text:ef.map(r=>r.Pct+'%'),textposition:'outside',
       customdata:ef.map(r=>r['Exception description']),
       hovertemplate:'<b>%{customdata}</b><br>Count: %{y}<br>Share: %{text}<extra></extra>'}
    ],{...ly,xaxis:{title:'Exception ID'},yaxis:{title:'Exception Events'},
       margin:{...ly.margin,b:60}},{responsive:true});

    buildTable('tbody-exc-freq', ef, ['Exception ID','Exception description','Count','Pct']);
  }

  if(sec==='vendors'){
    document.getElementById('top10-pct').textContent=D.kpi.top10_vendor_pct;
    const vt=D.vendor_top30;
    Plotly.newPlot('chart-vendor-vol',[
      {x:vt.map(r=>r.Exception_Events),
       y:vt.map(r=>r['Name 1'].length>35?r['Name 1'].substring(0,35)+'…':r['Name 1']),
       type:'bar',orientation:'h',
       marker:{color:BLUE},
       customdata:vt.map(r=>[r.Unique_Invoices,r.Avg_Exc_Per_Inv]),
       hovertemplate:'<b>%{y}</b><br>Exception events: %{x}<br>Invoices: %{customdata[0]}<br>Avg exc/inv: %{customdata[1]}<extra></extra>'}
    ],{...ly,margin:{l:260,r:60,t:20,b:50},xaxis:{title:'Exception Events'},yaxis:{autorange:'reversed'}},{responsive:true});

    const vi=D.vendor_intensity;
    Plotly.newPlot('chart-vendor-int',[
      {x:vi.map(r=>r.Avg_Exc_Per_Inv),
       y:vi.map(r=>r['Name 1'].length>35?r['Name 1'].substring(0,35)+'…':r['Name 1']),
       type:'bar',orientation:'h',
       marker:{color:vi.map(r=>r.Avg_Exc_Per_Inv>=3?RED:r.Avg_Exc_Per_Inv>=2?AMBER:TEAL)},
       customdata:vi.map(r=>[r.Unique_Invoices,r.Exception_Events]),
       hovertemplate:'<b>%{y}</b><br>Avg exc/inv: %{x}<br>Invoices: %{customdata[0]}<br>Total events: %{customdata[1]}<extra></extra>'}
    ],{...ly,margin:{l:260,r:60,t:20,b:50},xaxis:{title:'Avg Exceptions per Invoice'},yaxis:{autorange:'reversed'}},{responsive:true});

    buildTable('tbody-vendors', vt, ['Supplier','Name 1','Unique_Invoices','Exception_Events','Avg_Exc_Per_Inv']);
  }

  if(sec==='category'){
    const cs=D.cat_summary;
    Plotly.newPlot('chart-cat-pie',[
      {labels:cs.map(r=>r['PO category decription']),values:cs.map(r=>r.Exception_Events),
       type:'pie',hole:.4,
       marker:{colors:[BLUE,TEAL,AMBER,GREEN]},
       textinfo:'label+percent',hovertemplate:'<b>%{label}</b><br>%{value} events (%{percent})<extra></extra>'}
    ],{...ly,margin:{l:10,r:10,t:30,b:10},showlegend:false},{responsive:true});

    Plotly.newPlot('chart-cat-bar',[
      {x:cs.map(r=>r['PO category decription']),y:cs.map(r=>r.Exception_Events),
       type:'bar',marker:{color:[BLUE,TEAL,AMBER,GREEN]},
       text:cs.map(r=>r.Exception_Events.toLocaleString()),textposition:'outside',
       hovertemplate:'<b>%{x}</b><br>Events: %{y}<extra></extra>'}
    ],{...ly,margin:{l:50,r:20,t:30,b:60},yaxis:{title:'Exception Events'}},{responsive:true});

    // Stacked bar: top exceptions per category
    const ce=D.cat_exc;
    const cats=[...new Set(ce.map(r=>r['PO category decription']))];
    const excIds=[...new Set(ce.map(r=>r['Exception ID']))].slice(0,10);
    const traces=excIds.map((eid,i)=>({
      name:`ID ${eid}`,
      x:cats,
      y:cats.map(cat=>{const row=ce.find(r=>r['PO category decription']===cat&&r['Exception ID']===eid);return row?row.Count:0;}),
      type:'bar',marker:{color:PAL[i%PAL.length]},
      hovertemplate:`<b>ID ${eid}</b><br>%{x}: %{y}<extra></extra>`
    }));
    Plotly.newPlot('chart-cat-exc',traces,{...ly,barmode:'stack',
      yaxis:{title:'Exception Events'},xaxis:{title:'Material Category'},
      legend:{x:1,xanchor:'right',y:1}},{responsive:true});

    buildTable('tbody-cat-exc', ce, ['PO category decription','Exception ID','Exception description','Count']);
  }

  if(sec==='channel'){
    const cf=D.channel_fp;
    Plotly.newPlot('chart-channel-fp',[
      {x:cf.map(r=>r['Channel ID']),y:cf.map(r=>r.Total),name:'Exception Invoices',type:'bar',
       marker:{color:RED},
       customdata:cf.map(r=>r.Total-r.First_Pass_Count),
       hovertemplate:'<b>%{x}</b><br>Total: %{y}<extra></extra>'},
      {x:cf.map(r=>r['Channel ID']),y:cf.map(r=>r.First_Pass_Count),name:'First-Pass Invoices',type:'bar',
       marker:{color:GREEN},
       hovertemplate:'<b>%{x}</b><br>First-pass: %{y}<extra></extra>'},
      {x:cf.map(r=>r['Channel ID']),y:cf.map(r=>r.First_Pass_Rate),name:'First-Pass Rate (%)',type:'scatter',
       mode:'lines+markers+text',yaxis:'y2',
       line:{color:AMBER,width:3},marker:{size:10},
       text:cf.map(r=>r.First_Pass_Rate+'%'),textposition:'top center',
       hovertemplate:'<b>%{x}</b><br>Rate: %{y}%<extra></extra>'},
      {x:['COUPA','MAIL_IES','VIM_IES'],y:[80,80,80],name:'80% Target',type:'scatter',mode:'lines',
       yaxis:'y2',line:{color:GREEN,dash:'dash',width:2}}
    ],{...ly,barmode:'stack',
       yaxis:{title:'Invoice Count'},
       yaxis2:{title:'First-Pass Rate (%)',overlaying:'y',side:'right',range:[0,100]},
       legend:{x:1.05,y:1},margin:{l:60,r:80,t:30,b:60}},{responsive:true});

    // Channel x category
    const cc=D.channel_cat_fp;
    const channels=[...new Set(cc.map(r=>r['Channel ID']))];
    const catsCh=[...new Set(cc.map(r=>r['PO category decription']))];
    const tracesCh=channels.map((ch,i)=>({
      name:ch,
      x:catsCh,
      y:catsCh.map(cat=>{const r=cc.find(x=>x['Channel ID']===ch&&x['PO category decription']===cat);return r?r.First_Pass_Rate:null;}),
      type:'bar',marker:{color:PAL[i]},
      hovertemplate:`<b>${ch}</b><br>%{x}: %{y}%<extra></extra>`
    }));
    Plotly.newPlot('chart-channel-cat',tracesCh,{...ly,barmode:'group',
      yaxis:{title:'First-Pass Rate (%)'},
      shapes:[{type:'line',x0:-0.5,x1:catsCh.length-0.5,y0:80,y1:80,line:{color:GREEN,dash:'dash',width:2}}],
      annotations:[{x:catsCh.length-1,y:82,text:'80% Target',showarrow:false,font:{color:GREEN,size:11}}],
      legend:{x:1,xanchor:'right',y:1}},{responsive:true});

    buildTable('tbody-channel-cat',cc,['Channel ID','PO category decription','Total','First_Pass_Count','First_Pass_Rate']);
  }

  if(sec==='combos'){
    const ed=D.exc_dist;
    Plotly.newPlot('chart-exc-dist',[
      {x:ed.map(r=>r.N_Exceptions.toString()),y:ed.map(r=>r.Invoice_Count),type:'bar',
       marker:{color:PAL},
       text:ed.map(r=>r.Invoice_Count.toLocaleString()),textposition:'outside',
       hovertemplate:'<b>%{x} exception(s)</b><br>Invoices: %{y}<extra></extra>'}
    ],{...ly,xaxis:{title:'Number of Exceptions per Invoice'},yaxis:{title:'Invoice Count'}},{responsive:true});

    const ep=D.exc_pairs;
    Plotly.newPlot('chart-pairs',[
      {x:ep.map(r=>r.Count),y:ep.map(r=>r.Pair),type:'bar',orientation:'h',
       marker:{color:TEAL},
       text:ep.map(r=>r.Count),textposition:'outside',
       hovertemplate:'<b>%{y}</b><br>Count: %{x}<extra></extra>'}
    ],{...ly,margin:{l:100,r:60,t:20,b:50},xaxis:{title:'Occurrences'},yaxis:{autorange:'reversed'}},{responsive:true});

    const et=D.exc_triples;
    Plotly.newPlot('chart-triples',[
      {x:et.map(r=>r.Count),y:et.map(r=>r.Triple),type:'bar',orientation:'h',
       marker:{color:AMBER},
       text:et.map(r=>r.Count),textposition:'outside',
       hovertemplate:'<b>%{y}</b><br>Count: %{x}<extra></extra>'}
    ],{...ly,margin:{l:140,r:60,t:20,b:50},xaxis:{title:'Occurrences'},yaxis:{autorange:'reversed'}},{responsive:true});

    buildTable('tbody-pairs',ep,['Pair','Count']);
    buildTable('tbody-triples',et,['Triple','Count']);
  }

  if(sec==='trends'){
    const mn=D.monthly.filter(r=>r.Month_str!=='2026-01'); // exclude partial month
    Plotly.newPlot('chart-monthly-vol',[
      {x:mn.map(r=>r.Month_str),y:mn.map(r=>r.Total_Invoices),name:'Total Invoices',type:'bar',marker:{color:BLUE},
       hovertemplate:'<b>%{x}</b><br>Total: %{y}<extra></extra>'},
      {x:mn.map(r=>r.Month_str),y:mn.map(r=>r.Exc_Invoices),name:'Exception Invoices',type:'bar',marker:{color:RED},
       hovertemplate:'<b>%{x}</b><br>Exception: %{y}<extra></extra>'}
    ],{...ly,barmode:'overlay',yaxis:{title:'Invoice Count'},xaxis:{title:'Month'},
       legend:{x:1,xanchor:'right',y:1}},{responsive:true});

    Plotly.newPlot('chart-monthly-fp',[
      {x:mn.map(r=>r.Month_str),y:mn.map(r=>r.First_Pass_Rate),type:'scatter',mode:'lines+markers',
       name:'First-Pass %',line:{color:TEAL,width:3},marker:{size:8},
       text:mn.map(r=>r.First_Pass_Rate+'%'),textposition:'top center',
       hovertemplate:'<b>%{x}</b><br>First-pass: %{y}%<extra></extra>'},
      {x:mn.map(r=>r.Month_str),y:mn.map(()=>80),name:'80% Target',type:'scatter',mode:'lines',
       line:{color:GREEN,dash:'dash',width:2}}
    ],{...ly,yaxis:{title:'First-Pass Rate (%)',range:[0,100]},xaxis:{title:'Month'},
       shapes:[{type:'rect',x0:mn[0].Month_str,x1:mn[mn.length-1].Month_str,y0:0,y1:80,
                fillcolor:'rgba(232,80,58,.06)',line:{width:0}}],
       legend:{x:1,xanchor:'right',y:1}},{responsive:true});

    buildTable('tbody-monthly', D.monthly,['Month_str','Total_Invoices','Exc_Invoices','First_Pass_Rate']);
  }

  if(sec==='workload'){
    const wc=D.workload_conc;
    const top10pct=wc[9]?.Cumulative_Pct??'–';
    const top20pct=wc[19]?.Cumulative_Pct??'–';
    const top50pct=wc[49]?.Cumulative_Pct??'–';
    if(document.getElementById('top10-pct2')) document.getElementById('top10-pct2').textContent=top10pct;
    if(document.getElementById('top20-pct')) document.getElementById('top20-pct').textContent=top20pct;
    if(document.getElementById('top50-pct')) document.getElementById('top50-pct').textContent=top50pct;

    Plotly.newPlot('chart-pareto',[
      {x:wc.map((_,i)=>i+1),y:wc.map(r=>r.Exception_Events),name:'Exception Events',type:'bar',marker:{color:BLUE},
       hovertemplate:'Rank %{x} – %{customdata}<br>Events: %{y}<extra></extra>',
       customdata:wc.map(r=>r['Name 1'])},
      {x:wc.map((_,i)=>i+1),y:wc.map(r=>r.Cumulative_Pct),name:'Cumulative %',type:'scatter',mode:'lines',
       yaxis:'y2',line:{color:RED,width:3},
       hovertemplate:'Rank %{x}<br>Cumulative: %{y}%<extra></extra>'},
      {x:[1,50],y:[80,80],name:'80% threshold',type:'scatter',mode:'lines',yaxis:'y2',
       line:{color:AMBER,dash:'dot',width:2}}
    ],{...ly,barmode:'overlay',
       yaxis:{title:'Exception Events'},
       yaxis2:{title:'Cumulative %',overlaying:'y',side:'right',range:[0,100]},
       xaxis:{title:'Vendor Rank'},
       legend:{x:1.05,y:1},margin:{l:60,r:80,t:30,b:60}},{responsive:true});

    buildTable('tbody-workload', wc.map((r,i)=>({...r,rank:i+1})),
      ['rank','Supplier','Name 1','Exception_Events','Unique_Invoices','Cumulative_Pct']);
  }
}

// ── Initial render ──
renderSection('overview');
</script>

<style>@media print{
  #sidebar{display:none!important}
  #main{margin-left:0!important;padding:10px!important}
  .section{display:block!important}
  .card{break-inside:avoid;page-break-inside:avoid}
}</style>
</body>
</html>
"""

out_html = os.path.join(OUT_DIR, "dashboard.html")
with open(out_html, "w", encoding="utf-8") as f:
    f.write(HTML)

# Root index.html for GitHub Pages (branch deploy: / root)
index_html = os.path.join(SCRIPT_DIR, "index.html")
with open(index_html, "w", encoding="utf-8") as f:
    f.write(HTML)

print(f"Dashboard saved to {out_html}")
print(f"GitHub Pages entry: {index_html}")
print(f"File size: {os.path.getsize(out_html) / 1024:.0f} KB")
